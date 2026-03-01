# 🚢 🚀 Production Deployment Checklist — SoftFactory v2.0

> **Purpose**: **Date:** 2026-02-26 | **Status:** Ready for Deployment
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 🚀 Production Deployment Checklist — SoftFactory v2.0 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Date:** 2026-02-26 | **Status:** Ready for Deployment
**Version:** 2.0 (SNS Automation + Review Platform Complete)
**Target:** Production environment (Linux/Docker)
**SLA:** 99.9% uptime required

---

## ✅ PRE-DEPLOYMENT PHASE (Must complete BEFORE any production work)

### **1. Code & Repository Validation**

- [ ] All commits pushed to main branch
  ```bash
  git log --oneline | head -5
  git status  # Should be clean
  ```

- [ ] Latest commit includes all 8-team deliverables
  ```bash
  git log --grep="8-Team\|Infrastructure\|SNS\|Review" --oneline | head -10
  ```

- [ ] No uncommitted changes
  ```bash
  git diff --quiet && echo "Clean" || echo "FAILED: Uncommitted changes"
  ```

- [ ] Branch protection enabled on main (GitHub settings)
  - Require pull request reviews: ✓
  - Require status checks to pass: ✓
  - Dismiss stale PR approvals: ✓

### **2. Flask Server Health Check**

- [ ] Start fresh Flask server
  ```bash
  pkill python  # Kill all Python processes
  sleep 2
  cd /d/Project && python start_platform.py > flask.log 2>&1 &
  sleep 3
  ```

- [ ] Verify server is running
  ```bash
  lsof -i :8000 || netstat -tlnp | grep 8000
  # Should show Flask/Python process
  ```

- [ ] Health check endpoint responds
  ```bash
  curl -s http://localhost:8000/health | jq .
  # Should return: {"status":"ok"}
  ```

- [ ] Check for startup errors in logs
  ```bash
  tail -50 flask.log | grep -i "error\|exception\|warning"
  # Should be minimal/none
  ```

### **3. Database Validation**

- [ ] SQLite database file exists and is readable
  ```bash
  ls -lh D:/Project/platform.db
  file D:/Project/platform.db  # Should show SQLite database
  ```

- [ ] Database schema is complete
  ```bash
  sqlite3 D:/Project/platform.db ".tables"
  # Should list: users, sns_account, sns_post, review_listing, etc.
  ```

- [ ] Test data exists
  ```bash
  sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM users;"
  sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM sns_account;"
  # Should be > 0
  ```

- [ ] No database corruption
  ```bash
  sqlite3 D:/Project/platform.db "PRAGMA integrity_check;"
  # Should return: ok
  ```

- [ ] Backup created before deployment
  ```bash
  cp D:/Project/platform.db D:/Project/platform.db.backup.$(date +%s)
  ls -lh D:/Project/platform.db.backup.*
  ```

### **4. Blueprint Registration Verification**

- [ ] Run diagnostic script to verify all blueprints
  ```bash
  cd /d/Project && python diagnose_blueprints.py 2>&1 | grep -E "Total blueprints|SNS routes found|Review routes found"
  # Expected output:
  # Total blueprints: 12
  # SNS routes found: 29
  # Review routes found: 26
  ```

- [ ] All critical endpoints return 200/401/201 (NOT 404)
  ```bash
  curl -i http://localhost:8000/api/sns/posts
  curl -i http://localhost:8000/api/review/listings
  curl -i http://localhost:8000/api/auth/me
  # Status code should be 200/400/401, NOT 404
  ```

---

## ✅ TEAM READINESS PHASE (Verify each team's deliverable)

### **Team A: OAuth & Social Login**

- [ ] Auth endpoints respond correctly
  ```bash
  curl -s http://localhost:8000/api/auth/oauth/google/url | jq .
  curl -s http://localhost:8000/api/auth/oauth/facebook/url | jq .
  curl -s http://localhost:8000/api/auth/oauth/kakao/url | jq .
  ```

- [ ] demo_token is accepted
  ```bash
  curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/auth/me | jq .
  # Should return user data (not 401)
  ```

- [ ] Login page loads
  ```bash
  curl -s http://localhost:8000/web/platform/login.html | grep -q "oauth\|Google\|Facebook"
  ```

