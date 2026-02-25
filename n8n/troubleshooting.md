# n8n Troubleshooting & Debugging Guide

**Status:** Complete
**Last Updated:** 2026-02-25
**Version:** 1.0

---

## Quick Diagnosis

### Test 1: Is n8n running?

```bash
# Check if process is active
curl http://localhost:5678/api/v1/health

# Expected response:
# {"status":"ok"}
```

### Test 2: Can you access the UI?

```bash
# Open in browser
http://localhost:5679

# Should show login page or workflows list
```

### Test 3: Are credentials configured?

```bash
# In n8n UI: Settings → Credentials
# Should see:
# ✓ Gmail OAuth
# ✓ Notion API
# ✓ Telegram Bot
```

---

## Common Issues & Solutions

### Category A: Installation & Startup

#### A1: "command not found: n8n"

**Symptoms:**
```
bash: n8n: command not found
```

**Cause:** n8n not installed or not in PATH

**Solutions:**

```bash
# Solution 1: Install globally
npm install -g n8n

# Solution 2: Check npm installation path
npm config get prefix
# Should return something like /usr/local/

# Solution 3: Use npx to run directly
npx n8n start

# Solution 4: Verify PATH includes npm binaries
echo $PATH | grep -i npm
```

---

#### A2: "Port 5678 already in use"

**Symptoms:**
```
Server is already running on port 5678
Error: listen EADDRINUSE: address already in use :::5678
```

**Cause:** Another process using the port

**Solutions:**

```bash
# Solution 1: Find and kill process
# On macOS/Linux:
lsof -i :5678
kill -9 <PID>

# On Windows (PowerShell):
netstat -ano | findstr :5678
taskkill /PID <PID> /F

# Solution 2: Use different port
N8N_PORT=5680 n8n start

# Solution 3: Wait a bit (port may need time to release)
sleep 30 && n8n start
```

---

#### A3: "Cannot find module" error

**Symptoms:**
```
Cannot find module 'n8n-core'
Error: MODULE_NOT_FOUND
```

**Cause:** Incomplete npm installation

**Solutions:**

```bash
# Solution 1: Reinstall npm packages
npm install -g n8n --force

# Solution 2: Clear npm cache
npm cache clean --force

# Solution 3: Delete n8n and reinstall
npm uninstall -g n8n
npm install -g n8n

# Solution 4: Check Node version
node --version
# Should be v18+
```

---

#### A4: "ENOENT: no such file or directory"

**Symptoms:**
```
ENOENT: no such file or directory, open 'D:\Project\.n8n\database.sqlite'
```

**Cause:** Missing directories

**Solutions:**

```bash
# Solution 1: Create directories manually
mkdir -p D:/Project/.n8n
mkdir -p D:/Project/logs/n8n

# Solution 2: Run startup script
bash scripts/n8n-start.sh

# Solution 3: Check permissions
# Ensure you have write permission to D:/Project/
chmod -R 755 D:/Project/.n8n
```

---

### Category B: Environment & Credentials

#### B1: Credentials not loading

**Symptoms:**
```
Environment variable GMAIL_CLIENT_ID is undefined
Credentials not found in n8n UI
```

**Cause:** .env.n8n file not loaded or not found

**Solutions:**

```bash
# Solution 1: Verify .env.n8n exists
ls -la D:/Project/.env.n8n

# Solution 2: Load environment manually
set -a
source D:/Project/.env.n8n
set +a

# Verify loaded:
echo $GMAIL_CLIENT_ID

# Solution 3: Use absolute path
export ENV_FILE=/d/Project/.env.n8n
source $ENV_FILE

# Solution 4: Check file permissions
chmod 600 D:/Project/.env.n8n
```

---

#### B2: "Invalid credentials" error in workflow

**Symptoms:**
```
Gmail: Invalid authentication
Notion: Unauthorized
Telegram: Bot token invalid
```

