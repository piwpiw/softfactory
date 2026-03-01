# 📝 n8n Setup - Complete Index

> **Purpose**: **Status:** Production Ready
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 n8n Setup - Complete Index 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Status:** Production Ready
**Last Updated:** 2026-02-25
**Version:** 2.0

---

## Start Here

### For Quickest Deployment
1. Run: `bash /d/Project/scripts/n8n-start.sh`
2. Follow interactive prompts (30 minutes)
3. Access: http://localhost:5679

### For Step-by-Step Setup
1. Read: `setup-guide.md` (detailed)
2. Follow: Section by section
3. Troubleshoot with: `troubleshooting.md`

### For Understanding the System
1. Read: `README.md` (overview)
2. Review: `SETUP-SUMMARY.md` (complete picture)
3. Reference: Other docs as needed

---

## Document Guide

### README.md (13 KB)
**Purpose:** Overview, quick start, basic commands
**Read Time:** 10 minutes
**Best For:** Getting started quickly
**Contains:**
- What's included
- 5-minute quick start
- How it works
- Common commands
- Basic troubleshooting

**Start Here** ⭐ (unless time-constrained)

---

### setup-guide.md (14 KB)
**Purpose:** Complete step-by-step setup
**Read Time:** 30 minutes
**Best For:** First-time deployment
**Contains:**
- Prerequisites checklist
- Installation steps
- Gmail OAuth setup (detailed)
- Notion configuration (detailed)
- Telegram bot setup (detailed)
- Environment variables
- Workflow import
- Testing procedures

**Read Next** (after README)

---

### troubleshooting.md (19 KB)
**Purpose:** Problem diagnosis and solutions
**Read Time:** On-demand reference
**Best For:** When something breaks
**Contains:**
- Quick diagnosis commands
- 15+ issue categories
- 30+ specific solutions
- Prevention checklist
- Diagnostic tools
- Support resources

**Reference As Needed** 🆘

---

### backup-strategy.md (15 KB)
**Purpose:** Backup and disaster recovery
**Read Time:** 20 minutes (now), then reference
**Best For:** Protecting data
**Contains:**
- Backup schedule
- Automated scripts
- Manual procedures
- Off-site storage options
- Recovery procedures
- Compliance guidelines

**Read Before Production** ⚠️

---

### SETUP-SUMMARY.md (16 KB)
**Purpose:** Complete project overview
**Read Time:** 15 minutes
**Best For:** Understanding everything
**Contains:**
- Executive summary
- All deliverables
- Quick start commands
- Integration summary
- Directory structure
- Success criteria
- Checklists

**Review For Context** 📋

---

### MONITORING-DASHBOARD.json (11 KB)
**Purpose:** Grafana dashboard configuration
**Read Time:** N/A (config file)
**Best For:** Setting up monitoring
**Contains:**
- Dashboard definition
- Panel configurations
- Alert definitions
- Prometheus queries

**Use For Grafana** 📊

---

## Configuration Files

### .n8nconfig.json
**Location:** `/d/Project/.n8nconfig.json`
**Purpose:** Core n8n configuration
**What It Does:**
- Defines API ports (5678, 5679)
- Sets up database (SQLite)
- Configures logging
- Defines integrations
- Sets execution parameters
**When to Edit:** Only for advanced tuning

### environment-template.env
**Location:** `/d/Project/n8n/environment-template.env`
**Purpose:** Template for credentials
**What It Does:**
- Shows all environment variables needed
- Explains each credential
- Provides examples
**How to Use:** Copy to `.env.n8n`, fill in values

### .env.n8n (you create)
**Location:** `/d/Project/.env.n8n`
**Purpose:** Your actual credentials
**What It Contains:**
- Gmail OAuth tokens
- Notion API key
- Telegram bot token
- Security keys
**Important:** NEVER commit to git!

---

## Workflow File

### daily-report-automation.json
**Location:** `/d/Project/n8n/workflows/daily-report-automation.json`
**Purpose:** The actual workflow that sends reports
**What It Does:**
- 5 scheduled triggers (5AM, 10AM, 3PM, 5PM, 10PM)
- Fetches report data
- Sends to Gmail
- Saves to Notion
- Sends Telegram notification
- Logs execution
**Nodes:** 10 total (5 triggers, 1 data fetcher, 3 outputs, 1 logger)
**Import:** Automatic via startup script or manual via UI

---

## Startup Script

### n8n-start.sh
**Location:** `/d/Project/scripts/n8n-start.sh`
**Purpose:** One-command setup
**What It Does:**
```
1. Check prerequisites
2. Create directories
3. Set up environment
4. Install n8n
5. Import workflows
6. Validate config
7. Prompt to start
```
**Run:** `bash /d/Project/scripts/n8n-start.sh`
**Time:** ~30 minutes including setup

---

## Backup Scripts

### n8n-backup-workflows.sh
- **Purpose:** Export all workflows daily
- **Frequency:** Daily (configure via cron)
- **Retention:** 30 days
- **Location:** `/d/Project/n8n/backups/workflows/`

