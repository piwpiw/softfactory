# 📘 SoftFactory Public Access Guide

> **Purpose**: **Version:** 1.0
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Public Access Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 1.0
**Updated:** 2026-02-25
**Status:** Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [ngrok Configuration](#ngrok-configuration)
4. [Fallback Access (localtunnel)](#fallback-access-localtunnel)
5. [URL Management](#url-management)
6. [Access Control & Whitelist](#access-control--whitelist)
7. [Monitoring & Logging](#monitoring--logging)
8. [Incident Response](#incident-response)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Start SoftFactory API Locally

```bash
cd D:/Project
python start_platform.py
# API running on http://localhost:8000
```

### 2. Start ngrok Tunnel (Primary Method)

```bash
# Terminal 1: Start the tunnel
cd D:/Project
bash scripts/ngrok-start.sh --monitor

# Expected output:
# SUCCESS [timestamp] ngrok started (PID: 12345)
# SUCCESS [timestamp] ngrok tunnel established successfully
# SUCCESS [timestamp] Public URL saved: https://abc123.ngrok.io
```

### 3. Get Public URL

```bash
# Option A: Check the log file
cat D:/Project/logs/ngrok-url.txt
# Output: https://abc123.ngrok.io

# Option B: Query the API
curl http://localhost:8000/api/public/url
# Output: {"public_url": "https://abc123.ngrok.io", "status": "active"}

# Option C: Check ngrok web interface
open http://127.0.0.1:4040
```

### 4. Test Public Access

```bash
# Get the public URL (from step 3)
export PUBLIC_URL="https://abc123.ngrok.io"

# Test API access
curl $PUBLIC_URL/health
# Output: {"status": "ok"}

# Test with authentication
curl -X POST $PUBLIC_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@softfactory.com", "password": "admin123"}'
```

### 5. Share Public URL with Users

- **Demo URL:** `https://abc123.ngrok.io`
- **Landing Page:** `https://abc123.ngrok.io/web/platform/index.html`
- **API Endpoint:** `https://abc123.ngrok.io/api/`
- **Web Inspector:** `http://127.0.0.1:4040` (for debugging)

---

## Architecture Overview

### Network Flow

```
┌─────────────────────────────────────────────────┐
│  Internet (Public)                              │
│  ┌─────────────────────────────────────────┐   │
│  │  User Browser                           │   │
│  │  curl $PUBLIC_URL                       │   │
│  └──────────┬──────────────────────────────┘   │
│             │ HTTPS (TLS 1.2+)                 │
│             │ (encrypted, tunneled)           │
└─────────────┼──────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  ngrok Server (SaaS)                            │
│  ┌─────────────────────────────────────────┐   │
│  │  https://abc123.ngrok.io                │   │
│  │  (load balancer, TLS termination)       │   │
│  └──────────┬──────────────────────────────┘   │
│             │ HTTP (unencrypted)               │
│             │ (secure local network)          │
└─────────────┼──────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Local Machine (Windows)                        │
│  ┌─────────────────────────────────────────┐   │
│  │  ngrok client (CLI)                     │   │
│  │  Port: 8000 ←──────────────────────┐    │   │
│  └──────────────────────────────────┬─┘    │   │
│             ▲                       │      │   │
│             │ HTTP                  ▼      │   │
│  ┌──────────┴───────────────────────────┐ │   │
│  │  Flask API (http://localhost:8000)  │ │   │
│  │  - backend/app.py                   │ │   │
│  │  - Services: CooCook, SNS, Review   │ │   │
│  │  - Database: platform.db            │ │   │
│  └─────────────────────────────────────┘ │   │
│  ┌─────────────────────────────────────┐ │   │
│  │  Monitoring                         │─┘   │
│  │  - Access Logger                    │     │
│  │  - URL Manager                      │     │
│  │  - Health Checks                    │     │
│  └─────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

### Components

1. **ngrok Client** (`scripts/ngrok-start.sh`)
   - Maintains encrypted tunnel to ngrok server
   - Auto-reconnects on failure
   - Health checks every 30 seconds
   - Max 5 reconnect attempts

2. **Public Access Handler** (`backend/public_access_handler.py`)
   - Manages public URL discovery
   - Enforces IP whitelist (optional)
   - Logs all access attempts
   - Provides CORS updates

3. **Access Monitor** (`monitoring/access_logging.py`)
   - Real-time request logging
   - Metrics aggregation (response times, error rates)
   - Incident detection (slow responses, repeated errors)
   - Historical analysis and reporting

4. **Fallback System** (`scripts/localtunnel-start.sh`)
   - Backup public access via localtunnel
   - Automatic failover support
   - Simpler setup, fewer features than ngrok

---

## ngrok Configuration

### Installation

```bash
# ngrok is already installed in the project environment
# Verify:
ngrok version
# Output: ngrok version 3.36.1

# If not installed, install via pip:
pip install pyngrok
# OR download from: https://ngrok.com/download
```

### Configuration File: `.ngrok.yml`

```yaml
version: "3"

tunnels:
  softfactory:
    proto: http
    addr: 8000
    bind-tls: true

authtoken: "" # Set via NGROK_AUTHTOKEN environment variable
web_addr: "127.0.0.1:4040"
api_addr: "127.0.0.1:4041"
```

### Setting Auth Token

```bash
# Option 1: Via environment variable (recommended)
export NGROK_AUTHTOKEN="<your_token_here>"
bash scripts/ngrok-start.sh

# Option 2: Via command line
bash scripts/ngrok-start.sh --authtoken "<your_token_here>"

# Option 3: Permanently (one-time setup)
ngrok authtoken "<your_token_here>"
# Stores token in ~/.ngrok2/ngrok.yml

# Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken
```

### Pro Plan Features (Optional)

If using ngrok Pro ($9/mo):

```bash
# Custom domain (static)
ngrok http 8000 --domain=softfactory.ngrok.io

# IP restrictions
ngrok http 8000 --ip-policy-add=1.2.3.4,5.6.7.8

# Reserved TCP addresses
ngrok tcp 3306 --reserved-addr=tcp.ngrok.io:25000
```

### Startup Options

```bash
# Monitoring mode (with auto-reconnect and health checks)
bash scripts/ngrok-start.sh --monitor

# Custom config file
bash scripts/ngrok-start.sh --config /path/to/.ngrok.yml

# With IP whitelist
bash scripts/ngrok-start.sh --ip-whitelist "1.2.3.4,5.6.7.8"

# With custom domain (Pro plan)
bash scripts/ngrok-start.sh --custom-domain softfactory.ngrok.io
```

### Web Inspector

Access the ngrok web inspector for real-time traffic inspection:

```
URL: http://127.0.0.1:4040

Features:
- View all HTTP/HTTPS requests
- Inspect headers, body, response
- Replay requests
- Mock responses
- View tunnels status
```

### API Endpoint

Query ngrok programmatically:

```bash
# Get tunnel information
curl http://127.0.0.1:4041/api/tunnels | jq

# Output:
{
  "tunnels": [
    {
      "name": "softfactory",
      "uri": "/api/tunnels/softfactory",
      "public_url": "https://abc123.ngrok.io",
      "proto": "http",
      "config": {
        "addr": "http://localhost:8000",
        "inspect": true
      },
      "metrics": {
        "conns": {...}
      }
    }
  ]
}
```

---

## Fallback Access (localtunnel)

### When to Use Fallback

- ngrok API rate limits exceeded (free tier: 20 tunnels/40h)
- ngrok service outage
- Need quick backup access
- Testing tunnel failover

### Installation

```bash
# localtunnel requires Node.js
# Check if installed:
node --version
npm --version

# Install localtunnel:
npm install -g localtunnel

# Verify:
lt --version
```

### Starting Fallback Tunnel

```bash
# Option 1: Automatic subdomain
bash scripts/localtunnel-start.sh
# Output: https://randomname.loca.lt

# Option 2: Custom subdomain
bash scripts/localtunnel-start.sh --subdomain softfactory-demo
# Output: https://softfactory-demo.loca.lt

# Option 3: Different port
bash scripts/localtunnel-start.sh --port 3000
```

### Differences from ngrok

| Feature | ngrok | localtunnel |
|---------|-------|-------------|
| Setup | 1 command | Requires Node.js |
| Web Inspector | Yes (http://127.0.0.1:4040) | No |
| Custom Domain | Pro plan | Free ✓ |
| Uptime SLA | 99.9% | Best effort |
| Features | Extensive | Basic |
| Speed | Fast | Slightly slower |
| Auth Token | Recommended | Not needed |

---

## URL Management

### Automatic URL Discovery

```python
# Python API
from backend.public_access_handler import get_access_manager

manager = get_access_manager()
public_url = manager.get_public_url(force_refresh=True)
# Returns: "https://abc123.ngrok.io" or None
```

### API Endpoints

#### Get Current Public URL

```bash
curl http://localhost:8000/api/public/url

# Response:
{
  "public_url": "https://abc123.ngrok.io",
  "local_url": "http://localhost:8000",
  "status": "active",
  "timestamp": "2026-02-25T18:33:00"
}
```

#### Get Access Statistics

```bash
curl http://localhost:8000/api/public/stats

# Response:
{
  "stats": {
    "total_requests": 234,
    "errors": 12,
    "ips": {"1.2.3.4": 50, "5.6.7.8": 40, ...},
    "paths": {"/api/": 100, "/web/": 134, ...},
    "status_codes": {"200": 200, "404": 20, "500": 14},
    "avg_response_time": 45.3,
    "last_24h": 156
  },
  "timestamp": "2026-02-25T18:33:00"
}
```

#### Get Recent Access Logs

```bash
curl "http://localhost:8000/api/public/logs?limit=50"

# Response:
{
  "logs": [
    {
      "timestamp": "2026-02-25T18:32:00",
      "client_ip": "1.2.3.4",
      "method": "GET",
      "path": "/api/health",
      "status": 200,
      "response_time_ms": 5.2,
      "whitelisted": true
    },
    ...
  ],
  "count": 50,
  "timestamp": "2026-02-25T18:33:00"
}
```

### Manual URL Update

```bash
# Update Flask CORS configuration with new URL
curl -X POST http://localhost:8000/api/admin/public-url-update \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://new-url.ngrok.io",
    "type": "ngrok"
  }'
```

### Automated Update Script

```bash
# Run periodically to sync URLs across systems
bash scripts/update-public-urls.sh

# With Telegram notifications:
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
bash scripts/update-public-urls.sh

# Output file: D:/Project/public-urls.json
```

---

## Access Control & Whitelist

### IP Whitelist Configuration

The whitelist is stored in `access_whitelist.json`:

```json
{
  "enabled": false,
  "ips": ["127.0.0.1", "::1", "1.2.3.4"],
  "updated_at": "2026-02-25T00:00:00"
}
```

### Enabling Whitelist

```python
# Via API
curl -X POST http://localhost:8000/api/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{
    "ips": ["1.2.3.4", "5.6.7.8", "192.168.1.0/24"],
    "enabled": true
  }'

# Via Python
from backend.public_access_handler import get_access_manager

manager = get_access_manager()
manager.save_whitelist(
    ips=["1.2.3.4", "5.6.7.8"],
    enabled=True
)
```

### Checking Whitelist Status

```bash
curl http://localhost:8000/api/admin/whitelist

# Response:
{
  "whitelist": {
    "enabled": true,
    "ips": ["1.2.3.4", "5.6.7.8"],
    "updated_at": "2026-02-25T18:00:00"
  },
  "timestamp": "2026-02-25T18:33:00"
}
```

### Using Whitelist in Routes

```python
from flask import Flask
from backend.public_access_handler import require_public_access, log_access_decorator

app = Flask(__name__)

@app.route('/api/public/data')
@require_public_access  # Enforce whitelist
@log_access_decorator   # Log the request
def get_public_data():
    return jsonify({'data': 'public'})
```

---

## Monitoring & Logging

### Access Log Files

```
D:/Project/logs/
├── ngrok.log                 # ngrok tunnel logs
├── ngrok-url.txt             # Current ngrok URL
├── localtunnel.log           # localtunnel tunnel logs
├── localtunnel-url.txt       # Current localtunnel URL
├── access.log                # Public access log (JSON lines)
├── access_detailed.jsonl     # Detailed access entries
├── metrics.json              # Aggregated metrics
├── incidents.jsonl           # Detected incidents
└── url-updates.log           # URL update history
```

### Real-Time Monitoring

```bash
# Monitor ngrok tunnel
tail -f D:/Project/logs/ngrok.log

# Monitor access requests
tail -f D:/Project/logs/access.log | jq

# Monitor incidents
tail -f D:/Project/logs/incidents.jsonl | jq
```

### Access Log Entry Format

```json
{
  "timestamp": "2026-02-25T18:32:00.123456",
  "client_ip": "1.2.3.4",
  "method": "GET",
  "path": "/api/public/data",
  "status_code": 200,
  "response_time_ms": 45.3,
  "request_size_bytes": 256,
  "response_size_bytes": 1024,
  "access_level": "public",
  "user_agent": "Mozilla/5.0...",
  "referer": "https://example.com",
  "error": null,
  "whitelisted": true,
  "authenticated": false,
  "user_id": null,
  "session_id": null
}
```

### Monitoring API

```python
from monitoring.access_logging import get_monitor

monitor = get_monitor()

# Get summary metrics
summary = monitor.get_metrics_summary()
print(f"Total requests: {summary['total_requests']}")
print(f"Error rate: {summary['error_rate']*100:.1f}%")
print(f"P95 response time: {summary['p95_response_time_ms']:.1f}ms")

# Get top endpoints
endpoints = monitor.get_top_endpoints(limit=10)
for ep in endpoints:
    print(f"{ep['endpoint']}: {ep['requests']} requests")

# Get recent incidents
incidents = monitor.get_incidents(limit=5)
for incident in incidents:
    print(f"Incident: {incident}")

# Generate report
report = monitor.generate_report()
print(report)
```

### Metrics Dashboard

Access a real-time metrics dashboard:

```bash
# View ngrok web inspector
open http://127.0.0.1:4040

# View Flask health
curl http://localhost:8000/api/public/stats | jq

# View detailed metrics file
cat D:/Project/logs/metrics.json | jq
```

---

## Incident Response

### Common Incidents Detected

1. **SLOW_RESPONSE** — Response time > 5000ms
2. **SERVER_ERROR** — 5xx status codes
3. **REPEATED_CLIENT_ERRORS** — >10 4xx errors from same IP
4. **RATE_LIMIT_EXCEEDED** — >100 requests/minute from same IP
5. **TUNNEL_DOWN** — ngrok process not responding

### Automated Alerts

Alerts are triggered when:
- ngrok tunnel disconnects
- API response time exceeds 5 seconds
- Error rate exceeds 5% in 1 minute window
- Same IP makes >10 requests in 1 minute

### Manual Incident Investigation

```bash
# Check recent logs
tail -100 D:/Project/logs/access_detailed.jsonl | jq

# Filter by IP
cat D:/Project/logs/access_detailed.jsonl | jq 'select(.client_ip=="1.2.3.4")'

# Filter by status code
cat D:/Project/logs/access_detailed.jsonl | jq 'select(.status_code>=500)'

# Count errors in last hour
cat D:/Project/logs/access_detailed.jsonl | \
  jq 'select(.timestamp > now - 3600)' | \
  jq -s 'map(select(.status_code>=400)) | length'
```

### Emergency Procedures

**If ngrok tunnel is down:**

```bash
# Check ngrok process
ps aux | grep ngrok

# Restart tunnel
bash D:/Project/scripts/ngrok-start.sh --monitor

# Verify health
curl http://localhost:8000/health
```

**If API is responding slowly:**

```bash
# Check Flask logs
tail -50 D:/Project/logs/ngrok.log

# Check database
python -c "from backend.models import db, User; print(User.query.count())"

# Restart API
pkill -f "start_platform.py"
python D:/Project/start_platform.py
```

**If whitelist is blocking legitimate traffic:**

```bash
# Temporarily disable whitelist
curl -X POST http://localhost:8000/api/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "ips": []}'

# Or add the blocked IP
curl -X POST http://localhost:8000/api/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "ips": ["1.2.3.4"]}'
```

---

## Security Considerations

### Tunnel Security

1. **TLS Encryption**
   - ngrok uses TLS 1.2+ for all traffic
   - Traffic from user → ngrok server is encrypted
   - Local traffic (ngrok ↔ Flask) is unencrypted (isolated network)

2. **Authentication**
   - Use ngrok auth token to prevent URL hijacking
   - Auth token restricts tunnel creation to your account

3. **IP Whitelist**
   - Enable for sensitive environments
   - Restrict access to known IPs only
   - Review and update whitelist quarterly

### Best Practices

```bash
# 1. Never commit auth tokens to git
echo "NGROK_AUTHTOKEN=..." >> .env
# Ensure .env is in .gitignore

# 2. Use environment variables
export NGROK_AUTHTOKEN="..."
bash scripts/ngrok-start.sh

# 3. Rotate auth tokens regularly
# https://dashboard.ngrok.com/auth → Auth Tokens

# 4. Monitor access logs
tail -f D:/Project/logs/access.log

# 5. Set up alerts for anomalies
# See Monitoring & Logging section

# 6. Use HTTPS only (ngrok handles this)
# http://localhost:8000 → https://abc123.ngrok.io

# 7. Disable public access in production
# Disable ngrok tunnel
# Use private VPN instead
```

### Sensitive Data

```python
# Don't log sensitive data
LOG_MASK_PATTERNS = [
    'password',
    'token',
    'api_key',
    'secret',
    'credit_card'
]

# Access logs exclude:
# - Request/response bodies (headers only)
# - Authentication tokens
# - User credentials
# - Database passwords
```

---

## Troubleshooting

### ngrok Tunnel Won't Start

**Error: "Cannot login: 401 unauthorized"**

```bash
# Solution: Auth token is invalid
# Get valid token from: https://dashboard.ngrok.com/get-started/your-authtoken
export NGROK_AUTHTOKEN="<your_token>"
bash scripts/ngrok-start.sh
```

**Error: "Address already in use"**

```bash
# Solution: Port 8000 is already in use
# Find process using port 8000:
lsof -i :8000

# Kill process:
kill -9 <PID>

# Or use different port in .ngrok.yml:
# addr: 3000  # instead of 8000
```

**Error: "ngrok command not found"**

```bash
# Solution: ngrok is not in PATH
# Install ngrok:
pip install pyngrok
# OR download from: https://ngrok.com/download

# Or use full path:
/c/Users/piwpi/AppData/Local/Programs/Python/Python311/Scripts/ngrok start softfactory
```

### Public URL Not Accessible

**Symptom: "Connection timeout" when accessing public URL**

```bash
# 1. Check Flask is running
curl http://localhost:8000/health

# 2. Check ngrok tunnel is active
curl http://127.0.0.1:4040/api/tunnels | jq

# 3. Check public URL is correct
cat D:/Project/logs/ngrok-url.txt

# 4. Check for firewall issues
# Windows Firewall may block ngrok
# Allow Python.exe in Firewall settings
```

### Access Logs Not Recording

**Symptom: access.log file not created or empty**

```bash
# 1. Check if logging is enabled
curl http://localhost:8000/api/public/stats

# 2. Check log directory permissions
ls -la D:/Project/logs/

# 3. Manually enable logging
python -c "from backend.public_access_handler import get_access_manager; m = get_access_manager(); m.enable_logging = True"
```

### High Response Times

**Symptom: Response time > 1000ms**

```bash
# 1. Check metrics
curl http://localhost:8000/api/public/stats | jq .stats.avg_response_time_ms

# 2. Check for bottleneck
python -c "from backend.models import db, User; import time; start = time.time(); User.query.count(); print(f'{(time.time()-start)*1000:.1f}ms')"

# 3. Check network latency
# ngrok adds ~50-200ms latency
# Expected: local 5-50ms + ngrok 50-200ms = 55-250ms total
```

### Whitelist Blocking Legitimate Traffic

**Symptom: 403 Forbidden for known IP**

```bash
# 1. Check current whitelist
curl http://localhost:8000/api/admin/whitelist

# 2. Add IP to whitelist
curl -X POST http://localhost:8000/api/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "ips": ["1.2.3.4"]}'

# 3. Verify
curl -H "X-Forwarded-For: 1.2.3.4" http://localhost:8000/api/public/url
```

### Fallback Tunnel (localtunnel) Won't Start

**Error: "localtunnel (lt) is not installed"**

```bash
# Solution: Install localtunnel via npm
npm install -g localtunnel

# Verify:
lt --version
```

**Error: "Subdomain already taken"**

```bash
# Solution: Use different subdomain
bash scripts/localtunnel-start.sh --subdomain softfactory-backup-$(date +%s)
```

---

## Quick Reference

### Common Commands

```bash
# Start tunnel (primary)
bash D:/Project/scripts/ngrok-start.sh --monitor

# Start fallback tunnel
bash D:/Project/scripts/localtunnel-start.sh

# Get public URL
cat D:/Project/logs/ngrok-url.txt

# Update all URLs
bash D:/Project/scripts/update-public-urls.sh

# View access logs
tail -100 D:/Project/logs/access.log | jq

# View metrics
curl http://localhost:8000/api/public/stats | jq

# Enable IP whitelist
curl -X POST http://localhost:8000/api/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "ips": ["1.2.3.4"]}'

# View ngrok inspector
open http://127.0.0.1:4040

# Test API
curl https://abc123.ngrok.io/health
```

### Environment Variables

```bash
# Required
export NGROK_AUTHTOKEN="your_token_here"

# Optional
export TELEGRAM_BOT_TOKEN="bot_token"
export TELEGRAM_CHAT_ID="chat_id"
export PUBLIC_URL_WEBHOOK="https://webhook.url"
export NGROK_CUSTOM_DOMAIN="your.domain.ngrok.io"
```

### File Locations

| File | Purpose |
|------|---------|
| `.ngrok.yml` | ngrok configuration |
| `access_whitelist.json` | IP whitelist |
| `public-urls.json` | Current public URLs |
| `logs/ngrok.log` | ngrok tunnel logs |
| `logs/ngrok-url.txt` | Current ngrok URL |
| `logs/access.log` | Access request log |
| `logs/metrics.json` | Aggregated metrics |
| `logs/incidents.jsonl` | Detected incidents |

---

## Next Steps

1. **Start the tunnel:** `bash scripts/ngrok-start.sh --monitor`
2. **Share the public URL:** Send from `logs/ngrok-url.txt`
3. **Monitor access:** `curl http://localhost:8000/api/public/stats`
4. **Set up alerts:** Configure Telegram notifications (see env vars)
5. **Review security:** Enable IP whitelist for sensitive data

---

## Support & Resources

- **ngrok Documentation:** https://ngrok.com/docs
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **localtunnel Repo:** https://github.com/localtunnel/localtunnel
- **Flask CORS:** https://flask-cors.readthedocs.io
- **SoftFactory Issues:** `shared-intelligence/incidents.jsonl`

---

**Document Version:** 1.0 (2026-02-25)
**Maintained By:** DevOps
**Last Review:** 2026-02-25
**Next Review:** 2026-03-25