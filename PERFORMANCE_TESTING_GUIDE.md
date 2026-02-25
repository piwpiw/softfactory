# SoftFactory Performance Testing & Optimization Guide

Quick reference for running performance tests and implementing optimizations.

---

## Quick Start

### 1. Run Baseline Profiling
```bash
cd /d/Project
python tests/performance/profiler.py
```

**Output**:
- Console: Real-time profiling results with sample times
- File: `performance_baseline.json` (raw metrics)

**Metrics Collected**:
- Response time (min, max, mean, median, p95, p99)
- Success rate
- Error counts
- Throughput (for load tests)

---

### 2. Generate Performance Report
```bash
cd /d/Project
python tests/performance/performance_report_generator.py
```

**Output**:
- File: `docs/PERFORMANCE_REPORT.md` (comprehensive analysis)

**Includes**:
- Baseline performance metrics
- Load test results (50, 100, 500 concurrent)
- Bottleneck analysis with severity ratings
- 7 optimization recommendations
- 3-week implementation roadmap

---

## Recommended Optimizations (Priority Order)

### Phase 1: Week 1 (Quick Wins - 40-50% improvement)

#### 1. Connection Pooling (15 minutes)
```python
# Edit: backend/app.py
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 40,
}
```

#### 2. SQLite WAL Mode (30 minutes)
```python
# Edit: backend/app.py (in create_app function)
from sqlalchemy import event

@event.listens_for(db.engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.close()
```

#### 3. Create Database Indexes (1 hour)
```bash
cd /d/Project
sqlite3 platform.db << EOF
CREATE INDEX IF NOT EXISTS idx_chefs_is_active ON chefs(is_active);
CREATE INDEX IF NOT EXISTS idx_chefs_cuisine ON chefs(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_chef_id ON bookings(chef_id);
CREATE INDEX IF NOT EXISTS idx_sns_posts_status ON sns_posts(status);
EOF
```

#### 4. Implement Caching (1-2 hours)
```bash
pip install Flask-Caching Flask-Compress
```

```python
# Edit: backend/app.py
from flask_caching import Cache
from flask_compress import Compress

def create_app():
    app = Flask(__name__)

    # ... existing config ...

    cache_config = {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300,
    }
    cache = Cache(app, config=cache_config)
    Compress(app)

    return app
```

```python
# Edit: backend/services/coocook.py
from flask_caching import Cache

cache = None  # Passed from app

@coocook_bp.route('/chefs', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_chefs():
    # ... implementation ...
    pass
```

#### 5. Deploy Gunicorn (1-2 hours)
```bash
pip install gunicorn
```

Create `gunicorn_config.py`:
```python
import multiprocessing

bind = '0.0.0.0:8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 30
max_requests = 1000
```

Launch:
```bash
gunicorn -c gunicorn_config.py 'backend.app:create_app()'
```

**Expected Results**:
- Response time: 65-85ms → 30-45ms (45% faster)
- Concurrent capacity: 50 → 150+ (3× improvement)
- Throughput: 15 req/s → 40+ req/s

---

### Phase 2: Week 2 (Query Optimization - 70% total improvement)

#### 1. Fix N+1 Queries (2-4 hours)

Use eager loading with `joinedload`:

```python
# Edit: backend/services/coocook.py
from sqlalchemy.orm import joinedload

@coocook_bp.route('/chefs', methods=['GET'])
def get_chefs():
    # ✅ Fetch all related bookings in single query
    query = Chef.query.options(joinedload('bookings')).filter_by(is_active=True)

    # ... rest of implementation ...

    # Now accessing chef.bookings doesn't trigger additional queries!
    for chef in result.items:
        booking_count = len(chef.bookings)  # ← No new query!
```

**Identify N+1 problems**:
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
# Run requests and look for repeated queries
```

#### 2. Optimize Response Payloads (1-2 hours)

```python
# Reduce unnecessary fields in JSON responses
def create_optimized_response(chef):
    return {
        'id': chef.id,
        'name': chef.name,
        'cuisine': chef.cuisine_type,
        'location': chef.location,
        'price': chef.price_per_session,
        'rating': chef.rating,
        'reviews': chef.rating_count,
        # Removed: bio, user_id, is_active, created_at
    }
