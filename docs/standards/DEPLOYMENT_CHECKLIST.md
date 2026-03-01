# Deployment Checklist v2.0

> **Purpose:** Step-by-step deployment procedure for SoftFactory Platform
> **Owner:** DevOps Team (Team E)
> **Updated:** 2026-02-26
> **Status:** Production Ready

---

## Overview

This document provides a comprehensive checklist for deploying SoftFactory Platform to staging and production environments. Follow each section in order and mark off completed items.

**Deployment Timeline:** ~45 minutes (staging) + ~30 minutes (production)

---

## Pre-Deployment Phase (Hour -1)

Complete these checks 1 hour before scheduled deployment.

### Code Quality & Testing

- [ ] **All tests pass locally**
  ```bash
  pytest tests/ -v --tb=short
  ```

- [ ] **Coverage threshold met (≥80%)**
  ```bash
  coverage run -m pytest tests/
  coverage report --fail-under=80
  ```

- [ ] **Type checking passes**
  ```bash
  mypy backend/ --strict --ignore-missing-imports
  ```

- [ ] **No lint warnings**
  ```bash
  flake8 backend/ --max-complexity=10 --max-line-length=120
  ruff check backend/
  ```

- [ ] **No hardcoded secrets**
  ```bash
  grep -r "password\|api_key\|secret" backend/*.py | grep -v "getenv\|environ\|config"
  ```

- [ ] **All CI/CD workflows pass on main branch**
  - Check GitHub Actions dashboard
  - Verify: Tests ✅, Lint ✅, Security ✅, Build ✅

### Project Structure & Dependencies

- [ ] **Project structure validation passes**
  ```bash
  bash scripts/validate_project_structure.sh
  ```

- [ ] **Requirements.txt is current**
  ```bash
  pip freeze > /tmp/current_requirements.txt
  diff requirements.txt /tmp/current_requirements.txt
  ```

- [ ] **Environment variables documented**
  - Review `.env.example`
  - Confirm all required vars in deployment guide

- [ ] **Database migrations reviewed**
  - Check `backend/models.py` against current schema
  - Verify migration path if needed

### Approval & Sign-Off

- [ ] **QA Team approval obtained** (Team D sign-off)
  - All critical tests passed
  - No known blockers
  - Performance acceptable

- [ ] **Business sign-off obtained**
  - Feature completeness verified
  - Business logic validated
  - Acceptance criteria met

- [ ] **Deployment runbook reviewed**
  - Instructions clear and tested
  - Rollback procedure documented
  - Incident contacts identified

---

## Staging Deployment Phase (Hour 0 → Hour 0+20min)

### Pre-Staging Steps

- [ ] **Create deployment branch**
  ```bash
  git checkout -b deploy/staging-$(date +%Y%m%d-%H%M%S)
  git push origin deploy/staging-*
  ```

- [ ] **Pull latest code**
  ```bash
  git pull origin main
  git status
  ```

- [ ] **Prepare environment variables**
  ```bash
  cp .env.example .env.staging
  # Review and update .env.staging with staging-specific values
  cat .env.staging | grep -E "DATABASE|REDIS|API_KEY"
  ```

### Docker Build & Registry

- [ ] **Build Docker image**
  ```bash
  docker build -t softfactory:staging-$(date +%Y%m%d-%H%M%S) .
  docker build -t softfactory:staging .
  ```

- [ ] **Scan image for vulnerabilities**
  ```bash
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image softfactory:staging
  ```

- [ ] **Image scan passes (no critical vulnerabilities)**
  - Review Trivy report
  - Approve known acceptable issues
  - Document any CVEs accepted

### Staging Deployment

- [ ] **Start staging container**
  ```bash
  docker run -d --name softfactory-staging \
    -p 8001:8000 \
    -e DATABASE_URL="sqlite:///staging.db" \
    -e DEBUG=true \
    softfactory:staging
  ```

- [ ] **Wait for service readiness** (~10 seconds)
  ```bash
  sleep 10
  ```

- [ ] **Verify container is running**
  ```bash
  docker ps | grep softfactory-staging
  docker logs softfactory-staging | tail -20
  ```

### Smoke Tests (Staging)

- [ ] **Health check passes**
  ```bash
  curl -f http://localhost:8001/health
  curl -f http://localhost:8001/api/infrastructure/health
  ```

- [ ] **Core API endpoints respond**
  ```bash
  curl -s http://localhost:8001/api/services/health | jq .
  curl -s http://localhost:8001/api/metrics/prometheus | head -20
  ```

- [ ] **Database connectivity verified**
  ```bash
  curl -X GET http://localhost:8001/api/services/status
  ```

