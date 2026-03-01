# 📝 Scalability Optimization — Implementation Checklist

> **Purpose**: **Database Index Creation:**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Scalability Optimization — Implementation Checklist 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> Quick reference for engineers implementing each phase
> **Last Updated:** 2026-02-25

---

## PHASE 1: Database Optimization + Caching (2 weeks)

### Week 1: Database & Connection Pooling

**Database Index Creation:**
- [ ] Review slow query logs (enable in PostgreSQL)
  ```bash
  # In postgresql.conf
  log_min_duration_statement = 1000  # Log queries > 1s
  ```
- [ ] Create compound indexes
  ```sql
  CREATE INDEX CONCURRENTLY idx_chef_active_cuisine ON chefs(is_active, cuisine_type);
  CREATE INDEX CONCURRENTLY idx_booking_user_date ON bookings(user_id, booking_date DESC);
  CREATE INDEX CONCURRENTLY idx_campaign_status ON campaigns(status, created_at DESC);
  CREATE INDEX CONCURRENTLY idx_sns_post_status ON sns_posts(status, scheduled_at);
  ```
- [ ] Run ANALYZE to update statistics
  ```sql
  ANALYZE;
  ```
- [ ] Verify index usage with EXPLAIN ANALYZE

**Connection Pooling:**
- [ ] Update `backend/models.py`:
  ```python
  from sqlalchemy.pool import QueuePool

  SQLALCHEMY_ENGINE_OPTIONS = {
      'poolclass': QueuePool,
      'pool_size': 20,
      'max_overflow': 10,
      'pool_recycle': 3600,
      'pool_pre_ping': True,
  }
  ```
- [ ] Test with load tool: `locust`
- [ ] Monitor pool exhaustion: Add logging
  ```python
  @event.listens_for(Pool, "connect")
  def log_pool(dbapi_conn, connection_record):
      print(f"Pool size: {dbapi_conn.pool.size()}")
  ```

**PostgreSQL Tuning:**
- [ ] Update postgresql.conf:
  ```
  shared_buffers = 4GB
  effective_cache_size = 12GB
  work_mem = 20MB
  max_parallel_workers = 4
  ```
- [ ] Restart PostgreSQL and verify with `SELECT version();`

### Week 1: Redis Cache Setup

**Infrastructure:**
- [ ] Provision Redis 5.0+ instance
  - AWS: ElastiCache (cache.t3.small = $20/month)
  - Docker: `docker run -d -p 6379:6379 redis:7-alpine`
  - OR: Docker-compose addition to project
- [ ] Test connectivity: `redis-cli ping` → PONG

**Code Changes:**
- [ ] Add to `requirements.txt`:
  ```
  redis==5.0.0
  flask-caching==2.0.2
  ```
- [ ] Update `backend/app.py`:
  ```python
  from flask_caching import Cache

  app.config['CACHE_TYPE'] = 'RedisCache'
  app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
  cache = Cache(app)
  ```
- [ ] Add cache decorators to high-traffic endpoints:
  ```python
  @app.route('/api/coocook/chefs')
  @cache.cached(timeout=300, query_string=True)
  def get_chefs():
      # ...
  ```
- [ ] Implement cache invalidation on updates:
  ```python
  @coocook_bp.route('/chefs/<int:chef_id>', methods=['PUT'])
  def update_chef(chef_id):
      # ... update logic ...
      cache.delete(f'chef:{chef_id}')
      cache.delete('chefs:active:count')
  ```

**Testing:**
- [ ] Verify cache hits: Monitor Redis with `redis-cli MONITOR`
- [ ] Check cache hit ratio:
  ```bash
  redis-cli INFO stats | grep hits
  ```
- [ ] Unit tests for cache decorators

### Week 2: Gunicorn Optimization

**Configuration:**
- [ ] Create `gunicorn.conf.py` in project root:
  ```python
  import multiprocessing

  workers = multiprocessing.cpu_count() * 2 + 1  # For 4-core: 9
  worker_class = "sync"
  max_requests = 1000
  max_requests_jitter = 100
  worker_connections = 1000
  timeout = 30
  keepalive = 2
  preload_app = True
  ```
- [ ] Update `start_platform.py` or deployment command:
  ```bash
  gunicorn -c gunicorn.conf.py backend.app:create_app()
  ```
- [ ] Test with 4-8 cores (AWS t3.large = 2 vCPU, so 9 workers)

