# Production Deployment Checklist — SoftFactory v2.0
> **Complete step-by-step checklist for deploying all 8 agent teams' work to production**
>
> **Date:** 2026-02-26 | **Estimated Duration:** 130 minutes | **Status:** READY FOR DEPLOYMENT

---

## PRE-DEPLOYMENT (15 minutes)

### 1. Infrastructure Readiness

```
☐ PostgreSQL 14+ instance running
  └─ Verify: psql -U postgres -c "SELECT version();"
  └─ Create database: createdb softfactory
  └─ Create application user: CREATE USER softfactory_app WITH PASSWORD 'xxx';

☐ Redis 7+ instance running
  └─ Verify: redis-cli ping → PONG
  └─ Set password in redis.conf
  └─ Test auth: redis-cli -a <password> ping

☐ Elasticsearch 8+ cluster running
  └─ Verify: curl -X GET http://localhost:9200/
  └─ Create index: curl -X PUT http://localhost:9200/softfactory_posts
  └─ Install Nori analyzer plugin

☐ Docker & Docker Compose installed
  └─ Verify: docker --version && docker-compose --version
  └─ Ensure Docker daemon is running

☐ Domain & SSL certificate obtained
  └─ DNS configured to point to server IP
  └─ SSL certificate placed in /etc/ssl/certs/
  └─ Test: curl -I https://yourdomain.com → HTTP 200

☐ Firewall rules configured
  └─ Allow inbound: 80 (HTTP), 443 (HTTPS), 8000 (API), 5678 (n8n), 9200 (Elasticsearch)
  └─ Restrict to known IPs where possible
```

### 2. External Service Credentials

```
☐ AWS Account with S3 bucket created
  └─ Bucket: softfactory-uploads
  └─ Region: us-east-1
  └─ Versioning: Enabled
  └─ Server-side encryption: KMS (optional but recommended)
  └─ IAM user created with S3-only permissions
  └─ Access key & secret key saved in .env

☐ CloudFront distribution created
  └─ Origin: S3 bucket
  └─ Domain: d*.cloudfront.net
  └─ CNAME added to custom domain (optional)
  └─ Cache policy: 30 days
  └─ Domain saved as CLOUDFRONT_DOMAIN in .env

☐ Stripe account (Live mode, not test)
  └─ API keys: sk_live_* and pk_live_*
  └─ Webhook endpoint created at: https://yourdomain.com/api/payment/webhook
  └─ Webhook secret saved in .env (STRIPE_WEBHOOK_SECRET)
  └─ Subscription products configured in Stripe dashboard
  └─ KRW currency enabled in account settings

☐ OAuth credentials obtained
  ├─ Google OAuth
  │  ├─ Credentials at https://console.cloud.google.com/
  │  ├─ OAuth consent screen configured
  │  ├─ Authorized redirect URI: https://yourdomain.com/api/auth/oauth/google/callback
  │  ├─ Client ID & secret saved in .env (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
  │
  ├─ Facebook OAuth
  │  ├─ Credentials at https://developers.facebook.com/
  │  ├─ App domain: yourdomain.com
  │  ├─ Authorized redirect URI: https://yourdomain.com/api/auth/oauth/facebook/callback
  │  ├─ App ID & secret saved in .env
  │
  └─ KakaoTalk OAuth
     ├─ Credentials at https://developers.kakao.com/
     ├─ OAuth redirect URI: https://yourdomain.com/api/auth/oauth/kakao/callback
     ├─ REST API key saved in .env (KAKAO_REST_API_KEY)

☐ Firebase Cloud Messaging
  ├─ Project created in Firebase Console
  ├─ Service account JSON downloaded
  ├─ JSON file contents saved in .env (FIREBASE_PRIVATE_KEY, etc.)
  ├─ APNs certificate uploaded (for iOS push)

☐ Email Service (SendGrid)
  ├─ Account created at sendgrid.com
  ├─ API key generated (SG.xxx...)
  ├─ Sender address verified (noreply@yourdomain.com)
  ├─ Email templates created (welcome, receipt, notifications, reset password)
  ├─ API key saved in .env (MAIL_PASSWORD)

☐ Sentry (Error Tracking)
  ├─ Project created at sentry.io
  ├─ DSN obtained (https://xxx@sentry.io/xxx)
  ├─ Environment: production
  ├─ Alerts configured for critical errors
  ├─ DSN saved in .env (SENTRY_DSN)
```

