# Field-Level Encryption — Quick Start Guide

## 5-Minute Setup

### 1. Generate Encryption Key (Once)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy output and add to `.env`:
```
ENCRYPTION_KEY=your-generated-key-here
```

### 2. Run Database Migrations
```bash
# Existing database with new tables
python -c "
from backend.app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
print('Database tables created')
"
```

### 3. Restart Flask App
```bash
python backend/app.py
```

## Common Tasks

### Create API Key via API
```bash
curl -X POST http://localhost:8000/api/encryption/keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key",
    "expires_in_days": 30,
    "scopes": "read:projects,write:sns"
  }'
```

Response includes `"key"` field — **SAVE THIS IMMEDIATELY** (only returned once).

### List Your API Keys
```bash
curl http://localhost:8000/api/encryption/keys \
  -H "Authorization: Bearer $TOKEN"
```

### Revoke API Key
```bash
curl -X DELETE http://localhost:8000/api/encryption/keys/1 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reason": "No longer needed"}'
```

### Get Audit Log
```bash
curl "http://localhost:8000/api/encryption/audit-logs?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

## Using in Code

### Encrypt/Decrypt Explicitly
```python
from backend.encryption_service import encryption_service

# Encrypt
secret = "sensitive_data"
encrypted = encryption_service.encrypt_field(secret)
# Result: "gAAAAABmAb2J4..."

# Decrypt
decrypted = encryption_service.decrypt_field(encrypted)
# Result: "sensitive_data"
```

### Automatic Encryption in Models
```python
from backend.models import db
from backend.types import EncryptedString

class User(db.Model):
    # This field auto-encrypts on save, auto-decrypts on read
    phone_number = db.Column(EncryptedString(20))

# Usage
user = User(phone_number="+82-10-1234-5678")
db.session.add(user)
db.session.commit()

# When retrieved, automatically decrypted
print(user.phone_number)  # "+82-10-1234-5678"
```

### API Key Management in Code
```python
from backend.models import APIKey
from backend.encryption_service import encryption_service
from datetime import datetime, timedelta

# Create
api_key = APIKey(
    user_id=user.id,
    name="Integration",
    prefix="pk_integr123",
    encrypted_key=encryption_service.encrypt_field(generated_key),
    expires_at=datetime.utcnow() + timedelta(days=30),
    scopes="read:projects,write:sns"
)
db.session.add(api_key)
db.session.commit()

# Check validity
if api_key.is_valid():
    print("Key is active and not expired")

# Revoke
api_key.is_active = False
api_key.revoked_at = datetime.utcnow()
db.session.commit()
```

## Key Rotation (Quarterly)

### Step 1: Prepare
```bash
# Generate new key
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
OLD_KEY=$(grep ENCRYPTION_KEY .env | cut -d= -f2)
```

### Step 2: Test (Dry Run)
```bash
python scripts/rotate_encryption_key.py "$OLD_KEY" "$NEW_KEY" --dry-run
```

### Step 3: Execute
```bash
python scripts/rotate_encryption_key.py "$OLD_KEY" "$NEW_KEY"
```

### Step 4: Update & Restart
```bash
# Update .env
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$NEW_KEY/" .env

# Restart app
systemctl restart softfactory  # or your process manager
```

## Models Quick Reference

### APIKey Fields
```python
APIKey(
    id=1,
    user_id=1,
    name="Production Key",      # User-friendly name
    prefix="pk_abc123",         # Unique identifier
    encrypted_key="...",        # Encrypted Fernet token
    created_at="2026-02-26",
    last_used_at="2026-02-26",
    expires_at="2026-03-28",    # Auto-expire after period
    is_active=True,             # Soft delete
    scopes="read:*,write:sns",  # Permission string
    revoked_at=None,
    revocation_reason=None
)
```

### AuditLog Fields
```python
AuditLog(
    id=1,
    user_id=1,
    action="api_key_created",   # What happened
    resource_type="api_key",    # Type of resource
    resource_id=1,              # ID of affected resource
    ip_address="192.168.1.1",
    user_agent="Mozilla/...",
    status="success",           # or 'failure'
    details="...",              # Description
    timestamp="2026-02-26T10:00:00"
)
```

### EncryptionKeyRotation Fields
```python
EncryptionKeyRotation(
    id=1,
    old_key_version="v1",
    new_key_version="v2",
    timestamp="2026-02-26T10:00:00",
    initiated_by_user_id=1,
    rotation_status="completed",    # pending/in_progress/completed/failed
    total_records=100,
    rotated_records=100,
    failed_records=0,
    notes="Quarterly rotation",
    error_details=None
)
```

## Troubleshooting

### Issue: "Invalid Fernet key"
```bash
# Regenerate
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Update .env and restart
```

### Issue: "Failed to decrypt field"
```bash
# 1. Check ENCRYPTION_KEY matches original
# 2. Check data wasn't corrupted
# 3. Check database backup from before rotation
```

### Issue: Key creation fails
```bash
# Check encryption service initialized
python -c "from backend.encryption_service import encryption_service; print('OK')"

# Check ENCRYPTION_KEY is set in .env
grep ENCRYPTION_KEY .env
```

## API Endpoints Summary

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/encryption/keys` | Create API key | ✅ |
| GET | `/api/encryption/keys` | List API keys | ✅ |
| DELETE | `/api/encryption/keys/<id>` | Revoke key | ✅ |
| GET | `/api/encryption/audit-logs` | Get audit trail | ✅ |
| POST | `/api/encryption/rotate` | Initiate rotation | 🔐 Admin |
| GET | `/api/encryption/rotation-status/<id>` | Check progress | 🔐 Admin |

## Files

| File | Purpose |
|------|---------|
| `backend/encryption_service.py` | Core encryption logic |
| `backend/types.py` | SQLAlchemy TypeDecorators |
| `backend/services/encryption_api.py` | REST API |
| `backend/models.py` | Database models (APIKey, AuditLog, etc.) |
| `scripts/rotate_encryption_key.py` | Key rotation tool |
| `docs/ENCRYPTION_GUIDE.md` | Full documentation |
| `tests/test_encryption.py` | Test suite |

## Performance

- Encrypt/decrypt: < 1ms per field
- Create API key: ~150ms (with DB write)
- Audit log: ~50ms (minimal overhead)
- Rotate 1000 keys: ~30 seconds

## Security Checklist

- ✅ Never commit ENCRYPTION_KEY to git
- ✅ Store key in `.env` (git-ignored)
- ✅ Rotate keys quarterly
- ✅ Backup keys securely
- ✅ Set short expiration on API keys (30 days)
- ✅ Use scopes to limit permissions
- ✅ Monitor audit logs
- ✅ Revoke compromised keys immediately

---

**Full documentation:** See `docs/ENCRYPTION_GUIDE.md`
**Implementation summary:** See `ENCRYPTION_IMPLEMENTATION_SUMMARY.md`
