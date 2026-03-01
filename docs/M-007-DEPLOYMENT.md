# 🚢 M-007 Complete Deployment Guide

> **Purpose**: **Version:** 1.0.0
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 M-007 Complete Deployment Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Production-Ready
**Target Environments:** Development, Staging, Production

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Database Migration](#database-migration)
5. [Local Development](#local-development)
6. [Testing & Validation](#testing--validation)
7. [Docker Deployment](#docker-deployment)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Production Deployment](#production-deployment)
10. [Monitoring & Observability](#monitoring--observability)
11. [Troubleshooting](#troubleshooting)
12. [Rollback Procedures](#rollback-procedures)

---

## Overview

M-007 deployment consists of:
- **Backend:** Flask API with SNS/Review services (Python 3.11+)
- **Frontend:** Static HTML/JS pages (nginx or Flask static serving)
- **Database:** SQLite (dev) → PostgreSQL (production)
- **Background Jobs:** APScheduler for SNS automation
- **Caching:** Optional Redis for performance

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌────▼────┐
   │ API     │          │ API     │
   │ Server 1│          │ Server 2│
   │ :8000   │          │ :8001   │
   └────┬────┘          └────┬────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼──────┐        ┌────▼──────┐
   │PostgreSQL │        │   Redis   │
   │  14+      │        │  (Cache)  │
   └───────────┘        └───────────┘
```

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2GB | 4GB |
| Disk | 10GB | 50GB |
| OS | Linux/macOS/Windows | Linux (Ubuntu 20.04+) |

### Software Requirements

```bash
# Core
Python 3.11+
Node.js 22+ (optional, for frontend build)
Git 2.30+

# Database
PostgreSQL 14+ (production)
SQLite 3.30+ (development)

# Optional
Docker 24.0+
Redis 7.0+ (for caching)
nginx 1.18+ (as reverse proxy)
```

### Accounts & Credentials

- GitHub repository access
- Stripe API keys (for payment features)
- OAuth credentials (Google, Facebook, KakaoTalk)
- AWS/Linode/Digital Ocean credentials (for hosting)
- SMTP credentials (for email notifications)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/softfactory.git
cd softfactory
```

### 2. Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key dependencies (from requirements.txt):**
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.5.2
requests==2.32.3
APScheduler==3.10.4
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pyjwt==2.8.1
stripe==5.4.0
```

### 4. Environment Configuration

Create `.env` file in project root:

```bash
# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT=development  # development, staging, production
DEBUG=True               # Set to False in production
LOG_LEVEL=DEBUG          # DEBUG, INFO, WARNING, ERROR

# ============================================
# SERVER
# ============================================
PORT=8000
HOST=0.0.0.0
WORKERS=4  # For production (gunicorn)
WORKER_CLASS=sync  # or gevent for async

# ============================================
# DATABASE
# ============================================
# Development (SQLite)
DATABASE_URL=sqlite:///D:/Project/platform.db

# Production (PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/softfactory

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600

# ============================================
# JWT & SECURITY
# ============================================
JWT_SECRET_KEY=your-very-long-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# Encryption key for sensitive data
ENCRYPTION_KEY=your-32-byte-encryption-key-change-this

# ============================================
# CORS & SECURITY
# ============================================
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://softfactory.com
ALLOW_CREDENTIALS=True

# ============================================
# OAUTH CREDENTIALS
# ============================================
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/oauth/google/callback

FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/auth/oauth/facebook/callback

KAKAO_REST_API_KEY=your-kakao-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/api/auth/oauth/kakao/callback

# ============================================
# STRIPE PAYMENT
# ============================================
STRIPE_SECRET_KEY=sk_live_xxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxx

# ============================================
# REDIS (Optional, for Caching)
# ============================================
REDIS_URL=redis://localhost:6379
REDIS_DB=0
CACHE_TTL=900  # 15 minutes

# ============================================
# EMAIL & NOTIFICATIONS
# ============================================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@softfactory.com

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# ============================================
# SNS AUTOMATION
# ============================================
SCRAPER_RATE_LIMIT=2  # Seconds between requests
SCRAPER_TIMEOUT=120   # Seconds
MAX_CONCURRENT_SCRAPES=3

# ============================================
# ANTHROPIC CLAUDE
# ============================================
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 5. Security Checklist

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_hex(32))"  # JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(16))"  # ENCRYPTION_KEY

# Never commit .env to git
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# Restrict file permissions
chmod 600 .env
```

---

## Database Migration

### 1. SQLite (Development)

```bash
# Initialize database
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"

# Verify
sqlite3 platform.db ".tables"
```

### 2. PostgreSQL (Production)

#### 2.1 Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE softfactory;
CREATE USER softfactory_user WITH PASSWORD 'your-secure-password';
ALTER ROLE softfactory_user SET client_encoding TO 'utf8';
ALTER ROLE softfactory_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE softfactory_user SET default_transaction_deferrable TO on;
ALTER ROLE softfactory_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE softfactory TO softfactory_user;
\q
```

#### 2.2 Update .env

```bash
# Change DATABASE_URL
DATABASE_URL=postgresql://softfactory_user:your-secure-password@localhost:5432/softfactory
```

#### 2.3 Run Migration

```bash
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"
```

#### 2.4 Verify

```bash
psql -U softfactory_user -d softfactory -c "\dt"
```

### 3. Database Backup

```bash
# PostgreSQL
pg_dump -U softfactory_user softfactory > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -U softfactory_user softfactory < backup_20260226_100000.sql

# SQLite
cp platform.db platform.db.backup_$(date +%Y%m%d_%H%M%S)
```

---

## Local Development

### 1. Run Flask Server

```bash
python start_platform.py

# Server starts at http://localhost:8000
# Press CTRL+C to stop
```

### 2. Run with Gunicorn (Production-like)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:create_app()
```

### 3. Run with Hot Reload

```bash
flask --app backend.app run --reload
```

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# SNS LinkInBio
curl -H "Authorization: Bearer demo_token" \
  http://localhost:8000/api/sns/linkinbio

# Review Aggregated
curl -H "Authorization: Bearer demo_token" \
  http://localhost:8000/api/review/aggregated
```

---

## Testing & Validation

### 1. Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-flask

# Run tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=backend --cov-report=html
```

### 2. Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Full test suite
pytest tests/ -v --cov=backend --cov-report=term-missing
```

### 3. API Endpoint Tests

```bash
# Using curl (manual)
./scripts/test_api.sh

# Using Python requests
python -m pytest tests/integration/test_api_endpoints.py -v

# Using Postman/Thunder Client
# Import collection from: docs/postman/M-007-API.postman_collection.json
```

### 4. Code Quality Checks

```bash
# Linting
flake8 backend/ --max-line-length=120
pylint backend/

# Code formatting
black backend/
isort backend/

# Type checking
mypy backend/ --ignore-missing-imports

# Security scanning
bandit -r backend/
```

### 5. Performance Testing

```bash
# Load testing
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Profile memory usage
pip install memory-profiler
python -m memory_profiler backend/app.py
```

---

## Docker Deployment

### 1. Create Dockerfile

Already provided in project root. Build and run:

```bash
# Build image
docker build -t softfactory:latest .

# Run container
docker run -d \
  --name softfactory-app \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///tmp/platform.db \
  -e JWT_SECRET_KEY=your-key \
  softfactory:latest
```

### 2. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: softfactory
      POSTGRES_USER: softfactory_user
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U softfactory_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://softfactory_user:your-password@postgres:5432/softfactory
      REDIS_URL: redis://redis:6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app/backend
    command: gunicorn -w 4 -b 0.0.0.0:8000 backend.app:create_app()

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./web:/usr/share/nginx/html
    depends_on:
      - api

volumes:
  postgres_data:

networks:
  default:
    name: softfactory-net
```

Run all services:

```bash
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop all
docker-compose down
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy M-007

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main, staging]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14-alpine
        env:
          POSTGRES_DB: test_softfactory
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-flask

      - name: Lint
        run: |
          flake8 backend/ --max-line-length=120 --count --exit-zero
          black --check backend/

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=backend --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_softfactory
        run: pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
        run: |
          mkdir -p ~/.ssh
          echo "$DEPLOY_KEY" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST './scripts/deploy.sh'
```

---

## Production Deployment

### 1. Pre-deployment Checklist

```bash
# [ ] All tests passing
# [ ] Code review approved
# [ ] Security scan clean (0 critical issues)
# [ ] Database backup created
# [ ] Monitoring configured
# [ ] Rollback plan documented
# [ ] Load balancer health checks configured
# [ ] SSL/TLS certificates valid
```

### 2. Deploy Script

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Variables
DEPLOYMENT_DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/var/www/softfactory"
BACKUP_DIR="/var/backups/softfactory"

# 1. Backup current deployment
echo "Creating backup..."
cp -r $APP_DIR $BACKUP_DIR/backup_$DEPLOYMENT_DATE

# 2. Pull latest code
echo "Pulling latest code..."
cd $APP_DIR
git pull origin main

# 3. Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
echo "Running database migrations..."
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"

# 5. Run tests
echo "Running tests..."
pytest tests/ -v --tb=short

# 6. Restart service
echo "Restarting service..."
systemctl restart softfactory

# 7. Health check
echo "Verifying deployment..."
sleep 5
if curl -f http://localhost:8000/health > /dev/null; then
  echo "✅ Deployment successful!"
  exit 0
else
  echo "❌ Health check failed, rolling back..."
  rm -rf $APP_DIR
  cp -r $BACKUP_DIR/backup_$DEPLOYMENT_DATE $APP_DIR
  systemctl restart softfactory
  exit 1
fi
```

### 3. Systemd Service File

Create `/etc/systemd/system/softfactory.service`:

```ini
[Unit]
Description=SoftFactory Platform
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=softfactory
WorkingDirectory=/var/www/softfactory
ExecStart=/var/www/softfactory/venv/bin/gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/softfactory/access.log \
  --error-logfile /var/log/softfactory/error.log \
  backend.app:create_app()
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable softfactory
sudo systemctl start softfactory
sudo systemctl status softfactory
```

### 4. nginx Configuration

Create `/etc/nginx/sites-available/softfactory`:

```nginx
upstream api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name softfactory.com www.softfactory.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name softfactory.com www.softfactory.com;

    # SSL certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/softfactory.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/softfactory.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/softfactory_access.log;
    error_log /var/log/nginx/softfactory_error.log;

    # Compression
    gzip on;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/json;
    gzip_min_length 1000;

    # API proxy
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_read_timeout 120s;
    }

    # Static files
    location / {
        root /var/www/softfactory/web;
        try_files $uri $uri/ /index.html;
        expires 24h;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://api;
        access_log off;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/softfactory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Monitoring & Observability

### 1. Prometheus Metrics

Flask endpoint exposes metrics:

```bash
curl http://localhost:8000/metrics
```

Prometheus config (`/etc/prometheus/prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'softfactory'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 2. Logging

Logs written to:
- `/var/log/softfactory/app.log` (application)
- `/var/log/softfactory/error.log` (errors)
- `/var/log/softfactory/access.log` (nginx)

View logs:

```bash
# Real-time
tail -f /var/log/softfactory/app.log

# Filter errors
grep ERROR /var/log/softfactory/app.log

# Last 100 lines
tail -100 /var/log/softfactory/app.log
```

### 3. Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/api/infrastructure/health

# Database status
curl http://localhost:8000/api/infrastructure/health | jq '.database_status'
```

### 4. Alerting

Set up alerts for:
- API response time > 500ms
- Error rate > 1%
- Disk usage > 80%
- Memory usage > 85%
- Database connection pool exhausted

---

## Troubleshooting

### Common Issues

#### Port 8000 Already in Use

```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

#### Database Connection Error

```bash
# Check PostgreSQL running
systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection
psql -U softfactory_user -d softfactory -c "SELECT 1"
```

#### Permission Denied

```bash
# Fix directory permissions
sudo chown -R softfactory:softfactory /var/www/softfactory
sudo chmod -R 755 /var/www/softfactory

# Fix log directory
sudo mkdir -p /var/log/softfactory
sudo chown softfactory:softfactory /var/log/softfactory
sudo chmod 755 /var/log/softfactory
```

#### Module Not Found

```bash
# Verify virtual environment activated
which python  # Should show venv path

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

---

## Rollback Procedures

### Full Rollback (Systemd)

```bash
# Stop current version
sudo systemctl stop softfactory

# Restore from backup
sudo rm -rf /var/www/softfactory
sudo cp -r /var/backups/softfactory/backup_20260226_100000 /var/www/softfactory

# Start service
sudo systemctl start softfactory

# Verify
curl http://localhost:8000/health
```

### Database Rollback

```bash
# Backup current state
pg_dump softfactory > backup_failed_20260226.sql

# Restore from backup
psql softfactory < /var/backups/softfactory/backup_20260225.sql

# Verify
psql softfactory -c "SELECT COUNT(*) FROM users"
```

### Git Rollback

```bash
# View commit history
git log --oneline | head -10

# Revert to previous version
git revert <commit-hash>
git push origin main

# Deploy reverted code
./scripts/deploy.sh
```

---

## Deployment Checklist

```
PRE-DEPLOYMENT
[ ] All tests passing (unit + integration + e2e)
[ ] Code review approved
[ ] Security scan clean (bandit, safety)
[ ] Performance benchmarks acceptable
[ ] Database backup created
[ ] Rollback plan documented
[ ] Team notification sent

DEPLOYMENT
[ ] Pull latest code
[ ] Install/verify dependencies
[ ] Run database migrations
[ ] Health check passed
[ ] Monitor error rate (0 errors in 5 mins)
[ ] Smoke test critical paths
[ ] Monitor performance metrics

POST-DEPLOYMENT
[ ] All endpoints responding
[ ] Database queries performing
[ ] No increase in error logs
[ ] Email notifications working
[ ] Background jobs running
[ ] Monitoring alerts configured
[ ] User notification sent
```

---

**Document maintained by:** Team J (Documentation + Deployment)
**Last reviewed:** 2026-02-26
**Status:** Production-Ready ✅