### 3. Code & Environment Setup

```
☐ Clone production branch
  └─ git clone -b main https://github.com/yourorg/softfactory.git
  └─ cd softfactory

☐ Create .env file from template
  └─ cp .env.example .env
  └─ Fill all required variables (see section below)
  └─ Verify no hardcoded secrets in code: grep -r "sk_" backend/ web/

☐ Verify no debug mode enabled
  └─ FLASK_ENV=production (not development)
  └─ DEBUG=False
  └─ SECRET_KEY=<random string min 32 chars>

☐ Install dependencies
  └─ pip install -r requirements.txt
  └─ npm install (if using frontend build)

☐ Build Docker image
  └─ docker build -t softfactory:latest .
  └─ Verify: docker images | grep softfactory
```

---

## ENVIRONMENT VARIABLES CHECKLIST (.env)

### REQUIRED VARIABLES

```
# Core Flask
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
SQLALCHEMY_DATABASE_URI=postgresql://softfactory_app:password@postgres-host:5432/softfactory
SQLALCHEMY_ECHO=False
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_POOL_RECYCLE=3600

# JWT
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Redis
REDIS_URL=redis://:password@redis-host:6379/0
REDIS_CACHE_TTL=3600
REDIS_SESSION_TTL=86400

# Database
DATABASE_URL=postgresql://...  (duplicate of SQLALCHEMY_DATABASE_URI)

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=softfactory-uploads
AWS_S3_REGION=us-east-1
CLOUDFRONT_DOMAIN=d*.cloudfront.net

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OAuth Credentials
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
KAKAO_REST_API_KEY=...

# Firebase
FIREBASE_PROJECT_ID=...
FIREBASE_PRIVATE_KEY_ID=...
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
FIREBASE_CLIENT_EMAIL=...
FIREBASE_CLIENT_ID=...

# Elasticsearch
ELASTICSEARCH_HOST=elasticsearch-host
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_PROTOCOL=https  (or http if internal)
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=...

# Email
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxx...
DEFAULT_MAIL_SENDER=noreply@yourdomain.com

# Application
ENVIRONMENT=production
HOSTNAME=yourdomain.com
PORT=8000
WORKERS=4  (for Gunicorn)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=WARNING  (or INFO for initial debugging)

# Features
ENABLE_OAUTH_MOCK_MODE=False
ENABLE_2FA=True
ENABLE_PWA=True
ENABLE_WEBSOCKET=True
ENABLE_ELASTICSEARCH=True

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# n8n
N8N_HOST=n8n.yourdomain.com
N8N_PROTOCOL=https
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<strong password>
WEBHOOK_TUNNEL_URL=https://n8n.yourdomain.com/
```

---

## PHASE 1: DATABASE SETUP (10 minutes)

```
☐ Create PostgreSQL database
  └─ createdb softfactory

☐ Create database user with limited permissions
  └─ psql -U postgres -c "CREATE USER softfactory_app WITH PASSWORD 'xxx';"
  └─ psql -U postgres -c "GRANT CONNECT ON DATABASE softfactory TO softfactory_app;"
  └─ psql -U postgres -c "GRANT USAGE ON SCHEMA public TO softfactory_app;"
  └─ psql -U postgres -c "GRANT CREATE ON SCHEMA public TO softfactory_app;"

☐ Run database migrations
  └─ flask db init (if first time)
  └─ flask db migrate -m "Initial migration"
  └─ flask db upgrade
  └─ Verify: psql -U softfactory_app -d softfactory -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
  └─ Expected: 40+ tables

☐ Seed initial data
  └─ python backend/scripts/seed_database.py
  └─ Verify: SELECT COUNT(*) FROM users; (should be > 0)
  └─ Verify: SELECT COUNT(*) FROM subscription_plans; (should be 3-4)

☐ Create database backups
  └─ pg_dump softfactory > /backups/softfactory_2026-02-26.sql
  └─ Store backup in secure location (S3, separate server, etc.)

☐ Configure automated backups
  └─ Set up cron job: 0 2 * * * pg_dump softfactory | gzip > /backups/softfactory_$(date +\%Y-\%m-\%d).sql.gz
```