**Load Testing:**
- [ ] Install locust: `pip install locust`
- [ ] Create `locustfile.py`:
  ```python
  from locust import HttpUser, task, between

  class SoftFactoryUser(HttpUser):
      wait_time = between(1, 3)

      @task
      def get_chefs(self):
          self.client.get("/api/coocook/chefs")

      @task
      def search_campaigns(self):
          self.client.get("/api/review/campaigns")
  ```
- [ ] Run load test:
  ```bash
  locust -f locustfile.py --host=http://localhost:8000 \
      --users=1000 --spawn-rate=50 --run-time=5m
  ```
- [ ] Record baseline metrics:
  - Concurrent users: 100 → 1,000
  - p99 latency: 100ms → 50ms
  - Error rate: <0.1%

**Static File Optimization:**
- [ ] Configure HTTP caching headers:
  ```python
  @app.after_request
  def add_cache_headers(response):
      if response.status_code == 200:
          response.headers['Cache-Control'] = 'public, max-age=3600'
      return response
  ```
- [ ] Gzip responses: Flask does this automatically with gzip middleware

### Phase 1 Verification

**Metrics:**
- [ ] Database query latency: <50ms (p99) ✓
- [ ] Cache hit ratio: >50% ✓
- [ ] Concurrent users: 1K ✓
- [ ] RPS: 50-100 ✓
- [ ] Error rate: <0.1% ✓

**Documentation:**
- [ ] Update `docs/DEPLOYMENT.md` with new indexes
- [ ] Document cache key format in code comments
- [ ] Add Gunicorn tuning guide to `docs/`

---

## PHASE 2: Async Processing + Database Replication (4 weeks)

### Week 1: Celery + Redis Job Queue

**Infrastructure:**
- [ ] Ensure Redis running (can reuse Phase 1 instance with separate DB)
- [ ] Add to `requirements.txt`:
  ```
  celery==5.3.4
  ```

**Code:**
- [ ] Create `core/tasks.py`:
  ```python
  from celery import Celery
  import os

  celery_app = Celery('softfactory')
  celery_app.conf.broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/2')
  celery_app.conf.result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/3')

  @celery_app.task
  def post_to_sns(user_id, post_id):
      from backend.models import db, SNSPost
      post = SNSPost.query.get(post_id)
      # Actual posting logic
      post.status = 'published'
      db.session.commit()

  @celery_app.task
  def send_email(user_id, email_type):
      # Email sending logic
      pass
  ```

- [ ] Update service endpoints to use async tasks:
  ```python
  from core.tasks import post_to_sns

  @sns_bp.route('/schedule', methods=['POST'])
  @require_auth
  def schedule_post():
      post = SNSPost(...)
      db.session.add(post)
      db.session.commit()

      # Queue async job (return immediately)
      post_to_sns.delay(g.user_id, post.id)

      return jsonify({'status': 'scheduled'}), 202  # Accepted
  ```

**Testing:**
- [ ] Test celery task: `celery -A core.tasks worker --loglevel=info`
- [ ] Send test message: `post_to_sns.delay(1, 1)`
- [ ] Verify in Redis: `redis-cli LLEN celery`

### Week 2: Database Read Replicas

**Infrastructure Setup:**
- [ ] Provision 2 read replicas of PostgreSQL master
  - AWS RDS: Create read replica in console (5 min)
  - OR Docker: Run 3x PostgreSQL containers (master + 2 replicas)
  ```yaml
  # docker-compose addition
  db-replica-1:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: softfactory
    volumes:
      - postgres_replica_1:/var/lib/postgresql/data
  db-replica-2:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: softfactory
    volumes:
      - postgres_replica_2:/var/lib/postgresql/data
  ```

**Replication Setup:**
- [ ] Enable streaming replication in PostgreSQL master:
  ```sql
  -- On master
  ALTER SYSTEM SET wal_level = replica;
  ALTER SYSTEM SET max_wal_senders = 10;
  ALTER SYSTEM SET max_replication_slots = 10;
  SELECT pg_reload_conf();
  ```
- [ ] Create replication user:
  ```sql
  CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replicator_password';
  ```