**Cause:** Credentials configured incorrectly in n8n

**Solutions:**

```bash
# Solution 1: Delete and recreate credentials
# In n8n UI:
# Settings → Credentials → [Select credential]
# Delete and create new one from scratch

# Solution 2: Verify credential values
echo $GMAIL_CLIENT_ID
echo $NOTION_API_KEY
echo $TELEGRAM_BOT_TOKEN

# Solution 3: Test credentials manually
# For Gmail:
curl https://www.googleapis.com/oauth2/v1/userinfo?access_token={TOKEN}

# For Telegram:
curl https://api.telegram.org/bot{TOKEN}/getMe

# For Notion:
curl -H "Authorization: Bearer {KEY}" \
  https://api.notion.com/v1/users/me
```

---

#### B3: "NOTION_DATABASE_ID not found"

**Symptoms:**
```
Notion: Could not find database ID
Error: 404 Not Found
```

**Cause:** Wrong database ID or integration doesn't have access

**Solutions:**

```bash
# Solution 1: Verify database ID format
# Correct format: 123456789abcdef123456789abcdef123
# From URL: https://notion.so/workspace/123456789abcdef123456789abcdef123
# Remove hyphens!

# Solution 2: Check integration access
# In Notion:
# Settings & Members → Connections → Find your integration
# Check it has access to the database

# Solution 3: Reshare database
# In Notion: Database → Share → Add integration
# Copy database ID again (without hyphens)

# Solution 4: Verify API key
echo $NOTION_API_KEY
# Should start with: ntn_
```

---

#### B4: Gmail OAuth token expired

**Symptoms:**
```
Gmail: Invalid refresh token
Error: invalid_grant
```

**Cause:** Refresh token expired or revoked

**Solutions:**

```bash
# Solution 1: Get new refresh token
# Follow: n8n/setup-guide.md section "Get Gmail Refresh Token"

# Solution 2: Revoke and redo OAuth
# Visit: https://myaccount.google.com/permissions
# Find and revoke n8n access
# Re-authenticate in n8n credentials setup

# Solution 3: Update .env.n8n
# Add new: GMAIL_REFRESH_TOKEN=new_token_here
# Delete old credential from n8n UI
# Create new credential

# Solution 4: Check expiration manually
# In the credential response, should have:
# "expires_in": 3600
```

---

### Category C: Workflow Execution

#### C1: Workflow doesn't execute on schedule

**Symptoms:**
```
Workflow not running at scheduled time
No executions in history
```

**Cause:** Scheduler not active or cron expression wrong

**Solutions:**

```bash
# Solution 1: Check scheduler status
curl http://localhost:5678/api/v1/workflows

# Look for: "active": true

# Solution 2: Verify cron expression
# Visit: https://crontab.guru
# Test your cron: "0 5 * * *"
# Should show: "At 05:00"

# Solution 3: Check queue worker
# In logs, look for: "Queue processor started"
# If missing, restart n8n with queue enabled

# Solution 4: Manually trigger to test
curl -X POST http://localhost:5678/api/v1/workflows/{workflow_id}/execute

# Get workflow_id from:
curl http://localhost:5678/api/v1/workflows
```

---

#### C2: Workflow execution fails silently

**Symptoms:**
```
Workflow shows as executed but no email/Notion/Telegram
Execution history shows "error_state"
```

**Cause:** Error in node execution

**Solutions:**

```bash
# Solution 1: Check execution details
# In n8n UI: Workflow → Execution History
# Click failed execution
# Expand error node to see error message

# Solution 2: View logs
tail -f D:/Project/logs/n8n/n8n.log

# Solution 3: Test individual nodes
# In workflow editor:
# Right-click node → Execute
# See which node is failing

# Solution 4: Check error handlers
# In workflow editor:
# Each node should have "Continue on Error" option
# This prevents workflow from stopping
```

---

#### C3: Email not sending (Gmail node)

