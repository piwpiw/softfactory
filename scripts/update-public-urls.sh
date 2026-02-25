#!/bin/bash
#
# SoftFactory Update Public URLs Script
# Automatically updates public URLs in configuration and notifies systems
#
# This script:
# 1. Fetches current ngrok/localtunnel URLs
# 2. Updates environment configuration
# 3. Notifies backend services
# 4. Updates DNS/web configs (if configured)
# 5. Sends notifications (email, webhook, Telegram)
#
# Usage: ./scripts/update-public-urls.sh [options]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/url-updates.log"
NGROK_URL_FILE="${LOG_DIR}/ngrok-url.txt"
LOCALTUNNEL_URL_FILE="${LOG_DIR}/localtunnel-url.txt"
CONFIG_DIR="${PROJECT_ROOT}"
PUBLIC_URLS_FILE="${CONFIG_DIR}/public-urls.json"

# Functions
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[${timestamp}] INFO${NC} $@" | tee -a "$LOG_FILE"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}] SUCCESS${NC} $@" | tee -a "$LOG_FILE"
}

log_warn() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}] WARN${NC} $@" | tee -a "$LOG_FILE"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[${timestamp}] ERROR${NC} $@" | tee -a "$LOG_FILE"
}

# Setup
mkdir -p "$LOG_DIR"

log_info "========================================="
log_info "SoftFactory Public URL Update Script"
log_info "========================================="

# Fetch ngrok URL
fetch_ngrok_url() {
    if [ -f "$NGROK_URL_FILE" ]; then
        local url=$(cat "$NGROK_URL_FILE" 2>/dev/null | head -1)
        if [ -n "$url" ] && [ "$url" != "null" ]; then
            echo "$url"
            return 0
        fi
    fi

    # Try ngrok API
    if curl -sf http://127.0.0.1:4040/api/tunnels 2>/dev/null | \
       jq -e '.tunnels[0].public_url' > /dev/null 2>&1; then
        curl -s http://127.0.0.1:4040/api/tunnels | \
            jq -r '.tunnels[] | select(.proto == "http") | .public_url' | head -1
        return 0
    fi

    return 1
}

# Fetch localtunnel URL
fetch_localtunnel_url() {
    if [ -f "$LOCALTUNNEL_URL_FILE" ]; then
        local url=$(cat "$LOCALTUNNEL_URL_FILE" 2>/dev/null | head -1)
        if [ -n "$url" ] && [ "$url" != "null" ]; then
            echo "$url"
            return 0
        fi
    fi
    return 1
}

# Update public URLs JSON
update_urls_file() {
    local ngrok_url="$1"
    local localtunnel_url="$2"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$PUBLIC_URLS_FILE" << EOF
{
  "timestamp": "$timestamp",
  "primary": {
    "type": "ngrok",
    "url": "${ngrok_url:-null}",
    "status": "$([ -n "$ngrok_url" ] && echo "active" || echo "inactive")",
    "updated": "$timestamp"
  },
  "fallback": {
    "type": "localtunnel",
    "url": "${localtunnel_url:-null}",
    "status": "$([ -n "$localtunnel_url" ] && echo "active" || echo "inactive")",
    "updated": "$timestamp"
  },
  "local": {
    "url": "http://localhost:8000",
    "status": "active"
  },
  "web_inspector": {
    "ngrok": "http://127.0.0.1:4040",
    "api": "http://127.0.0.1:4041"
  }
}
EOF

    log_success "URLs file updated: $PUBLIC_URLS_FILE"
}

# Update backend configuration
update_backend_config() {
    local ngrok_url="$1"
    local localtunnel_url="$2"

    if [ -n "$ngrok_url" ]; then
        log_info "Notifying backend of new URL: $ngrok_url"

        # Call backend API to update CORS and configuration
        curl -X POST "http://localhost:8000/api/admin/public-url-update" \
            -H "Content-Type: application/json" \
            -d "{\"url\": \"$ngrok_url\", \"type\": \"ngrok\"}" \
            2>/dev/null || log_warn "Failed to notify backend of URL update"
    fi

    if [ -n "$localtunnel_url" ]; then
        log_info "Notifying backend of fallback URL: $localtunnel_url"

        curl -X POST "http://localhost:8000/api/admin/public-url-update" \
            -H "Content-Type: application/json" \
            -d "{\"url\": \"$localtunnel_url\", \"type\": \"localtunnel\"}" \
            2>/dev/null || log_warn "Failed to notify backend of fallback URL"
    fi
}

# Send notifications
send_notifications() {
    local ngrok_url="$1"
    local localtunnel_url="$2"

    # Log to file
    log_success "Public URLs updated"
    log_success "Primary (ngrok): ${ngrok_url:-not available}"
    log_success "Fallback (localtunnel): ${localtunnel_url:-not available}"

    # Telegram notification (if configured)
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        local message="SoftFactory public URLs updated:\n"
        if [ -n "$ngrok_url" ]; then
            message="${message}📡 Primary: $ngrok_url\n"
        fi
        if [ -n "$localtunnel_url" ]; then
            message="${message}🔄 Fallback: $localtunnel_url\n"
        fi
        message="${message}🕐 $(date '+%Y-%m-%d %H:%M:%S UTC')"

        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=$(echo -e $message)" \
            -d "parse_mode=Markdown" > /dev/null 2>&1 || \
            log_warn "Failed to send Telegram notification"
    fi

    # Webhook notification (if configured)
    if [ -n "$PUBLIC_URL_WEBHOOK" ]; then
        log_info "Sending webhook notification..."
        curl -X POST "$PUBLIC_URL_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"ngrok_url\": \"$ngrok_url\", \"localtunnel_url\": \"$localtunnel_url\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
            2>/dev/null || log_warn "Failed to send webhook notification"
    fi
}

# Main execution
log_info "Fetching current public URLs..."

NGROK_URL=""
LOCALTUNNEL_URL=""

# Try to fetch URLs
if NGROK_URL=$(fetch_ngrok_url); then
    log_success "ngrok URL found: $NGROK_URL"
else
    log_warn "ngrok URL not available"
fi

if LOCALTUNNEL_URL=$(fetch_localtunnel_url); then
    log_success "localtunnel URL found: $LOCALTUNNEL_URL"
else
    log_warn "localtunnel URL not available"
fi

# Check if at least one URL is available
if [ -z "$NGROK_URL" ] && [ -z "$LOCALTUNNEL_URL" ]; then
    log_error "No public URLs available"
    log_error "Please start ngrok or localtunnel first"
    exit 1
fi

# Update files
update_urls_file "$NGROK_URL" "$LOCALTUNNEL_URL"

# Update backend
update_backend_config "$NGROK_URL" "$LOCALTUNNEL_URL"

# Send notifications
send_notifications "$NGROK_URL" "$LOCALTUNNEL_URL"

log_success "========================================="
log_success "URL Update Complete"
log_success "========================================="

# Display summary
log_info "Public URLs Summary:"
if [ -n "$NGROK_URL" ]; then
    log_info "  Primary (ngrok):  $NGROK_URL"
fi
if [ -n "$LOCALTUNNEL_URL" ]; then
    log_info "  Fallback (lt):    $LOCALTUNNEL_URL"
fi
log_info "  Local:            http://localhost:8000"
log_info "  Config file:      $PUBLIC_URLS_FILE"

exit 0