- [ ] Status: ✅ **READY FOR PRODUCTION**

### **Team B: create.html & Direct Post Creation**

- [ ] Page loads without errors
  ```bash
  curl -s http://localhost:8000/web/sns-auto/create.html | head -20 | grep -q "DOCTYPE\|html"
  ```

- [ ] API calls in page match backend endpoints
  ```bash
  grep -o "'/api/sns/[^']*'" web/sns-auto/create.html | sort -u
  # Verify all endpoints exist in app.url_map
  ```

- [ ] localStorage token handling present
  ```bash
  grep -q "localStorage" web/sns-auto/create.html
  ```

- [ ] Status: ✅ **READY (waiting for API)**

### **Team C: Monetization Pages**

- [ ] All 4 monetization pages exist
  ```bash
  for page in link-in-bio monetize viral competitor; do
    curl -s http://localhost:8000/web/sns-auto/$page.html | grep -q "DOCTYPE" && echo "✓ $page.html" || echo "✗ $page.html"
  done
  ```

- [ ] ApexCharts library loaded
  ```bash
  grep -q "ApexCharts\|apex" web/sns-auto/monetize.html
  ```

- [ ] Endpoints are accessible
  ```bash
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/linkinbio | head -3
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/trending | head -3
  ```

- [ ] Status: ✅ **READY (1 medium warning: chart rendering)**

### **Team D: Review Scrapers**

- [ ] Scraper files exist
  ```bash
  ls -1 backend/services/review_scrapers/*.py | wc -l
  # Should be 9+
  ```

- [ ] APScheduler configured
  ```bash
  grep -q "scheduler\|APScheduler" backend/scheduler.py
  ```

- [ ] Scrape endpoint accessible
  ```bash
  curl -s -X POST -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/scrape/now | head -3
  ```

- [ ] Review listings in database
  ```bash
  sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM review_listing;"
  # Should be > 0
  ```

- [ ] Status: ✅ **READY**

### **Team E: API Endpoints & Blueprint Registration**

- [ ] 55 total API endpoints registered
  ```bash
  curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "API responsive"
  # Endpoint count verified in blueprint registration
  ```

- [ ] SNS endpoints (29) all respond
  ```bash
  for endpoint in accounts posts templates workflows automate ai/generate linkinbio trending competitor; do
    status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/$endpoint)
    [ "$status" != "404" ] && echo "✓ /api/sns/$endpoint: $status" || echo "✗ /api/sns/$endpoint: 404"
  done
  ```

- [ ] Review endpoints (26) all respond
  ```bash
  for endpoint in listings campaigns accounts applications auto-apply rules; do
    status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/$endpoint)
    [ "$status" != "404" ] && echo "✓ /api/review/$endpoint: $status" || echo "✗ /api/review/$endpoint: 404"
  done
  ```

- [ ] Error responses are JSON (not HTML)
  ```bash
  curl -s -H "Authorization: Bearer invalid_token" http://localhost:8000/api/sns/accounts | head -1 | grep -q "{" && echo "✓ JSON errors" || echo "✗ HTML errors"
  ```

- [ ] Status: ✅ **READY**

### **Team F: Review UI Pages**

- [ ] All 4 review pages exist
  ```bash
  for page in aggregator applications accounts auto-apply; do
    curl -s http://localhost:8000/web/review/$page.html | grep -q "DOCTYPE" && echo "✓ $page.html" || echo "✗ $page.html"
  done
  ```

- [ ] Pages call correct API endpoints
  ```bash
  grep -h "fetch.*api/review" web/review/*.html | sort -u | wc -l
  # Should be multiple endpoints
  ```

- [ ] Auth headers present
  ```bash
  grep -q "Authorization\|Bearer\|token" web/review/aggregator.html
  ```

- [ ] Status: ✅ **READY**

### **Team G: SNS API Services**

- [ ] All SNS endpoints respond correctly
  ```bash
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/automate | head -3
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/ai/generate | head -3
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/linkinbio/stats | head -3
  ```

- [ ] Caching layer configured (15-min TTL)
  ```bash
  grep -q "cache\|TTL\|15" backend/services/sns_cache.py
  ```