**Symptoms:**
```
Gmail node executes but no email received
No error message in logs
```

**Cause:** Email configuration or sending issues

**Solutions:**

```bash
# Solution 1: Check Gmail allows this
# In your Gmail account:
# Settings → Security → Less secure app access
# Should be enabled OR use OAuth (which we do)

# Solution 2: Verify sender email
echo $GMAIL_SENDER_EMAIL
# Should be valid Gmail address

# Solution 3: Test Gmail API directly
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
  https://www.googleapis.com/gmail/v1/users/me/messages/send \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"raw":"..."}'

# Solution 4: Check email logs
# In Gmail: Settings → Logs
# Search for failed sends

# Solution 5: Verify recipient
# Check "To" field in node
# Should be valid email address
```

---

#### C4: Notion save fails

**Symptoms:**
```
Notion node shows error
Database not updated
Error: "Could not create page"
```

**Cause:** Database schema mismatch or permission issues

**Solutions:**

```bash
# Solution 1: Verify database properties
# In Notion, database should have:
# - Title (title field)
# - Date (date field)
# - Report_Type (select field)
# - Time (text field)
# - Status (select field)

# Solution 2: Check property names match exactly
# Case-sensitive! "Report_Type" not "report_type"

# Solution 3: Verify integration access
# In Notion: Database → Share → Check integration listed

# Solution 4: Test Notion API directly
curl -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer {API_KEY}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Solution 5: Check property format
# Notion expects specific formats for each property type
# Verify in n8n node: propertyKeyValuePairs
```

---

#### C5: Telegram message not sending

**Symptoms:**
```
Telegram node executes with no error
No message in chat
Bot offline
```

**Cause:** Bot token invalid or chat ID wrong

**Solutions:**

```bash
# Solution 1: Verify bot is active
curl https://api.telegram.org/bot{TOKEN}/getMe

# Response should show bot info

# Solution 2: Check chat ID
echo $TELEGRAM_CHAT_ID

# Solution 3: Test message send
curl -X POST https://api.telegram.org/bot{TOKEN}/sendMessage \
  -d chat_id={CHAT_ID} \
  -d text="Test message"

# Solution 4: Verify bot can message you
# In Telegram: Message bot first
# Then try sending in n8n

# Solution 5: Check allowed users
# Verify TELEGRAM_ALLOWED_USERS includes your ID
TELEGRAM_ALLOWED_USERS=7910169750

# Solution 6: Check message format
# Telegram has character limits and markdown rules
# Plain text safer than formatted
```

---

### Category D: Performance & Resource Issues

#### D1: High memory usage

**Symptoms:**
```
n8n process using >1GB RAM
System slow when n8n running
```

**Cause:** Too many concurrent executions or memory leak

**Solutions:**

```bash
# Solution 1: Reduce concurrency
# In .env.n8n:
WORKER_CONCURRENCY=2

# Solution 2: Enable execution data pruning
EXECUTIONS_PRUNEDATA=true
EXECUTIONS_PRUNEDATA_MAXAGE=604800

# Solution 3: Restart n8n regularly
# Create cron job:
# 0 2 * * * killall n8n && sleep 5 && n8n start

# Solution 4: Monitor memory
# Linux/Mac:
watch -n 1 'ps aux | grep n8n'

# Windows PowerShell:
Get-Process n8n | Format-Table -Property Name, WorkingSet
```

---

#### D2: Slow workflow execution

**Symptoms:**
```
Workflow taking minutes instead of seconds
Timeouts occurring
```

**Cause:** Network delays, slow APIs, or queue congestion

**Solutions:**

```bash
# Solution 1: Check API response times
# In node: Parameters → Advanced → Request timeout
# Increase from 30s to 60s if needed

# Solution 2: Optimize code nodes
# Reduce complexity, use efficient logic

# Solution 3: Parallel execution
# Instead of sequential, run nodes in parallel
# In workflow: Connect multiple nodes to same source

# Solution 4: Use queue processing
# In .env.n8n:
EXECUTIONS_MODE=queue
QUEUE_BULL_PORT=6379

# Solution 5: Check network
ping api.example.com
# Response time should be <100ms
```

