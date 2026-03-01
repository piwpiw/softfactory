#!/bin/bash
#
# Enhanced SoftFactory Health Check Script
# Comprehensive system health verification with detailed reporting
#
# Usage: ./scripts/health-check-enhanced.sh [--json] [--verbose] [--slack] [--email]
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
REPORT_FILE="${LOG_DIR}/health-report_$(date +%Y%m%d_%H%M%S).json"

# Options
OUTPUT_JSON=false
VERBOSE=false
SEND_SLACK=false
SEND_EMAIL=false
EXIT_CODE=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize report
mkdir -p "$LOG_DIR"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            OUTPUT_JSON=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --slack)
            SEND_SLACK=true
            shift
            ;;
        --email)
            SEND_EMAIL=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Track all checks
declare -A HEALTH_STATUS
declare -a CHECK_RESULTS

# Function to print header
print_header() {
    if [ "$OUTPUT_JSON" = false ]; then
        echo ""
        echo -e "${BLUE}=== $1 ===${NC}"
    fi
}

# Function to print status
print_status() {
    local name=$1
    local status=$2
    local details=$3
    local metric=$4

    if [ "$OUTPUT_JSON" = true ]; then
        echo "{\"check\": \"$name\", \"status\": \"$status\", \"details\": \"$details\", \"metric\": \"$metric\"}"
    else
        if [ "$status" = "OK" ]; then
            echo -e "${GREEN}✓${NC} $name: $status"
        elif [ "$status" = "WARN" ]; then
            echo -e "${YELLOW}⚠${NC} $name: $status"
        else
            echo -e "${RED}✗${NC} $name: $status"
        fi
        if [ ! -z "$details" ] && [ "$VERBOSE" = true ]; then
            echo "  Details: $details"
        fi
    fi

    HEALTH_STATUS["$name"]=$status
    CHECK_RESULTS+=("$name:$status:$details")

    if [ "$status" = "FAIL" ]; then
        EXIT_CODE=1
    fi
}

# =============================================================================
# HTTP ENDPOINTS
# =============================================================================

print_header "HTTP Endpoints"

# Health check endpoint
START_TIME=$(date +%s.%N)
if curl -sf --connect-timeout 5 http://localhost:8000/health > /dev/null 2>&1; then
    END_TIME=$(date +%s.%N)
    RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc)
    print_status "API Health" "OK" "Endpoint responding" "${RESPONSE_TIME}ms"
else
    print_status "API Health" "FAIL" "Endpoint not responding" "N/A"
fi

# Nginx health check
if curl -sf --connect-timeout 5 http://localhost/health > /dev/null 2>&1; then
    print_status "Nginx Health" "OK" "Reverse proxy responding" "OK"
else
    print_status "Nginx Health" "WARN" "Nginx may not be running" "N/A"
fi

# Infrastructure health
if curl -sf --connect-timeout 5 http://localhost:8000/api/infrastructure/health > /dev/null 2>&1; then
    INFRA_STATUS=$(curl -s --connect-timeout 5 http://localhost:8000/api/infrastructure/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    print_status "Infrastructure Health" "OK" "$INFRA_STATUS" "OK"
else
    print_status "Infrastructure Health" "WARN" "Endpoint not responding" "N/A"
fi

# =============================================================================
# DATABASE
# =============================================================================

print_header "Database Status"

# Check SQLite database
if [ -f "$PROJECT_ROOT/platform.db" ]; then
    DB_SIZE=$(ls -lh "$PROJECT_ROOT/platform.db" | awk '{print $5}')
    DB_MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$PROJECT_ROOT/platform.db" 2>/dev/null || echo "unknown")
    print_status "SQLite Database" "OK" "File found at $PROJECT_ROOT/platform.db" "$DB_SIZE"
    if [ "$VERBOSE" = true ]; then
        echo "  Last modified: $DB_MODIFIED"
    fi
else
    print_status "SQLite Database" "FAIL" "Database file not found" "N/A"
fi

# =============================================================================
# DISK SPACE
# =============================================================================

print_header "Disk Space"

# Total disk usage
DISK_USAGE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}')
DISK_AVAILABLE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}')

if [ "${DISK_USAGE%\%}" -lt 80 ]; then
    print_status "Disk Usage" "OK" "Using $DISK_USAGE of available space" "$DISK_USAGE / $DISK_AVAILABLE"
