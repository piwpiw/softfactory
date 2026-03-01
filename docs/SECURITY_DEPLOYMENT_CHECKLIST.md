# 🚢 Security Deployment Checklist — Phase 2 Complete

> **Purpose**: **Date:** 2026-02-25
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Security Deployment Checklist — Phase 2 Complete 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Date:** 2026-02-25
**Version:** v2.0 (Production Ready)
**Status:** ✅ ALL ITEMS COMPLETE

---

## Pre-Deployment Verification

### Code Quality
- [x] All 20+ security tests passing
- [x] No hardcoded credentials in code
- [x] No demo token references remaining
- [x] Password validation enforced at registration
- [x] Rate limiting decorator applied to auth endpoints
- [x] Account lockout mechanism integrated

### Security Implementation
- [x] Demo token authentication bypass removed (CVSS 9.8 ✅ FIXED)
- [x] Password policy enforced (CVSS 8.6 ✅ FIXED)
- [x] Rate limiting enabled (CVSS 7.5 ✅ FIXED)
- [x] Account lockout enabled (15-minute duration)
- [x] Security audit logging enabled
- [x] Sensitive fields sanitized from API responses

### Database Preparation
- [x] LoginAttempt table schema defined
- [x] User model extended with security fields
- [x] Indexes created for performance
- [x] Migration script ready (auto-runs on startup)
- [x] No data loss for existing users

### Testing Completion
- [x] PasswordValidator tests (6 tests)
- [x] Registration password validation tests (2 tests)
- [x] Demo token bypass tests (2 tests)
- [x] Rate limiting tests (2 tests)
- [x] Account lockout tests (3 tests)
- [x] Login attempt tracking tests (5 tests)
- [x] Security event logging tests (3 tests)
- [x] Subscription security tests (1 test)
- [x] Sensitive data removal tests (2 tests)
- [x] All tests passing: 20+ ✅

### Documentation
- [x] SECURITY_FIXES.md created (550+ lines)
- [x] SECURITY_IMPLEMENTATION_SUMMARY.md created
- [x] SECURITY_DEPLOYMENT_CHECKLIST.md created (this file)
- [x] Pitfalls documented (PF-041 to PF-046)
- [x] ADR decision recorded (ADR-0016)
- [x] API changes documented
- [x] Migration guide provided
- [x] Compliance matrix included

### Code Review
- [x] backend/auth.py reviewed and updated
- [x] backend/models.py reviewed and updated
- [x] backend/password_validator.py created and reviewed
- [x] backend/security_middleware.py created and reviewed
- [x] tests/test_security_fixes.py reviewed
- [x] No merge conflicts
- [x] All files properly formatted
- [x] Imports verified

---

## Deployment Steps (For Operations Team)

### Step 1: Backup Current Database
```bash
# Create backup before deployment
cp D:/Project/platform.db D:/Project/platform.db.backup.2026-02-25
echo "Backup created: $(date)"
```

### Step 2: Stop Current Application
```bash
# Stop Flask server
ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
echo "Flask stopped"

# Wait for graceful shutdown
sleep 5
```

### Step 3: Deploy New Code
```bash
cd D:/Project
git pull origin clean-main
# Verify commit: 4d7f4276
git log -1 --format="%H %s"
```

### Step 4: Initialize Database
```bash
cd D:/Project
python3 << 'PYTHON'
from backend.app import create_app
from backend.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully")

    # Verify tables exist
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    assert 'login_attempts' in tables, "LoginAttempt table not created"
    assert 'users' in tables, "Users table not found"
    print(f"✅ All tables present: {tables}")
PYTHON
```

### Step 5: Run Security Tests
```bash
cd D:/Project
pytest tests/test_security_fixes.py -v

# Expected: All 20+ tests should pass
# If any test fails, DO NOT PROCEED to production
```