### n8n-backup-database.sh
- **Purpose:** Backup SQLite database hourly
- **Frequency:** Every hour (configure via cron)
- **Retention:** 7 days
- **Location:** `/d/Project/n8n/backups/database/`

### n8n-backup-full.sh
- **Purpose:** Complete system backup weekly
- **Frequency:** Weekly Sunday 3 AM (configure via cron)
- **Retention:** 12 weeks
- **Location:** `/d/Project/n8n/backups/full_*/`

### n8n-rotate-logs.sh
- **Purpose:** Rotate and compress logs
- **Frequency:** Daily (configure via cron)
- **Retention:** 30 days
- **Location:** `/d/Project/logs/n8n/archive/`

---

## Directory Structure

```
/d/Project/
├── .n8nconfig.json ..................... Core config
├── n8n/ ............................... Main directory
│   ├── INDEX.md ........................ This file
│   ├── README.md ....................... Quick start
│   ├── setup-guide.md .................. Setup steps
│   ├── troubleshooting.md .............. Solutions
│   ├── backup-strategy.md .............. Disaster recovery
│   ├── SETUP-SUMMARY.md ................ Overview
│   ├── environment-template.env ........ Credentials template
│   ├── monitoring-dashboard.json ....... Grafana config
│   ├── workflows/
│   │   └── daily-report-automation.json  Main workflow
│   ├── credentials/ .................... Auto-created
│   └── backups/ ........................ Auto-created
├── scripts/
│   ├── n8n-start.sh .................... Startup script
│   ├── n8n-backup-workflows.sh ......... Backup script
│   ├── n8n-backup-database.sh ......... Backup script
│   ├── n8n-backup-full.sh ............. Backup script
│   └── n8n-rotate-logs.sh ............. Log rotation
└── logs/
    └── n8n/ ............................ Auto-created
```

---

## Quick Reference - Commands

### Start n8n
```bash
# Interactive setup
bash /d/Project/scripts/n8n-start.sh

# Direct start
n8n start

# Start in background
n8n start &

# With specific port
N8N_PORT=5680 n8n start
```

### Access
```bash
# Web UI
http://localhost:5679

# API
http://localhost:5678

# Health check
curl http://localhost:5678/api/v1/health
```

### Workflows
```bash
# List workflows
curl http://localhost:5678/api/v1/workflows

# Export workflow
n8n export:workflow --id={id} > backup.json

# Import workflow
n8n import:workflow --input=backup.json
```

### Logs
```bash
# View logs
tail -f /d/Project/logs/n8n/n8n.log

# View errors only
grep ERROR /d/Project/logs/n8n/n8n.log

# Last 50 lines
tail -50 /d/Project/logs/n8n/n8n.log
```

### Backups
```bash
# List backups
ls /d/Project/n8n/backups/

# Manual backup
bash /d/Project/scripts/n8n-backup-full.sh

# Restore database
cp /d/Project/n8n/backups/database/*.sqlite /d/Project/.n8n/
```

---

## Setup Sequence (Recommended)

### Phase 1: Understanding (15 min)
1. ✅ Read this INDEX.md
2. ✅ Read README.md
3. ✅ Review SETUP-SUMMARY.md

### Phase 2: Preparation (15 min)
1. ✅ Get Gmail OAuth credentials
2. ✅ Create Notion integration
3. ✅ Create Telegram bot
4. ✅ Generate security secrets

### Phase 3: Installation (30 min)
1. ✅ Run setup script
2. ✅ Fill in credentials
3. ✅ Import workflow
4. ✅ Test execution

### Phase 4: Configuration (15 min)
1. ✅ Set up email destination
2. ✅ Verify Notion database
3. ✅ Confirm Telegram delivery
4. ✅ Check scheduling

### Phase 5: Deployment (10 min)
1. ✅ Enable automated backups
2. ✅ Set up monitoring
3. ✅ Document any customizations
4. ✅ Test 24-hour cycle

**Total Time:** ~90 minutes for complete setup

---

## Success Checklist

### Setup Complete When:
- [ ] n8n starts without errors
- [ ] Workflow appears in UI
- [ ] All 3 credentials configured
- [ ] 5 schedules show in workflow
- [ ] Manual execution succeeds
- [ ] Email received
- [ ] Notion page created
- [ ] Telegram message arrived

### Production Ready When:
- [ ] 24-hour test cycle passed
- [ ] All 5 schedules executed
- [ ] Backups running
- [ ] Monitoring active
- [ ] Team trained
- [ ] Documentation reviewed
- [ ] Disaster recovery tested

---

## Troubleshooting Quick Path

**Problem?** → **Solution Steps:**

1. **Check Logs**
   ```bash
   tail -f /d/Project/logs/n8n/n8n.log
   ```

2. **Run Diagnostics**
   ```bash
   curl http://localhost:5678/api/v1/health
   ```

3. **Review Docs**
   - Basic issue → troubleshooting.md
   - Setup issue → setup-guide.md
   - Backup issue → backup-strategy.md

