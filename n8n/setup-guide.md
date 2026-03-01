# 📘 n8n Automation Setup Guide

> **Purpose**: **Status:** Production Ready
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 n8n Automation Setup Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Status:** Production Ready
**Last Updated:** 2026-02-25
**Version:** 2.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Workflow Setup](#workflow-setup)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

For experienced users, run this one command:

```bash
bash scripts/n8n-start.sh
```

This will handle all steps automatically. For detailed setup, continue reading.

---

## Prerequisites

### System Requirements

- **OS:** Windows 10+ / macOS / Linux
- **Node.js:** v18 LTS or higher
- **npm:** v8+
- **Python:** 3.8+ (optional, for reporting)
- **Disk Space:** 500MB minimum
- **RAM:** 2GB minimum (4GB recommended)

### Required Credentials

You'll need to obtain these before starting:

1. **Gmail OAuth 2.0** - For sending email reports
2. **Notion API Key** - For saving reports to database
3. **Telegram Bot Token** - For sending messages
4. **n8n JWT Secret** - For security (generate random 32+ chars)

---

## Installation

### Step 1: Check Node.js Installation

```bash
node --version
npm --version
```

Expected output: `v18.x.x` or higher

If not installed, download from [nodejs.org](https://nodejs.org/)

### Step 2: Run Startup Script

```bash
# On Windows (PowerShell or Git Bash)
bash scripts/n8n-start.sh

# On macOS/Linux
bash scripts/n8n-start.sh
```

### Step 3: Follow Interactive Prompts

The script will:
- ✓ Check prerequisites
- ✓ Create necessary directories
- ✓ Set up environment variables
- ✓ Install/update n8n
- ✓ Import workflows
- ✓ Validate configuration

---

## Configuration

### Step 1: Gmail Setup (OAuth 2.0)

#### Get Gmail Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Click "Enable APIs and Services"
   - Search for "Gmail API"
   - Click Enable
4. Create OAuth 2.0 Credentials:
   - Go to "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file
5. Extract credentials from JSON:
   - `GMAIL_CLIENT_ID` - client_id value
   - `GMAIL_CLIENT_SECRET` - client_secret value

#### Get Gmail Refresh Token

```bash
# Manual flow (first time setup)
# 1. Open browser to Google OAuth consent screen
# 2. Authorize n8n
# 3. Copy refresh token from response
# 4. Add to .env.n8n
```

**Or use this Node.js script:**

```javascript
const { google } = require('googleapis');
const oauth2Client = new google.auth.OAuth2(
  'YOUR_CLIENT_ID',
  'YOUR_CLIENT_SECRET',
  'http://localhost:5678/webhook/oauth/callback'
);

// Generate auth URL and follow prompts
const url = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: ['https://www.googleapis.com/auth/gmail.send']
});
console.log('Open:', url);
```

#### Update .env.n8n

```bash
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=1//your_refresh_token
GMAIL_SENDER_EMAIL=your-email@gmail.com
```

---

### Step 2: Notion Setup

#### Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "Create new integration"
3. Name it: `n8n-softfactory-reports`
4. Enable capabilities:
   - ✓ Read
   - ✓ Update
   - ✓ Insert
5. Copy the **API Key**

#### Create Notion Database

1. Open a Notion workspace
2. Create new database with these properties:
   ```
   - Title (title)
   - Date (date)
   - Report_Type (select: Morning Brief, Mid-Morning, Afternoon, Evening, Night)
   - Time (text)
   - Status (select: OPERATIONAL, WARNING, CRITICAL)
   - Content (rich_text)
   - Services_Status (rich_text)
   - Metrics (rich_text)
   ```
3. Share database with integration:
   - Click "Share"
   - Search for integration name
   - Grant access
4. Copy the **Database ID** from URL

#### Update .env.n8n

```bash
NOTION_API_KEY=ntn_your_api_key_here
NOTION_DATABASE_ID=your_database_id_here
```

---

### Step 3: Telegram Setup

#### Create Telegram Bot

1. Open Telegram app
2. Search for and message `@BotFather`
3. Send `/newbot`
4. Follow prompts:
   - Name: `SoftFactory Reports Bot`
   - Username: `softfactory_reports_bot` (must be unique)
5. Copy the **Bot Token** from response

#### Get Your Chat ID

1. Message your new bot
2. Visit: `https://api.telegram.org/bot{TOKEN}/getUpdates`
   - Replace `{TOKEN}` with your bot token
3. Look for `chat.id` in the JSON response
4. This is your **Chat ID**

#### Update .env.n8n

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_ALLOWED_USERS=7910169750
```

---

### Step 4: n8n Security Setup

#### Generate JWT Secrets

```bash
# Generate 32-character random strings
# On macOS/Linux:
openssl rand -hex 16

# On Windows (PowerShell):
[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Random -Count 32 | ForEach-Object { [char]$_ } | Join-String)))

