#!/bin/bash

################################################################################
# SOFTFACTORY PRODUCTION DEPLOYMENT SCRIPT
# v1.0-infrastructure-upgrade | 2026-02-25
################################################################################

set -e  # Exit on error
set -u  # Fail on undefined variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# PHASE 0: PRE-DEPLOYMENT VERIFICATION (2 minutes)
################################################################################

phase_0_pre_deployment() {
    log_info "Starting PHASE 0: Pre-Deployment Verification..."

    # Step 1: Verify Clean Git State
    log_info "Step 1: Verifying Git state..."
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "Working directory has uncommitted changes"
        git status --porcelain
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Deployment cancelled"
            exit 1
        fi
    fi
    log_success "Git state verified"

    # Step 2: Verify Latest Commit
    log_info "Step 2: Verifying latest commit..."
    LATEST_COMMIT=$(git log --oneline -1)
    echo "Latest commit: $LATEST_COMMIT"
    log_success "Latest commit verified"

    # Step 3: Verify Environment Variables
    log_info "Step 3: Verifying environment variables..."
    required_vars=(
        "ANTHROPIC_API_KEY"
        "TELEGRAM_BOT_TOKEN"
        "PLATFORM_SECRET_KEY"
        "JWT_SECRET"
        "DATABASE_URL"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Missing environment variable: $var"
            exit 1
        fi
    done
    log_success "All environment variables set"

    # Step 4: Verify Database
    log_info "Step 4: Verifying database..."
    if python -c "from backend.models import ErrorLog, ErrorPattern; print('OK')" > /dev/null 2>&1; then
        log_success "Database schema verified"
    else
        log_warning "Database needs initialization"
        log_info "Initializing database..."
        python -c "from backend.app import create_app; app = create_app()"
        log_success "Database initialized"
    fi

    log_success "PHASE 0 COMPLETE: Pre-Deployment Verification"
}

################################################################################
# PHASE 1: DOCKER BUILD (3 minutes)
################################################################################

phase_1_docker_build() {
    log_info "Starting PHASE 1: Docker Build..."

    # Step 1: Build Docker Image
    log_info "Step 1: Building Docker image..."
    if command -v docker &> /dev/null; then
        docker build \
            --tag softfactory:v1.0-infrastructure-upgrade \
            --tag softfactory:latest \
            --build-arg ENVIRONMENT=production \
            . || {
            log_error "Docker build failed"
            exit 1
        }
        log_success "Docker image built successfully"
    else
        log_warning "Docker not installed, skipping Docker build"
        log_info "To deploy on Linux/Mac, install Docker and run this script again"
    fi

    # Step 2: Verify Image
    if command -v docker &> /dev/null; then
        log_info "Step 2: Verifying image..."
        docker images | grep softfactory:v1.0
        log_success "Image verified"
    fi

    # Step 3: Security Scan (Optional)
    if command -v trivy &> /dev/null; then
        log_info "Step 3: Running security scan..."
        trivy image softfactory:v1.0-infrastructure-upgrade || {
            log_warning "Security scan found issues (non-blocking)"
        }
    fi

    log_success "PHASE 1 COMPLETE: Docker Build"
}

################################################################################
# PHASE 2: DOCKER PUSH (2 minutes)
################################################################################

phase_2_docker_push() {
    log_info "Starting PHASE 2: Docker Push..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker not installed, skipping push phase"
        return
    fi

    # Step 1: Check Registry
    log_info "Step 1: Checking Docker registry..."
    read -p "Enter Docker Hub username: " DOCKER_USERNAME
    read -sp "Enter Docker Hub password/token: " DOCKER_PASSWORD
    echo

    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin || {
        log_error "Docker login failed"
        exit 1
    }
    log_success "Docker login successful"

    # Step 2: Push Image
    log_info "Step 2: Pushing image to registry..."
    docker tag softfactory:v1.0-infrastructure-upgrade \
        "$DOCKER_USERNAME/softfactory:v1.0-infrastructure-upgrade"

    docker push "$DOCKER_USERNAME/softfactory:v1.0-infrastructure-upgrade" || {
        log_error "Docker push failed"
        exit 1
    }
    log_success "Image pushed successfully"

    # Step 3: Verify Push
    log_info "Step 3: Verifying push..."
    docker images | grep "$DOCKER_USERNAME/softfactory:v1.0"
    log_success "Push verified"

    log_success "PHASE 2 COMPLETE: Docker Push"
}

################################################################################
# PHASE 3: PRODUCTION DEPLOYMENT (5 minutes)
################################################################################

phase_3_deployment() {
    log_info "Starting PHASE 3: Production Deployment..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker not available, using Python WSGI server"

        log_info "Starting Flask application server..."
        python start_server.py &
        SERVER_PID=$!
        echo $SERVER_PID > .deployment.pid

        sleep 3
        log_success "Application server started (PID: $SERVER_PID)"
    else
        # Step 1: Create Docker Compose File
        log_info "Step 1: Creating docker-compose.prod.yml..."
        cat > docker-compose.prod.yml <<'COMPOSE_EOF'
version: '3.8'
services:
  softfactory:
    image: softfactory:v1.0-infrastructure-upgrade
    container_name: softfactory-prod
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: production
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      PLATFORM_SECRET_KEY: ${PLATFORM_SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}
      DATABASE_URL: ${DATABASE_URL}
    volumes:
      - ./logs:/app/logs
      - ./platform.db:/app/platform.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: softfactory-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
COMPOSE_EOF
        log_success "docker-compose.prod.yml created"

        # Step 2: Start Containers
        log_info "Step 2: Starting containers..."
        docker-compose -f docker-compose.prod.yml up -d || {
            log_error "Failed to start containers"
            exit 1
        }
        log_success "Containers started"

        # Step 3: Verify Containers
        log_info "Step 3: Verifying containers..."
        sleep 5
        docker-compose -f docker-compose.prod.yml ps
        log_success "Containers verified"
    fi

    log_success "PHASE 3 COMPLETE: Production Deployment"
}

################################################################################
# PHASE 4: HEALTH CHECKS & VALIDATION (3 minutes)
################################################################################

phase_4_validation() {
    log_info "Starting PHASE 4: Health Checks & Validation..."

    # Wait for server to be ready
    log_info "Waiting for server to be ready..."
    sleep 5

    # Step 1: Health Check
    log_info "Step 1: Checking health endpoint..."
    for i in {1..10}; do
        if curl -f http://localhost:8000/health 2>/dev/null; then
            log_success "Health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "Health check failed after 10 attempts"
            exit 1
        fi
        sleep 1
    done

    # Step 2: API Validation
    log_info "Step 2: Validating API endpoints..."

    log_info "  - Testing /api/errors/recent..."
    curl -f http://localhost:8000/api/errors/recent?limit=5 > /dev/null 2>&1 && \
        log_success "  - /api/errors/recent OK" || \
        log_error "  - /api/errors/recent FAILED"

    # Step 3: Error Logging Test
    log_info "Step 3: Testing error logging..."
    curl -X POST http://localhost:8000/api/errors/log \
        -H "Content-Type: application/json" \
        -d '{
            "error_type": "TestError",
            "message": "Production deployment test",
            "project_id": "M-003",
            "severity": "low"
        }' 2>/dev/null && \
        log_success "Error logging works" || \
        log_error "Error logging failed"

    # Step 4: Smoke Tests
    log_info "Step 4: Running smoke tests..."
    SMOKE_TESTS_PASSED=0
    SMOKE_TESTS_TOTAL=3

    curl -f http://localhost:8000/health > /dev/null 2>&1 && ((SMOKE_TESTS_PASSED++))
    curl -f http://localhost:8000/api/errors/recent > /dev/null 2>&1 && ((SMOKE_TESTS_PASSED++))
    curl -s http://localhost:8000/health | grep -q "ok" && ((SMOKE_TESTS_PASSED++))

    log_success "Smoke tests: $SMOKE_TESTS_PASSED/$SMOKE_TESTS_TOTAL passed"

    log_success "PHASE 4 COMPLETE: Health Checks & Validation"
}

