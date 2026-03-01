# Twitter API v2 Integration — Complete Implementation Guide

**Status:** Production Ready | **Version:** 2.0 | **Date:** 2026-02-26

## Overview

Complete Twitter API v2 integration with OAuth 2.0, rate limiting (450 requests/15min), real-time analytics, and multi-account support.

### Features

- ✅ OAuth 2.0 with PKCE flow
- ✅ Tweet posting & threading (1-100 tweets per thread)
- ✅ Like, retweet, bookmark management
- ✅ Account insights & analytics (followers, engagement, impressions)
- ✅ Trend discovery (worldwide + by location)
- ✅ User search & discovery
- ✅ Rate limiting with sliding window
- ✅ Token refresh & revocation
- ✅ Multi-account management
- ✅ Database integration (SNSPost, SNSAnalytics models)

---

## 10 API Endpoints

### 1. OAuth Authorization

**Endpoint:** `GET /api/sns/twitter/oauth/authorize`

Initiates OAuth 2.0 flow with PKCE.

**Request:**
```bash
curl -X GET http://localhost:8000/api/sns/twitter/oauth/authorize \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

**Response (200):**
```json
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?...",
  "state": "random_state_token"
}
```

**Flow:**
1. User clicks authorization_url
2. Twitter redirects to `/api/sns/twitter/oauth/callback?code=...&state=...`
3. Backend exchanges code for tokens
4. Twitter account linked to user

---

### 2. Post Tweet

**Endpoint:** `POST /api/sns/twitter/tweets`

Post a single tweet (280 chars max).

**Request:**
```json
{
  "account_id": 123,
  "text": "Hello Twitter! 🚀",
  "media_ids": ["123456"],
  "reply_to_tweet_id": "789",
  "quote_tweet_id": "456",
  "schedule_at": "2025-02-27T10:00:00Z"
}
```

**Response (201):**
```json
{
  "success": true,
  "post_id": 456,
  "tweet_id": "1234567890",
  "url": "https://twitter.com/i/web/status/1234567890",
  "status": "published",
  "created_at": "2026-02-26T15:30:00Z"
}
```

**Features:**
- Immediate publishing or future scheduling
- Media attachments (images/videos)
- Reply to existing tweets
- Quote tweets
- Database tracking (SNSPost model)

---

### 3. Post Thread

**Endpoint:** `POST /api/sns/twitter/threads`

Post 1-100 tweets as a connected thread.

**Request:**
```json
{
  "account_id": 123,
  "tweets": [
    "First tweet of the thread...",
    "Second tweet continues the conversation...",
    "Third tweet with final thoughts..."
  ]
}
```

**Response (201):**
```json
{
  "success": true,
  "thread_count": 3,
  "tweets": [
    {
      "tweet_id": "1234567890",
      "text": "First tweet of the thread...",
      "url": "https://twitter.com/i/web/status/1234567890"
    },
    {
      "tweet_id": "1234567891",
      "text": "Second tweet continues the conversation...",
      "url": "https://twitter.com/i/web/status/1234567891"
    },
    {
      "tweet_id": "1234567892",
      "text": "Third tweet with final thoughts...",
      "url": "https://twitter.com/i/web/status/1234567892"
    }
  ],
  "created_at": "2026-02-26T15:30:00Z"
}
```

**Validation:**
- Max 100 tweets per thread
- Each tweet max 280 characters
- Replies automatically chained

---

### 4. Like Tweet

**Endpoint:** `POST /api/sns/twitter/{tweet_id}/like`

Like a tweet.

**Request:**
```json
{
  "account_id": 123
}
```

**Response (200):**
```json
{
  "success": true,
  "tweet_id": "1234567890",
  "timestamp": "2026-02-26T15:30:00Z"
}
```

---

### 5. Retweet

**Endpoint:** `POST /api/sns/twitter/{tweet_id}/retweet`

Retweet a tweet.

**Request:**
```json
{
  "account_id": 123
}
```

**Response (200):**
```json
{
  "success": true,
  "tweet_id": "1234567890",
  "timestamp": "2026-02-26T15:30:00Z"
}
```

---

### 6. Bookmark Tweet

**Endpoint:** `POST /api/sns/twitter/{tweet_id}/bookmark`

Bookmark a tweet for later.

**Request:**
```json
{
  "account_id": 123
}
```

**Response (200):**
```json
{
  "success": true,
  "tweet_id": "1234567890",
  "timestamp": "2026-02-26T15:30:00Z"
}
```

---

### 7. Get Tweet Insights

**Endpoint:** `GET /api/sns/twitter/{tweet_id}/insights`

Get real-time metrics for a specific tweet.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/sns/twitter/1234567890/insights?account_id=123" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

**Response (200):**
```json
{
  "tweet_id": "1234567890",
  "text": "Hello Twitter! 🚀",
  "created_at": "2026-02-26T15:00:00Z",
  "likes": 1250,
  "retweets": 342,
  "replies": 87,
  "quotes": 23,
  "impressions": 45000,
  "bookmark_count": 156
}
```

---

### 8. Get Account Insights

**Endpoint:** `GET /api/sns/twitter/account/insights`

Get account-level analytics (followers, engagement, impressions over time).

**Request:**
```bash
curl -X GET "http://localhost:8000/api/sns/twitter/account/insights?account_id=123&days=7" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

