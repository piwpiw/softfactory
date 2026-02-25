#!/bin/bash
#
# SoftFactory Production Backup Script
# Performs daily backups of database and uploads to S3 (optional)
#
# Setup cron job: 0 2 * * * /path/to/scripts/backup.sh >> /var/log/softfactory-backup.log 2>&1
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
RETENTION_DAYS=30
DOCKER_COMPOSE="docker-compose -f ${PROJECT_ROOT}/docker-compose-prod.yml"

# S3 Configuration (optional)
S3_ENABLED=${S3_ENABLED:-false}
S3_BUCKET=${S3_BUCKET:-"softfactory-backups"}
S3_REGION=${S3_REGION:-"us-east-1"}
S3_PREFIX=${S3_PREFIX:-"database"}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $@"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $@${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $@${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $@${NC}"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# =============================================================================
# DATABASE BACKUP
# =============================================================================

log "Starting database backup..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/softfactory_db_${TIMESTAMP}.sql"

# Check if database is running
if ! docker ps | grep -q softfactory-db; then
    log_error "Database container not running"
    exit 1
fi

# Perform backup
if docker exec softfactory-db pg_dump -U postgres softfactory > "$BACKUP_FILE"; then
    log_success "Database backup created: $(basename $BACKUP_FILE)"

    # Compress backup
    if gzip "$BACKUP_FILE"; then
        BACKUP_FILE="${BACKUP_FILE}.gz"
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_success "Backup compressed: $BACKUP_SIZE"
    else
        log_error "Failed to compress backup"
        exit 1
    fi
else
    log_error "Failed to create database backup"
    exit 1
fi

# =============================================================================
# BACKUP VERIFICATION
# =============================================================================

log "Verifying backup..."

# Check backup file exists and has content
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    log_error "Backup file is empty or missing"
    exit 1
fi

# Test restore (optional, commented out to avoid extra load)
# log "Testing backup restoration..."
# if docker exec softfactory-db gunzip -c "$BACKUP_FILE" | \
#    docker exec -i softfactory-db psql -U postgres --set=sslmode=require > /dev/null 2>&1; then
#     log_success "Backup restoration test passed"
# else
#     log_warn "Backup restoration test failed (this may be expected)"
# fi

log_success "Backup verification completed"

# =============================================================================
# S3 UPLOAD (optional)
# =============================================================================

if [ "$S3_ENABLED" = true ]; then
    log "Uploading backup to S3..."

    if command -v aws &> /dev/null; then
        S3_KEY="${S3_PREFIX}/$(basename $BACKUP_FILE)"

        if aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_KEY}" \
            --region "$S3_REGION" \
            --sse AES256 \
            --metadata "backup-date=$(date +'%Y-%m-%d'),database=softfactory"; then
            log_success "Backup uploaded to S3: s3://${S3_BUCKET}/${S3_KEY}"
        else
            log_warn "Failed to upload backup to S3"
        fi
    else
        log_warn "AWS CLI not found, skipping S3 upload"
    fi
fi

# =============================================================================
# LOCAL RETENTION POLICY
# =============================================================================

log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

CLEANUP_COUNT=0
while IFS= read -r OLD_BACKUP; do
    if rm -f "$OLD_BACKUP"; then
        CLEANUP_COUNT=$((CLEANUP_COUNT + 1))
        log "Deleted old backup: $(basename $OLD_BACKUP)"
    fi
done < <(find "$BACKUP_DIR" -name "softfactory_db_*.sql.gz" -type f -mtime +$RETENTION_DAYS)

log_success "Cleaned up $CLEANUP_COUNT old backups"

# =============================================================================
# BACKUP LISTING
# =============================================================================

log "Recent backups:"
ls -lh "$BACKUP_DIR"/softfactory_db_*.sql.gz 2>/dev/null | tail -5 || log_warn "No backups found"

# =============================================================================
# NOTIFICATION
# =============================================================================

# Optional: Send notification email
if [ ! -z "$BACKUP_NOTIFICATION_EMAIL" ]; then
    log "Sending backup notification..."

    if command -v mail &> /dev/null; then
        mail -s "SoftFactory Backup Complete - $(date +'%Y-%m-%d')" \
            "$BACKUP_NOTIFICATION_EMAIL" << EOF
Backup Status: SUCCESS

Backup File: $(basename $BACKUP_FILE)
Backup Size: $BACKUP_SIZE
Backup Time: $(date)
Retention Policy: $RETENTION_DAYS days

Database: softfactory
Host: $(hostname)
EOF
        log_success "Notification email sent"
    fi
fi

log_success "===== BACKUP COMPLETE ====="
