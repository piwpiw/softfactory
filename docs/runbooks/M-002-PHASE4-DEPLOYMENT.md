# 🚢 M-002: Phase 4 DevOps Deployment Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 M-002: Phase 4 DevOps Deployment Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **CooCook API → Production Ready**
> **Status**: Ready for 2026-03-01 deployment

---

## 🚀 Quick Start

### Step 1: Setup PostgreSQL
```bash
docker-compose up -d db
# Or use managed PostgreSQL (AWS RDS, Heroku, etc)
```

### Step 2: Migrate Data
```bash
python scripts/migrate_to_postgres.py
```

### Step 3: Deploy
```bash
docker-compose up -d web
# App runs on port 8000
```

---

## 📋 Deployment Checklist

- [ ] PostgreSQL setup (local or cloud)
- [ ] Run migration script
- [ ] Update DATABASE_URL environment variable
- [ ] Run tests: `pytest tests/`
- [ ] Build Docker image: `docker build -t softfactory:latest .`
- [ ] Deploy to staging
- [ ] Run production tests
- [ ] Deploy to production

---

## 🔒 Production Config

```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
JWT_SECRET=<secure-random-string>
ENCRYPTION_KEY=<secure-random-string>
STRIPE_API_KEY=<stripe-live-key>
```

---

## 📊 Monitoring

```bash
# Check logs
docker logs -f softfactory_web

# Health check
curl http://localhost:8000/api/health

# Test API
curl http://localhost:8000/api/chefs
```

---

## ✅ Success Criteria

- [ ] All 47 tests pass
- [ ] API response time < 500ms
- [ ] Database connection stable
- [ ] No critical security issues
- [ ] Monitoring active

---

**Ready for deployment on 2026-03-01** ✅