**Response (200):**
```json
{
  "period_days": 7,
  "start_date": "2026-02-19T00:00:00Z",
  "end_date": "2026-02-26T00:00:00Z",
  "followers": 15432,
  "following": 892,
  "tweets_count": 23,
  "total_likes": 3456,
  "total_retweets": 892,
  "total_replies": 234,
  "total_impressions": 125000,
  "total_engagement": 4582,
  "avg_engagement": 199.2,
  "avg_impressions": 5434.8,
  "engagement_rate": 1.98,
  "top_tweet": {
    "id": "1234567890",
    "text": "Best performing tweet...",
    "engagement": 2156
  }
}
```

**Metrics:**
- Followers growth
- Engagement rate = (likes + retweets + replies) / followers
- Average engagement per tweet
- Impressions trend
- Top performing tweet

---

### 9. Get Trending Topics

**Endpoint:** `GET /api/sns/twitter/trends`

Get trending topics worldwide (or by location).

**Request:**
```bash
curl -X GET "http://localhost:8000/api/sns/twitter/trends?woeid=1" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

**Response (200):**
```json
{
  "trends": [
    {
      "name": "#AI",
      "url": "https://twitter.com/search?q=%23AI",
      "tweet_volume": 345000,
      "query": "#AI"
    },
    {
      "name": "#Python",
      "url": "https://twitter.com/search?q=%23Python",
      "tweet_volume": 234000,
      "query": "#Python"
    },
    {
      "name": "#WebDevelopment",
      "url": "https://twitter.com/search?q=%23WebDevelopment",
      "tweet_volume": 156000,
      "query": "#WebDevelopment"
    }
  ]
}
```

**Location Codes (WOEID):**
- `1` = Worldwide
- `23424977` = United States
- `23424975` = Brazil
- `23424856` = India
- `23424819` = Japan

---

### 10. Get Account Info

**Endpoint:** `GET /api/sns/twitter/account/info`

Get authenticated user's profile information.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/sns/twitter/account/info?account_id=123" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

**Response (200):**
```json
{
  "user_id": "1234567890",
  "username": "john_doe",
  "name": "John Doe",
  "description": "Product manager & tech enthusiast",
  "location": "San Francisco, CA",
  "followers": 15432,
  "following": 892,
  "tweets": 3456,
  "verified": true,
  "created_at": "2015-06-15T12:30:00Z",
  "profile_url": "https://twitter.com/john_doe"
}
```

---

## Additional Endpoints

### Get Twitter Accounts (User's Linked Accounts)

**Endpoint:** `GET /api/sns/twitter/accounts`

**Response:**
```json
[
  {
    "id": 123,
    "username": "john_doe",
    "followers": 15432,
    "is_active": true,
    "linked_at": "2026-02-20T10:00:00Z",
    "status": "active"
  },
  {
    "id": 124,
    "username": "jane_smith",
    "followers": 8900,
    "is_active": true,
    "linked_at": "2026-02-21T14:30:00Z",
    "status": "active"
  }
]
```

### Unlink Twitter Account

**Endpoint:** `DELETE /api/sns/twitter/accounts/{account_id}`

Unlinks account and revokes token.

### Rate Limit Status

**Endpoint:** `GET /api/sns/twitter/rate-limit`

**Response:**
```json
{
  "remaining_requests": 342,
  "max_requests": 450,
  "window_minutes": 15,
  "reset_at": "2026-02-26T16:00:00Z",
  "requests_until_reset": 1234
}
```

### Health Check

**Endpoint:** `GET /api/sns/twitter/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-26T15:30:00Z"
}
```

---

## Authentication

All endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/sns/twitter/...
```

