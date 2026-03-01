# Review Scraper API - Complete Reference

**Version:** 2.0.0
**Last Updated:** 2026-02-26
**Base URL:** `http://localhost:8000/api` (dev) | `https://api.softfactory.com/api` (prod)
**Authentication:** Bearer token (JWT)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Listings & Aggregation](#listings--aggregation)
3. [Application Management](#application-management)
4. [Auto-Apply Rules](#auto-apply-rules)
5. [Rewards & Tracking](#rewards--tracking)
6. [Analytics](#analytics)

---

## Overview

The Review Scraper API aggregates review opportunities from multiple platforms (Revu, ReviewPlace, MarketPlace, etc.) and provides intelligent matching, auto-apply, and reward tracking.

**Supported Platforms:**
- Revu (Korean review community)
- ReviewPlace
- MarketPlace
- And more...

**Supported Categories:**
- 뷰티 (Beauty)
- 패션 (Fashion)
- 일렉트로닉스 (Electronics)
- 푸드 (Food)
- 라이프스타일 (Lifestyle)
- 가정용품 (Home & Garden)
- 스포츠 (Sports)
- 게임 (Gaming)

---

## Listings & Aggregation

### GET /review/aggregated
**Get aggregated review listings (cross-platform)**

**Query Parameters:**
```
GET /review/aggregated?category=뷰티&platform=revu&min_reward=50000&max_reward=500000&sort_by=deadline&limit=20&page=1
```

| Parameter | Type | Optional | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | Yes | null | 뷰티, 패션, 일렉트로닉스, 푸드, 라이프스타일, 가정용품, 스포츠, 게임 |
| `platform` | string | Yes | null | revu, reviewplace, marketplace, ... |
| `reward_type` | string | Yes | null | product, cash, mixed, affiliate |
| `min_reward` | number | Yes | 0 | Minimum reward value (KRW) |
| `max_reward` | number | Yes | null | Maximum reward value (KRW) |
| `sort_by` | string | Yes | created | deadline, reward, created, applicants |
| `order` | string | Yes | asc | asc, desc |
| `status` | string | Yes | open | open, closing_soon, closed, expired |
| `limit` | number | Yes | 20 | Items per page (max: 100) |
| `page` | number | Yes | 1 | Page number |
| `search` | string | Yes | null | Free text search |

**Response (200 OK):**
```json
{
  "listings": [
    {
      "id": "revu_12345",
      "source_platform": "revu",
      "source_url": "https://revu.com/campaigns/12345",
      "title": "신제품 뷰티 리뷰",
      "description": "새로운 스킨케어 제품의 리뷰를 작성해주실 분을 찾습니다",
      "brand": {
        "id": "brand_001",
        "name": "BeautyBrand",
        "logo_url": "https://cdn.example.com/brand-logo.jpg"
      },
      "category": "뷰티",
      "subcategory": "스킨케어",
      "reward": {
        "type": "product",
        "value": 150000,
        "value_krw": "₩150,000",
        "currency": "KRW",
        "includes_cash": false,
        "cash_amount": 0,
        "product_details": {
          "name": "Advanced Serum 50ml",
          "estimated_value": 150000
        }
      },
      "requirements": {
        "follower_min": 1000,
        "follower_max": null,
        "engagement_rate_min": 0.5,
        "account_age_days": 30,
        "location_required": ["KR"],
        "language": "ko",
        "content_format": ["instagram", "tiktok", "blog"]
      },
      "dates": {
        "posting_deadline": "2026-03-31T23:59:59Z",
        "application_deadline": "2026-03-25T23:59:59Z",
        "days_until_deadline": 28,
        "status": "open"
      },
      "applications": {
        "max_applicants": 50,
        "current_applicants": 23,
        "spots_available": 27,
        "application_rate": 46
      },
      "creator_requirements": {
        "must_have_content": ["unboxing", "first_impression", "review"],
        "hashtags_required": 5,
        "mentions_required": 1,
        "review_length_min": 500
      },
      "matching_score": 95,
      "match_reason": "Your engagement rate is excellent for this category",
      "similar_listings": 3
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 523,
    "pages": 27
  },
  "filters_applied": {
    "category": "뷰티",
    "platform": null,
    "reward_range": "50000-500000"
  },
  "summary": {
    "total_listings": 523,
    "average_reward": 185000,
    "highest_reward": 2000000,
    "closing_soon_count": 15
  }
}
```

---

### GET /review/listing/{listing_id}
**Get detailed listing information**

**Response (200 OK):** Extended listing object with:
- Full brand information
- Complete requirements
- Similar listings
- Matching analysis
- Application history

---

### GET /review/categories
**Get available categories and subcategories**

**Response (200 OK):**
```json
{
  "categories": [
    {
      "id": "beauty",
      "name": "뷰티",
      "count": 245,
      "subcategories": [
        {
          "id": "skincare",
          "name": "스킨케어",
          "count": 120
        },
        {
          "id": "makeup",
          "name": "메이크업",
          "count": 85
        },
        {
          "id": "haircare",
          "name": "헤어케어",
          "count": 40
        }
      ]
    },
    {
      "id": "fashion",
      "name": "패션",
      "count": 189,
      "subcategories": [...]
    }
  ]
}
```

---

### GET /review/platforms
**Get available platforms and their listing counts**

**Response (200 OK):**
```json
{
  "platforms": [
    {
      "id": "revu",
      "name": "Revu",
      "total_listings": 300,
      "active_listings": 278,
      "last_sync": "2026-02-26T10:30:00Z"
    },
    {
      "id": "reviewplace",
      "name": "ReviewPlace",
      "total_listings": 150,
      "active_listings": 142,
      "last_sync": "2026-02-26T10:25:00Z"
    }
  ]
}
```

---

## Application Management

### POST /review/application
**Apply for a review listing**

**Request Body:**
```json
{
  "listing_id": "revu_12345",
  "platform": "revu",
  "application_message": "I'm very interested in this review opportunity! I have extensive experience with skincare products.",
  "portfolio_url": "https://instagram.com/myprofile",
  "terms_accepted": true
}
```

**Response (201 Created):**
```json
{
  "id": "app_12345",
  "listing_id": "revu_12345",
  "status": "submitted",
  "submitted_at": "2026-02-26T10:30:00Z",
  "listing_details": {
    "title": "신제품 뷰티 리뷰",
    "brand": "BeautyBrand",
    "reward_value": 150000
  },
  "application_status_url": "https://softfactory.com/apps/app_12345"
}
```

---

### GET /review/application
**List all applications (user's)**

**Query Parameters:**
- `status` (string, optional): submitted, approved, rejected, completed, withdrawn
- `sort_by` (string, optional): submitted_at, deadline, reward (default: submitted_at)
- `limit` (integer, optional): default 20, max 100
- `page` (integer, optional): default 1

**Response (200 OK):**
```json
{
  "applications": [
    {
      "id": "app_12345",
      "listing_id": "revu_12345",
      "title": "신제품 뷰티 리뷰",
      "brand": "BeautyBrand",
      "reward": 150000,
      "status": "approved",
      "submitted_at": "2026-02-20T10:30:00Z",
      "deadline": "2026-03-31T23:59:59Z",
      "days_until_deadline": 34,
      "approval_date": "2026-02-21T08:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "pages": 1
  },
  "summary": {
    "total_applications": 15,
    "approved": 8,
    "pending": 3,
    "rejected": 2,
    "completed": 2
  }
}
```

---

### GET /review/application/{app_id}
**Get application details**

**Response (200 OK):**
```json
{
  "id": "app_12345",
  "listing_id": "revu_12345",
  "status": "approved",
  "submitted_at": "2026-02-20T10:30:00Z",
  "approval_date": "2026-02-21T08:15:00Z",
  "listing": {
    "title": "신제품 뷰티 리뷰",
    "brand": "BeautyBrand",
    "category": "뷰티",
    "reward": 150000,
    "deadline": "2026-03-31T23:59:59Z"
  },
  "approval_details": {
    "reason": "Great engagement rate and relevant followers",
    "contact_info": {
      "email": "contact@beautybrand.com",
      "phone": "+82-10-1234-5678"
    }
  },
  "next_steps": [
    "Wait for brand to send product",
    "Create review content",
    "Post by deadline",
    "Receive reward"
  ]
}
```

---

### POST /review/application/{app_id}/withdraw
**Withdraw application**

**Response (200 OK):**
```json
{
  "id": "app_12345",
  "status": "withdrawn",
  "withdrawn_at": "2026-02-26T10:35:00Z"
}
```

---

## Auto-Apply Rules

### POST /review/auto-apply/rule
**Create auto-apply rule**

**Request Body:**
```json
{
  "name": "My Beauty Rule",
  "enabled": true,
  "conditions": {
    "categories": ["뷰티"],
    "platforms": ["revu", "reviewplace"],
    "min_reward": 100000,
    "max_reward": 500000,
    "reward_type": ["product", "cash"],
    "min_followers": 1000,
    "max_followers": null,
    "required_engagement_rate": 0.5,
    "required_account_age_days": 30
  },
  "auto_apply_enabled": true,
  "auto_withdraw_enabled": false,
  "priority": 1,
  "notification_settings": {
    "notify_on_match": true,
    "notify_on_auto_applied": true,
    "notify_on_approval": true
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "My Beauty Rule",
  "enabled": true,
  "auto_apply_enabled": true,
  "created_at": "2026-02-26T10:30:00Z",
  "stats": {
    "total_matches": 0,
    "auto_applied": 0,
    "approved": 0
  }
}
```

---

### GET /review/auto-apply/rule
**List auto-apply rules**

**Response (200 OK):**
```json
{
  "rules": [
    {
      "id": 1,
      "name": "My Beauty Rule",
      "enabled": true,
      "priority": 1,
      "stats": {
        "matches": 45,
        "auto_applied": 12,
        "approved": 8,
        "rejected": 4
      },
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "total": 3,
  "active_rules": 3
}
```

---

### PUT /review/auto-apply/rule/{rule_id}
**Update auto-apply rule**

**Response (200 OK):** Updated rule object

---

### DELETE /review/auto-apply/rule/{rule_id}
**Delete auto-apply rule**

**Response (204 No Content)**

---

### GET /review/auto-apply/history
**View auto-apply history**

**Query Parameters:**
- `rule_id` (integer, optional): Filter by rule
- `status` (string, optional): success, failed
- `limit` (integer, optional): default 20
- `page` (integer, optional): default 1

**Response (200 OK):**
```json
{
  "history": [
    {
      "id": "apply_12345",
      "rule_id": 1,
      "listing_id": "revu_12345",
      "applied_at": "2026-02-26T10:35:00Z",
      "status": "success",
      "message": "Successfully applied to listing"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## Rewards & Tracking

### GET /review/rewards
**Get reward summary and tracking**

**Query Parameters:**
- `status` (string, optional): pending, received, expired
- `date_from` (string, optional): ISO 8601 date
- `date_to` (string, optional): ISO 8601 date

**Response (200 OK):**
```json
{
  "summary": {
    "total_pending_value": 1200000,
    "total_received_value": 8450000,
    "total_expired_value": 250000,
    "total_applications": 15,
    "approval_rate": 53.3
  },
  "pending_rewards": [
    {
      "id": "app_12345",
      "brand": "BeautyBrand",
      "reward_type": "product",
      "reward_value": 150000,
      "status": "pending",
      "deadline": "2026-03-31T23:59:59Z",
      "days_until_deadline": 34
    }
  ],
  "received_rewards": [
    {
      "id": "app_11111",
      "brand": "FashionBrand",
      "reward_type": "cash",
      "reward_value": 500000,
      "status": "received",
      "received_date": "2026-02-20T10:30:00Z"
    }
  ]
}
```

---

### GET /review/rewards/{reward_id}
**Get detailed reward tracking**

**Response (200 OK):**
```json
{
  "id": "app_12345",
  "brand": "BeautyBrand",
  "reward": {
    "type": "product",
    "value": 150000,
    "details": "Advanced Serum 50ml",
    "estimated_value": 150000
  },
  "timeline": [
    {
      "event": "application_submitted",
      "date": "2026-02-20T10:30:00Z"
    },
    {
      "event": "application_approved",
      "date": "2026-02-21T08:15:00Z"
    },
    {
      "event": "product_shipped",
      "date": "2026-02-23T14:00:00Z",
      "tracking_number": "123456789"
    }
  ],
  "status": "in_transit",
  "expected_delivery": "2026-03-02T23:59:59Z",
  "content_deadline": "2026-03-31T23:59:59Z"
}
```

---

### POST /review/rewards/{reward_id}/confirm-received
**Confirm reward received**

**Request Body:**
```json
{
  "received_date": "2026-02-26T10:30:00Z",
  "photos": [
    {
      "url": "https://cdn.example.com/photo1.jpg",
      "description": "Product packaging"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "id": "app_12345",
  "status": "received",
  "received_date": "2026-02-26T10:30:00Z",
  "message": "Reward confirmed received"
}
```

---

## Analytics

### GET /review/analytics/dashboard
**Get review analytics dashboard**

**Query Parameters:**
- `date_from` (string, optional): ISO 8601 date (default: 30 days ago)
- `date_to` (string, optional): ISO 8601 date (default: today)

**Response (200 OK):**
```json
{
  "period": {
    "from": "2026-01-27T00:00:00Z",
    "to": "2026-02-26T23:59:59Z",
    "days": 30
  },
  "overview": {
    "applications_submitted": 15,
    "applications_approved": 8,
    "approval_rate": 53.3,
    "total_rewards_value": 8450000,
    "average_reward": 562500,
    "highest_reward": 2000000
  },
  "by_category": {
    "뷰티": {
      "applications": 8,
      "approved": 5,
      "total_value": 1200000
    },
    "패션": {
      "applications": 4,
      "approved": 2,
      "total_value": 350000
    }
  },
  "by_platform": {
    "revu": {
      "applications": 10,
      "approved": 6,
      "total_value": 1600000
    },
    "reviewplace": {
      "applications": 5,
      "approved": 2,
      "total_value": 350000
    }
  },
  "trends": {
    "most_active_day": "Wednesday",
    "best_approval_category": "뷰티",
    "average_time_to_approval": "1.2 days"
  }
}
```

---

### GET /review/analytics/earnings
**Track earnings over time**

**Response (200 OK):**
```json
{
  "monthly": [
    {
      "month": "2026-02",
      "earned": 8450000,
      "applications": 15,
      "approved": 8
    },
    {
      "month": "2026-01",
      "earned": 5200000,
      "applications": 10,
      "approved": 5
    }
  ],
  "total_lifetime": 45000000,
  "average_monthly": 5625000
}
```

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
- `LISTING_NOT_FOUND`: Review listing not found
- `ALREADY_APPLIED`: Already applied to this listing
- `INELIGIBLE`: User doesn't meet requirements
- `LISTING_CLOSED`: Application deadline passed
- `QUOTA_EXCEEDED`: Maximum applicants reached
- `VALIDATION_ERROR`: Input validation failed

---

## Rate Limiting

- **Free tier:** 500 requests/hour
- **Professional:** 5,000 requests/hour
- **Enterprise:** Unlimited

---

## Pagination

All list endpoints support pagination with `page` and `limit` parameters.

---

**Last Updated:** 2026-02-26
**Status:** Production Ready ✅
