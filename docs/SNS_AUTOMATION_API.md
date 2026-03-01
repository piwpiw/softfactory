# SNS Automation API v2.0 — Complete Endpoint Reference

## Overview

The SNS Automation API provides complete social media automation, link-in-bio management, competitor tracking, and ROI analytics. All endpoints require authentication and active `sns-auto` subscription.

**Base URL:** `/api/sns`
**Authentication:** Bearer token (JWT or `demo_token`)
**Response Format:** JSON

---

## 1. Link-in-Bio Management

Create and manage landing pages with multiple links for bio redirects across platforms.

### POST /linkinbio — Create Link-in-Bio

Create a new link-in-bio landing page.

**Request:**
```json
{
  "slug": "my-links",
  "title": "My Important Links",
  "links": [
    {
      "url": "https://example.com",
      "label": "Website",
      "icon": "globe"
    },
    {
      "url": "https://youtube.com/@myaccount",
      "label": "YouTube",
      "icon": "youtube"
    }
  ],
  "theme": "dark"
}
```

**Response (201):**
```json
{
  "id": 1,
  "message": "Link in bio created successfully",
  "data": {
    "id": 1,
    "slug": "my-links",
    "title": "My Important Links",
    "links": [...],
    "theme": "dark",
    "click_count": 0,
    "created_at": "2026-02-26T10:00:00"
  }
}
```

**Status Codes:**
- `201` — Link-in-bio created
- `400` — Missing required fields or duplicate slug
- `401` — Unauthorized

---

### GET /linkinbio — List All Link-in-Bios

Get all link-in-bio pages for the authenticated user.

**Response (200):**
```json
[
  {
    "id": 1,
    "slug": "my-links",
    "title": "My Important Links",
    "links": [...],
    "theme": "dark",
    "click_count": 42,
    "created_at": "2026-02-26T10:00:00"
  }
]
```

---

### GET /linkinbio/<id> — Get Link-in-Bio

Retrieve a specific link-in-bio page by ID.

**Response (200):**
```json
{
  "id": 1,
  "slug": "my-links",
  "title": "My Important Links",
  "links": [...],
  "theme": "dark",
  "click_count": 42,
  "created_at": "2026-02-26T10:00:00"
}
```

**Status Codes:**
- `200` — Success
- `404` — Link-in-bio not found
- `401` — Unauthorized

---

### PUT /linkinbio/<id> — Update Link-in-Bio

Update a link-in-bio page.

**Request:**
```json
{
  "title": "Updated Title",
  "links": [...],
  "theme": "light"
}
```

**Response (200):**
```json
{
  "message": "Link in bio updated successfully",
  "data": {...}
}
```

---

### DELETE /linkinbio/<id> — Delete Link-in-Bio

Delete a link-in-bio page.

**Response (200):**
```json
{
  "message": "Link in bio deleted"
}
```

---

### GET /linkinbio/stats — Get Click Statistics

Get analytics for all or a specific link-in-bio page.

**Query Parameters:**
- `lib_id` (optional) — Get stats for specific link-in-bio

**Response (200):**
```json
{
  "total_click_count": 150,
  "link_in_bios": [
    {
      "lib_id": 1,
      "slug": "my-links",
      "title": "My Important Links",
      "click_count": 100
    },
    {
      "lib_id": 2,
      "slug": "products",
      "title": "Product Links",
      "click_count": 50
    }
  ],
  "count": 2
}
```

**Caching:** 15 minutes

---

## 2. Automation Rules

Create and manage automation rules for regular posting across multiple platforms.

### POST /automate — Create Automation Rule

Create a new automation rule for regular posting.

**Request:**
```json
{
  "name": "Daily AI News",
  "topic": "AI and Technology",
  "purpose": "홍보",
  "platforms": ["instagram", "twitter", "tiktok"],
  "frequency": "daily",
  "custom_hours": 24
}
```

**Fields:**
- `name` (string, required) — Rule name
- `topic` (string, required) — Content topic
- `purpose` (string, required) — Purpose: '홍보' (promotion), '판매' (sales), '커뮤니티' (community)
- `platforms` (array, required) — Target platforms
- `frequency` (string, required) — 'daily', 'weekly', or 'custom'
- `custom_hours` (integer, optional) — Hours between posts (for 'custom')
- `is_active` (boolean, optional) — Default true

