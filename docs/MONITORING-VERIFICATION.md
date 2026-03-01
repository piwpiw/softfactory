# 📝 Monitoring & Logging - Verification Checklist

> **Purpose**: Run from project root:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Monitoring & Logging - Verification Checklist 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Purpose:** Verify all monitoring components installed and working correctly
> **Updated:** 2026-02-25

---

## Pre-Deployment Verification

### Step 1: Files Created

Run from project root:

```bash
# Check Python modules
ls -l backend/metrics.py backend/logging_config.py
# Expected: Both files exist and > 200 lines each

# Check configuration files
ls -l orchestrator/prometheus-config.yml orchestrator/alert-rules.yml orchestrator/alertmanager-config.yml orchestrator/logstash-config.conf
# Expected: All 4 files exist

# Check documentation
ls -l docs/MONITORING-SETUP.md docs/MONITORING-INTEGRATION.md
# Expected: Both files exist and > 1000 lines total

# Check Docker Compose
ls -l docker-compose.monitoring.yml
# Expected: File exists
```

**Verification:**
```bash
[ ] backend/metrics.py exists and > 200 lines
[ ] backend/logging_config.py exists and > 200 lines
[ ] orchestrator/prometheus-config.yml exists
[ ] orchestrator/alert-rules.yml exists
[ ] orchestrator/alertmanager-config.yml exists
[ ] orchestrator/logstash-config.conf exists
[ ] docs/MONITORING-SETUP.md exists
[ ] docs/MONITORING-INTEGRATION.md exists
[ ] docker-compose.monitoring.yml exists
[ ] requirements.txt updated with python-json-logger, psutil
```

---

### Step 2: Dependencies Installed

```bash
pip install -r requirements.txt

# Verify packages
pip show python-json-logger psutil | grep Version
# Expected output: python-json-logger 2.0.7, psutil 5.9.6
```

**Verification:**
```bash
[ ] python-json-logger==2.0.7 installed
[ ] psutil==5.9.6 installed
```

---

### Step 3: Flask Integration

**Check backend/app.py contains:**

```bash
grep -n "configure_logging\|request_logging_middleware\|metrics_bp\|register_metrics_middleware" backend/app.py
```

**Expected output:**
```
import line: from backend.logging_config import configure_logging, request_logging_middleware
import line: from backend.metrics import metrics_bp, register_metrics_middleware
create_app line: configure_logging(app, log_file='logs/app.log', debug=False)
create_app line: request_logging_middleware(app)
create_app line: app.register_blueprint(metrics_bp)
create_app line: register_metrics_middleware(app)
```

**Verification:**
```bash
[ ] logging_config imports added to app.py
[ ] metrics imports added to app.py
[ ] configure_logging() called in create_app()
[ ] request_logging_middleware() called in create_app()
[ ] app.register_blueprint(metrics_bp) added
[ ] register_metrics_middleware(app) called
```

---

### Step 4: Logs Directory

```bash
mkdir -p logs
ls -ld logs
# Expected: drwxr-xr-x (755 permissions)
```

**Verification:**
```bash
[ ] logs/ directory exists
[ ] logs/ directory is writable (test: touch logs/test.txt && rm logs/test.txt)
```

---

## Local Testing (Before Docker)

### Step 5: Start Flask and Test Endpoints

**Terminal 1:**
```bash
python backend/app.py
# Expected output: Running on http://0.0.0.0:8000
```

**Terminal 2:**

#### Test 5.1: Basic Health Check

```bash
curl -s http://localhost:8000/api/metrics/health | jq .
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-25T...",
  "uptime_seconds": X,
  "database": "healthy",
  "api": "ok"
}
```

**Verification:**
```bash
[ ] Returns HTTP 200
[ ] "status" field present and equals "healthy" or "degraded"
[ ] "database" field present
[ ] "timestamp" field present in ISO format
```

#### Test 5.2: Prometheus Format Metrics

```bash
curl -s http://localhost:8000/api/metrics/prometheus | head -20
```

**Expected output:**
```
# HELP softfactory_up Application health status...
# TYPE softfactory_up gauge
softfactory_up 1

# HELP softfactory_uptime_seconds ...
# TYPE softfactory_uptime_seconds gauge
softfactory_uptime_seconds X
...
```

