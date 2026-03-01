# 📘 SoftFactory Monitoring Integration Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Monitoring Integration Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Quick Start for Adding Monitoring to Production**
> **Updated:** 2026-02-25

---

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**New packages added:**
- `python-json-logger==2.0.7` — JSON logging
- `psutil==5.9.6` — System metrics (CPU, memory)

---

## Step 2: Update Flask Application

**File:** `backend/app.py`

Add these imports at the top:

```python
from backend.logging_config import configure_logging, request_logging_middleware
from backend.metrics import metrics_bp, register_metrics_middleware
```

In the `create_app()` function, after all blueprint registrations, add:

```python
def create_app():
    app = Flask(__name__)

    # ... existing config ...

    # Register existing blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_bp)
    # ... other blueprints ...

    # ADD THESE LINES:
    # Configure structured JSON logging
    configure_logging(app, log_file='logs/app.log', debug=False)
    request_logging_middleware(app)

    # Register metrics endpoints (/api/metrics/*)
    app.register_blueprint(metrics_bp)
    register_metrics_middleware(app)

    # ... rest of create_app ...
    return app
```

---

## Step 3: Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

---

## Step 4: Test Health Endpoints (Local)

Start Flask:

```bash
python backend/app.py
```

In another terminal, test endpoints:

```bash
# Test 1: Basic health
curl http://localhost:8000/api/metrics/health | jq .

# Test 2: Prometheus format
curl http://localhost:8000/api/metrics/prometheus

# Test 3: Detailed metrics
curl http://localhost:8000/api/metrics/summary | jq .

# Test 4: Check logs created
tail -f logs/app.log | head -5
```

**Expected Output (health):**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-25T10:30:45Z",
  "uptime_seconds": 45,
  "database": "healthy",
  "api": "ok"
}
```

---

## Step 5: Start Monitoring Stack (Docker)

**Prerequisites:**
- Docker installed
- Docker Compose installed
- `orchestrator/prometheus-config.yml` exists
- `orchestrator/alert-rules.yml` exists
- `orchestrator/logstash-config.conf` exists
- `orchestrator/alertmanager-config.yml` exists

**Start:**

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Verify running:**

```bash
docker-compose -f docker-compose.monitoring.yml ps

# Expected:
# NAME                       STATUS      PORTS
# softfactory-prometheus     Up 2m       0.0.0.0:9090->9090/tcp
# softfactory-grafana        Up 2m       0.0.0.0:3000->3000/tcp
# softfactory-elasticsearch  Up 2m       0.0.0.0:9200->9200/tcp
# softfactory-kibana         Up 2m       0.0.0.0:5601->5601/tcp
# softfactory-alertmanager   Up 2m       0.0.0.0:9093->9093/tcp
# softfactory-logstash       Up 2m       0.0.0.0:5000->5000/tcp
```

---

## Step 6: Verify Prometheus Scraping

1. Open http://localhost:9090
2. Go to **Status → Targets**
3. Should see `softfactory-api` with state **UP**

**Troubleshoot if DOWN:**
```bash
# Check if Flask is running on port 8000
curl http://localhost:8000/api/metrics/prometheus | head -5

# Check Docker logs
docker logs softfactory-prometheus | tail -20
```

---

## Step 7: Setup Grafana Dashboard

1. Open http://localhost:3000
2. Login: `admin` / `admin` (change on first login!)
3. Add Prometheus data source:
   - Settings (gear icon) → Data Sources → New
   - Name: `Prometheus`
   - URL: `http://prometheus:9090`
   - Click **Save & Test**

4. Import dashboard:
   - Create → Import
   - Paste JSON from `docs/grafana-dashboard-softfactory.json`
   - Select Prometheus data source
   - Click **Import**

---

## Step 8: Setup Kibana Log Dashboard

1. Open http://localhost:5601
2. Go to **Stack Management → Index Patterns**
3. Create pattern:
   - Name: `softfactory-logs-*`
   - Timestamp: `@timestamp`
   - Click **Create**

4. Create dashboard:
   - Go to **Discover**
   - Select `softfactory-logs-*` index
   - View logs in real-time

---

## Step 9: Configure Alert Notifications

**Option A: Slack** (recommended)

1. Create Slack workspace webhook:
   - https://api.slack.com/apps
   - Create New App → From scratch
   - Enable Incoming Webhooks
   - Add New Webhook to Workspace → #alerts channel
   - Copy webhook URL

2. Update `orchestrator/alertmanager-config.yml`:
   ```yaml
   global:
     slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   ```

3. Restart AlertManager:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart alertmanager
   ```

**Option B: Email**

1. Update `orchestrator/alertmanager-config.yml`:
   ```yaml
   global:
     smtp_smarthost: 'smtp.gmail.com:587'
     smtp_auth_username: 'your-email@gmail.com'
     smtp_auth_password: 'your-app-password'
   ```

2. Restart AlertManager:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart alertmanager
   ```

**Option C: PagerDuty**

1. Get Integration Key from PagerDuty:
   - Services → Your Service → Integrations → Add integration
   - Select "Prometheus"
   - Copy Integration Key

2. Update `orchestrator/alertmanager-config.yml`:
   ```yaml
   receivers:
     - name: 'pagerduty-critical'
       pagerduty_configs:
         - service_key: 'YOUR_PAGERDUTY_KEY'
   ```

