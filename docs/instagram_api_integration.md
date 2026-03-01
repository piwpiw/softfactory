# 🔌 Instagram API Real Integration Guide (v1.0)

> **Purpose**: The Instagram API integration enables users to:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Instagram API Real Integration Guide (v1.0) 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Overview

The Instagram API integration enables users to:
- Authenticate Instagram accounts via OAuth 2.0
- Post to Instagram Feed, Stories, and Reels
- Retrieve post analytics and account information
- Manage multiple Instagram accounts
- Auto-refresh expired access tokens

**Status:** Production-Ready
**Created:** 2026-02-26
**API Version:** Instagram Graph API v18.0

---

## Architecture

### Service File
```
backend/services/instagram_api.py (440+ lines)
```

### Main Components

1. **InstagramAPI Class** - Core API client
   - `__init__(access_token)` - Initialize with access token
   - `authenticate(code)` - OAuth token exchange
   - `post_feed()` - Post to Instagram feed
   - `post_story()` - Post to Instagram story
   - `post_reel()` - Post to Instagram reels
   - `get_account_info()` - Get account details
   - `get_insights()` - Get post analytics
   - `get_media()` - List recent posts
   - `refresh_access_token()` - Auto-refresh tokens

2. **Flask Routes** - REST API endpoints
   - `POST /api/sns/instagram/oauth/authorize` - Start OAuth flow
   - `GET /api/sns/instagram/callback` - OAuth callback handler
   - `POST /api/sns/instagram/posts` - Create feed post
   - `POST /api/sns/instagram/stories` - Create story
   - `POST /api/sns/instagram/reels` - Create reel
   - `GET /api/sns/instagram/<post_id>/insights` - Get post analytics
   - `GET /api/sns/instagram/account/info` - Get account info
   - `GET /api/sns/instagram/media` - List posts
   - `GET /api/sns/instagram/accounts` - List connected accounts
   - `DELETE /api/sns/instagram/accounts/<account_id>` - Disconnect account

3. **Database Integration**
   - Uses existing `SNSAccount` model
   - Uses `SNSPost` model for post tracking
   - Uses `SNSAnalytics` model for insights

---

## Setup Instructions

### Step 1: Create Instagram App

1. Go to https://developers.facebook.com/
2. Create new app → Select "Consumer" type
3. In App Dashboard:
   - Go to Settings → Basic
   - Note your **App ID** and **App Secret**
   - Go to Products → Add Product → Instagram Graph API
   - Configure App Type: "Business" or "Creator"

4. Generate Access Token:
   - Go to Instagram Graph API → Tools
   - Generate long-lived token (valid 60 days)
   - Token format: `AAAA...` (typically 255+ characters)

### Step 2: Environment Variables

Edit `.env` file:

```bash
# Instagram API Credentials
INSTAGRAM_APP_ID=your_app_id_here
INSTAGRAM_APP_SECRET=your_app_secret_here
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/sns/instagram/callback
```

**Where to find:**
- `INSTAGRAM_APP_ID` - https://developers.facebook.com/apps/ → App ID
- `INSTAGRAM_APP_SECRET` - Settings → Basic → App Secret
- `INSTAGRAM_REDIRECT_URI` - Your callback URL (must be whitelisted in app settings)

### Step 3: Whitelist Redirect URI

1. In Facebook App Dashboard:
   - Settings → Basic → Add Platform → Web
   - App Domains: Add `localhost` (or your domain)
   - Settings → Instagram Graph API
   - Valid OAuth Redirect URIs: Add exact callback URL

### Step 4: Test Connection

