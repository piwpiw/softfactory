# CooCook Feed API Documentation

## Overview

The CooCook Feed API provides social features for recipe discovery, community interaction, and user engagement. It includes endpoints for managing reviews, likes, follows, and personalized feeds.

**Base URL:** `/api/coocook`
**Authentication:** All endpoints except `/recipes/{id}/reviews` require JWT authentication

---

## Endpoints

### 1. Get User Feed

Retrieve a personalized feed of recipes from followed chefs and activities from followed users.

**Endpoint:** `GET /feed`
**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Number of items to return (default: 20, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response:** 200 OK
```json
{
  "feed": [
    {
      "id": 1,
      "activity_type": "new_recipe",
      "content": {
        "recipe_id": 42,
        "title": "Bibimbap",
        "chef_id": 5,
        "chef_name": "Chef Park"
      },
      "created_at": "2026-02-26T10:30:00Z",
      "timestamp": "2026-02-26T10:35:00Z"
    }
  ],
  "total": 150,
  "has_more": true,
  "next_offset": 20,
  "timestamp": "2026-02-26T10:35:00Z"
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "error": "Feed generation failed: [error message]"
}
```

---

### 2. Post Recipe Review

Submit a review for a recipe with rating, text, and photos.

**Endpoint:** `POST /recipes/{recipe_id}/review`
**Authentication:** Required

**Path Parameters:**
- `recipe_id` (integer): Recipe ID

**Request Body:**
```json
{
  "rating": 5,
  "text": "Amazing recipe! Very easy to follow.",
  "photos": [
    "https://example.com/photo1.jpg",
    "https://example.com/photo2.jpg"
  ]
}
```

**Validation Rules:**
- `rating`: Integer between 1 and 5 (required)
- `text`: String, max 500 characters
- `photos`: Array of URLs (optional)

**Response:** 200 OK
```json
{
  "success": true,
  "review_id": 123,
  "message": "Review posted successfully"
}
```

**Error Responses:**
- 400 Bad Request: Missing or invalid rating
```json
{
  "success": false,
  "message": "Rating must be 1-5"
}
```
- 400 Bad Request: Text too long
```json
{
  "success": false,
  "message": "Review text too long (max 500)"
}
```
- 500 Internal Server Error
```json
{
  "success": false,
  "message": "Review creation failed: [error message]"
}
```

---

### 3. Get Recipe Reviews

Retrieve reviews for a recipe with pagination and sorting.

**Endpoint:** `GET /recipes/{recipe_id}/reviews`
**Authentication:** Not required

**Path Parameters:**
- `recipe_id` (integer): Recipe ID

**Query Parameters:**
- `page` (integer, optional): Page number, 1-indexed (default: 1)
- `per_page` (integer, optional): Reviews per page (default: 10, max: 50)
- `sort` (string, optional): Sort order
  - `recent`: Newest first (default)
  - `helpful`: Most helpful first
  - `rating_high`: Highest rated first
  - `rating_low`: Lowest rated first

**Response:** 200 OK
```json
{
  "reviews": [
    {
      "id": 123,
      "recipe_id": 42,
      "user_id": 10,
      "user_name": "John Doe",
      "rating": 5,
      "text": "Amazing recipe!",
      "photos": ["url1.jpg", "url2.jpg"],
      "helpful_count": 15,
      "unhelpful_count": 2,
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "total_pages": 5,
  "average_rating": 4.6,
  "rating_distribution": {
    "1": 2,
    "2": 1,
    "3": 5,
    "4": 10,
    "5": 27
  },
  "has_more": true
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "error": "Review retrieval failed: [error message]"
}
```

---

### 4. Like Recipe

Like or unlike a recipe (toggle action).

**Endpoint:** `POST /recipes/{recipe_id}/like`
**Authentication:** Required

**Path Parameters:**
- `recipe_id` (integer): Recipe ID

**Request Body:** (empty or null)

**Response:** 200 OK
```json
{
  "success": true,
  "liked": true,
  "message": "Recipe liked",
  "like_count": 42
}
```

Or if unliking:
```json
{
  "success": true,
  "liked": false,
  "message": "Recipe unliked",
  "like_count": 41
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "success": false,
  "message": "Like action failed: [error message]"
}
```

---

### 5. Follow Chef

Follow or unfollow a chef (toggle action).

**Endpoint:** `POST /chefs/{chef_id}/follow`
**Authentication:** Required

**Path Parameters:**
- `chef_id` (integer): Chef ID (User ID with Chef profile)

**Request Body:** (empty or null)

**Response:** 200 OK
```json
{
  "success": true,
  "following": true,
  "message": "Chef followed"
}
```

Or if unfollowing:
```json
{
  "success": true,
  "following": false,
  "message": "Chef unfollowed"
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "success": false,
  "message": "Follow action failed: [error message]"
}
```

---

### 6. Get User Profile

Get the authenticated user's profile with statistics and recent activity.

**Endpoint:** `GET /user/profile`
**Authentication:** Required

**Query Parameters:** None

**Response:** 200 OK
```json
{
  "success": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "avatar_url": "https://example.com/avatar.jpg",
    "created_at": "2026-01-15T00:00:00Z"
  },
  "stats": {
    "cooking_sessions": 12,
    "saved_recipes": 35,
    "followers": 150,
    "following": 45,
    "reviews_posted": 23,
    "recipes_liked": 35,
    "activity_level": "active"
  },
  "recent_activity": [
    {
      "id": 100,
      "activity_type": "review",
      "content": {
        "review_id": 50,
        "recipe_id": 42,
        "rating": 5
      },
      "created_at": "2026-02-26T10:30:00Z"
    }
  ]
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "success": false,
  "message": "Profile retrieval failed: [error message]"
}
```

---

### 7. Share Recipe

Track a recipe share event and increment share count.

**Endpoint:** `POST /recipes/{recipe_id}/share`
**Authentication:** Required

**Path Parameters:**
- `recipe_id` (integer): Recipe ID

**Request Body:**
```json
{
  "platform": "facebook"
}
```

**Platform Options:**
- `facebook`
- `twitter`
- `whatsapp`
- `email`
- `generic` (default)

**Response:** 200 OK
```json
{
  "success": true,
  "share_count": 25,
  "message": "Recipe shared successfully"
}
```

**Error Response:** 500 Internal Server Error
```json
{
  "success": false,
  "message": "Share action failed: [error message]"
}
```

---

## Data Models

### Feed Item
```javascript
{
  "id": integer,
  "activity_type": string,
  "content": object,
  "created_at": ISO8601 timestamp
}
```

### Recipe Review
```javascript
{
  "id": integer,
  "recipe_id": integer,
  "user_id": integer,
  "user_name": string,
  "rating": integer (1-5),
  "text": string,
  "photos": array of URLs,
  "helpful_count": integer,
  "unhelpful_count": integer,
  "created_at": ISO8601 timestamp
}
```

### User Profile Stats
```javascript
{
  "cooking_sessions": integer,
  "saved_recipes": integer,
  "followers": integer,
  "following": integer,
  "reviews_posted": integer,
  "activity_level": "active" | "moderate" | "inactive"
}
```

---

## Activity Types

The Feed API supports these activity types:

- `new_recipe`: User created a new recipe
- `recipe_liked`: User liked a recipe
- `recipe_reviewed`: User posted a review
- `user_followed`: User followed another user/chef
- `like`: User liked a recipe
- `review`: User posted a review
- `follow`: User followed someone
- `share`: User shared a recipe

---

## Authentication

All protected endpoints require a valid JWT token in the `Authorization` header:

```http
Authorization: Bearer <jwt_token>
```

The token is obtained from the `/api/auth/login` endpoint.

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input or validation error
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `message` field explaining the issue.

---

## Rate Limiting

Feed endpoints are subject to rate limiting. Limits are enforced per user:

- Authenticated users: 100 requests per minute
- Public endpoints: 30 requests per minute per IP

---

## Pagination

Paginated endpoints use offset-based pagination:

**For feed endpoints:**
- Use `limit` and `offset` parameters
- `limit`: Max items per page
- `offset`: Number of items to skip

**For reviews:**
- Use `page` and `per_page` parameters
- `page`: 1-indexed page number
- `per_page`: Items per page

---

## Implementation Details

### Feed Generation

The user feed is generated from:

1. **Recent recipes from followed chefs**: New recipes posted by chefs the user follows
2. **Activity from followed users**: Reviews, likes, and actions from users the user follows
3. **AI recommendations**: Popular and trending recipes
4. **Activity sorting**: Chronological order (newest first)

### Review Validation

- Ratings must be between 1 and 5
- Review text is limited to 500 characters
- Photos are optional and stored as URLs
- Each user can post one review per recipe
- Reviews are immutable after posting

### Follow Relationships

- Users can follow both other users and chefs
- Following is unidirectional (A follows B doesn't mean B follows A)
- Unfollowing removes the follow relationship immediately
- Follow actions create feed entries for the follower

### Share Tracking

- Share count is incremented on each share event
- Share events are recorded in the feed
- Platform information is stored for analytics

---

## Example Usage

### Get user's feed

```bash
curl -X GET "http://localhost:8000/api/coocook/feed?limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Post a review

```bash
curl -X POST "http://localhost:8000/api/coocook/recipes/42/review" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "text": "Excellent recipe!",
    "photos": ["https://example.com/photo.jpg"]
  }'
```

### Get recipe reviews

```bash
curl -X GET "http://localhost:8000/api/coocook/recipes/42/reviews?page=1&per_page=10&sort=helpful" \
  -H "Content-Type: application/json"
```

### Like a recipe

```bash
curl -X POST "http://localhost:8000/api/coocook/recipes/42/like" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Follow a chef

```bash
curl -X POST "http://localhost:8000/api/coocook/chefs/5/follow" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get user profile

```bash
curl -X GET "http://localhost:8000/api/coocook/user/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Share a recipe

```bash
curl -X POST "http://localhost:8000/api/coocook/recipes/42/share" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "facebook"
  }'
```

---

## Database Schema

### Tables

- `feeds`: User activity feed entries
- `recipe_reviews`: Recipe reviews and ratings
- `recipe_likes`: User likes on recipes
- `user_follows`: User follow relationships
- `cooking_sessions`: User cooking session history
- `recipes`: Recipe data
- `users`: User accounts

### Indexes

- `idx_feed_user_id`: Fast user feed lookup
- `idx_feed_created_at`: Feed ordering
- `idx_review_recipe_id`: Recipe reviews lookup
- `idx_review_user_id`: User reviews lookup
- `idx_like_recipe_id`: Recipe likes count
- `idx_like_user_id`: User likes lookup
- `idx_follow_follower_id`: User's following list
- `idx_follow_following_id`: User's followers list

---

## Performance Considerations

- Feed queries are optimized with pagination and indexes
- Review queries support efficient sorting and filtering
- User follow relationships use indexed lookups
- All timestamp-based queries use database indexes
- Feed generation uses connection pooling for efficiency

---

## Version History

- **v1.0** (2026-02-26): Initial release
  - Feed generation
  - Review system
  - Like/unlike functionality
  - Follow/unfollow system
  - User profile statistics
  - Share tracking
