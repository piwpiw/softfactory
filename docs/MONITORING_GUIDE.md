# 📘 SoftFactory Monitoring Guide

> **Purpose**: SoftFactory is fully instrumented with a production-grade monitoring stack:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Monitoring Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Overview

SoftFactory is fully instrumented with a production-grade monitoring stack:
- **Prometheus** — Metrics collection and storage
- **Alertmanager** — Alert routing and notification
- **Grafana** — Dashboards and visualization
- **Flask app** — Built-in `/metrics` endpoint for Prometheus

**Last Updated:** 2026-02-27
**Status:** ✅ Production Ready

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              SoftFactory API (Flask)                │
│  - Prometheus metrics endpoint (/metrics)           │
│  - Request telemetry (latency, errors, count)       │
│  - Resource metrics (memory, CPU, uptime)           │
└──────────────────┬──────────────────────────────────┘
                   │ Scrape every 15s
                   ▼
┌──────────────────────────────────────┐
│          Prometheus (9090)           │
│  - Stores metrics for 15 days        │
│  - Evaluates alert rules             │
│  - Provides query API                │
└──────────────┬──────────────────┬────┘
               │ Fire alerts      │ Query metrics
               ▼                  ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Alertmanager    │  │      Grafana     │
    │    (9093)        │  │     (3000)       │
    │                  │  │                  │
    │ Routes alerts to:│  │ Dashboards:      │
    │ - Slack          │  │ - API Performance│
    │ - Email          │  │ - Infrastructure │
    │ - PagerDuty      │  │ - Database       │
    │ - Webhooks       │  │ - Cache          │
    └──────────────────┘  └──────────────────┘
```

---

## Dashboard Access

| Component | URL | Credentials |
|-----------|-----|-------------|
| **Prometheus** | http://localhost:9090 | None (public) |
| **Alertmanager** | http://localhost:9093 | None (public) |
| **Grafana** | http://localhost:3000 | admin / admin |
| **API Metrics** | http://localhost:8000/metrics | None (public) |

---

## Available Metrics

### API Metrics (exported by Flask)

```
http_requests_total{endpoint, method, status}
  ↳ Total HTTP requests by endpoint, method, and outcome
  ↳ Example: http_requests_total{endpoint="/api/auth/login", method="POST", status="success"} 45

http_request_duration_seconds{endpoint, method}
  ↳ Average HTTP response time in seconds
  ↳ Example: http_request_duration_seconds{endpoint="/api/products", method="GET"} 0.0342

http_slow_requests_total{endpoint, method}
  ↳ Requests exceeding 1000ms SLA threshold
  ↳ Example: http_slow_requests_total{endpoint="/api/search", method="GET"} 3

active_users_gauge
  ↳ Number of active user accounts
  ↳ Example: active_users_gauge 142

scheduled_jobs_gauge
  ↳ Number of scheduled background jobs
  ↳ Example: scheduled_jobs_gauge 8

app_uptime_seconds
  ↳ Application uptime in seconds
  ↳ Example: app_uptime_seconds 86400

process_memory_mb
  ↳ Process RSS memory in MB
  ↳ Example: process_memory_mb 256.4

process_cpu_percent
  ↳ Process CPU usage percentage
  ↳ Example: process_cpu_percent 12.3
