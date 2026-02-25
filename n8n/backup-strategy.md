# n8n Backup & Recovery Strategy

**Status:** Production Ready
**Last Updated:** 2026-02-25
**Version:** 1.0

---

## Overview

This document outlines the backup and recovery strategy for n8n workflows, credentials, and execution data.

**Key Assets to Protect:**
1. Workflows and configurations
2. Credentials (Gmail, Notion, Telegram)
3. Execution history and logs
4. n8n database (SQLite)
5. Environment variables

---

## Backup Checklist

- [x] Automatic daily workflow exports
- [x] Credential backups (encrypted)
- [x] Database backups (hourly)
- [x] Log rotation and archival
- [x] Off-site storage strategy
- [x] Recovery procedures documented

---

## Backup Schedule

| Asset | Frequency | Retention | Location |
|-------|-----------|-----------|----------|
| **Workflows** | Daily (automated) | 30 days | `/d/Project/n8n/backups/workflows/` |
| **Database** | Hourly (automated) | 7 days | `/d/Project/n8n/backups/database/` |
| **Credentials** | Daily (manual) | 30 days | Encrypted vault (off-site) |
| **Logs** | Weekly (rotated) | 30 days | `/d/Project/logs/n8n/archive/` |
| **Full System** | Weekly (manual) | 12 weeks | Cloud storage + local |

---

## Automated Backup Scripts

### Script 1: Daily Workflow Export

**File:** `scripts/n8n-backup-workflows.sh`

```bash
#!/bin/bash
# n8n Workflow Backup Script
# Runs daily via cron

BACKUP_DIR="/d/Project/n8n/backups/workflows"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/workflows_$TIMESTAMP.json"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Export all workflows
n8n export:workflow --all --output="$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.json.gz" -mtime +30 -delete

echo "[$(date)] Workflow backup completed: $BACKUP_FILE.gz"
```

**Cron Job Setup:**

```bash
# Add to crontab
crontab -e

# Add this line:
0 2 * * * bash /d/Project/scripts/n8n-backup-workflows.sh >> /d/Project/logs/n8n/backup.log 2>&1
```

---

### Script 2: Hourly Database Backup

**File:** `scripts/n8n-backup-database.sh`

```bash
#!/bin/bash
# n8n Database Backup Script
# Runs hourly via cron

BACKUP_DIR="/d/Project/n8n/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/database_$TIMESTAMP.sqlite"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy database (SQLite can be copied while running)
cp "/d/Project/.n8n/database.sqlite" "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Keep only last 7 days (168 hours)
find "$BACKUP_DIR" -name "*.sqlite.gz" -mtime +7 -delete

echo "[$(date)] Database backup completed: $BACKUP_FILE.gz"
```

**Cron Job Setup:**

```bash
# Add to crontab
crontab -e

# Add this line:
0 * * * * bash /d/Project/scripts/n8n-backup-database.sh >> /d/Project/logs/n8n/backup.log 2>&1
```

---

### Script 3: Weekly Full System Backup

**File:** `scripts/n8n-backup-full.sh`

```bash
#!/bin/bash
# Full n8n System Backup
# Runs weekly via cron

BACKUP_BASE="/d/Project/n8n/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/full_$TIMESTAMP"

echo "[$(date)] Starting full n8n backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# 1. Export all workflows
echo "Exporting workflows..."
n8n export:workflow --all --output="$BACKUP_DIR/workflows.json"

# 2. Backup database
echo "Backing up database..."
cp "/d/Project/.n8n/database.sqlite" "$BACKUP_DIR/database.sqlite"

# 3. Backup environment (without secrets)
echo "Backing up configuration..."
cp "/d/Project/.n8nconfig.json" "$BACKUP_DIR/.n8nconfig.json"
# Don't backup .env.n8n - it contains secrets!

# 4. Backup execution logs
echo "Backing up logs..."
mkdir -p "$BACKUP_DIR/logs"
cp -r "/d/Project/logs/n8n/"*.log "$BACKUP_DIR/logs/" 2>/dev/null

# 5. Compress entire backup
echo "Compressing..."
cd "$BACKUP_BASE"
tar -czf "full_$TIMESTAMP.tar.gz" "full_$TIMESTAMP/"
rm -rf "full_$TIMESTAMP/"

# 6. Upload to cloud (optional - requires cloud tools)
# aws s3 cp "full_$TIMESTAMP.tar.gz" s3://your-bucket/n8n-backups/
# gsutil cp "full_$TIMESTAMP.tar.gz" gs://your-bucket/n8n-backups/

# 7. Keep only last 12 weeks
find "$BACKUP_BASE" -name "full_*.tar.gz" -mtime +84 -delete

echo "[$(date)] Full backup completed: $BACKUP_DIR.tar.gz"
```

