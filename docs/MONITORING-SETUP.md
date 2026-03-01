# SoftFactory Monitoring & Logging Setup
> **Version:** 1.0
> **Updated:** 2026-02-25
> **Status:** Production-Ready
> **Owner:** DevOps Engineering

---

## Executive Summary

This document provides a complete production monitoring and centralized logging strategy for SoftFactory. The implementation includes:

- **Health Checks**: Liveness, readiness, and detailed metrics endpoints
- **Structured Logging**: JSON-formatted logs with request tracing (correlation IDs)
- **Prometheus Integration**: Metric scraping, aggregation, and dashboards
- **Alert Rules**: 15+ automated alerts for availability, performance, and resources
- **ELK Stack**: Elasticsearch/Logstash/Kibana for log aggregation and analysis
- **Runbooks**: Step-by-step incident response procedures

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SoftFactory Monitoring Stack                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Flask API  │ (localhost:8000)
│   (backend)  │
└──────┬───────┘
       │
       ├─► Health Endpoints (Kubernetes-compatible)
       │   ├─ GET /api/metrics/health    (basic liveness)
       │   ├─ GET /api/metrics/ready     (readiness probe)
       │   └─ GET /api/metrics/live      (K8s liveness probe)
       │
       ├─► Metrics Endpoints
       │   ├─ GET /api/metrics/summary        (JSON format)
       │   ├─ GET /api/metrics/prometheus    (Prometheus format)
       │   └─ GET /api/metrics/errors        (error stats)
       │
       └─► Logging
           ├─ File: logs/app.log (JSON-formatted)
           ├─ Console: STDOUT (JSON format)
           └─ Correlation IDs: X-Request-Id header

       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
  ┌─────────────┐                   ┌──────────────────┐
  │ Prometheus  │                   │  Elasticsearch   │
  │ :9090       │                   │  :9200           │
  └─────────────┘                   └──────────────────┘
       │                                    │
       ├─ Scrape /api/metrics/prometheus   │
       │   every 15 seconds                │
       │                                    ├─ Logstash ships logs
       ▼                                    │   (logs/app.log)
  ┌─────────────┐                         │
  │   Grafana   │                         ▼
  │   :3000     │                   ┌──────────────────┐
  │ (Dashboards)│                   │    Kibana        │
  └─────────────┘                   │    :5601         │
                                    │ (Log analysis)   │
                                    └──────────────────┘

Alerting Flow:
  Prometheus Alert Rules → AlertManager (:9093) → Email/Slack/PagerDuty
```

---

## 1. Health Check Implementation

### Endpoints

#### `/api/metrics/health` — Basic Health Check
**Liveness Probe** (used by load balancers and monitoring)

```bash
curl http://localhost:8000/api/metrics/health
```

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-25T10:30:45Z",
  "uptime_seconds": 3600,
  "database": "healthy",
  "api": "ok"
}
```

**Status Codes:**
- `200` — Service healthy
- `503` — Service degraded (database unavailable)

**Used by:** Load balancers, Kubernetes liveness probes

---

#### `/api/metrics/ready` — Readiness Probe
**Kubernetes Readiness Probe** (indicates if service ready for traffic)

```bash
curl http://localhost:8000/api/metrics/ready
```

**Response:**
```json
{
  "ready": true,
  "timestamp": "2026-02-25T10:30:45Z"
}
```

**Checks:**
- Database connectivity
- Critical initialization complete

**Status Codes:**
- `200` — Ready to serve requests
- `503` — Not ready (dependencies unavailable)

---

#### `/api/metrics/live` — Liveness Probe
**Process Liveness** (minimal overhead)

```bash
curl http://localhost:8000/api/metrics/live
```

**Response:**
```json
{
  "alive": true,
  "timestamp": "2026-02-25T10:30:45Z",
  "pid": 1234
}
```

**Always returns `200`** (only checks if Flask process running)

---

#### `/api/metrics/summary` — Detailed Metrics
**Application Metrics** (JSON format)

```bash
curl http://localhost:8000/api/metrics/summary
```

**Response:**
```json
{
  "timestamp": "2026-02-25T10:30:45Z",
  "uptime": {
    "seconds": 3600,
    "human_readable": "1h 0m 0s"
  },
  "system": {
    "cpu_percent": 15.2,
    "memory": {
      "rss_mb": 128.5,
      "vms_mb": 256.3,
      "percent": 25.6
    },
    "process_id": 1234
  },
  "application": {
    "requests_total": 15432,
    "errors_total": 42,
    "error_rate": 0.27
  },
  "database": {
    "status": "healthy",
    "stats": {
      "users": 256,
      "payments": 1024,
      "bookings": 512,
      "sns_posts": 2048,
      "campaigns": 128,
      "ai_employees": 64
    }
  }
}
```

