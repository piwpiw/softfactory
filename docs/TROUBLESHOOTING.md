# TROUBLESHOOTING GUIDE

**Version:** 1.0 | **Date:** 2026-02-25 | **Status:** PRODUCTION

## Common Issues & Solutions

### 1. Flask API Won't Start (Port 8000)

**Problem:** `Address already in use`

**Solution:**
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
python -m backend.app --port 8001
```

### 2. Database Connection Error

**Problem:** `sqlite:///D:/Project/platform.db not found`

**Solution:**
```bash
# Verify absolute path
python -c "import os; print(os.path.abspath('platform.db'))"

# Ensure DB file exists
touch D:/Project/platform.db

# Reinitialize
python -c "from backend.models import init_db; init_db()"
```

### 3. JWT Token Expired

**Problem:** `401 Unauthorized`

**Solution:**
```bash
# Generate new token via /api/auth/login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token in Authorization header
Authorization: Bearer <token>
```

### 4. CORS Error in Browser Console

**Problem:** `No 'Access-Control-Allow-Origin' header`

**Solution:**
- Verify CORS origins in `backend/app.py`
- Add requesting origin to allowed list
- Restart Flask server

### 5. Service Returns 500 Error

**Problem:** `Internal Server Error`

**Solution:**
```bash
# Check stderr logs
tail -f /tmp/flask.log

# Verify service blueprint import
python -c "from backend.services.coocook import coocook_bp; print('OK')"

# Test database models
python -c "from backend.models import User; print(User.query.first())"
```

### 6. Sonolbot Not Responding

**Problem:** Telegram bot offline

**Solution:**
```bash
# Check daemon status
ps aux | grep daemon_service.py

# Restart daemon
cd D:/Project/daemon
pythonw.exe daemon_control_panel.py

# Verify project_brain.md exists
cat daemon/project_brain.md
```

## Monitoring & Debugging

**Health Check Dashboard:**
```
http://localhost:8000/web/infrastructure/monitor.html
```

**API Health Endpoints:**
```bash
# System status
curl http://localhost:8000/api/infrastructure/health

# Process list
curl http://localhost:8000/api/infrastructure/processes
```

## Recovery Procedures

**Database Backup/Restore:**
```bash
# Backup
cp D:/Project/platform.db D:/Project/platform.db.backup

# Restore
cp D:/Project/platform.db.backup D:/Project/platform.db
```

**Reset to Clean State:**
```bash
# Delete database
rm D:/Project/platform.db

# Restart Flask (reinits with clean schema)
python -m backend.app
```

---

**Last Updated:** 2026-02-25
**Status:** PRODUCTION READY ✓