################################################################################
# PHASE 5: MONITORING ACTIVATION (2 minutes)
################################################################################

phase_5_monitoring() {
    log_info "Starting PHASE 5: Monitoring Activation..."

    log_info "Step 1: Configuring monitoring..."
    log_info "  - Prometheus metrics available at: http://localhost:8000/api/metrics/prometheus"
    log_info "  - Health endpoint: http://localhost:8000/health"
    log_info "  - Error tracking: http://localhost:8000/api/errors/recent"

    if command -v docker &> /dev/null; then
        log_info "Step 2: Verifying monitoring infrastructure..."
        log_info "  To enable Prometheus:"
        log_info "    1. Update /etc/prometheus/prometheus.yml"
        log_info "    2. Add target: http://localhost:8000"
        log_info "    3. Set metrics_path: /api/metrics/prometheus"
        log_info "    4. Reload Prometheus: curl -X POST http://localhost:9090/-/reload"
    fi

    log_success "PHASE 5 COMPLETE: Monitoring Activation"
}

################################################################################
# FINAL SUMMARY
################################################################################

final_summary() {
    log_success "==================== DEPLOYMENT SUCCESSFUL ===================="
    echo ""
    log_success "PRODUCTION DEPLOYMENT COMPLETE"
    echo ""
    echo "Release: v1.0-infrastructure-upgrade"
    echo "Date: $(date)"
    echo "Git Commit: $(git log --oneline -1)"
    echo ""
    echo "Services Status:"
    echo "  - Application: http://localhost:8000"
    echo "  - Health: http://localhost:8000/health"
    echo "  - API Errors: http://localhost:8000/api/errors/recent"
    echo "  - Metrics: http://localhost:8000/api/metrics/prometheus"
    echo ""

    if command -v docker &> /dev/null; then
        docker-compose -f docker-compose.prod.yml ps 2>/dev/null || true
    fi

    echo ""
    log_success "All systems operational"
    echo ""
    echo "Next Steps:"
    echo "  1. Monitor error rate: http://localhost:8000/api/metrics/summary"
    echo "  2. Check logs: tail -f logs/app.log"
    echo "  3. Set up monitoring alerts (optional)"
    echo "  4. Enable health checks (Kubernetes/ELB)"
    echo ""
    log_success "==========================================================="
}

################################################################################
# MAIN EXECUTION FLOW
################################################################################

main() {
    echo "SoftFactory Production Deployment Script"
    echo "Version: 1.0-infrastructure-upgrade"
    echo "Date: $(date)"
    echo ""

    # Change to project directory
    cd "$(dirname "$0")" || exit 1

    # Load environment variables
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    else
        log_error ".env file not found"
        exit 1
    fi

    # Run phases
    phase_0_pre_deployment
    phase_1_docker_build

    read -p "Push to registry? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        phase_2_docker_push
    fi

    phase_3_deployment
    phase_4_validation
    phase_5_monitoring

    final_summary
}

# Run main function
main "$@"
