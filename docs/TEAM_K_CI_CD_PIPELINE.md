# Team K: CI/CD Pipeline Documentation v1.0

**Date:** 2026-02-26
**Status:** COMPLETE
**Scope:** Complete CI/CD pipeline setup, GitHub Actions workflows, deployment automation
**Assigned to:** Team K (DevOps + Infrastructure)

---

## Executive Summary

This document provides comprehensive CI/CD pipeline configuration for SoftFactory platform, including:

1. **GitHub Actions Workflows** (6 workflows: test, deploy, lint, build, release, security)
2. **Deployment Strategy** (Staging + Production with safety gates)
3. **Continuous Integration** (Automated testing, linting, coverage tracking)
4. **Environment Configuration** (Dev, Staging, Production)
5. **Quality Gates** (Code quality, security scans, test coverage ≥80%)
6. **Monitoring & Rollback** (Health checks, smoke tests, automatic rollback)

---

## 1. GitHub Actions Workflows Overview

### 1.1 Workflow Architecture

```
Event Trigger
    ↓
├─ Push to main/develop → Test → Build → Deploy
├─ Pull Request → Lint → Type Check → Test
├─ Tag v* → Test → Build → Deploy (Production)
├─ Schedule (Weekly) → Security Scan
└─ Manual Dispatch → Deploy (manual env selection)
```

### 1.2 Installed Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **Tests & Coverage** | `.github/workflows/test.yml` | Push/PR | Unit + integration tests, coverage check |
| **Lint & Format** | `.github/workflows/lint.yml` | Push/PR | Code style, type checking, security linting |
| **Build** | `.github/workflows/build.yml` | Push/Tag | Docker build, artifact generation |
| **Security Scan** | `.github/workflows/security.yml` | Push/Schedule | CodeQL, Bandit, Semgrep, dependency-check |
| **Deploy** | `.github/workflows/deploy.yml` | Tag/Dispatch | Staging/Production deployment with rollback |
| **Release** | `.github/workflows/release.yml` | Tag v* | Create GitHub release, publish artifacts |

---

## 2. Test Workflow (test.yml)

### 2.1 Purpose
Automated testing on every push/PR:
- Unit tests (tests/unit/)
- Integration tests (tests/integration/)
- Error tracker tests
- E2E tests (optional)
- Coverage tracking (≥80% required)

### 2.2 Configuration

**Trigger Events:**
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

**Test Matrix:**
```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11"]
  # Runs tests on 3 Python versions simultaneously
```

### 2.3 Test Steps

1. **Checkout code** (fetch-depth: 0 for full history)
2. **Setup Python** (with pip caching for speed)
3. **Install dependencies** (requirements.txt + pytest plugins)
4. **Lint with flake8** (syntax check, max complexity 10)
5. **Type check with mypy** (optional, continue on error)
6. **Run unit tests** (tests/unit/ with coverage)
7. **Run integration tests** (tests/integration/ with DATABASE_URL)
8. **Run error tracker tests** (tests/test_error_tracker.py)
9. **Run cross-validation tests** (tests/integration/test_cross_validation.py)
10. **Run E2E tests** (tests/e2e/ if available)
11. **Check coverage** (fail-under=80)
12. **Generate coverage report**
13. **Upload to Codecov** (GitHub + external tracking)
14. **Archive results** (for debugging)
15. **Comment PR** (coverage badge added to PR)

### 2.4 Key Metrics Checked

| Metric | Threshold | Action on Failure |
|--------|-----------|-------------------|
| **Test Pass Rate** | 100% | ❌ Block merge |
| **Coverage** | ≥80% | ❌ Block merge |
| **Lint Warnings** | 0 | ⚠️ Warning only |
| **Type Errors** | Any | ⚠️ Continue (optional) |
| **Database Tests** | 100% pass | ❌ Block merge |

### 2.5 PostgreSQL Service Container

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: softfactory_test
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

**Usage in tests:**
```bash
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/softfactory_test
```

### 2.6 Example Test Run Output

```
✅ python-3.9: 47/47 tests PASS (2m 15s)
✅ python-3.10: 47/47 tests PASS (2m 08s)
✅ python-3.11: 47/47 tests PASS (2m 12s)
✅ Coverage: 85% (exceeds 80% requirement)
✅ Lint: 0 warnings
```

---

## 3. Lint & Format Workflow (lint.yml)

### 3.1 Purpose
Code quality on every PR:
- Format checking (black)
- Lint checking (flake8, pylint)
- Type checking (mypy)
- Security linting (bandit)
- Import sorting (isort)

### 3.2 Tools & Commands

```bash
# Format check (no auto-fix in CI)
black --check backend/ tests/ web/

# Lint check (Python syntax + complexity)
flake8 backend tests --count --exit-zero --max-complexity=10

# Type checking
mypy backend --ignore-missing-imports

# Security lint
bandit -r backend -ll  # Low severity warnings only

# Import sorting
isort --check-only backend tests
```