3. Restart AlertManager

---

## Step 10: Test Monitoring Pipeline

### Test 1: Trigger High Error Rate Alert

```bash
# Generate errors
for i in {1..100}; do
  curl http://localhost:8000/api/auth/invalid-endpoint 2>/dev/null &
done

# Watch alert in Prometheus (should trigger in ~5 min)
# http://localhost:9090 → Alerts tab
```

### Test 2: Check Logs in Kibana

```bash
# Generate some requests
curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/coocook/chefs

# View in Kibana
# http://localhost:5601 → Discover → softfactory-logs-*
```

### Test 3: Verify Metrics in Grafana

```bash
# Open dashboard
# http://localhost:3000 → SoftFactory Main Dashboard
# Should see metrics updating in real-time
```

---

## Production Deployment Checklist

```bash
# Pre-deployment
[ ] All tests pass: pytest tests/
[ ] Code review completed
[ ] Secrets not in logs (check logs/app.log for tokens)
[ ] Disk space available: df -h (>50GB recommended)

# Monitoring stack
[ ] Docker Compose working: docker-compose -f docker-compose.monitoring.yml config
[ ] All environment variables set (Slack webhook, PagerDuty key, etc.)
[ ] Prometheus retains 30 days of data
[ ] Elasticsearch disk space configured
[ ] Log rotation enabled

# Flask updates
[ ] logging_config.py added to backend/
[ ] metrics.py added to backend/
[ ] app.py updated with logging/metrics initialization
[ ] requirements.txt updated

# Alerting
[ ] Alert rules imported: orchestrator/alert-rules.yml
[ ] Slack/Email/PagerDuty configured
[ ] Test alert received
[ ] On-call rotation established

# Verification
[ ] /api/metrics/health returns 200
[ ] /api/metrics/prometheus returns metrics
[ ] Prometheus scraping target is UP
[ ] Kibana receives logs (check index count)
[ ] Grafana dashboard loads with data
[ ] Alerts route to Slack/Email/PagerDuty
```

---

## Common Issues & Troubleshooting

### Issue: Prometheus target shows "DOWN"

**Symptom:** `softfactory-api` in Prometheus targets shows state "DOWN"

**Solution:**
```bash
# 1. Check if Flask is running on port 8000
netstat -tlnp | grep 8000

# 2. Check if /api/metrics/prometheus endpoint exists
curl http://localhost:8000/api/metrics/prometheus

# 3. If endpoint missing, re-run Flask initialization:
python -c "from backend.app import create_app; app = create_app()"

# 4. Check Prometheus logs
docker logs softfactory-prometheus | grep error
```

---

### Issue: Kibana shows no logs

**Symptom:** Kibana index pattern created but "0 results" in Discover

**Solution:**
```bash
# 1. Check if Logstash is running
docker logs softfactory-logstash | tail -20

# 2. Verify logs/app.log exists and has content
wc -l logs/app.log

# 3. Check Logstash can read the file
docker exec softfactory-logstash tail -f /logs/app.log

# 4. Check Elasticsearch has data
curl http://localhost:9200/_cat/indices?v

# 5. If no indices, restart Logstash
docker-compose -f docker-compose.monitoring.yml restart logstash
```

---

### Issue: Alerts not sending to Slack

**Symptom:** Alerts fire in Prometheus but don't appear in Slack

**Solution:**
```bash
# 1. Check AlertManager logs
docker logs softfactory-alertmanager | grep -i slack

# 2. Verify webhook URL is correct
grep slack_api_url orchestrator/alertmanager-config.yml

# 3. Test webhook manually
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from AlertManager"}'

# 4. If webhook returns 404, regenerate in Slack workspace

# 5. Restart AlertManager
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

---

### Issue: High memory usage / Elasticsearch crashes

**Symptom:** `docker logs softfactory-elasticsearch` shows "OutOfMemory"

**Solution:**
```bash
# 1. Increase Java heap memory in docker-compose.monitoring.yml
ES_JAVA_OPTS=-Xms1g -Xmx1g

# 2. Delete old indices to free space
curl -X DELETE http://localhost:9200/softfactory-logs-2026.01.*

# 3. Set index lifecycle policy
curl -X PUT http://localhost:9200/_ilm/policy/softfactory-policy \
  -H 'Content-Type: application/json' \
  -d '{"policy": "softfactory-logs", "phases": {"hot": {"min_age": "0d"}, "delete": {"min_age": "30d"}}}'

# 4. Restart with new memory limit
docker-compose -f docker-compose.monitoring.yml down
docker-compose -f docker-compose.monitoring.yml up -d elasticsearch
```

---

## Next Steps

1. **Read:** `docs/MONITORING-SETUP.md` — Comprehensive monitoring guide
2. **Watch:** Dashboards for 24 hours to baseline normal values
3. **Tune:** Alert thresholds based on baseline
4. **Train:** Team on incident response runbooks
5. **Monitor:** Weekly review of alerts and SLO performance

---

## Support

- **Questions:** Email ops@softfactory.local
- **Bugs:** GitHub Issues with label `monitoring`
- **On-call:** Page via PagerDuty

---

**Last Updated:** 2026-02-25