elif [ "${DISK_USAGE%\%}" -lt 90 ]; then
    print_status "Disk Usage" "WARN" "Disk usage above 80%" "$DISK_USAGE / $DISK_AVAILABLE"
else
    print_status "Disk Usage" "FAIL" "Disk usage critical (>90%)" "$DISK_USAGE / $DISK_AVAILABLE"
fi

# =============================================================================
# LOGS
# =============================================================================

print_header "Recent Logs"

# Check for recent errors in app logs
if [ -f "$PROJECT_ROOT/logs/app.log" ]; then
    ERROR_COUNT=$(tail -100 "$PROJECT_ROOT/logs/app.log" | grep -i "error\|exception\|failed" | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        print_status "Application Errors (recent)" "OK" "0 errors in recent logs" "0"
    else
        print_status "Application Errors (recent)" "WARN" "$ERROR_COUNT errors found in recent logs" "$ERROR_COUNT"
    fi
else
    print_status "Application Logs" "WARN" "Log file not found at $PROJECT_ROOT/logs/app.log" "N/A"
fi

# =============================================================================
# PERFORMANCE
# =============================================================================

print_header "Performance Metrics"

# Check Python process memory
if command -v python3 &> /dev/null; then
    PYTHON_PROCESSES=$(pgrep -f "python.*flask\|python.*app" | wc -l)
    if [ "$PYTHON_PROCESSES" -gt 0 ]; then
        PYTHON_MEMORY=$(ps aux | grep -i "python.*flask\|python.*app" | grep -v grep | awk '{sum+=$6} END {print sum/1024 "MB"}')
        print_status "Python Memory Usage" "OK" "$PYTHON_PROCESSES process(es) using $PYTHON_MEMORY" "$PYTHON_MEMORY"
    fi
fi

# =============================================================================
# CODE QUALITY
# =============================================================================

print_header "Code Quality"

# Check for untracked Python files (potential issues)
PYTHON_FILES=$(find "$PROJECT_ROOT/backend" -name "*.py" 2>/dev/null | wc -l)
print_status "Python Code Files" "OK" "$PYTHON_FILES Python files found" "$PYTHON_FILES"

# Check requirements.txt
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    REQ_COUNT=$(wc -l < "$PROJECT_ROOT/requirements.txt")
    print_status "Dependencies" "OK" "$REQ_COUNT dependencies listed" "$REQ_COUNT"
else
    print_status "Dependencies" "WARN" "requirements.txt not found" "N/A"
fi

# =============================================================================
# CONFIGURATION
# =============================================================================

print_header "Configuration"

# Check environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    print_status "Environment File" "OK" ".env file found" "OK"
else
    print_status "Environment File" "WARN" ".env file not found (using defaults)" "N/A"
fi

# Check configuration files
if [ -f "$PROJECT_ROOT/backend/config.py" ]; then
    print_status "Backend Config" "OK" "config.py found" "OK"
else
    print_status "Backend Config" "FAIL" "config.py not found" "N/A"
fi

# =============================================================================
# TESTS
# =============================================================================

print_header "Test Status"

if [ -d "$PROJECT_ROOT/tests" ]; then
    TEST_FILES=$(find "$PROJECT_ROOT/tests" -name "test_*.py" | wc -l)
    print_status "Test Suite" "OK" "$TEST_FILES test files found" "$TEST_FILES"
else
    print_status "Test Suite" "WARN" "tests directory not found" "N/A"
fi

# =============================================================================
# GIT
# =============================================================================

print_header "Git Status"

if [ -d "$PROJECT_ROOT/.git" ]; then
    CURRENT_BRANCH=$(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD)
    COMMIT_HASH=$(cd "$PROJECT_ROOT" && git rev-parse --short HEAD)
    UNCOMMITTED=$(cd "$PROJECT_ROOT" && git status --porcelain | wc -l)

    print_status "Git Repository" "OK" "Branch: $CURRENT_BRANCH, Commit: $COMMIT_HASH" "OK"

    if [ "$UNCOMMITTED" -eq 0 ]; then
        print_status "Uncommitted Changes" "OK" "No uncommitted changes" "0"
    else
        print_status "Uncommitted Changes" "WARN" "$UNCOMMITTED files with changes" "$UNCOMMITTED"
    fi
else
    print_status "Git Repository" "WARN" "Not a git repository" "N/A"
fi

# =============================================================================
# SUMMARY
# =============================================================================

print_header "Health Check Summary"

TOTAL_CHECKS=${#HEALTH_STATUS[@]}
OK_COUNT=$(echo "${HEALTH_STATUS[@]}" | grep -o "OK" | wc -l)
WARN_COUNT=$(echo "${HEALTH_STATUS[@]}" | grep -o "WARN" | wc -l)
FAIL_COUNT=$(echo "${HEALTH_STATUS[@]}" | grep -o "FAIL" | wc -l)

if [ "$OUTPUT_JSON" = false ]; then
    echo ""
    echo -e "${BLUE}Summary:${NC}"
    echo "  Total Checks: $TOTAL_CHECKS"
    echo -e "  ${GREEN}OK: $OK_COUNT${NC}"
    echo -e "  ${YELLOW}Warnings: $WARN_COUNT${NC}"
    echo -e "  ${RED}Failed: $FAIL_COUNT${NC}"

    if [ "$EXIT_CODE" -eq 0 ]; then
        echo -e "${GREEN}✓ All systems operational${NC}"
    else
        echo -e "${RED}✗ Some systems are not operational${NC}"
    fi

    echo ""
    echo "Report saved to: $REPORT_FILE"
fi

# =============================================================================
# SAVE REPORT
# =============================================================================

cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "status": $([ $EXIT_CODE -eq 0 ] && echo '"HEALTHY"' || echo '"UNHEALTHY"'),
  "summary": {
    "total_checks": $TOTAL_CHECKS,
    "ok": $OK_COUNT,
    "warnings": $WARN_COUNT,
    "failed": $FAIL_COUNT
  },
  "checks": [
EOF

for check in "${CHECK_RESULTS[@]}"; do
    IFS=':' read -r name status details <<< "$check"
    echo "    {\"name\": \"$name\", \"status\": \"$status\", \"details\": \"$details\"}," >> "$REPORT_FILE"
done

# Remove trailing comma and close JSON
sed -i '$ s/,$//' "$REPORT_FILE"
cat >> "$REPORT_FILE" << EOF
  ]
}
EOF

# =============================================================================
# SLACK NOTIFICATION
# =============================================================================

if [ "$SEND_SLACK" = true ] && [ ! -z "$SLACK_WEBHOOK" ]; then
    if [ $EXIT_CODE -eq 0 ]; then
        SLACK_COLOR="good"
        SLACK_TEXT="SoftFactory Health Check: All systems operational ✓"
    else
        SLACK_COLOR="danger"
        SLACK_TEXT="SoftFactory Health Check: Some systems down ✗"
    fi

    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"attachments\": [{
                \"color\": \"$SLACK_COLOR\",
                \"title\": \"$SLACK_TEXT\",
                \"text\": \"OK: $OK_COUNT | Warnings: $WARN_COUNT | Failed: $FAIL_COUNT\",
                \"ts\": $(date +%s)
            }]
        }" \
        > /dev/null 2>&1 || echo "Failed to send Slack notification"
fi

# =============================================================================
# EMAIL NOTIFICATION
# =============================================================================

if [ "$SEND_EMAIL" = true ] && [ ! -z "$HEALTH_EMAIL" ]; then
    echo "Health Check Report - $(date)" > /tmp/health_email.txt
    echo "" >> /tmp/health_email.txt
    echo "Status: $([ $EXIT_CODE -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")" >> /tmp/health_email.txt
    echo "Summary: OK=$OK_COUNT, Warnings=$WARN_COUNT, Failed=$FAIL_COUNT" >> /tmp/health_email.txt
    echo "" >> /tmp/health_email.txt
    cat "$REPORT_FILE" >> /tmp/health_email.txt

    if command -v mail &> /dev/null; then
        mail -s "SoftFactory Health Check Report" "$HEALTH_EMAIL" < /tmp/health_email.txt
    elif command -v sendmail &> /dev/null; then
        sendmail "$HEALTH_EMAIL" < /tmp/health_email.txt
    fi
fi

exit "$EXIT_CODE"
