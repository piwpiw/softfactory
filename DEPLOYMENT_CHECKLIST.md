# M-002 Phase 4: PostgreSQL Docker Deployment Checklist

**Status:** 🟡 READY TO DEPLOY (Docker Desktop offline)
**Phase:** 4 - Database Migration & Containerization
**Date:** 2026-02-25
**Target:** Production PostgreSQL + Docker deployment for CooCook API

---

## Part 1: Prerequisites Status

### System Requirements

| Requirement | Status | Details |
|-------------|--------|---------|
| **Docker** | ✅ INSTALLED | Version 29.2.1 |
| **docker-compose** | ✅ INSTALLED | Available at `/c/Program Files/Docker/Docker/resources/bin/docker-compose` |
| **Python** | ✅ INSTALLED | Version 3.11.8 |
| **PostgreSQL Driver** | ⚠️ VERIFY | Run: `pip install psycopg2-binary` |
| **Docker Desktop** | 🔴 **NOT RUNNING** | See Part 2 below |

### Project Files Status

| File | Status | Details |
|------|--------|---------|
| `docker-compose.yml` | ✅ READY | PostgreSQL 15-alpine configured |
| `Dockerfile` | ✅ READY | Flask app image with Python 3.11-slim |
| `scripts/migrate_to_postgres.py` | ✅ READY | SQLite → PostgreSQL migration script |
| `.env` | ✅ READY | DATABASE_URL configured for SQLite (dev) |
| `backend/app.py` | ✅ READY | Flask application with models |
| `backend/models.py` | ✅ READY | SQLAlchemy models defined |

### Environment Configuration

| Variable | Current Value | Status |
|----------|--------------|--------|
| `DATABASE_URL` | `sqlite:///D:/Project/platform.db` | ✅ DEV (will switch to PostgreSQL) |
| `FLASK_ENV` | development | ✅ |
| `ANTHROPIC_API_KEY` | Configured | ✅ |
| `TELEGRAM_BOT_TOKEN` | Configured | ✅ |

---

## Part 2: Start Docker Desktop (Step-by-Step)

### If Docker Desktop is NOT running (current state):

**Option A: GUI Method (Recommended)**
1. Open Windows Start Menu (or press `Win` key)
2. Type: `Docker Desktop`
3. Click the application to launch
4. Wait for the taskbar icon to appear and stop animating (~30-60 seconds)
5. Verify: Open PowerShell/bash and run:
   ```bash
   docker ps
   ```
   Expected output: `CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES`

**Option B: Command Line (PowerShell - Admin Required)**
```powershell
# Open PowerShell as Administrator, then:
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```
Then wait for daemon to start (check taskbar).

**Option C: WSL2 Backend Check**
If Docker Desktop uses WSL2 backend:
```bash
wsl --list --verbose
# Should show: Ubuntu or other distro with STATE: Running
```

### Verify Docker Daemon is Running
```bash
docker version
# Should show both client and server information
```

---

## Part 3: Initialize PostgreSQL Container

Once Docker Desktop is running, execute these commands in order:

### Step 1: Navigate to Project Root
```bash
cd D:/Project
```

### Step 2: Start PostgreSQL Service Only
```bash
docker-compose up -d db
# -d = detached (background)
# db = service name from docker-compose.yml
```

**Expected Output:**
```
Creating network "project_default" with the default driver
Creating project_db_1 ... done
```

### Step 3: Verify Container is Running
```bash
docker ps
# Should show: project_db_1 (postgres:15-alpine) in CONTAINER ID list
```

### Step 4: Wait for PostgreSQL to Initialize
```bash
docker logs project_db_1
# Look for: "database system is ready to accept connections"
# Wait 5-10 seconds after seeing this message
```

### Step 5: Verify Database Connection
```bash
docker exec -it project_db_1 psql -U postgres -c "SELECT version();"
# Should return PostgreSQL version info
```

**Expected Output:**
```
PostgreSQL 15.X on x86_64-...
```

---

## Part 4: Database Migration (Pre-Migration Checks)

### Before Running migrate_to_postgres.py