Get JWT token via login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

---

## Error Responses

### Rate Limit Exceeded (429)
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

### Invalid Account (404)
```json
{
  "error": "Twitter account not found or not owned by user"
}
```

### API Error (400)
```json
{
  "error": "Failed to post tweet"
}
```

### Server Error (500)
```json
{
  "error": "Internal server error"
}
```

---

## Rate Limiting

**Limits:** 450 requests per 15 minutes (Twitter API v2 standard)

**Sliding Window Implementation:**
- Tracks timestamps of all requests
- Removes requests outside 15-minute window
- Returns 429 when limit exceeded
- Provides remaining count + reset timestamp

**Usage:**
```python
from backend.services.twitter_api import TwitterAPI

client = TwitterAPI(access_token="your_token")

# Check rate limit
remaining, reset_ts = client.rate_limiter.get_remaining('endpoint')
print(f"Remaining: {remaining}, Reset at: {reset_ts}")

# Make request (auto-checks limit internally)
try:
    result = client.post_tweet("Hello Twitter!")
except RateLimitException as e:
    print(f"Rate limited: {e}")
```

---

## OAuth 2.0 Flow with PKCE

**Step 1: Initiate Authorization**
```bash
GET /api/sns/twitter/oauth/authorize
```

**Step 2: User Authorizes (Redirects to Twitter)**
```
https://twitter.com/i/oauth2/authorize?
  client_id=...&
  redirect_uri=http://localhost:8000/api/sns/twitter/oauth/callback&
  response_type=code&
  scope=tweet.read%20tweet.write%20users.read%20...&
  state=random_state&
  code_challenge=...&
  code_challenge_method=S256
```

**Step 3: Handle Callback**
```bash
GET /api/sns/twitter/oauth/callback?code=...&state=...
```

**Step 4: Backend Exchanges Code for Token**
- POST to Twitter token endpoint
- Verifies PKCE code_verifier
- Returns access_token + refresh_token
- Stores in database

---

## Database Integration

### SNSAccount Model
```python
class SNSAccount:
    id: int
    user_id: int
    platform: str = 'twitter'
    account_name: str  # username
    external_account_id: str  # Twitter user ID
    access_token: str
    refresh_token: Optional[str]
    token_expires_at: datetime
    is_active: bool
    created_at: datetime
```

### SNSPost Model
```python
class SNSPost:
    id: int
    user_id: int
    account_id: int
    platform: str = 'twitter'
    content: str  # Tweet text
    external_post_id: str  # Tweet ID
    status: str  # 'draft', 'scheduled', 'published', 'failed'
    published_at: Optional[datetime]
    likes_count: int
    comments_count: int
    views_count: int
    reach: int
```