```

### Infrastructure Metrics (from exporters)

#### PostgreSQL (via postgres-exporter)
```
pg_up                              — Database availability
pg_stat_activity_count             — Active connections
pg_stat_statements_mean_exec_time   — Query response time
pg_table_live_tuples{tablename}    — Row counts by table
```

#### Redis (via redis-exporter)
```
redis_up                           — Cache availability
redis_connected_clients            — Active client connections
redis_memory_used_bytes            — Memory usage
redis_commands_processed_total     — Commands per second
redis_instantaneous_ops_per_sec    — Real-time operations
```

#### Elasticsearch (direct scrape)
```
elasticsearch_cluster_health_status  — Cluster health (0=red, 1=yellow, 2=green)
elasticsearch_indices_docs_total    — Total indexed documents
elasticsearch_indices_store_size_bytes — Index storage size
elasticsearch_jvm_memory_used_bytes — JVM memory used
```

---

## Alert Rules

### Critical Alerts (Severity: critical)

| Alert | Condition | Action |
|-------|-----------|--------|
| **ApiDown** | API unreachable for 5min | Email ops + Webhook |
| **HighErrorRate** | >5% requests fail | Email ops + Slack |
| **DatabaseDown** | PostgreSQL unreachable | Email ops + PagerDuty |
| **RedisDown** | Cache unreachable | Email ops + Webhook |
| **ElasticsearchDown** | Search engine unreachable | Email ops + Webhook |
| **DiskSpaceLow** | <10% disk space free | Email ops + Alert |
| **MemoryUsageHigh** | >90% memory used | Email ops + Alert |

### Warning Alerts (Severity: warning)

| Alert | Condition | Action |
|-------|-----------|--------|
| **HighResponseTime** | >500ms average latency | Slack #alerts-warning |
| **SlowQueries** | >5 queries exceeding 1s | Slack #alerts-warning |
| **CacheHitRatioDegraded** | <70% Redis hit ratio | Slack #alerts-warning |
| **ConnectionPoolNearMax** | >80% connections used | Slack #alerts-warning |

### Info Alerts (Severity: info)

Informational alerts are grouped and sent to webhook only.

---

## Prometheus Queries (PromQL)

### API Performance

```promql
# Average response time per endpoint (last 5 minutes)
avg(http_request_duration_seconds) by (endpoint)

# Request rate (requests per second)
rate(http_requests_total[1m]) by (endpoint)

# Error rate percentage
(rate(http_requests_total{status="error"}[5m]) /
 rate(http_requests_total[5m])) * 100

# Slow requests (>1s) count over time
increase(http_slow_requests_total[1h])
```

### Infrastructure Health

```promql
# PostgreSQL connection count
pg_stat_activity_count

# Redis memory usage (in MB)
redis_memory_used_bytes / 1024 / 1024

# Elasticsearch cluster health
elasticsearch_cluster_health_status

# Elasticsearch indices count
count(elasticsearch_indices_docs_total)
```

### Resource Usage

```promql
# API process memory trend
rate(process_memory_mb[5m])

# CPU usage percentage
process_cpu_percent

# Application uptime
app_uptime_seconds

# Active user count
active_users_gauge
```

---

## Grafana Dashboards

### Available Dashboards

1. **SoftFactory API Performance**
   - Request rate, error rate, response time
   - P50/P95/P99 latencies
   - Slow requests count
   - Active users over time

2. **Infrastructure Status**
   - PostgreSQL health and connections
   - Redis memory and hit ratio
   - Elasticsearch cluster status
   - Disk space and system load

3. **Application Resources**
   - Memory usage trend
   - CPU usage percentage
   - Uptime timeline
   - Scheduled jobs count

### Creating Custom Dashboards

1. Navigate to http://localhost:3000
2. Click **"+"** → **"Dashboard"**
3. Click **"Add a new panel"**
4. Select **Prometheus** as data source
5. Enter PromQL query (see examples above)
6. Customize visualization (Graph, Gauge, Table, etc.)
7. Save dashboard

---

## Alert Configuration

### Receiving Alerts

#### Email Notifications
Edit `/monitoring/alertmanager.yml`:
```yaml
email_configs:
  - to: 'ops@your-company.com'
    from: 'alertmanager@softfactory.local'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@gmail.com'
    auth_password: 'your-app-password'
```

#### Slack Notifications
Edit `/monitoring/alertmanager.yml`:
```yaml
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: '[{{ .Status }}] {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### PagerDuty Integration
```yaml
pagerduty_configs:
  - routing_key: 'YOUR_PAGERDUTY_ROUTING_KEY'
    description: '{{ .GroupLabels.alertname }}'
```

### Webhook Integration

Receive alert JSON at your custom endpoint:
```bash
curl -X POST http://localhost:5001/alerts \
  -H "Content-Type: application/json" \
  -d '{"alerts": [...], "status": "firing"}'
```

---

## Deployment Checklist

