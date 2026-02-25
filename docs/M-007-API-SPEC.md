# M-007 Complete API Specification (OpenAPI 3.1)

**Version:** 3.0.0
**Last Updated:** 2026-02-26
**Status:** Production-Ready
**Base URL:** `http://localhost:8000/api` (dev) | `https://api.softfactory.com/api` (prod)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [SNS LinkInBio Endpoints](#sns-linkinbio-endpoints)
4. [SNS Automate Endpoints](#sns-automate-endpoints)
5. [SNS Trending Endpoints](#sns-trending-endpoints)
6. [SNS ROI Endpoints](#sns-roi-endpoints)
7. [Review Aggregation Endpoints](#review-aggregation-endpoints)
8. [Review Account Endpoints](#review-account-endpoints)
9. [Review Application Endpoints](#review-application-endpoints)
10. [Review AutoApply Endpoints](#review-autoapply-endpoints)
11. [Error Handling](#error-handling)
12. [Rate Limiting](#rate-limiting)
13. [Response Formats](#response-formats)

---

## Overview

M-007 combines two major feature sets:
- **SNS (Social Network Services) v3.0:** Link-in-bio, automation, trending analysis, ROI tracking
- **Review System v3.0:** Integrated review aggregation, influencer matching, auto-apply campaigns

### Supported Platforms

**SNS Platforms:**
- Instagram, Facebook, Twitter/X, TikTok, LinkedIn, YouTube, Pinterest, Threads, YouTube Shorts

**Review Sources:**
- Coupang Rocket Wow, Naver Shopping, Watcha (Korean influencer platforms)
- Amazon Reviews (US influencer campaigns)

### Authentication Methods
- **Bearer Token (JWT):** Standard authentication for all protected endpoints
- **Demo Token:** Static `'demo_token'` for testing without setup
- **OAuth:** Google, Facebook, KakaoTalk (for 3rd-party integrations)

---

## Authentication

### JWT Authentication

All protected endpoints require Bearer token in Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Token Structure
```json
{
  "user_id": 1,
  "email": "user@softfactory.com",
  "role": "user",
  "exp": 1708951325,
  "iat": 1708947725
}
```

#### Token Lifetime
- **Access Token:** 1 hour
- **Refresh Token:** 30 days

### Demo Mode (Testing)

For quick testing without authentication setup:

```http
Authorization: Bearer demo_token
```

Demo user profile:
```json
{
  "user_id": 1,
  "email": "demo@softfactory.com",
  "role": "user",
  "subscription": "premium"
}
```

### OAuth Endpoints

#### Get Google OAuth URL
```http
GET /auth/oauth/google/url
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
    "state": "state_123abc"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

#### Google OAuth Callback
```http
GET /auth/oauth/google/callback?code=AUTH_CODE&state=STATE
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "user@gmail.com",
      "name": "John Doe"
    }
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Errors:**
- `400`: Invalid authorization code
- `401`: OAuth state mismatch
- `500`: OAuth provider error

---

## SNS LinkInBio Endpoints

Link-in-bio is a landing page that consolidates all your social media and monetization links.

### Create LinkInBio

```http
POST /sns/linkinbio
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "slug": "myprofile",
  "title": "My Professional Profile",
  "description": "Digital creator and coach",
  "links": [
    {
      "url": "https://instagram.com/myprofile",
      "label": "Instagram",
      "icon": "instagram",
      "order": 1
    },
    {
      "url": "https://youtube.com/@mychannel",
      "label": "YouTube",
      "icon": "youtube",
      "order": 2
    },
    {
      "url": "https://shop.mysite.com",
      "label": "Online Store",
      "icon": "shopping-cart",
      "order": 3
    }
  ],
  "theme": "dark",
  "bio": "Follow my journey",
  "analytics_enabled": true
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "linkinbio_001",
    "user_id": 1,
    "slug": "myprofile",
    "title": "My Professional Profile",
    "description": "Digital creator and coach",
    "links": [
      {
        "id": "link_001",
        "url": "https://instagram.com/myprofile",
        "label": "Instagram",
        "icon": "instagram",
        "order": 1,
        "click_count": 0
      }
    ],
    "theme": "dark",
    "bio": "Follow my journey",
    "analytics_enabled": true,
    "public_url": "https://softfactory.com/l/myprofile",
    "created_at": "2026-02-26T10:30:00Z",
    "updated_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Validations:**
- `slug`: 3-50 characters, alphanumeric + dash
- `links`: 1-50 items
- `theme`: `light`, `dark`, `neon`, `minimal`

**Errors:**
- `400`: Validation error (invalid slug format, duplicate slug)
- `401`: Unauthorized
- `422`: Business logic error (slug already taken)

### Get All LinkInBios

```http
GET /sns/linkinbio
Authorization: Bearer {token}
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort`: `created_at`, `updated_at`, `click_count` (default: `created_at`)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "linkinbio_001",
      "slug": "myprofile",
      "title": "My Professional Profile",
      "links_count": 3,
      "click_count": 1250,
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get LinkInBio Details

```http
GET /sns/linkinbio/{id}
Authorization: Bearer {token}
```

**Path Parameters:**
- `id`: LinkInBio ID

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "linkinbio_001",
    "slug": "myprofile",
    "title": "My Professional Profile",
    "description": "Digital creator and coach",
    "links": [
      {
        "id": "link_001",
        "url": "https://instagram.com/myprofile",
        "label": "Instagram",
        "icon": "instagram",
        "order": 1,
        "click_count": 500
      }
    ],
    "analytics": {
      "total_clicks": 1250,
      "clicks_today": 45,
      "clicks_this_week": 320,
      "clicks_this_month": 1250
    },
    "theme": "dark",
    "public_url": "https://softfactory.com/l/myprofile",
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Errors:**
- `404`: LinkInBio not found
- `401`: Unauthorized

### Update LinkInBio

```http
PUT /sns/linkinbio/{id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:** (partial update supported)
```json
{
  "title": "Updated Title",
  "links": [
    {
      "url": "https://instagram.com/newprofile",
      "label": "Instagram",
      "icon": "instagram",
      "order": 1
    }
  ],
  "theme": "light"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "linkinbio_001",
    "title": "Updated Title",
    "links": [...],
    "updated_at": "2026-02-26T10:35:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:35:00Z"
}
```

### Delete LinkInBio

```http
DELETE /sns/linkinbio/{id}
Authorization: Bearer {token}
```

**Response (204 No Content):**
```
(empty body)
```

**Errors:**
- `404`: LinkInBio not found
- `401`: Unauthorized

---

## SNS Automate Endpoints

Automatic content generation and scheduling for multiple SNS platforms.

### Create Automation Campaign

```http
POST /sns/automate
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Daily Fitness Tips",
  "topic": "fitness",
  "purpose": "engagement",
  "platforms": ["instagram", "tiktok", "youtube_shorts"],
  "frequency": "daily",
  "schedule_time": "09:00",
  "content_style": "motivational",
  "hashtags": ["fitness", "wellness", "gym"],
  "target_audience": "18-35, fitness enthusiasts",
  "ai_model": "claude-3-sonnet"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "automate_001",
    "user_id": 1,
    "name": "Daily Fitness Tips",
    "topic": "fitness",
    "purpose": "engagement",
    "platforms": ["instagram", "tiktok", "youtube_shorts"],
    "frequency": "daily",
    "schedule_time": "09:00",
    "content_style": "motivational",
    "status": "active",
    "next_post_at": "2026-02-26T09:00:00Z",
    "posts_generated": 0,
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Supported Platforms:**
- `instagram`, `facebook`, `twitter`, `tiktok`, `youtube_shorts`, `linkedin`, `pinterest`, `threads`, `youtube`

**Frequency Options:**
- `daily`, `3-daily`, `weekly`, `3-weekly`, `bi-weekly`, `monthly`

### Get Automation Campaigns

```http
GET /sns/automate
Authorization: Bearer {token}
```

**Query Parameters:**
- `status`: `active`, `paused`, `completed` (default: all)
- `platform`: Filter by platform (optional)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "automate_001",
      "name": "Daily Fitness Tips",
      "topic": "fitness",
      "platforms": ["instagram", "tiktok"],
      "frequency": "daily",
      "status": "active",
      "posts_generated": 15,
      "next_post_at": "2026-02-27T09:00:00Z",
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "total_pages": 1
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get Campaign Details

```http
GET /sns/automate/{id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "automate_001",
    "name": "Daily Fitness Tips",
    "topic": "fitness",
    "platforms": ["instagram", "tiktok"],
    "frequency": "daily",
    "schedule_time": "09:00",
    "content_style": "motivational",
    "hashtags": ["fitness", "wellness"],
    "status": "active",
    "ai_model": "claude-3-sonnet",
    "posts_generated": 15,
    "posts": [
      {
        "id": "post_001",
        "content": "Start your day with 10 minutes of stretching...",
        "image_url": "https://cdn.softfactory.com/auto_gen_001.jpg",
        "scheduled_at": "2026-02-27T09:00:00Z",
        "status": "scheduled"
      }
    ],
    "next_post_at": "2026-02-27T09:00:00Z",
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Update Campaign

```http
PUT /sns/automate/{id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:** (partial update)
```json
{
  "name": "Updated Fitness Tips",
  "frequency": "3-daily",
  "status": "paused"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "automate_001",
    "name": "Updated Fitness Tips",
    "frequency": "3-daily",
    "status": "paused",
    "updated_at": "2026-02-26T10:40:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:40:00Z"
}
```

### Delete Campaign

```http
DELETE /sns/automate/{id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

## SNS Trending Endpoints

Get trending hashtags and topics across SNS platforms.

### Get Trending Content

```http
GET /sns/trending
Authorization: Bearer {token}
```

**Query Parameters:**
- `platform`: `instagram`, `tiktok`, `twitter`, `youtube`, etc. (default: all)
- `category`: `fitness`, `fashion`, `food`, `tech`, `entertainment` (optional)
- `limit`: Max items (default: 20, max: 50)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "platform": "instagram",
    "hashtags": [
      {
        "name": "#fitnessmotivation",
        "popularity": 95,
        "trend_score": 8.7,
        "post_count": 2500000,
        "surge": true,
        "trend_direction": "up"
      },
      {
        "name": "#workoutchallenge",
        "popularity": 88,
        "trend_score": 7.9,
        "post_count": 1800000,
        "surge": false,
        "trend_direction": "stable"
      }
    ],
    "topics": [
      {
        "name": "Home Workouts",
        "relevance": 92,
        "mentions": 1200000,
        "growth_rate": 15
      }
    ],
    "updated_at": "2026-02-26T10:00:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## SNS ROI Endpoints

Calculate return on investment for SNS campaigns.

### Get ROI Metrics

```http
GET /sns/roi
Authorization: Bearer {token}
```

**Query Parameters:**
- `campaign_id`: Optional campaign ID filter
- `period`: `week`, `month`, `quarter`, `year` (default: month)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_campaigns": 5,
    "active_campaigns": 3,
    "metrics": {
      "total_reach": 250000,
      "total_engagement": 5200,
      "engagement_rate": 2.08,
      "conversion_rate": 0.42,
      "monthly_revenue": 12500,
      "monthly_cost": 800,
      "roi_percent": 1462.5,
      "payback_period_days": 8
    },
    "top_performing_campaigns": [
      {
        "campaign_id": "automate_001",
        "name": "Daily Fitness Tips",
        "reach": 85000,
        "engagement": 1800,
        "revenue": 4200,
        "roi_percent": 425
      }
    ],
    "period": "month",
    "calculated_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## Review Aggregation Endpoints

Unified collection of review opportunities from multiple platforms.

### Get Aggregated Reviews

```http
GET /review/aggregated
Authorization: Bearer {token}
```

**Query Parameters:**
- `category`: `fashion`, `beauty`, `food`, `electronics`, `home` (optional)
- `min_reward`: Minimum reward amount (optional, default: 0)
- `max_reward`: Maximum reward amount (optional)
- `status`: `open`, `closed`, `completed` (default: open)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)
- `sort`: `reward_desc`, `deadline`, `popularity` (default: reward_desc)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "listings": [
      {
        "id": "listing_001",
        "platform": "coupang",
        "product_name": "Wireless Earbuds Pro",
        "category": "electronics",
        "description": "Review our latest wireless earbuds",
        "reward": 50000,
        "reward_type": "coupon",
        "spots_available": 5,
        "spots_filled": 12,
        "required_followers": 1000,
        "required_engagement": 2.0,
        "deadline": "2026-03-15T23:59:59Z",
        "status": "open",
        "requirements": {
          "post_count": 1,
          "photo_count": 3,
          "video_required": true,
          "must_include_hashtags": ["#review", "#product"]
        },
        "created_at": "2026-02-20T10:00:00Z",
        "created_by": "brand_001"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 250,
      "total_pages": 5
    }
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Trigger Immediate Scrape

```http
POST /review/scrape/now
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "platforms": ["coupang", "naver_shopping"],
  "categories": ["fashion", "beauty"],
  "priority": "high"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "task_id": "scrape_task_001",
    "status": "queued",
    "platforms": ["coupang", "naver_shopping"],
    "estimated_duration_seconds": 120,
    "queued_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get Scrape Task Status

```http
GET /review/scrape/status/{task_id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "task_id": "scrape_task_001",
    "status": "completed",
    "progress": 100,
    "new_listings": 42,
    "updated_listings": 15,
    "started_at": "2026-02-26T10:30:00Z",
    "completed_at": "2026-02-26T10:32:15Z",
    "duration_seconds": 135
  },
  "error": null,
  "timestamp": "2026-02-26T10:32:15Z"
}
```

---

## Review Account Endpoints

Manage influencer accounts for review campaigns.

### Create Account

```http
POST /review/accounts
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "platform": "instagram",
  "account_name": "@fashionista_style",
  "follower_count": 25000,
  "engagement_rate": 3.5,
  "category_tags": ["fashion", "lifestyle", "beauty"],
  "bio": "Fashion blogger & style influencer",
  "verified": true
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "account_001",
    "user_id": 1,
    "platform": "instagram",
    "account_name": "@fashionista_style",
    "follower_count": 25000,
    "engagement_rate": 3.5,
    "category_tags": ["fashion", "lifestyle", "beauty"],
    "score": 8.2,
    "eligible_listings": 45,
    "completed_reviews": 12,
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get All Accounts

```http
GET /review/accounts
Authorization: Bearer {token}
```

**Query Parameters:**
- `platform`: Filter by platform (optional)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "account_001",
      "platform": "instagram",
      "account_name": "@fashionista_style",
      "follower_count": 25000,
      "engagement_rate": 3.5,
      "score": 8.2,
      "eligible_listings": 45,
      "completed_reviews": 12
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "total_pages": 1
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Update Account

```http
PUT /review/accounts/{id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:** (partial update)
```json
{
  "follower_count": 26000,
  "engagement_rate": 3.8,
  "category_tags": ["fashion", "lifestyle", "beauty", "sustainability"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "account_001",
    "follower_count": 26000,
    "engagement_rate": 3.8,
    "category_tags": ["fashion", "lifestyle", "beauty", "sustainability"],
    "score": 8.4,
    "updated_at": "2026-02-26T10:35:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:35:00Z"
}
```

### Delete Account

```http
DELETE /review/accounts/{id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

## Review Application Endpoints

Submit and manage applications for review campaigns.

### Create Application

```http
POST /review/applications
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "listing_id": "listing_001",
  "account_id": "account_001",
  "message": "Great product! I'd love to review this.",
  "proposed_post_date": "2026-03-05T00:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "application_001",
    "user_id": 1,
    "listing_id": "listing_001",
    "account_id": "account_001",
    "status": "pending",
    "match_score": 0.92,
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Match Score Calculation:**
- Account followers ÷ Required followers = 0-100%
- Engagement rate comparison = 0-100%
- Category tag match = 0-100%
- Previous review quality = 0-100%
- Final Score = Average of above

### Get Applications

```http
GET /review/applications
Authorization: Bearer {token}
```

**Query Parameters:**
- `status`: `pending`, `accepted`, `rejected`, `completed` (default: all)
- `listing_id`: Filter by listing (optional)
- `account_id`: Filter by account (optional)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "application_001",
      "listing_id": "listing_001",
      "account_id": "account_001",
      "account_name": "@fashionista_style",
      "product_name": "Wireless Earbuds Pro",
      "status": "pending",
      "match_score": 0.92,
      "submitted_at": "2026-02-26T10:30:00Z",
      "response_at": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8,
    "total_pages": 1
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get Application Details

```http
GET /review/applications/{id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "application_001",
    "listing_id": "listing_001",
    "account_id": "account_001",
    "status": "pending",
    "match_score": 0.92,
    "message": "Great product! I'd love to review this.",
    "proposed_post_date": "2026-03-05T00:00:00Z",
    "brand_response": null,
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## Review AutoApply Endpoints

Configure automatic application rules for matching campaigns.

### Create AutoApply Rule

```http
POST /review/auto-apply/rules
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Fashion Brands Auto-Apply",
  "description": "Auto-apply to all fashion brands with rewards > 20000",
  "categories": ["fashion", "beauty"],
  "min_reward": 20000,
  "min_followers": 10000,
  "min_engagement_rate": 2.0,
  "excluded_brands": ["brand_banned_001"],
  "is_active": true,
  "auto_message": "I'm very interested in reviewing this product!"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "rule_001",
    "user_id": 1,
    "name": "Fashion Brands Auto-Apply",
    "categories": ["fashion", "beauty"],
    "min_reward": 20000,
    "min_followers": 10000,
    "min_engagement_rate": 2.0,
    "is_active": true,
    "matching_listings": 15,
    "auto_applied_count": 0,
    "created_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Get AutoApply Rules

```http
GET /review/auto-apply/rules
Authorization: Bearer {token}
```

**Query Parameters:**
- `is_active`: true, false (optional)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "rule_001",
      "name": "Fashion Brands Auto-Apply",
      "categories": ["fashion", "beauty"],
      "min_reward": 20000,
      "is_active": true,
      "matching_listings": 15,
      "auto_applied_count": 8,
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Update AutoApply Rule

```http
PUT /review/auto-apply/rules/{id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:** (partial update)
```json
{
  "min_reward": 25000,
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "rule_001",
    "min_reward": 25000,
    "is_active": false,
    "updated_at": "2026-02-26T10:35:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:35:00Z"
}
```

### Run AutoApply Now

```http
POST /review/auto-apply/run
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "rule_id": "rule_001",
  "dry_run": false
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "task_id": "autoapply_task_001",
    "rule_id": "rule_001",
    "status": "running",
    "applied_count": 0,
    "failed_count": 0,
    "queued_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Delete AutoApply Rule

```http
DELETE /review/auto-apply/rules/{id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

## Error Handling

### Standard Error Response Format

All errors follow this structure:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success (GET, PUT) | List items, update successful |
| 201 | Created | POST endpoint successfully created resource |
| 202 | Accepted | Async task queued (scraping, auto-apply) |
| 204 | No Content | DELETE successful |
| 400 | Bad Request | Invalid JSON, validation error |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | User not authorized for this resource |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate slug, duplicate entry |
| 422 | Unprocessable Entity | Business logic error (e.g., slug taken) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unexpected error on server |
| 502 | Bad Gateway | Upstream service down |
| 503 | Service Unavailable | Maintenance mode |

### Common Error Codes

| Code | Meaning |
|------|---------|
| `AUTH_REQUIRED` | Token missing or invalid |
| `AUTH_EXPIRED` | Token expired, need refresh |
| `PERMISSION_DENIED` | User doesn't have permission |
| `VALIDATION_ERROR` | Request body validation failed |
| `RESOURCE_NOT_FOUND` | Resource not found |
| `DUPLICATE_ENTRY` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `BUSINESS_LOGIC_ERROR` | Business rule violated |
| `EXTERNAL_SERVICE_ERROR` | Third-party service failed |
| `DATABASE_ERROR` | Database operation failed |

### Example Error Responses

**Validation Error (400):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "slug": "Invalid format. Must be 3-50 alphanumeric characters.",
      "links": "Must have at least 1 link."
    }
  },
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Authentication Error (401):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required",
    "details": {
      "hint": "Include 'Authorization: Bearer {token}' header"
    }
  },
  "timestamp": "2026-02-26T10:30:00Z"
}
```

**Not Found (404):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "LinkInBio not found",
    "details": {
      "id": "linkinbio_001"
    }
  },
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## Rate Limiting

All API requests are rate-limited to prevent abuse.

### Rate Limit Headers

Each response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1708947900
```

### Rate Limits by Endpoint Category

| Category | Requests | Window | Note |
|----------|----------|--------|------|
| General API | 100 | 60 seconds | Most endpoints |
| Authentication | 10 | 60 seconds | Login, token refresh |
| Scraping/Crawling | 10 | 60 seconds | Auto-scrape endpoints |
| Search/Trending | 50 | 60 seconds | Trending endpoints |
| File Upload | 5 | 60 seconds | Media uploads |

### Handling Rate Limits

When rate limit is exceeded, response is:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "retry_after_seconds": 45,
      "limit": 100,
      "window_seconds": 60
    }
  },
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## Response Formats

### Standard Success Response

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Async Task Response

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "status": "queued|running|completed|failed",
    "progress": 0,
    "queued_at": "2026-02-26T10:30:00Z"
  },
  "error": null,
  "timestamp": "2026-02-26T10:30:00Z"
}
```

---

## Date/Time Format

All timestamps use ISO 8601 format with UTC timezone:

```
2026-02-26T10:30:00Z
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-02-26 | M-007: SNS v3.0 + Review v3.0 complete API spec |
| 2.1.0 | 2026-02-25 | Infrastructure upgrade, added metrics endpoints |
| 2.0.0 | 2026-02-22 | Multi-service consolidation |

---

**Document maintained by:** Team J (Documentation + Deployment)
**Last reviewed:** 2026-02-26
**Status:** Production-Ready ✅
