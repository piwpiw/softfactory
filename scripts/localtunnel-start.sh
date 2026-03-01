#!/bin/bash
#
# SoftFactory localtunnel Fallback Tunnel Script
# Provides backup public access when ngrok is unavailable
#
# localtunnel is a simpler alternative to ngrok with fewer features but
# useful as a fallback for quick public access
#
# Usage: ./scripts/localtunnel-start.sh [options]
# Options:
#   --subdomain NAME    Custom subdomain (optional, localtunnel generates if not provided)
#   --port PORT         Local port (default: 8000)
#   --log-file PATH     Log file location
#   --help              Show this help message
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
LOG_FILE="${LOG_DIR}/localtunnel.log"
URL_FILE="${LOG_DIR}/localtunnel-url.txt"

# Defaults
LOCAL_PORT=8000
CUSTOM_SUBDOMAIN=""
HELP=false

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

usage() {
    cat << EOF
Usage: $0 [options]

SoftFactory localtunnel backup tunnel (fallback for ngrok)

Options:
    --subdomain NAME    Custom subdomain (e.g., 'softfactory-demo')
    --port PORT         Local port to tunnel (default: 8000)
    --log-file PATH     Log file location
    --help              Show this help message

Examples:
    # Start with default settings (random subdomain)
    ./scripts/localtunnel-start.sh

    # Start with custom subdomain
    ./scripts/localtunnel-start.sh --subdomain softfactory-demo

    # Start on different port
    ./scripts/localtunnel-start.sh --port 3000

Notes:
    - localtunnel requires Node.js and npm to be installed
    - Install with: npm install -g localtunnel
    - Public URL will be: https://[subdomain].loca.lt

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --subdomain)
            CUSTOM_SUBDOMAIN="$2"
            shift 2
            ;;
        --port)
            LOCAL_PORT="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
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
mkdir -p "$LOG_DIR"

log_info "========================================="
log_info "SoftFactory localtunnel Fallback Tunnel"
log_info "========================================="

# Check dependencies
if ! command -v lt &> /dev/null; then
    log_error "localtunnel (lt) is not installed"
    log_info "Install with: npm install -g localtunnel"
    exit 1
fi

LT_VERSION=$(lt --version 2>/dev/null || echo "unknown")
log_info "localtunnel version: $LT_VERSION"

# Check Flask app
log_info "Checking Flask app on port $LOCAL_PORT..."
if ! curl -sf "http://localhost:$LOCAL_PORT/health" > /dev/null 2>&1; then
    log_warn "Flask app not responding on http://localhost:$LOCAL_PORT"
    log_warn "Please start the Flask app first"
    exit 1
fi

log_success "Flask app is healthy"

# Build localtunnel command
LT_CMD="lt --port $LOCAL_PORT"

if [ -n "$CUSTOM_SUBDOMAIN" ]; then
    LT_CMD="$LT_CMD --subdomain $CUSTOM_SUBDOMAIN"
    log_info "Custom subdomain: $CUSTOM_SUBDOMAIN"
else
    log_info "Using random subdomain (will be shown in output)"
fi

# Start localtunnel
log_info "Starting localtunnel..."

# Create a wrapper to capture the URL
(
    $LT_CMD 2>&1 | tee -a "$LOG_FILE" | while IFS= read -r line; do
        if [[ $line == *"https://"* ]]; then
            # Extract URL and save to file
            url=$(echo "$line" | grep -oE 'https://[^[:space:]]+' | head -1)
            if [ -n "$url" ]; then
                echo "$url" > "$URL_FILE"
                log_success "Public URL: $url"
                log_success "Web interface: $url"
            fi
        fi
    done
) &

# Wait for tunnel to establish
sleep 3

# Check if URL file was created
if [ -f "$URL_FILE" ]; then
    URL=$(cat "$URL_FILE")
    log_success "========================================="
    log_success "localtunnel Tunnel Active"
    log_success "========================================="
    log_success "Public URL: $URL"
    log_success "Local Port: $LOCAL_PORT"
    log_success "========================================="
else
    log_warn "Could not determine public URL"
    log_info "Check the log file: $LOG_FILE"
fi

# Keep the script running
log_info "Tunnel is running. Press Ctrl+C to stop."
wait
