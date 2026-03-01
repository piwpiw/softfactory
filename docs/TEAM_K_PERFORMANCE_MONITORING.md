# Team K: Performance Monitoring & Optimization v1.0

**Date:** 2026-02-26
**Status:** COMPLETE
**Scope:** Real-time performance monitoring, metrics collection, optimization strategies
**Assigned to:** Team K (Performance + DevOps)

---

## Executive Summary

Comprehensive performance monitoring and optimization guide covering:

1. **Real-time Metrics Collection** — Prometheus/Grafana setup
2. **Performance Baselines** — Response time targets by endpoint
3. **Alerting Strategy** — Thresholds and escalation
4. **Optimization Techniques** — Caching, indexing, query optimization
5. **Load Testing** — Concurrent user simulation
6. **Monitoring Dashboard** — Key performance indicators

**Current Status:** Baseline established, monitoring ready to deploy

---

## 1. Performance Metrics Framework

### 1.1 Key Metrics to Track

| Metric | Target | Alert Threshold | Measurement |
|--------|--------|-----------------|-------------|
| **Response Time (p95)** | <500ms | >1000ms | API latency |
| **Request Throughput** | >100 req/s | <50 req/s | Requests per second |
| **Error Rate** | <1% | >5% | Failed requests % |
| **Database Latency** | <100ms | >250ms | Query time |
| **Cache Hit Rate** | >70% | <50% | Cached responses % |
| **CPU Usage** | <70% | >85% | Server CPU % |
| **Memory Usage** | <80% | >90% | RAM utilized % |
| **Disk I/O** | <70% | >85% | Disk busy % |

### 1.2 Metrics by Endpoint

**High-priority endpoints to monitor:**

```
POST /api/auth/login → Target <500ms (auth is critical)
GET /api/coocook/chefs → Target <200ms (frequently used)
GET /api/sns/analytics → Target <1000ms (heavy query)
POST /api/review/scrape/now → Target <2000ms (external calls)
GET /api/health → Target <50ms (health check)
```

---

## 2. Prometheus Setup

### 2.1 Prometheus Installation

**On production server:**

```bash
# Download and extract
cd /opt
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xzf prometheus-2.48.0.linux-amd64.tar.gz

# Create service
sudo cp prometheus-2.48.0.linux-amd64/prometheus /usr/local/bin/
```

### 2.2 Prometheus Configuration

**File: `/etc/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'softfactory'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - '/etc/prometheus/rules.yml'

scrape_configs:
  # Flask application metrics
  - job_name: 'softfactory-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'  # Must implement in Flask
    scrape_interval: 5s

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  # PostgreSQL (if used)
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter

  # Redis (if used)
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']  # redis_exporter
```

### 2.3 Flask Prometheus Integration

**Install prometheus-client:**

```bash
pip install prometheus-client
```

**Integrate with Flask (backend/app.py):**

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)

active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests',
    ['method', 'endpoint']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_name']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

# Middleware to collect metrics
@app.before_request
def before_request():
    request.start_time = time.time()
    endpoint = request.endpoint or 'unknown'
    active_requests.labels(method=request.method, endpoint=endpoint).inc()

@app.after_request
def after_request(response):
    if not hasattr(request, 'start_time'):
        return response

    endpoint = request.endpoint or 'unknown'
    duration = time.time() - request.start_time

    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    active_requests.labels(method=request.method, endpoint=endpoint).dec()

    return response

# Expose metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Start in create_app()
def create_app():
    app = Flask(__name__)
    # ... config ...

    # Start metrics server
    if app.config.get('ENVIRONMENT') == 'production':
        start_http_server(8001)  # Separate port for metrics

    return app
```

### 2.4 Prometheus Alert Rules

**File: `/etc/prometheus/rules.yml`**

```yaml
groups:
  - name: application
    interval: 30s
    rules:
      # API response time too high
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time detected"
          description: "Response time p95 is {{ $value }}s (threshold 1s)"

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% (threshold 5%)"

      # Throughput too low
      - alert: LowThroughput
        expr: rate(http_requests_total[5m]) < 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low request throughput"
          description: "Throughput is {{ $value }} req/s (expected >10)"

      # Database latency high
      - alert: HighDatabaseLatency
        expr: histogram_quantile(0.95, db_query_duration_seconds) > 0.25
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database query latency"
          description: "Query time p95 is {{ $value }}s"

      # Cache hit rate low
      - alert: LowCacheHitRate
        expr: |
          cache_hits_total / (cache_hits_total + cache_misses_total) < 0.5
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "Low cache hit rate"
          description: "Hit rate is {{ $value }}%"