- [ ] **Authentication working**
  ```bash
  # Test demo credentials
  curl -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"demo2026","password":"demo2026"}'
  ```

- [ ] **Error tracking functional**
  ```bash
  curl -X GET http://localhost:8001/api/errors/stats
  ```

### Performance Baseline (Staging)

- [ ] **Response time acceptable**
  ```bash
  curl -w "Response time: %{time_total}s\n" http://localhost:8001/health
  ```

- [ ] **No memory leaks (basic check)**
  ```bash
  docker stats softfactory-staging --no-stream
  ```

- [ ] **Log output clean**
  ```bash
  docker logs softfactory-staging 2>&1 | grep -i "error\|warning" | wc -l
  ```

### Staging Sign-Off

- [ ] **Performance acceptable**
  - Response times < 100ms (API calls)
  - CPU usage < 50%
  - Memory usage < 500MB

- [ ] **All endpoints tested**
  - Auth endpoints working
  - Service endpoints accessible
  - Metrics exported correctly

- [ ] **QA final check on staging**
  - Manual testing completed
  - No new issues discovered
  - Performance verified

---

## Production Deployment Phase (Hour +30 → Hour +1)

### Production Prerequisites

- [ ] **Production environment ready**
  - Database backup completed
  - Current production version tagged in git
  - Rollback procedure tested

- [ ] **Create production tag**
  ```bash
  git tag -a v$(date +%Y.%m.%d-%H%M%S) -m "Production deployment $(date)"
  git push origin v$(date +%Y.%m.%d-%H%M%S)
  ```

- [ ] **Staging has been validated for 10+ minutes**
  - No errors in logs
  - Performance stable
  - No user reports

- [ ] **Change window confirmed**
  - Team available for 2 hours post-deployment
  - Incident commander assigned
  - Communication channels ready

### Production Deployment

- [ ] **Stop current production container (with backup)**
  ```bash
  docker tag softfactory:production softfactory:production-backup-$(date +%s)
  docker stop softfactory-production
  ```

- [ ] **Start production container**
  ```bash
  docker run -d --name softfactory-production \
    -p 8000:8000 \
    -e DATABASE_URL="postgresql://prod_user:REDACTED@prod-db:5432/softfactory" \
    -e ENVIRONMENT="production" \
    softfactory:staging  # Use same image as staging
  ```

- [ ] **Wait for service stabilization** (~15 seconds)
  ```bash
  sleep 15
  ```

- [ ] **Verify production container running**
  ```bash
  docker ps | grep softfactory-production
  ```

### Production Smoke Tests

- [ ] **Health check passes**
  ```bash
  curl -f https://softfactory.com/health
  curl -f https://softfactory.com/api/infrastructure/health
  ```

- [ ] **Core features working**
  ```bash
  # Test each service briefly
  curl -f https://softfactory.com/api/coocook/health
  curl -f https://softfactory.com/api/sns-auto/health
  curl -f https://softfactory.com/api/review/health
  curl -f https://softfactory.com/api/ai-automation/health
  curl -f https://softfactory.com/api/webapp-builder/health
  ```

- [ ] **Metrics collection working**
  ```bash
  curl -s https://softfactory.com/api/metrics/prometheus | head -5
  ```

- [ ] **Error tracking active**
  ```bash
  curl https://softfactory.com/api/errors/stats | jq .
  ```

- [ ] **No critical errors in first 60 seconds**
  ```bash
  docker logs softfactory-production --since 60s | grep -i "critical\|panic\|fatal"
  # Should return nothing
  ```

### Monitoring Activation

- [ ] **Prometheus scraping production**
  - Verify targets: http://prometheus:9090/targets
  - Confirm "softfactory-api" job is UP

- [ ] **Alerting rules active**
  - Error rate alerts armed
  - Performance alerts armed
  - Health alerts armed

- [ ] **Log aggregation collecting**
  - Application logs ingested
  - Error patterns detected
  - Audit log flowing

- [ ] **APM dashboard updated**
  - Service traces appearing
  - Performance metrics updating
  - Error traces visible

### User Communication

- [ ] **"Deployment in progress" banner added** (if applicable)
  - Users notified of potential issues
  - ETA provided

- [ ] **Slack/Teams notification sent**
  - Deployment started message
  - Team notified of timeline
  - Incident link provided

---

## Post-Deployment Phase (Hour +1 → Hour +2)

### Immediate Validation (First 5 minutes)

- [ ] **Error rate normal** (< 0.5%)
  ```bash
  # Check error metrics
  curl https://softfactory.com/api/errors/rate
  ```

