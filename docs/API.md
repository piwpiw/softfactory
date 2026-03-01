# 🔌 CooCook API Specification v1.0

> **Purpose**: | Property | Value |
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 CooCook API Specification v1.0 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> OpenAPI 3.1 | REST Level 3 (HATEOAS) | ISO 8601 Timestamps

---

## 📋 Base Information

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.coocook.com/api/v1` |
| **Auth** | Bearer Token (JWT) |
| **Content-Type** | `application/json` |
| **Pagination** | Cursor-based |

---

## 🔐 Authentication

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📚 Core Endpoints

### 1. Recipes

#### List Recipes (Personalized)
```http
GET /recipes?limit=20&cursor=abc123&tags=vegetarian
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "recipe_001",
      "title": "Thai Green Curry",
      "cuisine": "Thai",
      "difficulty": "MEDIUM",
      "prep_time_mins": 25,
      "cook_time_mins": 30,
      "servings": 4,
      "rating": 4.8,
      "tags": ["vegetarian", "spicy", "quick"],
      "image_url": "https://cdn.coocook.com/recipes/001.jpg",
      "chef_id": "chef_123",
      "chef_name": "Sara",
      "_links": {
        "self": { "href": "/recipes/recipe_001" },
        "chef": { "href": "/chefs/chef_123" },
        "reviews": { "href": "/recipes/recipe_001/reviews" }
      }
    }
  ],
  "pagination": {
    "cursor": "next_cursor_123",
    "has_more": true,
    "total": 4521
  }
}
```

#### Get Recipe Details
```http
GET /recipes/{recipe_id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "recipe_001",
  "title": "Thai Green Curry",
  "description": "Authentic Bangkok-style green curry...",
  "ingredients": [
    { "name": "Coconut milk", "quantity": 400, "unit": "ml" },
    { "name": "Green curry paste", "quantity": 3, "unit": "tbsp" }
  ],
  "instructions": [
    { "step": 1, "description": "Heat coconut milk..." },
    { "step": 2, "description": "Add curry paste..." }
  ],
  "nutrition": {
    "calories": 280,
    "protein_g": 12,
    "carbs_g": 8,
    "fat_g": 22
  },
  "reviews_summary": {
    "count": 342,
    "avg_rating": 4.8
  }
}
```

#### Create Recipe (Chef Only)
```http
POST /recipes
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "New Recipe",
  "cuisine": "Italian",
  "ingredients": [...],
  "instructions": [...],
  "prep_time_mins": 20,
  "cook_time_mins": 30,
  "servings": 4,
  "price_usd": 0
}
```

**Response (201 Created):**
```json
{
  "id": "recipe_new_001",
  "title": "New Recipe",
  "status": "PUBLISHED",
  "created_at": "2026-02-23T10:30:00Z",
  "_links": {
    "self": { "href": "/recipes/recipe_new_001" },
    "edit": { "href": "/recipes/recipe_new_001", "method": "PATCH" }
  }
}
```

---

### 2. Chef Bookings

#### Search Available Chefs
```http
GET /chefs/available?location=Bangkok&date=2026-02-28&party_size=4
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "chef_123",
      "name": "Marco",
      "cuisine_specialties": ["Italian", "Mediterranean"],
      "rating": 4.9,
      "reviews": 156,
      "price_per_hour_usd": 85,
      "availability": {
        "date": "2026-02-28",
        "time_slots": [
          { "start": "18:00", "end": "22:00", "available": true }
        ]
      },
      "_links": {
        "book": { "href": "/chefs/chef_123/bookings", "method": "POST" }
      }
    }
  ],
  "pagination": { "total": 24 }
}
```

#### Create Booking
```http
POST /chefs/{chef_id}/bookings
Authorization: Bearer {token}

