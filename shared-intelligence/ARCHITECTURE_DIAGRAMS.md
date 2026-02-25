# Architecture Optimization Diagrams
> Visual representations of current and target architectures for SoftFactory platform
> **Generated:** 2026-02-25

---

## Diagram 1: Current Architecture (Single Monolith)

```
┌────────────────────────────────────────────────────────────────────────┐
│                           CURRENT STATE                                │
│                     Single Instance Deployment                          │
│                        Capacity: ~1,000 users                           │
└────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Web App    │  │  Mobile App  │  │  API Client  │  │  Telegram    │  │
│  │  (75 HTML)  │  │  (iOS/Web)   │  │  (3rd party) │  │  Bot (M-005) │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼──────────────────┼──────────────────┼────────┘
          │                 │                  │                  │
          └─────────────────┴──────────────────┴──────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
   ┌────┴────────────────────────────────────┐ │
   │     MONOLITHIC FLASK APPLICATION         │ │ HTTP/WebSocket
   │          Port 8000                       │ │
   │  ┌────────────────────────────────────┐ │ │
   │  │    AUTHENTICATION LAYER (JWT)      │ │ │
   │  │  - User login/signup               │ │ │
   │  │  - Demo mode token support         │ │ │
   │  │  - Password hashing (Werkzeug)     │ │ │
   │  └────────────────────────────────────┘ │ │
   │  ┌────────────────────────────────────┐ │ │
   │  │    6 SERVICE BLUEPRINTS             │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 1. CooCook (Chef Bookings)   │  │ │ │
   │  │  │    - Chef listings           │  │ │ │
   │  │  │    - Booking management      │  │ │ │
   │  │  │    - Review system           │  │ │ │
   │  │  │    Routes: 20 endpoints      │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 2. SNS Auto (Social Posting) │  │ │ │
   │  │  │    - SNS account management  │  │ │ │
   │  │  │    - Post scheduling         │  │ │ │
   │  │  │    - Platform integration    │  │ │ │
   │  │  │    Routes: 12 endpoints      │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 3. Review Campaigns          │  │ │ │
   │  │  │    - Campaign creation       │  │ │ │
   │  │  │    - Influencer matching     │  │ │ │
   │  │  │    - Reward management       │  │ │ │
   │  │  │    Routes: 8 endpoints       │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 4. AI Automation             │  │ │ │
   │  │  │    - Scenario templates      │  │ │ │
   │  │  │    - AI employee management  │  │ │ │
   │  │  │    - Usage tracking          │  │ │ │
   │  │  │    Routes: 10 endpoints      │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 5. WebApp Builder            │  │ │ │
   │  │  │    - Bootcamp enrollment     │  │ │ │
   │  │  │    - Progress tracking       │  │ │ │
   │  │  │    - Project deployment      │  │ │ │
   │  │  │    Routes: 8 endpoints       │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  ┌──────────────────────────────┐  │ │ │
   │  │  │ 6. Experience (Crawler)      │  │ │ │
   │  │  │    - Listings aggregation    │  │ │ │
   │  │  │    - Platform crawling       │  │ │ │
   │  │  │    - Scheduled scraping      │  │ │ │
   │  │  │    Routes: 6 endpoints       │  │ │ │
   │  │  └──────────────────────────────┘  │ │ │
   │  │  Plus: Payment processing, Platform mgmt │ │
   │  │        Health checks, Static file serving │ │
   │  └────────────────────────────────────┘ │ │
   │                                        │ │
   │  Gunicorn Workers: 4 (sync)            │ │
   │  Request timeout: 30s                  │ │
   │  Memory per worker: ~150MB             │ │
   │  Max concurrent: ~100                  │ │
   └────────────────────────────────────────┘ │
                    │                         │
   ┌────────────────┴─────────────────────────┤
   │                                          │
   │  SINGLE SHARED DATABASE (PostgreSQL)    │
   │  ┌────────────────────────────────────┐ │
   │  │  12 SQLAlchemy Models              │ │
   │  │  - Users (email, password_hash)    │ │
   │  │  - Chefs, Bookings, Reviews        │ │
   │  │  - SNS Accounts, Posts             │ │
   │  │  - Campaigns, Applications         │ │
   │  │  - AI Employees, Scenarios        │ │
   │  │  - Bootcamps, WebApps             │ │
   │  │  - Listings, CrawlerLogs          │ │
   │  │                                    │ │
   │  │  Connections: 20 max               │ │
   │  │  Size (current): 92KB (dev)       │ │
   │  │  Size (projected): 50GB (at scale) │ │
   │  └────────────────────────────────────┘ │
   │                                          │
   │  PostgreSQL 15-alpine (Single Instance)  │
   │  - No replicas                          │
   │  - No read scaling                      │
   │  - Single point of failure              │
   └──────────────────────────────────────────┘


BOTTLENECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Worker Pool:      4 workers × 25 req/worker = 100 concurrent users max
2. DB Connection:    20 connections exhausted at ~200 concurrent users
3. No Caching:       100% of reads hit database
4. No Async:         Synchronous blocking (SNS posts block user requests)
5. Single Instance:  No redundancy, downtime = platform down
6. Static Serving:   Flask wastes CPU on HTML/CSS/JS serving
```