# Or use online tool: https://www.uuidgenerator.net/
```

#### Update .env.n8n

```bash
N8N_JWT_SECRET=your_generated_secret_here_min_32_chars
N8N_USER_MANAGEMENT_JWT_SECRET=another_random_secret_min_32_chars
N8N_ENCRYPTION_KEY=third_random_secret_min_32_chars
```

---

### Step 5: Complete Environment File

Copy the template and fill in all values:

```bash
cp n8n/environment-template.env .env.n8n
```

Then edit `.env.n8n` with your credentials:

```bash
# .env.n8n structure
N8N_PORT=5678
N8N_PROTOCOL=http

# Gmail
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_SENDER_EMAIL=...

# Notion
NOTION_API_KEY=...
NOTION_DATABASE_ID=...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Security
N8N_JWT_SECRET=...
N8N_ENCRYPTION_KEY=...
```

---

## Workflow Setup

### Import Daily Report Workflow

The workflow should be in: `D:/Project/n8n/workflows/daily-report-automation.json`

#### Via n8n UI (Recommended)

1. Open n8n: http://localhost:5679
2. Click "+" → "Import from File"
3. Select `daily-report-automation.json`
4. Click "Import"

#### Via CLI

```bash
n8n import:workflow --input=D:/Project/n8n/workflows/daily-report-automation.json
```

### Configure Workflow Nodes

#### Gmail Node

1. Edit "Send Email (Gmail)" node
2. In Credentials dropdown: "Gmail OAuth (configured)"
3. If no credential exists:
   - Click "Create New"
   - Paste your `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`
   - Save
4. Set **To Email**: `{{$env.GMAIL_SENDER_EMAIL}}`
5. Test: Click "Execute"

#### Notion Node

1. Edit "Save to Notion" node
2. In Credentials dropdown: "Notion API (configured)"
3. If no credential exists:
   - Click "Create New"
   - Paste your `NOTION_API_KEY`
   - Save
4. Set **Database ID**: `{{$env.NOTION_DATABASE_ID}}`
5. Test: Click "Execute"

#### Telegram Node

1. Edit "Send to Telegram" node
2. In Credentials dropdown: "Telegram Bot (configured)"
3. If no credential exists:
   - Click "Create New"
   - Paste your `TELEGRAM_BOT_TOKEN`
   - Save
4. Set **Chat ID**: `{{$env.TELEGRAM_CHAT_ID}}`
5. Test: Click "Execute"

### Verify Schedules

Check that all 5 cron triggers are configured:

| Trigger | Time | Cron |
|---------|------|------|
| Morning Brief | 5 AM | `0 5 * * *` |
| Mid-Morning | 10 AM | `0 10 * * *` |
| Afternoon | 3 PM | `0 15 * * *` |
| Evening | 5 PM | `0 17 * * *` |
| Night | 10 PM | `0 22 * * *` |

All times in **Asia/Seoul** timezone.

---

## Testing

### Test 1: Manual Workflow Execution

1. Open n8n: http://localhost:5679
2. Open "Daily Report Automation" workflow
3. Click "Execute" button
4. Check outputs:
   - ✓ Generate Report Data - should show timestamp and report type
   - ✓ Send Email - should show success
   - ✓ Save to Notion - should show page creation
   - ✓ Send to Telegram - should show message ID

### Test 2: Check Email

Check your Gmail inbox for a test email with:
- Subject: Contains "Daily Report"
- Content: Shows greeting and status

### Test 3: Check Notion

Open Notion database and verify:
- New entry with today's date
- Report type is populated
- Status shows "OPERATIONAL"

### Test 4: Check Telegram

Open Telegram and verify:
- Bot sent you a message
- Message shows greeting
- Status is displayed

### Test 5: Scheduled Execution

Wait for next scheduled time (or adjust cron to test at a closer time):

```bash
# Test with 1-minute schedule (for testing)
# Edit cron in n8n UI: "* * * * *" = every minute
# After successful test, revert to original schedule
```

---

## Monitoring

### View Execution Logs

#### In n8n UI

1. Open workflow
2. Click "Execution History" tab
3. View all past runs with:
   - Status (success/error)
   - Duration
   - Execution time
   - Any error messages

#### In File System

```bash
# Check log files
tail -f D:/Project/logs/n8n/n8n.log

