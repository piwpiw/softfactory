#!/bin/bash
#
# SoftFactory Production Deployment Script
# Orchestrates full deployment pipeline with error handling and rollback
#
# Usage: ./scripts/deploy.sh [staging|production] [--dry-run] [--skip-tests]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env-prod"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DOCKER_COMPOSE="docker-compose -f ${PROJECT_ROOT}/docker-compose-prod.yml"
LOG_FILE="${BACKUP_DIR}/deployment_$(date +%Y%m%d_%H%M%S).log"

# Default values
ENVIRONMENT="staging"
DRY_RUN=false
SKIP_TESTS=false
VERBOSE=false

# Functions
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }
log_success() { log "${GREEN}SUCCESS${NC}" "$@"; }

usage() {
    cat << EOF
Usage: $0 [environment] [options]

Environments:
    staging         Deploy to staging (default)
    production      Deploy to production (requires confirmation)

Options:
    --dry-run       Show what would be done without making changes
    --skip-tests    Skip running tests before deployment
    --verbose       Enable verbose output
    --help          Show this help message

Examples:
    ./scripts/deploy.sh staging
    ./scripts/deploy.sh production --skip-tests
    ./scripts/deploy.sh staging --dry-run

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Setup
mkdir -p "$BACKUP_DIR"

log_info "Starting SoftFactory deployment script"
log_info "Environment: $ENVIRONMENT"
log_info "Dry run: $DRY_RUN"
log_info "Log file: $LOG_FILE"

# =============================================================================
# PHASE 1: PRE-DEPLOYMENT CHECKS
# =============================================================================

phase_checks() {
    log_info "===== PHASE 1: Pre-Deployment Checks ====="

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env-prod file not found at $ENV_FILE"
        exit 1
    fi
    log_success ".env-prod file found"

    # Check Docker daemon
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon not running or not accessible"
        exit 1
    fi
    log_success "Docker daemon is running"

    # Check git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    log_success "Git repository detected"

    # Check disk space (minimum 10GB)
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=$((10 * 1024 * 1024))  # 10GB in KB
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space. Available: ${AVAILABLE_SPACE}KB, Required: ${REQUIRED_SPACE}KB"
        exit 1
    fi
    log_success "Sufficient disk space available"

    # Confirm production deployment
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warn "PRODUCTION DEPLOYMENT REQUESTED"
        read -p "Are you sure? This will affect live users. Type 'yes' to continue: " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            log_error "Deployment cancelled by user"
            exit 1
        fi
        log_success "Production deployment confirmed"
    fi
}

# =============================================================================
# PHASE 2: BACKUP CURRENT STATE
# =============================================================================

phase_backup() {
    log_info "===== PHASE 2: Backup Current State ====="

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would backup database and code"
        return
    fi

    # Backup database
    log_info "Backing up PostgreSQL database..."
    if ! docker ps | grep -q softfactory-db; then
        log_warn "Database container not running, skipping database backup"
    else
        BACKUP_FILE="${BACKUP_DIR}/softfactory_db_$(date +%Y%m%d_%H%M%S).sql"
        if docker exec softfactory-db pg_dump -U postgres softfactory > "$BACKUP_FILE"; then
            log_success "Database backed up to $BACKUP_FILE"
            gzip "$BACKUP_FILE"
            log_info "Database backup compressed"
        else
            log_error "Failed to backup database"
            return 1
        fi
    fi

    # Backup code
    log_info "Backing up application code..."
    CODE_BACKUP="${BACKUP_DIR}/softfactory_code_$(date +%Y%m%d_%H%M%S).tar.gz"
    if tar -czf "$CODE_BACKUP" \
        --exclude=.git \
        --exclude=__pycache__ \
        --exclude=.venv \
        --exclude=node_modules \
        -C "$PROJECT_ROOT" backend/ web/ requirements.txt > /dev/null 2>&1; then
        log_success "Code backed up to $CODE_BACKUP"
    else
        log_error "Failed to backup code"
        return 1
    fi

    # Backup environment file
    cp "$ENV_FILE" "${BACKUP_DIR}/.env-prod_$(date +%Y%m%d_%H%M%S)"
    log_success "Environment file backed up"
}

# =============================================================================
# PHASE 3: CODE PREPARATION
# =============================================================================

phase_code_prep() {
    log_info "===== PHASE 3: Code Preparation ====="

    # Fetch latest
    log_info "Fetching latest code from git..."
    if [ "$DRY_RUN" = false ]; then
        git fetch origin main || log_error "Failed to fetch from git"
    fi

    # Verify current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log_info "Current branch: $CURRENT_BRANCH"

    # Get git info
    COMMIT_HASH=$(git rev-parse HEAD)
    COMMIT_SHORT=$(git rev-parse --short HEAD)
    COMMIT_MESSAGE=$(git log -1 --pretty=%B)

    log_success "Git info:"
    log_success "  Hash: $COMMIT_HASH"
    log_success "  Short: $COMMIT_SHORT"
    log_success "  Message: $COMMIT_MESSAGE"
}

# =============================================================================
# PHASE 4: TESTING
# =============================================================================

phase_testing() {
    log_info "===== PHASE 4: Testing ====="

    if [ "$SKIP_TESTS" = true ]; then
        log_warn "Skipping tests (--skip-tests flag)"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would run tests"
        return
    fi

    # Run pytest
    log_info "Running pytest..."
    if [ -d "${PROJECT_ROOT}/tests" ]; then
        if docker run --rm \
            -v "${PROJECT_ROOT}:/app" \
            -w /app \
            python:3.11-slim \
            bash -c "pip install -q pytest && python -m pytest tests/ -v"; then
            log_success "Tests passed"
        else
            log_error "Tests failed"
            return 1
        fi
    else
        log_warn "No tests directory found"
    fi
}

# =============================================================================
# PHASE 5: DOCKER BUILD
# =============================================================================

phase_docker_build() {
    log_info "===== PHASE 5: Docker Build ====="

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would build Docker image"
        return
    fi

    # Build image
    log_info "Building Docker image..."
    IMAGE_TAG="softfactory:${COMMIT_SHORT}"

    if docker build \
        -f "${PROJECT_ROOT}/Dockerfile.prod" \
        -t softfactory:latest \
        -t "$IMAGE_TAG" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$COMMIT_HASH" \
        --build-arg VERSION="$COMMIT_SHORT" \
        "${PROJECT_ROOT}"; then
        log_success "Docker image built successfully: $IMAGE_TAG"
    else
        log_error "Failed to build Docker image"
        return 1
    fi
}

# =============================================================================
# PHASE 6: DEPLOYMENT
# =============================================================================

phase_deployment() {
    log_info "===== PHASE 6: Deployment ====="

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would deploy containers"
        return
    fi

    # Load environment
    set -a
    source "$ENV_FILE"
    set +a

    # Stop current services
    log_info "Stopping current services..."
    if $DOCKER_COMPOSE ps | grep -q "running"; then
        $DOCKER_COMPOSE stop web nginx || log_warn "Some services may not have been running"
    fi

    # Start services
    log_info "Starting services..."
    if ! $DOCKER_COMPOSE up -d db redis; then
        log_error "Failed to start database and redis"
        return 1
    fi

    # Wait for database
    log_info "Waiting for database to be ready (30 seconds)..."
    sleep 30

    # Run migrations
    log_info "Running database migrations..."
    if docker run --rm \
        --network "$(basename $PROJECT_ROOT)_softfactory" \
        -e DATABASE_URL="$DATABASE_URL" \
        softfactory:latest \
        flask db upgrade; then
        log_success "Database migrations completed"
    else
        log_warn "Database migrations may have failed or not needed"
    fi

    # Start API
    log_info "Starting API container..."
    if ! $DOCKER_COMPOSE up -d web nginx; then
        log_error "Failed to start API and nginx"
        return 1
    fi

    log_success "Deployment completed successfully"
}

# =============================================================================
# PHASE 7: VERIFICATION
# =============================================================================

phase_verification() {
    log_info "===== PHASE 7: Verification ====="

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would verify deployment"
        return
    fi

    # Wait for services
    log_info "Waiting for services to become ready (20 seconds)..."
    sleep 20

    # Check containers
    log_info "Checking container status..."
    $DOCKER_COMPOSE ps

    # Health check
    log_info "Running health checks..."
    MAX_RETRIES=5
    RETRY=0

    while [ $RETRY -lt $MAX_RETRIES ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API health check passed"
            break
        fi
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRIES ]; then
            log_warn "Health check failed, retrying... ($RETRY/$MAX_RETRIES)"
            sleep 5
        fi
    done

    if [ $RETRY -eq $MAX_RETRIES ]; then
        log_error "API health check failed after $MAX_RETRIES attempts"
        return 1
    fi

    # Check logs for errors
    log_info "Checking logs for errors..."
    if $DOCKER_COMPOSE logs web | grep -i "error\|exception" | head -5; then
        log_warn "Some errors found in logs (check above)"
    else
        log_success "No obvious errors in logs"
    fi

    log_success "Verification completed"
}

# =============================================================================
# ERROR HANDLING & ROLLBACK
# =============================================================================

rollback() {
    log_error "Deployment failed, initiating rollback..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would rollback"
        return
    fi

    # Stop services
    log_info "Stopping services..."
    $DOCKER_COMPOSE down

    # Find latest backup
    LATEST_DB_BACKUP=$(ls -t "${BACKUP_DIR}"/softfactory_db_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$LATEST_DB_BACKUP" ]; then
        log_error "No database backup found for rollback"
        return 1
    fi

    # Restore database
    log_info "Restoring database from backup: $LATEST_DB_BACKUP"
    if $DOCKER_COMPOSE up -d db; then
        sleep 15
        if gunzip -c "$LATEST_DB_BACKUP" | docker exec -i softfactory-db psql -U postgres softfactory; then
            log_success "Database restored successfully"
        else
            log_error "Failed to restore database"
            return 1
        fi
    fi

    # Start services
    log_info "Starting services with previous version..."
    $DOCKER_COMPOSE up -d

    log_warn "Rollback completed. Please verify system is operational."
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run phases
if phase_checks && \
   phase_backup && \
   phase_code_prep && \
   phase_testing && \
   phase_docker_build && \
   phase_deployment && \
   phase_verification; then
    log_success "===== DEPLOYMENT SUCCESSFUL ====="
    log_success "Environment: $ENVIRONMENT"
    log_success "Commit: $COMMIT_SHORT"
    log_success "Deployment time: $(date)"
    exit 0
else
    log_error "===== DEPLOYMENT FAILED ====="
    rollback
    exit 1
fi
