# 📘 Docker + PostgreSQL Quick Start Guide

> **Purpose**: **For:** M-002 Phase 4 PostgreSQL Migration
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Docker + PostgreSQL Quick Start Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**For:** M-002 Phase 4 PostgreSQL Migration
**Time:** 15-30 minutes
**Difficulty:** Beginner-friendly

---

## 🚀 TL;DR (If You're in a Hurry)

**Prerequisites Met?** ✅ Yes
- Docker 29.2.1 installed ✅
- docker-compose installed ✅
- Python 3.11.8 ✅
- psycopg2-binary installed ✅
- platform.db exists (92K) ✅

**Steps:**
```bash
# 1. Start Docker Desktop (GUI or command)
# 2. Run in bash/PowerShell:
cd D:/Project
docker-compose up -d db
sleep 10
python scripts/migrate_to_postgres.py
docker-compose up -d
curl http://localhost:8000/health
```

**Done!** Your API now uses PostgreSQL.

---

## Step 1: Start Docker Desktop

### Windows Easiest Way:
1. Press `Win` key
2. Type `Docker`
3. Click "Docker Desktop"
4. Wait for taskbar icon to stabilize (~60 seconds)
5. Verify with:
   ```bash
   docker ps
   ```

---

## Step 2: Start PostgreSQL Container

```bash
cd D:/Project
docker-compose up -d db
```

Wait for this output:
```
Creating project_db_1 ... done
```

Verify it's running:
```bash
docker ps | grep postgres
```

---

## Step 3: Run Migration Script

```bash
python scripts/migrate_to_postgres.py
```

Expected:
```
🔄 Starting SQLite → PostgreSQL migration...
Found 12 tables: [users, products, ...]
  → Migrating users...
  → Migrating products...
  ... (all tables)
✅ Migration complete!
```

---

## Step 4: Start Full Stack

```bash
docker-compose up -d
```

Wait 10 seconds, then verify:
```bash
docker ps
# Should show 2 containers: web + db
```

---

## Step 5: Test It Works

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

Or visit: `http://localhost:8000` in your browser

---

## Troubleshooting in 30 Seconds

| Error | Fix |
|-------|-----|
| `Cannot connect to Docker daemon` | Docker Desktop not running. Start it (Step 1). |
| `Port 5432 already in use` | Another PostgreSQL is running. Run: `docker-compose down` |
| `psycopg2 not found` | Run: `pip install psycopg2-binary` |
| `Connection refused` | PostgreSQL still initializing. Wait 15 seconds, retry. |
| `Migration failed` | Check: `docker logs project_db_1` |

---

## Stop Everything (When Done)

```bash
docker-compose down
```

Data persists in PostgreSQL volume. To fully cleanup:
```bash
docker-compose down -v  # -v = remove volumes too
```

---

## View Logs (Debugging)

```bash
# Follow Flask logs:
docker-compose logs -f web

# PostgreSQL logs:
docker-compose logs -f db

# All logs:
docker-compose logs -f
```

---

## That's It!

Your Flask app is now connected to PostgreSQL in Docker.

For detailed info, see: `DEPLOYMENT_CHECKLIST.md`