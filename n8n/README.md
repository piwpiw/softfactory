# 📊 n8n Daily Report Automation System

> **Purpose**: **Status:** Production Ready ✓
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 n8n Daily Report Automation System 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Status:** Production Ready ✓
**Last Updated:** 2026-02-25
**Version:** 2.0

---

## Quick Overview

This is a complete n8n automation setup for **daily SoftFactory reports** sent to:
- 📧 **Gmail** - Email reports
- 📝 **Notion** - Database records
- 💬 **Telegram** - Instant notifications

**Schedule:** 5 AM, 10 AM, 3 PM, 5 PM, 10 PM (Asia/Seoul timezone)

---

## What's Included

### Configuration Files
| File | Purpose |
|------|---------|
| `.n8nconfig.json` | n8n core configuration |
| `environment-template.env` | Template for credentials (copy to `.env.n8n`) |
| `workflows/daily-report-automation.json` | Main workflow (5 schedules + 3 integrations) |

### Documentation
| Document | Content |
|----------|---------|
| `setup-guide.md` | Step-by-step installation (30 mins) |
| `troubleshooting.md` | 30+ solutions for common issues |
| `backup-strategy.md` | Backup & recovery procedures |
| `monitoring-dashboard.json` | Grafana dashboard config |

### Scripts
| Script | Function |
|--------|----------|
| `scripts/n8n-start.sh` | One-command startup (interactive) |
| `scripts/n8n-backup-workflows.sh` | Daily workflow backups |
| `scripts/n8n-backup-database.sh` | Hourly database backups |
| `scripts/n8n-backup-full.sh` | Weekly full system backup |
| `scripts/n8n-rotate-logs.sh` | Log rotation & archival |

---

## 5-Minute Quick Start

### Step 1: Run Setup Script
```bash
bash scripts/n8n-start.sh
```

The script will:
- ✓ Check prerequisites (Node.js, npm)
- ✓ Create directories
- ✓ Set up environment variables
- ✓ Install n8n
- ✓ Import workflows
- ✓ Guide you to add credentials

### Step 2: Configure Credentials

**You need 3 things:**