### Step 6: Verify No Demo Token References
```bash
cd D:/Project
grep -r "demo_token" backend/ || echo "✅ No demo_token references found"
grep -r "if token ==" backend/auth.py || echo "✅ No hardcoded token checks found"
```

### Step 7: Start Application
```bash
cd D:/Project
python3 backend/app.py

# Verify startup
# Should see: "Running on http://0.0.0.0:8000"
# Look for any errors in logs
```

### Step 8: Smoke Tests
```bash
# Test 1: Demo token rejected
curl -s -H "Authorization: Bearer demo_token" \
  http://localhost:8000/api/auth/me | grep -q "Invalid or expired token"
[ $? -eq 0 ] && echo "✅ Demo token correctly rejected" || echo "❌ FAILED"

# Test 2: Weak password rejected
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","password":"weak"}' | grep -q "8 characters"
[ $? -eq 0 ] && echo "✅ Weak password correctly rejected" || echo "❌ FAILED"

# Test 3: Valid registration works
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","name":"Test","password":"SecurePass123!"}' | grep -q "access_token"
[ $? -eq 0 ] && echo "✅ Valid registration works" || echo "❌ FAILED"

# Test 4: Rate limiting (run 6 times, expect 429 on 6th)
for i in {1..6}; do
  response=$(curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' -w "%{http_code}")
  code=${response: -3}
  if [ "$i" -lt 6 ]; then
    echo "Attempt $i: HTTP $code"
  else
    [ "$code" = "429" ] && echo "✅ Rate limiting works" || echo "❌ FAILED (got $code, expected 429)"
  fi
done
```

### Step 9: Monitor Logs
```bash
# Check for any errors
tail -50 logs/security_audit.log
tail -50 logs/app.log

# Look for: LOGIN_SUCCESS, LOGIN_FAILED, USER_REGISTERED events
grep "SECURITY_EVENT" logs/security_audit.log | head -10
```

### Step 10: Verify Admin Access
```bash
# Login with admin credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@softfactory.com", "password": "admin123"}'

# Should return valid JWT token
```

---

## Post-Deployment Verification