- [ ] **Response time acceptable**
  ```bash
  # Sample 5 requests, check timing
  for i in {1..5}; do curl -w "%{time_total}\n" https://softfactory.com/health; done
  ```

- [ ] **No database errors**
  ```bash
  docker logs softfactory-production | grep -i "database.*error"
  # Should return nothing
  ```

- [ ] **Authentication working**
  ```bash
  curl -X POST https://softfactory.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin@softfactory.com","password":"REDACTED"}'
  ```

### Extended Validation (5-30 minutes)

- [ ] **Transaction throughput normal**
  - Confirm booking rates match baseline
  - Verify payment processing working
  - Check notification delivery

- [ ] **Background jobs running**
  - Email queue processing
  - Report generation active
  - Analytics jobs executing

- [ ] **Third-party integrations functional**
  - Stripe payment working
  - Email service active
  - Analytics tracking operational

- [ ] **No memory leaks**
  ```bash
  docker stats softfactory-production --no-stream
  # Memory should stabilize
  ```

### Monitoring & Alerting (30+ minutes)

- [ ] **Dashboard updated**
  - Latest data points visible
  - Trends normal
  - Baselines matched

- [ ] **No critical alerts firing**
  - Check Alertmanager: `http://alertmanager:9093`
  - Investigate any warnings
  - Suppress known false positives

- [ ] **Team feedback positive**
  - Support team reports no issues
  - Business team confirms features working
  - End-users reporting normal operation

### Final Checklist

- [ ] **Remove "deployment in progress" banner**
  - Communicate deployment successful
  - Provide release notes link

- [ ] **Update deployment log**
  ```bash
  echo "✅ Deployment $(date) - v$(git describe --tags) - SUCCESS" >> DEPLOYMENT_LOG.md
  ```

- [ ] **Commit deployment changes**
  ```bash
  git add .
  git commit -m "chore: production deployment $(date)"
  git push origin main
  ```

- [ ] **Close deployment ticket/incident**
  - Document outcomes
  - Note any issues encountered
  - Lessons learned recorded

- [ ] **Archive staging logs**
  ```bash
  docker logs softfactory-staging > staging-deployment-logs-$(date +%Y%m%d).log
  ```

---

## Rollback Procedure (If Needed)

**Use only if critical production issue occurs:**

### Immediate Rollback

1. **Stop production container**
   ```bash
   docker stop softfactory-production
   ```

2. **Restart previous version**
   ```bash
   docker run -d --name softfactory-production \
     -p 8000:8000 \
     softfactory:production-backup-TIMESTAMP
   ```

3. **Verify rollback**
   ```bash
   curl -f https://softfactory.com/health
   ```

4. **Notify team immediately**
   - Post incident alert
   - Begin root cause analysis
   - Document issue in ADR

### Post-Rollback Analysis

- [ ] **Capture production logs before cleanup**
  ```bash
  docker logs softfactory-production-new > production-failure-logs.txt
  ```

- [ ] **Update shared-intelligence/pitfalls.md**
  - Document the issue
  - Add prevention rule

- [ ] **Create ADR for the incident**
  - Problem statement
  - Root cause
  - Prevention measures

- [ ] **Schedule post-mortem**
  - Team review
  - Timeline analysis
  - Action items

---

## Success Criteria

Deployment is considered successful when:

✅ All health checks pass
✅ Error rate < 0.5%
✅ Response time < 100ms (p99)
✅ No critical alerts
✅ Zero database errors
✅ All services responding
✅ Metrics flowing correctly
✅ Team feedback positive

---

## Important Notes

**Before Each Deployment:**
1. Read this checklist in full
2. Understand each step
3. Have all prerequisites ready
4. Communicate timeline to stakeholders

**During Deployment:**
1. Follow steps in order
2. Don't skip checks
3. Document any issues
4. Stay in communication with team

**After Deployment:**
1. Monitor closely for 2 hours
2. Be ready to rollback
3. Update documentation
4. Capture lessons learned

---

## Support Contacts

| Role | Contact | Phone |
|------|---------|-------|
| Incident Commander | TBD | TBD |
| DevOps Lead | TBD | TBD |
| On-Call Engineer | TBD | TBD |
| Platform Lead | TBD | TBD |

---

---

## Environment Variable Reference

All variables that must be set before deployment. Copy `.env.example` and fill in values.

### Required Variables

| Variable | Description | Example | Required In |
|----------|-------------|---------|-------------|
| `PLATFORM_SECRET_KEY` | JWT signing secret | `your-256-bit-secret` | All |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///platform.db` | All |
| `ENVIRONMENT` | Deployment environment | `development` / `production` | All |

