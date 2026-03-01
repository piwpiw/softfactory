# 📘 M-002 Phase 4 Execution Guide: PostgreSQL Docker Migration

> **Purpose**: **Status:** READY TO EXECUTE
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 M-002 Phase 4 Execution Guide: PostgreSQL Docker Migration 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Status:** READY TO EXECUTE
**Date:** 2026-02-25
**Phase:** 4 - Database Migration & Containerization
**Execution Time:** 15-30 minutes

---

## Quick Reference

### Prerequisites Status
All prerequisites are **VERIFIED** ✅

```
[PASS] Docker (29.2.1)
[PASS] docker-compose
[PASS] Python (3.11.8)
[PASS] docker-compose.yml
[PASS] Dockerfile
[PASS] migration script
[PASS] .env file
[PASS] Flask app
[PASS] SQLite DB (92K)
[PASS] psycopg2-binary
[PASS] Flask (6.0.2)
[PASS] SQLAlchemy
```

### One-Liner (If Comfortable)
```bash
# NOT YET - requires Docker Desktop to be running first!
# See "Step 1" below
```

---

## Step 1: Start Docker Desktop (CRITICAL FIRST STEP)

Docker Desktop must be running before any docker commands will work.

### Windows GUI Method (Easiest - Recommended)
1. Open Windows Start Menu (click Windows icon or press `Win`)
2. Type: `Docker`
3. Click: **Docker Desktop** application
4. Wait: ~60 seconds for startup (watch the taskbar icon)
5. Verify: Icon stabilizes (stops animating)

### Verify Docker is Running
Open PowerShell or bash and type:
```bash
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
(empty list - no containers running yet)
```

**If Error:**
```
Cannot connect to Docker daemon
```
→ Docker Desktop is still not running. Wait longer and retry.

---

## Step 2: Initialize PostgreSQL Container (2 minutes)

Once Docker Desktop is confirmed running, open bash/PowerShell and run:

```bash
cd D:/Project
docker-compose up -d db
```

**Expected Output:**
```
Creating project_default network with the default driver
Creating project_db_1 ... done
```

**Verify Container Started:**
```bash
docker ps | grep postgres
```

**Expected:** Should show a running container like:
```
1a2b3c4d5e6f  postgres:15-alpine  ... Up 10 seconds  5432/tcp  project_db_1
```

**Wait for PostgreSQL to Initialize:**
```bash
docker logs project_db_1
```

Look for line: `"database system is ready to accept connections"`

If you see this, PostgreSQL is ready. If not, wait 10 more seconds and check again.

---

## Step 3: Run Migration Script (5 minutes)

```bash
cd D:/Project
python scripts/migrate_to_postgres.py
```

**Expected Output:**
```
🔄 Starting SQLite → PostgreSQL migration...
Found 12 tables: [users, products, orders, reviews, ...]
  → Migrating users...
  → Migrating products...
  → Migrating orders...
  ... (12 tables total)
✅ Migration complete!
```

**If Error Occurs:**

### Error: `Connection refused on port 5432`
```bash
# PostgreSQL still initializing. Wait 15 seconds:
docker logs project_db_1
# Look for "ready to accept connections"
# Then retry the migration
```

### Error: `psycopg2 module not found`
```bash
pip install psycopg2-binary
# Then retry migration
```

### Error: `database is locked`
```bash
# Another process has platform.db open
# Make sure Flask/other tools are stopped
# Then retry migration
```

---

## Step 4: Verify Data Migration (2 minutes)

Check that data was copied correctly:

```bash
# Count rows in PostgreSQL (should match SQLite)
docker exec -it project_db_1 psql -U postgres -d softfactory -c "SELECT COUNT(*) as row_count FROM users;"
```

**Expected Output:**
```
 row_count
-----------
        15
(1 row)
```

Check all tables were migrated:
```bash
docker exec -it project_db_1 psql -U postgres -d softfactory -c "\dt"
```

**Expected Output:** List of ~12 tables

---

## Step 5: Start Full Stack (Flask + PostgreSQL) (2 minutes)

```bash
docker-compose up -d
```

**Expected Output:**
```
Creating project_web_1 ... done
project_db_1 is already running
```

**Verify Both Services Running:**
```bash
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                  STATUS           NAMES
...            postgres:15-alpine     Up 2 minutes     project_db_1
...            project_web:latest     Up 30 seconds    project_web_1
```

---

## Step 6: Test Everything Works (2 minutes)

### Test API Health Endpoint
```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status": "ok"}
```

### Visit Web UI
Open browser and go to: `http://localhost:8000`

Should load the SoftFactory platform homepage.

### Run Full Test Suite
```bash
pytest tests/ -v
```

**Expected Output:**
```
tests/integration/test_api_endpoints.py::test_get_health PASSED
tests/integration/test_api_endpoints.py::test_get_users PASSED
... (16/16 tests should PASS)
```

---

## Step 7: Update Environment (AFTER Successful Migration)

If migration was successful, update `.env` to use PostgreSQL by default:

### For Docker Containers (Production)
```bash
# In .env, change:
DATABASE_URL=postgresql://postgres:postgres@db:5432/softfactory
# (Note: 'db' is the Docker service name, works inside containers)
```

### For Local Testing (Without Docker)
```bash
# In .env, change:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/softfactory
# (Note: 'localhost' works on your machine, not in containers)
```

**Then Restart Flask:**
```bash
docker-compose restart web
# or if testing locally without Docker:
# python start_platform.py
```

