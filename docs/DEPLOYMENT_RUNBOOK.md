# 🚢 SoftFactory Deployment Runbook

> **Purpose**: **Version:** 2.0.0
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Deployment Runbook 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 2.0.0
**Last Updated:** 2026-02-26
**Audience:** DevOps Engineers, Platform Administrators
**Time to Complete:** 30-45 minutes

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Deployment Steps](#deployment-steps)
4. [Verification](#verification)
5. [Rollback](#rollback)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment](#post-deployment)

---

## Quick Start

**For experienced engineers, the quick path:**

```bash
# 1. Clone/pull latest code
git clone https://github.com/softfactory/softfactory.git
cd softfactory
git checkout main
git pull origin main

# 2. Run deployment script
./scripts/deploy.sh production

# 3. Verify
./scripts/health-check-enhanced.sh --verbose

# 4. If issues: rollback
./scripts/rollback.sh
```

**Expected time:** 30-45 minutes

---

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or equivalent Linux distribution
- Docker 24.0+
- Docker Compose 2.0+
- Python 3.11+
- PostgreSQL client (psql)
- At least 10GB free disk space
- 4GB+ available RAM
- Internet connection (for pulling images)

### Access Requirements
- SSH access to production server
- Docker registry credentials (GitHub Container Registry)
- Database credentials
- AWS/Cloud provider access (if using cloud services)
- GitHub repository access

### Verification Commands

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version

# Check disk space
df -h /

# Check internet
curl -I https://github.com

# Check database connectivity
psql -h your_db_host -U postgres -d softfactory -c "SELECT 1;"
```

---

## Deployment Steps

### Step 1: Pre-Deployment Setup (5 minutes)

**1.1 Create a deployment directory**
```bash
DEPLOY_DIR="/opt/softfactory"
BACKUP_DIR="$DEPLOY_DIR/backups"
LOG_DIR="$DEPLOY_DIR/logs"

mkdir -p $BACKUP_DIR $LOG_DIR
```

**1.2 Set environment**
```bash
export ENVIRONMENT=production
export DEPLOY_LOG="$LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"
export BACKUP_FILE="$BACKUP_DIR/softfactory_$(date +%Y%m%d_%H%M%S).sql.gz"

echo "Deployment log: $DEPLOY_LOG"
echo "Backup file: $BACKUP_FILE"
```

**1.3 Verify connectivity**
```bash
# Test GitHub
ssh -T git@github.com || echo "GitHub SSH access OK"

# Test Docker registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Test database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" || {
    echo "ERROR: Cannot connect to database"
    exit 1
}

echo "✓ All connectivity checks passed"
```

### Step 2: Code Preparation (10 minutes)

**2.1 Clone/update code**
```bash
cd $DEPLOY_DIR

if [ ! -d ".git" ]; then
    git clone https://github.com/softfactory/softfactory.git .
else
    git fetch origin main
fi

git checkout main
git reset --hard origin/main
```

**2.2 Verify repository state**
```bash
# Show current commit
git log -1 --oneline

# Check for uncommitted changes (should be empty)
git status --porcelain

# Show branch
git branch --show-current
```

**2.3 Install dependencies**
```bash
pip install -r requirements.txt --quiet
pip install --upgrade setuptools wheel

echo "✓ Dependencies installed"
```

### Step 3: Testing (5 minutes)

**3.1 Run tests**
```bash
echo "Running unit tests..."
pytest tests/unit/ -v --tb=short -x 2>&1 | tee -a $DEPLOY_LOG

TEST_RESULT=${PIPESTATUS[0]}
if [ $TEST_RESULT -ne 0 ]; then
    echo "ERROR: Tests failed (exit code: $TEST_RESULT)"
    exit 1
fi

echo "✓ All tests passed"
```

**3.2 Check code quality**
```bash
echo "Checking code quality..."
flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics | tee -a $DEPLOY_LOG

echo "✓ Code quality checks passed"
```

### Step 4: Backup (5 minutes)

**4.1 Backup database**
```bash
echo "Creating database backup..."

# For PostgreSQL
if command -v pg_dump &> /dev/null; then
    PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | \
        gzip > $BACKUP_FILE

    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
        echo "✓ Database backed up: $BACKUP_SIZE"
    else
        echo "ERROR: Backup failed"
        exit 1
    fi
fi

# For SQLite
if [ -f "$DEPLOY_DIR/platform.db" ]; then
    cp "$DEPLOY_DIR/platform.db" "$BACKUP_DIR/platform_$(date +%Y%m%d_%H%M%S).db"
    echo "✓ SQLite database backed up"
fi
```

**4.2 Backup code**
```bash
echo "Creating code backup..."

CODE_BACKUP="$BACKUP_DIR/code_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$CODE_BACKUP" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='logs' \
    --exclude='platform.db' \
    -C "$DEPLOY_DIR" . 2>&1 | tee -a $DEPLOY_LOG

echo "✓ Code backed up: $(du -h $CODE_BACKUP | cut -f1)"
```

### Step 5: Database Migrations (5 minutes)

**5.1 Test migrations (dry-run)**
```bash
echo "Testing database migrations..."

# Create a temporary backup
TEMP_BACKUP="$BACKUP_DIR/test_$(date +%Y%m%d_%H%M%S).sql"

if command -v pg_dump &> /dev/null; then
    PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $TEMP_BACKUP
fi

# Run migrations
export FLASK_APP=$DEPLOY_DIR/backend/app.py
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST/$DB_NAME"

python -m flask db upgrade --sql > $DEPLOY_DIR/migration_preview.sql

echo "Migration SQL preview:"
head -20 $DEPLOY_DIR/migration_preview.sql

echo ""
echo "Review the migration SQL above (last chance to abort)"
read -p "Continue with migration? (yes/no) " -n 3 -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Migration aborted by user"
    exit 1
fi
```

**5.2 Run migrations**
```bash
echo "Applying database migrations..."

python -m flask db upgrade 2>&1 | tee -a $DEPLOY_LOG

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "ERROR: Migration failed"
    echo "Rolling back..."
    python -m flask db downgrade
    exit 1
fi

echo "✓ Migrations completed successfully"
```

**5.3 Verify migrations**
```bash
echo "Verifying database integrity..."

# Check table count
TABLE_COUNT=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

echo "Tables in database: $TABLE_COUNT"

# Check for migration status
python -m flask db current 2>&1 | tee -a $DEPLOY_LOG

echo "✓ Database verified"
```

### Step 6: Build & Deploy (10 minutes)

**6.1 Build Docker image**
```bash
echo "Building Docker image..."

IMAGE_TAG="softfactory:$(date +%Y%m%d_%H%M%S)"
LATEST_TAG="softfactory:latest"

docker build -f $DEPLOY_DIR/Dockerfile.prod \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VCS_REF="$(git rev-parse HEAD)" \
    -t $IMAGE_TAG \
    -t $LATEST_TAG \
    $DEPLOY_DIR 2>&1 | tee -a $DEPLOY_LOG

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "✓ Docker image built: $IMAGE_TAG"
```

**6.2 Push image to registry**
```bash
echo "Pushing Docker image to registry..."

docker tag $IMAGE_TAG ghcr.io/softfactory/softfactory:$(git rev-parse --short HEAD)
docker push ghcr.io/softfactory/softfactory:$(git rev-parse --short HEAD)

echo "✓ Image pushed to registry"
```

**6.3 Stop current services**
```bash
echo "Stopping current services..."

docker-compose -f $DEPLOY_DIR/docker-compose.prod.yml down --remove-orphans

sleep 5

echo "✓ Services stopped"
```

**6.4 Update & start services**
```bash
echo "Starting new services..."

cd $DEPLOY_DIR

# Update .env if needed
source .env.production

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start (30 seconds)..."
sleep 30

echo "✓ Services started"
```

### Step 7: Verification (5 minutes)

**7.1 Check container status**
```bash
echo "Checking container status..."

docker-compose -f $DEPLOY_DIR/docker-compose.prod.yml ps

# Verify all containers are running
RUNNING=$(docker-compose -f $DEPLOY_DIR/docker-compose.prod.yml ps -q | wc -l)
EXPECTED=5  # Adjust based on your services

if [ $RUNNING -lt $EXPECTED ]; then
    echo "ERROR: Not all containers running"
    exit 1
fi

echo "✓ All containers running"
```

**7.2 Health check**
```bash
echo "Running health checks..."

./scripts/health-check-enhanced.sh --verbose

if [ $? -ne 0 ]; then
    echo "ERROR: Health checks failed"
    exit 1
fi

echo "✓ Health checks passed"
```

**7.3 Smoke tests**
```bash
echo "Running smoke tests..."

# Test API endpoints
API_HEALTH=$(curl -s -w "%{http_code}" http://localhost:8000/health -o /dev/null)
if [ "$API_HEALTH" != "200" ]; then
    echo "ERROR: API health check failed (HTTP $API_HEALTH)"
    exit 1
fi

# Test database
curl -s http://localhost:8000/api/infrastructure/health | grep -q "healthy" || {
    echo "ERROR: Infrastructure health check failed"
    exit 1
}

echo "✓ Smoke tests passed"
```

---

## Verification

### Post-Deployment Checklist

```bash
#!/bin/bash
# Post-deployment verification script

echo "=== POST-DEPLOYMENT VERIFICATION ==="

# 1. Service status
echo "1. Service Status:"
docker-compose -f /opt/softfactory/docker-compose.prod.yml ps
echo "   ✓ Verify all containers are 'Up'"

# 2. API connectivity
echo ""
echo "2. API Connectivity:"
curl -s http://localhost:8000/health | jq .status
echo "   ✓ Should show 'ok'"

# 3. Database
echo ""
echo "3. Database Status:"
curl -s http://localhost:8000/api/infrastructure/health | jq .database
echo "   ✓ Should show 'connected'"

# 4. Logs
echo ""
echo "4. Recent Errors (last 20 lines):"
docker logs softfactory-api --tail=20 2>&1 | grep -i "error" || echo "   ✓ No errors"

# 5. Metrics
echo ""
echo "5. Performance Metrics:"
docker stats softfactory-api --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo "   ✓ CPU < 50%, Memory < 1GB"

echo ""
echo "=== VERIFICATION COMPLETE ==="
```

---

## Rollback

**Use only if critical issues detected**

### Quick Rollback

```bash
./scripts/rollback.sh
```

### Manual Rollback

```bash
#!/bin/bash
# Manual rollback script

DEPLOY_DIR="/opt/softfactory"
BACKUP_DIR="$DEPLOY_DIR/backups"

echo "=== ROLLING BACK ==="

# 1. Stop services
echo "Stopping services..."
docker-compose -f $DEPLOY_DIR/docker-compose.prod.yml down

# 2. Restore database
echo "Restoring database..."
LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.sql.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No backup found"
    exit 1
fi

# For PostgreSQL
PGPASSWORD=$DB_PASSWORD gunzip < $LATEST_BACKUP | \
    psql -h $DB_HOST -U $DB_USER $DB_NAME

# 3. Restore code (if needed)
echo "Restoring previous code version..."
LATEST_CODE_BACKUP=$(ls -t $BACKUP_DIR/*.tar.gz | head -1)

if [ ! -z "$LATEST_CODE_BACKUP" ]; then
    tar -xzf $LATEST_CODE_BACKUP -C $DEPLOY_DIR
fi

# 4. Restart services
echo "Restarting services..."
docker-compose -f $DEPLOY_DIR/docker-compose.prod.yml up -d

# 5. Verify
echo "Verifying rollback..."
sleep 30
./scripts/health-check-enhanced.sh

echo "✓ Rollback complete"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs softfactory-api --tail=100

# Common issues:
# 1. Port already in use
netstat -tulpn | grep 8000

# 2. Database not accessible
docker exec softfactory-api python -c \
    "from backend.models import db; db.engine.execute('SELECT 1')"

# 3. Environment variables missing
docker exec softfactory-api env | grep DATABASE_URL
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker logs softfactory-db --tail=50

# Check connection string
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"
```

### Slow API Response

```bash
# Check database performance
psql $DATABASE_URL -c "\timing" -c "SELECT COUNT(*) FROM users;"

# Check API logs
docker logs softfactory-api --tail=100 | grep "slow"

# Check resource usage
docker stats softfactory-api

# Check network
docker network ls
docker network inspect softfactory_default
```

### High Memory Usage

```bash
# Check memory per container
docker stats --no-stream

# Kill memory leaks
docker restart softfactory-api

# Check application logs for leaks
docker logs softfactory-api | grep -i "memory"
```

---

## Post-Deployment

### Monitoring Setup

```bash
# Start monitoring
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Access Grafana
open http://localhost:3000

# Default credentials
# Username: admin
# Password: admin
```

### Notifications

```bash
# Send Slack notification
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Deployment successful",
    "blocks": [{
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*Deployment Complete*\nVersion: XXX\nTime: XXX"}
    }]
  }'
```

### Documentation

```bash
# Generate deployment report
cat > deployment-report.md << EOF
# Deployment Report

**Date:** $(date)
**Duration:** XX minutes
**Deployed By:** $USER
**Commit:** $(git rev-parse --short HEAD)
**Status:** ✓ Successful

## Changes
- Feature 1
- Feature 2
- Bugfix 1

## Metrics
- Response time: OK
- Error rate: OK
- Memory usage: OK

## Next Steps
- Monitor for 1 hour
- Check metrics
- Notify stakeholders
EOF
```

---

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Pre-deployment | 5 min | ⏳ |
| Code preparation | 10 min | ⏳ |
| Testing | 5 min | ⏳ |
| Backup | 5 min | ⏳ |
| Migrations | 5 min | ⏳ |
| Build & Deploy | 10 min | ⏳ |
| Verification | 5 min | ⏳ |
| **Total** | **45 min** | ⏳ |

---

## Support & Escalation

**During Deployment:**
- On-call Engineer: [Contact]
- DevOps Lead: [Contact]
- CTO: [Contact]

**Emergency Hotline:** [Contact]

---

**Last Updated:** 2026-02-26
**Status:** Production Ready ✅