4. **Get Help**
   - n8n docs: https://docs.n8n.io
   - Community: https://community.n8n.io

---

## Credentials Checklist

### Gmail Setup
- [ ] Created OAuth app (Google Cloud Console)
- [ ] Got Client ID
- [ ] Got Client Secret
- [ ] Got Refresh Token
- [ ] Added to .env.n8n
- [ ] Tested "Send Email" node

### Notion Setup
- [ ] Created integration
- [ ] Got API Key
- [ ] Created/shared database
- [ ] Got Database ID
- [ ] Added to .env.n8n
- [ ] Tested "Save to Notion" node

### Telegram Setup
- [ ] Created bot (@BotFather)
- [ ] Got Bot Token
- [ ] Got Chat ID
- [ ] Added to .env.n8n
- [ ] Tested "Send Telegram" node

### Security Setup
- [ ] Generated N8N_JWT_SECRET (32+ chars)
- [ ] Generated N8N_ENCRYPTION_KEY (32+ chars)
- [ ] Added to .env.n8n
- [ ] Backed up credentials file

---

## Performance Metrics

**Expected Performance:**
- Execution Duration: 2-3 seconds
- Success Rate: >99%
- Memory: 200-400MB
- Database: <100MB
- Backups: ~50MB/week

**Monitor Via:**
- n8n UI: Execution History
- Logs: `/d/Project/logs/n8n/n8n.log`
- Dashboard: Grafana (see monitoring-dashboard.json)

---

## File Size Reference

| File | Size | Type |
|------|------|------|
| .n8nconfig.json | 3 KB | Config |
| environment-template.env | 4.6 KB | Template |
| README.md | 13 KB | Docs |
| setup-guide.md | 14 KB | Docs |
| troubleshooting.md | 19 KB | Docs |
| backup-strategy.md | 15 KB | Docs |
| monitoring-dashboard.json | 11 KB | Config |
| daily-report-automation.json | 5 KB | Workflow |

**Total Documentation:** ~100 KB

---

## What's Not Included

(And how to add it)

- Redis Queue Setup - See setup-guide.md Advanced section
- Prometheus Metrics - See monitoring-dashboard.json
- Sentry Error Tracking - See setup-guide.md Advanced section
- Slack Notifications - Add to workflow as new node
- Custom Webhooks - See n8n API docs
- SSL/HTTPS - See setup-guide.md Production section

---

## Glossary

| Term | Meaning |
|------|---------|
| **n8n** | Workflow automation platform (this tool) |
| **Workflow** | Sequence of steps (the Daily Report) |
| **Node** | Individual action (Send Email, Save to Notion) |
| **Cron** | Schedule expression (0 5 * * * = 5 AM daily) |
| **OAuth** | Secure authentication (Gmail) |
| **API Key** | Access token (Notion) |
| **Bot Token** | Bot identifier (Telegram) |
| **Execution** | Single run of a workflow |
| **Schedule** | Automated trigger time |
| **Webhook** | External trigger (URL) |

---

## Support Resources

**Official:**
- n8n Docs: https://docs.n8n.io
- n8n API: https://docs.n8n.io/api
- GitHub: https://github.com/n8n-io/n8n

**Community:**
- Forum: https://community.n8n.io
- Slack: n8n community Slack
- Discord: n8n Discord server

**Internal:**
- Team Chat: (your team channel)
- Wiki: (your internal docs)
- Contact: DevOps team

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 2.0 | 2026-02-25 | Complete setup + docs + monitoring + backup |
| 1.0 | 2026-02-24 | Initial workflow |

---

## License & Maintenance

**Ownership:** SoftFactory Team
**Status:** Production Ready
**Maintenance:** DevOps/Infrastructure Team
**Last Update:** 2026-02-25
**Next Review:** 2026-03-25

---

## Final Checklist

Before Going Live:
- [ ] Read all relevant documentation
- [ ] Complete setup script
- [ ] Test all integrations
- [ ] Verify all 5 schedules
- [ ] Enable automated backups
- [ ] Set up monitoring
- [ ] Test disaster recovery
- [ ] Train team
- [ ] Document customizations
- [ ] Get approval from stakeholders

---

## Quick Links

**Installation:**
- Startup: `bash /d/Project/scripts/n8n-start.sh`
- Setup Guide: `/d/Project/n8n/setup-guide.md`

**Operations:**
- Access UI: http://localhost:5679
- View Logs: `/d/Project/logs/n8n/n8n.log`
- Backups: `/d/Project/n8n/backups/`

**Help:**
- Troubleshooting: `/d/Project/n8n/troubleshooting.md`
- Disaster Recovery: `/d/Project/n8n/backup-strategy.md`
- Configuration: `/d/Project/n8n/README.md`

---

**Ready to Start?** → Run: `bash /d/Project/scripts/n8n-start.sh`

**Need Help?** → Read: `setup-guide.md` or `troubleshooting.md`

**Have Questions?** → Check: `README.md` or this INDEX.md

---

**Version:** 2.0 | **Last Updated:** 2026-02-25 | **Status:** Production Ready ✓