```bash
curl -X GET "http://localhost:8000/api/sns/instagram/oauth/authorize" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## API Endpoints

### 1. Authorize Instagram Account

**Request:**
```
GET /api/sns/instagram/oauth/authorize
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
{
  "auth_url": "https://api.instagram.com/oauth/authorize?client_id=...&redirect_uri=...&scope=..."
}
```

**Usage:**
1. Redirect user to `auth_url`
2. User logs in to Instagram
3. Redirected to callback URL with `code` parameter
4. System exchanges code for access token
5. Account saved to database

---

### 2. Create Instagram Feed Post

**Request:**
```
POST /api/sns/instagram/posts
Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "account_id": 1,
  "image_url": "https://example.com/image.jpg",
  "caption": "Check out this amazing product! #marketing #instagood",
  "hashtags": ["marketing", "instagood", "socialmedia"]
}
```

**Response (201):**
```json
{
  "message": "Post created successfully",
  "post_id": "17892456789123456",
  "db_id": 42
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields
- `401 Unauthorized` - Account not authenticated
- `404 Not Found` - Account not found
- `429 Too Many Requests` - Rate limit exceeded

**Constraints:**
- `image_url`: Required, valid URL (10-2000 chars)
- `caption`: Optional, max 2200 characters
- `hashtags`: Optional, array of strings
- Supported formats: JPEG, PNG
- Max image size: 8 MB (Instagram limit)

---

### 3. Create Instagram Story

**Request:**
```
POST /api/sns/instagram/stories
Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "account_id": 1,
  "image_url": "https://example.com/story.jpg",
  "text": "Check back soon!"
}
```

**Response (201):**
```json
{
  "message": "Story created successfully",
  "story_id": "17892456789123789"
}
```

**Constraints:**
- Stories expire after 24 hours
- Image format: JPEG, PNG
- Recommended dimensions: 1080x1920 px
- Max text: 100 characters

---

### 4. Create Instagram Reel

**Request:**
```
POST /api/sns/instagram/reels
Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "account_id": 1,
  "video_url": "https://example.com/video.mp4",
  "caption": "Amazing tutorial! #reels #tutorial",
  "thumbnail_url": "https://example.com/thumbnail.jpg"
}
```

**Response (201):**
```json
{
  "message": "Reel created successfully",
  "reel_id": "17892456789123999",
  "db_id": 43
}
```

**Constraints:**
- Video format: MP4, MOV
- Duration: 15 seconds to 10 minutes
- Max video size: 4 GB
- Audio: Optional
- Aspect ratio: 9:16 (vertical)

---

### 5. Get Post Insights

**Request:**
```
GET /api/sns/instagram/42/insights
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
{
  "likes": 245,
  "comments": 18,
  "shares": 5,
  "reach": 3890,
  "impressions": 5234,
  "saved": 12,
  "engagement_rate": 4.87
}
```

**Notes:**
- Insights updated in real-time
- Requires post to be published >24 hours for full data
- Business/Creator accounts only
- Metrics saved to SNSAnalytics table

---

### 6. Get Account Information

**Request:**
```
GET /api/sns/instagram/account/info?account_id=1
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
{
  "id": "123456789",
  "username": "john_doe",
  "name": "John Doe",
  "bio": "Marketing expert 🚀",
  "followers_count": 15420,
  "following_count": 850,
  "profile_picture_url": "https://...",
  "website": "https://example.com",
  "account_type": "business"
}
```

---

### 7. Get Recent Posts

**Request:**
```
GET /api/sns/instagram/media?account_id=1&limit=25&after=cursor_token
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
{
  "posts": [
    {
      "id": "17892456789123456",
      "caption": "Great day at the office!",
      "media_type": "IMAGE",
      "media_url": "https://...",
      "timestamp": "2026-02-26T10:30:00Z",
      "likes": 245,
      "comments": 18
    }
  ],
  "next_cursor": "NEXT_PAGE_TOKEN"
}
```

**Parameters:**
- `account_id` (required): Instagram account ID
- `limit` (optional): Max 100, default 25
- `after` (optional): Pagination cursor

---

### 8. List Connected Accounts

**Request:**
```
GET /api/sns/instagram/accounts
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "platform": "instagram",
    "account_name": "john_doe",
    "is_active": true,
    "platform_user_id": "123456789",
    "profile_picture_url": "https://...",
    "account_type": "business",
    "followers_count": 15420,
    "following_count": 850,
    "token_expires_at": "2026-04-26T00:00:00Z",
    "created_at": "2026-02-26T10:00:00Z"
  }
]
```

---

### 9. Disconnect Instagram Account

**Request:**
```
DELETE /api/sns/instagram/accounts/1
Headers:
  Authorization: Bearer {jwt_token}
```

**Response (200):**
```json
{
  "message": "Account disconnected successfully"
}
```

---

## Error Handling

### InstagramAPIError Exception

The service throws `InstagramAPIError` for:

```python
# Rate limit (429)
InstagramAPIError("Rate limit exceeded. Please try again later.")

# Token expired (401)
InstagramAPIError("Access token expired. Please re-authenticate.")

# Permission denied (403)
InstagramAPIError("Permission denied. Check account permissions.")

# Timeout
InstagramAPIError("Request timeout. Please try again.")

# Connection error
InstagramAPIError("Connection error. Please check your internet connection.")
```

### Auto-Refresh Token

When a token expires:
1. System detects 401 error
2. Attempts to refresh token using `refresh_access_token()`
3. Retries operation with new token
4. Updates database with new token

---

## Database Schema

### SNSAccount Extension

```sql
-- Already exists, no migration needed
CREATE TABLE sns_accounts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    platform VARCHAR(50) NOT NULL,  -- 'instagram'
    account_name VARCHAR(120) NOT NULL,  -- username
    is_active BOOLEAN DEFAULT true,

    -- OAuth fields
    access_token TEXT,  -- Encrypted in production
    refresh_token TEXT,  -- Instagram long-lived tokens
    token_expires_at DATETIME,
    platform_user_id VARCHAR(255),  -- Instagram user ID
    profile_picture_url VARCHAR(500),
    account_type VARCHAR(50),  -- 'personal' or 'business'

    -- Analytics
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    permissions_json JSON,

    created_at DATETIME DEFAULT datetime('now')
);
```

### SNSPost Extension

```sql
-- Already exists
CREATE TABLE sns_posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    platform VARCHAR(50),  -- 'instagram'
    content TEXT,  -- caption
    media_url VARCHAR(500),  -- image/video URL
    status VARCHAR(20),  -- 'published', 'draft', 'scheduled'
    platform_post_id VARCHAR(255),  -- Instagram post ID
    published_at DATETIME,
    created_at DATETIME DEFAULT datetime('now'),

    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(account_id) REFERENCES sns_accounts(id)
);
```

### SNSAnalytics Extension

```sql
-- Already exists
CREATE TABLE sns_analytics (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT datetime('now'),

    FOREIGN KEY(post_id) REFERENCES sns_posts(id)
);
```

---

## Rate Limiting

Instagram API Rate Limits:
- **Standard calls:** 200 calls per hour per user
- **Video uploads:** 50 uploads per hour
- **Media insights:** 200 requests per hour

Our system implements:
- Exponential backoff on rate limits (429 errors)
- Request queuing for high-volume operations
- Per-user request tracking

---

## Security Considerations

### 1. Token Storage

```python
# Tokens should be encrypted in production
from cryptography.fernet import Fernet

# Enable field-level encryption in config
ENCRYPTION_ENABLED = True
ENCRYPTED_FIELDS = ['access_token', 'refresh_token']
```

### 2. OAuth Security

- Always use HTTPS for redirect URIs in production
- Validate `state` parameter to prevent CSRF
- Store tokens securely (never in logs)
- Implement token rotation

### 3. API Key Management

```bash
# Environment variables must never be committed
# Use secure secret management:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Bitwarden
```

### 4. Rate Limiting

```python
# Implement per-user rate limiting
@limiter.limit("100 per hour")
def create_instagram_post():
    pass
```

---

## Testing

### Unit Tests

```python
# tests/test_instagram_api.py

def test_authenticate():
    instagram = InstagramAPI('')
    token, info = instagram.authenticate('valid_code')
    assert token is not None
    assert info['username'] == 'john_doe'

def test_post_feed():
    instagram = InstagramAPI('valid_token')
    post_id = instagram.post_feed(
        'https://example.com/image.jpg',
        'Test caption',
        ['test', 'instagram']
    )
    assert post_id is not None

def test_rate_limit_error():
    instagram = InstagramAPI('valid_token')
    with pytest.raises(InstagramAPIError):
        instagram.post_feed(...)  # Trigger 429
```

### Integration Tests

```bash
# curl test
curl -X POST http://localhost:8000/api/sns/instagram/posts \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/test.jpg",
    "caption": "Test post"
  }'
```

---

## Troubleshooting

### Issue: "App not configured"
- Solution: Check INSTAGRAM_APP_ID in .env

### Issue: "Invalid redirect URI"
- Solution: Whitelist redirect URI in Facebook App Settings

### Issue: "Token expired"
- Solution: System auto-refreshes, but if manual refresh needed:
  ```python
  instagram = InstagramAPI(old_token)
  new_token = instagram.refresh_access_token(old_token)
  ```

### Issue: "Media upload failed"
- Solution: Check image dimensions, format, and file size limits

### Issue: "Rate limit exceeded"
- Solution: Wait 1 hour, or implement request queuing

---

## Examples

### Complete Flow: Post to Instagram

```python
from backend.services.instagram_api import InstagramAPI

# 1. Get user's Instagram account
account = SNSAccount.query.filter_by(
    user_id=user_id,
    platform='instagram'
).first()

# 2. Initialize API
instagram = InstagramAPI(account.access_token)

# 3. Post to feed
try:
    post_id = instagram.post_feed(
        image_url='https://example.com/product.jpg',
        caption='Amazing product #shopping #love',
        hashtags=['shopping', 'love', 'instagood']
    )
    print(f"Posted successfully! Post ID: {post_id}")
except InstagramAPIError as e:
    print(f"Failed to post: {e}")
    # Handle token refresh
    account.access_token = instagram.refresh_access_token(
        account.access_token
    )
    db.session.commit()
```

### Get Analytics

```python
# Fetch latest insights
insights = instagram.get_insights(post_id)

print(f"Likes: {insights['likes']}")
print(f"Reach: {insights['reach']}")
print(f"Engagement: {insights['engagement_rate']}%")

# Save to database
analytics = SNSAnalytics(
    post_id=db_post_id,
    likes=insights['likes'],
    comments=insights['comments'],
    reach=insights['reach']
)
db.session.add(analytics)
db.session.commit()
```

---

## Future Enhancements

- [ ] Carousel posts (multiple images)
- [ ] IGTV video hosting
- [ ] Story stickers and tags
- [ ] Direct messaging API
- [ ] User hashtag search
- [ ] Location-based features
- [ ] Shopping integration
- [ ] Analytics scheduling (auto-refresh)

---

## References

- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api)
- [Instagram Graph API Rate Limiting](https://developers.facebook.com/docs/graph-api/overview/rate-limiting)
- [Instagram Platform Policies](https://www.instagram.com/about/policies/)
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)

---

**Last Updated:** 2026-02-26
**Maintained By:** SoftFactory Development Team