1. **Gmail OAuth**
   - Get from: [Google Cloud Console](https://console.cloud.google.com)
   - Add to `.env.n8n`: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`

2. **Notion API**
   - Get from: [Notion Integrations](https://www.notion.so/my-integrations)
   - Add to `.env.n8n`: `NOTION_API_KEY`, `NOTION_DATABASE_ID`

3. **Telegram Bot**
   - Get from: Message `@BotFather` on Telegram
   - Add to `.env.n8n`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### Step 3: Test
```bash
# Open n8n UI
http://localhost:5679

# Open workflow: "Daily Report Automation"
# Click "Execute" button
# Verify Gmail, Notion, and Telegram all received the report
```

**That's it! Reports will now send automatically at scheduled times.**

---

## File Structure

```
/d/Project/
├── .n8nconfig.json                    ← Core configuration
├── .env.n8n                           ← Credentials (git-ignored)
├── n8n/
│   ├── README.md                      ← This file
│   ├── setup-guide.md                 ← Detailed setup instructions
│   ├── troubleshooting.md             ← Problem solving guide
│   ├── backup-strategy.md             ← Backup & recovery
│   ├── monitoring-dashboard.json      ← Grafana dashboard
│   ├── environment-template.env       ← Template for credentials
│   ├── workflows/
│   │   └── daily-report-automation.json  ← Main workflow
│   ├── credentials/                   ← Auto-created (encrypted)
│   └── backups/                       ← Auto-created (automatic backups)
├── scripts/
│   ├── n8n-start.sh                   ← Main startup script
│   ├── n8n-backup-workflows.sh        ← Workflow backup
│   ├── n8n-backup-database.sh         ← Database backup
│   ├── n8n-backup-full.sh             ← Full system backup
│   └── n8n-rotate-logs.sh             ← Log rotation
└── logs/
    └── n8n/                           ← Execution logs
```

---

## How It Works

### Workflow Structure

```
Cron Triggers (5 schedules)
    ↓
Fetch Report Data (API call to localhost:8000)
    ↓
    ├─→ Send Gmail Report ────┐
    ├─→ Save to Notion ───────┤
    └─→ Send Telegram Report ─┤
                              ↓
                         Log Execution
                              ↓
                        Final Summary
```

### Schedule Details

| Time | Report Type | Greeting |
|------|-------------|----------|
| 5 AM | Morning Brief | Good Morning! |
| 10 AM | Mid-Morning Check | Good Morning! |
| 3 PM | Afternoon Update | Good Afternoon! |
| 5 PM | Evening Status | Good Evening! |
| 10 PM | Night Summary | Good Night! |

All times in **Asia/Seoul** timezone.

---

## Daily Workflow

### What Happens When Report Triggers

1. **Fetch Data** - Gets latest metrics from SoftFactory API
2. **Format Report** - Structures data with greeting and type
3. **Send Gmail** - Email sent to configured recipient
4. **Save Notion** - Record created in database for history
5. **Telegram Alert** - Instant notification sent
6. **Log Execution** - Records success/failure for monitoring

**Total Duration:** ~2-3 seconds per execution

---

## Accessing the Reports

### Via Email (Gmail)
- **Subject:** `Good Morning! - SoftFactory morning_brief Report`
- **Format:** HTML formatted with styling
- **Frequency:** 5 times daily

### Via Notion Database
- **Table Name:** (As configured in `NOTION_DATABASE_ID`)
- **Columns:** Title, Date, Report_Type, Time, Status, Metrics
- **Access:** https://www.notion.so/[your-workspace]

### Via Telegram Bot
- **Bot Name:** SoftFactory Reports Bot
- **Format:** Formatted message with emoji
- **Notifications:** Pin important messages for visibility

---

## Configuration Reference

### Environment Variables (.env.n8n)

**Required:**
```bash
# n8n
N8N_PORT=5678
N8N_JWT_SECRET=random_32_character_string

# Gmail
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
GMAIL_SENDER_EMAIL=your-email@gmail.com

# Notion
NOTION_API_KEY=ntn_your_api_key
NOTION_DATABASE_ID=your_database_id

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Optional:**
```bash
# Logging
N8N_LOG_LEVEL=info
N8N_LOG_FILE_LOCATION=D:/Project/logs/n8n

# Database
DB_SQLITE_PATH=D:/Project/.n8n/database.sqlite

# Performance
WORKER_CONCURRENCY=5
EXECUTIONS_PRUNEDATA=true
```

---

## Commands Reference

### Start n8n
```bash
# Interactive setup and start
bash scripts/n8n-start.sh

# Start in background
N8N_PORT=5678 n8n start &

# Start with debug logging
N8N_LOG_LEVEL=debug n8n start
```

### Stop n8n
```bash
# Kill process
kill $(pgrep n8n)

# Or if using systemd
systemctl stop n8n
```

### View Logs
```bash
# Real-time logs
tail -f /d/Project/logs/n8n/n8n.log

# Last 50 lines
tail -50 /d/Project/logs/n8n/n8n.log

# Search for errors
grep ERROR /d/Project/logs/n8n/n8n.log
```

### Export Workflow
```bash
n8n export:workflow --id={workflow_id} > backup.json
```

### Import Workflow
```bash
n8n import:workflow --input=backup.json
```

### Backup Database
```bash
cp /d/Project/.n8n/database.sqlite /d/Project/n8n/backups/database_backup.sqlite
```

---

## Monitoring & Health Checks

### Is n8n Running?
```bash
curl http://localhost:5678/api/v1/health
# Should return: {"status":"ok"}
```

### View Active Workflows
```bash
curl http://localhost:5678/api/v1/workflows
```

### Check Recent Executions
```bash
curl http://localhost:5678/api/v1/executions?limit=10
```

### Monitor CPU/Memory
```bash
# Linux/Mac
ps aux | grep n8n

# Or use top
top -p $(pgrep n8n)
```

---

## Common Issues

### Port 5678 in use?
```bash
# Find what's using the port
lsof -i :5678

# Kill it
kill -9 <PID>
```

### Credentials not loading?
```bash
# Check file exists
ls -la /d/Project/.env.n8n

# Load manually
set -a
source /d/Project/.env.n8n
set +a

# Verify
echo $GMAIL_CLIENT_ID
```

### Workflow not running on schedule?
```bash
# Check queue worker is running
curl http://localhost:5678/api/v1/health

# Check workflow is active
curl http://localhost:5678/api/v1/workflows | grep -i "Daily Report"

# Test manual execution
curl -X POST http://localhost:5678/api/v1/workflows/{id}/execute
```

**For more issues, see `troubleshooting.md`**

---

## Backups

### Automatic Backups
- **Workflows:** Daily at 2 AM → `/d/Project/n8n/backups/workflows/`
- **Database:** Every hour → `/d/Project/n8n/backups/database/`
- **Full System:** Weekly Sunday 3 AM → `/d/Project/n8n/backups/`

### Manual Backup
```bash
# Backup everything
bash scripts/n8n-backup-full.sh

# Backup just workflows
bash scripts/n8n-backup-workflows.sh

# Backup just database
bash scripts/n8n-backup-database.sh
```

### Restore from Backup
```bash
# Stop n8n
systemctl stop n8n

# Restore database
gunzip /d/Project/n8n/backups/database/database_20260225_020000.sqlite.gz
cp /d/Project/n8n/backups/database/database_20260225_020000.sqlite /d/Project/.n8n/database.sqlite

# Restart
systemctl start n8n
```

**Full recovery procedures in `backup-strategy.md`**

---

## Security

### Protecting Credentials
- ✓ Never commit `.env.n8n` to git
- ✓ Store in secure location only
- ✓ Rotate tokens periodically
- ✓ Encrypt backups with GPG
- ✓ Use strong JWT secrets

### Access Control
- ✓ Set n8n admin password
- ✓ Restrict API access
- ✓ Enable HTTPS in production
- ✓ Use VPN/Firewall for API

### Compliance
- ✓ GDPR - execution data retention policy
- ✓ Data encryption at rest
- ✓ Audit logs for all operations
- ✓ Regular security reviews

---

## Performance Tuning

### Optimize for Speed
```bash
# Reduce queue processing
WORKER_CONCURRENCY=2

# Disable unnecessary logging
N8N_LOG_LEVEL=warn

# Prune old executions
EXECUTIONS_PRUNEDATA=true
EXECUTIONS_PRUNEDATA_MAXAGE=604800
```

### Scale for Volume
```bash
# Enable Redis queue (for multiple workers)
QUEUE_BULL_PORT=6379

# Increase concurrency
WORKER_CONCURRENCY=10

# Enable caching
CACHE_ENABLED=true
```

---

## Next Steps

1. **Setup:** Follow `setup-guide.md` (30 minutes)
2. **Test:** Run workflow manually and verify all 3 destinations
3. **Monitor:** Check logs and execution history daily
4. **Backup:** Set up automated backups via cron jobs
5. **Scale:** Add more workflows or destinations as needed

---

## Documentation Index

| Document | For |
|----------|-----|
| `setup-guide.md` | Installation & configuration |
| `troubleshooting.md` | Debugging problems |
| `backup-strategy.md` | Backup & recovery |
| `monitoring-dashboard.json` | Performance monitoring |
| `.n8nconfig.json` | Core configuration reference |

---

## Support Resources

| Resource | Link |
|----------|------|
| **n8n Docs** | https://docs.n8n.io |
| **n8n API** | https://docs.n8n.io/api/ |
| **Community** | https://community.n8n.io |
| **GitHub** | https://github.com/n8n-io/n8n |

---

## Status & Metrics

### Current Status
- **n8n Version:** 1.45.0+
- **Node.js:** v18 LTS
- **Database:** SQLite
- **Workflows:** 1 (Daily Report Automation)
- **Integrations:** 3 (Gmail, Notion, Telegram)
- **Uptime:** Depends on infrastructure

### Expected Performance
- **Execution Time:** 2-3 seconds
- **Success Rate:** >99%
- **Database Size:** <100MB (with auto-pruning)
- **Memory Usage:** 200-400MB

### Last Test
- **Date:** 2026-02-25
- **Status:** ✓ All systems operational
- **Email:** ✓ Sending
- **Notion:** ✓ Creating pages
- **Telegram:** ✓ Delivering messages

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-02-25 | Complete setup + monitoring + backup |
| 1.0 | 2026-02-24 | Initial workflow implementation |

---

## License & Usage

This n8n setup is part of the SoftFactory Platform.

**Usage:** Internal daily reporting only
**Maintenance:** DevOps/Infrastructure team
**Support:** See troubleshooting.md or contact team

---

**Setup Complete!** 🎉

Your n8n automation is ready. Start with `bash scripts/n8n-start.sh` and follow the prompts.

Questions? Check `setup-guide.md` or `troubleshooting.md`.

---

**Last Updated:** 2026-02-25 | **Status:** Production Ready ✓