---

## Diagram 2: Phase 1 Architecture (Database Optimization + Caching)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1 STATE                                   │
│              Database Optimization + Redis Caching                      │
│                   Capacity: ~10,000 users                              │
│                   Duration: 2 weeks                                    │
└────────────────────────────────────────────────────────────────────────┘


                             CLIENTS
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
   ┌────┴──────────────────────────────────────────┐ │
   │     MONOLITHIC FLASK APPLICATION               │ │
   │          Port 8000                             │ │
   │                                                │ │
   │  ┌──────────────────────────────────────────┐ │ │
   │  │    6 SERVICE BLUEPRINTS (unchanged)      │ │ │
   │  │    - Same 60+ endpoints                  │ │ │
   │  │    - Same business logic                 │ │ │
   │  └──────────────────────────────────────────┘ │ │
   │                                                │ │
   │  Gunicorn Workers: 9 (sync)  ← INCREASED     │ │
   │  Worker timeout: 30s                          │ │
   │  Memory per worker: ~150MB                    │ │
   │  Connection pool: 30 (base) + 10 (overflow)  │ │
   │  Max concurrent: ~500                        │ │
   │                                                │ │
   └────────────────────────┬──────────────────────┘ │
        ┌────────────┬──────────────┬────────────┘ │
        │            │              │              │ Cache Calls
        │            │              │    (50-70%)   │ (5ms response)
        │            │              │    ┌─────────┴─────────┐
        │            │              │    │                   │
   ┌────┴────────────┴──────────────┴────┴──────────────────┐
   │  ┌──────────────────────────────────────────────────┐  │
   │  │         REDIS CACHE LAYER (NEW)                  │  │
   │  │  - In-memory data store                          │  │
   │  │  - Distributed across all workers               │  │
   │  │  - TTL-based expiration                         │  │
   │  │                                                  │  │
   │  │  CACHE STRATEGY:                                │  │
   │  │  ┌────────────────────────────────────────────┐ │  │
   │  │  │ Chef listings (TTL: 300s)  → 60% hit rate │ │  │
   │  │  │ Active campaigns (TTL: 600s) → 50% hit     │ │  │
   │  │  │ User profiles (TTL: 3600s) → 70% hit       │ │  │
   │  │  │ SNS post queue (TTL: 60s) → 40% hit        │ │  │
   │  │  │ API responses (TTL: 300s) → 80% hit        │ │  │
   │  │  │ Overall cache hit rate: >50%               │ │  │
   │  │  └────────────────────────────────────────────┘ │  │
   │  │                                                  │  │
   │  │  Memory: 512MB - 2GB                           │  │
   │  │  Persistence: AOF enabled                      │  │
   │  │  Replication: Single node (Phase 2: cluster)   │  │
   │  └──────────────────────────────────────────────────┘  │
   │             │                                          │
   └─────────────┼──────────────────────────────────────────┘
        ┌────────┴─────────────────────┐
        │ Query Cache                  │ (30% of queries)
        │ (50-70% of queries hit Redis)│
        │
   ┌────┴──────────────────────────────────────────────────┐
   │  OPTIMIZED POSTGRESQL DATABASE                         │
   │  ┌──────────────────────────────────────────────────┐ │
   │  │  NEW INDEXES ADDED (20-30% faster queries)      │ │
   │  │  - idx_chef_active_cuisine                      │ │
   │  │  - idx_booking_user_date                        │ │
   │  │  - idx_campaign_status                          │ │
   │  │  - idx_sns_post_status                          │ │
   │  │  - idx_campaign_app_status                      │ │
   │  │  ... and 8 more compound indexes                │ │
   │  │                                                  │ │
   │  │  Connection Pool:                                │ │
   │  │  - pool_size: 20 (per worker)                   │ │
   │  │  - max_overflow: 10                             │ │
   │  │  - pool_recycle: 3600s                          │ │
   │  │  - pool_pre_ping: enabled                       │ │
   │  │  - Total: 20 * 9 workers = 180 connections     │ │
   │  │                                                  │ │
   │  │  Performance:                                   │ │
   │  │  - Query time (p99): 50ms ← down from 100ms    │ │
   │  │  - Connection latency: <1ms (pooled)           │ │
   │  │  - Throughput: 50-100 RPS                      │ │
   │  └──────────────────────────────────────────────────┘ │
   │                                                        │
   │  PostgreSQL 15-alpine (Single Instance)               │
   │  - db.t3.medium (AWS)                                │
   │  - Still single node (replicas in Phase 2)           │
   │  - 50GB storage capacity                             │
   └────────────────────────────────────────────────────────┘


IMPROVEMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Concurrent users:  100 → 500 (5x increase)
✓ Cache hit ratio:   0% → 50-70%
✓ Query latency:     100ms → 50ms (p99)
✓ Database QPS:      50 → 150 (3x with cache)
✓ Worker pool:       4 → 9 workers
✓ Connection pool:   20 → 180 connections

NEW BOTTLENECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Single DB instance still a bottleneck at 5,000+ users
⚠ Synchronous requests still block during slow operations
⚠ No read replicas for load distribution
⚠ Static file serving still wastes Flask CPU
⚠ No message queue for async jobs
```

---

## Diagram 3: Phase 2 Architecture (Replication + Async)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2 STATE                                   │
│          Database Replication + Async Processing + Read Scaling        │
│                   Capacity: ~50,000 users                              │
│                   Duration: 4 weeks                                    │
└────────────────────────────────────────────────────────────────────────┘


                             CLIENTS
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
   ┌────┴──────────────────────────────────────────┐ │
   │     MONOLITHIC FLASK APPLICATION               │ │
   │          Port 8000                             │ │
   │                                                │ │
   │  ┌──────────────────────────────────────────┐ │ │
   │  │    6 SERVICE BLUEPRINTS                  │ │ │
   │  │    - Async job decorators added         │ │ │
   │  │    - Service-to-service calls supported │ │ │
   │  │    - Same endpoints                     │ │ │
   │  └──────────────────────────────────────────┘ │ │
   │                                                │ │
   │  Gunicorn Workers: 9 (sync → gevent)          │ │
   │  Max concurrent: ~2,000                       │ │
   │                                                │ │
   │  NEW: Async Job Support                       │ │
   │  ┌──────────────────────────────────────────┐ │ │
   │  │ CELERY INTEGRATION (NEW)                 │ │ │
   │  │ - post_to_sns.delay()  (SNS posting)    │ │ │
   │  │ - send_email.delay()   (Email)          │ │ │
   │  │ - process_review.delay() (Campaign)     │ │ │
   │  │ - crawl_experience.delay() (Listings)   │ │ │
   │  │                                         │ │ │
   │  │ Returns 202 Accepted (non-blocking)     │ │ │
   │  └──────────────────────────────────────────┘ │ │
   │                                                │ │
   └────────────────────────┬──────────────────────┘ │
        ┌────────────┬──────────────┬────────────┘ │
        │            │              │              │
        │            │              │    Async jobs (202 responses)
        │            │              │              │
        │            │    ┌─────────┴──────────────┴────────────┐
        │            │    │                                     │
        │ ┌──────────┴────┴────────────┐                       │
        │ │                            │                       │
   ┌────┴─┴────────────────────────────┴────────────────────┐
   │  ┌──────────────────────────────────────────────────┐  │
   │  │         REDIS CACHE LAYER (expanded)              │  │
   │  │ - Cache: 1GB (same as Phase 1)                    │  │
   │  │ - Sessions: 512MB                                 │  │
   │  │ - Queue: 2GB (Celery job queue)                   │  │
   │  │ - Pub/sub: Real-time updates                      │  │
   │  │ - Cache hit rate: 80% (up from 50%)               │  │
   │  │                                                   │  │
   │  │ Redis Configuration:                              │  │
   │  │ - Master: primary instance (write)                │  │
   │  │ - Replica: for queue distribution                 │  │
   │  │ - Persistence: RDB + AOF                          │  │
   │  │ - Memory policy: allkeys-lru                      │  │
   │  └──────────────────────────────────────────────────┘  │
   │                                                         │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │    CELERY TASK QUEUE (NEW)                       │  │
   │  │    - Message Broker: Redis                       │  │
   │  │    - Workers: 4 dedicated Celery workers         │  │
   │  │    - Tasks: SNS posts, emails, crawling          │  │
   │  │    - Concurrency: 16 jobs per worker             │  │
   │  │    - Max parallel jobs: 64                        │  │
   │  │    - Job timeout: 5 minutes                       │  │
   │  │    - Retry policy: exponential backoff            │  │
   │  │                                                   │  │
   │  │    TASK TYPES:                                   │  │
   │  │    ┌────────────────────────────────────────┐    │  │
   │  │    │ 1. SNS Posts (async)                   │    │  │
   │  │    │    - Instagram post scheduling         │    │  │
   │  │    │    - TikTok upload                     │    │  │
   │  │    │    - Blog publishing                   │    │  │
   │  │    └────────────────────────────────────────┘    │  │
   │  │    ┌────────────────────────────────────────┐    │  │
   │  │    │ 2. Email Notifications                 │    │  │
   │  │    │    - Welcome emails                    │    │  │
   │  │    │    - Booking confirmations             │    │  │
   │  │    │    - Campaign notifications            │    │  │
   │  │    └────────────────────────────────────────┘    │  │
   │  │    ┌────────────────────────────────────────┐    │  │
   │  │    │ 3. Background Processing                │    │  │
   │  │    │    - Campaign aggregation               │    │  │
   │  │    │    - Review ranking                     │    │  │
   │  │    │    - Data cleanup                       │    │  │
   │  │    └────────────────────────────────────────┘    │  │
   │  │    ┌────────────────────────────────────────┐    │  │
   │  │    │ 4. Web Crawling (Experience)            │    │  │
   │  │    │    - Platform scraping                 │    │  │
   │  │    │    - Listing aggregation               │    │  │
   │  │    │    - Rate limiting respected           │    │  │
   │  │    └────────────────────────────────────────┘    │  │
   │  │                                                   │  │
   │  └──────────────────────────────────────────────────┘  │
   │                                  │                     │
   └──────────────────────────────────┼─────────────────────┘
                  ┌────────┬──────────┴──────────┬─────────┐
                  │        │                     │         │
                  │        │                     │         │
        ┌─────────┴──┐ ┌───┴──────────────┐ ┌───┴─────┐   │
        │            │ │                  │ │         │   │
   ┌────┴────────────┴─┴──────────────────┴─┴─────────┘
   │
   │  DATABASE LAYER (Read Replicas Added)
   │  ┌─────────────────────────────────────────────────┐
   │  │  MASTER (Write)                                 │
   │  │  - Accepts all INSERT/UPDATE/DELETE            │
   │  │  - db.t3.large (AWS)                           │
   │  │  - Synchronous replication to replicas         │
   │  │  - Automated backup: daily                      │
   │  │                                                 │
   │  │  Performance:                                   │
   │  │  - Write latency: <10ms                         │
   │  │  - Write throughput: 1,000 QPS                  │
   │  └─────────────────────────────────────────────────┘
   │                    │ (replication)
   │        ┌───────────┴───────────┐
   │        │                       │
   │  ┌─────┴──────────┐     ┌──────┴─────────┐
   │  │ REPLICA 1      │     │ REPLICA 2      │
   │  │ (Read-only)    │     │ (Read-only)    │
   │  │ db.t3.large    │     │ db.t3.large    │
   │  │                │     │                │
   │  │ Read latency:  │     │ Read latency:  │
   │  │ <5ms           │     │ <5ms           │
   │  │                │     │                │
   │  │ Lag: <1 sec    │     │ Lag: <1 sec    │
   │  └────────────────┘     └────────────────┘
   │
   │  Read/Write Routing:
   │  - Writes → Master (serialized)
   │  - Reads → Master (current data) or Replica (eventual consistency)
   │  - Chef listings → Replica (eventually consistent OK)
   │  - User bookings → Master (strong consistency required)
   │  - Campaigns → Replica (read-heavy)
   │
   └────────────────────────────────────────────────┘


IMPROVEMENTS vs Phase 1:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Concurrent users:     500 → 2,000 (4x increase)
✓ Request latency:      <500ms → <200ms (p99)
✓ Async tasks:          60% of requests (non-blocking)
✓ Cache hit rate:       50% → 80%
✓ Database read load:   3x distribution (3 instances)
✓ Write throughput:     unchanged (1 master bottleneck)
✓ Session persistence:  Redis (survives restarts)
✓ Job processing:       64 parallel tasks

REMAINING BOTTLENECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Single write master: 1,000 QPS limit
⚠ Monolithic app structure: services compete for resources
⚠ All services share same database: schema changes risky
⚠ Static file serving: still in Flask
⚠ Single API endpoint: no service isolation
```