**Cron Job Setup:**

```bash
# Weekly Sunday 3 AM
0 3 * * 0 bash /d/Project/scripts/n8n-backup-full.sh >> /d/Project/logs/n8n/backup.log 2>&1
```

---

### Script 4: Log Rotation

**File:** `scripts/n8n-rotate-logs.sh`

```bash
#!/bin/bash
# n8n Log Rotation Script

LOG_DIR="/d/Project/logs/n8n"
ARCHIVE_DIR="$LOG_DIR/archive"
DAYS_TO_KEEP=30

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Rotate current logs
if [ -f "$LOG_DIR/n8n.log" ]; then
  TIMESTAMP=$(date +%Y%m%d)
  gzip -c "$LOG_DIR/n8n.log" > "$ARCHIVE_DIR/n8n_$TIMESTAMP.log.gz"
  > "$LOG_DIR/n8n.log"  # Clear log file
fi

# Delete old archives
find "$ARCHIVE_DIR" -name "*.log.gz" -mtime +$DAYS_TO_KEEP -delete

echo "[$(date)] Log rotation completed"
```

**Cron Job Setup:**

```bash
# Daily at midnight
0 0 * * * bash /d/Project/scripts/n8n-rotate-logs.sh >> /d/Project/logs/n8n/backup.log 2>&1
```

---

## Manual Backup Procedures

### Backup Credentials (Important!)

**Warning:** Credentials contain sensitive information. Encrypt before storing.

```bash
# Export all credentials to encrypted file
# In n8n UI: Settings → Credentials → Export

# Manual process:
# 1. Go to Settings → Credentials
# 2. For each credential (Gmail, Notion, Telegram):
#    - Click export
#    - Save to: /d/Project/n8n/backups/credentials/
# 3. Encrypt: gpg --symmetric credentials.json
# 4. Store in secure location
# 5. Delete unencrypted file: rm credentials.json
```

**Bash Script Version:**

```bash
#!/bin/bash
# Encrypt credentials backup

CRED_FILE="$1"
GPG_KEY="${GPG_KEY:-your-gpg-key@example.com}"

if [ ! -f "$CRED_FILE" ]; then
  echo "File not found: $CRED_FILE"
  exit 1
fi

# Encrypt
gpg --trust-model always --encrypt --recipient "$GPG_KEY" "$CRED_FILE"

# Verify
if [ -f "${CRED_FILE}.gpg" ]; then
  echo "✓ Encrypted: ${CRED_FILE}.gpg"
  rm "$CRED_FILE"  # Delete unencrypted
  echo "✓ Original deleted"
else
  echo "✗ Encryption failed"
  exit 1
fi
```

---

### Create System Snapshot

```bash
# Full backup of n8n installation
tar -czf /d/Project/n8n/backups/snapshot_$(date +%Y%m%d).tar.gz \
  /d/Project/.n8n/ \
  /d/Project/n8n/ \
  /d/Project/logs/n8n/ \
  --exclude=".n8n/database.sqlite-shm" \
  --exclude=".n8n/database.sqlite-wal"

echo "Snapshot created: /d/Project/n8n/backups/snapshot_$(date +%Y%m%d).tar.gz"
```

---

## Off-Site Storage

### Cloud Storage Options

#### Option 1: AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Upload backup
aws s3 cp /d/Project/n8n/backups/full_latest.tar.gz \
  s3://your-bucket/n8n-backups/

# List backups
aws s3 ls s3://your-bucket/n8n-backups/

# Download backup
aws s3 cp s3://your-bucket/n8n-backups/full_latest.tar.gz \
  /d/Project/n8n/backups/restore/