### Within First Hour
- [ ] Monitor logs for errors
- [ ] Verify no locked users (shouldn't happen on day 1)
- [ ] Test new user registration with strong password
- [ ] Test admin login
- [ ] Verify audit logs being created

### Within First Day
- [ ] Check database size (LoginAttempt table should have ~10-50 rows)
- [ ] Monitor CPU/memory usage (should have minimal impact)
- [ ] Test API response times (should be same or faster)
- [ ] Review audit logs for any suspicious patterns
- [ ] Communicate changes to users if needed

### First Week
- [ ] Monitor for account lockouts (normal: 0-3 per day)
- [ ] Review failed login patterns for attacks
- [ ] Verify all users can still login with updated passwords
- [ ] Performance metrics show no degradation
- [ ] Zero security incidents reported

---

## Rollback Procedure (If Needed)

### If Tests Fail Before Production
```bash
git revert 4d7f4276
python3 -c "
from backend.app import create_app
from backend.models import db
app = create_app()
with app.app_context():
    db.create_all()
"
```

### If Issues Found in Production
```bash
# Disable rate limiting (temporary)
# In backend/auth.py, comment out: @require_rate_limit

# Disable password policy (temporary)
# In backend/auth.py, comment out password validation

# Disable account lockout (temporary)
# In backend/auth.py, comment out account lock checks

# DO NOT KEEP PRODUCTION WITHOUT THESE SECURITY FEATURES
# These are critical — re-enable immediately and fix underlying issue
```

### Full Rollback
```bash
# Stop app
ps aux | grep app.py | grep -v grep | awk '{print $2}' | xargs kill -9

# Restore backup
cp D:/Project/platform.db.backup.2026-02-25 D:/Project/platform.db

# Revert code
git revert 4d7f4276

# Restart
python3 backend/app.py
```

---

## Commit Hash & Version

**Commit:** `4d7f4276`
**Date:** 2026-02-25
**Branch:** clean-main
**Tag:** security-v2.0

```bash
# Verify deployment version
git log -1 --format="%H %ai %s"
# Should show: 4d7f4276 2026-02-25... Security Hardening Phase 2
```

---

## Configuration Reference

### Security Parameters (customizable)
```python
# backend/security_middleware.py

RATE_LIMIT_WINDOW = 60                    # seconds (1 minute)
MAX_ATTEMPTS_PER_WINDOW = 5               # failed attempts
ACCOUNT_LOCKOUT_THRESHOLD = 5             # failures before lockout
ACCOUNT_LOCKOUT_DURATION = 15             # minutes
```

### Password Policy (customizable)
```python
# backend/password_validator.py

MIN_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL = True
SPECIAL_CHARS = r'!@#$%^&*()_+-=[]{}|;:,.<>?'
```

---

## Monitoring & Alerting

### Metrics to Monitor
1. **Failed Login Rate**
   - Alert if > 100 failures/hour (possible brute force)
   - Action: Review IP patterns, consider IP-based rate limiting

2. **Account Lockouts**
   - Alert if > 20 lockouts/day
   - Action: Check for password reset issues or attacks

3. **New User Registration**
   - Track daily registration count
   - Alert if unusual patterns (sudden spike or drop)

4. **Security Audit Log Size**
   - Monitor disk usage for logs/security_audit.log
   - Setup log rotation: max 100MB, keep 30 days

### Queries for Monitoring
```bash
# Count failed logins in last hour
sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM login_attempts WHERE success=0 AND timestamp > datetime('now', '-1 hour');"

# Find accounts locked
sqlite3 D:/Project/platform.db "SELECT email, locked_until FROM users WHERE is_locked=1;"

# Count successful registrations today
sqlite3 D:/Project/platform.db "SELECT COUNT(*) FROM login_attempts WHERE event_type='USER_REGISTERED' AND DATE(timestamp)=DATE('now');"
```

---

## User Communication Template

### Optional: Email to Users (if needed)

**Subject:** Security Improvements to Your SoftFactory Account

Hello SoftFactory User,

We've just deployed enhanced security features to protect your account:

1. **Stronger Passwords:** New accounts and password changes now require stronger passwords (8+ characters, mixed case, numbers, special characters). This protects your account from brute force attacks.

2. **Failed Login Protection:** After 5 failed login attempts in a minute, your account will automatically lock for 15 minutes. This prevents attackers from guessing your password.

3. **Audit Logging:** All login attempts are now logged for your security.

**What You Need to Do:**
- If you have an old weak password, you'll be prompted to update it on next login
- If you see an "Account Locked" message, wait 15 minutes and try again
- All existing functionality remains unchanged — just more secure!

Questions? Contact: security@softfactory.com

---

## Sign-Off Sheet

**Deployment by:** [Name] [Date]
**Verified by:** [QA/Security] [Date]
**Approved by:** [Manager] [Date]

- [ ] All deployment steps completed
- [ ] All smoke tests passed
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Admin confirmed access working
- [ ] Security audit logs enabled
- [ ] Rollback procedure tested and documented

---

## Appendix: Quick Command Reference

```bash
# View commit
git show 4d7f4276

# View what changed
git diff HEAD~1 HEAD --stat

# Test password validator
python3 -c "
from backend.password_validator import PasswordValidator
valid, msg = PasswordValidator.validate('SecurePass123!')
print(f'Valid: {valid}, Message: {msg}')
"

# Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{\"email\":\"test@test.com\",\"password\":\"wrong\"}'
done

# Check security logs
tail logs/security_audit.log

# Database backup
cp D:/Project/platform.db D:/Project/platform.db.backup.$(date +%Y%m%d-%H%M%S)
```

---

**END OF DEPLOYMENT CHECKLIST**

For support: devops@softfactory.com
For security issues: security@softfactory.com