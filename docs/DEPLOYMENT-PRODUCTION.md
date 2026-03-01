# 🚢 Production Deployment Runbook — SoftFactory Platform

> **Purpose**: 1. [Pre-Deployment Checklist](#pre-deployment-checklist)
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Production Deployment Runbook — SoftFactory Platform 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Status:** PRODUCTION-READY | **Version:** 1.0 | **Updated:** 2026-02-25
> **Scope:** Complete deployment pipeline for SoftFactory Platform on production infrastructure

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Architecture Overview](#architecture-overview)
3. [Environment Setup](#environment-setup)
4. [Deployment Procedures](#deployment-procedures)
5. [Health Checks & Verification](#health-checks--verification)
6. [Scaling & Performance](#scaling--performance)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [Emergency Contacts](#emergency-contacts)

---

## Pre-Deployment Checklist

### Phase 1: Code & Infrastructure (24 hours before)

- [ ] **Code Review Complete**
  - [ ] All PRs merged and tested
  - [ ] CI/CD pipeline passing (all tests, lint, type checks)
  - [ ] Security scan clean (no vulnerabilities flagged)
  - [ ] Database migrations reviewed and tested

- [ ] **Documentation Verified**
  - [ ] API documentation up-to-date
  - [ ] Deployment runbook reviewed
  - [ ] Known issues documented
  - [ ] Rollback plan communicated to team

- [ ] **Database Ready**
  - [ ] Current production backup created (dated)
  - [ ] Migration scripts tested on staging
  - [ ] Database schema validated (all tables present)
  - [ ] Indexes verified for performance queries

- [ ] **Configuration Ready**
  - [ ] All environment variables defined in `.env-prod`
  - [ ] Database credentials set up securely
  - [ ] Redis password configured
  - [ ] SSL certificates valid (check expiration dates)

- [ ] **Infrastructure Prepared**
  - [ ] Docker daemon running and healthy
  - [ ] Disk space available: minimum 10GB
  - [ ] Network connectivity verified
  - [ ] Firewall rules configured (80, 443 open)

### Phase 2: Pre-Deployment Testing (4 hours before)

- [ ] **Docker Build & Test**
  ```bash
  docker build -f Dockerfile.prod -t softfactory:latest .
  docker run --rm softfactory:latest python -m pytest tests/ -v
  ```

- [ ] **Staging Deployment**
  - [ ] Deploy to staging environment
  - [ ] Run full API test suite
  - [ ] Manual smoke tests of critical flows
  - [ ] Performance testing (response times < 500ms)

- [ ] **Backup Verification**
  - [ ] Production database backup exists
  - [ ] Backup restoration tested (can recover data)
  - [ ] Backup location accessible
  - [ ] Backup encryption verified

- [ ] **Alert Configuration**
  - [ ] All Prometheus alerts configured
  - [ ] Slack/email notifications tested
  - [ ] Pagerduty integration (if applicable) verified
  - [ ] Runbook links in alert definitions

### Phase 3: Deployment Window (30 min before)

- [ ] **Team Coordination**
  - [ ] Team members on-call and ready
  - [ ] Communication channel open (Slack, Discord)
  - [ ] Deployment commander identified
  - [ ] Rollback authority confirmed

- [ ] **Final Sanity Checks**
  - [ ] No critical issues reported
  - [ ] All prerequisites complete
  - [ ] No competing deployments in progress
  - [ ] Production database backup successful

- [ ] **Deployment Authorization**
  - [ ] DevOps lead approval obtained
  - [ ] Product manager confirmation
  - [ ] Security team cleared (if required)

---

## Architecture Overview

### Production Stack

```
┌─────────────────────────────────────────────┐
│              Users (Internet)                │
└────────────────┬────────────────────────────┘
                 │ HTTPS (443)
                 ▼
         ┌───────────────┐
         │  nginx        │ (Reverse proxy, SSL termination)
         │  Port: 80/443 │
         └───────┬───────┘
                 │ HTTP (8000)
        ┌────────▼────────┐
        │   Flask API     │ (4 Gunicorn workers)
        │  Port: 8000     │
        │  Container:     │
        │ softfactory-api │
        └────────┬────────┘
                 │
        ┌────────┴──────┬────────┬──────────┐
        ▼               ▼        ▼          ▼
     ┌─────┐      ┌─────────┐ ┌──────┐ ┌──────────┐
     │ PG  │      │ Redis   │ │ Prom │ │ Logging  │
     │ 5432│      │ 6379    │ │ 9090 │ │          │
     └─────┘      └─────────┘ └──────┘ └──────────┘
      ●DB         ●Cache     ●Metrics  ●Logs
      ●Backup                          (ELK)
```

### Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| nginx | nginx:1.25-alpine | 80, 443 | Reverse proxy, SSL termination, rate limiting |
| web | softfactory:latest | 8000 (internal) | Flask API with Gunicorn |
| db | postgres:15-alpine | 5432 (localhost) | Primary database |
| redis | redis:7-alpine | 6379 (localhost) | Session cache, job queue |
| prometheus | prom/prometheus | 9090 (localhost) | Metrics collection |

---

## Environment Setup

### 1. Create Production Environment File

Create `.env-prod`:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_LOG_LEVEL=info
WORKERS=4

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:YOUR_SECURE_PASSWORD@db:5432/softfactory
DB_USER=postgres
DB_PASSWORD=YOUR_SECURE_PASSWORD
DB_NAME=softfactory

# Redis
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=YOUR_REDIS_PASSWORD

# Security
JWT_SECRET=your_very_long_jwt_secret_key_here_at_least_32_chars
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key

# Domain & URLs
DOMAIN=yourdomain.com
API_URL=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Email (for alerts & notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=true

# Telegram (for bot notifications)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Sentry (error tracking, optional)
SENTRY_DSN=https://your_key@sentry.io/project_id

# Feature flags
ENABLE_DEMO_MODE=false
DEBUG=false
```

### 2. Generate SSL Certificates

For self-signed (development):
```bash
mkdir -p nginx/ssl
openssl req -x509 -newkey rsa:4096 -nodes \
    -out nginx/ssl/cert.pem -keyout nginx/ssl/key.pem -days 365
```

For production, use Let's Encrypt with certbot:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
# Copy certificates to nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown $(id -u):$(id -g) nginx/ssl/*
```

### 3. Prepare Database

Create `scripts/init-db.sql`:

```sql
-- Create database user
CREATE USER IF NOT EXISTS softfactory_user WITH PASSWORD 'secure_password';

-- Create database
CREATE DATABASE softfactory OWNER softfactory_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE softfactory TO softfactory_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO softfactory_user;

-- Enable extensions
\c softfactory
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### 4. Create Systemd Service (for container management on Linux)

Create `/etc/systemd/system/softfactory.service`:

```ini
[Unit]
Description=SoftFactory Platform
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/softfactory
ExecStart=/usr/bin/docker-compose -f docker-compose-prod.yml up
ExecStop=/usr/bin/docker-compose -f docker-compose-prod.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable: `sudo systemctl enable softfactory && sudo systemctl start softfactory`

---

## Deployment Procedures

### Step 1: Pre-Deployment Backup

```bash
# Backup current database
docker exec softfactory-db pg_dump -U postgres softfactory > \
    backups/softfactory_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
tar -czf backups/softfactory_code_$(date +%Y%m%d_%H%M%S).tar.gz \
    backend/ web/ requirements.txt

# Verify backups
ls -lh backups/
```

### Step 2: Pull Latest Code

```bash
cd /path/to/softfactory
git fetch origin main
git checkout origin/main
git log -1 --oneline  # Verify latest commit
```

### Step 3: Build Docker Image

```bash
# Build production image
docker build -f Dockerfile.prod -t softfactory:latest \
    -t softfactory:$(git rev-parse --short HEAD) .

# Verify image
docker run --rm softfactory:latest python --version
```

### Step 4: Pre-deployment Database Migration

```bash
# Start database only
docker-compose -f docker-compose-prod.yml up -d db redis

# Wait for database to be ready
sleep 15

# Run migrations
docker run --rm \
    --network softfactory_softfactory \
    -e DATABASE_URL="postgresql://postgres:password@db:5432/softfactory" \
    softfactory:latest \
    flask db upgrade

# Verify schema
docker exec softfactory-db psql -U postgres -d softfactory -c "\dt"
```

### Step 5: Blue-Green Deployment

```bash
# Stop current deployment (blue)
docker-compose -f docker-compose-prod.yml stop web

# Start new deployment (green)
docker-compose -f docker-compose-prod.yml up -d web

# Monitor logs
docker-compose -f docker-compose-prod.yml logs -f web
```

### Step 6: Health Check & Verification

```bash
# Wait for service to be ready
sleep 10

# Check health endpoint
curl -s http://localhost:8000/health | jq .

# Check API endpoints
curl -s https://localhost/api/platform/status | jq .

# Monitor resource usage
docker stats softfactory-api
```

### Step 7: Post-Deployment Tasks

```bash
# Verify all containers running
docker ps | grep softfactory

# Check logs for errors
docker-compose -f docker-compose-prod.yml logs --tail=100 web

# Update DNS (if domain changed)
# Update load balancer (if applicable)

# Notify stakeholders
# Email notification to team@company.com
```

---

## Health Checks & Verification

### Manual Health Checks

```bash
# 1. Flask API Health
curl -s http://localhost:8000/health | jq .

# 2. Database Connectivity
docker exec softfactory-db psql -U postgres -d softfactory -c "SELECT version();"

# 3. Redis Connectivity
docker exec softfactory-redis redis-cli ping

# 4. Nginx Status
curl -s http://localhost/health

# 5. Full Infrastructure Health
curl -s https://localhost/api/infrastructure/health | jq .
```

### Automated Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

echo "=== SoftFactory Health Check ==="
echo ""

# Check services running
echo "1. Checking container status..."
docker ps | grep -q softfactory-api && echo "✓ API running" || echo "✗ API down"
docker ps | grep -q softfactory-db && echo "✓ Database running" || echo "✗ Database down"
docker ps | grep -q softfactory-redis && echo "✓ Redis running" || echo "✗ Redis down"
docker ps | grep -q softfactory-nginx && echo "✓ Nginx running" || echo "✗ Nginx down"

echo ""
echo "2. Checking HTTP endpoints..."
curl -sf http://localhost:8000/health > /dev/null && echo "✓ API healthy" || echo "✗ API unhealthy"
curl -sf http://localhost/health > /dev/null && echo "✓ Nginx healthy" || echo "✗ Nginx unhealthy"

echo ""
echo "3. Checking database..."
docker exec softfactory-db psql -U postgres -d softfactory -c "SELECT 1;" > /dev/null 2>&1
[ $? -eq 0 ] && echo "✓ Database accessible" || echo "✗ Database inaccessible"

echo ""
echo "4. Checking resource usage..."
docker stats --no-stream softfactory-api softfactory-db
```

---

## Scaling & Performance

### Horizontal Scaling (Multiple API Servers)

For multiple API instances behind load balancer:

```yaml
# docker-compose-prod.yml (modified)
services:
  web1:
    <<: *web_service
    container_name: softfactory-api-1

  web2:
    <<: *web_service
    container_name: softfactory-api-2

  web3:
    <<: *web_service
    container_name: softfactory-api-3
```

Update nginx upstream:
```nginx
upstream flask_backend {
    least_conn;
    server web1:8000 max_fails=3 fail_timeout=30s;
    server web2:8000 max_fails=3 fail_timeout=30s;
    server web3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### Vertical Scaling (Increase Resources)

```yaml
# docker-compose-prod.yml
services:
  web:
    cpu_shares: 2048      # Increase from 1024
    mem_limit: 1g         # Increase from 512m
    memswap_limit: 1.5g   # Increase from 768m
```

Update Gunicorn workers:
```bash
# .env-prod
WORKERS=8  # Increase from 4
```

### Database Performance Tuning

```sql
-- Check slow queries
SELECT query, calls, total_time FROM pg_stat_statements
WHERE mean_time > 100 ORDER BY mean_time DESC;

-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_bookings_user_id ON bookings(user_id);
CREATE INDEX CONCURRENTLY idx_bookings_created_at ON bookings(created_at DESC);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM bookings WHERE user_id = 123;
```

---

## Rollback Procedures

### Scenario 1: Application Code Issues (5-10 min recovery)

If API is throwing 500 errors:

```bash
# 1. Identify last stable version
git log --oneline | head -10

# 2. Checkout previous commit
git checkout abc1234def

# 3. Rebuild image
docker build -f Dockerfile.prod -t softfactory:stable .

# 4. Update docker-compose to use :stable tag
sed -i 's/softfactory:latest/softfactory:stable/' docker-compose-prod.yml

# 5. Restart services
docker-compose -f docker-compose-prod.yml up -d web

# 6. Verify
curl -s http://localhost:8000/health | jq .
```

### Scenario 2: Database Migration Failure (10-15 min recovery)

If database schema is corrupted:

```bash
# 1. Restore from backup
docker exec softfactory-db psql -U postgres -d softfactory < \
    backups/softfactory_YYYYMMDD_HHMMSS.sql

# 2. Verify restoration
docker exec softfactory-db psql -U postgres -d softfactory -c "SELECT COUNT(*) FROM users;"

# 3. Restart API
docker-compose -f docker-compose-prod.yml restart web

# 4. Test endpoints
curl -s http://localhost:8000/api/auth/status
```

### Scenario 3: Configuration/Environment Issues (3-5 min recovery)

If wrong environment variables set:

```bash
# 1. Restore .env-prod from backup
git checkout HEAD~1 -- .env-prod

# 2. Verify new values
cat .env-prod | grep DATABASE_URL

# 3. Restart containers to pick up new variables
docker-compose -f docker-compose-prod.yml down
docker-compose -f docker-compose-prod.yml up -d

# 4. Verify
docker-compose -f docker-compose-prod.yml logs web | tail -20
```

### Scenario 4: Full Rollback (15-30 min recovery)

If multiple issues require complete version revert:

```bash
# 1. Restore database
docker exec softfactory-db psql -U postgres -d softfactory < \
    backups/softfactory_last_known_good.sql

# 2. Restore code
cd /path/to/softfactory
git checkout v1.0.0  # Last known good tag

# 3. Restore .env
cp backups/.env-prod.backup .env-prod

# 4. Rebuild and deploy
docker build -f Dockerfile.prod -t softfactory:v1.0.0 .
docker-compose -f docker-compose-prod.yml down
docker-compose -f docker-compose-prod.yml up -d

# 5. Verify all services
./scripts/health-check.sh
```

---

## Monitoring & Alerts

### Prometheus Queries (Grafana Dashboards)

```promql
# CPU Usage
rate(container_cpu_usage_seconds_total{name="softfactory-api"}[5m]) * 100

# Memory Usage
container_memory_usage_bytes{name="softfactory-api"} / 1024 / 1024

# API Request Rate
rate(http_requests_total[5m])

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response Time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database Connection Count
pg_stat_activity_count{}

# Database Query Duration
rate(pg_slow_queries_total[5m])
```

### Alert Rules

Create `orchestrator/alert-rules.yml`:

```yaml
groups:
- name: softfactory
  interval: 30s
  rules:

  - alert: APIDown
    expr: up{job="softfactory-api"} == 0
    for: 2m
    annotations:
      summary: "API Server Down"
      description: "softfactory-api container is not responding for 2+ minutes"

  - alert: HighErrorRate
    expr: (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) > 0.05
    for: 5m
    annotations:
      summary: "High Error Rate (5%+)"
      description: "API error rate exceeded 5% threshold"

  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes{name="softfactory-api"} / 536870912) > 0.9
    for: 5m
    annotations:
      summary: "High Memory Usage (90%+)"
      description: "API container memory usage over 90%"

  - alert: DatabaseDown
    expr: up{job="softfactory-db"} == 0
    for: 1m
    annotations:
      summary: "Database Offline"
      description: "PostgreSQL container is not responding"

  - alert: SlowQueries
    expr: rate(pg_slow_queries_total[5m]) > 10
    for: 10m
    annotations:
      summary: "High Slow Query Rate"
      description: "More than 10 slow queries per minute"
```

---

## Troubleshooting

### Issue: API Container Won't Start

**Symptoms:** `docker ps` shows `Restarting` status

**Debug steps:**
```bash
# 1. Check logs
docker logs softfactory-api

# 2. Check environment variables
docker inspect softfactory-api | grep -A 20 "Env"

# 3. Check database connectivity
docker run --rm --network softfactory_softfactory \
    postgres:15 psql -h db -U postgres -c "SELECT 1;"

# 4. Manual container start with debug
docker run -it --rm \
    -e DATABASE_URL="postgresql://..." \
    softfactory:latest \
    bash
```

### Issue: High Memory Usage

**Symptoms:** API consuming > 80% of allocated memory

**Debug steps:**
```bash
# 1. Check memory limit
docker inspect softfactory-api | grep Memory

# 2. Profile memory usage
docker exec softfactory-api pip install memory-profiler
docker exec softfactory-api python -m memory_profiler app.py

# 3. Check for memory leaks in logs
docker logs softfactory-api | grep -i "memory\|leak"

# 4. Increase memory allocation
# Edit docker-compose-prod.yml, increase mem_limit, then restart
```

### Issue: Database Connection Errors

**Symptoms:** `Connection refused` or `too many connections` errors

**Debug steps:**
```bash
# 1. Check database status
docker exec softfactory-db psql -U postgres -c "SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;"

# 2. Check connection limit
docker exec softfactory-db psql -U postgres -c "SHOW max_connections;"

# 3. Kill idle connections
docker exec softfactory-db psql -U postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# 4. Increase connection pool
# Edit DATABASE_URL connection string in .env-prod
# Add ?max_overflow=20&pool_size=10
```

### Issue: Nginx SSL Certificate Errors

**Symptoms:** `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` in browser

**Debug steps:**
```bash
# 1. Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout | grep -A 5 "Validity"

# 2. Verify certificate matches key
openssl x509 -noout -modulus -in nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/key.pem | openssl md5
# Both should produce same hash

# 3. Test SSL configuration
openssl s_client -connect localhost:443 -showcerts

# 4. Check nginx ssl settings
docker exec softfactory-nginx nginx -T
```

---

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| DevOps Lead | [Name] | +1-XXX-XXX-XXXX | devops@company.com |
| Platform Lead | [Name] | +1-XXX-XXX-XXXX | platform@company.com |
| On-Call | [Name] | +1-XXX-XXX-XXXX | oncall@company.com |

### Incident Response Process

1. **Detect** → Alert triggered in Prometheus/monitoring
2. **Notify** → Slack alert + email to on-call
3. **Assess** → Check monitoring dashboard, run health checks
4. **Mitigate** → Apply quickfix or initiate rollback
5. **Resolve** → Verify services operational, document issue
6. **Post-mortem** → Schedule within 24 hours

### Escalation Path

- Level 1 (Automated checks) → Check health-check.sh
- Level 2 (Manual troubleshooting) → Run debug steps above
- Level 3 (Service restart) → `docker-compose restart web`
- Level 4 (Rollback) → Execute rollback procedures
- Level 5 (DevOps team) → Page on-call via PagerDuty

---

## Post-Deployment Checklist (Within 24 Hours)

- [ ] Monitor error logs for anomalies
- [ ] Verify database backups completed
- [ ] Check resource usage metrics (CPU, memory, disk)
- [ ] Confirm all alert rules firing correctly
- [ ] Review slow query logs
- [ ] Test critical user journeys manually
- [ ] Document any issues encountered
- [ ] Update team wiki with deployment results

---

**Last Updated:** 2026-02-25
**Next Review:** 2026-03-25 (monthly)