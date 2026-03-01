#!/bin/bash
# ============================================================================
# SoftFactory Monitoring Stack Health Check
# Validates all monitoring components are operational
# ============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== SoftFactory Monitoring Stack Health Check ===${NC}"
echo "Time: $(date)"
echo ""

# Component list with URLs and expected status codes
declare -A COMPONENTS=(
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["Alertmanager"]="http://localhost:9093/-/healthy"
    ["Grafana"]="http://localhost:3000/api/health"
    ["API Metrics"]="http://localhost:8000/metrics"
)

# Check each component
FAILED_COUNT=0
PASSED_COUNT=0

for component in "${!COMPONENTS[@]}"; do
    url="${COMPONENTS[$component]}"
    echo -n "Checking ${component}... "

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED_COUNT++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED_COUNT++))
    fi
done

echo ""
echo -e "${BLUE}=== Detailed Status ===${NC}"

# Prometheus status
echo -n "Prometheus targets: "
TARGETS=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | grep -o '"activeTargets"' | wc -l)
if [ "$TARGETS" -gt 0 ]; then
    echo -e "${GREEN}${TARGETS} active targets${NC}"
else
    echo -e "${YELLOW}No targets found${NC}"
fi

# Alert rules count
echo -n "Alert rules: "
RULES=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | grep -o '"name"' | wc -l)
echo -e "${GREEN}${RULES} rules defined${NC}"

# Alertmanager status
echo -n "Alertmanager alerts: "
ALERTS=$(curl -s http://localhost:9093/api/v1/alerts 2>/dev/null | grep -o '"status"' | wc -l)
echo -e "${GREEN}${ALERTS} alerts${NC}"

# Grafana datasources
echo -n "Grafana datasources: "
DATASOURCES=$(curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | grep -o '"type"' | wc -l)
echo -e "${GREEN}${DATASOURCES} datasources${NC}"

# API metrics sample
echo -n "API metrics endpoint: "
METRICS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep -c "^http_" || echo "0")
if [ "$METRICS" -gt 0 ]; then
    echo -e "${GREEN}${METRICS} metric families${NC}"
else
    echo -e "${RED}No metrics found${NC}"
fi

echo ""
echo -e "${BLUE}=== Dashboard URLs ===${NC}"
echo "Prometheus:   http://localhost:9090"
echo "Alertmanager: http://localhost:9093"
echo "Grafana:      http://localhost:3000 (admin/admin)"
echo ""

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "Passed: ${GREEN}${PASSED_COUNT}${NC}"
echo -e "Failed: ${FAILED_COUNT}"

if [ "$FAILED_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ All monitoring components operational${NC}"
    exit 0
else
    echo -e "${RED}✗ Some monitoring components failed${NC}"
    exit 1
fi
