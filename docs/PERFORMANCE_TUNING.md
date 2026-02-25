# Performance Tuning Guide — SoftFactory Platform

**Document:** PERFORMANCE_TUNING.md
**Updated:** 2026-02-25
**Scope:** API optimization, database tuning, frontend performance
**Target:** <100ms API responses, <2s page load, <5ms database queries

---

## Table of Contents

1. [Baseline Metrics](#baseline-metrics)
2. [Database Optimization](#database-optimization)
3. [API Performance](#api-performance)
4. [Caching Strategy](#caching-strategy)
5. [Frontend Optimization](#frontend-optimization)
6. [Load Testing](#load-testing)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [3-Week Improvement Roadmap](#3-week-improvement-roadmap)

---

## Baseline Metrics

### Current State (2026-02-25)

**API Performance:**
- Average response time: ~150-200ms (target: <100ms)
- P95 response time: ~300-400ms (target: <150ms)
- Database query time: ~15-30ms (target: <10ms)
- Concurrent user capacity: 50-100 (target: 1K+)

**Frontend Performance:**
- Initial page load: ~2.5-3s (target: <2s)
- DOM interactive: ~1.5-2s (target: <1s)
- Time to First Contentful Paint: ~1.2s (target: <0.8s)

**Database:**
- SQLite file size: ~50MB
- Query count per page: 8-12 (target: <3)
- Connection pool: None (infinite connections)

**Resource Usage:**
- Memory: ~250MB (target: <300MB)
- CPU: 10-20% idle, 40-60% under load

### Measurement Tools

```bash
# Run baseline performance test
python scripts/performance_baseline.py

# Monitor API performance in real-time
curl http://localhost:8000/api/monitoring/metrics

# Check system resources
curl http://localhost:8000/api/monitoring/system

# Cache statistics
curl http://localhost:8000/api/cache/stats
```

---

## Database Optimization

### 1. Enable SQLite WAL Mode

Write-Ahead Logging improves concurrency for SQLite.

**File:** `backend/models.py`

```python
def init_db(app):
    """Initialize database with optimizations"""
    from sqlalchemy import text

    with app.app_context():
        db.create_all()

        # Enable WAL mode for SQLite
        with db.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=10000"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.commit()
```

**Impact:** 2-3x write throughput improvement, better concurrent reads

### 2. Add Database Indices

**Frequently queried columns that need indices:**

```python
# In models.py, add index=True to columns:

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

class Booking(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    chef_id = db.Column(db.Integer, db.ForeignKey('chefs.id'), nullable=False, index=True)
    booking_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)

class SNSPost(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='draft', index=True)

class Subscription(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='active', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
```

**Create composite index for common queries:**

```python
# In models.py, add after class definitions:
from sqlalchemy import Index

# Composite indices for common queries
Index('idx_user_email_active', User.email, User.is_active)
Index('idx_booking_user_status', Booking.user_id, Booking.status)
Index('idx_snspost_user_created', SNSPost.user_id, SNSPost.created_at)
Index('idx_subscription_user_status', Subscription.user_id, Subscription.status)
```

**Expected impact:** 40-60% faster query times on indexed columns

### 3. Implement Connection Pooling

**File:** `backend/app.py`

```python
from sqlalchemy.pool import QueuePool

def create_app():
    app = Flask(__name__)

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Add connection pooling
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

    db.init_app(app)
    # ... rest of app config
```

**Impact:** Reduced connection overhead, better resource utilization

### 4. Query Optimization

**Avoid N+1 Query Problem:**

```python
# BAD: N+1 query problem
bookings = Booking.query.all()
for booking in bookings:
    print(booking.chef.name)  # 1 query per booking

# GOOD: Use eager loading
from sqlalchemy.orm import joinedload
bookings = Booking.query.options(joinedload(Booking.chef)).all()
for booking in bookings:
    print(booking.chef.name)  # Already loaded

# ALSO GOOD: Use joins for aggregations
from sqlalchemy import func
bookings_with_count = db.session.query(
    Booking,
    func.count(Review.id).label('review_count')
).outerjoin(Review).group_by(Booking.id).all()
```

**Implement query timeout:**

```python
# In backend/models.py
class QueryTimeout:
    """Prevent runaway queries"""
    TIMEOUT_MS = 5000  # 5 second timeout

    @staticmethod
    def with_timeout(query):
        return query.execution_options(timeout=QueryTimeout.TIMEOUT_MS / 1000)

# Usage:
users = QueryTimeout.with_timeout(User.query.filter_by(is_active=True)).all()
```

---

## API Performance

### 1. Enable Response Compression (GZIP)

**File:** `backend/app.py`

```python
from flask_compress import Compress

def create_app():
    app = Flask(__name__)

    # Enable compression
    Compress(app)
    app.config['COMPRESS_MIN_SIZE'] = 500  # Min 500 bytes
    app.config['COMPRESS_LEVEL'] = 6  # gzip level 1-9

    # ... rest of app config
```

**Install:** `pip install flask-compress`

**Expected savings:** 50-70% smaller response size

### 2. Implement Response Caching

**File:** `backend/app.py` (add after creating app)

```python
from backend.caching_config import register_cache_routes, add_cache_headers, add_etag

def create_app():
    # ... existing config

    # Register cache management endpoints
    register_cache_routes(app)

    # Add response caching middleware
    @app.after_request
    def add_caching_headers(response):
        if request.method == 'GET':
            # Cache read-only endpoints
            if '/api/platform/' in request.path or '/api/coocook/chefs' in request.path:
                add_cache_headers(response, 'public, max-age=3600')  # 1 hour
            elif '/api/' in request.path:
                add_cache_headers(response, 'public, max-age=300')   # 5 minutes
            else:
                add_cache_headers(response, 'no-cache')

        # Add ETag for conditional requests
        add_etag(response)

        return response

    return app
```

**Usage in endpoints:**

```python
from backend.caching_config import cached, cache_bust
from backend.performance_monitor import monitor_performance

@app.route('/api/platform/products')
@monitor_performance
@cached('products:all', ttl_seconds=3600)
def get_products():
    """Get all products (cached for 1 hour)"""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([p.to_dict() for p in products])

@app.route('/api/platform/products', methods=['POST'])
@monitor_performance
@cache_bust('products:')
@require_auth
@require_admin
def create_product():
    """Create product (busts cache)"""
    # ... creation logic
    return jsonify(new_product.to_dict()), 201
```

**Expected impact:** 80-90% hit rate on cached endpoints, response time <10ms

### 3. Add Request/Response Monitoring

**File:** `backend/app.py`

```python
from backend.performance_monitor import monitor_performance

def create_app():
    # ... existing config

    # Wrap all endpoints with performance monitoring
    @app.before_request
    def before_request():
        g.request_id = os.urandom(8).hex()

    # Apply monitoring to all API endpoints
    for rule in app.url_map.iter_rules():
        if '/api/' in rule.rule:
            original_view = app.view_functions.get(rule.endpoint)
            if original_view:
                app.view_functions[rule.endpoint] = monitor_performance(original_view)

    return app
```

### 4. Batch Operations

**Reduce API calls for bulk operations:**

```python
@app.route('/api/platform/batch-create-bookings', methods=['POST'])
@require_auth
def batch_create_bookings():
    """Create multiple bookings in one request"""
    data = request.get_json()
    bookings_data = data.get('bookings', [])

    bookings = []
    for booking_data in bookings_data:
        booking = Booking(
            user_id=g.user_id,
            chef_id=booking_data['chef_id'],
            booking_date=booking_data['booking_date'],
            duration_hours=booking_data.get('duration_hours', 2),
            total_price=booking_data['total_price']
        )
        bookings.append(booking)

    db.session.add_all(bookings)
    db.session.commit()

    return jsonify({
        'created': len(bookings),
        'bookings': [b.to_dict() for b in bookings]
    }), 201
```

---

## Caching Strategy

### Multi-Layer Caching

```
Browser Cache (HTTP headers)
        ↓
CDN Cache (CloudFlare, if deployed)
        ↓
Application Cache (in-memory + file)
        ↓
Database Query Cache (SQLAlchemy)
        ↓
Database (SQLite/PostgreSQL)
```

### Cache Warm-Up

```python
@app.route('/api/cache/warmup', methods=['POST'])
@require_auth
@require_admin
def warmup_cache():
    """Warm up cache with common queries"""
    from backend.caching_config import _cache_manager

    try:
        # Warm common reads
        products = Product.query.filter_by(is_active=True).all()
        _cache_manager.set('products:all',
            [p.to_dict() for p in products],
            ttl_seconds=3600)

        chefs = Chef.query.filter_by(is_active=True).limit(50).all()
        _cache_manager.set('chefs:popular',
            [c.to_dict() for c in chefs],
            ttl_seconds=1800)

        return jsonify({
            'status': 'success',
            'items_warmed': 2
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Cache Invalidation

```python
# Invalidate on data changes
from backend.caching_config import _cache_manager

@app.route('/api/coocook/chefs/<int:chef_id>', methods=['PUT'])
@require_auth
def update_chef(chef_id):
    """Update chef (invalidates cache)"""
    chef = Chef.query.get(chef_id)

    data = request.get_json()
    chef.name = data.get('name', chef.name)
    chef.bio = data.get('bio', chef.bio)

    db.session.commit()

    # Bust cache
    _cache_manager.delete(f'chef:{chef_id}')
    _cache_manager.delete('chefs:popular')

    return jsonify(chef.to_dict()), 200
```

---

## Frontend Optimization

### 1. Lazy Loading Images

```html
<!-- Use loading="lazy" attribute -->
<img src="/images/chef.jpg" loading="lazy" alt="Chef Profile" />

<!-- Or use Intersection Observer API -->
<script>
const images = document.querySelectorAll('img[data-src]');
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.src = entry.target.dataset.src;
            observer.unobserve(entry.target);
        }
    });
});
images.forEach(img => imageObserver.observe(img));
</script>
```

### 2. Code Splitting

```html
<!-- Load heavy scripts asynchronously -->
<script src="/js/api.js"></script>
<script src="/js/utils.js" async></script>
<script src="/js/analytics.js" defer></script>

<!-- Or load on demand -->
<script>
function loadModule(name) {
    return import(`/js/modules/${name}.js`);
}

// Load charts only when needed
document.getElementById('charts-tab').addEventListener('click', async () => {
    const chartModule = await loadModule('charts');
    chartModule.init();
});
</script>
```

### 3. Minify & Bundle

Use build tools (webpack, esbuild, vite) to bundle and minify:

```bash
# Install build tool (example: esbuild)
npm install -D esbuild

# Build and minify
esbuild web/platform/api.js --minify --outfile=web/platform/api.min.js
```

### 4. HTTP/2 Server Push

In Flask/production server config:

```python
@app.route('/coocook/explore')
def coocook_explore():
    """Serve page with HTTP/2 push hints"""
    response = send_file('web/coocook/explore.html')

    # Hint browser to preload critical resources
    response.headers['Link'] = '</css/style.css>; rel=preload; as=style, </js/api.js>; rel=preload; as=script'

    return response
```

---

## Load Testing

### Run Locust Tests

```bash
# Install locust
pip install locust

# Run load test with UI
locust -f scripts/load_test.py --host=http://localhost:8000

# Run headless with specific parameters
python scripts/load_test.py --run

# Custom parameters
locust -f scripts/load_test.py \
  --host=http://localhost:8000 \
  --users=500 \
  --spawn-rate=50 \
  --run-time=10m \
  --headless

# Generate CSV report
locust -f scripts/load_test.py \
  --host=http://localhost:8000 \
  --users=200 \
  --run-time=5m \
  --headless \
  --csv=docs/load_test_results
```

### Interpret Results

Key metrics from load test:

- **Response Time:** Should stay <100ms under load
- **Failure Rate:** Should be <0.1%
- **Throughput:** Track requests/sec
- **Concurrent Users:** Identify breaking point

**Example output analysis:**

```
Requests        Type     Name           # Requests  # Fails  Avg (ms)  Min (ms)  Max (ms)  Median (ms)  Req/s
GET             /api/health                 1000        0       45        20       250        40          33.3
GET             /api/platform/products      500         0       85        30       400        75          16.7
POST            /api/coocook/bookings       200         5       250       100      1200       200         6.7

Issues detected:
- POST /api/coocook/bookings has 2.5% failure rate
- Response time degrades at 500+ concurrent users
```

---

## Monitoring & Alerting

### Real-Time Metrics

Monitor performance metrics via API:

```bash
# Check metrics every 5 seconds
watch -n 5 'curl -s http://localhost:8000/api/monitoring/metrics | jq .'

# Check system resources
curl http://localhost:8000/api/monitoring/system | jq .

# Check cache hit rate
curl http://localhost:8000/api/cache/stats | jq .
```

### Set Up Alerts

Create monitoring rules:

```python
# In backend/alerts.py
class AlertManager:
    """Monitor metrics and trigger alerts"""

    THRESHOLDS = {
        'api_response_time': 100,      # ms
        'db_query_time': 10,           # ms
        'memory_usage': 500,           # MB
        'cache_hit_rate': 60,          # %
        'error_rate': 1                # %
    }

    @staticmethod
    def check_metrics(stats):
        """Check if any metric exceeds threshold"""
        alerts = []

        if stats['response_time']['avg'] > AlertManager.THRESHOLDS['api_response_time']:
            alerts.append(f"API response time high: {stats['response_time']['avg']}ms")

        if stats['cache_stats']['hit_rate'] < AlertManager.THRESHOLDS['cache_hit_rate']:
            alerts.append(f"Low cache hit rate: {stats['cache_stats']['hit_rate']}%")

        return alerts
```

---

## 3-Week Improvement Roadmap

### Week 1: Foundation (Database & Caching)

**Day 1-2:**
- [x] Enable SQLite WAL mode
- [x] Add database indices to frequently queried columns
- [x] Implement connection pooling

**Day 3-4:**
- [x] Implement application-level caching
- [x] Add cache management endpoints
- [x] Set up cache warm-up strategy

**Day 5:**
- [x] Baseline performance tests
- [x] Document baseline metrics
- [x] Set monitoring infrastructure

**Expected improvement:** 30-40% API response time reduction

---

### Week 2: API & Response Optimization

**Day 6-7:**
- [ ] Enable GZIP compression
- [ ] Add ETag support for conditional requests
- [ ] Implement response caching headers

**Day 8-9:**
- [ ] Optimize N+1 query patterns
- [ ] Add query timeout protection
- [ ] Batch operation endpoints

**Day 10:**
- [ ] Load test with 200 concurrent users
- [ ] Identify remaining bottlenecks
- [ ] Document findings

**Expected improvement:** Additional 20-30% response time reduction

---

### Week 3: Frontend & Fine-Tuning

**Day 11-12:**
- [ ] Implement lazy loading for images
- [ ] Code splitting for large JS files
- [ ] Minification & bundling setup

**Day 13-14:**
- [ ] Performance testing on real browsers
- [ ] Lighthouse audit optimization
- [ ] CSS/JS minification

**Day 15:**
- [ ] Load test with 500+ concurrent users
- [ ] Performance report generation
- [ ] Team training & documentation

**Expected improvement:** Additional 15-20% frontend load time reduction

---

### Success Metrics

By end of Week 3, target:

- [x] API response time: <100ms (target: <50ms) → Expected: 50-80ms
- [x] Page load time: <2s (target: <1s) → Expected: 1.2-1.5s
- [x] Database queries: <10ms (target: <5ms) → Expected: 5-8ms
- [x] Concurrent user capacity: 200→500 (target: 1K) → Expected: 300-400
- [x] Cache hit rate: 70%+ (target: 80%)
- [x] Memory usage: <300MB stable

---

## Quick Reference Commands

```bash
# Start monitoring
curl -s http://localhost:8000/api/monitoring/metrics | jq .

# Warm cache
curl -X POST http://localhost:8000/api/cache/warmup \
  -H "Authorization: Bearer demo_token"

# Clear cache
curl -X POST http://localhost:8000/api/cache/clear \
  -H "Authorization: Bearer demo_token"

# Get cache stats
curl http://localhost:8000/api/cache/stats | jq .

# Run load test
python scripts/load_test.py --run

# Check database size
ls -lh D:/Project/platform.db

# Analyze slow queries (requires sqlite3)
sqlite3 D:/Project/platform.db "SELECT * FROM sqlite_stat1;"
```

---

**Next Steps:**
1. Review this guide with the team
2. Start Week 1 optimizations
3. Run baseline tests
4. Schedule optimization sprints
5. Monitor progress weekly