---

## PHASE 2: REDIS SETUP (5 minutes)

```
☐ Start Redis service
  └─ systemctl start redis-server (Linux)
  └─ brew services start redis (macOS)
  └─ docker run -d -p 6379:6379 redis:7 (Docker)

☐ Test Redis connection
  └─ redis-cli ping → PONG
  └─ redis-cli SET test_key "hello" → OK
  └─ redis-cli GET test_key → "hello"
  └─ redis-cli -a <password> ping (if password set)

☐ Configure Redis persistence (optional but recommended)
  └─ Edit /etc/redis/redis.conf:
     save 900 1     (save every 15 min if 1+ keys changed)
     save 300 10    (save every 5 min if 10+ keys changed)
     appendonly yes (AOF persistence)

☐ Set Redis password
  └─ Edit redis.conf: requirepass <strong_password>
  └─ Update .env: REDIS_URL=redis://:password@host:6379/0
  └─ Test: redis-cli -a <password> ping
```

---

## PHASE 3: ELASTICSEARCH SETUP (15 minutes)

```
☐ Start Elasticsearch service
  └─ Docker: docker run -d -p 9200:9200 -e discovery.type=single-node docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  └─ Systemd: systemctl start elasticsearch
  └─ Verify: curl -X GET http://localhost:9200/

☐ Create indices
  └─ curl -X PUT http://localhost:9200/softfactory_posts -d '{
       "settings": {
         "number_of_shards": 1,
         "number_of_replicas": 0,
         "analysis": {
           "analyzer": {
             "nori_analyzer": {
               "type": "custom",
               "tokenizer": "nori_tokenizer"
             }
           }
         }
       },
       "mappings": {
         "properties": {
           "title": { "type": "text", "analyzer": "nori_analyzer" },
           "content": { "type": "text", "analyzer": "nori_analyzer" },
           "created_at": { "type": "date" }
         }
       }
     }'

☐ Install Nori analyzer (Korean support)
  └─ elasticsearch-plugin install analysis-nori
  └─ Restart Elasticsearch

☐ Index initial data
  └─ python backend/scripts/index_elasticsearch.py
  └─ Verify: curl -X GET http://localhost:9200/_cat/indices
  └─ Expected: softfactory_posts, softfactory_reviews, softfactory_users

☐ Test search functionality
  └─ curl -X POST http://localhost:9200/softfactory_posts/_search -d '{"query": {"match_all": {}}}'
  └─ Expected: Non-zero hits
```

---

## PHASE 4: FLASK API DEPLOYMENT (10 minutes)

```
☐ Create Gunicorn service file
  └─ cat > /etc/systemd/system/softfactory.service << 'EOF'
     [Unit]
     Description=SoftFactory API
     After=network.target postgresql.service redis.service

     [Service]
     Type=notify
     User=softfactory
     Group=softfactory
     WorkingDirectory=/opt/softfactory
     Environment="PATH=/opt/softfactory/venv/bin"
     Environment="PYTHONUNBUFFERED=1"
     EnvironmentFile=/opt/softfactory/.env
     ExecStart=/opt/softfactory/venv/bin/gunicorn \
       --workers 4 \
       --worker-class sync \
       --bind 127.0.0.1:8000 \
       --timeout 60 \
       --access-logfile /var/log/softfactory/access.log \
       --error-logfile /var/log/softfactory/error.log \
       backend.app:app

     Restart=always
     RestartSec=10

     [Install]
     WantedBy=multi-user.target
     EOF

☐ Create application user
  └─ useradd -m -s /bin/bash softfactory
  └─ chown -R softfactory:softfactory /opt/softfactory
  └─ chmod 700 /opt/softfactory/.env

☐ Create log directory
  └─ mkdir -p /var/log/softfactory
  └─ chown softfactory:softfactory /var/log/softfactory
  └─ chmod 755 /var/log/softfactory

☐ Start Flask service
  └─ systemctl daemon-reload
  └─ systemctl start softfactory
  └─ systemctl enable softfactory
  └─ Verify: systemctl status softfactory

☐ Test API health
  └─ curl http://localhost:8000/api/health
  └─ Expected: HTTP 200 + {"status": "ok"}
```

