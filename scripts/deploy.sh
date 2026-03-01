#!/bin/bash
# =============================================================================
# SoftFactory — Zero-Downtime Deployment Script
#
# Usage:
#   ./scripts/deploy.sh [staging|production] [image_tag]
#
# Examples:
#   ./scripts/deploy.sh staging staging-a1b2c3d4
#   ./scripts/deploy.sh production v1.5.0
#   ./scripts/deploy.sh production          # uses image tagged 'latest'
#
# Environment variables (override defaults):
#   DEPLOY_DIR      Base directory on host  (default: /opt/softfactory)
#   HEALTH_URL      Health check URL        (default: http://localhost:PORT/health)
#   HEALTH_RETRIES  Max health-check tries  (default: 10)
#   HEALTH_INTERVAL Seconds between retries (default: 6)
#   DOCKER_IMAGE    Full image name         (default: softfactory/softfactory)
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
ENVIRONMENT="${1:-staging}"
IMAGE_TAG="${2:-latest}"
DOCKER_IMAGE="${DOCKER_IMAGE:-softfactory/softfactory}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/softfactory}"
HEALTH_RETRIES="${HEALTH_RETRIES:-10}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-6}"
COMPOSE_FILE=""
APP_PORT=""
CONTAINER_NAME=""
CANARY_PORT=""

case "$ENVIRONMENT" in
  staging)
    COMPOSE_FILE="$DEPLOY_DIR/staging/docker-compose.staging.yml"
    APP_PORT=9001
    CANARY_PORT=9003
    CONTAINER_NAME="softfactory-staging"
    ENV_FILE="$DEPLOY_DIR/staging/.env"
    ;;
  production)
    COMPOSE_FILE="$DEPLOY_DIR/production/docker-compose.production.yml"
    APP_PORT=9000
    CANARY_PORT=9002
    CONTAINER_NAME="softfactory-prod"
    ENV_FILE="$DEPLOY_DIR/production/.env"
    ;;
  *)
    log_error "Unknown environment: $ENVIRONMENT (use: staging | production)"
    exit 1
    ;;
esac

HEALTH_URL="${HEALTH_URL:-http://localhost:${APP_PORT}/health}"
FULL_IMAGE="${DOCKER_IMAGE}:${IMAGE_TAG}"
ROLLBACK_FILE="$DEPLOY_DIR/$ENVIRONMENT/rollback_image.txt"
LOG_FILE="$DEPLOY_DIR/$ENVIRONMENT/deploy_$(date +%Y%m%d_%H%M%S).log"

# ── Redirect all output to log file as well ───────────────────────────────────
mkdir -p "$DEPLOY_DIR/$ENVIRONMENT/logs"
exec > >(tee -a "$LOG_FILE") 2>&1

# ── Pre-flight ────────────────────────────────────────────────────────────────
log_step "Pre-flight Checks"

if [[ "$ENVIRONMENT" == "production" ]] && [[ -t 0 ]]; then
  echo -e "${RED}${BOLD}PRODUCTION DEPLOYMENT — THIS AFFECTS LIVE USERS${NC}"
  read -r -p "Type 'deploy' to confirm: " CONFIRM
  if [[ "$CONFIRM" != "deploy" ]]; then
    log_warn "Aborted by user."
    exit 1
  fi
fi

for cmd in docker curl; do
  command -v "$cmd" > /dev/null || { log_error "Required command not found: $cmd"; exit 1; }
done

if [[ ! -f "$ENV_FILE" ]]; then
  log_error ".env file not found: $ENV_FILE"
  exit 1
fi

DISK_FREE=$(df "$DEPLOY_DIR" | awk 'NR==2 {print $4}')
DISK_NEEDED=$((3 * 1024 * 1024))  # 3 GB in KB
if (( DISK_FREE < DISK_NEEDED )); then
  log_error "Insufficient disk space: ${DISK_FREE}KB free, ${DISK_NEEDED}KB required"
  exit 1
fi

log_ok "Pre-flight passed"

# ── Pull image ────────────────────────────────────────────────────────────────
log_step "Pulling Image"
log_info "Image: $FULL_IMAGE"