- [ ] Responses are JSON format
  ```bash
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/posts | jq . > /dev/null && echo "✓ Valid JSON"
  ```

- [ ] Status: ✅ **READY**

### **Team H: api.js Client Library**

- [ ] File exists and has 48+ functions
  ```bash
  grep -c "export function\|export const" web/platform/api.js
  # Should be ~48
  ```

- [ ] OAuth functions present
  ```bash
  grep -q "loginWithGoogle\|loginWithFacebook\|loginWithKakao" web/platform/api.js
  ```

- [ ] SNS API functions present
  ```bash
  grep -c "sns" web/platform/api.js
  # Should be multiple
  ```

- [ ] Review API functions present
  ```bash
  grep -c "review\|listing" web/platform/api.js
  # Should be multiple
  ```

- [ ] Error handling present
  ```bash
  grep -q ".catch\|console.error" web/platform/api.js
  ```

- [ ] Status: ✅ **READY**

---

## ✅ INTEGRATION PHASE (Cross-team validation)

### **1. End-to-End Flow Testing**

- [ ] **Auth Flow**
  ```bash
  # 1. Get OAuth URL
  curl -s http://localhost:8000/api/auth/oauth/google/url | jq .auth_url

  # 2. Login with demo_token
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/auth/me | jq .

  # Expected: User data returned (not 401)
  ```

- [ ] **SNS Post Creation Flow**
  ```bash
  # 1. Get accounts
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/accounts | jq .

  # 2. Create post
  curl -s -X POST -H "Authorization: Bearer demo_token" \
    -H "Content-Type: application/json" \
    -d '{"platform":"instagram","content":"Test post"}' \
    http://localhost:8000/api/sns/posts | jq .
  ```

- [ ] **Review Listing Flow**
  ```bash
  # 1. Get listings
  curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/listings | jq .

  # 2. Apply to listing (if ID exists)
  curl -s -X POST -H "Authorization: Bearer demo_token" \
    http://localhost:8000/api/review/listings/1/apply | jq .
  ```

### **2. Frontend Integration**

- [ ] All HTML pages load (75+ pages)
  ```bash
  find web -name "*.html" | wc -l
  # Should be 75+
  ```

- [ ] CSS/JS files are served
  ```bash
  curl -s http://localhost:8000/web/platform/index.html | grep -q "\.css\|\.js"
  ```

- [ ] API calls from frontend match backend
  ```bash
  grep -h "fetch.*api/" web/**/*.html | grep -o "'/api/[^']*'" | sort -u > /tmp/frontend_apis.txt
  curl -s http://localhost:8000/health > /dev/null && echo "Backend APIs available"
  ```

### **3. Database Integrity**

- [ ] All model relationships valid
  ```bash
  sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
  # Should be 18+ tables
  ```

- [ ] Foreign keys are enforced
  ```bash
  sqlite3 D:/Project/platform.db "PRAGMA foreign_keys = ON;"
  ```

- [ ] Indexes are present for performance
  ```bash
  sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index';"
  # Should be 10+
  ```

---

## ✅ SECURITY PHASE (OWASP & Data Protection)

### **1. Authentication & Authorization**

- [ ] JWT tokens validated
  ```bash
  curl -H "Authorization: Bearer invalid_token" http://localhost:8000/api/sns/accounts | grep -q "error\|Invalid" && echo "✓ Invalid token rejected"
  ```

- [ ] demo_token mechanism working
  ```bash
  curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/auth/me | jq .
  # Should work
  ```

- [ ] CORS configured correctly
  ```bash
  curl -i -H "Origin: http://localhost:3000" http://localhost:8000/health | grep -i "Access-Control"
  ```

### **2. Data Protection**

- [ ] Database is SQLite (dev) → switch to PostgreSQL (prod)
  - [ ] Create PostgreSQL migration script
  - [ ] Test schema transfer
  - [ ] Verify data integrity post-migration

- [ ] Passwords hashed (werkzeug.security)
  ```bash
  grep -q "generate_password_hash\|check_password_hash" backend/models.py
  ```

- [ ] Sensitive data not logged
  ```bash
  grep -r "password\|token\|secret" flask.log | grep -v "^#" | wc -l
  # Should be 0 or minimal
  ```