---

## PHASE 5: NGINX REVERSE PROXY (10 minutes)

```
☐ Install Nginx
  └─ apt-get install nginx (Ubuntu)
  └─ brew install nginx (macOS)

☐ Create Nginx config
  └─ cat > /etc/nginx/sites-available/softfactory << 'EOF'
     upstream flask_app {
         server 127.0.0.1:8000;
     }

     server {
         listen 80;
         server_name yourdomain.com www.yourdomain.com;
         return 301 https://$server_name$request_uri;
     }

     server {
         listen 443 ssl http2;
         server_name yourdomain.com www.yourdomain.com;

         ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
         ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
         ssl_protocols TLSv1.2 TLSv1.3;
         ssl_ciphers HIGH:!aNULL:!MD5;
         ssl_prefer_server_ciphers on;

         # Security headers
         add_header X-Frame-Options "SAMEORIGIN";
         add_header X-Content-Type-Options "nosniff";
         add_header X-XSS-Protection "1; mode=block";
         add_header Referrer-Policy "strict-origin-when-cross-origin";

         client_max_body_size 50M;

         location / {
             proxy_pass http://flask_app;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
             proxy_redirect off;
         }

         location /static/ {
             alias /opt/softfactory/web/;
             expires 30d;
             add_header Cache-Control "public, immutable";
         }
     }
     EOF

☐ Enable Nginx config
  └─ ln -s /etc/nginx/sites-available/softfactory /etc/nginx/sites-enabled/
  └─ nginx -t  (test config)
  └─ systemctl restart nginx

☐ Test HTTPS
  └─ curl -I https://yourdomain.com
  └─ Expected: HTTP 200
```

---

## PHASE 6: OAUTH & EXTERNAL SERVICES (10 minutes)

```
☐ Test Google OAuth
  └─ curl "http://localhost:8000/api/auth/oauth/google/url"
  └─ Expected: auth_url, state_token
  └─ Visit URL, authorize, capture authorization code
  └─ Call callback with code
  └─ Expected: access_token, refresh_token

☐ Test Stripe Integration
  └─ curl "http://localhost:8000/api/payment/plans"
  └─ Expected: 200 OK + list of plans
  └─ Test charge: Create test charge in Stripe dashboard
  └─ Verify webhook delivery: Check Stripe dashboard → Webhooks

☐ Test AWS S3 Upload
  └─ curl -X POST http://localhost:8000/api/files/upload \
     -H "Authorization: Bearer <test_token>" \
     -F "file=@test.jpg"
  └─ Expected: 200 OK + file_id, cdn_url

☐ Test Firebase Push Notifications
  └─ python -c "from backend.services.fcm_service import FCMService; FCMService.test_connection()"
  └─ Expected: Connection successful
```

---

## PHASE 7: WebSocket & REAL-TIME (5 minutes)

```
☐ Test WebSocket connection
  └─ python -c "import socketio; client = socketio.Client(); client.connect('http://localhost:8000'); print('Connected')"
  └─ Expected: Connected message

☐ Verify namespace availability
  └─ Check: SNS namespace (/sns), Orders (/orders), Chat (/chat), Notifications (/notifications)

☐ Test real-time event
  └─ Create a post via API
  └─ Listen to /sns namespace for post:created event
  └─ Expected: Event received within 1 second
```

---

## PHASE 8: ELASTICSEARCH INDEXING (5 minutes)

```
☐ Index all existing posts
  └─ python backend/scripts/index_elasticsearch.py --posts

☐ Index all existing reviews
  └─ python backend/scripts/index_elasticsearch.py --reviews

☐ Index all existing users
  └─ python backend/scripts/index_elasticsearch.py --users

☐ Verify indexing
  └─ curl -X GET http://localhost:9200/_cat/indices?v
  └─ Expected: 3 indices with > 0 docs

☐ Test search
  └─ curl -X POST http://localhost:9200/softfactory_posts/_search -d '{"query": {"match": {"content": "test"}}}'
  └─ Expected: Relevant results
```

---

## PHASE 9: MONITORING & ALERTING (10 minutes)

### Prometheus