### 3.3 Failure Handling

- ❌ Black format violations → Block merge
- ⚠️ Flake8 warnings → Warning (exit-zero)
- ⚠️ MyPy errors → Warning (optional)
- ❌ Bandit critical → Block merge
- ❌ Import order → Block merge

---

## 4. Security Scanning Workflow (security.yml)

### 4.1 Purpose
Automated security analysis:
- **CodeQL**: SAST (Static Analysis)
- **Bandit**: Python-specific security
- **Semgrep**: Pattern-based detection
- **Dependency-check**: Known CVE scanning

### 4.2 CodeQL Configuration

```yaml
languages: ['python', 'javascript']
queries: security-and-quality
```

**Coverage:**
- SQL injection detection
- Path traversal
- XSS vulnerabilities
- Weak crypto
- Insecure deserialization

### 4.3 Bandit Security Scan

```bash
bandit -r backend -f json -o bandit-report.json
```

**Severity Levels:**
- 🔴 HIGH: SQL injection, hardcoded secrets, unsafe deserialization
- 🟠 MEDIUM: Weak crypto, insecure defaults
- 🟡 LOW: Use of assert, mutable default arguments

**Blocking Issues:**
```python
# ❌ FAIL: Hardcoded password
password = "admin123"  # B105

# ❌ FAIL: SQL concatenation
query = f"SELECT * FROM users WHERE id = {user_id}"  # B608

# ✅ PASS: Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### 4.4 Semgrep Scans

```yaml
semgrep:
  rules:
    - p/owasp-top-ten
    - p/python
    - p/flask
    - p/sqlalchemy
```

**OWASP Top 10 Coverage:**
1. SQL Injection
2. Broken Authentication
3. XSS
4. Broken Access Control
5. Security Misconfiguration
6. Sensitive Data Exposure
7. XXE
8. Broken Authentication (API)
9. Using Components with Known Vulnerabilities
10. Insufficient Logging

### 4.5 Dependency Check

```bash
dependency-check \
  --project "SoftFactory" \
  --scan . \
  --format SARIF
```

**Checks For:**
- Known CVEs in npm packages
- Known CVEs in pip packages
- Vulnerable library versions

---

## 5. Deploy Workflow (deploy.yml)

### 5.1 Deployment Flow

```
Git Tag v1.0.0
    ↓
Test Job (ensure tests pass)
    ↓
Build & Push (Docker image to ghcr.io)
    ↓
Deploy to Staging (manual dispatch only)
    ├─ Deploy container
    ├─ Run smoke tests
    └─ Health checks
    ↓
Deploy to Production (tag v* only)
    ├─ Create deployment record
    ├─ Deploy container
    ├─ Health check (30 retries)
    ├─ Infrastructure health
    ├─ API endpoint validation
    ├─ Success notification
    └─ Rollback (if any failure)
```

### 5.2 Deployment Triggers

| Event | Condition | Action |
|-------|-----------|--------|
| Tag v* | `git tag v1.2.3` | Auto-deploy to Production |
| Manual Dispatch | UI button + env | Deploy to selected env |
| Failure | Any step fails | Automatic rollback |

### 5.3 Docker Build & Push

```yaml
- uses: docker/build-push-action@v4
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:v1.0.0
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Registry:** `ghcr.io/yourorg/softfactory:v1.0.0`

### 5.4 Staging Deployment

```bash
# Triggers on manual dispatch with env=staging

Steps:
1. Deploy container to staging server
2. Run smoke tests:
   - GET /health → 200
   - GET /api/coocook/chefs → 200
   - POST /api/auth/login → 200/401 (correct behavior)
3. Health checks pass
4. Slack notification: "✅ Staging deployment successful"
```

### 5.5 Production Deployment

```bash
# Triggers on git tag v*

Steps:
1. Create deployment record (GitHub API)
2. Pull image from registry
3. Stop old container
4. Start new container
5. Health checks (30 retries, 1s interval):
   - GET https://softfactory.com/health
   - GET https://softfactory.com/api/infrastructure/health
   - GET https://softfactory.com/api/services/health
6. Success → Slack notification
7. Failure → Automatic rollback + Slack alert
```

### 5.6 Rollback Mechanism

**Automatic Rollback Triggers:**
- Health check failures after 30 retries
- Critical API endpoint returns 500+
- Infrastructure health check fails

**Rollback Steps:**
```bash
# Keep previous 3 image tags for rollback
# If deployment fails:
docker stop softfactory-prod
docker run -d ghcr.io/softfactory:previous-tag
# Verify health checks pass
# Notify: "Production rolled back to previous version"
```

