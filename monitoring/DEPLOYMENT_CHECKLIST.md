# 🚢 Phase 8: Monitoring Stack Deployment Checklist

> **Purpose**: **Project:** SoftFactory
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Phase 8: Monitoring Stack Deployment Checklist 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Project:** SoftFactory
**Phase:** 8 (Final) — Monitoring
**Date:** 2026-02-27
**Status:** ✅ Complete

---

## Objective

Deploy complete monitoring stack with:
- Prometheus metrics collection
- Alertmanager alert routing
- Grafana dashboards
- Health checks and documentation

---

## Pre-Deployment Verification

### Step 1: Configuration Files ✅

- [x] `monitoring/prometheus.yml` — Prometheus configuration
- [x] `monitoring/alerts.yml` — Alert rules (9 rules)
- [x] `monitoring/alertmanager.yml` — Alert routing (enhanced)
- [x] `monitoring/grafana_init.sh` — Grafana bootstrap script
- [x] `monitoring/health_check.sh` — Health verification script
- [x] `docs/MONITORING_GUIDE.md` — Complete documentation

**Verification:**
```bash
cd /d/Project
ls -la monitoring/*.yml monitoring/*.sh
```

Expected output:
```
-rw-r--r-- alertmanager.yml (1,610 bytes)
-rw-r--r-- alerts.yml (2,986 bytes)
-rw-r--r-- prometheus.yml (543 bytes)
-rwxr-xr-x grafana_init.sh
-rwxr-xr-x health_check.sh
```

### Step 2: Backend Integration ✅

- [x] Flask `/metrics` endpoint implemented
- [x] Request telemetry (latency, errors, count)
- [x] Resource metrics (memory, CPU, uptime)
- [x] Active users and scheduled jobs tracking
- [x] Metrics service module created

**Verification:**
```bash
curl http://localhost:8000/metrics | head -30
```

Expected output: Prometheus text-format metrics (HELP + TYPE headers)

### Step 3: Docker Compose Services ✅

- [x] Prometheus container defined
- [x] Alertmanager container defined
- [x] Grafana container defined
- [x] All volumes mounted
- [x] Healthcheck probes configured
- [x] Network connectivity verified

---

## Deployment Steps

### 1️⃣ Start Monitoring Stack

```bash
cd /d/Project

# Start all services
docker compose up -d prometheus alertmanager grafana

# Verify containers are running
docker ps | grep -E "prometheus|alertmanager|grafana"

# Check logs for errors
docker logs softfactory-prometheus --tail 20
docker logs softfactory-alertmanager --tail 20
docker logs softfactory-grafana --tail 20
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    STATUS
abc123...      prom/prometheus:latest   Up 2 minutes (healthy)
def456...      prom/alertmanager:latest Up 2 minutes (healthy)
ghi789...      grafana/grafana:latest   Up 2 minutes (healthy)
```

### 2️⃣ Initialize Grafana Datasources and Dashboards

```bash
# Make script executable
chmod +x /d/Project/monitoring/grafana_init.sh

# Run initialization
bash /d/Project/monitoring/grafana_init.sh

# Expected output:
# [1/5] Waiting for Grafana to be ready...
# ✓ Grafana is ready
# [2/5] Adding Prometheus datasource...
# ✓ Prometheus datasource added (ID: 1)
# ...
# ✓ All monitoring components operational
```

### 3️⃣ Verify All Components

```bash
bash /d/Project/monitoring/health_check.sh
```

**Expected Output:**
```
=== SoftFactory Monitoring Stack Health Check ===
Checking Prometheus... ✓ OK
Checking Alertmanager... ✓ OK
Checking Grafana... ✓ OK
Checking API Metrics... ✓ OK

Prometheus targets: 8 active targets
Alert rules: 9 rules defined
Alertmanager alerts: 0 alerts
Grafana datasources: 2 datasources

✓ All monitoring components operational
```

### 4️⃣ Configure Notifications (Optional)

Edit `/d/Project/monitoring/alertmanager.yml`:

```yaml
# For Slack notifications
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'

# For Email notifications
email_configs:
  - to: 'ops@your-company.com'
    from: 'alertmanager@softfactory.local'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@gmail.com'
    auth_password: 'your-app-password'
```

Restart Alertmanager:
```bash
docker restart softfactory-alertmanager
```

---

## Post-Deployment Testing

### Test 1: Generate Metrics

```bash
# Make several API requests to generate metrics
for i in {1..10}; do
    curl http://localhost:8000/api/auth/signup \
      -H "Content-Type: application/json" \
      -d '{"email":"test'$i'@example.com","password":"Test123456!"}'
done

# Check metrics endpoint
curl http://localhost:8000/metrics | grep "http_requests_total"
```

**Expected:** Request count increases

### Test 2: Prometheus Scraping

```bash
curl http://localhost:9090/api/v1/targets
```