**Verification:**
```bash
[ ] Returns HTTP 200
[ ] Contains "# HELP" and "# TYPE" lines
[ ] Contains "softfactory_up" metric
[ ] Contains "softfactory_requests_total" metric
[ ] Contains "softfactory_errors_total" metric
[ ] Contains "softfactory_cpu_percent" metric
[ ] Contains "softfactory_memory_percent" metric
```

#### Test 5.3: Detailed Metrics Summary

```bash
curl -s http://localhost:8000/api/metrics/summary | jq .
```

**Expected output:**
```json
{
  "timestamp": "2026-02-25T...",
  "uptime": {
    "seconds": X,
    "human_readable": "Xh Ym Zs"
  },
  "system": {
    "cpu_percent": X.X,
    "memory": {
      "rss_mb": X.X,
      "vms_mb": X.X,
      "percent": X.X
    },
    "process_id": XXXX
  },
  "application": {
    "requests_total": X,
    "errors_total": X,
    "error_rate": X.X
  },
  "database": {
    "status": "healthy",
    "stats": {
      "users": X,
      "payments": X,
      "bookings": X,
      "sns_posts": X,
      "campaigns": X,
      "ai_employees": X
    }
  }
}
```

**Verification:**
```bash
[ ] Returns HTTP 200
[ ] All top-level fields present
[ ] "system" contains cpu, memory, process_id
[ ] "application" contains requests_total, errors_total
[ ] "database" shows table counts
```

#### Test 5.4: Request Correlation IDs

```bash
curl -v -H "Authorization: Bearer demo_token" http://localhost:8000/api/coocook/chefs 2>&1 | grep -i "x-request-id"
```

**Expected output:**
```
< X-Request-Id: a1b2c3d4
```

**Verification:**
```bash
[ ] Response contains X-Request-Id header
[ ] Request ID is 8-character string
```

#### Test 5.5: JSON Logs

```bash
tail -5 logs/app.log | python -m json.tool
```

**Expected output:**
```json
{
  "timestamp": "2026-02-25T...",
  "level": "INFO",
  "logger": "backend.platform",
  "message": "Request completed: 200",
  "method": "GET",
  "path": "/api/coocook/chefs",
  "status": 200,
  "latency_ms": X.X,
  "request_id": "a1b2c3d4"
}
```

**Verification:**
```bash
[ ] logs/app.log file created
[ ] logs/app.log contains valid JSON (parseable by `python -m json.tool`)
[ ] Each log line has: timestamp, level, message, request_id
[ ] Timestamp in ISO format (YYYY-MM-DDTHH:MM:SSZ)
```

---

## Docker Monitoring Stack Testing

### Step 6: Validate Docker Compose

```bash
docker-compose -f docker-compose.monitoring.yml config
# Expected: Valid YAML output, no errors
```

**Verification:**
```bash
[ ] docker-compose.monitoring.yml is valid YAML
[ ] All 6 services defined (prometheus, grafana, alertmanager, elasticsearch, kibana, logstash)
[ ] All volumes defined
[ ] All networks defined
```

---

### Step 7: Start Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services running
docker-compose -f docker-compose.monitoring.yml ps
```

**Expected output:**
```
NAME                       STATUS      PORTS
softfactory-prometheus     Up (healthy) 0.0.0.0:9090->9090/tcp
softfactory-grafana        Up (healthy) 0.0.0.0:3000->3000/tcp
softfactory-alertmanager   Up (healthy) 0.0.0.0:9093->9093/tcp
softfactory-elasticsearch  Up (healthy) 0.0.0.0:9200->9200/tcp
softfactory-kibana         Up (healthy) 0.0.0.0:5601->5601/tcp
softfactory-logstash       Up (healthy) 0.0.0.0:5000->5000/tcp
```

**Verification:**
```bash
[ ] All 6 services show "Up (healthy)"
[ ] All services are publicly accessible on specified ports
[ ] No services show "Exited" or "Dead" status
```

---

### Step 8: Prometheus Verification

**Access:** http://localhost:9090

**Check 8.1: Targets Status**

1. Click: Status → Targets
2. Should see `softfactory-api` target

**Expected:**
- Endpoint: `http://localhost:8000/api/metrics/prometheus`
- State: **UP** (green)
- Last Scrape: < 1 minute ago
- Scrape Duration: < 1 second

