#!/bin/bash
#
# SoftFactory ngrok Startup Script with Auto-Reconnect
# Manages ngrok tunnel lifecycle with health checks and automatic recovery
#
# Usage: ./scripts/ngrok-start.sh [options]
# Options:
#   --authtoken TOKEN    Set ngrok auth token
#   --custom-domain NAME Set custom domain (Pro plan required)
#   --ip-whitelist IPS   Comma-separated IP list for access control
#   --monitor           Enable continuous monitoring mode
#   --log-file PATH     Log file location (default: logs/ngrok.log)
#   --config PATH       Custom ngrok config file
#   --help              Show this help message
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NGROK_CONFIG="${PROJECT_ROOT}/.ngrok.yml"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/ngrok.log"
PID_FILE="${LOG_DIR}/ngrok.pid"
URL_FILE="${LOG_DIR}/ngrok-url.txt"
HISTORY_FILE="${LOG_DIR}/ngrok-history.json"

# Defaults
AUTHTOKEN=""
CUSTOM_DOMAIN=""
IP_WHITELIST=""
MONITOR_MODE=false
CHECK_INTERVAL=30
MAX_RESTARTS=5
RESTART_DELAY=10

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

SoftFactory ngrok tunnel management with auto-reconnect

Options:
    --authtoken TOKEN      Set ngrok authentication token
    --custom-domain NAME   Custom domain (Pro plan required)
    --ip-whitelist IPS     Comma-separated IP list (e.g., "1.2.3.4,5.6.7.8")
    --monitor              Enable continuous monitoring mode
    --log-file PATH        Custom log file location
    --config PATH          Custom ngrok config file
    --help                 Show this help message

Environment Variables:
    NGROK_AUTHTOKEN        ngrok authentication token (alternative to --authtoken)
    NGROK_CUSTOM_DOMAIN    Custom domain (alternative to --custom-domain)

Examples:
    # Start with default config
    ./scripts/ngrok-start.sh

    # Start with auth token and monitoring
    ./scripts/ngrok-start.sh --authtoken <token> --monitor

    # Start with custom domain and IP whitelist
    ./scripts/ngrok-start.sh --custom-domain softfactory.ngrok.io --ip-whitelist "1.2.3.4,5.6.7.8"

    # Start in monitoring mode (continuous health checks)
    ./scripts/ngrok-start.sh --monitor

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --authtoken)
            AUTHTOKEN="$2"
            shift 2
            ;;
        --custom-domain)
            CUSTOM_DOMAIN="$2"
            shift 2
            ;;
        --ip-whitelist)
            IP_WHITELIST="$2"
            shift 2
            ;;
        --monitor)
            MONITOR_MODE=true
            shift
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --config)
            NGROK_CONFIG="$2"
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

# Use environment variables if not set via arguments
AUTHTOKEN="${AUTHTOKEN:-${NGROK_AUTHTOKEN}}"
CUSTOM_DOMAIN="${CUSTOM_DOMAIN:-${NGROK_CUSTOM_DOMAIN}}"

# Setup directories
mkdir -p "$LOG_DIR"

log_info "========================================="
log_info "SoftFactory ngrok Tunnel Manager v1.0"
log_info "========================================="
log_info "Project Root: $PROJECT_ROOT"
log_info "Config File: $NGROK_CONFIG"
log_info "Log File: $LOG_FILE"
log_info "PID File: $PID_FILE"
log_info "URL File: $URL_FILE"

# Check ngrok installation
if ! command -v ngrok &> /dev/null; then
    log_error "ngrok is not installed or not in PATH"
    log_info "Install ngrok: https://ngrok.com/download"
    exit 1
fi

NGROK_VERSION=$(ngrok version)
log_info "ngrok Version: $NGROK_VERSION"