**Expected:** List of targets with `state: "up"`

### Test 3: Alert Evaluation

```bash
curl http://localhost:9090/api/v1/rules
```

**Expected:** 9 alert rules listed

### Test 4: Grafana Dashboards

1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to Dashboards
4. Verify imported dashboards appear
5. Check that Prometheus datasource is connected

**Expected:** At least 5 dashboards visible

---

## Documentation Verification

- [x] `docs/MONITORING_GUIDE.md` — Complete guide
  - Architecture diagram
  - Available metrics (API, PostgreSQL, Redis, Elasticsearch)
  - Alert rules (7 critical, 4 warning)
  - PromQL query examples
  - Grafana dashboard guide
  - Troubleshooting section

- [x] `monitoring/DEPLOYMENT_CHECKLIST.md` — This file

- [x] Inline code documentation
  - `backend/app.py` — `/metrics` endpoint (94 lines)
  - `backend/services/metrics_service.py` — Enhanced metrics (300+ lines)

---

## Metrics Summary

### Exported Metrics (16 total)

**API Performance (7)**
- `http_requests_total` — Total requests by endpoint/method/status
- `http_request_duration_seconds` — Average response time
- `http_slow_requests_total` — Requests >1000ms
- `active_users_gauge` — Active user accounts
- `scheduled_jobs_gauge` — Scheduled background jobs
- `app_uptime_seconds` — Application uptime
- `process_memory_mb` — Process memory usage

**Application Resources (2)**
- `process_cpu_percent` — CPU usage percentage
- Infrastructure metrics from PostgreSQL, Redis, Elasticsearch exporters

**Business Metrics (7)**
- `db_query_count` — Total database queries
- `db_query_duration_ms` — Average query time
- `db_query_errors` — Query errors
- `cache_hits_total` — Cache successes
- `cache_misses_total` — Cache misses
- `auth_successful_logins` — Successful authentications
- `email_sent_total` — Emails sent

---

## Alert Rules Summary

### Critical Severity (5)
1. **ApiDown** — API unreachable for 5 minutes
2. **HighErrorRate** — >5% request failure rate
3. **DatabaseDown** — PostgreSQL unreachable
4. **RedisDown** — Cache unreachable
5. **ElasticsearchDown** — Search engine unreachable

### Warning Severity (4)
1. **HighResponseTime** — >500ms average latency
2. **SlowQueries** — >5 queries exceeding 1s
3. **CacheHitRatioDegraded** — <70% hit ratio
4. **ConnectionPoolNearMax** — >80% connections used

---

## Dashboard Overview

| Dashboard | Source | Metrics |
|-----------|--------|---------|
| Prometheus 2.0 Stats | Grafana Hub #1860 | Prometheus internals |
| Prometheus + Alertmanager | Grafana Hub #3662 | Alert firing, evaluations |
| PostgreSQL Exporter | Grafana Hub #6417 | Database connections, queries |
| Redis Exporter | Grafana Hub #11600 | Cache memory, operations |
| Elasticsearch | Grafana Hub #266 | Cluster health, indices |

---

## Maintenance Tasks

### Daily
- Monitor alert notifications
- Check dashboard health scores

### Weekly
- Review slow queries in Prometheus
- Audit failed authentication attempts
- Verify backup retention

### Monthly
- Prune old metrics (>15 days)
- Update alert thresholds based on trends
- Review error logs in Alertmanager

### Quarterly
- Optimize Prometheus recording rules
- Update Grafana dashboards with new metrics
- Capacity planning based on growth

---

## Troubleshooting Reference

| Issue | Solution |
|-------|----------|
| Prometheus has no targets | Check `prometheus.yml` scrape_configs; verify API is running |
| Grafana cannot connect to Prometheus | Update datasource URL to `http://localhost:9090` |
| Alerts not firing | Check Prometheus alert rules; verify Alertmanager connectivity |
| High disk usage | Reduce Prometheus retention time or scrape interval |
| Slow dashboard loads | Increase Prometheus scrape interval from 15s to 30s |

---

## Sign-Off

**Deployer Name:** ________________
**Date:** ________________
**Approval:** ✅ All systems operational

---

## Rollback Plan

If monitoring stack needs to be disabled:

```bash
# Stop monitoring containers (keep data)
docker compose stop prometheus alertmanager grafana

# OR remove completely (delete volumes)
docker compose down -v prometheus alertmanager grafana
```

**Note:** Flask `/metrics` endpoint will continue to function without Prometheus.

---

## Next Steps (Phase 9+)

1. **Alerting Customization** — Configure Slack/Email/PagerDuty
2. **Custom Dashboards** — Create business-specific visualizations
3. **Performance Tuning** — Optimize Prometheus retention
4. **Integration** — Connect to incident management systems

---

**Document Version:** 1.0
**Last Updated:** 2026-02-27
**Status:** ✅ Production Ready