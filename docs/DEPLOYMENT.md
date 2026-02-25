# DEPLOYMENT GUIDE

**Version:** 2.0 | **Date:** 2026-02-25 | **Status:** PRODUCTION

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server (port 8000)
python -m backend.app

# Access platform
http://localhost:8000/web/
```

## Services Deployed

| Service | Port | Status | Technology |
|---------|------|--------|-----------|
| Flask API | 8000 | ACTIVE | Python 3.11 + Flask |
| SQLite DB | — | ACTIVE | platform.db (absolute path) |
| Sonolbot | Telegram | ACTIVE | Python daemon + Claude |

## Configuration

### Database
- **File:** `D:/Project/platform.db`
- **Type:** SQLite3
- **Models:** 12 (User, Task, Project, Service, etc.)
- **Init:** Auto-run on app start via `init_db(app)`

### Authentication
- **Method:** JWT tokens
- **Duration:** 30 days
- **Demo:** passkey=demo2026, token=demo_token

### CORS
- **Allowed Origins:** localhost:5000, localhost:8000, null
- **Methods:** GET, POST, PUT, DELETE, OPTIONS

## Health Checks

**Dashboard:** `http://localhost:8000/web/infrastructure/monitor.html`

**API Endpoints:**
```bash
# System health
curl http://localhost:8000/api/infrastructure/health

# Process list
curl http://localhost:8000/api/infrastructure/processes
```

## Monitoring

**Cost Log:** `shared-intelligence/cost-log.md`
- Token usage tracked per session
- Flag threshold: 50,000 tokens
- Monthly summary auto-calculated

**Error Handling:**
- All errors logged to stderr
- Critical issues escalated to orchestrator
- Zero silent failures policy

## Rollback Procedure

1. Stop Flask: `Ctrl+C`
2. Restore backup: `cp platform.db.backup platform.db`
3. Restart: `python -m backend.app`

## Performance Targets

- API response: <500ms
- Token per task: <50,000 (flag if exceeded)
- Monthly cost: <$5 USD (flag if exceeded)

**Production Ready:** Yes ✓