```
☐ Install Prometheus
  └─ Docker: docker run -d -p 9090:9090 -v prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

☐ Configure scrape targets
  └─ API: localhost:8000/metrics
  └─ PostgreSQL: postgresql exporter
  └─ Redis: redis exporter
  └─ Elasticsearch: elasticsearch exporter

☐ Test metrics collection
  └─ curl http://localhost:9090/api/v1/query?query=up
  └─ Expected: All targets = 1 (up)
```

### Grafana

```
☐ Install Grafana
  └─ Docker: docker run -d -p 3000:3000 grafana/grafana

☐ Add Prometheus data source
  └─ URL: http://prometheus:9090
  └─ Test connection: OK

☐ Import dashboards
  └─ PostgreSQL (ID: 9628)
  └─ Redis (ID: 11835)
  └─ Elasticsearch (ID: 14682)

☐ Create custom dashboard
  └─ API Response Time (p95, p99)
  └─ Error Rate
  └─ Database Connections
  └─ Redis Memory Usage
```

### Alerts

```
☐ Configure alerting rules
  └─ High error rate (>5%)
  └─ Database connection pool exhausted
  └─ Elasticsearch unhealthy
  └─ Redis memory usage >90%
  └─ API response time >5s

☐ Set up alert channels
  └─ Email notifications
  └─ Slack integration (optional)
  └─ SMS alerts (for critical)
```

---

## PHASE 10: n8n WORKFLOW AUTOMATION (20 minutes)

```
☐ Deploy n8n instance
  └─ Docker: docker run -d -p 5678:5678 n8nio/n8n
  └─ Or: n8n start

☐ Access n8n UI
  └─ URL: http://localhost:5678
  └─ Set admin credentials (N8N_BASIC_AUTH_USER, N8N_BASIC_AUTH_PASSWORD)

☐ Configure API endpoint nodes
  └─ Create HTTP request node for Flask API
  └─ Test connection: GET /api/health
  └─ Expected: 200 OK

☐ Create initial workflows
  ├─ User Registration (POST /register → Send welcome email)
  ├─ SNS Post Scheduler (Hourly trigger → Post to platforms)
  ├─ Payment Processing (Stripe webhook → Update invoice)
  ├─ Review Scraping (Hourly → Scrape listings → Store results)
  └─ See N8N_INTEGRATION_GUIDE.md section 7 for details

☐ Set up webhook triggers
  └─ Stripe webhook: https://yourdomain.com/api/payment/webhook
  └─ Custom webhooks for internal workflows

☐ Test workflow execution
  └─ Trigger workflow manually
  └─ Verify output logs
  └─ Check database for expected changes
```

---

## PHASE 11: SMOKE TESTS (15 minutes)

### Health Checks

```bash
#!/bin/bash

echo "=== SoftFactory Production Smoke Tests ==="

# API Health
echo "1. API Health Check..."
curl -s http://localhost:8000/api/health | jq .
[ $? -eq 0 ] && echo "✓ API OK" || echo "✗ API FAILED"

# Database
echo "2. Database Connection..."
curl -s -H "Authorization: Bearer demo_token" http://localhost:8000/api/auth/user
[ $? -eq 0 ] && echo "✓ Database OK" || echo "✗ Database FAILED"

# Redis
echo "3. Redis Connection..."
redis-cli ping
[ $? -eq 0 ] && echo "✓ Redis OK" || echo "✗ Redis FAILED"

# Elasticsearch
echo "4. Elasticsearch..."
curl -s http://localhost:9200/_health | jq .
[ $? -eq 0 ] && echo "✓ Elasticsearch OK" || echo "✗ Elasticsearch FAILED"

# OAuth
echo "5. OAuth Google..."
curl -s "http://localhost:8000/api/auth/oauth/google/url" | jq .
[ $? -eq 0 ] && echo "✓ OAuth OK" || echo "✗ OAuth FAILED"

# Stripe
echo "6. Payment Plans..."
curl -s "http://localhost:8000/api/payment/plans" | jq .
[ $? -eq 0 ] && echo "✓ Stripe OK" || echo "✗ Stripe FAILED"

# S3
echo "7. File Upload..."
curl -s -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer demo_token" \
  -F "file=@test.txt"
[ $? -eq 0 ] && echo "✓ S3 OK" || echo "✗ S3 FAILED"

# WebSocket
echo "8. WebSocket..."
python -c "import socketio; c = socketio.Client(); c.connect('http://localhost:8000'); print('OK')"
[ $? -eq 0 ] && echo "✓ WebSocket OK" || echo "✗ WebSocket FAILED"

# Frontend
echo "9. Frontend..."
curl -s http://localhost:8000/ | grep -q "<!DOCTYPE html>"
[ $? -eq 0 ] && echo "✓ Frontend OK" || echo "✗ Frontend FAILED"

# n8n
echo "10. n8n..."
curl -s http://localhost:5678/ | grep -q "n8n"
[ $? -eq 0 ] && echo "✓ n8n OK" || echo "✗ n8n FAILED"

echo "=== All Smoke Tests Complete ==="
```