---

#### D3: Database getting too large

**Symptoms:**
```
.n8n/database.sqlite > 1GB
Queries getting slow
```

**Cause:** Too many execution records

**Solutions:**

```bash
# Solution 1: Enable auto-pruning
# In .env.n8n:
EXECUTIONS_PRUNEDATA=true
EXECUTIONS_PRUNEDATA_MAXAGE=604800  # 7 days
EXECUTIONS_PRUNEDATA_SOFTDELETE=true

# Solution 2: Manual cleanup
# Stop n8n
n8n stop

# Backup database
cp D:/Project/.n8n/database.sqlite D:/Project/.n8n/database.sqlite.bak

# Restart and let pruning run
n8n start

# Solution 3: Reduce save frequency
# In workflow node parameters:
# Save execution data: Only on error

# Solution 4: Archive old data
# Export executions older than 30 days
# Delete from database
```

---

### Category E: Data & Integration

#### E1: Report data formatting issues

**Symptoms:**
```
Email shows broken formatting
Notion database shows [object Object]
Telegram shows raw JSON
```

**Cause:** Incorrect data transformation in nodes

**Solutions:**

```bash
# Solution 1: Check Code node output
# In workflow: Edit "Generate Report Data" node
# Verify returned JSON structure matches expectation

// Correct format:
{
  "timestamp": "2026-02-25T10:30:00Z",
  "reportType": "morning_brief",
  "greeting": "Good Morning!"
}

# Solution 2: Fix Gmail formatting
# In Gmail node:
# Use HTML formatting instead of plain text
# Wrap in <html><body>...</body></html>

# Solution 3: Fix Notion formatting
# Notion requires specific formats:
# Text: plain string
# Date: ISO 8601 format
# Select: string matching option name

# Solution 4: Test transformation in Code node
# In n8n editor:
# Click Code node → Test Code
# See actual output
```

---

#### E2: Missing data in reports

**Symptoms:**
```
Report shows "undefined"
Fields empty or null
Data not fetched from API
```

**Cause:** API call failing or data path wrong

**Solutions:**

```bash
# Solution 1: Test API endpoint directly
curl -H "Authorization: Bearer demo_token" \
  http://localhost:8000/api/reports/daily

# Should return JSON with data

# Solution 2: Check node data paths
# In workflow: Click "Fetch Report Data" node
# Verify URL: http://localhost:8000/api/reports/daily
# Check headers include Authorization

# Solution 3: Verify API is running
curl http://localhost:8000/api/health

# Should return: {"status":"ok"}

# Solution 4: Check response mapping
# In HTTP Request node:
# Response body should contain data
# Not wrapped in extra object

# Solution 5: Use JSONata to extract data
# If API returns: {"result": {...}}
# Use: $node["Fetch Report Data"].json.result
```

---

### Category F: Logging & Debugging

#### F1: No logs appearing

**Symptoms:**
```
Log files empty or not created
No visibility into execution
```

**Cause:** Logging not configured or disabled

**Solutions:**

```bash
# Solution 1: Enable logging
# In .env.n8n:
N8N_LOG_LEVEL=info
N8N_LOG_OUTPUT=file,console

# Solution 2: Create log directory
mkdir -p D:/Project/logs/n8n
chmod 755 D:/Project/logs/n8n

# Solution 3: Set log path
# In .env.n8n:
N8N_LOG_FILE_LOCATION=D:/Project/logs/n8n

# Solution 4: View real-time logs
tail -f D:/Project/logs/n8n/n8n.log

# Solution 5: Check permissions
# Make sure process can write to log directory
chmod 755 D:/Project/logs/
chmod 755 D:/Project/logs/n8n
```

---

#### F2: Logs too verbose