{
  "date": "2026-02-28",
  "start_time": "18:00",
  "duration_hours": 4,
  "party_size": 4,
  "dietary_preferences": ["vegetarian", "gluten_free"],
  "special_requests": "Birthday celebration"
}
```

**Response (201 Created):**
```json
{
  "booking_id": "booking_001",
  "chef_id": "chef_123",
  "status": "CONFIRMED",
  "total_price_usd": 340,
  "confirmation_code": "COO-2026-0001",
  "meeting_point": { "lat": 13.7563, "lng": 100.5018 },
  "_links": {
    "confirm": { "href": "/bookings/booking_001/confirm", "method": "POST" },
    "cancel": { "href": "/bookings/booking_001/cancel", "method": "POST" }
  }
}
```

---

### 3. User Preferences & Personalization

#### Update User Preferences
```http
PATCH /users/me/preferences
Authorization: Bearer {token}

{
  "dietary_restrictions": ["gluten_free"],
  "cuisine_preferences": ["Thai", "Italian", "Mediterranean"],
  "spice_level": 3,
  "budget_per_meal_usd": [10, 50],
  "allergies": ["peanuts", "shellfish"]
}
```

**Response (200 OK):**
```json
{
  "user_id": "user_001",
  "preferences_updated": true,
  "personalization_score": 0.87,
  "_links": {
    "personalized_recommendations": { "href": "/recipes/recommendations" }
  }
}
```

#### Get AI Recommendations
```http
GET /recommendations?limit=10&type=recipe
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "recommendations": [
    {
      "recipe_id": "recipe_042",
      "title": "Thai Basil Chicken",
      "match_score": 0.94,
      "reason": "Matches your spice level & cuisine preference",
      "personalization_factors": ["spice_level", "cuisine_preference", "prep_time"]
    }
  ]
}
```

---

### 4. Reviews & Ratings

#### Submit Review
```http
POST /recipes/{recipe_id}/reviews
Authorization: Bearer {token}

{
  "rating": 5,
  "title": "Amazing!",
  "content": "Turned out perfectly. Highly recommend!",
  "photos": ["photo_id_1", "photo_id_2"]
}
```

**Response (201 Created):**
```json
{
  "review_id": "review_001",
  "recipe_id": "recipe_001",
  "rating": 5,
  "created_at": "2026-02-23T10:35:00Z",
  "_links": {
    "self": { "href": "/reviews/review_001" }
  }
}
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "INVALID_PARAMS",
    "message": "Missing required field: title",
    "details": [
      { "field": "title", "reason": "required" }
    ]
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid or expired token"
  }
}
```

### 429 Too Many Requests
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after_seconds": 60
  }
}
```

---

## 🔄 Rate Limits

| Plan | Requests/min | Requests/day |
|------|-------------|-------------|
| **Free** | 10 | 1,000 |
| **Pro** | 100 | 50,000 |
| **Enterprise** | Unlimited | Unlimited |

---

## 📊 Webhook Events

```http
POST {your_webhook_url}

{
  "event_type": "booking.confirmed",
  "timestamp": "2026-02-23T10:30:00Z",
  "data": {
    "booking_id": "booking_001",
    "chef_id": "chef_123"
  }
}
```

**Supported Events:**
- `recipe.created` / `recipe.updated` / `recipe.deleted`
- `booking.confirmed` / `booking.completed` / `booking.cancelled`
- `user.joined` / `user.subscription_renewed`

---

## 🔗 Response Format (HATEOAS)

All responses include `_links` for navigation:
```json
{
  "data": {...},
  "_links": {
    "self": { "href": "/recipes/001", "method": "GET" },
    "update": { "href": "/recipes/001", "method": "PATCH" },
    "delete": { "href": "/recipes/001", "method": "DELETE" },
    "reviews": { "href": "/recipes/001/reviews" }
  }
}
```

---

## 📖 SDK Integration

**JavaScript/Node.js:**
```javascript
const coocook = require('@coocook/sdk');
const client = new coocook.Client({ token: 'your_token' });

const recipes = await client.recipes.list({ tags: ['vegetarian'] });
```

**Python:**
```python
from coocook import Client
client = Client(token='your_token')
recipes = client.recipes.list(tags=['vegetarian'])
```