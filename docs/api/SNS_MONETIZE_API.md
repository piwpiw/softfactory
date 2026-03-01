# SNS Monetization v2.0 - Complete API Reference

**Version:** 2.0.0
**Last Updated:** 2026-02-26
**Base URL:** `http://localhost:8000/api` (dev) | `https://api.softfactory.com/api` (prod)
**Authentication:** Bearer token (JWT)

---

## 📋 Table of Contents

1. [Link-in-Bio Management](#link-in-bio-management)
2. [Auto-Posting & Scheduling](#auto-posting--scheduling)
3. [Social Platform Integration](#social-platform-integration)
4. [Analytics & ROI](#analytics--roi)
5. [Settings & Configuration](#settings--configuration)

---

## Link-in-Bio Management

### POST /sns/linkinbio
**Create a new Link-in-Bio**

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "title": "My Links",
  "bio_text": "Everything I love in one place",
  "links": [
    {
      "url": "https://example.com",
      "label": "Website",
      "icon": "link",
      "order": 1
    },
    {
      "url": "https://shop.example.com",
      "label": "Shop",
      "icon": "shopping-bag",
      "order": 2
    }
  ],
  "theme": "minimal",
  "color_scheme": {
    "primary": "#000000",
    "secondary": "#ffffff",
    "accent": "#ff6b35"
  },
  "social_platforms": ["instagram", "tiktok"]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 123,
  "slug": "mylinks",
  "title": "My Links",
  "bio_text": "Everything I love in one place",
  "links": [
    {
      "id": 1,
      "url": "https://example.com",
      "label": "Website",
      "icon": "link",
      "order": 1,
      "click_count": 0
    }
  ],
  "theme": "minimal",
  "color_scheme": {
    "primary": "#000000",
    "secondary": "#ffffff",
    "accent": "#ff6b35"
  },
  "social_platforms": ["instagram", "tiktok"],
  "public_url": "https://softfactory.com/link/mylinks",
  "created_at": "2026-02-26T10:30:00Z",
  "updated_at": "2026-02-26T10:30:00Z",
  "click_count": 0,
  "unique_clicks": 0
}
```

**Error Responses:**
- **400 Bad Request:** Invalid input data
  ```json
  {
    "error": "INVALID_INPUT",
    "message": "Title is required and must be between 3 and 100 characters",
    "field": "title"
  }
  ```

- **401 Unauthorized:** Missing or invalid token
  ```json
  {
    "error": "UNAUTHORIZED",
    "message": "Authentication token required"
  }
  ```

- **422 Unprocessable Entity:** Validation error
  ```json
  {
    "error": "VALIDATION_ERROR",
    "details": {
      "links": "Must contain at least 1 link"
    }
  }
  ```

---

### GET /sns/linkinbio
**List all Link-in-Bios (paginated)**

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20, max: 100)
- `sort_by` (string, optional): Sort field - `created_at`, `updated_at`, `click_count` (default: `created_at`)
- `order` (string, optional): Sort order - `asc`, `desc` (default: `desc`)

**Example Request:**
```
GET /sns/linkinbio?page=1&limit=20&sort_by=click_count&order=desc
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "slug": "mylinks",
      "title": "My Links",
      "click_count": 542,
      "unique_clicks": 287,
      "created_at": "2026-02-20T10:30:00Z",
      "updated_at": "2026-02-26T15:45:00Z",
      "public_url": "https://softfactory.com/link/mylinks"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "pages": 1
  }
}
```

---

### GET /sns/linkinbio/{id}
**Get Link-in-Bio details**

**Response (200 OK):**
```json
{
  "id": 1,
  "slug": "mylinks",
  "title": "My Links",
  "bio_text": "Everything I love in one place",
  "links": [
    {
      "id": 1,
      "url": "https://example.com",
      "label": "Website",
      "icon": "link",
      "order": 1,
      "click_count": 150
    }
  ],
  "theme": "minimal",
  "public_url": "https://softfactory.com/link/mylinks",
  "click_count": 542,
  "unique_clicks": 287,
  "created_at": "2026-02-20T10:30:00Z",
  "updated_at": "2026-02-26T15:45:00Z"
}
```

---

### PUT /sns/linkinbio/{id}
**Update Link-in-Bio**

**Request Body:** (same as POST, all fields optional)

**Response (200 OK):** Updated Link-in-Bio object

---

### DELETE /sns/linkinbio/{id}
**Delete Link-in-Bio**

**Response (204 No Content)**

---

## Auto-Posting & Scheduling

### POST /sns/campaign/create
**Create a new SNS campaign**

**Request Body:**
```json
{
  "name": "Summer Campaign 2026",
  "description": "Product launch campaign",
  "platforms": ["instagram", "tiktok", "twitter"],
  "content": {
    "text": "Check out our new product! 🚀",
    "media": [
      {
        "type": "image",
        "url": "https://cdn.example.com/image.jpg",
        "alt_text": "Product preview"
      }
    ],
    "hashtags": ["#newproduct", "#summer2026"],
    "mentions": ["@brand1", "@brand2"]
  },
  "schedule": {
    "start_date": "2026-03-01T09:00:00Z",
    "end_date": "2026-03-31T23:59:59Z",
    "frequency": "daily",
    "times": ["09:00", "14:00", "20:00"],
    "timezone": "Asia/Seoul"
  },
  "targeting": {
    "regions": ["KR"],
    "languages": ["ko"],
    "interests": ["fashion", "lifestyle"]
  },
  "automation_rules": {
    "auto_reply_enabled": true,
    "auto_reply_message": "Thanks for your interest!",
    "auto_like_enabled": true,
    "auto_comment_enabled": false
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Summer Campaign 2026",
  "description": "Product launch campaign",
  "platforms": ["instagram", "tiktok", "twitter"],
  "status": "scheduled",
  "schedule": {
    "start_date": "2026-03-01T09:00:00Z",
    "end_date": "2026-03-31T23:59:59Z",
    "frequency": "daily",
    "times": ["09:00", "14:00", "20:00"],
    "next_post_time": "2026-03-01T09:00:00Z"
  },
  "stats": {
    "total_posts_scheduled": 90,
    "posts_completed": 0,
    "posts_failed": 0,
    "engagement_rate": 0,
    "reach": 0,
    "impressions": 0
  },
  "created_at": "2026-02-26T10:30:00Z",
  "updated_at": "2026-02-26T10:30:00Z"
}
```

---

### GET /sns/campaign
**List all campaigns (paginated)**

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `status` (string, optional): Filter by status - `scheduled`, `active`, `paused`, `completed`
- `platform` (string, optional): Filter by platform - `instagram`, `tiktok`, `twitter`, `facebook`, `linkedin`
- `sort_by` (string, optional): `created_at`, `engagement_rate` (default: `created_at`)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Summer Campaign 2026",
      "status": "active",
      "platforms": ["instagram", "tiktok"],
      "posts_scheduled": 90,
      "posts_completed": 15,
      "engagement_rate": 3.5,
      "reach": 5000,
      "impressions": 12000,
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "pages": 1
  }
}
```

---

### GET /sns/campaign/{id}
**Get campaign details**

**Response (200 OK):** Full campaign object with detailed statistics

---

### PUT /sns/campaign/{id}
**Update campaign**

**Request Body:** (any campaign field)

**Response (200 OK):** Updated campaign object

---

### POST /sns/campaign/{id}/pause
**Pause campaign**

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "paused",
  "message": "Campaign paused successfully",
  "paused_at": "2026-02-26T10:35:00Z"
}
```

---

### POST /sns/campaign/{id}/resume
**Resume campaign**

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "active",
  "message": "Campaign resumed successfully",
  "resumed_at": "2026-02-26T10:36:00Z"
}
```

---

### DELETE /sns/campaign/{id}
**Delete campaign**

**Response (204 No Content)**

---

## Social Platform Integration

### POST /sns/account/connect/{platform}
**Connect social media account**

**Supported Platforms:** instagram, facebook, twitter, linkedin, tiktok, youtube, pinterest, threads, youtube_shorts

**Request Body:**
```json
{
  "platform": "instagram",
  "username": "myusername",
  "access_token": "platform_access_token"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "platform": "instagram",
  "username": "myusername",
  "followers": 10500,
  "engagement_rate": 3.2,
  "connected_at": "2026-02-26T10:30:00Z",
  "status": "active",
  "profile_url": "https://instagram.com/myusername",
  "profile_image": "https://cdn.example.com/profile.jpg"
}
```

---

### GET /sns/account
**List connected accounts**

**Response (200 OK):**
```json
{
  "accounts": [
    {
      "id": 1,
      "platform": "instagram",
      "username": "myusername",
      "followers": 10500,
      "engagement_rate": 3.2,
      "status": "active",
      "connected_at": "2026-02-26T10:30:00Z"
    }
  ],
  "total": 3,
  "active_accounts": 3
}
```

---

### DELETE /sns/account/{id}
**Disconnect social account**

**Response (204 No Content)**

---

## Analytics & ROI

### GET /sns/analytics/dashboard
**Get comprehensive analytics dashboard**

**Query Parameters:**
- `date_from` (string, optional): ISO 8601 date (default: 30 days ago)
- `date_to` (string, optional): ISO 8601 date (default: today)
- `platform` (string, optional): Filter by platform

**Response (200 OK):**
```json
{
  "period": {
    "from": "2026-01-27T00:00:00Z",
    "to": "2026-02-26T23:59:59Z",
    "days": 30
  },
  "overview": {
    "total_posts": 45,
    "total_engagement": 8934,
    "engagement_rate": 3.5,
    "total_reach": 255000,
    "total_impressions": 751000,
    "growth_rate": 12.5
  },
  "by_platform": {
    "instagram": {
      "posts": 20,
      "engagement": 4500,
      "engagement_rate": 4.2,
      "reach": 150000,
      "impressions": 450000
    },
    "tiktok": {
      "posts": 15,
      "engagement": 2800,
      "engagement_rate": 3.1,
      "reach": 80000,
      "impressions": 250000
    },
    "twitter": {
      "posts": 10,
      "engagement": 1634,
      "engagement_rate": 2.1,
      "reach": 25000,
      "impressions": 51000
    }
  },
  "top_posts": [
    {
      "id": 1,
      "platform": "instagram",
      "content_preview": "Check out our new product...",
      "engagement": 523,
      "reach": 12000,
      "posted_at": "2026-02-25T09:00:00Z"
    }
  ],
  "trending": {
    "hashtags": ["#newproduct", "#summer2026"],
    "mentions": ["@brand1", "@competitor"]
  }
}
```

---

### GET /sns/analytics/roi
**Calculate ROI for campaigns**

**Query Parameters:**
- `campaign_id` (integer, optional): Specific campaign ID
- `date_from` (string, optional): ISO 8601 date
- `date_to` (string, optional): ISO 8601 date

**Response (200 OK):**
```json
{
  "campaigns": [
    {
      "id": 1,
      "name": "Summer Campaign 2026",
      "investment": 500,
      "revenue": 15000,
      "roi_percentage": 2900,
      "roi": 29,
      "cost_per_acquisition": 10,
      "customer_lifetime_value": 150,
      "payback_period_days": 8,
      "conversion_rate": 2.5
    }
  ],
  "total_investment": 1000,
  "total_revenue": 45000,
  "total_roi": 4400,
  "avg_roi_percentage": 2900
}
```

---

### GET /sns/analytics/post/{post_id}
**Get detailed analytics for specific post**

**Response (200 OK):**
```json
{
  "post_id": 1,
  "platform": "instagram",
  "posted_at": "2026-02-25T09:00:00Z",
  "content": "Check out our new product! 🚀",
  "media_count": 1,
  "likes": 450,
  "comments": 45,
  "shares": 28,
  "saves": 32,
  "total_engagement": 555,
  "engagement_rate": 4.5,
  "reach": 12000,
  "impressions": 15000,
  "click_through_rate": 1.2,
  "traffic_generated": 145,
  "conversions": 12,
  "conversion_value": 3600,
  "hours_until_peak": 3,
  "peak_hour": "10:00"
}
```

---

## Settings & Configuration

### GET /sns/settings
**Get current SNS settings**

**Response (200 OK):**
```json
{
  "automation_enabled": true,
  "daily_post_limit": 10,
  "auto_best_time_posting": true,
  "auto_hashtag_generation": true,
  "ai_content_optimization": true,
  "content_calendar_enabled": true,
  "analytics_tracking": true,
  "notifications": {
    "email_on_engagement": true,
    "push_on_campaign_update": true,
    "daily_digest": true
  },
  "posting_defaults": {
    "platforms": ["instagram", "tiktok"],
    "timezone": "Asia/Seoul",
    "posting_times": ["09:00", "14:00", "20:00"]
  }
}
```

---

### PUT /sns/settings
**Update SNS settings**

**Request Body:** (any settings field)

**Response (200 OK):** Updated settings object

---

## Error Handling

All error responses follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2026-02-26T10:30:00Z",
  "request_id": "req_12345"
}
```

**Common Error Codes:**
- `UNAUTHORIZED`: Authentication failed
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Rate Limiting

- **Free tier:** 100 requests/hour
- **Professional:** 1,000 requests/hour
- **Enterprise:** Unlimited

Response headers include:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20, max: 100)

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

## Authentication

All endpoints (except public links) require JWT Bearer authentication:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

To get a token, call: `POST /auth/login` or `POST /auth/oauth/{provider}/callback`

---

## Webhooks (Coming Soon)

Subscribe to events via webhooks:

```json
{
  "event": "campaign.completed",
  "timestamp": "2026-02-26T10:30:00Z",
  "data": {
    "campaign_id": 1,
    "campaign_name": "Summer Campaign 2026"
  }
}
```

Events:
- `campaign.created`
- `campaign.completed`
- `campaign.failed`
- `post.published`
- `engagement.received`

---

**Last Updated:** 2026-02-26
**Status:** Production Ready ✅
