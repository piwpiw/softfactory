# 📘 M-006 Experience Platform — Quick Start Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 M-006 Experience Platform — Quick Start Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## In 60 Seconds

### 1. Start the Server
```bash
cd D:\Project
python start_platform.py
```

### 2. Open Dashboard
```
http://localhost:8000/web/experience/index.html
```

### 3. Test API
```bash
curl http://localhost:8000/api/experience/listings
curl http://localhost:8000/api/experience/stats
```

Done! You have 8 experience listings across 4 Korean platforms.

---

## What You Got (MVP)

| Component | Status | Location |
|-----------|--------|----------|
| Backend API | Working | `backend/services/experience.py` |
| Database Models | Ready | `backend/models.py` |
| Frontend Dashboard | Live | `web/experience/index.html` |
| Crawler Framework | Ready | `scripts/crawlers/` |
| Documentation | Complete | `web/experience/README.md` |

---

## Features

- **8 Sample Listings** from 4 Korean platforms
- **Real-time Filtering** by site and category
- **Responsive Design** (works on mobile, tablet, desktop)
- **Auto-Refresh** every 5 minutes
- **Deadline Alerts** for urgent opportunities
- **6 API Endpoints** for data access

---

## API Endpoints

### Get Listings
```bash
GET http://localhost:8000/api/experience/listings?site=coupang_eats&category=음식
```

### Get Stats
```bash
GET http://localhost:8000/api/experience/stats
```

### Trigger Crawl
```bash
curl -X POST http://localhost:8000/api/experience/crawl
```

Full API docs in `/web/experience/README.md`

---

## What's Next (Phase 5)

- [ ] Real web crawlers with BeautifulSoup
- [ ] Database persistence (SQLite → PostgreSQL)
- [ ] Automated scheduling (hourly crawls)
- [ ] User accounts + saved listings

---

## Troubleshooting

**Q: Dashboard shows no listings?**
- Check if Flask is running: `python start_platform.py`
- Open browser console (F12) to see errors
- Try refreshing the page

**Q: API returns 404?**
- Make sure server is running on port 8000
- Check URL format: `http://localhost:8000/api/experience/...`

**Q: Crawl button not working?**
- Check Flask logs for errors
- Currently returns dummy data (Phase 5 will add real crawlers)

---

## Files Created

```
backend/
  services/experience.py         157 lines - Main API service
  models.py                      +50 lines - Database models

web/experience/
  index.html                     15 KB - Responsive dashboard
  README.md                      10 KB - Full documentation

scripts/crawlers/
  crawler_base.py               Abstract base class
  coupang_eats_crawler.py       Sample crawler
  danggeun_crawler.py           Sample crawler
  soomgo_crawler.py             Sample crawler
```

---

## Project Info

- **Code:** M-006
- **Title:** Korean Experience Platform Integration
- **Started:** 2026-02-25
- **Status:** MVP Phase 2 Complete → Ready for QA (Phase 3)
- **Team:** Multi-Agent System

---

For detailed documentation, see `/web/experience/README.md`