**Checklist:**
- [ ] Docker Desktop is running (verify with `docker ps`)
- [ ] PostgreSQL container is running (verify above)
- [ ] SQLite source database exists: `D:/Project/platform.db`
- [ ] Python dependencies installed:
  ```bash
  pip install psycopg2-binary
  ```

### Verify Source Data
```bash
sqlite3 D:/Project/platform.db ".tables"
# Should list tables: users, products, orders, etc.
```

### Set Environment Variable (Optional)
```bash
# Linux/Mac/WSL:
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/softfactory"

# Windows PowerShell:
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/softfactory"
```

---

## Part 5: Execute Migration Script

### Run Migration (One Command)
```bash
cd D:/Project
python scripts/migrate_to_postgres.py
```

**Expected Output:**
```
🔄 Starting SQLite → PostgreSQL migration...
Found 12 tables: [users, products, orders, ...]
  → Migrating users...
  → Migrating products...
  ... (12 tables total)
✅ Migration complete!
```

### Verify Migration Success
```bash
# Connect to PostgreSQL and verify data
docker exec -it project_db_1 psql -U postgres -d softfactory -c "SELECT COUNT(*) FROM users;"
# Should show row count: X rows

# Or check all tables:
docker exec -it project_db_1 psql -U postgres -d softfactory -c "\dt"
# Should list all migrated tables
```

---

## Part 6: Build & Start Full Stack

### Option A: Start Both Web + DB (Full Stack)
```bash
docker-compose up -d
# Both web and db services start
```

**Wait for:**
- PostgreSQL to be ready (~10 seconds)
- Flask app to initialize (~5 seconds)
- Both services should show as "running"

### Verify All Services
```bash
docker ps
# Should show:
# - project_db_1 (postgres:15-alpine)
# - project_web_1 (your-image-name)
```

### Test API Endpoint
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

### View Logs
```bash
# Web logs:
docker logs project_web_1

# Database logs:
docker logs project_db_1

# Follow logs (real-time):
docker logs -f project_web_1
```

---

## Part 7: Update Environment for Production

### .env Changes After Migration
```bash
# Change from:
DATABASE_URL=sqlite:///D:/Project/platform.db

# To:
DATABASE_URL=postgresql://postgres:postgres@db:5432/softfactory
# (Note: 'db' is the Docker service name, resolved within container network)
```

### For Local Testing (Before Container)
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/softfactory
```

### For Production Deployment
```bash
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
# Example with Cloud PostgreSQL:
DATABASE_URL=postgresql://admin:SecurePass123@coocook-prod.c.db.cloud.com:5432/coocook_prod
```

---

## Part 8: Troubleshooting

### Issue 1: Docker Desktop Won't Start
**Solution:**
- Ensure Virtualization is enabled in BIOS (check Windows Settings → Apps → Programs → Turn Windows features on or off → Hyper-V)
- Restart Windows
- If still failing, check Docker Desktop logs: `%AppData%\Docker\`

### Issue 2: PostgreSQL Container Fails to Start
**Symptoms:** `docker ps` shows no `project_db_1`
```bash
# Check error logs:
docker logs project_db_1
# Look for: permission denied, port conflict, volume mount errors

# Common fix - remove old volume:
docker volume rm project_postgres_data
docker-compose up -d db
```

### Issue 3: Migration Fails (psycopg2 error)
**Symptoms:** `ERROR: psycopg2 module not found`
```bash
pip install --upgrade psycopg2-binary
python scripts/migrate_to_postgres.py
```

### Issue 4: Connection Refused Error
**Symptoms:** `Could not connect to server: Connection refused`
```bash
# Verify PostgreSQL is ready:
docker logs project_db_1 | grep "ready to accept"
# Wait 10+ seconds before retrying migration
```

### Issue 5: SQLite Database Locked
**Symptoms:** `database is locked`
```bash
# Ensure no other processes are using platform.db:
lsof | grep platform.db  # Linux/Mac
# On Windows, close any other terminals using the DB
```

---

## Part 9: Cleanup & Rollback

### If Migration Fails, Rollback to SQLite
```bash
# Stop containers:
docker-compose down