# Check Flask app is running
check_flask_health() {
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Set ngrok auth token
setup_authtoken() {
    if [ -n "$AUTHTOKEN" ]; then
        log_info "Setting ngrok authtoken..."
        if ngrok authtoken "$AUTHTOKEN" > /dev/null 2>&1; then
            log_success "Auth token configured"
        else
            log_error "Failed to set auth token"
            return 1
        fi
    else
        log_warn "No auth token provided (using anonymous tunnel)"
        log_warn "Feature limitations: dynamic subdomains, no IP restriction"
    fi
}

# Fetch current tunnel URL
fetch_tunnel_url() {
    local api_url="http://127.0.0.1:4040/api/tunnels"
    local retries=5
    local count=0

    while [ $count -lt $retries ]; do
        if curl -sf "$api_url" > /tmp/ngrok_api.json 2>/dev/null; then
            local public_url=$(jq -r '.tunnels[0].public_url' /tmp/ngrok_api.json 2>/dev/null)
            if [ -n "$public_url" ] && [ "$public_url" != "null" ]; then
                echo "$public_url"
                return 0
            fi
        fi
        count=$((count + 1))
        sleep 1
    done

    return 1
}

# Save tunnel URL to file for other processes to read
save_tunnel_url() {
    local url="$1"
    if [ -n "$url" ]; then
        echo "$url" > "$URL_FILE"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "{\"url\": \"$url\", \"timestamp\": \"$timestamp\"}" > "$HISTORY_FILE"
        log_success "Tunnel URL saved: $url"
        return 0
    fi
    return 1
}

# Display tunnel info
display_tunnel_info() {
    local url=$(fetch_tunnel_url)
    if [ $? -eq 0 ]; then
        log_success "========================================="
        log_success "ngrok Tunnel Active"
        log_success "========================================="
        log_success "Public URL: $url"
        log_success "Web Inspector: http://127.0.0.1:4040"
        log_success "API Endpoint: http://127.0.0.1:4041"
        log_success "Local Address: http://localhost:8000"
        log_success "========================================="
        save_tunnel_url "$url"
        return 0
    else
        log_warn "Could not retrieve tunnel URL"
        return 1
    fi
}

# Health check with auto-recovery
health_check_loop() {
    local restart_count=0

    while true; do
        sleep "$CHECK_INTERVAL"

        # Check if ngrok process is still running
        if ! kill -0 "$(cat $PID_FILE 2>/dev/null)" 2>/dev/null; then
            log_error "ngrok process died unexpectedly"
            restart_count=$((restart_count + 1))

            if [ $restart_count -gt $MAX_RESTARTS ]; then
                log_error "Max restart attempts ($MAX_RESTARTS) exceeded"
                exit 1
            fi

            log_warn "Attempting restart ($restart_count/$MAX_RESTARTS)..."
            sleep "$RESTART_DELAY"
            start_ngrok_tunnel
            continue
        fi

        # Check Flask app health
        if check_flask_health; then
            # Verify tunnel URL still accessible
            if fetch_tunnel_url > /dev/null; then
                log_info "Health check passed (Flask: OK, Tunnel: OK)"
                restart_count=0
            else
                log_warn "Tunnel URL unreachable, but ngrok process running"
            fi
        else
            log_warn "Flask app health check failed"
        fi

        # Check ngrok API endpoint
        if ! curl -sf http://127.0.0.1:4040/api/tunnels > /dev/null 2>&1; then
            log_warn "ngrok API endpoint unreachable"
        fi
    done
}

# Start ngrok tunnel
start_ngrok_tunnel() {
    log_info "Starting ngrok tunnel..."

    # Build ngrok command
    local ngrok_cmd="ngrok start softfactory"

    if [ -f "$NGROK_CONFIG" ]; then
        ngrok_cmd="$ngrok_cmd --config $NGROK_CONFIG"
    fi

    # Start tunnel in background
    if $ngrok_cmd > "$LOG_FILE" 2>&1 & then
        local ngrok_pid=$!
        echo "$ngrok_pid" > "$PID_FILE"
        log_success "ngrok started (PID: $ngrok_pid)"

        # Wait for tunnel to establish
        sleep 3

        # Display tunnel info
        if display_tunnel_info; then
            log_success "ngrok tunnel established successfully"
            return 0
        else
            log_error "Failed to establish tunnel"
            kill "$ngrok_pid" 2>/dev/null || true
            return 1
        fi
    else
        log_error "Failed to start ngrok"
        return 1
    fi
}

# Cleanup on exit
cleanup() {
    log_info "Shutting down ngrok tunnel..."
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill "$pid" 2>/dev/null; then
            log_success "ngrok process terminated (PID: $pid)"
        fi
        rm -f "$PID_FILE"
    fi
    log_info "Cleanup complete"
}

trap cleanup EXIT INT TERM

# Main execution
log_info "Checking prerequisites..."

# Check Flask app
if ! check_flask_health; then
    log_warn "Flask app not responding on http://localhost:8000"
    log_warn "Please start the Flask app first: python start_platform.py"
    log_info "Waiting for Flask app to become available..."

    local retries=30
    local count=0
    while [ $count -lt $retries ]; do
        if check_flask_health; then
            log_success "Flask app is now available"
            break
        fi
        count=$((count + 1))
        sleep 2
    done

    if [ $count -eq $retries ]; then
        log_error "Flask app failed to start after $((retries * 2)) seconds"
        exit 1
    fi
fi

log_success "Flask app is healthy"

# Setup auth token if provided
if [ -n "$AUTHTOKEN" ]; then
    if ! setup_authtoken; then
        log_error "Failed to setup auth token"
        exit 1
    fi
fi

# Start ngrok tunnel
if ! start_ngrok_tunnel; then
    log_error "Failed to start ngrok tunnel"
    exit 1
fi

# Enter monitoring loop if requested
if [ "$MONITOR_MODE" = true ]; then
    log_info "Entering monitoring mode (Ctrl+C to exit)"
    log_info "Health checks every $CHECK_INTERVAL seconds"
    log_info "Auto-restart on failure (max $MAX_RESTARTS attempts)"
    health_check_loop
else
    log_info "Tunnel is running. Press Ctrl+C to stop."
    log_info "Web inspector: http://127.0.0.1:4040"
    log_info "Tunnel URL saved to: $URL_FILE"

    # Keep the script running
    wait $(cat "$PID_FILE" 2>/dev/null)
fi