**Symptoms:**
```
Log files growing too fast
Disk space issues
Hard to find actual errors
```

**Cause:** Log level set to DEBUG

**Solutions:**

```bash
# Solution 1: Change log level
# In .env.n8n:
N8N_LOG_LEVEL=warn  # or error

# Solution 2: Rotate logs
# Add to crontab:
# 0 0 * * * gzip D:/Project/logs/n8n/n8n.log

# Solution 3: Limit log retention
# In .env.n8n:
N8N_LOG_FILE_RETENTION=7  # days

# Solution 4: Use structured logging
# Pipe logs to file with rotation:
# n8n start 2>&1 | rotatelogs D:/Project/logs/n8n/n8n.%Y%m%d.log 86400
```

---

#### F3: Can't find error in logs

**Symptoms:**
```
Know something failed but can't find error message
Logs have thousands of lines
```

**Cause:** Error buried in logs

**Solutions:**

```bash
# Solution 1: Filter logs
grep -i "error" D:/Project/logs/n8n/n8n.log
grep -i "fail" D:/Project/logs/n8n/n8n.log
grep "ERR" D:/Project/logs/n8n/n8n.log

# Solution 2: Show recent errors with context
tail -200 D:/Project/logs/n8n/n8n.log | grep -i "error" -A 5 -B 5

# Solution 3: Check specific time period
# Convert execution timestamp to search logs
grep "2026-02-25 10:30" D:/Project/logs/n8n/n8n.log

# Solution 4: Use execution history
# In n8n UI: Workflow → Execution History
# Filter by status: "error"
# Click to see full error trace

# Solution 5: Enable debug logging temporarily
N8N_LOG_LEVEL=debug n8n start
# Run problematic workflow
# Stop and review logs
```

---

## Diagnostic Commands

### Check n8n Status

```bash
# Is process running?
ps aux | grep n8n

# Is port listening?
netstat -an | grep 5678
lsof -i :5678

# Health check
curl http://localhost:5678/api/v1/health

# Get version
n8n --version
```

### Check Environment

```bash
# Print all n8n env vars
env | grep N8N_

# Check critical variables
echo "GMAIL: $GMAIL_CLIENT_ID"
echo "NOTION: $NOTION_API_KEY"
echo "TELEGRAM: $TELEGRAM_BOT_TOKEN"

# Test file access
test -r D:/Project/.env.n8n && echo "Can read .env.n8n"
test -w D:/Project/logs/n8n && echo "Can write to logs"
```

### Test Credentials

```bash
# Gmail
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
  https://www.googleapis.com/gmail/v1/users/me/profile

# Notion
curl -H "Authorization: Bearer {API_KEY}" \
  -H "Notion-Version: 2022-06-28" \
  https://api.notion.com/v1/users/me

# Telegram
curl https://api.telegram.org/bot{TOKEN}/getMe
```

---

## Prevention Checklist

- [ ] Regular backups of database.sqlite
- [ ] Monitor disk space usage
- [ ] Check logs weekly
- [ ] Test workflows monthly
- [ ] Update n8n regularly
- [ ] Rotate credentials periodically
- [ ] Keep .env.n8n secure (not in git)
- [ ] Enable execution pruning
- [ ] Monitor resource usage

---

## Getting Help

If issue persists:

1. **Collect diagnostics:**
   ```bash
   n8n --version
   node --version
   npm --version
   tail -50 D:/Project/logs/n8n/n8n.log
   ```

2. **Check resources:**
   - [n8n Docs](https://docs.n8n.io)
   - [Community Forum](https://community.n8n.io)
   - [GitHub Issues](https://github.com/n8n-io/n8n/issues)

3. **Create issue with:**
   - n8n version
   - Node.js version
   - Steps to reproduce
   - Error logs
   - Expected vs actual behavior

---

**Last Updated:** 2026-02-25
**Version:** 1.0
**Status:** Complete
