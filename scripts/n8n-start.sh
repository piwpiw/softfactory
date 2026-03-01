#!/bin/bash
# =============================================================
# n8n Automation Startup Script
# =============================================================
# Purpose: Start n8n with proper configuration and error handling
# Usage:   bash scripts/n8n-start.sh [--headless] [--debug]
# =============================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
N8N_HOME="${PROJECT_ROOT}/.n8n"
N8N_LOG_DIR="${PROJECT_ROOT}/logs/n8n"
ENV_FILE="${PROJECT_ROOT}/.env.n8n"
ENV_TEMPLATE="${PROJECT_ROOT}/n8n/environment-template.env"
N8N_PORT=5678
N8N_UI_PORT=5679

# Functions
print_header() {
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
  print_header "Step 1: Checking Prerequisites"

  # Check Node.js
  if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    echo "Please install Node.js v18+ from https://nodejs.org"
    exit 1
  fi
  NODE_VERSION=$(node -v)
  print_success "Node.js found: $NODE_VERSION"

  # Check npm
  if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
  fi
  NPM_VERSION=$(npm -v)
  print_success "npm found: $NPM_VERSION"

  # Check Python (for reporting integration)
  if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 not found (optional, needed for advanced reporting)"
  else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python 3 found: $PYTHON_VERSION"
  fi

  # Check ports availability
  print_info "Checking port availability..."
  if nc -z localhost $N8N_PORT 2>/dev/null; then
    print_warning "Port $N8N_PORT is already in use"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  else
    print_success "Port $N8N_PORT is available"
  fi
}

setup_directories() {
  print_header "Step 2: Setting Up Directories"

  # Create necessary directories
  mkdir -p "$N8N_HOME"
  mkdir -p "$N8N_LOG_DIR"
  mkdir -p "${PROJECT_ROOT}/n8n/credentials"
  mkdir -p "${PROJECT_ROOT}/n8n/workflows"
  mkdir -p "${PROJECT_ROOT}/n8n/backups"

  print_success "Created n8n home: $N8N_HOME"
  print_success "Created log directory: $N8N_LOG_DIR"
}

setup_environment() {
  print_header "Step 3: Setting Up Environment Variables"

  if [ ! -f "$ENV_FILE" ]; then
    print_warning "Environment file not found: $ENV_FILE"
    print_info "Creating from template..."

    if [ ! -f "$ENV_TEMPLATE" ]; then
      print_error "Template file not found: $ENV_TEMPLATE"
      exit 1
    fi

    cp "$ENV_TEMPLATE" "$ENV_FILE"
    print_success "Created $ENV_FILE from template"

    print_warning "⚠  IMPORTANT: You must configure the following before running n8n:"
    echo ""
    echo "1. Gmail OAuth 2.0:"
    echo "   - Go to: https://console.cloud.google.com"
    echo "   - Create OAuth 2.0 credentials (Desktop application)"
    echo "   - Download JSON file and set: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET"
    echo "   - Run initial auth flow to get GMAIL_REFRESH_TOKEN"
    echo ""
    echo "2. Notion API:"
    echo "   - Go to: https://www.notion.so/my-integrations"
    echo "   - Create new integration"
    echo "   - Copy API key to NOTION_API_KEY"
    echo "   - Share your database with the integration"
    echo "   - Set NOTION_DATABASE_ID"
    echo ""
    echo "3. Telegram:"
    echo "   - Talk to @BotFather on Telegram"
    echo "   - Get your bot token (TELEGRAM_BOT_TOKEN)"
    echo "   - Your chat ID is: TELEGRAM_CHAT_ID"
    echo ""
    echo "4. Security:"
    echo "   - Set random N8N_JWT_SECRET (min 32 chars)"
    echo "   - Set random N8N_ENCRYPTION_KEY (min 32 chars)"
    echo ""
    echo "Edit $ENV_FILE and fill in all values marked as 'your_...'"
    echo ""
    read -p "Press Enter once you've configured the environment file..."
  else
    print_success "Environment file found: $ENV_FILE"
  fi

  # Load environment variables
  set -a
  source "$ENV_FILE"
  set +a
  print_success "Loaded environment variables from $ENV_FILE"
}

install_n8n() {
  print_header "Step 4: Installing/Updating n8n"

  print_info "Checking n8n installation..."

  if command -v n8n &> /dev/null; then
    N8N_VERSION=$(n8n --version 2>/dev/null || echo "unknown")
    print_success "n8n found: $N8N_VERSION"

    read -p "Update n8n to latest version? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      print_info "Updating n8n..."
      npm install -g n8n@latest
      print_success "n8n updated"
    fi
  else
    print_info "Installing n8n globally..."
    npm install -g n8n
    print_success "n8n installed successfully"
  fi
}

import_workflows() {
  print_header "Step 5: Importing Workflows"

  WORKFLOWS_DIR="${PROJECT_ROOT}/n8n/workflows"

  if [ ! -d "$WORKFLOWS_DIR" ]; then
    print_warning "Workflows directory not found: $WORKFLOWS_DIR"
    return
  fi

  # Count JSON workflows
  WORKFLOW_COUNT=$(find "$WORKFLOWS_DIR" -name "*.json" | wc -l)

  if [ "$WORKFLOW_COUNT" -gt 0 ]; then
    print_info "Found $WORKFLOW_COUNT workflow(s) to import"
    print_info "Workflows will be imported when n8n starts"
    print_info "Location: $WORKFLOWS_DIR"
  else
    print_warning "No workflows found in $WORKFLOWS_DIR"
    print_info "You can import workflows via the n8n UI or manually place .json files"
  fi
}