---

#### `/api/metrics/prometheus` — Prometheus Format
**Prometheus Scrape Target** (used by Prometheus for time-series storage)

```bash
curl http://localhost:8000/api/metrics/prometheus
```

**Sample Output:**
```
# HELP softfactory_up Application health status (1=healthy)
# TYPE softfactory_up gauge
softfactory_up 1

# HELP softfactory_uptime_seconds Application uptime in seconds
# TYPE softfactory_uptime_seconds gauge
softfactory_uptime_seconds 3600

# HELP softfactory_requests_total Total HTTP requests received
# TYPE softfactory_requests_total counter
softfactory_requests_total 15432

# HELP softfactory_errors_total Total HTTP errors
# TYPE softfactory_errors_total counter
softfactory_errors_total 42

# HELP softfactory_memory_rss_mb Resident set size in MB
# TYPE softfactory_memory_rss_mb gauge
softfactory_memory_rss_mb 128.5

# HELP softfactory_memory_percent Memory usage percentage
# TYPE softfactory_memory_percent gauge
softfactory_memory_percent 25.6

# HELP softfactory_cpu_percent CPU usage percentage
# TYPE softfactory_cpu_percent gauge
softfactory_cpu_percent 15.2

# HELP softfactory_database_users Total registered users
# TYPE softfactory_database_users gauge
softfactory_database_users 256
...
```

---

## 2. Structured Logging Setup

### Features

All logs are written in **JSON format** for easy machine parsing:

```json
{
  "timestamp": "2026-02-25T10:30:45.123Z",
  "level": "INFO",
  "logger": "backend.platform",
  "message": "Request completed: 200",
  "method": "POST",
  "path": "/api/coocook/bookings",
  "status": 200,
  "content_length": 256,
  "latency_ms": 45.3,
  "request_id": "a1b2c3d4",
  "user_id": 42
}
```

### Configuration

**File:** `backend/logging_config.py`

```python
from backend.logging_config import configure_logging, request_logging_middleware

app = create_app()

# Configure logging (JSON format, 15 levels, correlation IDs)
logger = configure_logging(
    app,
    log_file='logs/app.log',
    debug=False  # Set True in development
)

# Enable request logging middleware
request_logging_middleware(app)
```

### Log Locations

| Log Type | Path | Rotation | Retention |
|----------|------|----------|-----------|
| Application | `logs/app.log` | Daily @ midnight | 30 days (prod), 7 days (dev) |
| Request tracking | `logs/app.log` | Daily | 30 days (prod) |
| Error logs | `logs/errors.log` (optional) | Daily | 90 days |
| Access logs | `logs/access.log` | Daily | 14 days |

### Request ID Tracking (Correlation IDs)

Every request is assigned a unique correlation ID (`request_id`) for end-to-end tracing:

```bash
# Client sends request
curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/coocook/chefs

# Response includes request ID
X-Request-Id: a1b2c3d4
```

**Log Trail Example:**
```json
Request received       → request_id: a1b2c3d4
Auth check            → request_id: a1b2c3d4
Query database        → request_id: a1b2c3d4
Return response       → request_id: a1b2c3d4
Request completed     → request_id: a1b2c3d4
```

**Use Cases:**
- **Debugging**: Track all events for a single request
- **Root cause analysis**: Find when/where error occurred
- **Tracing**: Visualize request flow through system

---

## 3. Monitoring Dashboard Specification

### Key Metrics to Track

#### Availability (SLO: 99.9%)
- `softfactory_up` — Service health (1=up, 0=down)
- `softfactory_database_status` — Database connectivity
- Uptime percentage (rolling 30-day)

#### Performance (SLO: P95 < 1s)
- `softfactory_request_latency_ms` — Response time by endpoint
- Latency percentiles: P50, P90, P95, P99
- Requests per second (RPS)

#### Reliability (SLO: 99.99% success)
- `softfactory_requests_total` — Total requests
- `softfactory_errors_total` — Failed requests (4xx, 5xx)
- Error rate by endpoint, status code, user

