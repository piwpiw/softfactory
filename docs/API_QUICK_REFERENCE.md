# 🔌 SoftFactory API - Quick Reference Card

> **Purpose**: **Version:** 2.0.0 | **Last Updated:** 2026-02-26 | **Print-Friendly:** Yes
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory API - Quick Reference Card 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 2.0.0 | **Last Updated:** 2026-02-26 | **Print-Friendly:** Yes

---

## 🚀 Getting Started

### Authentication
```bash
# OAuth Login
curl http://localhost:8000/api/auth/oauth/google/url

# Use JWT Token in Requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/sns/linkinbio
```

### Base URL
- **Development:** `http://localhost:8000/api`
- **Production:** `https://api.softfactory.com/api`

---

## 📱 SNS API (Social Media)

### Link-in-Bio
```bash
# Create
POST /sns/linkinbio
{"title": "My Links", "links": [...], "theme": "minimal"}

# List
GET /sns/linkinbio?page=1&limit=20

# Get
GET /sns/linkinbio/{id}

# Update
PUT /sns/linkinbio/{id}

# Delete
DELETE /sns/linkinbio/{id}
```

### Campaigns
```bash
# Create
POST /sns/campaign/create
{"name": "Summer 2026", "platforms": ["instagram", "tiktok"], ...}

# List
GET /sns/campaign?status=active&platform=instagram

# Get
GET /sns/campaign/{id}

# Update
PUT /sns/campaign/{id}

# Pause
POST /sns/campaign/{id}/pause

# Resume
POST /sns/campaign/{id}/resume

# Delete
DELETE /sns/campaign/{id}
```

### Analytics
```bash
# Dashboard
GET /sns/analytics/dashboard?date_from=2026-02-01&date_to=2026-02-28

# ROI
GET /sns/analytics/roi?campaign_id={id}

# Post Metrics
GET /sns/analytics/post/{post_id}
```

---

## 🏷️ Review Scraper API

### Search Listings
```bash
# Get Listings
GET /review/aggregated?category=뷰티&platform=revu&min_reward=100000&limit=20

# Filter Parameters:
# - category: 뷰티, 패션, 일렉트로닉스, 푸드, ...
# - platform: revu, reviewplace, marketplace, ...
# - reward_type: product, cash, mixed
# - min_reward / max_reward: numbers in KRW
# - sort_by: deadline, reward, created, applicants
# - status: open, closing_soon, closed
```

### Applications
```bash
# Apply
POST /review/application
{"listing_id": "revu_12345", "application_message": "..."}

# List My Applications
GET /review/application?status=approved

# Get Application
GET /review/application/{app_id}

# Withdraw
POST /review/application/{app_id}/withdraw
```

### Auto-Apply Rules
```bash
# Create Rule
POST /review/auto-apply/rule
{
  "name": "Beauty Products",
  "conditions": {
    "categories": ["뷰티"],
    "min_reward": 100000
  }
}

# List Rules
GET /review/auto-apply/rule

# Update Rule
PUT /review/auto-apply/rule/{id}

# Delete Rule
DELETE /review/auto-apply/rule/{id}

# View History
GET /review/auto-apply/history
```

### Rewards
```bash
# Get Rewards Summary
GET /review/rewards?status=pending

# Get Reward Details
GET /review/rewards/{id}

# Confirm Received
POST /review/rewards/{id}/confirm-received
```

---

## 🔐 Authentication

### OAuth 2.0 Providers
```bash
# Google
GET /auth/oauth/google/url
POST /auth/oauth/google/callback

# Facebook
GET /auth/oauth/facebook/url
POST /auth/oauth/facebook/callback

# Kakao
GET /auth/oauth/kakao/url
POST /auth/oauth/kakao/callback
```

### Token Management
```bash
# Refresh Token
POST /auth/refresh
{"refresh_token": "YOUR_REFRESH_TOKEN"}

# Logout
POST /auth/logout

# Current User
GET /auth/me

# Link Provider
POST /auth/oauth/link/{provider}
{"code": "oauth_code"}
```

---

## 💰 Payment API

### Subscriptions
```bash
# Create Session
POST /payment/create-session
{"tier": "professional", "billing_cycle": "monthly"}

# Check Status
GET /payment/status/{session_id}

# Create Subscription
POST /payment/subscription
{"tier": "professional"}

# Cancel Subscription
DELETE /payment/subscription/{id}
```

### Invoices
```bash
# List Invoices
GET /payment/invoice

# Get Invoice
GET /payment/invoice/{id}
```

---

## ⚙️ Settings API

### Profile & Preferences
```bash
# Get Profile
GET /settings/profile

# Update Profile
PUT /settings/profile
{"name": "...", "email": "...", ...}

# Get Preferences
GET /settings/preferences

# Update Preferences
PUT /settings/preferences
{"theme": "dark", "notifications": true, ...}
```

### API Keys
```bash
# Create Key
POST /settings/api-keys
{"name": "My Integration", "permissions": ["read:sns"]}

# List Keys
GET /settings/api-keys

# Delete Key
DELETE /settings/api-keys/{id}
```

---