create_systemd_service() {
  print_header "Step 6: Optional - Create SystemD Service"

  if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    read -p "Create systemd service for n8n? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      print_info "Creating systemd service..."

      sudo tee /etc/systemd/system/n8n.service > /dev/null <<EOF
[Unit]
Description=n8n Workflow Automation
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT
EnvironmentFile=$ENV_FILE
ExecStart=$(which n8n) start
Restart=on-failure
RestartSec=10
StandardOutput=append:$N8N_LOG_DIR/n8n.log
StandardError=append:$N8N_LOG_DIR/n8n.error.log

[Install]
WantedBy=multi-user.target
EOF

      sudo systemctl daemon-reload
      print_success "SystemD service created"
      print_info "To start: sudo systemctl start n8n"
      print_info "To enable on boot: sudo systemctl enable n8n"
      print_info "To check status: sudo systemctl status n8n"
    fi
  fi
}

validate_configuration() {
  print_header "Step 7: Validating Configuration"

  local ERRORS=0

  # Check required environment variables
  if [ -z "$GMAIL_CLIENT_ID" ] || [ "$GMAIL_CLIENT_ID" = "your_google_client_id_here.apps.googleusercontent.com" ]; then
    print_warning "GMAIL_CLIENT_ID not configured"
    ERRORS=$((ERRORS+1))
  else
    print_success "GMAIL_CLIENT_ID configured"
  fi

  if [ -z "$NOTION_API_KEY" ] || [ "$NOTION_API_KEY" = "ntn_your_notion_api_key_here" ]; then
    print_warning "NOTION_API_KEY not configured"
    ERRORS=$((ERRORS+1))
  else
    print_success "NOTION_API_KEY configured"
  fi

  if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    print_warning "TELEGRAM_BOT_TOKEN not configured"
    ERRORS=$((ERRORS+1))
  else
    print_success "TELEGRAM_BOT_TOKEN configured"
  fi

  if [ -z "$N8N_JWT_SECRET" ] || [ ${#N8N_JWT_SECRET} -lt 32 ]; then
    print_warning "N8N_JWT_SECRET not configured or too short (min 32 chars)"
    ERRORS=$((ERRORS+1))
  else
    print_success "N8N_JWT_SECRET configured"
  fi

  if [ "$ERRORS" -gt 0 ]; then
    print_warning "Configuration incomplete - $ERRORS issue(s) found"
    print_info "Please update $ENV_FILE with required credentials"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  else
    print_success "Configuration validated"
  fi
}

start_n8n() {
  print_header "Step 8: Starting n8n"

  # Set environment variables
  set -a
  source "$ENV_FILE"
  set +a

  # Export n8n specific variables
  export N8N_PORT=$N8N_PORT
  export N8N_EDITOR_PORT=$N8N_UI_PORT
  export N8N_LOG_LEVEL=${N8N_LOG_LEVEL:-info}
  export DB_SQLITE_PATH="${N8N_HOME}/database.sqlite"
  export NODE_ENV=production

  print_info "Starting n8n..."
  print_info "API:  http://localhost:$N8N_PORT"
  print_info "UI:   http://localhost:$N8N_UI_PORT"
  print_info "Logs: $N8N_LOG_DIR"
  echo ""

  # Check if headless mode requested
  if [[ "$*" == *"--headless"* ]]; then
    print_info "Starting in headless mode..."
    n8n start --headless >> "$N8N_LOG_DIR/n8n.log" 2>&1 &
    echo $! > "$N8N_HOME/n8n.pid"
    print_success "n8n started in background (PID: $!)"
    print_info "To view logs: tail -f $N8N_LOG_DIR/n8n.log"
  else
    # Start in foreground with debug output
    if [[ "$*" == *"--debug"* ]]; then
      print_info "Starting with debug logging..."
      export N8N_LOG_LEVEL=debug
    fi

    n8n start
  fi
}

show_next_steps() {
  print_header "Setup Complete!"

  echo ""
  print_success "n8n is ready to use!"
  echo ""
  echo "Next Steps:"
  echo "1. Open the n8n Editor: http://localhost:$N8N_UI_PORT"
  echo "2. Create your admin user account"
  echo "3. Import workflows from: ${PROJECT_ROOT}/n8n/workflows/"
  echo "4. Configure webhook URLs for incoming triggers"
  echo "5. Set up credentials for Gmail, Notion, and Telegram"
  echo "6. Test the daily report workflow"
  echo ""
  echo "Useful Commands:"
  echo "  View logs:       tail -f $N8N_LOG_DIR/n8n.log"
  echo "  Stop n8n:        kill \$(cat ${N8N_HOME}/n8n.pid)"
  echo "  Export workflow: n8n export:workflow --id=workflow_id > backup.json"
  echo "  Import workflow: n8n import:workflow --input=workflow.json"
  echo ""
  echo "Documentation:"
  echo "  n8n Docs:        https://docs.n8n.io"
  echo "  API Reference:   https://docs.n8n.io/api/"
  echo "  Community Forum: https://community.n8n.io"
  echo ""
}

# Main execution
main() {
  print_header "n8n Automation Setup Script"
  echo "Project Root: $PROJECT_ROOT"
  echo "Started: $(date)"
  echo ""

  # Run setup steps
  check_prerequisites
  setup_directories
  setup_environment
  install_n8n
  import_workflows
  validate_configuration
  create_systemd_service

  echo ""
  show_next_steps

  # Ask to start n8n
  read -p "Start n8n now? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    start_n8n "$@"
  else
    print_info "To start n8n later, run: bash scripts/n8n-start.sh"
  fi
}

# Run main
main "$@"
