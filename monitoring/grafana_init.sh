#!/bin/bash
# ============================================================================
# Grafana Initialization Script
# Automatically creates datasources, dashboards, and alert notifications
# ============================================================================

set -e

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus:9090}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Grafana Initialization Script ===${NC}"
echo "Grafana URL: $GRAFANA_URL"
echo "Admin User: $ADMIN_USER"
echo "Prometheus URL: $PROMETHEUS_URL"
echo ""

# Wait for Grafana to be ready
echo -e "${YELLOW}[1/5] Waiting for Grafana to be ready...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s -f "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Grafana is ready${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ Grafana did not start in time${NC}"
    exit 1
fi

# Step 1: Add Prometheus datasource
echo -e "${YELLOW}[2/5] Adding Prometheus datasource...${NC}"
DATASOURCE_ID=$(curl -s -X POST "${GRAFANA_URL}/api/datasources" \
  -H "Content-Type: application/json" \
  -u "${ADMIN_USER}:${ADMIN_PASSWORD}" \
  -d "{
    \"name\": \"Prometheus\",
    \"type\": \"prometheus\",
    \"url\": \"${PROMETHEUS_URL}\",
    \"access\": \"proxy\",
    \"isDefault\": true,
    \"jsonData\": {
      \"httpMethod\": \"POST\"
    }
  }" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$DATASOURCE_ID" ]; then
    echo -e "${RED}✗ Failed to add Prometheus datasource${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Prometheus datasource added (ID: $DATASOURCE_ID)${NC}"

# Step 2: Add Alertmanager datasource
echo -e "${YELLOW}[3/5] Adding Alertmanager datasource...${NC}"
curl -s -X POST "${GRAFANA_URL}/api/datasources" \
  -H "Content-Type: application/json" \
  -u "${ADMIN_USER}:${ADMIN_PASSWORD}" \
  -d "{
    \"name\": \"Alertmanager\",
    \"type\": \"alertmanager\",
    \"url\": \"http://alertmanager:9093\",
    \"access\": \"proxy\",
    \"isDefault\": false
  }" > /dev/null

echo -e "${GREEN}✓ Alertmanager datasource added${NC}"

# Step 3: Create folders for dashboards
echo -e "${YELLOW}[4/5] Creating dashboard folders...${NC}"

FOLDERS=("SoftFactory" "Infrastructure" "Database" "Cache" "Search")
for folder in "${FOLDERS[@]}"; do
    FOLDER_ID=$(curl -s -X POST "${GRAFANA_URL}/api/folders" \
      -H "Content-Type: application/json" \
      -u "${ADMIN_USER}:${ADMIN_PASSWORD}" \
      -d "{\"title\": \"$folder\"}" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

    if [ -n "$FOLDER_ID" ]; then
        echo -e "${GREEN}✓ Created folder: $folder (ID: $FOLDER_ID)${NC}"
    fi
done

# Step 4: Import public dashboards from Grafana Hub
echo -e "${YELLOW}[5/5] Importing public dashboards...${NC}"

DASHBOARDS=(
    "1860:Prometheus 2.0 Stats"
    "3662:Prometheus and Alertmanager"
    "6417:PostgreSQL Exporter"
    "11600:Redis Exporter"
    "266:Elasticsearch"
)

for dashboard in "${DASHBOARDS[@]}"; do
    DASH_ID="${dashboard%:*}"
    DASH_NAME="${dashboard#*:}"

    echo "  Importing: $DASH_NAME (ID: $DASH_ID)..."

    # Fetch dashboard from Grafana Hub
    DASHBOARD_JSON=$(curl -s "https://grafana.com/api/dashboards/${DASH_ID}/revisions/latest/download" 2>/dev/null)

    if [ -n "$DASHBOARD_JSON" ]; then
        # Import dashboard
        curl -s -X POST "${GRAFANA_URL}/api/dashboards/db" \
          -H "Content-Type: application/json" \
          -u "${ADMIN_USER}:${ADMIN_PASSWORD}" \
          -d "{
            \"overwrite\": true,
            \"dashboard\": $(echo "$DASHBOARD_JSON" | jq '.dashboard // .')
          }" > /dev/null

        echo -e "${GREEN}✓ Imported: $DASH_NAME${NC}"
    else
        echo -e "${YELLOW}⚠ Could not import: $DASH_NAME (network error)${NC}"
    fi
done

# Step 5: Create alert notification channels (if configured)
echo -e "${YELLOW}[5/5] Configuring notification channels...${NC}"

# Webhook notification channel
curl -s -X POST "${GRAFANA_URL}/api/alert-notifications" \
  -H "Content-Type: application/json" \
  -u "${ADMIN_USER}:${ADMIN_PASSWORD}" \
  -d "{
    \"name\": \"Webhook\",
    \"type\": \"webhook\",
    \"isDefault\": false,
    \"settings\": {
      \"url\": \"http://localhost:5001/alerts\"
    }
  }" > /dev/null 2>&1

echo -e "${GREEN}✓ Webhook notification channel configured${NC}"

# Success message
echo ""
echo -e "${GREEN}=== Grafana Initialization Complete ===${NC}"
echo ""
echo "Access Grafana:"
echo "  URL: $GRAFANA_URL"
echo "  Username: $ADMIN_USER"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Next steps:"
echo "1. Change default password (Grafana → Preferences → Change Password)"
echo "2. Configure additional notification channels (Alerts → Notification channels)"
echo "3. Create custom dashboards using imported data sources"
echo ""