**If target shows DOWN:**

```bash
# Debug steps
# 1. Check Flask is running
curl http://localhost:8000/api/metrics/prometheus

# 2. Check Prometheus logs
docker logs softfactory-prometheus | tail -20

# 3. Verify endpoint exists
curl -v http://localhost:8000/api/metrics/prometheus 2>&1 | head -20

# 4. Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

**Verification:**
```bash
[ ] softfactory-api target shows "UP"
[ ] Last scrape < 1 minute ago
[ ] No errors in target details
```

**Check 8.2: Metrics Stored**

1. Click: Graph
2. Enter query: `softfactory_requests_total`
3. Click: Execute

**Expected:**
- Graph shows time-series data (upward trending line)
- Query returns values > 0

**Verification:**
```bash
[ ] softfactory_requests_total query returns data
[ ] softfactory_up query returns 1 or 0
[ ] softfactory_memory_percent query returns value 0-100
```

---

### Step 9: Grafana Setup

**Access:** http://localhost:3000

**Login:** admin / admin

**Check 9.1: Add Prometheus Data Source**

1. Settings (gear icon) → Data Sources
2. Click: New data source
3. Select: Prometheus
4. URL: `http://prometheus:9090`
5. Click: Save & Test

**Expected:**
- Message: "datasource is working"
- Green checkmark

**Verification:**
```bash
[ ] Prometheus data source created successfully
[ ] Test returns "datasource is working"
```

**Check 9.2: Create Test Dashboard**

1. Click: Create → Dashboard
2. Add panel: Add new panel
3. Data source: Prometheus
4. Metrics: `softfactory_requests_total`
5. Click: Save

**Expected:**
- Panel shows graph with upward trending line
- Can see metrics updating in real-time

**Verification:**
```bash
[ ] Dashboard created successfully
[ ] Panel shows Prometheus metrics
[ ] Metrics refresh every 5-30 seconds
```

---

### Step 10: Elasticsearch & Kibana

**Access:** http://localhost:5601

**Check 10.1: Index Pattern**

1. Settings → Index Patterns
2. Should see `softfactory-logs-*` pattern
   - If not, create one:
   - Index pattern: `softfactory-logs-*`
   - Time field: `@timestamp`
   - Click: Create

**Verification:**
```bash
[ ] Index pattern created for softfactory-logs-*
[ ] Time field set to @timestamp
```

**Check 10.2: View Logs**

1. Click: Discover
2. Select index: `softfactory-logs-*`
3. Should see log entries

**If no logs appear:**

```bash
# Check if Elasticsearch has data
curl http://localhost:9200/_cat/indices?v

# Check Logstash logs
docker logs softfactory-logstash | tail -20

# Verify logs/app.log has content
wc -l logs/app.log

# Force Logstash to re-read logs (remove sincedb)
docker exec softfactory-logstash rm /var/lib/logstash/.sincedb*
docker-compose -f docker-compose.monitoring.yml restart logstash
```

**Verification:**
```bash
[ ] Kibana shows log entries in Discover
[ ] Each log has timestamp, level, message fields
[ ] Can filter logs by status code, path, user_id
```

---

### Step 11: AlertManager

**Access:** http://localhost:9093

**Check 11.1: Configuration Loaded**

1. Click: Status
2. Should see configuration displayed

**Verification:**
```bash
[ ] AlertManager status page accessible
[ ] Configuration loaded successfully
```

**Check 11.2: Alert Notifications (Slack)**

1. Configure Slack webhook in `orchestrator/alertmanager-config.yml`
2. Restart AlertManager: `docker-compose -f docker-compose.monitoring.yml restart alertmanager`
3. Generate test alert: (See section below)

**Verification:**
```bash
[ ] AlertManager configuration includes slack_api_url
[ ] AlertManager restarted without errors
```

---

## Load Test (Optional)

### Step 12: Generate Load to Trigger Alerts

```bash
# Generate 10,000 requests with 100 concurrent connections
ab -n 10000 -c 100 http://localhost:8000/api/metrics/health

# Monitor metrics during load test in separate terminal
watch -n 1 'curl -s http://localhost:8000/api/metrics/summary | jq ".system, .application"'
```

