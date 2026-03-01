# SoftFactory API Reference - Complete Index

**Version:** 2.0.0
**Last Updated:** 2026-02-26
**Platform:** SoftFactory Multi-Service Architecture
**Base URL:** `http://localhost:8000/api` (dev) | `https://api.softfactory.com/api` (prod)

---

## Quick Navigation

### 🔐 Authentication
- [OAuth 2.0 Flow Guide](OAUTH_FLOW_GUIDE.md) — Google, Facebook, Kakao
- [JWT Token Management](#jwt-token-management)
- [API Key Authentication](#api-key-authentication)

### 📱 Social Media Services
- [SNS Monetization v2.0](api/SNS_MONETIZE_API.md) — Link-in-Bio, Auto-Posting, Analytics
- [Review Scraper](api/REVIEW_SCRAPER_API.md) — Review Aggregation, Auto-Apply, Rewards

### 🍳 Core Services
- [CooCook API](#coocook-api) — Chef Booking, Recipes
- [AI Automation](#ai-automation-api) — Business Process Automation
- [WebApp Builder](#webapp-builder-api) — Low-Code Website Builder

### 📊 Platform Management
- [Analytics & Dashboard](#analytics-dashboard)
- [Payment Integration](#payment-integration)
- [Settings & Configuration](#settings-configuration)

---

## Authentication

### OAuth 2.0 Flow

**Best for:** Web apps, mobile apps, user-facing applications

See [OAuth 2.0 Flow Guide](OAUTH_FLOW_GUIDE.md) for complete guide.

**Quick Start:**
```bash
# 1. Get authorization URL
GET /auth/oauth/google/url

# 2. User logs in and grants permission

# 3. Exchange code for JWT
POST /auth/oauth/google/callback
{
  "code": "authorization_code",
  "state": "state_token"
}

# Response
{
  "access_token": "jwt_token",
  "user": {...}
}
```

### JWT Token Management

**Store JWT:**
```javascript
localStorage.setItem('auth_token', token);
```

**Use in API Calls:**
```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

**Refresh Token:**
```bash
POST /auth/refresh
{
  "refresh_token": "refresh_token"
}
```

### API Key Authentication

**For server-to-server or service integrations:**

```bash
Authorization: ApiKey YOUR_API_KEY

# or

?api_key=YOUR_API_KEY
```

**Get API Key:**
```bash
POST /settings/api-keys
{
  "name": "My Integration",
  "permissions": ["read:sns", "write:sns"]
}
```

---

## SNS Monetization v2.0

**Documentation:** [SNS_MONETIZE_API.md](api/SNS_MONETIZE_API.md)

**Overview:** Complete social media automation, link-in-bio, campaign management, and ROI tracking.

**Key Endpoints:**

```
POST   /sns/linkinbio              Create link-in-bio
GET    /sns/linkinbio              List all link-in-bios
GET    /sns/linkinbio/{id}         Get link-in-bio details
PUT    /sns/linkinbio/{id}         Update link-in-bio
DELETE /sns/linkinbio/{id}         Delete link-in-bio

POST   /sns/campaign/create         Create campaign
GET    /sns/campaign                List campaigns
GET    /sns/campaign/{id}           Get campaign details
PUT    /sns/campaign/{id}           Update campaign
POST   /sns/campaign/{id}/pause    Pause campaign
POST   /sns/campaign/{id}/resume   Resume campaign
DELETE /sns/campaign/{id}           Delete campaign

POST   /sns/account/connect/{platform}  Connect social account
GET    /sns/account                      List connected accounts
DELETE /sns/account/{id}                 Disconnect account

GET    /sns/analytics/dashboard    Get analytics dashboard
GET    /sns/analytics/roi          Calculate ROI
GET    /sns/analytics/post/{id}    Get post analytics

GET    /sns/settings               Get settings
PUT    /sns/settings               Update settings
```

**Authentication:** Required (Bearer token)

**Rate Limit:** 1,000 requests/hour (Professional tier)

---

## Review Scraper

**Documentation:** [REVIEW_SCRAPER_API.md](api/REVIEW_SCRAPER_API.md)

**Overview:** Aggregated review listings across platforms, intelligent matching, auto-apply, and reward tracking.

**Key Endpoints:**

```
GET    /review/aggregated                  Get aggregated listings
GET    /review/listing/{listing_id}        Get listing details
GET    /review/categories                  Get available categories
GET    /review/platforms                   Get available platforms

POST   /review/application                 Apply for listing
GET    /review/application                 List applications
GET    /review/application/{app_id}        Get application details
POST   /review/application/{app_id}/withdraw  Withdraw application

POST   /review/auto-apply/rule             Create auto-apply rule
GET    /review/auto-apply/rule             List auto-apply rules
PUT    /review/auto-apply/rule/{id}        Update auto-apply rule
DELETE /review/auto-apply/rule/{id}        Delete auto-apply rule
GET    /review/auto-apply/history          View auto-apply history

GET    /review/rewards                     Get reward summary
GET    /review/rewards/{id}                Get reward details
POST   /review/rewards/{id}/confirm-received  Confirm reward received

GET    /review/analytics/dashboard         Get analytics dashboard
GET    /review/analytics/earnings          Track earnings
```

**Authentication:** Required (Bearer token)

**Rate Limit:** 500 requests/hour (Free tier)

---

## CooCook API

**Overview:** Chef booking, recipe management, meal planning, and nutrition tracking.

**Key Endpoints:**

```
POST   /coocook/chef/register              Register as chef
GET    /coocook/chef/{id}                  Get chef profile
PUT    /coocook/chef/{id}                  Update chef profile
GET    /coocook/chef/{id}/availability     Get availability
PUT    /coocook/chef/{id}/availability     Update availability

POST   /coocook/recipe                     Create recipe
GET    /coocook/recipe                     Search recipes
GET    /coocook/recipe/{id}                Get recipe details
PUT    /coocook/recipe/{id}                Update recipe
DELETE /coocook/recipe/{id}                Delete recipe

POST   /coocook/booking                    Create booking
GET    /coocook/booking                    List bookings
GET    /coocook/booking/{id}               Get booking details
PUT    /coocook/booking/{id}               Update booking status
POST   /coocook/booking/{id}/cancel        Cancel booking

POST   /coocook/meal-plan                  Create meal plan
GET    /coocook/meal-plan/{id}             Get meal plan
PUT    /coocook/meal-plan/{id}             Update meal plan

GET    /coocook/nutrition/{recipe_id}      Get nutrition info
POST   /coocook/shopping-list              Create shopping list
```

**Authentication:** Required (Bearer token)

---

## AI Automation API

**Overview:** Business process automation using AI, workflow orchestration, and task automation.

**Key Endpoints:**

```
POST   /ai-automation/workflow             Create workflow
GET    /ai-automation/workflow             List workflows
GET    /ai-automation/workflow/{id}        Get workflow details
PUT    /ai-automation/workflow/{id}        Update workflow
DELETE /ai-automation/workflow/{id}        Delete workflow
POST   /ai-automation/workflow/{id}/run    Execute workflow

POST   /ai-automation/task                 Create task
GET    /ai-automation/task                 List tasks
GET    /ai-automation/task/{id}            Get task details
PUT    /ai-automation/task/{id}            Update task
POST   /ai-automation/task/{id}/execute    Execute task

GET    /ai-automation/templates            List available templates
GET    /ai-automation/templates/{id}       Get template details
```

**Authentication:** Required (Bearer token)

---

## WebApp Builder API

**Overview:** No-code website and landing page builder.

**Key Endpoints:**

```
POST   /webapp-builder/site                Create new site
GET    /webapp-builder/site                List sites
GET    /webapp-builder/site/{id}           Get site details
PUT    /webapp-builder/site/{id}           Update site
DELETE /webapp-builder/site/{id}           Delete site
POST   /webapp-builder/site/{id}/publish   Publish site

POST   /webapp-builder/page                Create page
GET    /webapp-builder/page/{id}           Get page
PUT    /webapp-builder/page/{id}           Update page
DELETE /webapp-builder/page/{id}           Delete page

POST   /webapp-builder/component           Add component
PUT    /webapp-builder/component/{id}      Update component
DELETE /webapp-builder/component/{id}      Delete component

GET    /webapp-builder/site/{id}/preview   Get preview
GET    /webapp-builder/site/{id}/publish   Get published URL
```

**Authentication:** Required (Bearer token)

---

## Analytics & Dashboard

**Overview:** Comprehensive analytics across all services.

**Key Endpoints:**

```
GET    /analytics/overview                 Get platform overview
GET    /analytics/revenue                  Get revenue analytics
GET    /analytics/users                    Get user analytics
GET    /analytics/engagement               Get engagement metrics
GET    /analytics/performance              Get performance metrics
GET    /analytics/export                   Export analytics data
```

**Authentication:** Required (Bearer token)

---

## Payment Integration

**Overview:** Stripe integration for subscriptions and payments.

**Key Endpoints:**

```
POST   /payment/create-session              Create Stripe session
GET    /payment/status/{session_id}         Get payment status
POST   /payment/webhook                     Webhook handler
GET    /payment/invoice                     List invoices
GET    /payment/invoice/{id}                Get invoice details
POST   /payment/subscription                Create subscription
GET    /payment/subscription                List subscriptions
PUT    /payment/subscription/{id}           Update subscription
DELETE /payment/subscription/{id}           Cancel subscription
```

**Webhooks:**
- `payment.completed`
- `subscription.created`
- `subscription.cancelled`
- `invoice.generated`

---

## Settings & Configuration

**Overview:** User settings, preferences, and account management.

**Key Endpoints:**

```
GET    /settings/profile                   Get user profile
PUT    /settings/profile                   Update profile
GET    /settings/preferences               Get preferences
PUT    /settings/preferences               Update preferences
POST   /settings/password                  Change password
GET    /settings/api-keys                  List API keys
POST   /settings/api-keys                  Create API key
DELETE /settings/api-keys/{id}             Delete API key
GET    /settings/notifications             Get notification settings
PUT    /settings/notifications             Update notifications
```

**Authentication:** Required (Bearer token)

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `CONFLICT` | 409 | Resource already exists or conflict |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content to return |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or invalid |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

---

## Response Format

All API responses follow this format:

**Success Response (2xx):**
```json
{
  "data": {
    // Response data
  },
  "meta": {
    "request_id": "req_12345",
    "timestamp": "2026-02-26T10:30:00Z"
  }
}
```

**Error Response (4xx, 5xx):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  },
  "meta": {
    "request_id": "req_12345",
    "timestamp": "2026-02-26T10:30:00Z"
  }
}
```

---

## Common Request Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
Accept: application/json
X-Request-ID: optional_request_id
X-Client-Version: optional_client_version
```

---

## Common Response Headers

```
Content-Type: application/json
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
X-Request-ID: req_12345
Cache-Control: no-cache
```

---

## Pagination

All list endpoints support pagination:

```bash
GET /api/resource?page=1&limit=20
```

**Response:**
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

---

## Filtering & Sorting

Most endpoints support filtering and sorting:

```bash
GET /api/resource?status=active&sort_by=created_at&order=desc
```

**Common Query Parameters:**
- `status` — Filter by status
- `sort_by` — Sort by field
- `order` — asc or desc
- `date_from` — Start date (ISO 8601)
- `date_to` — End date (ISO 8601)
- `search` — Free text search

---

## Webhooks

Subscribe to events via webhooks:

```bash
POST /settings/webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["sns.post.published", "review.application.approved"]
}
```

**Events:**
- `sns.post.published`
- `sns.campaign.completed`
- `review.application.approved`
- `review.reward.received`
- `payment.completed`
- `subscription.created`

---

## Rate Limiting

| Tier | Requests/Hour | Concurrent |
|------|---------------|-----------|
| Free | 100 | 5 |
| Professional | 1,000 | 25 |
| Enterprise | Unlimited | 100 |

When rate limited, response includes:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000000
```

---

## SDK & Libraries

### JavaScript/TypeScript
```bash
npm install @softfactory/sdk
```

```javascript
import { SoftFactory } from '@softfactory/sdk';

const client = new SoftFactory({
  accessToken: 'your_token'
});

// Use client
const listings = await client.review.getListings();
```

### Python
```bash
pip install softfactory-sdk
```

```python
from softfactory import SoftFactory

client = SoftFactory(access_token='your_token')
listings = client.review.get_listings()
```

---

## Support & Documentation

- **Documentation:** https://docs.softfactory.com
- **API Status:** https://status.softfactory.com
- **Support:** support@softfactory.com
- **Community:** https://community.softfactory.com

---

**Last Updated:** 2026-02-26
**Status:** Production Ready ✅
**Version:** 2.0.0