### SNSAnalytics Model
```python
class SNSAnalytics:
    id: int
    user_id: int
    account_id: int
    date: date
    followers: int
    total_engagement: int
    total_reach: int
    total_impressions: int
```

---

## Python Client Usage

```python
from backend.services.twitter_api import TwitterAPI

# Initialize client
client = TwitterAPI(
    access_token="your_access_token",
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="http://localhost:8000/api/sns/twitter/oauth/callback"
)

# Post tweet
result = client.post_tweet("Hello Twitter!")
print(f"Tweet ID: {result['tweet_id']}")

# Post thread
tweets = [
    "First tweet...",
    "Second tweet...",
    "Third tweet..."
]
result = client.post_thread(tweets)
print(f"Posted {result['thread_count']} tweets")

# Get insights
insights = client.get_insights(days=7)
print(f"Followers: {insights['followers']}")
print(f"Engagement: {insights['total_engagement']}")

# Get trending topics
trends = client.get_trending_topics(location_woeid=1)
for trend in trends[:5]:
    print(f"{trend['name']}: {trend['tweet_volume']} tweets")

# Like, retweet, bookmark
client.like_tweet("1234567890")
client.retweet("1234567890")
client.bookmark_tweet("1234567890")

# Get account info
user_info = client.get_account_info()
print(f"User: @{user_info['username']}")
print(f"Followers: {user_info['followers']}")
```

---

## Environment Variables

Add to `.env`:

```
# Twitter API v2
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_REDIRECT_URI=http://localhost:8000/api/sns/twitter/oauth/callback
TWITTER_ACCESS_TOKEN=your_bearer_token  # For direct API calls
```

---

## Testing

### Unit Tests
```bash
pytest tests/unit/test_twitter_api.py -v
```

### Integration Tests
```bash
pytest tests/integration/test_twitter_endpoints.py -v
```

### Manual Testing with cURL

```bash
# Get authorization URL
curl -X GET http://localhost:8000/api/sns/twitter/oauth/authorize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Post tweet
curl -X POST http://localhost:8000/api/sns/twitter/tweets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 123,
    "text": "Hello Twitter API!"
  }'

# Get account insights
curl -X GET "http://localhost:8000/api/sns/twitter/account/insights?account_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get trends
curl -X GET "http://localhost:8000/api/sns/twitter/trends" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Production Deployment

### Requirements
- Python 3.9+
- Flask 2.0+
- requests 2.28+
- SQLAlchemy 1.4+

### Configuration
1. Set environment variables in production
2. Use HTTPS for OAuth callbacks
3. Enable database connection pooling
4. Set up monitoring for rate limits
5. Configure error logging/alerting

### Performance
- Rate limiter uses in-memory thread-safe sliding window
- User info cached for 1 hour
- Database queries optimized with indexes
- Concurrent request handling via Flask threading

---

## Troubleshooting

### OAuth State Expired
**Error:** "Invalid or expired state"
**Solution:** State tokens expire after 10 minutes. Initiate new authorization.

### Rate Limit Exceeded
**Error:** "Rate limit exceeded"
**Solution:** Wait for reset window (15 minutes) or upgrade API tier.

### Invalid Bearer Token
**Error:** "Unauthorized"
**Solution:** Check token is still valid. Use refresh_token endpoint if expired.

### Account Not Found
**Error:** "Twitter account not found"
**Solution:** Complete OAuth flow first via `/api/sns/twitter/oauth/authorize`.

---

## Changelog

### v2.0 (2026-02-26)
- ✅ Complete OAuth 2.0 with PKCE
- ✅ Rate limiting (450/15min)
- ✅ Tweet posting & threading
- ✅ Real-time insights & analytics
- ✅ Trend discovery
- ✅ Multi-account management
- ✅ 10 API endpoints
- ✅ Database integration

### v1.0 (2025-12-01)
- Basic Twitter client
- Simulation mode