#### Resource Utilization
- CPU: % usage (alert at 80%+)
- Memory: % usage (alert at 80%+, critical 95%+)
- Disk: Free space (alert at <10%)
- Database: Size, connections, slow queries

#### Business Metrics
- `softfactory_database_users` — Active users
- `softfactory_database_bookings` — Booking volume
- `softfactory_database_payments` — Revenue transactions
- Subscription counts by product

### Grafana Dashboard Panels

#### Panel 1: System Health (Top)
- Type: Status indicator
- Shows: API status, Database status, Last scrape time
- Alert when: any status != "OK"

#### Panel 2: Request Rate & Errors (Time-series)
- Query: `rate(softfactory_requests_total[5m])`
- Query: `rate(softfactory_errors_total[5m])`
- Show: RPS line (blue), Error rate line (red)
- X-axis: time, Y-axis: requests/sec
- Alert threshold: >5% error rate

#### Panel 3: Response Latency (Percentiles)
- Query: `histogram_quantile(0.50, request_latency_ms)`
- Query: `histogram_quantile(0.95, request_latency_ms)`
- Query: `histogram_quantile(0.99, request_latency_ms)`
- Show: P50 (green), P95 (yellow), P99 (red) lines
- Alert threshold: P95 > 1000ms

#### Panel 4: CPU & Memory Usage
- Query: `softfactory_cpu_percent`
- Query: `softfactory_memory_percent`
- Show: Gauge charts (0-100%)
- Danger zone: Red at 80%+

#### Panel 5: Database Stats (Stat)
- Queries: User count, Booking count, Payment count
- Show: Large numbers with sparkline trends

#### Panel 6: Error Distribution (Pie chart)
- Segment by HTTP status code (200, 400, 401, 403, 500, 503)
- Show: % of total errors

#### Panel 7: Endpoint Performance (Table)
- Columns: Endpoint, Method, Avg Latency, P95, % Errors, RPS
- Sort by: Latency (slowest first)
- Useful for identifying bottlenecks

#### Panel 8: Daily Uptime (Calendar heatmap)
- Show: Green (up) / Red (down) by hour for last 30 days
- Hover: See detailed stats for that hour

### Dashboard JSON Configuration

**Export after creating in Grafana:**
```bash
# Download dashboard JSON from Grafana UI
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/dashboards/uid/softfactory-main \
  -o docs/grafana-dashboard-softfactory.json
```

---

## 4. Log Aggregation & ELK Stack Setup

### Architecture

```
Flask App
  ↓ (logs/app.log)
Logstash
  ↓ (parses JSON)
Elasticsearch
  ↓ (indexes)
Kibana
  ↓ (visualizes)
User Dashboard
```

### Installation

#### 4.1 Elasticsearch (Log Storage)

**Docker:**
```bash
docker run -d \
  --name elasticsearch \
  -e discovery.type=single-node \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -p 9200:9200 \
  -p 9300:9300 \
  docker.elastic.co/elasticsearch/elasticsearch:8.6.0
```

**Verify:**
```bash
curl http://localhost:9200/_health
```

**Expected Output:**
```json
{
  "status": "yellow",
  "number_of_nodes": 1,
  "active_shards": 0
}
```

---

#### 4.2 Logstash (Log Parser/Shipper)

**Configuration File:** `logstash-config/softfactory.conf`

```conf
input {
  file {
    path => "/path/to/logs/app.log"
    start_position => "beginning"
    codec => json
  }
}

filter {
  # Add grok pattern for non-JSON lines (fallback)
  if [type] == "json_event" {
    json {
      source => "message"
    }
  }

  # Parse timestamp to @timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }

  # Add environment tag
  mutate {
    add_field => { "environment" => "production" }
    add_field => { "service" => "softfactory-api" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "softfactory-logs-%{+YYYY.MM.dd}"
  }

  # Also output to stdout for debugging
  stdout {
    codec => rubydebug
  }
}
```

**Docker:**
```bash
docker run -d \
  --name logstash \
  --link elasticsearch \
  -v /path/to/logstash-config:/usr/share/logstash/pipeline \
  -v /path/to/logs:/logs \
  -e "ES_HOST=elasticsearch" \
  docker.elastic.co/logstash/logstash:8.6.0
```

---

#### 4.3 Kibana (Log Visualization)

**Docker:**
```bash
docker run -d \
  --name kibana \
  --link elasticsearch \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  -p 5601:5601 \
  docker.elastic.co/kibana/kibana:8.6.0
```