# Reset DATABASE_URL in .env:
DATABASE_URL=sqlite:///D:/Project/platform.db

# Restart Flask with SQLite:
python start_platform.py
```

### Clean Docker Resources (if needed)
```bash
# Stop all containers:
docker-compose down

# Remove containers:
docker-compose rm

# Remove volume (⚠️ deletes PostgreSQL data):
docker volume rm project_postgres_data

# Clean all unused resources:
docker system prune -a --volumes
```

---

## Part 10: Next Steps After Successful Deployment

### Immediate (After Migration ✅)
- [ ] Verify all API endpoints work with PostgreSQL
- [ ] Run QA test suite: `pytest tests/`
- [ ] Check data integrity: Row counts match SQLite
- [ ] Monitor container logs for errors

### Within 24 Hours
- [ ] Performance test with sample load (100+ concurrent users)
- [ ] Backup PostgreSQL database
- [ ] Document any breaking changes to API
- [ ] Update internal wiki/runbooks

### Before Production (M-002 Final)
- [ ] Set up automated database backups
- [ ] Configure monitoring/alerts (CPU, memory, query performance)
- [ ] Load testing with production-like dataset
- [ ] Disaster recovery testing (backup restore)
- [ ] Security scan: OWASP checks on PostgreSQL schema

### Production Checklist (Final Gate)
- [ ] `docker push` image to Docker Hub/registry
- [ ] Update K8s/Swarm manifests (if applicable)
- [ ] Set up CI/CD to auto-deploy on git push
- [ ] Configure secrets management (AWS Secrets Manager, etc.)
- [ ] Run smoke tests post-deployment
- [ ] Notify stakeholders of PostgreSQL cutover

---

## Part 11: Quick Reference Commands

### Daily Operations
```bash
# Start all services:
docker-compose up -d

# Stop all services:
docker-compose down

# Restart services:
docker-compose restart

# View all logs:
docker-compose logs -f

# Access PostgreSQL shell:
docker exec -it project_db_1 psql -U postgres

# Backup database:
docker exec project_db_1 pg_dump -U postgres softfactory > backup_$(date +%Y%m%d).sql

# Run migrations (Flask-Migrate):
docker exec project_web_1 flask db upgrade
```

### Monitoring
```bash
# Container stats (CPU, memory):
docker stats

# Network inspection:
docker network inspect project_default

# Check service dependencies:
docker-compose ps
```

---

## Part 12: Success Criteria (Phase 4 Complete)

| Criterion | Status | Verification |
|-----------|--------|--------------|
| Docker Desktop Running | 🟡 PENDING | `docker ps` shows running containers |
| PostgreSQL Container Started | 🟡 PENDING | `docker logs project_db_1` shows "ready" |
| Database Connection Verified | 🟡 PENDING | `docker exec ... psql` succeeds |
| SQLite → PostgreSQL Migration Complete | 🟡 PENDING | Row counts match between DBs |
| Flask App Connected to PostgreSQL | 🟡 PENDING | `curl http://localhost:8000/health` returns 200 |
| All API Tests Passing | 🟡 PENDING | `pytest` output: 16/16 tests pass |
| Zero Critical Warnings | 🟡 PENDING | Docker logs show no ERROR lines |
| Documentation Complete | ✅ DONE | This file (DEPLOYMENT_CHECKLIST.md) |

---

## Summary

**Current Status:** Docker infrastructure ready, awaiting Docker Desktop start
**Time to Complete:** 15-30 minutes (after Docker Desktop starts)
**Risk Level:** LOW (non-destructive, can rollback to SQLite)
**Owner:** M-002 Phase 4 DevOps Lead

**Next Action:**
1. **START Docker Desktop** (Part 2 above)
2. **Initialize PostgreSQL:** `docker-compose up -d db`
3. **Run Migration:** `python scripts/migrate_to_postgres.py`
4. **Verify:** `docker-compose up -d` (full stack)
5. **Test:** API endpoints + QA suite

**Support:** Refer to Part 8 (Troubleshooting) if issues arise

---

**Document Version:** 1.0
**Last Updated:** 2026-02-25
**Next Review:** 2026-02-27 (after successful migration)