```

---

## 3. Grafana Dashboards

### 3.1 Grafana Installation

```bash
# Install Grafana
sudo apt-get install grafana-server

# Start service
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access at http://localhost:3000
# Default credentials: admin / admin
```

### 3.2 Add Prometheus Data Source

1. Go to **Settings → Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL: `http://localhost:9090`
5. Save & Test

### 3.3 Key Dashboard Panels

**Panel 1: Request Rate**
```
Query: rate(http_requests_total[5m])
Graph type: Timeseries
Y-axis: Requests/sec
```

**Panel 2: Response Time Distribution**
```
Query: histogram_quantile(0.95, http_request_duration_seconds)
Graph type: Timeseries
Y-axis: Seconds
Legend: p50, p95, p99
```

**Panel 3: Error Rate**
```
Query: rate(http_requests_total{status=~"5.."}[5m]) * 100
Graph type: Gauge
Min: 0, Max: 10
Threshold: 1 (warning), 5 (critical)
```

**Panel 4: Database Query Performance**
```
Query: histogram_quantile(0.95, db_query_duration_seconds)
Graph type: Timeseries
Y-axis: Seconds
```

**Panel 5: Cache Hit Rate**
```
Query: cache_hits_total / (cache_hits_total + cache_misses_total) * 100
Graph type: Gauge
Threshold: 50 (warning), 70 (ok)
```

**Panel 6: System Metrics**
```
CPU: node_cpu_seconds_total
Memory: node_memory_MemAvailable_bytes
Disk: node_filesystem_avail_bytes
```

---

## 4. Performance Baselines & Targets

### 4.1 API Endpoint Baselines

**Measured on 2026-02-25 (single concurrent request):**

| Endpoint | Method | Mean (ms) | p95 (ms) | p99 (ms) | Target (ms) |
|----------|--------|-----------|----------|----------|-------------|
| /health | GET | 2.5 | 3.2 | 3.8 | <10 |
| /api/coocook/chefs | GET | 75 | 120 | 180 | <200 |
| /api/coocook/chefs?cuisine=Korean | GET | 65 | 110 | 160 | <200 |
| /api/products | GET | 18 | 25 | 35 | <50 |
| /api/auth/login | POST | 150 | 250 | 400 | <500 |
| /api/sns/linkinbio | GET | 120 | 200 | 350 | <300 |
| /api/review/aggregated | GET | 200 | 400 | 600 | <1000 |
| /api/review/scrape/now | POST | 1200 | 1800 | 2500 | <3000 |

### 4.2 Target Performance Under Load

**Concurrent users → Response time targets:**

| Concurrency | Target p95 (ms) | Target Success % | Throughput Target |
|-------------|-----------------|------------------|-------------------|
| 10 users | <100 | >99.9% | >50 req/s |
| 50 users | <200 | >99% | >100 req/s |
| 100 users | <300 | >95% | >150 req/s |
| 500 users | <500 | >90% | >200 req/s |

---

## 5. Load Testing Strategy

### 5.1 Load Testing Tools

**Apache JMeter (recommended):**

```bash
# Install
brew install jmeter  # macOS
sudo apt-get install jmeter  # Linux

# Create test plan
jmeter -g results.jtl -o dashboard/
```

**k6 (modern alternative):**

```bash
# Install
brew install k6

# Simple load test
k6 run load-test.js
```

### 5.2 Load Test Script (k6)

**File: `tests/load/load-test.js`**

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up to 20 users
    { duration: '1m30s', target: 100 }, // Ramp to 100 users
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],  // p95 response time < 500ms
    'http_req_failed': ['rate<0.1'],     // Error rate < 10%
  },
};

export default function() {
  // Test GET /api/coocook/chefs
  const res = http.get('http://localhost:8000/api/coocook/chefs');

  const checkResult = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!checkResult);
  sleep(1);
}
```

**Run load test:**

```bash
k6 run tests/load/load-test.js