**Access:** http://localhost:5601

**Setup Index Pattern:**
1. Go to Settings → Index Patterns
2. Create pattern: `softfactory-logs-*`
3. Set timestamp field: `@timestamp`
4. Create

---

### Kibana Dashboards & Queries

#### Dashboard: Request Logging

**Query 1: Failed Requests**
```json
{
  "bool": {
    "must": [
      { "range": { "status": { "gte": 400 } } }
    ]
  }
}
```

**Visualize:** Time-series of 4xx and 5xx errors by status code

---

#### Dashboard: Performance Analysis

**Query: Slow Requests**
```json
{
  "bool": {
    "must": [
      { "range": { "latency_ms": { "gte": 1000 } } }
    ]
  }
}
```

**Visualize:**
- Top 10 slowest endpoints
- Latency distribution histogram
- Request count by endpoint

---

#### Dashboard: Security Events

**Query: Auth Failures**
```json
{
  "bool": {
    "must": [
      { "match": { "message": "Invalid or expired token" } }
    ]
  }
}
```

**Visualize:**
- Failed login attempts over time
- Unique IP addresses with most failures
- User accounts under attack

---

### Log Retention Policy

| Log Type | Elasticsearch Index | Retention | Rotation |
|----------|-------------------|-----------|----------|
| Application | `softfactory-logs-*` | 30 days | Daily |
| Errors | `softfactory-errors-*` | 90 days | Daily |
| Audit (admin actions) | `softfactory-audit-*` | 365 days | Daily |

**Cleanup (automated):**
```bash
# Delete logs older than 30 days
curator --config curator.yml --dry-run delete --filter_list '{ "filtertype": "age", "source": "creation_date", "direction": "older", "unit": "days", "unit_count": 30 }'
```

---

## 5. Prometheus Configuration

### File: `orchestrator/prometheus-config.yml`