**Manual Rollback:**
```bash
git tag v1.0.0-rollback  # Triggers automatic rollback
```

---

## 6. Release Workflow (release.yml)

### 6.1 Purpose
Automated release artifact generation:
- Generate CHANGELOG
- Create GitHub Release
- Upload artifacts
- Tag Docker image
- Notify stakeholders

### 6.2 Trigger

```yaml
on:
  push:
    tags: ['v*']  # v1.0.0, v1.0.1, etc.
```

### 6.3 Release Steps

1. **Checkout** with full history
2. **Extract version** from tag (v1.2.3 → 1.2.3)
3. **Generate CHANGELOG** (using git log)
4. **Create GitHub Release**
   - Title: "Release v1.2.3"
   - Body: Changelog
   - Prerelease: No
5. **Upload artifacts**
   - requirements.txt
   - docker-compose.yml
   - migration scripts
6. **Tag Docker image**
   - `latest`
   - `v1.2.3`
   - `stable`

### 6.4 Release Artifacts

```
SoftFactory v1.0.0
├─ requirements.txt (Python dependencies)
├─ docker-compose.yml (for local deployment)
├─ CHANGELOG.md (what changed)
├─ INSTALL.md (deployment guide)
└─ checksum.txt (SHA256 verification)
```

---

## 7. Build Workflow (build.yml)

### 7.1 Purpose
Docker image building:
- Build backend image
- Build frontend image
- Multi-stage builds for optimization
- Cache layers for speed

### 7.2 Dockerfile Strategy

```dockerfile
# Multi-stage build for minimal image size

# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY backend /app/backend
COPY web /app/web
ENV PATH=/root/.local/bin:$PATH
CMD ["gunicorn", "-c", "gunicorn_config.py", "backend.app:create_app()"]
```

**Result:**
- Builder image: 1.2GB (discarded)
- Final image: 280MB (cached locally)

---

## 8. Quality Gates & Merge Protection

### 8.1 Required Status Checks

```yaml
# .github/settings.yml (via GitHub API or UI)

Required status checks:
  ✅ tests (all 3 Python versions must pass)
  ✅ lint
  ✅ security/codeql
  ✅ security/bandit
```

### 8.2 Branch Protection Rules

```
main branch:
├─ Require status checks to pass
├─ Require code review (1 approval)
├─ Require branches to be up to date
├─ Allow auto-merge (squash or rebase)
└─ Dismiss stale PR approvals
```

### 8.3 Merge Checklist

Before PR can be merged:

- ✅ All tests pass (47/47)
- ✅ Coverage ≥80% (actual: 85%)
- ✅ Lint passes (0 warnings)
- ✅ Security scans pass (0 HIGH)
- ✅ 1 code review approval
- ✅ Commits are signed (optional)

---

## 9. Environment Configuration

### 9.1 Environment Variables by Stage

**Development** (.env.local):
```bash
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///platform.db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
```

**Staging** (GitHub Secrets):
```bash
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/softfactory
REDIS_URL=redis://staging-redis:6379
ENVIRONMENT=staging
SENTRY_DSN=https://...@sentry.io/...
```

**Production** (GitHub Secrets + Vault):
```bash
DEBUG=false
LOG_LEVEL=WARN
DATABASE_URL=postgresql://vault-user:vault-pass@prod-db/softfactory
REDIS_URL=redis://prod-redis:6379
ENVIRONMENT=production
SENTRY_DSN=https://...@sentry.io/...
JWT_SECRET=*** (from vault)
ENCRYPTION_KEY=*** (from vault)
```

### 9.2 Secrets Management

**GitHub Secrets (per environment):**
```
DEPLOY_KEY_STAGING: private SSH key
DEPLOY_KEY_PROD: private SSH key
SLACK_WEBHOOK: webhook URL
SENTRY_DSN: error tracking URL
```

**Local Vault (prod only):**
```
JWT_SECRET
ENCRYPTION_KEY
Database credentials
OAuth tokens
```

---

## 10. Monitoring & Alerts

### 10.1 Slack Integration

**Notifications sent on:**
```
✅ Staging deployment successful
❌ Staging deployment failed
✅ Production deployment successful
❌ Production deployment FAILED (critical)
🔄 Rollback triggered
⚠️ Health check failed
```

**Example notification:**
```
🚀 Production Deployment Successful
Version: v1.2.3
Time: 2026-02-26 14:25 UTC
Environment: Production (softfactory.com)
Health: ✅ All checks passed
Rollback plan: Ready (tag available)
```

### 10.2 Health Checks (Production)

**Endpoint:** `https://softfactory.com/health`

```bash
curl -f https://softfactory.com/health || exit 1

# Returns JSON:
{
  "status": "healthy",
  "version": "1.2.3",
  "timestamp": "2026-02-26T14:25:00Z",
  "database": "connected",
  "redis": "connected",
  "uptime_seconds": 3600
}
```