### Database Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection (production) | `postgresql://user:pass@host:5432/softfactory` |
| `REDIS_URL` | Redis connection for caching | `redis://localhost:6379` |

### Payment (Stripe)

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret API key |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |

### OAuth Providers

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | Google OAuth redirect URI |
| `FACEBOOK_APP_ID` | Facebook app ID |
| `FACEBOOK_APP_SECRET` | Facebook app secret |
| `FACEBOOK_REDIRECT_URI` | Facebook OAuth redirect URI |
| `KAKAO_REST_API_KEY` | Kakao REST API key |
| `KAKAO_CLIENT_SECRET` | Kakao client secret |
| `KAKAO_REDIRECT_URI` | Kakao OAuth redirect URI |

### CORS & Security

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGIN` | Production frontend origin | (none) |
| `PLATFORM_URL` | Platform base URL | `http://localhost:8000` |

### Telegram Bot (Sonolbot)

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token |
| `TELEGRAM_ALLOWED_USERS` | Comma-separated allowed user IDs |

---

## Database Migration Steps

### Development (SQLite)

```bash
# Database is auto-initialized on first run via init_db()
python -c "from backend.app import create_app; app = create_app()"
```

### Production (PostgreSQL Migration)

```bash
# 1. Export existing SQLite data
python scripts/migrate_to_postgres.py --export-sqlite

# 2. Create PostgreSQL database
createdb softfactory
psql softfactory < schema.sql

# 3. Import data
python scripts/migrate_to_postgres.py --import-postgres

# 4. Update environment variable
export DATABASE_URL="postgresql://user:pass@host:5432/softfactory"

# 5. Verify migration
python -c "
from backend.app import create_app
app = create_app()
with app.app_context():
    from backend.models import db, User
    print(f'Users: {User.query.count()}')
"
```

### Schema Changes

When models change, manually apply schema updates:

```bash
# Compare current DB schema with models
python -c "
from backend.app import create_app
from backend.models import db
app = create_app()
with app.app_context():
    db.create_all()  # Creates missing tables only
    print('Schema sync complete')
"
```

---

## Enhanced Rollback Procedure

### Pre-Rollback Checklist

- [ ] Confirm the issue is deployment-related (not external)
- [ ] Capture current logs before rollback
- [ ] Notify stakeholders of rollback decision
- [ ] Identify the exact commit/tag to roll back to

### Rollback Steps

1. **Stop current production**
   ```bash
   docker stop softfactory-production
   ```

2. **Restore database backup (if schema changed)**
   ```bash
   # SQLite
   cp platform.db.backup platform.db

   # PostgreSQL
   pg_restore -d softfactory backup_file.dump
   ```

3. **Deploy previous version**
   ```bash
   docker run -d --name softfactory-production \
     -p 8000:8000 \
     softfactory:production-backup-TIMESTAMP
   ```

4. **Verify rollback**
   ```bash
   curl -f http://localhost:8000/health
   python scripts/verify_integration.py --no-start --port 8000
   ```

5. **Post-rollback**
   - Document root cause in `shared-intelligence/pitfalls.md`
   - Create ADR for the incident
   - Schedule team post-mortem

---

## Monitoring Setup

### Health Check Monitoring

The `/health` endpoint returns detailed status including:
- Database connectivity
- All 5 service blueprint registrations
- Application version
- Server uptime

```bash
# Continuous monitoring (every 30s)
while true; do
  curl -s http://localhost:8000/health | python -m json.tool
  sleep 30
done
```

### Prometheus Metrics

Verify metrics are being scraped:

```bash
curl -s http://localhost:8000/api/metrics/prometheus | head -20
```

### Log Monitoring

```bash
# Watch for errors
docker logs -f softfactory-production 2>&1 | grep -i "error\|critical\|warning"

# Check error rate
curl -s http://localhost:8000/api/errors/stats | python -m json.tool
```

### Alert Configuration

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 1% | Page on-call engineer |
| Response time (p99) | > 500ms | Alert DevOps channel |
| Database disconnected | health.database != "connected" | Page DBA |
| Memory usage | > 80% | Scale or investigate |
| Disk usage | > 90% | Clean logs, expand disk |

---

## Integration Verification

Before signing off on any deployment, run the integration verification script:

```bash
# Against running server
python scripts/verify_integration.py --no-start --port 8000

# Start fresh server and test
python scripts/verify_integration.py --port 8001 --report-file test_report.json
```

Expected result: All endpoints return expected status codes with demo token authentication.

---

**Last Updated:** 2026-02-26
**Next Review:** 2026-03-10
**Version:** 2.0