See [Prometheus Configuration Reference](#prometheus-configuration-reference) below.

### Running Prometheus

**Docker:**
```bash
docker run -d \
  --name prometheus \
  -v /path/to/orchestrator/prometheus-config.yml:/etc/prometheus/prometheus.yml \
  -v /path/to/orchestrator/alert-rules.yml:/etc/prometheus/alert-rules.yml \
  -p 9090:9090 \
  prom/prometheus:latest
```

**Verify Scraping:**
1. Go to http://localhost:9090
2. Status → Targets
3. Should see `softfactory-api` target with state "UP"

**Verify Metrics:**
1. Go to http://localhost:9090/graph
2. Enter: `softfactory_requests_total`
3. Should see time-series data

---

### Alert Rules: `orchestrator/alert-rules.yml`

**15+ automated alerts covering:**

#### Critical (Page on-call)
- `SoftFactoryDown` — API unreachable
- `CriticalMemoryUsage` — Memory > 95%
- `DatabaseUnhealthy` — Cannot connect to DB

#### High Priority (Quick response)
- `HighErrorRate` — >5% errors
- `SlowResponseTime` — P95 latency > 1s
- `HighMemoryUsage` — Memory > 80%
- `FailedPayments` — Stripe integration errors
- `FailedBackup` — No backup in 24 hours

#### Medium Priority (Plan soon)
- `HighCPUUsage` — CPU > 80% for 10 min
- `DatabaseSizeCritical` — DB > 1GB
- `ServiceRestart` — Unexpected restart
- `ConfigurationChanged` — Config mismatch

#### Informational
- `NoActiveUsers` — No users for 30 min

---

## 6. Alert Management

### AlertManager Configuration

**File:** `orchestrator/alertmanager-config.yml`

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'team-slack'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

  # Route CRITICAL to PagerDuty + Slack
  routes:
    - match:
        severity: CRITICAL
      receiver: 'pagerduty'
      repeat_interval: 15m

    - match:
        severity: HIGH
      receiver: 'team-slack'
      repeat_interval: 30m

receivers:
  - name: 'team-slack'
    slack_configs:
      - channel: '#alerts'
        title: 'SoftFactory Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

**Testing Alert:**
```bash
# Test Slack notification
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "HIGH"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test"
    }
  }]'
```

---

## 7. Runbooks (Incident Response)

### Alert Response Playbook

#### Alert: `SoftFactoryDown`

**Symptoms:**
- Cannot access API
- Health check returns 503

**Root Causes:**
1. Flask process crashed
2. Database connection lost
3. Port 8000 blocked
4. Out of memory (OOM)

**Response Steps:**

```bash
# Step 1: Check if Flask is running
ps aux | grep python | grep flask
# If not found, go to Step 5

# Step 2: Check service logs
tail -f logs/app.log | grep ERROR

# Step 3: Check database
curl http://localhost:8000/api/metrics/summary | jq .database

# If database unhealthy:
  # Check PostgreSQL
  sudo systemctl status postgres
  # Restart if needed
  sudo systemctl restart postgres
  # Wait 30 seconds for readiness

# Step 4: Check memory/CPU
free -h
ps aux --sort=-%mem | head -5

# Step 5: If process crashed, restart
systemctl restart softfactory-api
sleep 10
curl http://localhost:8000/api/metrics/health

# Step 6: If still down, check for OOM killer
journalctl -n 50 | grep -i "killed\|oom"

# Step 7: Escalate to on-call senior engineer
```

**Escalation:** If still down after 5 min → Page on-call

---

#### Alert: `HighErrorRate`

**Symptoms:**
- Error rate > 5% for 5 minutes
- Many 5xx responses in logs

**Response Steps:**

```bash
# Step 1: Check recent errors
grep '"level":"ERROR"' logs/app.log | tail -20 | jq .

# Step 2: Identify affected endpoints
grep 'status.*5[0-9][0-9]' logs/app.log | jq '.path' | sort | uniq -c | sort -rn

# Step 3: Check database health
curl http://localhost:8000/api/metrics/summary | jq .database

# Step 4: Check for known issues
# - Are third-party APIs down? (Stripe, AWS, etc.)
# - Is there a code deployment in progress?

# Step 5: Monitor error rate
watch -n 5 'curl -s http://localhost:8000/api/metrics/errors | jq .error_rate_percent'

# Step 6: If errors continue, check for exceptions
grep 'Traceback\|Exception' logs/app.log | head -5

# Step 7: Roll back recent changes if error rate doesn't drop
git log --oneline -5
git revert <commit-hash>
systemctl restart softfactory-api
```

**Escalation:** Contact development team lead if errors not resolved in 15 min

---

#### Alert: `HighMemoryUsage`

**Symptoms:**
- Memory usage > 80%
- May lead to OOM kill if not addressed

**Response Steps:**

```bash
# Step 1: Get memory breakdown
ps aux --sort=-%mem | head -10

# Step 2: Check for memory leaks in Flask
pip install memory_profiler
python -m memory_profiler backend/app.py

# Step 3: Enable garbage collection logging
export PYTHONUNBUFFERED=1
python -u backend/app.py 2>&1 | grep -i garbage

# Step 4: Increase available memory if on container/VM
# Option A: Restart with more memory
docker run -m 2g softfactory-api

# Option B: Optimize code
# - Check for unbounded lists in loops
# - Use generators for large datasets
# - Add redis caching for frequently accessed data

# Step 5: Monitor
watch -n 2 'curl -s http://localhost:8000/api/metrics/summary | jq .system.memory'

# Step 6: If memory doesn't drop, restart Flask
systemctl restart softfactory-api
```

**Prevention:**
- Set memory limits on containers: `--memory=1g`
- Monitor for memory leaks in CI/CD testing
- Use profiling in staging before production

---

## 8. Integration Checklist

### Flask Integration

**Add to `backend/app.py`:**

```python
from backend.logging_config import configure_logging, request_logging_middleware
from backend.metrics import metrics_bp, register_metrics_middleware

def create_app():
    app = Flask(__name__)

    # ... other config ...

    # Configure logging (JSON format)
    configure_logging(app, log_file='logs/app.log', debug=False)
    request_logging_middleware(app)

    # Register metrics endpoints
    app.register_blueprint(metrics_bp)
    register_metrics_middleware(app)

    return app
```

**Add dependencies to `requirements.txt`:**

```
python-json-logger==2.0.7
psutil==5.9.6
```

**Install:**

```bash
pip install -r requirements.txt
```

---

### Prometheus Integration

**Update `orchestrator/prometheus-config.yml`:**

```yaml
scrape_configs:
  - job_name: 'softfactory-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics/prometheus'
    scrape_interval: 15s
```

---

### Docker Compose (All-in-One Setup)

**File:** `docker-compose.monitoring.yml`

```yaml
version: '3.8'

services:
  flask:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./orchestrator/prometheus-config.yml:/etc/prometheus/prometheus.yml
      - ./orchestrator/alert-rules.yml:/etc/prometheus/alert-rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./orchestrator/alertmanager-config.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-storage:/var/lib/grafana

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.6.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  grafana-storage:
  elasticsearch-data:
```

**Start All Services:**

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 9. Testing & Validation

### Health Check Tests

```bash
# Test all endpoints
chmod +x tests/health-check-tests.sh
./tests/health-check-tests.sh
```

**Script Content:**

```bash
#!/bin/bash

echo "Testing SoftFactory Health Endpoints..."
BASE_URL="http://localhost:8000/api/metrics"

# Test 1: Health check
echo "✓ Health check:"
curl -s $BASE_URL/health | jq .

# Test 2: Readiness probe
echo "✓ Readiness check:"
curl -s $BASE_URL/ready | jq .

# Test 3: Liveness probe
echo "✓ Liveness check:"
curl -s $BASE_URL/live | jq .

# Test 4: Metrics summary
echo "✓ Metrics summary:"
curl -s $BASE_URL/summary | jq .

# Test 5: Prometheus metrics
echo "✓ Prometheus format:"
curl -s $BASE_URL/prometheus | head -20

echo "All tests passed!"
```

---

### Load Test

**Test monitoring under load (using Apache Bench):**

```bash
ab -n 10000 -c 100 http://localhost:8000/api/metrics/health
```

**Monitor during test:**

```bash
# Terminal 1
watch -n 1 'curl -s http://localhost:8000/api/metrics/summary | jq ".system, .application"'

# Terminal 2
tail -f logs/app.log | grep 'Request completed'
```

**Expected:**
- CPU usage increases
- Memory usage increases
- Response times increase (higher latencies)
- Error rate stays < 1%

---

## 10. Production Deployment Checklist

- [ ] Python dependencies installed: `pip install -r requirements.txt`
- [ ] Logging enabled in `backend/app.py`
- [ ] Metrics endpoints verified at `/api/metrics/*`
- [ ] Prometheus configured to scrape endpoints
- [ ] Alert rules deployed to Prometheus
- [ ] Grafana dashboards imported
- [ ] ELK stack running (Elasticsearch, Logstash, Kibana)
- [ ] AlertManager configured with Slack/PagerDuty
- [ ] Log rotation configured (daily @ midnight)
- [ ] Disk space for logs monitored (alert at <10% free)
- [ ] Health check endpoints added to load balancer
- [ ] Kubernetes readiness/liveness probes configured
- [ ] Backup of Prometheus data scheduled
- [ ] Team trained on runbooks and alert response
- [ ] On-call rotation established

---

## 11. Key Files Reference

| File | Purpose |
|------|---------|
| `backend/logging_config.py` | JSON logging setup, request middleware |
| `backend/metrics.py` | Health checks, metrics endpoints |
| `orchestrator/prometheus-config.yml` | Prometheus scrape configuration |
| `orchestrator/alert-rules.yml` | Alert definitions (15+ rules) |
| `orchestrator/alertmanager-config.yml` | Alert routing (Slack, PagerDuty) |
| `docker-compose.monitoring.yml` | All-in-one monitoring stack |
| `docs/MONITORING-SETUP.md` | This document |

---

## 12. Metrics Summary

### Exported Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `softfactory_up` | gauge | Health status (0/1) | — |
| `softfactory_uptime_seconds` | gauge | Uptime in seconds | — |
| `softfactory_requests_total` | counter | Total requests | `method`, `path`, `status` |
| `softfactory_errors_total` | counter | Total errors | `method`, `path`, `status` |
| `softfactory_request_latency_ms` | histogram | Response latency | `method`, `path` |
| `softfactory_memory_rss_mb` | gauge | Memory usage (MB) | — |
| `softfactory_memory_percent` | gauge | Memory % | — |
| `softfactory_cpu_percent` | gauge | CPU % | — |
| `softfactory_database_users` | gauge | User count | — |
| `softfactory_database_payments` | gauge | Payment count | — |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-25 | Initial release: Health checks, metrics, logging, alerts, runbooks |

---

## Support & Escalation

**Questions about monitoring:**
- Email: ops@softfactory.local
- Slack: #monitoring
- PagerDuty: On-call engineer

**Report Bugs:**
- GitHub: https://github.com/softfactory/platform/issues
- Label: `monitoring`

---

**End of Document**