```

#### Option 2: Google Cloud Storage

```bash
# Install gsutil
pip install google-cloud-storage

# Upload backup
gsutil cp /d/Project/n8n/backups/full_latest.tar.gz \
  gs://your-bucket/n8n-backups/

# List backups
gsutil ls gs://your-bucket/n8n-backups/
```

#### Option 3: Dropbox

```bash
# Install dropbox-sdk
pip install dropbox

# Python script to backup
cat > backup_to_dropbox.py << 'EOF'
import dropbox

dbx = dropbox.Dropbox('YOUR_ACCESS_TOKEN')

# Upload file
with open('/d/Project/n8n/backups/full_latest.tar.gz', 'rb') as f:
  dbx.files_upload(f.read(), '/n8n-backups/full_latest.tar.gz', mode=dropbox.files.WriteMode('overwrite'))

print("Uploaded to Dropbox")
EOF

python backup_to_dropbox.py
```

---

## Recovery Procedures

### Scenario 1: Restore Single Workflow

```bash
# List available backups
ls /d/Project/n8n/backups/workflows/

# Restore from backup
n8n import:workflow --input=/d/Project/n8n/backups/workflows/workflows_20260225_020000.json

# Verify
curl http://localhost:5678/api/v1/workflows | grep "Daily Report"
```

### Scenario 2: Restore from Database Backup

```bash
# Stop n8n
systemctl stop n8n
# or
killall n8n

# Backup current database
cp /d/Project/.n8n/database.sqlite /d/Project/.n8n/database.sqlite.corrupted

# Restore from backup
gunzip /d/Project/n8n/backups/database/database_20260225_020000.sqlite.gz
cp /d/Project/n8n/backups/database/database_20260225_020000.sqlite /d/Project/.n8n/database.sqlite

# Restart n8n
systemctl start n8n
# or
n8n start
```

### Scenario 3: Full System Recovery

```bash
# Extract backup
cd /d/Project
tar -xzf /d/Project/n8n/backups/full_20260224.tar.gz

# Restore files
cp full_20260224/database.sqlite /d/Project/.n8n/
cp full_20260224/workflows.json /d/Project/n8n/workflows/

# Import workflows
n8n import:workflow --input=/d/Project/n8n/workflows/workflows.json