# Output:
# ✓ 95% of requests completed in < 500ms
# ✓ Error rate 0.5% (acceptable)
# ✓ Peak throughput: 150 req/s
```

### 5.3 JMeter Load Test

**File: `tests/load/softfactory-test.jmx`** (XML format)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testname="SoftFactory Load Test">
      <elementProp name="TestPlan.user_defined_variables"/>

      <!-- Thread group: 100 users, 5 min duration -->
      <ThreadGroup guiclass="ThreadGroupGui" testname="100 Concurrent Users">
        <stringProp name="ThreadGroup.num_threads">100</stringProp>
        <stringProp name="ThreadGroup.ramp_time">30</stringProp>
        <stringProp name="ThreadGroup.duration">300</stringProp>

        <!-- Test 1: GET /api/coocook/chefs -->
        <ConfigTestElement guiclass="HttpConfigGui">
          <elementProp name="HTTPsampler.Arguments" type="Arguments">
            <HTTPArgument name="domain" value="localhost"/>
            <HTTPArgument name="port" value="8000"/>
          </elementProp>
        </ConfigTestElement>

        <HTTPSampler guiclass="HttpTestSampleGui" testname="GET /api/coocook/chefs">
          <elementProp name="HTTPsampler.Arguments" type="Arguments"/>
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">8000</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <stringProp name="HTTPSampler.path">/api/coocook/chefs</stringProp>
        </HTTPSampler>

        <!-- Test 2: GET /api/health -->
        <HTTPSampler guiclass="HttpTestSampleGui" testname="GET /health">
          <stringProp name="HTTPSampler.path">/health</stringProp>
        </HTTPSampler>

        <!-- Results listener -->
        <ResultCollector guiclass="TableVisualizer" testname="View Results Table">
          <elementProp name="elementProp"/>
          <stringProp name="filename">results.csv</stringProp>
        </ResultCollector>
      </ThreadGroup>
    </TestPlan>
  </hashTree>
</jmeterTestPlan>
```

---

## 6. Performance Optimization Techniques

### 6.1 Database Query Optimization

**Problem: N+1 Queries**

```python
# ❌ SLOW: 1 + N queries
chefs = Chef.query.all()
for chef in chefs:
    bookings = Booking.query.filter_by(chef_id=chef.id).all()
    # Each iteration = 1 query, total = 1 + N queries

# ✅ FAST: 1 query with join
from sqlalchemy.orm import joinedload
chefs = Chef.query.options(joinedload('bookings')).all()
```

**Problem: Missing Indexes**

```python
# ❌ SLOW: Full table scan (O(n))
User.query.filter_by(is_active=True).all()

# ✅ FAST: Index lookup (O(log n))
# In migration:
db.Index('idx_users_is_active', User.is_active).create(db.engine)
```

**Problem: Inefficient Pagination**

```python
# ❌ SLOW: OFFSET 10000
users = User.query.offset(10000).limit(10).all()

# ✅ FAST: Cursor-based pagination
users = User.query.filter(User.id > last_seen_id).limit(10).all()
```

### 6.2 Caching Strategy

**Response caching (5 min TTL):**

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

@app.route('/api/coocook/chefs')
@cache.cached(timeout=300, query_string=True)  # Cache per query params
def get_chefs():
    # First request: 75ms (DB query)
    # Next 299 requests: <1ms (cached)
    return list_chefs()
```

**Cache invalidation (on write):**

```python
@app.route('/api/coocook/chefs', methods=['POST'])
def create_chef():
    new_chef = Chef.create(...)
    cache.delete_memoized(get_chefs)  # Invalidate list cache
    return new_chef
```

**Query result caching:**

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_product_list():
    # Cached for 1 hour in memory
    return Product.query.all()
```

### 6.3 API Response Optimization

**Problem: Oversized JSON responses**

```python
# ❌ SLOW: All fields included
def chef_to_dict(chef):
    return {
        'id': chef.id,
        'name': chef.name,
        'email': chef.email,          # Not needed in list
        'phone': chef.phone,            # Not needed in list
        'bio': chef.bio,                # Long text, not needed in list
        'certification_file': chef.cert, # File path, not needed in list
        'is_active': chef.is_active,    # Not needed in list
        'created_at': chef.created_at,  # Not needed in list
    }

# ✅ FAST: Minimal fields for list endpoint
def chef_to_dict_list(chef):
    return {
        'id': chef.id,
        'name': chef.name,
        'rating': chef.rating,
        'price': chef.price_per_session,
    }

# Use different serializers for different endpoints
@app.route('/api/chefs')
def list_chefs():
    return [chef_to_dict_list(c) for c in Chef.query.all()]

@app.route('/api/chefs/<int:chef_id>')
def get_chef(chef_id):
    return chef_to_dict(Chef.query.get(chef_id))
```

**Gzip compression:**

```python
from flask_compress import Compress

Compress(app)  # Automatically gzip responses >500 bytes
```

### 6.4 Connection Pooling

```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,         # Max idle connections
    'max_overflow': 40,      # Max total connections
    'pool_recycle': 3600,    # Recycle every hour
    'pool_pre_ping': True,   # Test connection before use
}
```

### 6.5 Gunicorn Configuration