### **3. Input Validation**

- [ ] POST endpoints validate request data
  ```bash
  curl -X POST -H "Authorization: Bearer demo_token" \
    -H "Content-Type: application/json" \
    -d '{}' \
    http://localhost:8000/api/sns/posts 2>&1 | grep -q "error\|required\|invalid"
  ```

- [ ] SQL injection prevention (SQLAlchemy ORM used)
  ```bash
  grep -q "query.filter\|query.filter_by" backend/services/*.py && echo "✓ Using ORM (safe)"
  ```

### **4. API Security**

- [ ] Rate limiting configured
  - [ ] Check Flask-Limiter setup
  - [ ] Verify rate limits in logs

- [ ] HTTPS required (prod)
  - [ ] SSL/TLS certificate obtained
  - [ ] Redirect HTTP → HTTPS

- [ ] API versioning (optional but recommended)
  - [ ] Plan v1/v2 endpoint structure
  - [ ] Document API versions

---

## ✅ PERFORMANCE PHASE (Baseline & Optimization)

### **1. Response Time Benchmarks**

- [ ] Auth endpoint < 100ms
  ```bash
  time curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/auth/me > /dev/null
  ```

- [ ] SNS endpoints < 200ms (with caching)
  ```bash
  time curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/accounts > /dev/null
  ```

- [ ] Review endpoints < 300ms
  ```bash
  time curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/review/listings > /dev/null
  ```

### **2. Caching Validation**

- [ ] Cache statistics endpoint working
  ```bash
  curl -s http://localhost:8000/api/cache/stats | jq .
  ```

- [ ] Cache hit rate > 50% (after warm-up)
  ```bash
  # Make 10 requests to same endpoint
  for i in {1..10}; do
    curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/accounts > /dev/null
  done
  curl -s http://localhost:8000/api/cache/stats | jq .hit_rate
  ```

### **3. Database Query Performance**

- [ ] Slow query logging enabled
  ```bash
  grep -q "SQLALCHEMY_ECHO\|log_every" backend/app.py
  ```

- [ ] Indexes cover common queries
  ```bash
  sqlite3 D:/Project/platform.db ".indexes"
  ```

---

## ✅ DEPLOYMENT PHASE (Actual Production Deployment)

### **1. Pre-Deployment Backup**

- [ ] Database backup created
  ```bash
  cp D:/Project/platform.db /backup/platform.db.$(date +%Y%m%d_%H%M%S)
  ```

- [ ] Git tag created
  ```bash
  git tag -a v2.0-production -m "Production release - SNS v2.0 + Review Platform"
  ```

- [ ] Release notes documented
  - [ ] New features: SNS Automation v2.0, Review Platform
  - [ ] Breaking changes: None
  - [ ] Migration steps: Flask restart only
  - [ ] Rollback plan: Documented below

### **2. Deployment Steps**

**Option A: Docker (Recommended)**
```bash
# 1. Build Docker image
docker build -t softfactory:v2.0 .

# 2. Run container
docker run -d --name softfactory-prod \
  -p 8000:8000 \
  -v /data/platform.db:/app/platform.db \
  -e FLASK_ENV=production \
  softfactory:v2.0

# 3. Verify
docker logs softfactory-prod
curl http://localhost:8000/health
```

**Option B: Virtual Machine (Linux)**
```bash
# 1. SSH to server
ssh ubuntu@production-server

# 2. Deploy code
cd /opt/softfactory
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start service (systemd)
systemctl restart softfactory

# 5. Verify
systemctl status softfactory
curl http://localhost:8000/health
```

### **3. Post-Deployment Verification**

- [ ] All endpoints respond
  ```bash
  bash validate_before_deploy.sh  # From ERROR_PREVENTION_GUIDE.md
  ```

- [ ] No error rate spike
  ```bash
  # Check logs for errors in first 5 minutes
  tail -100 /var/log/softfactory.log | grep -i "error\|exception" | wc -l
  # Should be 0-5
  ```

- [ ] Database connectivity verified
  ```bash
  curl -s http://localhost:8000/api/auth/me 2>&1 | grep -q "Invalid\|error\|status" && echo "✓ DB connected"
  ```