# View all executions
ls -la D:/Project/logs/n8n/
```

### Dashboard Setup

See `monitoring-dashboard.json` for Grafana integration.

### Health Checks

```bash
# Check n8n is running
curl http://localhost:5678/api/v1/health

# Check available workflows
curl http://localhost:5678/api/v1/workflows

# View execution stats
curl http://localhost:5678/api/v1/executions
```

---

## Troubleshooting

### Issue: "n8n command not found"

**Solution:**
```bash
# Install globally
npm install -g n8n

# Or use via npx
npx n8n start
```

### Issue: Port 5678 already in use

**Solution:**
```bash
# Find process using port
lsof -i :5678  # macOS/Linux
netstat -ano | findstr :5678  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
N8N_PORT=5680 n8n start
```

### Issue: Credentials not working

**Check:**
1. Environment variables loaded: `echo $GMAIL_CLIENT_ID`
2. Credentials file exists: `cat D:/Project/.env.n8n`
3. Run startup script again: `bash scripts/n8n-start.sh`

**Solution:**
```bash
# Reload environment
set -a
source .env.n8n
set +a

# Restart n8n
n8n start
```

### Issue: Gmail OAuth expired

**Solution:**
1. Get new refresh token (see Gmail Setup section)
2. Update `.env.n8n`
3. Delete old credential from n8n UI
4. Create new credential with updated token
5. Test "Send Email (Gmail)" node

### Issue: Notion database not found

**Check:**
1. Database ID is correct (copy from URL)
2. Integration has access (check "Shared" section)
3. Database properties match workflow requirements

**Solution:**
```bash
# Verify database ID format
# Should look like: 123456789abcdef123456789abcdef123

# Check integration access
# In Notion: Settings → Connections → Your n8n integration
```

### Issue: Telegram message not sending

**Check:**
1. Bot token is correct
2. Chat ID is correct
3. Bot has permission to send messages

**Solution:**
```bash
# Test bot manually
curl https://api.telegram.org/bot{TOKEN}/sendMessage \
  -d chat_id={CHAT_ID} \
  -d text="Test message"
```

### Issue: Workflow not executing at scheduled time

**Check:**
1. n8n is running: `curl http://localhost:5678/api/v1/health`
2. Queue worker is active (check logs)
3. Cron expression is valid: https://crontab.guru

**Solution:**
```bash
# Check if scheduler is running
curl http://localhost:5678/api/v1/workflows

# Look for 'active: true' on your workflow

# Manually trigger to test
curl -X POST http://localhost:5678/api/v1/workflows/{workflow_id}/execute
```

### Issue: High memory usage

**Solution:**
1. Reduce execution concurrency:
   ```
   WORKER_CONCURRENCY=2
   ```
2. Enable data pruning:
   ```
   EXECUTIONS_PRUNEDATA=true
   EXECUTIONS_PRUNEDATA_MAXAGE=604800
   ```
3. Restart n8n

### Issue: Logs not being written

**Solution:**
```bash
# Create log directory
mkdir -p D:/Project/logs/n8n

# Check permissions
chmod 755 D:/Project/logs/n8n

# Verify log location in .env.n8n
N8N_LOG_FILE_LOCATION=D:/Project/logs/n8n
```

---

## Advanced Configuration

### Enable Redis Queue

For high-volume workflows, use Redis:

```bash
# Install Redis
brew install redis  # macOS
apt-get install redis-server  # Linux

# Update .env.n8n
QUEUE_BULL_PORT=6379
QUEUE_BULL_HOST=localhost
QUEUE_BULL_DB=0
```

### Enable Prometheus Metrics

```bash
# Update .env.n8n
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# View metrics at http://localhost:9090
```

### Setup Sentry Error Tracking

```bash
# Get DSN from https://sentry.io
SENTRY_ENABLED=true
SENTRY_DSN=your_sentry_dsn_here
```

---

## Next Steps

1. ✅ Complete setup using this guide
2. ✅ Test workflow execution
3. ✅ Monitor logs and dashboards
4. ✅ Schedule production deployment
5. 📚 Read [n8n Documentation](https://docs.n8n.io)

---

## Support & Resources

| Resource | Link |
|----------|------|
| n8n Documentation | https://docs.n8n.io |
| API Reference | https://docs.n8n.io/api/ |
| Community Forum | https://community.n8n.io |
| GitHub Issues | https://github.com/n8n-io/n8n/issues |

---

**Setup Version:** 2.0
**Last Updated:** 2026-02-25
**Status:** Production Ready ✓