if ! docker pull "$FULL_IMAGE"; then
  log_error "Failed to pull image: $FULL_IMAGE"
  exit 1
fi
log_ok "Image pulled"

# ── Save rollback target ──────────────────────────────────────────────────────
log_step "Saving Rollback Checkpoint"
CURRENT_IMAGE=$(docker inspect "$CONTAINER_NAME" \
  --format '{{.Config.Image}}' 2>/dev/null || echo "")

if [[ -n "$CURRENT_IMAGE" ]]; then
  echo "$CURRENT_IMAGE" > "$ROLLBACK_FILE"
  log_ok "Rollback target saved: $CURRENT_IMAGE"
else
  log_warn "No running container found — this appears to be a first deploy"
  echo "" > "$ROLLBACK_FILE"
fi

# ── Canary validation ─────────────────────────────────────────────────────────
log_step "Canary Health Check (port $CANARY_PORT)"
docker stop "${CONTAINER_NAME}-canary" 2>/dev/null || true
docker rm   "${CONTAINER_NAME}-canary" 2>/dev/null || true

docker run -d \
  --name "${CONTAINER_NAME}-canary" \
  --restart no \
  -p "${CANARY_PORT}:9000" \
  --env-file "$ENV_FILE" \
  "$FULL_IMAGE"

CANARY_HEALTH="http://localhost:${CANARY_PORT}/health"
RETRY=0
PASSED=false

while (( RETRY < HEALTH_RETRIES )); do
  CODE=$(curl -sf --max-time 5 "$CANARY_HEALTH" -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
  if [[ "$CODE" == "200" ]]; then
    log_ok "Canary healthy after $((RETRY + 1)) attempt(s)"
    PASSED=true
    break
  fi
  log_warn "Canary attempt $((RETRY + 1))/${HEALTH_RETRIES}: HTTP ${CODE}"
  sleep "$HEALTH_INTERVAL"
  RETRY=$(( RETRY + 1 ))
done

docker stop "${CONTAINER_NAME}-canary" 2>/dev/null || true
docker rm   "${CONTAINER_NAME}-canary" 2>/dev/null || true

if [[ "$PASSED" != "true" ]]; then
  log_error "Canary health check failed — deployment aborted"
  exit 1
fi

# ── Traffic switch ────────────────────────────────────────────────────────────
log_step "Switching Traffic"
log_info "Stopping current container: $CONTAINER_NAME"
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm   "$CONTAINER_NAME" 2>/dev/null || true

log_info "Starting new container on port $APP_PORT"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${APP_PORT}:9000" \
  --env-file "$ENV_FILE" \
  -e GIT_SHA="${GIT_SHA:-}" \
  -e VERSION="$IMAGE_TAG" \
  -v "$DEPLOY_DIR/$ENVIRONMENT/logs:/app/logs" \
  "$FULL_IMAGE"

# ── Post-swap health check ────────────────────────────────────────────────────
log_step "Post-Swap Health Check"
sleep 5

CODE=$(curl -sf --max-time 10 "$HEALTH_URL" -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
if [[ "$CODE" != "200" ]]; then
  log_error "Post-swap health check failed [HTTP ${CODE}] — initiating automatic rollback"
  exec "$(dirname "$0")/rollback.sh" "$ENVIRONMENT"
  exit 1
fi

log_ok "Production health check passed [HTTP 200]"

# ── Cleanup old images ────────────────────────────────────────────────────────
log_step "Cleanup"
docker image prune -f 2>/dev/null || true
log_ok "Old images pruned"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  DEPLOYMENT SUCCESSFUL${NC}"
echo -e "${GREEN}${BOLD}  Environment : $ENVIRONMENT${NC}"
echo -e "${GREEN}${BOLD}  Image       : $FULL_IMAGE${NC}"
echo -e "${GREEN}${BOLD}  Container   : $CONTAINER_NAME${NC}"
echo -e "${GREEN}${BOLD}  Health URL  : $HEALTH_URL${NC}"
echo -e "${GREEN}${BOLD}  Log file    : $LOG_FILE${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