**Response (201):**
```json
{
  "id": 1,
  "message": "Automation rule created successfully",
  "data": {
    "id": 1,
    "name": "Daily AI News",
    "topic": "AI and Technology",
    "purpose": "홍보",
    "platforms": ["instagram", "twitter", "tiktok"],
    "frequency": "daily",
    "next_run": "2026-02-27T10:00:00",
    "is_active": true,
    "created_at": "2026-02-26T10:00:00"
  }
}
```

---

### GET /automate — List Automation Rules

Get all automation rules for the user.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Daily AI News",
    "topic": "AI and Technology",
    "purpose": "홍보",
    "platforms": ["instagram", "twitter", "tiktok"],
    "frequency": "daily",
    "next_run": "2026-02-27T10:00:00",
    "is_active": true,
    "created_at": "2026-02-26T10:00:00"
  }
]
```

**Caching:** 15 minutes

---

### GET /automate/<id> — Get Automation Rule

Retrieve a specific automation rule by ID.

**Response (200):**
```json
{
  "id": 1,
  "name": "Daily AI News",
  "topic": "AI and Technology",
  "purpose": "홍보",
  "platforms": ["instagram", "twitter", "tiktok"],
  "frequency": "daily",
  "next_run": "2026-02-27T10:00:00",
  "is_active": true,
  "created_at": "2026-02-26T10:00:00"
}
```

---

### PUT /automate/<id> — Update Automation Rule

Update an automation rule.

**Request:**
```json
{
  "name": "Updated Rule Name",
  "frequency": "weekly",
  "is_active": false
}
```

**Response (200):**
```json
{
  "message": "Automation rule updated successfully",
  "data": {...}
}
```

---

### DELETE /automate/<id> — Delete Automation Rule

Delete an automation rule.

**Response (200):**
```json
{
  "message": "Automation rule deleted"
}
```

---

## 3. Trending Topics & Hashtags

Get trending information for each platform.

### GET /trending — Get Trending Topics

Get trending hashtags, topics, and engagement scores by platform.

**Query Parameters:**
- `platform` (optional) — Filter by specific platform

**Response (200) — All Platforms:**
```json
{
  "platforms": {
    "instagram": {
      "hashtags": ["#ai2026", "#socialmedia", "#contentcreator"],
      "topics": ["AI and Technology", "Digital Marketing", "E-commerce"],
      "engagement_score": 8.5
    },
    "tiktok": {
      "hashtags": ["#foryoupage", "#trending", "#challenge"],
      "topics": ["Entertainment", "Comedy", "Education"],
      "engagement_score": 9.2
    },
    "twitter": {
      "hashtags": ["#tech", "#news", "#politics"],
      "topics": ["Breaking News", "Technology", "Politics"],
      "engagement_score": 7.8
    },
    "linkedin": {
      "hashtags": ["#business", "#career", "#leadership"],
      "topics": ["Business", "Career Development", "Leadership"],
      "engagement_score": 7.2
    },
    "facebook": {
      "hashtags": ["#family", "#lifestyle", "#community"],
      "topics": ["Lifestyle", "Community", "Entertainment"],
      "engagement_score": 6.9
    }
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

**Response (200) — Single Platform:**
```json
{
  "platform": "instagram",
  "data": {
    "hashtags": ["#ai2026", "#socialmedia", "#contentcreator"],
    "topics": ["AI and Technology", "Digital Marketing", "E-commerce"],
    "engagement_score": 8.5
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

**Caching:** 15 minutes

---

## 4. Competitor Tracking

Track and analyze competitor accounts across platforms.

### POST /competitor — Add Competitor

Add a competitor account to track.

**Request:**
```json
{
  "platform": "instagram",
  "username": "competitor_account",
  "followers_count": 50000,
  "engagement_rate": 3.5,
  "avg_likes": 1500,
  "avg_comments": 250,
  "posting_frequency": "daily",
  "data": {
    "top_hashtags": ["#marketing", "#ai"],
    "content_types": ["carousel", "reel"]
  }
}
```

**Response (201):**
```json
{
  "id": 1,
  "message": "Competitor added successfully",
  "data": {
    "id": 1,
    "platform": "instagram",
    "username": "competitor_account",
    "followers_count": 50000,
    "engagement_rate": 3.5,
    "avg_likes": 1500,
    "avg_comments": 250,
    "posting_frequency": "daily",
    "data": {...},
    "last_analyzed": "2026-02-26T10:00:00",
    "created_at": "2026-02-26T10:00:00"
  }
}
```

**Status Codes:**
- `201` — Competitor added
- `400` — Duplicate competitor
- `401` — Unauthorized

---

### GET /competitor — List Competitors

Get all tracked competitors.

**Query Parameters:**
- `platform` (optional) — Filter by platform
- `page` (optional) — Pagination (default: 1)

**Response (200):**
```json
{
  "competitors": [
    {
      "id": 1,
      "platform": "instagram",
      "username": "competitor_account",
      "followers_count": 50000,
      "engagement_rate": 3.5,
      "avg_likes": 1500,
      "avg_comments": 250,
      "posting_frequency": "daily",
      "data": {...},
      "last_analyzed": "2026-02-26T10:00:00",
      "created_at": "2026-02-26T10:00:00"
    }
  ],
  "total": 10,
  "pages": 1,
  "current_page": 1
}
```

---

### GET /competitor/<id> — Get Competitor Details

Get detailed information about a specific competitor.

**Response (200):**
```json
{
  "id": 1,
  "platform": "instagram",
  "username": "competitor_account",
  "followers_count": 50000,
  "engagement_rate": 3.5,
  "avg_likes": 1500,
  "avg_comments": 250,
  "posting_frequency": "daily",
  "data": {...},
  "last_analyzed": "2026-02-26T10:00:00",
  "created_at": "2026-02-26T10:00:00"
}
```

**Caching:** 15 minutes

---

### PUT /competitor/<id> — Update Competitor Data

Update competitor analytics data.

**Request:**
```json
{
  "followers_count": 55000,
  "engagement_rate": 3.8,
  "avg_likes": 1600,
  "avg_comments": 280,
  "data": {
    "top_hashtags": ["#marketing", "#ai", "#growth"]
  }
}
```

**Response (200):**
```json
{
  "message": "Competitor updated successfully",
  "data": {...}
}
```

---

### DELETE /competitor/<id> — Stop Tracking Competitor

Remove a competitor from tracking.

**Response (200):**
```json
{
  "message": "Competitor tracking stopped"
}
```

---

## 5. Content Repurposing

Use AI to repurpose content across multiple platforms.

### POST /ai/repurpose — Repurpose Content

Automatically adapt content for different platforms.

**Request:**
```json
{
  "content": "Just launched our new AI product! Check it out.",
  "source_platform": "linkedin",
  "target_platforms": ["instagram", "twitter", "tiktok"]
}
```

**Response (200):**
```json
{
  "source_platform": "linkedin",
  "source_content": "Just launched our new AI product! Check it out.",
  "repurposed_content": {
    "instagram": "Just launched our new AI product! Check it out.\n\n#socialmedia #content #marketing",
    "twitter": "Just launched our new AI product! Check it out.",
    "tiktok": "Just launched our new AI product! ... 👀 Full content in bio! #trending"
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

**Platform Adaptations:**
- **Instagram** — Full length with emojis and hashtags
- **Twitter** — 280 character limit
- **TikTok** — Engagement-focused with call-to-action
- **LinkedIn** — Professional tone with thought-leadership
- **Facebook** — Warm, community-focused
- **YouTube** — Clear title and description format
- **Pinterest** — Visual inspiration format
- **Threads** — Personal and authentic tone

---

## 6. ROI Metrics & Analytics

Calculate return on investment and performance metrics.

### GET /roi — Get ROI Metrics

Get comprehensive ROI analysis and performance metrics.

**Query Parameters:**
- `platform` (optional) — Filter by specific platform
- `date_from` (optional) — Start date (ISO format: YYYY-MM-DD)
- `date_to` (optional) — End date (ISO format: YYYY-MM-DD)

**Response (200):**
```json
{
  "period": {
    "from": "2026-02-19",
    "to": "2026-02-26"
  },
  "metrics": {
    "total_engagement": 12500,
    "total_reach": 150000,
    "total_impressions": 450000,
    "avg_followers": 45000,
    "engagement_rate": 8.33
  },
  "financial": {
    "estimated_cost": 99.99,
    "estimated_revenue": 6250.0,
    "roi_percentage": 6150.02
  },
  "timestamp": "2026-02-26T10:00:00"
}
```

**Metrics Explained:**
- **total_engagement** — Sum of likes, comments, shares
- **total_reach** — Unique users reached
- **total_impressions** — Total content views
- **engagement_rate** — (engagement / reach) × 100
- **estimated_cost** — Advertising/subscription costs
- **estimated_revenue** — Value generated ($0.50 per engagement)
- **roi_percentage** — ((revenue - cost) / cost) × 100

**Caching:** 15 minutes

---

## Authentication

All endpoints require a valid authentication token.

### Headers:
```
Authorization: Bearer {token}
Content-Type: application/json
```

### Token Types:
- **JWT Token** — Generated via `/api/auth/login` or `/api/auth/refresh`
- **Demo Token** — `demo_token` for testing

### Example:
```bash
curl -X GET "http://localhost:8000/api/sns/automate" \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json"
```

---

## Rate Limiting & Caching

- **Rate Limit** — 100 requests/minute per user
- **Cache TTL** — 15 minutes for analytics endpoints
- **Cache Invalidation** — Automatic on POST/PUT/DELETE

---

## Error Handling

### Standard Error Response:
```json
{
  "error": "Error message describing the issue"
}
```

### Common Status Codes:
- `200` — Success
- `201` — Resource created
- `400` — Bad request (missing fields, validation error)
- `401` — Unauthorized (missing or invalid token)
- `403` — Forbidden (insufficient subscription)
- `404` — Resource not found
- `500` — Server error

---

## Database Models

### SNSLinkInBio
```python
{
  'id': int,
  'user_id': int,
  'slug': str (unique),
  'title': str,
  'links': JSON,
  'theme': str,
  'click_count': int,
  'created_at': datetime,
  'updated_at': datetime
}
```

### SNSAutomate
```python
{
  'id': int,
  'user_id': int,
  'name': str,
  'topic': str,
  'purpose': str,
  'platforms': JSON,
  'frequency': str,
  'next_run': datetime,
  'is_active': bool,
  'created_at': datetime,
  'updated_at': datetime
}
```

### SNSCompetitor
```python
{
  'id': int,
  'user_id': int,
  'platform': str,
  'username': str,
  'followers_count': int,
  'engagement_rate': float,
  'avg_likes': int,
  'avg_comments': int,
  'posting_frequency': str,
  'data': JSON,
  'last_analyzed': datetime,
  'created_at': datetime
}
```

---

## Usage Examples

### Example 1: Create Automation & Track Competitors

```bash
# 1. Create automation rule
curl -X POST "http://localhost:8000/api/sns/automate" \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Tech News",
    "topic": "Technology",
    "purpose": "홍보",
    "platforms": ["instagram", "twitter"],
    "frequency": "daily"
  }'

# 2. Add competitor
curl -X POST "http://localhost:8000/api/sns/competitor" \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "username": "techcompetitor"
  }'

# 3. Check ROI
curl -X GET "http://localhost:8000/api/sns/roi" \
  -H "Authorization: Bearer demo_token"
```

### Example 2: Manage Link-in-Bio

```bash
# 1. Create link-in-bio
curl -X POST "http://localhost:8000/api/sns/linkinbio" \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "my-landing",
    "title": "Welcome to My Links",
    "links": [
      {
        "url": "https://example.com",
        "label": "Website",
        "icon": "globe"
      },
      {
        "url": "https://youtube.com/@myaccount",
        "label": "YouTube",
        "icon": "youtube"
      }
    ]
  }'

# 2. Get click statistics
curl -X GET "http://localhost:8000/api/sns/linkinbio/stats" \
  -H "Authorization: Bearer demo_token"
```

---

## Best Practices

1. **Authentication** — Always include valid Bearer token in headers
2. **Rate Limiting** — Implement client-side retry with exponential backoff
3. **Caching** — Leverage 15-minute cache for analytics queries
4. **Error Handling** — Check response status codes and error messages
5. **Data Validation** — Validate all inputs before sending to API
6. **Pagination** — Use page parameter for large result sets
7. **Filtering** — Use query parameters to reduce response size

---

## Versioning

- **Current Version** — v2.0
- **Released** — 2026-02-26
- **Status** — Production Ready

---

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/softfactory/sns-auto
- Email: support@softfactory.com
- Docs: https://docs.softfactory.com/sns-auto