---

## Troubleshooting Quick Lookup

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Cannot connect to Docker daemon` | Docker Desktop not running | Start Docker Desktop (Step 1) |
| `Port 5432 already in use` | Another PostgreSQL running | `docker-compose down` then `up -d` |
| `Connection refused` | PostgreSQL not fully initialized | Wait 15 seconds, check `docker logs project_db_1` |
| `psycopg2 not found` | Driver not installed | `pip install psycopg2-binary` |
| `Migration failed` | SQLite file locked or corrupted | Stop Flask, retry migration |
| `docker-compose command not found` | docker-compose not in PATH | Reinstall Docker Desktop |
| API returns 500 error | Flask can't connect to PostgreSQL | Check `.env` DATABASE_URL is correct |

---

## Verify Phase 4 Complete

Check all these boxes:

- [ ] Docker Desktop is running
- [ ] PostgreSQL container running: `docker ps | grep postgres`
- [ ] SQLite → PostgreSQL migration completed without errors
- [ ] Row count verified: `docker exec project_db_1 psql -U postgres -d softfactory -c "SELECT COUNT(*) FROM users"`
- [ ] Flask app running: `docker ps | grep web`
- [ ] API health check passes: `curl http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] Web UI loads in browser: `http://localhost:8000`
- [ ] All tests pass: `pytest tests/ -v` shows 16/16 PASSED
- [ ] `.env` updated with PostgreSQL connection string
- [ ] Documentation reviewed: `DEPLOYMENT_CHECKLIST.md`

---

## Rollback Plan (If Something Goes Wrong)

If you need to revert to SQLite:

```bash
# 1. Stop everything
docker-compose down

# 2. Reset .env to SQLite
# Edit .env and change:
# DATABASE_URL=sqlite:///D:/Project/platform.db

# 3. Run Flask with SQLite (no Docker)
python start_platform.py

# 4. Data is safe - platform.db was never modified
```

**Note:** Original SQLite database (`platform.db`) is untouched by the migration script. You can always go back.

---

## Next Steps After Phase 4

Once PostgreSQL migration is successful:

### Immediate (Same Day)
- [ ] Update team wiki/docs: "We now use PostgreSQL for CooCook"
- [ ] Monitor logs for 1 hour: `docker-compose logs -f`
- [ ] Spot-check 3-5 API endpoints manually

### Within 24 Hours
- [ ] Load test: 100+ concurrent users via `pytest`
- [ ] Backup PostgreSQL: `docker exec project_db_1 pg_dump -U postgres softfactory > backup_$(date +%Y%m%d).sql`
- [ ] Document any API changes
- [ ] Schedule QA sign-off meeting

### Before M-002 Final Release
- [ ] Set up automated daily backups
- [ ] Configure monitoring/alerts (CPU, memory, connections)
- [ ] Security audit: OWASP Top 10 check
- [ ] Disaster recovery test (backup restore)
- [ ] Load test with production dataset (10K+ rows)

---

## Success Criteria

| Item | Requirement | Verification |
|------|-------------|--------------|
| **PostgreSQL Up** | Running container | `docker ps \| grep postgres` |
| **Data Migrated** | All rows match SQLite | `SELECT COUNT(*)` comparison |
| **Flask Connected** | API responds | `curl http://localhost:8000/health` |
| **Tests Pass** | 16/16 passing | `pytest tests/ -v` |
| **Zero Errors** | No ERROR in logs | `docker-compose logs` (WARNINGs OK) |
| **Performance OK** | Response time < 500ms | `curl` timing or Postman |
| **Docs Complete** | All guides updated | `DEPLOYMENT_CHECKLIST.md` exists |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `DEPLOYMENT_CHECKLIST.md` | Complete 16-section guide with troubleshooting |
| `DOCKER_QUICK_START.md` | 5-minute quick reference |
| `M-002_PHASE4_SUMMARY.md` | Executive overview |
| `PHASE4_EXECUTION_GUIDE.md` | This file - step-by-step walkthrough |
| `docker-compose.yml` | Container configuration |
| `Dockerfile` | Flask app image definition |
| `scripts/migrate_to_postgres.py` | SQLite → PostgreSQL migration script |
| `shared-intelligence/decisions.md` | ADR-0010 (Docker decision) |
| `shared-intelligence/pitfalls.md` | PF-012 to PF-016 (Docker pitfalls) |

---

## Support

**Questions?** Refer to:
1. `DEPLOYMENT_CHECKLIST.md` Part 8 (Troubleshooting section)
2. `shared-intelligence/pitfalls.md` (common issues + fixes)
3. `docker logs project_db_1` or `docker logs project_web_1` (service logs)

**Report Issues:**
- Document exact command + error message
- Share relevant log output
- Verify Docker Desktop is actually running first

---

## Timeline

| Step | Time | Status |
|------|------|--------|
| Start Docker Desktop | 5 min | ⏳ NOW |
| Initialize PostgreSQL | +2 min | ⏳ NEXT |
| Run Migration | +5 min | ⏳ THEN |
| Start Full Stack | +2 min | ⏳ THEN |
| Verify & Test | +5 min | ⏳ FINALLY |
| **Total** | **~20 min** | 🎯 GOAL |

---

**Document Version:** 1.0
**Status:** READY FOR EXECUTION
**Last Updated:** 2026-02-25
**Next Phase:** M-002 Phase 5 (API Optimization)