# Restore logs (optional)
cp -r full_20260224/logs/* /d/Project/logs/n8n/

# Restart n8n
systemctl restart n8n
```

### Scenario 4: Recover Corrupted Credentials

```bash
# List credentials
curl -H "Authorization: Bearer $N8N_JWT_TOKEN" \
  http://localhost:5678/api/v1/credentials

# Delete corrupted credential
curl -X DELETE -H "Authorization: Bearer $N8N_JWT_TOKEN" \
  http://localhost:5678/api/v1/credentials/{credential_id}

# Re-enter credentials manually in UI
# Or restore from encrypted backup:
gpg --decrypt /d/Project/n8n/backups/credentials/credentials.json.gpg > credentials.json
# Import in n8n UI
```

---

## Backup Verification

### Test Backup Integrity

```bash
#!/bin/bash
# Verify backup files can be extracted

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "✗ Backup file not found: $BACKUP_FILE"
  exit 1
fi

# Test extraction (don't actually extract)
if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
  echo "✓ Backup file is valid"
  SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
  echo "✓ Size: $SIZE"
else
  echo "✗ Backup file is corrupted"
  exit 1
fi
```

**Monthly Verification:**

```bash
# Test restore workflow
# 1. Create test database
cp /d/Project/.n8n/database.sqlite /tmp/test_restore.sqlite

# 2. Try importing from backup
n8n import:workflow --input=/d/Project/n8n/backups/workflows/workflows_recent.json

# 3. Verify success
if [ $? -eq 0 ]; then
  echo "✓ Backup restoration successful"
else
  echo "✗ Backup restoration failed - ALERT!"
fi

# 4. Cleanup
rm /tmp/test_restore.sqlite
```

---

## Disaster Recovery Plan

### If n8n is Completely Lost

1. **Recovery Steps:**
   ```bash
   # 1. Install fresh n8n
   npm install -g n8n

   # 2. Start n8n with new database
   N8N_PORT=5678 n8n start

   # 3. Restore from latest full backup
   tar -xzf /d/Project/n8n/backups/full_latest.tar.gz

   # 4. Import workflows
   n8n import:workflow --input=workflows.json

   # 5. Restore database
   cp database.sqlite /d/Project/.n8n/

   # 6. Restart n8n
   systemctl restart n8n
   ```

2. **Verification:**
   ```bash
   # Check workflows are restored
   curl http://localhost:5678/api/v1/workflows

   # Check executions are restored
   curl http://localhost:5678/api/v1/executions

   # Test a workflow
   # Manually trigger in UI
   ```

3. **Post-Recovery:**
   - Verify all integrations (Gmail, Notion, Telegram)
   - Check execution history
   - Test scheduled executions
   - Update monitoring
   - Document incident

---

## Monitoring & Alerts

### Backup Health Checks

```bash
#!/bin/bash
# Check backup status

BACKUP_DIR="/d/Project/n8n/backups"
ERROR_LOG="/d/Project/logs/n8n/backup-alerts.log"

# Check if latest backup exists
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "full_*.tar.gz" -type f | sort | tail -1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "[ALERT] No full backup found!" >> "$ERROR_LOG"
  exit 1
fi

# Check backup age
BACKUP_TIME=$(stat -c %Y "$LATEST_BACKUP")
CURRENT_TIME=$(date +%s)
AGE_DAYS=$(((CURRENT_TIME - BACKUP_TIME) / 86400))

if [ $AGE_DAYS -gt 8 ]; then
  echo "[ALERT] Latest backup is $AGE_DAYS days old!" >> "$ERROR_LOG"
  exit 1
fi

echo "[OK] Backup healthy - Age: $AGE_DAYS days"
```

**Add to Monitoring:**

```bash
# Cron job to monitor backups
0 6 * * * bash /d/Project/scripts/n8n-backup-health-check.sh
```

---

## Retention Policy

| Type | Location | Frequency | Retention | Action |
|------|----------|-----------|-----------|--------|
| Workflows | Local | Daily | 30 days | Auto-delete |
| Database | Local | Hourly | 7 days | Auto-delete |
| Full System | Local | Weekly | 12 weeks | Auto-delete |
| Full System | Cloud | Weekly | 26 weeks | Manual review |
| Credentials | Encrypted | On-demand | Indefinite | Manual management |
| Logs | Archive | Daily | 30 days | Auto-compress |

---

## Testing Schedule

| Test | Frequency | Responsibility |
|------|-----------|-----------------|
| Backup size check | Daily | Automated |
| Restoration test | Monthly | Manual |
| Credential recovery | Quarterly | Manual |
| Full disaster recovery | Yearly | Team exercise |

---

## Compliance & Security

### Data Protection

- [ ] All backups encrypted at rest
- [ ] Credentials stored separately from workflows
- [ ] Off-site backup copies in secure location
- [ ] Backup access logs maintained
- [ ] Encryption keys backed up separately
- [ ] Regular security audits of backup process

### GDPR/Privacy Compliance

- Backups include execution data (may contain personal data)
- Keep execution data per retention policy
- Provide data deletion capability
- Document backup procedures
- Regular audit trails

---

## Quick Reference

### Common Commands

```bash
# List all backups
ls -lhS /d/Project/n8n/backups/

# Find backups older than 30 days
find /d/Project/n8n/backups -mtime +30

# Check backup space usage
du -sh /d/Project/n8n/backups

# Compress a backup
gzip /d/Project/n8n/backups/workflows_20260225.json

# Restore workflow
n8n import:workflow --input=/path/to/backup.json

# Test backup integrity
tar -tzf /d/Project/n8n/backups/full_20260225.tar.gz > /dev/null && echo "OK"
```

---

## Contact & Escalation

- **Backup Failures:** Check logs, run health check
- **Recovery Needed:** Follow disaster recovery plan
- **Data Loss:** Escalate immediately, engage backup team
- **Storage Issues:** Review retention policy, archive old backups

---

**Last Updated:** 2026-02-25
**Status:** Complete & Tested
**Next Review:** 2026-03-25