```

**Expected Results**:
- Response time: 30-45ms → 15-25ms (70% total improvement)
- Concurrent capacity: 150+ → 300+
- Success rate at 500 concurrent: 94% → 98%+

---

### Phase 3: Week 3+ (Production Monitoring)

#### 1. Implement APM Monitoring (4-8 hours)
```bash
pip install sentry-sdk
```

#### 2. Setup CI/CD Performance Testing (4-6 hours)
- Add performance tests to CI pipeline
- Alert on regression > 10%

#### 3. Database Migration Planning (2-3 weeks)
- Plan PostgreSQL migration
- Create fallback strategy

---

## Testing & Verification

### After Each Phase

```bash
# 1. Run profiling again
python tests/performance/profiler.py

# 2. Generate comparison report
python tests/performance/performance_report_generator.py

# 3. Verify in browser
# Load test: ab -n 1000 -c 50 http://localhost:8000/api/coocook/chefs
```

### Load Testing with Apache Bench
```bash
# Install (macOS)
brew install httpd

# Or (Windows)
choco install apachebench

# Test
ab -n 1000 -c 50 http://localhost:8000/api/coocook/chefs
ab -n 1000 -c 100 http://localhost:8000/api/coocook/chefs
ab -n 1000 -c 500 http://localhost:8000/api/coocook/chefs
```

### Performance Thresholds
| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|-----------|------|-----------|
| Response Time | > 500ms | 200-500ms | 100-200ms | < 50ms |
| Success Rate | < 80% | 80-95% | 95-99% | > 99% |
| Throughput | < 5 req/s | 5-20 req/s | 20-50 req/s | > 50 req/s |

---

## File Reference

### Performance Testing Tools
- `tests/performance/profiler.py` - Baseline profiling & load testing
- `tests/performance/optimizations.py` - Optimization implementations
- `tests/performance/performance_report_generator.py` - Report generation
- `tests/performance/__init__.py` - Module exports

### Reports & Documentation
- `docs/PERFORMANCE_REPORT.md` - Comprehensive analysis (auto-generated)
- `PERFORMANCE_TESTING_GUIDE.md` - This file
- `performance_baseline.json` - Raw metrics (auto-generated)

---

## Common Issues

### "QueuePool size limit exceeded"
→ Increase pool_size in SQLAlchemy config

### Response times still high
→ Check if caching is enabled; verify with SQL logging

### Connection pool not helping
→ Verify WAL mode is enabled on SQLite

### Load test failures increasing with concurrency
→ May need to migrate to PostgreSQL for production scale

---

## Success Checklist

### Phase 1 Complete
- [ ] Connection pooling configured (pool_size >= 20)
- [ ] SQLite WAL mode enabled
- [ ] Database indexes created (5+ indexes)
- [ ] Flask-Caching installed and decorators added
- [ ] Response times < 50ms (mean)
- [ ] 100 concurrent requests: 95%+ success rate

### Phase 2 Complete
- [ ] N+1 queries fixed with joinedload
- [ ] Response payloads optimized (30% smaller)
- [ ] Response times < 20ms (mean)
- [ ] 300+ concurrent capacity
- [ ] Gunicorn deployed with 8+ workers

### Phase 3 Complete
- [ ] APM monitoring active
- [ ] CI/CD performance testing integrated
- [ ] Response times < 15ms (mean)
- [ ] 500+ concurrent capacity with 98%+ success
- [ ] PostgreSQL migration (or SQLite optimized)

---

## Resources

### Tools Used
- **Flask-Caching**: In-memory cache for responses
- **Flask-Compress**: Gzip compression
- **SQLAlchemy**: Query optimization with eager loading
- **Gunicorn**: Production WSGI server
- **APM**: Performance monitoring (Sentry, New Relic, etc.)

### Documentation
- [SQLAlchemy Eager Loading](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html)
- [Flask-Caching](https://flask-caching.readthedocs.io/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/latest/settings.html)
- [SQLite PRAGMA](https://www.sqlite.org/pragma.html)

---

**Last Updated**: 2026-02-25
**Next Review**: After Phase 1 completion (Week 1)