**Expected observations:**
- CPU usage increases
- Memory usage increases
- Request latency increases
- Error count increases (possibly)

**Verification:**
```bash
[ ] Prometheus receives metric spikes during load
[ ] Grafana shows latency/request graphs updating
[ ] No errors in Flask/Prometheus logs
```

---

## Post-Deployment Verification

### Step 13: Production Readiness Checklist

```bash
[ ] All files created and in correct locations
[ ] All Python dependencies installed
[ ] Flask app updated with logging/metrics initialization
[ ] Logs directory created with correct permissions
[ ] Health endpoints tested and returning 200
[ ] Prometheus metrics endpoint working
[ ] JSON logs created in logs/app.log
[ ] Request correlation IDs present in logs and headers
[ ] Docker Compose stack started successfully
[ ] All 6 Docker services healthy
[ ] Prometheus targets show "UP"
[ ] Prometheus stores metrics over time
[ ] Grafana data source created and tested
[ ] Grafana dashboard working with live metrics
[ ] Kibana index pattern created
[ ] Kibana receives logs from Elasticsearch
[ ] AlertManager configuration loaded
[ ] Alert notifications configured (Slack/Email/PagerDuty)
[ ] No errors in any service logs
[ ] Load test shows expected metric increases
```

---

### Step 14: Documentation Review

Verify all documentation complete:

```bash
# Check MONITORING-SETUP.md
wc -l docs/MONITORING-SETUP.md
# Expected: > 1000 lines

# Check MONITORING-INTEGRATION.md
wc -l docs/MONITORING-INTEGRATION.md
# Expected: > 400 lines

# Verify both are valid Markdown
file docs/MONITORING-SETUP.md docs/MONITORING-INTEGRATION.md
# Expected: both "ASCII text"
```

**Verification:**
```bash
[ ] MONITORING-SETUP.md > 1000 lines
[ ] MONITORING-INTEGRATION.md > 400 lines
[ ] Both files valid Markdown
[ ] All code examples valid
[ ] All configuration files referenced
```

---

## Troubleshooting If Issues Found

### Issue: Prometheus target "DOWN"

**Solution:**
```bash
# 1. Verify Flask is running on port 8000
netstat -tlnp | grep 8000

# 2. Test endpoint directly
curl http://localhost:8000/api/metrics/prometheus | head -5

# 3. Check Flask logs
tail -f logs/app.log | grep -i error

# 4. Verify blueprint registered
grep "register_blueprint(metrics_bp)" backend/app.py
```

### Issue: No logs in Kibana

**Solution:**
```bash
# 1. Check if logs/app.log has content
wc -l logs/app.log

# 2. Verify JSON format
tail logs/app.log | python -m json.tool

# 3. Check Logstash status
docker logs softfactory-logstash | tail -20

# 4. Check Elasticsearch
curl http://localhost:9200/_cat/indices?v

# 5. Force re-read
docker exec softfactory-logstash rm /var/lib/logstash/.sincedb*
docker-compose -f docker-compose.monitoring.yml restart logstash
```

### Issue: High CPU/Memory Usage

**Solution:**
```bash
# 1. Check which service is using resources
docker stats

# 2. Review container logs
docker logs softfactory-elasticsearch  # May need more memory
docker logs softfactory-prometheus     # May need more disk

# 3. Increase resource limits in docker-compose.monitoring.yml
# For Elasticsearch:
#   environment:
#     ES_JAVA_OPTS: -Xms1g -Xmx1g

# 4. Clean up old data
curl -X DELETE http://localhost:9200/softfactory-logs-2026.01.*
```

---

## Sign-Off

Once all checks pass, sign off:

**Name:** ___________________
**Date:** ___________________
**Status:** ✅ Production Ready for Deployment

---

## Next Steps

1. Configure notification channels (Slack webhook, PagerDuty integration key)
2. Baseline metrics for 24 hours
3. Tune alert thresholds from baseline values
4. Train team on incident response procedures
5. Schedule weekly metric reviews

---

**Last Updated:** 2026-02-25
**Questions:** See docs/MONITORING-SETUP.md or contact ops@softfactory.local