### Functional Tests

```
☐ User Registration Flow
  └─ POST /api/auth/register → verify email → click link → login
  └─ Expected: JWT tokens issued

☐ OAuth Login Flow
  └─ GET /api/auth/oauth/google/url → authorize → callback → redirect
  └─ Expected: User created, JWT tokens issued

☐ SNS Post Creation
  └─ POST /api/sns/posts → verify content → schedule → publish
  └─ Expected: Post visible on platform

☐ Payment Processing
  └─ POST /api/payment/subscribe → enter card → charge → verify subscription
  └─ Expected: Invoice generated, subscription active

☐ Review Scraping
  └─ POST /api/review/scrape/now → wait for completion → check results
  └─ Expected: Listings aggregated, displayed in UI

☐ Search Function
  └─ POST /api/search/full-text → enter query → get results
  └─ Expected: Results ranked by relevance

☐ Admin Dashboard
  └─ Login as admin → access /admin → view KPIs
  └─ Expected: All metrics loaded, no errors

☐ Real-time Notification
  └─ Create post → listen to WebSocket → verify event received
  └─ Expected: Event within 1 second
```

---

## PHASE 12: BACKUP & DISASTER RECOVERY (5 minutes)

```
☐ Verify database backup
  └─ pg_dump softfactory > /backups/final_backup.sql
  └─ Test restore: createdb softfactory_test && psql softfactory_test < /backups/final_backup.sql
  └─ Verify: SELECT COUNT(*) FROM users; (should match production)

☐ Store backups offsite
  └─ Upload to S3 or secure cloud storage
  └─ Keep last 30 days of daily backups
  └─ Keep last 12 months of weekly backups

☐ Document disaster recovery procedure
  └─ How to restore database
  └─ How to restore S3 files
  └─ How to restore Elasticsearch indices
  └─ RTO (Recovery Time Objective): < 1 hour
  └─ RPO (Recovery Point Objective): < 1 day

☐ Test disaster recovery (dry run)
  └─ Simulate database failure
  └─ Restore from backup
  └─ Verify all systems operational
```

---

## PHASE 13: SECURITY HARDENING (10 minutes)

```
☐ Enable HTTPS/SSL
  └─ All traffic redirected HTTP → HTTPS
  └─ HSTS header enabled: max-age=31536000

☐ API Key Security
  └─ Stripe keys: never logged, never sent to frontend
  └─ OAuth secrets: rotated quarterly
  └─ Database password: unique, strong (min 16 chars)

☐ Database Security
  └─ User accounts: least privilege (read-only where possible)
  └─ Network: only from application server
  └─ Backups: encrypted at rest

☐ Application Security
  └─ CORS: only trusted origins
  └─ CSRF protection: enabled for state-changing requests
  └─ SQL injection: ORM protection, parameterized queries
  └─ XSS protection: input validation, output encoding

☐ Infrastructure Security
  └─ Firewall: restrictive inbound rules
  └─ SSH: key-based auth, no password login
  └─ Secrets: never in code, use .env
  └─ Logs: no sensitive data logged

☐ Dependency Security
  └─ pip audit: scan for known vulnerabilities
  └─ npm audit: scan for npm vulnerabilities
  └─ Regular updates: monthly security patches
```

---

## PHASE 14: FINAL VALIDATION & GO-LIVE (10 minutes)