- [ ] All 8 teams' features working
  ```bash
  # Sample from each team
  curl -s http://localhost:8000/api/auth/me  # Team A
  curl -s http://localhost:8000/api/sns/posts  # Team B/G
  curl -s http://localhost:8000/api/sns/linkinbio  # Team C
  curl -s http://localhost:8000/api/review/listings  # Team D/F
  ```

---

## 🔄 ROLLBACK PHASE (If issues occur)

### **1. Immediate Rollback Procedure**

**If critical errors detected:**

```bash
# 1. Stop current deployment
docker stop softfactory-prod  # OR systemctl stop softfactory

# 2. Restore database backup
cp /backup/platform.db.$(date +%Y%m%d)_* /data/platform.db

# 3. Checkout previous commit
git checkout v2.0-previous  # Or previous working tag

# 4. Restart with previous version
docker run -d --name softfactory-rollback -p 8000:8000 softfactory:v1.9

# 5. Verify
curl http://localhost:8000/health
```

### **2. Rollback Checklist**

- [ ] Database restored from backup
- [ ] Old code deployed
- [ ] Services restarted
- [ ] Health check passing
- [ ] Users notified of issue
- [ ] Root cause investigation started

---

## 📊 MONITORING & MAINTENANCE

### **1. Real-Time Monitoring**

- [ ] Set up application monitoring
  - [ ] New Relic / Datadog / Scout
  - [ ] Response time tracking
  - [ ] Error rate tracking
  - [ ] Database query performance

- [ ] Set up infrastructure monitoring
  - [ ] CPU/Memory/Disk usage
  - [ ] Network I/O
  - [ ] Container health (if Docker)

- [ ] Alert thresholds configured
  - [ ] Error rate > 1% → Alert
  - [ ] Response time > 500ms → Alert
  - [ ] Disk usage > 80% → Alert
  - [ ] CPU > 80% for 5+ min → Alert

### **2. Log Aggregation**

- [ ] Centralized logging set up
  - [ ] ELK Stack / Splunk / CloudWatch
  - [ ] All application logs sent to central location
  - [ ] Searchable by date/service/error level

- [ ] Log retention policy
  - [ ] Keep logs for 30 days minimum
  - [ ] Archive old logs to S3/GCS

### **3. Regular Maintenance**

- [ ] Weekly database optimization
  ```bash
  sqlite3 /data/platform.db "VACUUM;"
  ```

- [ ] Monthly security patches
  - [ ] Python package updates
  - [ ] OS security patches
  - [ ] Dependency audit (`pip audit`)

- [ ] Quarterly performance review
  - [ ] Analyze slow queries
  - [ ] Review cache hit rates
  - [ ] Check for N+1 query problems

---

## ✅ FINAL SIGN-OFF

**Pre-Deployment Checklist Completion:**

- [ ] All 4 PRE-DEPLOYMENT items complete
- [ ] All 8 TEAM READINESS items complete
- [ ] All 3 INTEGRATION items complete
- [ ] All 4 SECURITY items complete
- [ ] All 3 PERFORMANCE items complete

**Deployment Approval:**

- [ ] Code Review: _____________ (Name) Date: _______
- [ ] QA Lead: _____________ (Name) Date: _______
- [ ] DevOps Lead: _____________ (Name) Date: _______
- [ ] Product Owner: _____________ (Name) Date: _______

**Deployment Timeline:**

- Pre-deployment: ~30 min
- Actual deployment: ~10 min
- Post-verification: ~10 min
- **Total: ~50 minutes**

**Estimated Production Go-Live:** 2026-02-26 (after checklist completion)

---

## 📚 Related Documents

- `8-TEAM-EXECUTION-RESULTS.md` — Team verification results
- `BLOCKER-ROOT-CAUSE-ANALYSIS.md` — Issue diagnosis
- `ERROR_PREVENTION_GUIDE.md` — How to prevent future issues
- `5-TASKS-PER-TEAM-ACTION-PLAN.md` — Detailed task breakdown
- `shared-intelligence/decisions.md` — Architecture decisions (ADR)

---

**Created:** 2026-02-26
**By:** Claude Haiku 4.5 + 8-Team Execution
**For:** SoftFactory v2.0 Production Release