- [ ] Start replica instances (they'll automatically sync)

**Code Changes:**
- [ ] Create read/write router:
  ```python
  # backend/db_router.py
  from sqlalchemy import create_engine

  master_engine = create_engine(os.getenv('DATABASE_URL_MASTER'))
  replica_engine = create_engine(os.getenv('DATABASE_URL_REPLICA'))

  def get_chef_listings(page=1):
      # Read from replica (ok to be slightly stale)
      with replica_engine.connect() as conn:
          result = conn.execute(
              "SELECT * FROM chefs WHERE is_active=true LIMIT 20 OFFSET ?",
              (page * 20,)
          )
          return result.fetchall()
  ```

- [ ] Update high-traffic read endpoints:
  ```python
  from backend.db_router import get_chef_listings

  @coocook_bp.route('/chefs')
  def get_chefs():
      chefs = get_chef_listings()
      return jsonify([c.to_dict() for c in chefs])
  ```

**Monitoring:**
- [ ] Check replication lag:
  ```sql
  SELECT slot_name, restart_lsn FROM pg_replication_slots;
  ```
- [ ] Add alert if lag > 1 second

### Week 3: Redis Session Store

**Code:**
- [ ] Add to `requirements.txt`:
  ```
  flask-session==0.5.0
  ```

- [ ] Update `backend/app.py`:
  ```python
  from flask_session import Session
  import redis

  app.config['SESSION_TYPE'] = 'redis'
  app.config['SESSION_REDIS'] = redis.from_url(
      os.getenv('REDIS_URL', 'redis://localhost:6379/1')
  )
  Session(app)
  ```

**Testing:**
- [ ] Verify session persistence across restarts
- [ ] Test multiple instances reading same session

### Week 4: Load Testing & Optimization

**Load Test:**
- [ ] Run with 10K concurrent users:
  ```bash
  locust -f locustfile.py --host=http://localhost:8000 \
      --users=10000 --spawn-rate=100 --run-time=10m
  ```

**Metrics:**
- [ ] Record:
  - Concurrent users: 10,000 ✓
  - p99 latency: <200ms ✓
  - Cache hit ratio: 80% ✓
  - Async job success rate: 99.9% ✓
  - Database lag: <1 sec ✓

---

## PHASE 3: Microservices Migration (8 weeks)

### Week 1-2: CooCook Service Design

**Architecture:**
- [ ] Design CooCook API spec (OpenAPI/Swagger)
  - [ ] List chefs: GET /chefs?page=1&per_page=12
  - [ ] Book chef: POST /bookings
  - [ ] Get reviews: GET /bookings/{id}/reviews
  - [ ] Rate chef: POST /reviews

- [ ] Design database schema (dedicated to CooCook)
  - [ ] Chef table
  - [ ] Booking table
  - [ ] Review table
  - [ ] Copy data from main database

- [ ] Create project structure:
  ```
  coocook-service/
  ├── main.py
  ├── models.py
  ├── schemas.py
  ├── routers/
  │   ├── chefs.py
  │   ├── bookings.py
  │   └── reviews.py
  ├── requirements.txt
  ├── Dockerfile
  └── docker-compose.yml
  ```

### Week 2-3: Extract CooCook Service

**Code Implementation:**
- [ ] Create FastAPI app:
  ```python
  # coocook-service/main.py
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI()

  # Add routers
  from routers import chefs, bookings, reviews

  app.include_router(chefs.router)
  app.include_router(bookings.router)
  app.include_router(reviews.router)
  ```

- [ ] Implement routers (FastAPI):
  ```python
  # coocook-service/routers/chefs.py
  from fastapi import APIRouter, HTTPException
  from sqlalchemy.orm import Session

  router = APIRouter(prefix="/chefs", tags=["chefs"])

  @router.get("/")
  async def list_chefs(page: int = 1, per_page: int = 12, db: Session = Depends(get_db)):
      chefs = db.query(Chef).filter(Chef.is_active == True).offset((page-1)*per_page).limit(per_page).all()
      return chefs
  ```

- [ ] Migrate data from monolith:
  ```python
  # scripts/migrate_coocook_data.py
  from sqlalchemy import create_engine
  import pandas as pd

  source_db = create_engine('postgresql://user:pass@localhost/softfactory')
  target_db = create_engine('postgresql://user:pass@localhost:5433/coocook')

  # Copy chefs table
  chefs_df = pd.read_sql('SELECT * FROM chefs', source_db)
  chefs_df.to_sql('chefs', target_db, if_exists='append', index=False)
  ```

- [ ] Verify data consistency:
  ```bash
  python scripts/verify_migration.py
  ```

### Week 3: Set Up API Gateway (Kong)

**Infrastructure:**
- [ ] Deploy Kong API Gateway:
  ```bash
  docker run -d -p 8001:8001 -p 8000:8000 \
      -e KONG_DATABASE=postgres \
      -e KONG_PG_HOST=postgres \
      kong:latest
  ```

- [ ] Register services:
  ```bash
  # Add Platform service
  curl -i -X POST http://localhost:8001/services \
    -d "name=platform" \
    -d "url=http://platform-app:8000"

  # Add CooCook service
  curl -i -X POST http://localhost:8001/services \
    -d "name=coocook" \
    -d "url=http://coocook-service:8000"
  ```

- [ ] Add routes:
  ```bash
  curl -i -X POST http://localhost:8001/services/platform/routes \
    -d "name=platform-routes" \
    -d "paths[]=/api/auth" \
    -d "paths[]=/api/payment"

  curl -i -X POST http://localhost:8001/services/coocook/routes \
    -d "name=coocook-routes" \
    -d "paths[]=/api/coocook"
  ```

- [ ] Test routing:
  ```bash
  curl http://localhost:8000/api/coocook/chefs
  # Should route to coocook service
  ```

### Week 4: Service Integration & Testing

**Integration Tests:**
- [ ] Test service-to-service communication:
  ```python
  # Platform service calls CooCook service
  response = requests.get('http://coocook-service:8000/chefs')
  assert response.status_code == 200
  ```

- [ ] Test API Gateway routing:
  ```bash
  curl http://api-gateway:8000/api/coocook/chefs
  # Should get chefs from CooCook service
  ```

- [ ] Test data consistency:
  ```python
  # Verify monolith and new service return same data
  monolith_chefs = requests.get('http://monolith:8000/api/coocook/chefs').json()
  coocook_chefs = requests.get('http://coocook-service:8000/chefs').json()
  assert len(monolith_chefs) == len(coocook_chefs)
  ```

### Week 5: SNS Auto Service Extraction (similar to CooCook)

### Week 6: Review Service Extraction (similar to CooCook)

### Week 7-8: Full Integration & Load Testing

**Final Load Test:**
- [ ] 100,000 concurrent users
- [ ] Distributed across 5 services
- [ ] Verify:
  - [ ] p99 latency: <100ms ✓
  - [ ] Error rate: <0.01% ✓
  - [ ] Service isolation working ✓
  - [ ] Independent scaling ✓

---

## Operational Checklist

### Monitoring Setup

- [ ] Install Prometheus exporter:
  ```python
  from prometheus_client import Counter, Histogram, generate_latest

  http_requests_total = Counter('http_requests_total', 'Total requests')
  request_duration = Histogram('request_duration_seconds', 'Request duration')
  ```

- [ ] Create Grafana dashboards:
  - [ ] Request latency (p50, p95, p99)
  - [ ] Error rate
  - [ ] Cache hit ratio
  - [ ] Database connections
  - [ ] Worker CPU/memory usage
  - [ ] Service health (up/down)

- [ ] Set up alerts:
  - [ ] Error rate > 1%
  - [ ] p99 latency > 1s
  - [ ] Cache hit < 70%
  - [ ] Database connections > 80% pool
  - [ ] Service down

### Backup & Recovery

- [ ] PostgreSQL automated backups (daily)
- [ ] Redis persistence (AOF)
- [ ] Disaster recovery test (quarterly)

### Documentation

- [ ] Update DEPLOYMENT.md with new architecture
- [ ] Document service API endpoints
- [ ] Create runbooks for common issues
- [ ] Document database migration procedures

### Team Training

- [ ] Train team on new architecture
- [ ] Document code patterns (caching, async, service calls)
- [ ] Create troubleshooting guide
- [ ] Set up on-call rotation

---

## Success Criteria by Phase

### Phase 1 (Complete by Mar 15)
- [ ] Load test: 1,000 → 10,000 concurrent users
- [ ] p99 latency: <500ms
- [ ] Cache hit ratio: >50%
- [ ] Zero regression in existing tests
- [ ] Documentation complete
- [ ] Team trained

### Phase 2 (Complete by May 1)
- [ ] Load test: 10,000 → 50,000 concurrent users
- [ ] p99 latency: <200ms
- [ ] Cache hit ratio: >80%
- [ ] Async job success rate: 99.9%
- [ ] Database replication lag: <1 sec
- [ ] Documentation complete

### Phase 3 (Complete by Aug 15)
- [ ] Load test: 50,000 → 100,000+ concurrent users
- [ ] p99 latency: <100ms
- [ ] Individual service scaling: independent
- [ ] Service-to-service latency: <50ms
- [ ] Deployment time: <5 min per service
- [ ] Documentation complete

---

## Resources Required

| Phase | AWS Cost | Dev Time | Engineers |
|-------|----------|----------|-----------|
| 1 | $200/mo | 80 hours | 2 |
| 2 | $500/mo | 160 hours | 3 |
| 3 | $1,500/mo | 320 hours | 4 |
| **Total** | **$1,500/mo** | **560 hours** | **3-4 avg** |

---

**Next Review:** 2026-03-15 (Phase 1 completion)
**Last Updated:** 2026-02-25