```
☐ Stakeholder Sign-off
  └─ Business stakeholders: all features verified working
  └─ Technical team: all systems healthy
  └─ Product manager: deployment approved
  └─ Security: no critical issues

☐ Load Testing (optional but recommended)
  └─ Use k6 to simulate 100+ concurrent users
  └─ Target latency: <1 second for API calls
  └─ Expected throughput: 1000+ requests/second

☐ Performance Baseline
  └─ Document current response times:
     - API endpoints: <500ms (p95)
     - Search queries: <100ms
     - File uploads: <5 seconds for 10MB
     - Database queries: <50ms
  └─ Set alerts if metrics exceed 2x baseline

☐ Create incident response runbook
  └─ How to handle API downtime
  └─ How to handle database issues
  └─ How to handle payment processing failure
  └─ Emergency contacts list
  └─ Post-incident review template

☐ Schedule on-call rotation
  └─ 24/7 monitoring during first 30 days
  └─ Page on-call for critical alerts
  └─ Daily standup to review issues

☐ Deploy to production
  └─ docker-compose up -d (if using Docker)
  └─ systemctl restart softfactory (if systemd)
  └─ Monitor logs for first 1 hour
  └─ Verify all alerts working
```

---

## POST-DEPLOYMENT MONITORING (Next 7 Days)

```
Day 1:
  ☐ Monitor error rates (target: <0.1%)
  ☐ Monitor response times (target: <500ms p95)
  ☐ Check database query performance
  ☐ Verify all scheduled jobs running
  ☐ Review Sentry for new issues

Day 2-7:
  ☐ Daily standup: discuss any incidents
  ☐ Monitor user feedback
  ☐ Review analytics for unusual patterns
  ☐ Verify backups completing successfully
  ☐ Performance trending (should be stable)

Week 2-4:
  ☐ Switch from 24/7 on-call to business hours
  ☐ Analyze usage patterns
  ☐ Optimize slow queries based on real data
  ☐ Update runbooks based on learnings
  ☐ Plan for scaling if needed
```

---

## ROLLBACK PLAN

If critical issues occur post-deployment:

```
Severity: CRITICAL (>50% users affected)
  ☐ Immediate: Revert to previous Docker image tag
  ☐ Command: docker-compose down && docker-compose up -d
  ☐ Expected downtime: <5 minutes
  ☐ Notify users: Post status on status page

Severity: HIGH (1-50% users affected)
  ☐ Analyze issue (15 minutes max)
  ☐ Attempt fix if straightforward
  ☐ Otherwise: rollback to previous version
  ☐ Schedule post-mortem within 24 hours

Severity: MEDIUM (specific feature broken)
  ☐ Disable feature (if possible)
  ☐ Develop fix in hotfix branch
  ☐ Deploy fix in next 1-2 hours
  ☐ No rollback needed if feature is isolated
```

---

## DEPLOYMENT SUMMARY

| Phase | Duration | Critical? | Status |
|-------|----------|-----------|--------|
| Pre-deployment | 15 min | YES | ☐ |
| Database setup | 10 min | YES | ☐ |
| Redis setup | 5 min | YES | ☐ |
| Elasticsearch | 15 min | NO | ☐ |
| Flask API | 10 min | YES | ☐ |
| Nginx proxy | 10 min | YES | ☐ |
| OAuth setup | 10 min | YES | ☐ |
| WebSocket | 5 min | NO | ☐ |
| Elasticsearch indexing | 5 min | NO | ☐ |
| Monitoring | 10 min | NO | ☐ |
| n8n workflows | 20 min | NO | ☐ |
| Smoke tests | 15 min | YES | ☐ |
| Backup & DR | 5 min | YES | ☐ |
| Security | 10 min | YES | ☐ |
| Final validation | 10 min | YES | ☐ |
| **TOTAL** | **145 min** | | |

---

**Deployment Date:** [INSERT DATE]
**Deployed By:** [NAME]
**Approved By:** [MANAGER]
**Time Started:** [TIME]
**Time Completed:** [TIME]
**Outcome:** ☐ SUCCESS ☐ PARTIAL SUCCESS ☐ ROLLBACK

**Post-Deployment Notes:**
[Space for notes and issues encountered]

---

**For support:** See DAILY_OPERATIONS_GUIDE.md
**For architecture:** See N8N_INTEGRATION_GUIDE.md
**For API reference:** See API_ENDPOINT_QUICK_REFERENCE.md
