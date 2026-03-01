#!/bin/bash
# =============================================================================
# SoftFactory — Quick Rollback Script
#
# Restores the previous Docker image saved by deploy.sh.
#
# Usage:
#   ./scripts/rollback.sh [staging|production]
#
# Examples:
#   ./scripts/rollback.sh production    # restore last known-good image
#   ./scripts/rollback.sh staging
#
# The rollback target is the image stored in:
#   /opt/softfactory/<env>/rollback_image.txt
#
# To override the target image explicitly:
#   ROLLBACK_IMAGE=softfactory/softfactory:v1.4.0 ./scripts/rollback.sh production
# =============================================================================

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log()       { echo -e "$(date '+%H:%M:%S') ${BOLD}[$1]${NC} $2"; }
log_info()  { log "${BLUE}INFO${NC}" "$1"; }
log_ok()    { log "${GREEN} OK ${NC}" "$1"; }
log_warn()  { log "${YELLOW}WARN${NC}" "$1"; }
log_error() { log "${RED}FAIL${NC}" "$1"; }
log_step()  { echo -e "\n${BOLD}${BLUE}━━━ $1 ━━━${NC}"; }

# ── Defaults ──────────────────────────────────────────────────────────────────
ENVIRONMENT="${1:-production}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/softfactory}"
HEALTH_RETRIES="${HEALTH_RETRIES:-8}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-5}"

case "$ENVIRONMENT" in
  staging)
    APP_PORT=9001
    CONTAINER_NAME="softfactory-staging"
    ENV_FILE="$DEPLOY_DIR/staging/.env"
    ROLLBACK_FILE="$DEPLOY_DIR/staging/rollback_image.txt"
    ;;
  production)
    APP_PORT=9000
    CONTAINER_NAME="softfactory-prod"
    ENV_FILE="$DEPLOY_DIR/production/.env"
    ROLLBACK_FILE="$DEPLOY_DIR/production/rollback_image.txt"
    ;;
  *)
    log_error "Unknown environment: $ENVIRONMENT (use: staging | production)"
    exit 1
    ;;
esac

HEALTH_URL="http://localhost:${APP_PORT}/health"
LOG_FILE="$DEPLOY_DIR/$ENVIRONMENT/rollback_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$DEPLOY_DIR/$ENVIRONMENT/logs"
exec > >(tee -a "$LOG_FILE") 2>&1

# ── Determine rollback target ─────────────────────────────────────────────────
log_step "Determining Rollback Target"

# Explicit override wins
if [[ -n "${ROLLBACK_IMAGE:-}" ]]; then
  TARGET_IMAGE="$ROLLBACK_IMAGE"
  log_info "Using explicit override: $TARGET_IMAGE"
elif [[ -f "$ROLLBACK_FILE" ]]; then
  TARGET_IMAGE=$(cat "$ROLLBACK_FILE")
  if [[ -z "$TARGET_IMAGE" ]]; then
    log_error "Rollback file is empty: $ROLLBACK_FILE"
    log_error "Cannot determine previous image. Supply ROLLBACK_IMAGE=<image:tag>"
    exit 1
  fi
  log_info "Rollback target from file: $TARGET_IMAGE"
else
  log_error "No rollback file found: $ROLLBACK_FILE"
  log_error "Run deploy.sh at least once before attempting a rollback."
  exit 1
fi

# ── Confirmation ──────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}${BOLD}  ROLLBACK REQUESTED${NC}"
echo -e "${YELLOW}${BOLD}  Environment    : $ENVIRONMENT${NC}"
echo -e "${YELLOW}${BOLD}  Rolling back to: $TARGET_IMAGE${NC}"
echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [[ -t 0 ]]; then   # only prompt when run interactively
  read -r -p "Confirm rollback? [y/N] " CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    log_warn "Rollback cancelled by user."
    exit 0
  fi
fi

# ── Pull rollback image (it should already be cached, but pull to be safe) ────
log_step "Pulling Rollback Image"
if ! docker pull "$TARGET_IMAGE"; then
  log_warn "Could not pull $TARGET_IMAGE from registry — attempting with cached local image"
fi

# ── Record current image before overwriting rollback file ────────────────────
CURRENT_IMAGE=$(docker inspect "$CONTAINER_NAME" \
  --format '{{.Config.Image}}' 2>/dev/null || echo "")
if [[ -n "$CURRENT_IMAGE" ]]; then
  log_info "Current running image (will be stored as new rollback): $CURRENT_IMAGE"
  # Do NOT overwrite rollback_file here — we want to keep the last known-good
fi

# ── Stop failed container ─────────────────────────────────────────────────────
log_step "Stopping Failed Container"
docker stop "$CONTAINER_NAME" 2>/dev/null && \
  log_ok "Container stopped" || \
  log_warn "Container was not running"
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# ── Start previous image ──────────────────────────────────────────────────────
log_step "Starting Previous Version"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${APP_PORT}:9000" \
  --env-file "$ENV_FILE" \
  -e ROLLBACK=true \
  -v "$DEPLOY_DIR/$ENVIRONMENT/logs:/app/logs" \
  "$TARGET_IMAGE"

log_ok "Container started: $CONTAINER_NAME"

# ── Health check ──────────────────────────────────────────────────────────────
log_step "Verifying Rollback Health"

RETRY=0
PASSED=false
while (( RETRY < HEALTH_RETRIES )); do
  CODE=$(curl -sf --max-time 5 "$HEALTH_URL" -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
  if [[ "$CODE" == "200" ]]; then
    log_ok "Health check passed [HTTP 200] after $((RETRY + 1)) attempt(s)"
    PASSED=true
    break
  fi
  log_warn "Health check attempt $((RETRY + 1))/${HEALTH_RETRIES}: HTTP ${CODE}"
  sleep "$HEALTH_INTERVAL"
  RETRY=$(( RETRY + 1 ))
done

if [[ "$PASSED" != "true" ]]; then
  log_error "Rollback health check failed! Container is unhealthy."
  log_error "Manual intervention required. Check logs:"
  log_error "  docker logs $CONTAINER_NAME --tail=100"
  exit 1
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  ROLLBACK SUCCESSFUL${NC}"
echo -e "${GREEN}${BOLD}  Environment  : $ENVIRONMENT${NC}"
echo -e "${GREEN}${BOLD}  Restored to  : $TARGET_IMAGE${NC}"
echo -e "${GREEN}${BOLD}  Container    : $CONTAINER_NAME${NC}"
echo -e "${GREEN}${BOLD}  Health URL   : $HEALTH_URL${NC}"
echo -e "${GREEN}${BOLD}  Log file     : $LOG_FILE${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
log_warn "IMPORTANT: Investigate the failed deploy before pushing again."
log_warn "           Rollback file still points to: $TARGET_IMAGE"