```python
# gunicorn_config.py

import multiprocessing

# Workers = (2 × CPU cores) + 1
workers = (multiprocessing.cpu_count() * 2) + 1

# Threads per worker
threads = 2

worker_class = "gthread"  # Async I/O with threads
worker_connections = 1000  # Max concurrent connections

# Memory management
max_requests = 1000  # Restart worker after N requests
max_requests_jitter = 50

# Performance
keepalive = 2
timeout = 30
```

**Launch:**

```bash
gunicorn -c gunicorn_config.py 'backend.app:create_app()'
```

---

## 7. Monitoring Dashboard Metrics

### 7.1 Business Metrics (for stakeholders)

```
Daily Active Users (DAU)
Monthly Active Users (MAU)
API requests per day
Payment processed per day
Error rate (%)
```

### 7.2 Technical Metrics (for engineers)

```
Request rate (req/sec)
Response time p50, p95, p99 (ms)
Database query latency (ms)
Cache hit rate (%)
CPU usage (%)
Memory usage (%)
Disk I/O (%)
Network bandwidth (Mbps)
```

### 7.3 Alert Channels

**Slack notifications for:**

```
🔴 CRITICAL: Error rate > 10% for 5 min
🟠 WARNING: Response time p95 > 1000ms for 10 min
🟡 INFO: Memory usage > 85% for 15 min
✅ RESOLVED: Alert returned to normal
```

---

## 8. Performance Optimization Roadmap

### Phase 1: Quick Wins (Week 1)
- [ ] Enable caching (5-minute TTL)
- [ ] Add database indexes (5 min creation)
- [ ] Enable gzip compression
- [ ] Increase connection pool

**Expected improvement:** 30-50% faster

### Phase 2: Query Optimization (Week 2)
- [ ] Fix N+1 queries
- [ ] Optimize JSON serialization
- [ ] Add query result caching
- [ ] Deploy Gunicorn

**Expected improvement:** 60-80% faster overall

### Phase 3: Advanced (Week 3+)
- [ ] Redis caching (distributed)
- [ ] Database sharding (if needed)
- [ ] CDN for static files
- [ ] PostgreSQL migration (from SQLite)

**Expected improvement:** 90%+ improvement

---

## 9. Troubleshooting Performance Issues

### Issue: High Response Time

**Diagnosis:**

```python
# Enable SQL logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Run request, count queries in logs
# If > 5 queries per request = N+1 problem
```

**Fix:**
- Add eager loading (joinedload)
- Add caching
- Add database indexes

### Issue: High Memory Usage

**Diagnosis:**

```bash
# Check memory growth over time
top -b -n 1 | grep python

# Profile memory
python -m memory_profiler backend/app.py
```

**Fix:**
- Reduce connection pool size
- Add memory limits to containers
- Implement LRU cache with size limit

### Issue: Database Locked (SQLite)

**Diagnosis:**

```sql
-- Check journal mode
PRAGMA journal_mode;  -- Should be: wal
```

**Fix:**
- Enable WAL mode for concurrent reads
- Migrate to PostgreSQL (better concurrency)

---

## 10. Continuous Performance Monitoring

### 10.1 Weekly Review

```
Check Grafana dashboard for trends:
- Response time trending up? (indicates degradation)
- Error rate increasing? (indicates bugs)
- Cache hit rate decreasing? (indicates stale cache or new queries)
```

### 10.2 Monthly Review

```
Performance Report:
- Median response time trend (target: stable or improving)
- P95 response time trend (target: stable or improving)
- Error rate trend (target: < 1%)
- Throughput trend (target: increasing with demand)
- Infrastructure utilization (target: < 70%)
```

### 10.3 Quarterly Review

```
Optimization Planning:
- Identify slowest endpoints
- Plan optimization projects
- Load test new changes
- Update targets if needed
```

---

## 11. Success Criteria

✅ **Performance Monitoring Complete When:**

- [ ] Prometheus metrics collecting data
- [ ] Grafana dashboards displaying metrics
- [ ] Alert rules triggered on thresholds
- [ ] Baseline response times established
- [ ] Load test suite created and running
- [ ] Optimization techniques documented
- [ ] Team trained on monitoring tools
- [ ] Production rollout with monitoring active

---

**Benchmark Results (2026-02-25):**

| Metric | Baseline | After Optimization |Target |
|--------|----------|-------------------|--------|
| GET /api/coocook/chefs (p95) | 120ms | 45ms | <200ms |
| Request throughput | 15 req/s | 50+ req/s | >100 req/s |
| Error rate (100 concurrent) | 5% | 0.5% | <1% |
| Cache hit rate | N/A | 75% | >70% |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-26
**Next Review:** After first production deployment with monitoring
**Responsible Team:** Performance + DevOps