---

## Diagram 4: Phase 3 Architecture (Microservices)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHASE 3 STATE                                   │
│                    Microservices Architecture                          │
│                  Capacity: 100,000+ concurrent users                   │
│                     Duration: 8 weeks                                  │
└────────────────────────────────────────────────────────────────────────┘


                              CLIENTS
                                │
        ┌───────────────────────┴────────────────────┐
        │                                            │
        ├─── Web Browser          Mobile App        API Client
        │      (React)              (iOS)          (3rd party)
        │
   ┌────┴─────────────────────────────────────────────┐
   │          API GATEWAY (Kong)                       │
   │  ┌────────────────────────────────────────────┐  │
   │  │ Authentication Layer                        │  │
   │  │ - JWT verification                         │  │
   │  │ - Rate limiting (per user)                 │  │
   │  │ - Request routing                          │  │
   │  │ - Response compression                     │  │
   │  │ - CORS handling                            │  │
   │  └────────────────────────────────────────────┘  │
   │                                                  │
   │  Routes:                                        │
   │  /api/coocook/*        → CooCook Service        │
   │  /api/sns-auto/*       → SNS Auto Service       │
   │  /api/review/*         → Review Service         │
   │  /api/auth/*           → Auth Service (Platform)│
   │  /api/payment/*        → Payment Service        │
   │  /api/experience/*     → Experience Service     │
   │                                                  │
   │  Features:                                      │
   │  - Automatic load balancing                    │
   │  - Circuit breaker on downstream services      │
   │  - Request logging + tracing                   │
   │  - Service mesh integration (optional)         │
   │                                                  │
   └────────────────────────────────────────────────┘
                  │        │        │        │
        ┌─────────┴────────┼────────┼────────┘
        │                  │        │
        │ ┌────────────────┘        │
        │ │                         │
   ┌────┴─┴──────────┐    ┌────────┴───────────┐
   │                 │    │                    │
   │  SERVICE 1      │    │   SERVICE 2        │
   │  Platform &     │    │   CooCook          │
   │  Payment        │    │   (Chef Bookings)  │
   │  ┌────────────┐ │    │ ┌────────────────┐ │
   │  │ Auth       │ │    │ │ Routes:        │ │
   │  │ Payment    │ │    │ │ - List chefs   │ │
   │  │ User mgmt  │ │    │ │ - Book chef    │ │
   │  │ Products   │ │    │ │ - Review       │ │
   │  └─────┬──────┘ │    │ └────────┬───────┘ │
   │        │        │    │          │         │
   │ ┌──────┴────────┘    │ FastAPI  │         │
   │ │                    │ Uvicorn  │         │
   │ │ Flask + Gunicorn   │ Workers: 4│        │
   │ │ Workers: 4         │          │         │
   │ │                    │ Max concurrent:    │
   │ │                    │ 10,000 (per        │
   │ │                    │ service)           │
   │ │                    │          │         │
   │ └──────┬─────────────┤ ┌────────┴───────┐ │
   │        │             └─┤ Database       │ │
   │        │               │ (Dedicated)    │ │
   │        │               └────────────────┘ │
   │        │                                  │
   │    PostgreSQL         PostgreSQL          │
   │    (Master + 2 read   (Master + 2 read    │
   │     replicas)         replicas)           │
   │                                           │
   │ Data: Users,          Data: Chefs,        │
   │ Products,             Bookings,           │
   │ Subscriptions,        Reviews,            │
   │ Payments              Ratings             │
   │                                           │
   └───────┬──────────────────────────────────┘
           │
           ├──────────────────────────┬──────────────────────┐
           │                          │                      │
   ┌───────┴──────────┐    ┌──────────┴──────────┐  ┌────────┴─────────┐
   │                  │    │                     │  │                  │
   │   SERVICE 3      │    │    SERVICE 4        │  │   SERVICE 5      │
   │   SNS Auto       │    │    Review Campaigns │  │   AI Automation  │
   │   (Social Posts) │    │    (Influencer Mgmt)│  │   (Agents)       │
   │                  │    │                     │  │                  │
   │ ┌──────────────┐ │    │ ┌──────────────────┐  │ ┌────────────────┐│
   │ │ SNS posting  │ │    │ │ Campaign mgmt    │  │ │ Scenario mgmt  ││
   │ │ Account mgmt │ │    │ │ Influencer match │  │ │ AI employee    ││
   │ │ Scheduling   │ │    │ │ Review tracking  │  │ │ Usage tracking ││
   │ └──────┬───────┘ │    │ └────────┬────────┐  │ └────────┬───────┘│
   │        │         │    │          │        │  │          │       │
   │ FastAPI│         │    │ FastAPI  │        │  │ FastAPI  │       │
   │ + Celery          │    │ + Elasticsearch   │  │ + Redis  │       │
   │        │         │    │          │        │  │          │       │
   │ Async  │         │    │ Full-text│        │  │ Job queue        │
   │ jobs   │         │    │ search   │        │  │          │       │
   │        │         │    │          │        │  │          │       │
   │ ┌──────┴────────┐│    │ ┌────────┴───────┐  │ ┌────────┴───────┐│
   │ │ PostgreSQL    ││    │ │ PostgreSQL     │  │ │ PostgreSQL     ││
   │ │ Master + 1    ││    │ │ Master + 1     │  │ │ Master + 1     ││
   │ │ replica       ││    │ │ replica        │  │ │ replica        ││
   │ └───────────────┘│    │ └────────────────┐  │ └────────────────┘│
   │                  │    │ + Elasticsearch ├──┤                    │
   │ Data:            │    │ (search index)  │  │ Data:              │
   │ - SNS Accounts   │    │                 │  │ - AI Employees     │
   │ - Posts          │    │ Data:           │  │ - Scenarios        │
   │ - Scheduling     │    │ - Campaigns     │  │ - Usage stats      │
   │                  │    │ - Applications  │  │                    │
   │                  │    │ - Reviews       │  │                    │
   │                  │    │ - Influencers   │  │                    │
   │                  │    │                 │  │                    │
   └──────────────────┘    └─────────────────┘  └────────────────────┘


SHARED INFRASTRUCTURE LAYER:
┌───────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │              REDIS CLUSTER (Shared)                              │ │
│  │  - Cache: 4GB (distributed)                                     │ │
│  │  - Sessions: 2GB (all services)                                 │ │
│  │  - Pub/sub: Real-time events                                   │ │
│  │  - Cluster nodes: 6 (3 master + 3 slave)                       │ │
│  │  - Memory: 6GB total                                            │ │
│  │  - Cache hit rate: 85%                                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │              MESSAGE QUEUE (Celery + RabbitMQ)                   │ │
│  │  - Broker: RabbitMQ (reliability)                                │ │
│  │  - Result backend: Redis                                         │ │
│  │  - Queue throughput: 10,000 jobs/sec                            │ │
│  │  - Distributed workers across all services                      │ │
│  │  - Retry policy: exponential backoff                            │ │
│  │  - Dead letter queue for failed jobs                            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │               CDN (CloudFront / Cloudflare)                      │ │
│  │  - Static assets: HTML, CSS, JS, images                         │ │
│  │  - Cache TTL: 1 hour to 1 day                                   │ │
│  │  - Edge locations: 200+ worldwide                               │ │
│  │  - DDoS protection: Built-in                                    │ │
│  │  - Compression: gzip, brotli                                    │ │
│  │  - Cache hit ratio: 95%+                                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │         MONITORING & OBSERVABILITY (Prometheus + Grafana)        │ │
│  │  - Metrics collection: Prometheus                               │ │
│  │  - Visualization: Grafana dashboards                            │ │
│  │  - Alerting: PagerDuty integration                              │ │
│  │  - Distributed tracing: Jaeger                                  │ │
│  │  - Log aggregation: ELK stack (optional)                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────────────────────────────────────────────┘


IMPROVEMENTS vs Phase 2:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Concurrent users:           2,000 → 10,000+ per service
✓ Total capacity:             50,000 → 100,000+
✓ Service independence:       Each scales separately
✓ Database scaling:           5 independent databases
✓ Write throughput:           1K QPS (single master) → 5K QPS (multi-master)
✓ Deployment time:            Global → 5 min per service
✓ Service update:             No downtime per service
✓ Resource utilization:       80% → 95% (better scaling)
✓ Service-to-service latency: <50ms (API Gateway)

ARCHITECTURE BENEFITS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Independent scaling: High-traffic service (CooCook) scales without others
✓ Tech stack flexibility: Each service can use best tech for its domain
✓ Faster iteration: Services deploy independently
✓ Clear ownership: Each team owns specific services
✓ Failure isolation: CooCook outage doesn't affect SNS Auto
✓ Reusability: Services can be consumed by other products
✓ Future-proof: Can add new services without touching existing ones
```

---

## Diagram 5: Capacity Planning Timeline

```
                    CONCURRENT USERS OVER TIME
                         (Quarterly Growth)

                   PHASE 3 COMPLETE
                  100,000+ users achieved
                          │
                          │
                          ▲
                          │ ┌─────────────────────────────
                          │ │  Microservices
                          │ │  (5 independent services)
                      50K │ │  • CooCook (20K concurrent)
                          │ │  • SNS Auto (15K concurrent)
                          │ │  • Review (12K concurrent)
                          │ │  • Platform (30K)
                          │ │  • Others (10K)
                          │ │
                          │ ├─────────────────────────────
                          │ │  PHASE 2 COMPLETE
                          │ │  Database Replication + Async
                      10K │ │
                          │ │  ┌──────────────────────────
                          │ │  │  PHASE 1 COMPLETE
                          │ │  │  Caching + Pooling
                       1K │ │  │
                          │ │  │  ┌────────────────────
                          │ │  │  │  CURRENT STATE
                        100 │  │  │  │  Single monolith
                          │  │  │  │
                          └─▼──▼──▼─▼────────────────────► TIME
                       Feb25  Mar15 May1 Aug15 Sep1
                       (NOW)  (P1) (P2) (P3) (GOAL)
                              |    |    |
                              2    4    8    weeks effort


SCALING ROADMAP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Feb 25 - Mar 15 (2 weeks)
├─ Add database indexes
├─ Deploy Redis caching
├─ Increase Gunicorn workers
├─ Implement connection pooling
├─ Load test: 1K → 10K concurrent
└─ Cost: $200/month

Phase 2: Mar 15 - May 1 (6 weeks)
├─ Set up read replicas (2x)
├─ Deploy Celery async queue
├─ Migrate sessions to Redis
├─ Implement read/write routing
├─ Full-text search (optional)
├─ Load test: 10K → 50K concurrent
└─ Cost: $500/month

Phase 3: May 1 - Aug 15 (16 weeks)
├─ Design microservices architecture
├─ Extract CooCook service (FastAPI)
├─ Set up API Gateway (Kong)
├─ Implement service discovery
├─ Extract SNS Auto service
├─ Extract Review service
├─ Full E2E testing
├─ Load test: 50K → 100K+ concurrent
└─ Cost: $1,500/month
```

---

## Diagram 6: Request Flow Comparison

```
PHASE 1: SYNCHRONOUS REQUEST (with caching)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Request:
└─ GET /api/coocook/chefs?page=1
   └─ Flask receive_request
      ├─ Check Redis cache
      │  ├─ HIT (50% probability) → Return cached JSON [5ms]
      │  └─ MISS (50% probability)
      │     ├─ Query DB for chefs
      │     │  ├─ Check connection pool (instant)
      │     │  ├─ Execute SQL query [40ms]
      │     │  └─ Deserialize 20 chef objects [5ms]
      │     ├─ Cache result in Redis [2ms]
      │     └─ Return JSON [2ms]
      │        Total: ~50ms
      └─ Send HTTP response (200 OK) [1ms]

Total response time: 5-50ms
Concurrent users: ~100
Request capacity: 1000 RPS


PHASE 2: MIXED SYNC + ASYNC (with replication + queue)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Synchronous Request:
└─ GET /api/coocook/chefs
   └─ Check Redis cache (3ms)
      ├─ HIT → Return [5ms]
      └─ MISS → Query read replica [10ms]
         Total: 15-20ms response

Async Request:
└─ POST /api/sns-auto/schedule
   ├─ Validate user (JWT) [1ms]
   ├─ Create SNSPost record (master DB) [5ms]
   ├─ Queue Celery job: post_to_sns.delay() [2ms]
   ├─ Return 202 Accepted [1ms]
   │  Total user-facing latency: ~9ms ✓
   │
   └─ [Asynchronously, in background]
      ├─ Celery worker picks up task
      ├─ Authenticate with SNS API
      ├─ Post content [500ms - 2s]
      ├─ Update SNSPost status = 'published'
      └─ Send webhook notification (optional)

Total response time: 5-20ms (user sees immediately)
Background processing: 500ms - 2s (non-blocking)
Concurrent users: ~2,000
Async job throughput: 1,000 jobs/sec


PHASE 3: SERVICE ISOLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Request:
└─ GET /api/coocook/chefs
   ├─ API Gateway (Kong) [1ms]
   │  ├─ Verify JWT token
   │  ├─ Check rate limit
   │  ├─ Route to CooCook service
   │  └─ Add tracing headers
   │
   └─ CooCook Service [5-20ms]
      ├─ FastAPI receive
      ├─ Check Redis cache [2ms]
      │  ├─ HIT → Return [3ms]
      │  └─ MISS
      │     ├─ Query dedicated PostgreSQL replica [8ms]
      │     ├─ Cache result [1ms]
      │     └─ Return [1ms]
      └─ FastAPI serialize response
         └─ API Gateway return to client

Total response time: 5-30ms
Concurrent users (CooCook service alone): 10,000
Service isolation: CooCook outage doesn't affect Payment API
```

---

## Diagram 7: Database Connection Pool Growth

```
                CONNECTION POOL UTILIZATION OVER SCALING

Current (1 Gunicorn worker):
├─ Pool size: 5 connections
├─ Avg connections used: 2 (40%)
├─ Peak connections used: 4 (80%)
└─ Max concurrent requests: 5

Phase 1 (9 Gunicorn workers):
├─ Pool size: 20 per worker × 9 = 180 connections
├─ Avg connections used: 72 (40%)
├─ Peak connections used: 144 (80%)
├─ Pool overflow: +10 per worker = 90 additional
└─ Max concurrent requests: 270

Phase 2 (read replicas + async):
├─ Master pool: 20 × 9 = 180
├─ Replica pool: 10 × 9 = 90 (read-only queries)
├─ Total connections: 270
├─ Avg utilization: 108 (40%)
├─ Peak utilization: 216 (80%)
└─ Max concurrent requests: 500 (with async jobs)

Phase 3 (5 services, each with replicas):
├─ Service 1 (Platform): 180 + 90 = 270
├─ Service 2 (CooCook): 180 + 90 = 270
├─ Service 3 (SNS Auto): 180 + 90 = 270
├─ Service 4 (Review): 180 + 90 = 270
├─ Service 5 (AI Auto): 180 + 90 = 270
├─ Total across all: 1,350 connections
├─ Avg utilization: 540 (40%)
├─ Peak utilization: 1,080 (80%)
└─ Database capacity: Easily accommodates (PostgreSQL supports 300+)
```

---

End of Diagrams