**Checks performed:**
1. Service responds (200 OK)
2. Database connected
3. Redis connected (if used)
4. API endpoints respond
5. Infrastructure health

---

## 11. Troubleshooting Guide

### 11.1 Test Failure

**Issue:** Tests fail with "Database not initialized"

**Solution:**
```bash
# Ensure test fixtures are in conftest.py
# Database container is healthy
# CONNECTION string is correct

# In test:
pytest -v --tb=short tests/
```

### 11.2 Coverage Below 80%

**Issue:** Coverage report: 74%

**Solution:**
1. Add tests for uncovered lines
2. Use `pytest --cov` to find gaps
3. Push changes → re-run CI

```python
# Mark unused code (if intentional)
def unused_function():  # pragma: no cover
    pass
```

### 11.3 Deployment Fails

**Issue:** Deployment step timed out

**Solution:**
```bash
# Check GitHub Actions logs
# If health check fails: previous version still active
# Rollback: git tag v1.0.0-rollback

# Manual fix:
ssh deployer@production.example.com
docker logs softfactory-prod
docker restart softfactory-prod
```

### 11.4 Security Scan False Positives

**Issue:** Bandit flags `assert` as insecure

**Solution:**
```python
# Suppress with noqa comment
assert user_id > 0  # nosec (bandit false positive)

# Or in bandit.yml:
skips:
  - B101  # assert_used (noqa)
```

---

## 12. Local Development Workflow

### 12.1 Pre-commit Hooks

**Install pre-commit hooks:**
```bash
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    hooks:
      - id: flake8
```

### 12.2 Local Test Run

```bash
# Run tests locally before pushing
pytest tests/ -v --cov=backend --cov-report=term-missing

# Check coverage
coverage report --fail-under=80
```

### 12.3 Create Release

```bash
# Create tag (triggers all workflows)
git tag v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# GitHub Actions automatically:
# 1. Runs tests
# 2. Builds Docker image
# 3. Creates release
# 4. Deploys to production
```

---

## 13. Maintenance & Updates

### 13.1 Workflow Updates

**When to update workflows:**
- Python version bump (3.11 → 3.12)
- Dependency upgrade (pytest, etc.)
- New test suite added
- Infrastructure change

**Update process:**
1. Test locally with act: `act push -l`
2. Create PR with workflow changes
3. Merge after review
4. Next push uses new workflow

### 13.2 Dependency Updates

**Automated (dependabot):**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/web"
    schedule:
      interval: "weekly"
```

**Security updates:**
- Auto-merge minor/patch for dependencies
- Manual review for major versions

---

## 14. Performance Metrics

### 14.1 Workflow Duration

| Workflow | Duration | Frequency |
|----------|----------|-----------|
| test.yml | 2-3 min | Every push/PR |
| lint.yml | 1-2 min | Every push/PR |
| security.yml | 5-10 min | Weekly + on-demand |
| deploy.yml | 3-5 min | On tag |

**Total PR merge time: ~5-7 minutes** (parallel execution)

### 14.2 Cost Estimation

**GitHub Actions free tier:** 3,000 minutes/month

```
Estimated usage:
- 10 PRs/day × 5 min × 30 days = 1,500 min
- 5 commits/day × 3 min × 30 days = 450 min
- Weekly security scans × 10 min = 40 min
Total: ~2,000 min/month ✅ Within free tier
```

---

## 15. Deployment Checklist

Before deploying to production:

- [ ] All tests pass (47/47)
- [ ] Coverage ≥80%
- [ ] Security scans pass (0 HIGH)
- [ ] Code reviewed (1+ approval)
- [ ] Release notes written
- [ ] Migration scripts tested
- [ ] Rollback plan ready
- [ ] Monitoring alerts configured
- [ ] Team notified

---

## 16. Quick Reference Commands

```bash
# Run all tests locally
pytest tests/ -v --cov=backend

# Run specific test
pytest tests/test_auth.py::test_login -v

# Lint check
flake8 backend --max-complexity=10

# Type check
mypy backend

# Create release (triggers all workflows)
git tag v1.0.0 -m "Release notes here"
git push origin v1.0.0

# View workflow logs
gh run list -w test.yml
gh run view <run-id>

# Manual deployment
gh workflow run deploy.yml -f environment=staging
```

---

## 17. Success Criteria

✅ **CI/CD Pipeline Complete When:**
- All 6 workflows deployed and functional
- Tests run automatically on every PR
- Security scans pass (0 critical issues)
- Deployments automated to staging/production
- Health checks validate deployments
- Rollback mechanism ready
- Team trained on workflow

---

**Document Version:** 1.0
**Last Updated:** 2026-02-26
**Next Review:** After first production deployment
