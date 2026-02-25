#!/bin/bash
#
# SoftFactory Health Check Script
# Comprehensive system health verification
#
# Usage: ./scripts/health-check.sh [--json] [--verbose]
#

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE="docker-compose -f ${PROJECT_ROOT}/docker-compose-prod.yml"

# Options
OUTPUT_JSON=false
VERBOSE=false
EXIT_CODE=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
        *)
            shift
            ;;
    esac
done

# Functions
print_header() {
    if [ "$OUTPUT_JSON" = false ]; then
        echo ""
        echo -e "${BLUE}=== $1 ===${NC}"
    fi
}

print_status() {
    local name=$1
    local status=$2
    local details=$3

    if [ "$OUTPUT_JSON" = true ]; then
        echo "{\"check\": \"$name\", \"status\": \"$status\", \"details\": \"$details\"}"
    else
        if [ "$status" = "OK" ]; then
            echo -e "${GREEN}✓${NC} $name: $status"
        else
            echo -e "${RED}✗${NC} $name: $status"
        fi
        if [ ! -z "$details" ] && [ "$VERBOSE" = true ]; then
            echo "  Details: $details"
        fi
    fi

    if [ "$status" != "OK" ]; then
        EXIT_CODE=1
    fi
}

# =============================================================================
# DOCKER STATUS
# =============================================================================

print_header "Container Status"

# Check Docker daemon
if docker ps > /dev/null 2>&1; then
    print_status "Docker Daemon" "OK" "Connected"
else
    print_status "Docker Daemon" "FAIL" "Cannot connect to Docker"
    exit 1
fi

# Check each container
CONTAINERS=("softfactory-nginx" "softfactory-api" "softfactory-db" "softfactory-redis" "softfactory-prometheus")
for container in "${CONTAINERS[@]}"; do
    if docker ps | grep -q "$container"; then
        STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "^$container" | awk '{print $2}')
        print_status "Container: $container" "OK" "$STATUS"
    else
        print_status "Container: $container" "FAIL" "Not running"
    fi
done

# =============================================================================
# HTTP ENDPOINTS
# =============================================================================

print_header "HTTP Endpoints"

# Health check endpoint
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    RESPONSE=$(curl -s http://localhost:8000/health | jq .status 2>/dev/null || echo "OK")
    print_status "API Health" "OK" "$RESPONSE"
else
    print_status "API Health" "FAIL" "Endpoint not responding"
fi

# Nginx health check
if curl -sf http://localhost/health > /dev/null 2>&1; then
    print_status "Nginx Health" "OK" "Reverse proxy responding"
else
    print_status "Nginx Health" "FAIL" "Nginx not responding"
fi

# Infrastructure health
if curl -sf http://localhost:8000/api/infrastructure/health > /dev/null 2>&1; then
    INFRA_STATUS=$(curl -s http://localhost:8000/api/infrastructure/health | jq .overall_status 2>/dev/null || echo "unknown")
    print_status "Infrastructure Health" "OK" "$INFRA_STATUS"
else
    print_status "Infrastructure Health" "FAIL" "Endpoint not responding"
fi

# =============================================================================
# DATABASE
# =============================================================================

print_header "Database Status"

# Database connectivity
if docker exec softfactory-db psql -U postgres -d softfactory -c "SELECT 1;" > /dev/null 2>&1; then
    print_status "PostgreSQL Connection" "OK" "Connected"
else
    print_status "PostgreSQL Connection" "FAIL" "Cannot connect"
fi

# Database version
DB_VERSION=$(docker exec softfactory-db psql -U postgres -t -c "SELECT version();" 2>/dev/null | cut -d',' -f1)
if [ ! -z "$DB_VERSION" ]; then
    print_status "PostgreSQL Version" "OK" "$DB_VERSION"
fi

# Table count
TABLE_COUNT=$(docker exec softfactory-db psql -U postgres -d softfactory -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null)
if [ ! -z "$TABLE_COUNT" ]; then
    print_status "Database Tables" "OK" "$TABLE_COUNT tables"
fi

# User count
USER_COUNT=$(docker exec softfactory-db psql -U postgres -d softfactory -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null)
if [ ! -z "$USER_COUNT" ]; then
    print_status "Database Users" "OK" "$USER_COUNT users"
fi

# =============================================================================
# REDIS
# =============================================================================

print_header "Redis Status"

if docker exec softfactory-redis redis-cli ping > /dev/null 2>&1; then
    print_status "Redis Connection" "OK" "Connected"

    # Redis memory usage
    MEMORY=$(docker exec softfactory-redis redis-cli info memory | grep used_memory_human | cut -d':' -f2)
    if [ ! -z "$MEMORY" ]; then
        print_status "Redis Memory" "OK" "$MEMORY"
    fi
else
    print_status "Redis Connection" "FAIL" "Cannot connect"
fi

# =============================================================================
# DISK SPACE
# =============================================================================

print_header "Disk Space"

# Total disk usage
DISK_USAGE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}')
print_status "Disk Usage" "OK" "$DISK_USAGE used"

# Docker volumes size
if command -v docker &> /dev/null; then
    VOLUME_SIZE=$(docker system df --format "table {{.Size}}" | tail -1)
    print_status "Docker Volumes" "OK" "$VOLUME_SIZE"
fi

# =============================================================================
# RESOURCE USAGE
# =============================================================================

print_header "Resource Usage"

# Container resource stats
echo ""
docker stats --no-stream softfactory-api softfactory-db --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "Cannot get resource stats"

# =============================================================================
# LOGS
# =============================================================================

print_header "Recent Logs"

# Check for recent errors in API logs
ERROR_COUNT=$(docker logs softfactory-api --since 1h 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    print_status "API Errors (last 1h)" "OK" "0 errors"
else
    print_status "API Errors (last 1h)" "WARN" "$ERROR_COUNT errors found"
fi

# Check for database errors
DB_ERROR_COUNT=$(docker logs softfactory-db --since 1h 2>/dev/null | grep -i "error\|fatal" | wc -l)
if [ "$DB_ERROR_COUNT" -eq 0 ]; then
    print_status "Database Errors (last 1h)" "OK" "0 errors"
else
    print_status "Database Errors (last 1h)" "WARN" "$DB_ERROR_COUNT errors found"
fi

# =============================================================================
# MONITORING
# =============================================================================

print_header "Monitoring"

# Prometheus status
if curl -sf http://localhost:9090 > /dev/null 2>&1; then
    print_status "Prometheus" "OK" "Running"
else
    print_status "Prometheus" "FAIL" "Not responding"
fi

# =============================================================================
# SUMMARY
# =============================================================================

print_header "Health Check Summary"

if [ "$EXIT_CODE" -eq 0 ]; then
    if [ "$OUTPUT_JSON" = false ]; then
        echo -e "${GREEN}✓ All systems operational${NC}"
    fi
    echo "Status: HEALTHY"
else
    if [ "$OUTPUT_JSON" = false ]; then
        echo -e "${RED}✗ Some systems are not operational${NC}"
    fi
    echo "Status: UNHEALTHY"
fi

exit "$EXIT_CODE"