- [ ] Prometheus container running: `docker ps | grep prometheus`
- [ ] Alertmanager container running: `docker ps | grep alertmanager`
- [ ] Grafana container running: `docker ps | grep grafana`
- [ ] API metrics endpoint responsive: `curl http://localhost:8000/metrics`
- [ ] Prometheus targets healthy: `http://localhost:9090/targets`
- [ ] Alert rules loaded: `http://localhost:9090/rules`
- [ ] Grafana datasources created: `http://localhost:3000/datasources`
- [ ] Notification channels tested

### Run Health Check

```bash
bash monitoring/health_check.sh
```

Expected output:
```
=== SoftFactory Monitoring Stack Health Check ===
Checking Prometheus... ✓ OK
Checking Alertmanager... ✓ OK
Checking Grafana... ✓ OK
Checking API Metrics... ✓ OK

✓ All monitoring components operational
```

---

## Troubleshooting

### Prometheus Not Scraping API

**Issue:** No targets visible at `http://localhost:9090/targets`

**Solution:**
```bash
# Check Prometheus logs
docker logs softfactory-prometheus

# Verify Flask app is running
curl http://localhost:8000/health

# Verify metrics endpoint
curl http://localhost:8000/metrics | head -20
```

### Grafana Cannot Connect to Prometheus

**Issue:** "No data" on dashboards

**Solution:**
1. Go to http://localhost:3000/datasources
2. Edit "Prometheus" datasource
3. Change URL from `http://prometheus:9090` to `http://localhost:9090`
4. Click "Test" button
5. Save

### Alerts Not Firing

**Issue:** Alert rules defined but no notifications

**Solution:**
1. Check Prometheus rule evaluation: `http://localhost:9090/rules`
2. Verify Alertmanager can receive alerts:
   ```bash
   curl http://localhost:9093/api/v1/alerts
   ```
3. Test notification webhook:
   ```bash
   curl -X POST http://localhost:5001/alerts \
     -H "Content-Type: application/json" \
     -d '{"alerts": [{"status": "firing", "labels": {"alertname": "TestAlert"}}]}'
   ```

### Docker Compose Services Not Starting

**Issue:** `docker compose up` fails

**Solution:**
```bash
# Stop all containers
docker compose down

# Remove volumes to reset state
docker volume rm softfactory_prometheus_data
docker volume rm softfactory_alertmanager_data
docker volume rm softfactory_grafana_data

# Start fresh
docker compose up -d
```

---

## Performance Tuning

### Prometheus Storage

**Current configuration:** 15-day retention

To adjust retention:
```bash
# Edit docker-compose.yml
prometheus:
  command: >
    --config.file=/etc/prometheus/prometheus.yml
    --storage.tsdb.retention.time=30d
    --storage.tsdb.retention.size=50GB
```

### Grafana Dashboard Loading

Large dashboards may load slowly. Optimize by:
- Reducing query time range (use relative instead of absolute)
- Increasing scrape interval from 15s to 30s (trades off granularity)
- Using recording rules for complex queries

---

## Best Practices

1. **Alert Fatigue Prevention**
   - Set appropriate thresholds (not too sensitive)
   - Use inhibition rules to suppress lower-severity alerts
   - Regularly review and tune rules

2. **Dashboard Design**
   - Group related metrics (API, Infrastructure, Resources)
   - Use appropriate visualization (Graph for trends, Gauge for current)
   - Document dashboard purpose in description

3. **Retention Policy**
   - Keep detailed metrics for 7-15 days
   - Archive important metrics for 90 days
   - Delete old data to manage disk space

4. **Alerting Strategy**
   - Critical alerts → Immediate notification (ops on-call)
   - Warning alerts → Delayed notification (investigation)
   - Info alerts → Log only

---

## Related Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Dashboarding](https://grafana.com/docs/grafana/latest/dashboards/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

## Support

For issues or questions:
1. Check `/monitoring/health_check.sh` output
2. Review component logs in `docker logs`
3. Verify configuration files in `/monitoring/`
4. Consult troubleshooting section above

**Last Verified:** 2026-02-27
**Certification:** ✅ Production Ready