## 📊 Analytics API

### Dashboard
```bash
# Get Overview
GET /analytics/overview

# Revenue
GET /analytics/revenue?date_from=2026-02-01&date_to=2026-02-28

# Users
GET /analytics/users

# Engagement
GET /analytics/engagement

# Performance
GET /analytics/performance
```

---

## ✋ Common Responses

### Success (200, 201)
```json
{
  "data": {
    "id": 1,
    "name": "...",
    ...
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-02-26T10:30:00Z"
  }
}
```

### Paginated Response
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Error (4xx, 5xx)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": {"email": "required"}
  }
}
```

---

## 🔴 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - New resource created |
| 204 | No Content - Successful, no response body |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Auth required |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Server Error - Something went wrong |

---

## 🛑 Common Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `CONFLICT` | 409 | Resource conflict (duplicate) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `LISTING_NOT_FOUND` | 404 | Review listing not found |
| `ALREADY_APPLIED` | 409 | Already applied to this listing |
| `INELIGIBLE` | 422 | User doesn't meet requirements |

---

## 📈 Query Parameters (Common)

```bash
# Pagination
?page=1&limit=20

# Sorting
?sort_by=created_at&order=desc

# Filtering
?status=active&category=뷰티&platform=revu

# Date Range
?date_from=2026-02-01&date_to=2026-02-28

# Search
?search=keyword

# Combine
?page=1&limit=20&sort_by=engagement&order=desc&date_from=2026-02-01
```

---

## 🔑 Request Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
Accept: application/json
X-Request-ID: optional_id
X-Client-Version: 2.0.0
```

---

## 📊 Rate Limits

| Tier | Limit | Window |
|------|-------|--------|
| Free | 100 | 1 hour |
| Pro | 1,000 | 1 hour |
| Enterprise | Unlimited | - |

**Headers Included:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

---

## 🧪 Test with cURL

### Simple GET
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/sns/linkinbio
```

### POST with Data
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Links"}' \
  http://localhost:8000/api/sns/linkinbio
```

### With Query Parameters
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/review/aggregated?category=뷰티&limit=10"
```

### View Headers
```bash
curl -i -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/sns/linkinbio
```

---

## 🛠️ Testing Tools

- **Postman:** Excellent for API testing with collections
- **Insomnia:** Great REST client alternative
- **cURL:** Command-line testing
- **Swagger UI:** Interactive API documentation (if deployed)
- **Bruno:** Lightweight API client

---

## 📞 Help & Support

| Question | Answer |
|----------|--------|
| **How do I get a token?** | Use OAuth endpoints or API keys in settings |
| **What's my rate limit?** | Check `X-RateLimit-*` headers in responses |
| **How do I fix 401 errors?** | Verify token is valid and not expired |
| **What about CORS errors?** | Ensure request has proper headers and origin |
| **How do I get help?** | Check docs.softfactory.com or email support |

---

## 📚 Full Documentation

- **SNS API Docs:** See `/docs/api/SNS_MONETIZE_API.md`
- **Review API Docs:** See `/docs/api/REVIEW_SCRAPER_API.md`
- **OAuth Guide:** See `/docs/OAUTH_FLOW_GUIDE.md`
- **API Reference:** See `/docs/API_REFERENCE_INDEX.md`
- **Full Specification:** See FULL API documentation files

---

## ⏱️ Common Workflows

### Sign Up & Get Token
```bash
# 1. Get Google auth URL
curl http://localhost:8000/api/auth/oauth/google/url

# 2. User logs in (in browser)

# 3. Exchange code for token
curl -X POST \
  -d '{"code": "AUTH_CODE"}' \
  http://localhost:8000/api/auth/oauth/google/callback

# 4. Use token in subsequent requests
```

### Search & Apply for Review
```bash
# 1. Search listings
curl "http://localhost:8000/api/review/aggregated?category=뷰티&limit=20"

# 2. Apply for listing
curl -X POST \
  -d '{"listing_id": "revu_123", "message": "I'm interested"}' \
  -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/review/application

# 3. Track application
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/review/application
```

### Create SNS Campaign
```bash
# 1. Connect social account
curl -X POST \
  -d '{"platform": "instagram", "access_token": "..."}' \
  -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/sns/account/connect/instagram

# 2. Create campaign
curl -X POST \
  -d '{"name": "Campaign", "platforms": ["instagram"]}' \
  -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/sns/campaign/create

# 3. Check analytics
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/sns/analytics/dashboard
```

---

## 💡 Pro Tips

1. **Bookmark this page** for quick reference
2. **Use Postman collections** for API testing
3. **Enable request logging** to debug issues
4. **Check response headers** for rate limits
5. **Implement retry logic** for reliability (429 errors)
6. **Cache API responses** when possible (GET requests)
7. **Use pagination** to handle large result sets
8. **Keep tokens secure** - never commit to git
9. **Monitor error rates** in production
10. **Read full docs** when stuck on implementation

---

**Laminated Version:** Available in team Slack
**Digital Version:** https://docs.softfactory.com/quick-reference
**Last Updated:** 2026-02-26
**Status:** ✅ Ready to Print & Use