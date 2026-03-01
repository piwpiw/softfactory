# SoftFactory Platform API Reference

> **Version:** 1.0.0 | **Base URL:** `http://localhost:8000` | **Updated:** 2026-02-26

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Platform](#2-platform)
3. [Payment](#3-payment)
4. [SNS Auto](#4-sns-auto)
5. [SNS Revenue API (v2)](#5-sns-revenue-api-v2)
6. [Review Campaigns](#6-review-campaigns)
7. [CooCook](#7-coocook)
8. [AI Automation](#8-ai-automation)
9. [WebApp Builder](#9-webapp-builder)
10. [Dashboard](#10-dashboard)
11. [Analytics](#11-analytics)
12. [Performance](#12-performance)
13. [Settings](#13-settings)

---

## Common Conventions

### Authentication Header

All authenticated endpoints require:

```
Authorization: Bearer <token>
```

**Demo mode:** Use `Bearer demo_token` for testing. The demo token maps to user ID 1 with role `user`.

### Error Response Format

```json
{
  "error": "Human-readable error message"
}
```

### Pagination (standard)

Most list endpoints support:

| Parameter  | Type | Default | Description              |
|------------|------|---------|--------------------------|
| `page`     | int  | 1       | Page number              |
| `per_page` | int  | 12-20   | Items per page           |

Response includes:

```json
{
  "total": 100,
  "pages": 10,
  "current_page": 1,
  "items": [...]
}
```

### Subscription Guard

Endpoints marked with **[subscription: slug]** require an active subscription to the named product. Demo user (ID 1) bypasses this check.

---

## 1. Authentication

**Prefix:** `/api/auth`

### POST /api/auth/register

Register a new user account.

**Auth:** None

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response (201):**

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "user": {
    "id": 2,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Errors:** `400` Missing required fields | `400` Email already registered

---

### POST /api/auth/login

Authenticate and receive tokens.

**Auth:** None

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "user": {
    "id": 2,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Errors:** `400` Missing email or password | `401` Invalid credentials | `403` Account inactive

---

### POST /api/auth/refresh

Refresh an expired access token.

**Auth:** None

**Request Body:**

```json
{
  "refresh_token": "eyJhbG..."
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG..."
}
```

**Errors:** `400` Missing refresh token | `401` Invalid or expired refresh token

---

### GET /api/auth/me

Get current authenticated user info.

**Auth:** Bearer token required

**Response (200):**

```json
{
  "id": 1,
  "email": "demo@softfactory.com",
  "name": "Demo User",
  "role": "user"
}
```

**Errors:** `401` Missing or invalid token

---

### GET /api/auth/oauth/{provider}/url

Get OAuth authorization URL for social login.

**Auth:** None

**Path Parameters:** `provider` - one of `google`, `facebook`, `kakao`

**Response (200):**

```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random_state_token"
}
```

**Errors:** `400` Unknown provider

---

### POST /api/auth/oauth/{provider}/callback

Handle OAuth callback after user authorizes.

**Auth:** None

**Request Body:**

```json
{
  "code": "authorization_code_from_provider",
  "state": "state_token"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "user": {
    "id": 3,
    "email": "user@google.com",
    "name": "Social User",
    "role": "user"
  }
}
```

**Errors:** `400` Missing authorization code | `400` Token exchange failed

---

## 2. Platform

**Prefix:** `/api/platform`

### GET /api/platform/products

Get all active products/services.

**Auth:** None

**Response (200):**

```json
[
  {
    "id": 1,
    "name": "SNS Auto",
    "slug": "sns-auto",
    "monthly_price": 29.99,
    "annual_price": 299.99,
    "is_active": true
  }
]
```

---

### GET /api/platform/dashboard

Get user dashboard with subscription status.

**Auth:** Bearer token required

**Response (200):**

```json
{
  "user": { "id": 1, "email": "demo@softfactory.com", "name": "Demo User", "role": "user" },
  "products": [
    {
      "id": 1,
      "name": "SNS Auto",
      "slug": "sns-auto",
      "subscribed": true,
      "subscription": { "id": 1, "status": "active", "plan_type": "monthly" }
    }
  ],
  "subscription_count": 3
}
```

---

### GET /api/platform/admin/users

Get all users (admin only).

**Auth:** Bearer token required (admin role)

**Query Parameters:** `page` (int, default 1), `per_page` (int, default 20)

**Response (200):**

```json
{
  "users": [
    { "id": 1, "email": "admin@softfactory.com", "name": "Admin", "role": "admin", "active_subscriptions": 5 }
  ],
  "total": 100,
  "pages": 5,
  "current_page": 1
}
```

**Errors:** `403` Admin access required

---

### GET /api/platform/admin/revenue

Get revenue statistics (admin only).

**Auth:** Bearer token required (admin role)

**Response (200):**

```json
{
  "mrr": 1500.00,
  "arr": 18000.00,
  "total_revenue": 5000.00,
  "total_users": 100,
  "active_subscriptions": 50,
  "revenue_by_product": [
    { "product_name": "SNS Auto", "subscriptions": 25, "monthly_revenue": 749.75 }
  ]
}
```

---

### GET /api/platform/admin/executive-dashboard

Comprehensive C-level executive dashboard metrics.

**Auth:** Bearer token required (admin role)

**Response (200):**

```json
{
  "kpis": {
    "monthly_revenue": 5000.00,
    "growth_rate": 15.5,
    "active_users": 250,
    "roi": 382.8
  },
  "revenue_trends": [0, 0, 500, 1200, 3000, 5000],
  "service_distribution": [
    { "name": "SNS Auto", "users": 25, "revenue": 749.75 }
  ],
  "regional_distribution": [
    { "region": "Seoul", "revenue": 580000, "users": 2450 }
  ],
  "metrics": {
    "churn_rate": 2.3,
    "retention_rate": 97.7,
    "avg_subscription_length": 14.2,
    "cac": 580000,
    "ltv": 2800000
  },
  "subscription_breakdown": { "basic": 10, "premium": 20, "enterprise": 5, "total": 35 },
  "daily_comparison": { "yesterday": 100.00, "today": 150.00, "hourly": {} }
}
```

---

## 3. Payment

**Prefix:** `/api/payment`

### GET /api/payment/plans

Get all active product plans.

**Auth:** None

**Response (200):**

```json
[
  {
    "id": 1,
    "name": "SNS Auto",
    "slug": "sns-auto",
    "monthly_price": 29.99,
    "annual_price": 299.99,
    "is_active": true
  }
]
```

---

### POST /api/payment/checkout

Create a Stripe checkout session.

**Auth:** Bearer token required

**Request Body:**

```json
{
  "product_id": 1,
  "plan_type": "monthly"
}
```

`plan_type` is `"monthly"` or `"annual"`.

**Response (200):**

```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

**Errors:** `400` Payment not available in dev mode | `404` Product not found | `400` Already subscribed

---

### GET /api/payment/success

Handle Stripe checkout success callback (redirect).

**Auth:** None (Stripe redirect)

**Query Parameters:** `session_id` (string, required)

**Response (200):**

```json
{
  "message": "Payment successful"
}
```

---

### POST /api/payment/webhook

Handle Stripe webhook events.

**Auth:** Stripe signature header (`Stripe-Signature`)

**Response (200):**

```json
{
  "message": "Webhook received"
}
```

---

### GET /api/payment/subscriptions

Get current user's subscriptions.

**Auth:** Bearer token required

**Response (200):**

```json
[
  {
    "id": 1,
    "product_id": 1,
    "plan_type": "monthly",
    "status": "active",
    "current_period_end": "2026-03-26T00:00:00"
  }
]
```

---

### DELETE /api/payment/subscriptions/{subscription_id}

Cancel a subscription.

**Auth:** Bearer token required

**Response (200):**

```json
{
  "message": "Subscription canceled"
}
```

**Errors:** `404` Subscription not found | `403` Not authorized

---

## 4. SNS Auto

**Prefix:** `/api/sns`

All endpoints (except `/templates`) require **[subscription: sns-auto]**.

### Accounts

#### GET /api/sns/accounts

Get user's linked SNS accounts.

**Auth:** Bearer token + subscription

**Response (200):**

```json
[
  {
    "id": 1,
    "platform": "instagram",
    "account_name": "@mybrand",
    "is_active": true,
    "post_count": 42,
    "created_at": "2026-02-20T10:00:00"
  }
]
```

---

#### POST /api/sns/accounts

Link a new SNS account.

**Auth:** Bearer token + subscription

**Request Body:**

```json
{
  "platform": "instagram",
  "account_name": "@mybrand"
}
```

**Response (201):**

```json
{
  "id": 1,
  "message": "Account linked successfully"
}
```

**Errors:** `400` Missing fields | `400` Account already linked

---

#### DELETE /api/sns/accounts/{account_id}

Unlink an SNS account.

**Auth:** Bearer token + subscription

**Response (200):**

```json
{
  "message": "Account unlinked"
}
```

---

### Posts

#### GET /api/sns/posts

Get user's SNS posts (paginated).

**Auth:** Bearer token + subscription

**Query Parameters:**

| Parameter    | Type   | Description                       |
|-------------|--------|-----------------------------------|
| `account_id` | int    | Filter by account                 |
| `status`     | string | Filter by status (draft/scheduled/published) |
| `page`       | int    | Page number (default 1)           |

**Response (200):**

```json
{
  "posts": [
    {
      "id": 1,
      "account_name": "@mybrand",
      "platform": "instagram",
      "content": "Check out our new...",
      "status": "draft",
      "template_type": "card_news",
      "scheduled_at": null,
      "created_at": "2026-02-25T14:30:00"
    }
  ],
  "total": 42,
  "pages": 3,
  "current_page": 1
}
```

---

#### POST /api/sns/posts

Create a new SNS post.

**Auth:** Bearer token + subscription

**Request Body:**

```json
{
  "account_id": 1,
  "content": "Exciting news about our product!",
  "template_type": "card_news"
}
```

Valid `template_type` values: `card_news`, `blog_post`, `reel`, `shorts`, `carousel`

**Response (201):**

```json
{
  "id": 1,
  "message": "Post created successfully"
}
```

---

#### POST /api/sns/posts/{post_id}/publish

Publish or schedule a post.

**Auth:** Bearer token + subscription

**Request Body:**

```json
{
  "scheduled_at": "2026-03-01T10:00:00"
}
```

Omit `scheduled_at` to publish immediately.

**Response (200):**

```json
{
  "id": 1,
  "status": "scheduled",
  "message": "Post scheduled"
}
```

---

#### DELETE /api/sns/posts/{post_id}

Delete a post (cannot delete published posts).

**Auth:** Bearer token + subscription

**Response (200):**

```json
{
  "message": "Post deleted"
}
```

**Errors:** `400` Cannot delete published posts

---

### Templates

#### GET /api/sns/templates

Get available post templates.

**Auth:** Bearer token (no subscription required)

**Response (200):**

```json
{
  "card_news": { "name": "Card News", "platforms": ["instagram", "tiktok"] },
  "blog_post": { "name": "Blog Post", "platforms": ["blog"] },
  "reel": { "name": "Reel", "platforms": ["instagram"] },
  "shorts": { "name": "YouTube Shorts", "platforms": ["youtube"] },
  "carousel": { "name": "Carousel", "platforms": ["instagram"] }
}
```

---

### Link-in-Bio

#### GET /api/sns/linkinbio

Get user's link-in-bio pages.

**Auth:** Bearer token + subscription

**Response (200):** Array of link-in-bio objects.

---

#### POST /api/sns/linkinbio

Create a link-in-bio page.

**Request Body:**

```json
{
  "slug": "my-brand",
  "title": "My Brand Links",
  "links": [{ "url": "https://shop.example.com", "label": "Shop" }],
  "theme": "light"
}
```

**Response (201):** Link-in-bio object with `id`.

**Errors:** `400` Missing slug/title | `400` Slug already exists

---

#### GET /api/sns/linkinbio/{lib_id}

Get specific link-in-bio page.

---

#### PUT /api/sns/linkinbio/{lib_id}

Update link-in-bio page. Fields: `title`, `links`, `theme`.

---

#### DELETE /api/sns/linkinbio/{lib_id}

Delete link-in-bio page.

---

#### GET /api/sns/linkinbio/stats

Get click statistics. Optional query: `lib_id` (int).

---

### Automation Rules

#### GET /api/sns/automate

List automation rules.

---

#### POST /api/sns/automate

Create an automation rule.

**Request Body:**

```json
{
  "name": "Daily Tips",
  "topic": "Product tips",
  "purpose": "engagement",
  "platforms": ["instagram", "twitter"],
  "frequency": "daily"
}
```

Valid `frequency`: `daily`, `weekly`, `custom`

---

#### GET /api/sns/automate/{automate_id}

Get automation rule details.

---

#### PUT /api/sns/automate/{automate_id}

Update automation rule. Updatable fields: `name`, `topic`, `purpose`, `platforms`, `frequency`, `is_active`.

---

#### DELETE /api/sns/automate/{automate_id}

Delete automation rule.

---

### Trending

#### GET /api/sns/trending

Get trending topics/hashtags by platform.

**Query Parameters:** `platform` (string, optional) - `instagram`, `tiktok`, `twitter`, `linkedin`, `facebook`

**Response (200):**

```json
{
  "platforms": {
    "instagram": {
      "hashtags": ["#ai2026", "#socialmedia"],
      "topics": ["AI and Technology", "Digital Marketing"],
      "engagement_score": 8.5
    }
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

---

### Competitor Analysis

#### GET /api/sns/competitor

List tracked competitors. Query: `platform`, `page`.

---

#### POST /api/sns/competitor

Add a competitor to track.

**Request Body:**

```json
{
  "platform": "instagram",
  "username": "@competitor"
}
```

---

#### GET /api/sns/competitor/{competitor_id}

Get competitor details.

---

#### PUT /api/sns/competitor/{competitor_id}

Update competitor data. Fields: `followers_count`, `engagement_rate`, `avg_likes`, `avg_comments`, `posting_frequency`, `data`.

---

#### DELETE /api/sns/competitor/{competitor_id}

Stop tracking competitor.

---

### AI Content

#### POST /api/sns/ai/repurpose

AI-powered content repurposing.

**Request Body:**

```json
{
  "content": "Our latest product launch...",
  "source_platform": "blog",
  "target_platforms": ["instagram", "twitter", "linkedin"]
}
```

**Response (200):**

```json
{
  "source_platform": "blog",
  "source_content": "Our latest product launch...",
  "repurposed_content": {
    "instagram": "Our latest product launch......\n\n#socialmedia #content #marketing",
    "twitter": "Our latest product launch...",
    "linkedin": "Thought: Our latest product launch...\n\nWhat's your take? #business"
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

---

#### POST /api/sns/ai/generate

Generate SNS post content using AI.

**Request Body:**

```json
{
  "topic": "New product launch",
  "tone": "professional",
  "language": "ko",
  "platform": "instagram",
  "charLimit": 280
}
```

Valid `tone`: `professional`, `casual`, `humorous`, `inspiring`

**Response (200):**

```json
{
  "content": "Generated content...",
  "hashtags": "#SoftFactory #SNSAuto",
  "tone": "professional",
  "language": "ko",
  "platform": "instagram",
  "generated_at": "2026-02-26T10:00:00"
}
```

---

### ROI Metrics

#### GET /api/sns/roi

Get ROI metrics and performance analytics.

**Query Parameters:** `date_from`, `date_to` (ISO date), `platform` (string)

**Response (200):**

```json
{
  "period": { "from": "2026-01-01", "to": "today" },
  "metrics": {
    "total_engagement": 5000,
    "total_reach": 100000,
    "total_impressions": 250000,
    "avg_followers": 15000,
    "engagement_rate": 2.0
  },
  "financial": {
    "estimated_cost": 99.99,
    "estimated_revenue": 2500.00,
    "roi_percentage": 2400.24
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

---

## 5. SNS Revenue API (v2)

**Prefix:** `/api/sns` (registered via `sns_revenue_bp`)

Enhanced versions of SNS endpoints with standardized responses, cursor/offset pagination, and field filtering.

### Response Format (v2)

All v2 endpoints return:

```json
{
  "success": true,
  "data": {},
  "timestamp": "2026-02-26T10:00:00",
  "pagination": { "page": 1, "per_page": 50, "total_pages": 2 },
  "total": 100
}
```

### Common Query Parameters (v2)

| Parameter    | Type   | Default  | Description                                    |
|-------------|--------|----------|------------------------------------------------|
| `pagination` | string | `offset` | `offset` or `cursor`                           |
| `page`       | int    | 1        | Page number (offset mode)                      |
| `cursor`     | int    | null     | Cursor ID (cursor mode)                        |
| `per_page`   | int    | 50       | Items per page (1-100)                         |
| `fields`     | string | null     | Comma-separated fields to return               |

---

### Link-in-Bio (v2)

- **POST /api/sns/linkinbio** - Create (slug must be alphanumeric + hyphen)
- **GET /api/sns/linkinbio** - List with pagination
- **GET /api/sns/linkinbio/{id}** - Get details
- **PUT /api/sns/linkinbio/{id}** - Update (`title`, `links`, `theme`)
- **DELETE /api/sns/linkinbio/{id}** - Delete
- **GET /api/sns/linkinbio/stats/{id}** - Click statistics

### Automation (v2)

- **POST /api/sns/automate** - Create (frequency: `daily`/`weekly`/`biweekly`/`monthly`, purpose: `promotion`/`engagement`/`education`/`community`/`news`)
- **GET /api/sns/automate** - List with pagination
- **GET /api/sns/automate/{id}** - Get details
- **PUT /api/sns/automate/{id}** - Update
- **DELETE /api/sns/automate/{id}** - Delete
- **POST /api/sns/automate/{id}/run** - Execute immediately

### Trending (v2)

#### GET /api/sns/trending

Enhanced trending with region support.

**Query Parameters:** `platform` (default `all`), `region` (default `KR`)

Valid platforms: `instagram`, `twitter`, `tiktok`, `linkedin`, `all`
Valid regions: `KR`, `US`, `JP`, `GB`, `DE`

### Content Repurpose (v2)

#### POST /api/sns/repurpose

**Request Body:**

```json
{
  "content": "Check out our new AI tool!",
  "platforms": ["instagram", "twitter", "linkedin"],
  "tone": "professional"
}
```

Valid tones: `professional`, `casual`, `humorous`, `inspirational`, `promotional`

### Competitor (v2)

- **POST /api/sns/competitor** - Add competitor
- **GET /api/sns/competitor** - List with pagination
- **GET /api/sns/competitor/{id}** - Get details
- **GET /api/sns/competitor/{id}/compare** - Detailed comparison (query: `period` = `week`/`month`/`year`)
- **DELETE /api/sns/competitor/{id}** - Remove

### ROI Calculator (v2)

#### GET /api/sns/roi

**Query Parameters:** `period` (`week`/`month`/`year`/`all`), `platform` (`instagram`/`twitter`/`linkedin`/`all`)

Returns detailed revenue breakdown (engagement, impression, affiliate), costs, ROI percentage, and ROAS.

---

## 6. Review Campaigns

**Prefix:** `/api/review`

### Campaigns

#### GET /api/review/campaigns

List active campaigns (public, no auth required).

**Query Parameters:** `category`, `page`, `per_page` (default 12)

**Response (200):**

```json
{
  "campaigns": [
    {
      "id": 1,
      "title": "Beauty Product Review",
      "product_name": "Moisturizer X",
      "category": "beauty",
      "reward_type": "product",
      "reward_value": 50000,
      "max_reviewers": 10,
      "applications_count": 3,
      "deadline": "2026-03-15T00:00:00",
      "created_at": "2026-02-20T10:00:00"
    }
  ],
  "total": 25,
  "pages": 3,
  "current_page": 1
}
```

---

#### GET /api/review/campaigns/{campaign_id}

Get campaign details (public).

---

#### POST /api/review/campaigns

Create a campaign. **[subscription: review]**

**Request Body:**

```json
{
  "title": "Review our new product",
  "product_name": "Product X",
  "category": "beauty",
  "description": "We need honest reviews...",
  "reward_type": "product",
  "reward_value": 50000,
  "max_reviewers": 10,
  "deadline": "2026-03-15T00:00:00"
}
```

---

#### POST /api/review/campaigns/{campaign_id}/apply

Apply to a campaign (reviewer). **Auth required.**

**Request Body:**

```json
{
  "message": "I'd love to review this product",
  "sns_link": "https://instagram.com/myaccount",
  "follower_count": 5000
}
```

---

#### GET /api/review/my-campaigns

Get user's created campaigns. **[subscription: review]**

---

#### GET /api/review/my-applications

Get user's campaign applications. **Auth required.**

---

#### GET /api/review/campaigns/{campaign_id}/applications

Get applications for a campaign (creator only). **[subscription: review]**

---

#### PUT /api/review/applications/{application_id}

Approve or reject application (creator only). **[subscription: review]**

**Request Body:**

```json
{
  "status": "approved"
}
```

Valid status: `pending`, `approved`, `rejected`

---

### Scraped Listings

#### GET /api/review/listings

Get scraped review listings with filters. **Auth required.**

**Query Parameters:** `page`, `per_page`, `category`, `platform`, `reward_type`, `min_reward`, `max_reward`, `sort_by` (`deadline`/`reward_value`/`created`)

---

#### GET /api/review/listings/{listing_id}

Get listing detail with bookmark status and user's applications.

---

#### GET /api/review/listings/search

Search listings by keyword. **Auth required.**

**Query Parameters:** `q` (min 2 chars), `page`, `per_page`

---

#### POST /api/review/listings/{listing_id}/apply

Apply to a listing. **Auth required.**

**Request Body:**

```json
{
  "account_id": 1
}
```

---

### Bookmarks

#### GET /api/review/bookmarks

Get bookmarked listings. **Auth required.**

---

#### POST /api/review/listings/{listing_id}/bookmark

Bookmark a listing. **Auth required.**

---

#### DELETE /api/review/listings/{listing_id}/bookmark

Remove bookmark. **Auth required.**

---

### Review Accounts

#### GET /api/review/accounts

Get user's review accounts. **Auth required.**

---

#### POST /api/review/accounts

Create review account. **Auth required.**

**Request Body:**

```json
{
  "platform": "naver",
  "account_name": "myblog",
  "follower_count": 1000,
  "category_tags": ["beauty", "food"]
}
```

Valid platforms: `naver`, `instagram`, `blog`, `youtube`, `tiktok`, `facebook`

---

#### PUT /api/review/accounts/{account_id}

Update review account. Fields: `follower_count`, `category_tags`, `is_active`.

---

#### DELETE /api/review/accounts/{account_id}

Delete review account.

---

### Review Applications

#### GET /api/review/applications

Get user's review applications. **Auth required.**

**Query Parameters:** `status`, `page`, `per_page`

---

### Auto-Apply Rules

#### GET /api/review/auto-rules

Get auto-apply rules. **Auth required.**

---

#### POST /api/review/auto-rules

Create auto-apply rule. **Auth required.**

**Request Body:**

```json
{
  "name": "Beauty products auto-apply",
  "target_categories": ["beauty", "skincare"],
  "min_reward": 10000,
  "max_reward": 100000,
  "apply_deadline_days": 30,
  "max_applicants_ratio": 0.5,
  "preferred_accounts": [1, 2],
  "reward_types": ["product", "cash"],
  "is_active": true
}
```

---

#### PUT /api/review/auto-rules/{rule_id}

Update auto-apply rule. All fields updatable.

---

#### DELETE /api/review/auto-rules/{rule_id}

Delete auto-apply rule.

---

### Scraper Control

#### GET /api/review/scraper/status

Get scraper status across all platforms. **Auth required.**

**Response (200):**

```json
{
  "total_listings": 500,
  "active_listings": 320,
  "expired_listings": 180,
  "platforms": {
    "revu": { "total_listings": 100, "last_scraped": "2026-02-26T08:00:00" },
    "reviewplace": { "total_listings": 80, "last_scraped": "2026-02-26T08:00:00" }
  }
}
```

---

#### POST /api/review/scraper/run

Manually trigger scraper (admin only). **Auth required.**

**Errors:** `403` Only admins can trigger scraper

---

## 7. CooCook

**Prefix:** `/api/coocook`

### GET /api/coocook/chefs

List active chefs. **Auth:** None

**Query Parameters:** `cuisine`, `location`, `page`, `per_page` (default 12)

**Response (200):**

```json
{
  "chefs": [
    {
      "id": 1,
      "name": "Chef Kim",
      "bio": "Specializing in Korean cuisine",
      "cuisine_type": "korean",
      "location": "Seoul",
      "price_per_session": 50000,
      "rating": 4.8,
      "rating_count": 120
    }
  ],
  "total": 50,
  "pages": 5,
  "current_page": 1
}
```

---

### GET /api/coocook/chefs/{chef_id}

Get chef details. **Auth:** None

---

### POST /api/coocook/chefs

Register as a chef. **Auth:** Bearer token required

**Request Body:**

```json
{
  "name": "Chef Kim",
  "bio": "Korean cuisine specialist",
  "cuisine_type": "korean",
  "location": "Seoul",
  "price_per_session": 50000
}
```

---

### GET /api/coocook/bookings

Get user's bookings. **[subscription: coocook]**

---

### POST /api/coocook/bookings

Create a booking. **[subscription: coocook]**

**Request Body:**

```json
{
  "chef_id": 1,
  "booking_date": "2026-03-15",
  "duration_hours": 3,
  "special_requests": "Vegetarian menu please"
}
```

**Response (201):**

```json
{
  "id": 1,
  "message": "Booking created successfully",
  "total_price": 150000
}
```

**Errors:** `404` Chef not found | `400` Past date | `400` Missing fields

---

### GET /api/coocook/bookings/{booking_id}

Get booking details. **[subscription: coocook]**

---

### PUT /api/coocook/bookings/{booking_id}

Update booking status (chef only). **[subscription: coocook]**

**Request Body:**

```json
{
  "status": "confirmed"
}
```

---

## 8. AI Automation

**Prefix:** `/api/ai-automation`

### GET /api/ai-automation/plans

Get subscription plans. **Auth:** None

**Response (200):**

```json
{
  "starter": { "name": "Starter", "price": 49000, "hours_saved": "10h", "features": ["..."] },
  "ambassador": { "name": "Ambassador", "price": 89000, "hours_saved": "15h", "features": ["..."] },
  "enterprise": { "name": "Enterprise", "price": 290000, "hours_saved": "30h", "features": ["..."] }
}
```

---

### GET /api/ai-automation/scenarios

Get automation scenarios. **Auth:** None

**Query Parameters:** `category`

---

### GET /api/ai-automation/scenarios/{scenario_id}

Get scenario details. **Auth:** None

---

### GET /api/ai-automation/employees

Get user's AI employees. **[subscription: ai-automation]**

---

### POST /api/ai-automation/employees

Create AI employee. **[subscription: ai-automation]**

**Request Body:**

```json
{
  "name": "Email Assistant",
  "scenario_type": "email",
  "description": "Handles email responses"
}
```

Valid `scenario_type`: `email`, `social`, `customer_service`, `data_entry`, `scheduling`

---

### GET /api/ai-automation/employees/{employee_id}

Get AI employee details. **[subscription: ai-automation]**

---

### POST /api/ai-automation/employees/{employee_id}/deploy

Deploy AI employee (starts training). **[subscription: ai-automation]**

**Request Body (optional):**

```json
{
  "savings_hours": 10
}
```

---

### POST /api/ai-automation/employees/{employee_id}/activate

Activate AI employee (training -> active). **[subscription: ai-automation]**

---

### DELETE /api/ai-automation/employees/{employee_id}

Delete AI employee (must not be active). **[subscription: ai-automation]**

**Errors:** `400` Cannot delete active employee

---

### GET /api/ai-automation/dashboard

Get automation dashboard summary. **[subscription: ai-automation]**

**Response (200):**

```json
{
  "total_employees": 5,
  "active_employees": 3,
  "total_monthly_savings_hours": 30,
  "estimated_annual_savings": "W450,000",
  "employees": [...]
}
```

---

## 9. WebApp Builder

**Prefix:** `/api/webapp-builder`

### GET /api/webapp-builder/plans

Get bootcamp plans. **Auth:** None

---

### GET /api/webapp-builder/courses

Get bootcamp courses. **Auth:** None

---

### POST /api/webapp-builder/enroll

Enroll in bootcamp. **[subscription: webapp-builder]**

**Request Body:**

```json
{
  "plan_type": "weekday"
}
```

Valid `plan_type`: `weekday`, `weekend`

---

### GET /api/webapp-builder/enrollments

Get user's enrollments. **[subscription: webapp-builder]**

---

### GET /api/webapp-builder/webapps

Get user's webapp projects. **[subscription: webapp-builder]**

---

### POST /api/webapp-builder/webapps

Create webapp project. **[subscription: webapp-builder]**

**Request Body:**

```json
{
  "name": "My First App",
  "description": "A task management app"
}
```

---

### GET /api/webapp-builder/webapps/{webapp_id}

Get webapp details. **[subscription: webapp-builder]**

---

### POST /api/webapp-builder/webapps/{webapp_id}/deploy

Deploy webapp. **[subscription: webapp-builder]**

**Request Body (optional):**

```json
{
  "url": "https://myapp.example.com",
  "repo": "https://github.com/user/myapp"
}
```

---

### GET /api/webapp-builder/dashboard

Get bootcamp dashboard. **[subscription: webapp-builder]**

---

## 10. Dashboard

**Prefix:** `/api/dashboard`

### GET /api/dashboard/kpis

Get KPI metrics (cached 15 min). **Auth required.**

**Response (200):**

```json
{
  "revenue": { "value": 5000.00, "unit": "$" }
}
```

---

### GET /api/dashboard/charts

Get chart data. **Auth required.**

**Response (200):**

```json
{
  "revenue_trend": { "labels": ["Jan", "Feb"], "datasets": [] }
}
```

---

### GET /api/dashboard/summary

Get dashboard summary. **Auth required.**

**Response (200):**

```json
{
  "total_users": 100,
  "active_subscriptions": 50
}
```

---

## 11. Analytics

**Prefix:** `/api/analytics`

### GET /api/analytics/advanced

Advanced analytics with time series. **Auth required.**

**Query Parameters:** `metric` (default `revenue`), `period` (default `30` days)

---

### GET /api/analytics/cohort

User cohort analysis (last 180 days). **Auth required.**

---

### GET /api/analytics/funnel

Conversion funnel (Signup -> Subscribed -> Paid). **Auth required.**

**Response (200):**

```json
[
  { "stage": "Signups", "users": 100, "conversion_rate": 100.0 },
  { "stage": "Subscribed", "users": 50, "conversion_rate": 50.0 },
  { "stage": "Paid", "users": 25, "conversion_rate": 50.0 }
]
```

---

### GET /api/analytics/service-metrics

Per-service metrics. **Auth required.**

---

### GET /api/analytics/trends

Market trends and forecast. **Auth required.**

**Query Parameters:** `days` (int, default 30)

---

## 12. Performance

**Prefix:** `/api/performance`

### GET /api/performance/roi

Overall ROI metrics (cached 15 min). **Auth required.**

**Response (200):**

```json
{
  "overall_roi": { "value": 85.5, "unit": "%" },
  "customer_acquisition_cost": { "value": 50, "unit": "$" },
  "customer_lifetime_value": { "value": 500.0, "unit": "$" },
  "clv_cac_ratio": { "value": 10.0, "unit": "x" },
  "breakeven_subscriptions": { "value": 10, "current": 25 },
  "profit_margin": { "value": 45.0, "unit": "%" }
}
```

---

### GET /api/performance/product-roi

Per-product ROI ranking. **Auth required.**

---

### GET /api/performance/efficiency

Operational efficiency metrics. **Auth required.**

---

### GET /api/performance/forecast

Quarterly ROI forecast. **Auth required.**

---

### GET /api/performance/benchmarks

Industry benchmarks comparison. **Auth required.**

---

## 13. Settings

**Prefix:** `/api/settings`

### GET /api/settings/organization

Get organization settings. **Auth required.**

**Response (200):**

```json
{
  "organization_name": "Demo User",
  "organization_email": "demo@softfactory.com",
  "timezone": "UTC",
  "language": "en",
  "currency": "USD",
  "theme": "light"
}
```

---

### PUT /api/settings/organization

Update organization settings. **Auth required.**

**Request Body (partial update):**

```json
{
  "organization_name": "My Company",
  "timezone": "Asia/Seoul",
  "language": "ko",
  "currency": "KRW",
  "theme": "dark"
}
```

Allowed keys: `organization_name`, `timezone`, `language`, `currency`, `theme`

---

### GET /api/settings/integrations

Get connected and available integrations. **Auth required.**

---

### POST /api/settings/integrations/{platform}/connect

Initiate platform connection. **Auth required.**

**Response (200):**

```json
{
  "status": "pending",
  "platform": "instagram",
  "state": "random_oauth_state"
}
```

---

### POST /api/settings/integrations/{account_id}/disconnect

Disconnect an integration. **Auth required.**

---

### GET /api/settings/api-keys

Get API keys (masked). **Auth required.**

---

### GET /api/settings/webhook-endpoints

Get webhook endpoints. **Auth required.**

---

### GET /api/settings/notifications

Get notification preferences. **Auth required.**

---

### GET /api/settings/billing

Get billing settings and invoices. **Auth required.**

---

## Health Check

### GET /health

Basic health check. **Auth:** None

**Response (200):**

```json
{
  "status": "ok",
  "database": "connected",
  "services": {
    "sns_auto": "ok",
    "review": "ok",
    "coocook": "ok",
    "ai_automation": "ok",
    "webapp_builder": "ok"
  },
  "version": "1.0.0",
  "uptime": "2h 15m 30s"
}
```

---

## Quick Start: Demo Token Usage

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Or use demo token for immediate access
export TOKEN="demo_token"

# Get user info
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# List chefs
curl http://localhost:8000/api/coocook/chefs

# Get SNS accounts
curl http://localhost:8000/api/sns/accounts \
  -H "Authorization: Bearer $TOKEN"

# Create a post
curl -X POST http://localhost:8000/api/sns/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_id":1,"content":"Hello world!","template_type":"card_news"}'
```
