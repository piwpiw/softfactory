# SoftFactory External Network Access Setup

**Status:** Platform running at localhost:8000
**Goal:** Make the platform accessible from external networks (home, office, internet)
**Last Updated:** 2026-02-25 16:56 KST

---

## 🟢 Option 1: ngrok (Recommended for Quick Setup)

### Prerequisites
- ngrok CLI installed ✅ (already at `C:/Users/piwpi/AppData/Local/Programs/Python/Python311/Scripts/ngrok`)
- Free ngrok account (https://dashboard.ngrok.com)

### Quick Setup (2 minutes)

**Step 1: Get your authtoken**
```bash
# Visit: https://dashboard.ngrok.com/get-started/your-authtoken
# Copy your authtoken (looks like: 8a_abcdefghijklmnop1234567890)
```

**Step 2: Configure ngrok**
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

**Step 3: Start the tunnel**
```bash
cd D:/Project
ngrok http 8000
```

**Expected output:**
```
Session Status                online
Session Expires               2 hours, 59 minutes
Update Status                 update available (version 3.x.x > 3.x.x)
Version                       3.x.x
Region                        jp (Japan)
Latency                        45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxxx-xxxx-xxxx.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p95
                              0       0       0.00    0.00    0.00    0.00
```

**Step 4: Share the public URL**
```
Your public URL: https://xxxx-xxxx-xxxx-xxxx.ngrok.io
Anyone can access: https://xxxx-xxxx-xxxx-xxxx.ngrok.io/
```

### Free Tier Limitations
- Session expires in 2 hours (restart needed)
- Shares the same URL for all sessions
- TCP traffic included
- 20 concurrent connections per account

### Pro Tier (Optional)
- $10/month for persistent URLs
- Higher connection limits
- Custom domains available

---

## 🟡 Option 2: LocalTunnel (No Account Required)

### Quick Setup (1 minute)

**Step 1: Install localtunnel**
```bash
npm install -g localtunnel
```

**Step 2: Start tunnel**
```bash
lt --port 8000 --subdomain softfactory-demo
```

**Expected output:**
```
your url is: https://softfactory-demo.loca.lt
```

### Advantages
- ✅ No account needed
- ✅ Instant setup
- ✅ Works well for demos
- ✅ Custom subdomain option

### Limitations
- ⚠️ URL may change on restart
- ⚠️ Requires npm/Node.js
- ⚠️ Fewer reliability guarantees

---

## 🔵 Option 3: Cloudflare Tunnel (Most Secure)

### Prerequisites
- Cloudflare account (free)
- Cloudflare CLI (cloudflared)

### Quick Setup (5 minutes)

**Step 1: Install cloudflared**
```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-and-setup/installation/
# Or via Chocolatey:
choco install cloudflare-warp
```

**Step 2: Authenticate**
```bash
cloudflared tunnel login
```

**Step 3: Create tunnel**
```bash
cloudflared tunnel create softfactory
```

**Step 4: Configure tunnel**
```bash
# Create ~/.cloudflared/config.yml:
tunnel: softfactory
credentials-file: C:\Users\piwpi\.cloudflared\softfactory.json

ingress:
  - hostname: softfactory.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

**Step 5: Start tunnel**
```bash
cloudflared tunnel run softfactory
```

### Advantages
- ✅ Most secure (DDoS protection)
- ✅ Own domain support
- ✅ Enterprise-grade reliability
- ✅ Free tier available

---

## 🟠 Option 4: SSH Reverse Tunnel (If You Have Linux Server)

If you have a Linux VPS or server:

```bash
# On your Windows machine:
ssh -R 8000:localhost:8000 user@your-server.com

# Then access via: http://your-server.com:8000
```

### Advantages
- ✅ Complete control
- ✅ Persistent URL
- ✅ Custom ports

### Limitations
- ⚠️ Requires external server
- ⚠️ More complex setup

---

## ⚫ Option 5: Self-Hosted Reverse Proxy (Advanced)

If hosting on your own infrastructure:

**Using nginx:**
```nginx
server {
    listen 80;
    server_name softfactory.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Using Caddy (simpler):**
```
softfactory.yourdomain.com {
    reverse_proxy localhost:8000
}
```

---

## 📊 Comparison Table

| Feature | ngrok | LocalTunnel | Cloudflare | SSH | Self-Hosted |
|---------|-------|-------------|-----------|-----|------------|
| Setup Time | 2 min | 1 min | 5 min | 10 min | 30+ min |
| Account Required | Yes (free) | No | Yes (free) | No | No |
| Persistent URL | Pro tier | Optional | Yes | Yes | Yes |
| Security | Good | Fair | Excellent | Good | Depends |
| Uptime SLA | Good | Fair | Excellent | ⚠️ SSH fragile | Depends |
| Cost | $0-10/mo | Free | Free-Pro | Free | Free (your server) |
| Best For | Quick demos | Temporary access | Production | Hacky workaround | Enterprise |

---

## 🔒 Security Considerations

### For Public Access:
1. **Add basic auth** to Flask (optional):
   ```python
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()

   @auth.verify_password
   def verify_password(username, password):
       if username == 'demo' and password == 'demo2026':
           return username

   @app.route('/api/...')
   @auth.login_required
   def protected_endpoint():
       ...
   ```

2. **Enable rate limiting**:
   ```bash
   pip install Flask-Limiter
   ```

3. **Monitor access logs**:
   ```bash
   tail -f logs/access.log
   ```

4. **Set expiration** for temporary access:
   - ngrok: 2 hours (restart needed)
   - Cloudflare: Optional TTL per tunnel

---

## 📝 Current Status

### Flask Server
- ✅ Running at `http://localhost:8000`
- ✅ Login: `demo2026`
- ✅ Admin account: `admin@softfactory.com / admin123`
- ✅ Database: SQLite (platform.db)

### Test Connectivity (from your machine)
```bash
# Test local access
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "timestamp": "..."}

# After tunnel is set up, test external access
curl https://xxxx-xxxx-xxxx-xxxx.ngrok.io/api/health
```

---

## 🚀 Immediate Next Steps

### Option A: Quick Demo (ngrok) — RECOMMENDED
```bash
# 1. Get free ngrok authtoken (5 sec)
# Visit: https://dashboard.ngrok.com/get-started/your-authtoken

# 2. Configure it
ngrok config add-authtoken YOUR_TOKEN

# 3. Start tunnel
cd D:/Project && ngrok http 8000

# 4. Share the https://xxxx-xxxx-xxxx-xxxx.ngrok.io URL
```

### Option B: Zero-Setup (localtunnel)
```bash
# 1. Install (if npm not available)
npm install -g localtunnel

# 2. Run
lt --port 8000

# 3. Share the public URL
```

---

## 📱 Testing External Access

Once tunnel is running, test from external device:

**From mobile phone on different WiFi:**
```bash
curl https://xxxx-xxxx-xxxx-xxxx.ngrok.io/
```

**From web browser:**
```
https://xxxx-xxxx-xxxx-xxxx.ngrok.io/
Login: demo2026
```

---

## ✅ Verification Checklist

- [ ] Flask server running at localhost:8000
- [ ] One tunnel option selected (ngrok recommended)
- [ ] External URL obtained
- [ ] External access tested from different device/network
- [ ] Access logs monitored
- [ ] Security measures applied if needed

---

## 🛠️ Troubleshooting

### ngrok Says "Authtoken Required"
```bash
# Solution: Configure authtoken
ngrok config add-authtoken YOUR_TOKEN
```

### Tunnel Times Out / 502 Error
```bash
# Check if Flask is still running
curl http://localhost:8000/api/health

# Restart Flask if needed
python D:/Project/start_platform.py
```

### External URL Changes on Restart
- ngrok free tier: Expected behavior (2-hour sessions)
- Solution: Upgrade to Pro ($10/mo) for persistent URL

### DNS Resolution Fails
```bash
# Try flushing DNS cache
ipconfig /flushdns

# Verify tunnel domain
nslookup xxxx-xxxx-xxxx-xxxx.ngrok.io
```

---

## 📞 Support Links

- **ngrok:** https://ngrok.com/docs
- **LocalTunnel:** https://theboroer.github.io/localtunnel-www/
- **Cloudflare:** https://developers.cloudflare.com/cloudflare-one/
- **Flask Deployment:** https://flask.palletsprojects.com/deployment/

---

## 📊 Recommended Setup

**For this project, I recommend: ngrok (Option 1)**

**Reasons:**
- ✅ Simplest setup (2 minutes)
- ✅ Most reliable
- ✅ Best for production demos
- ✅ Free tier sufficient for testing
- ✅ Dashboard to monitor traffic
- ✅ Webhook support built-in

**Next action:** Get your free authtoken and configure ngrok

---

**Created:** 2026-02-25 16:56 KST
**Updated:** Ongoing
**Part of:** SoftFactory Continuous Improvement Phase 4
