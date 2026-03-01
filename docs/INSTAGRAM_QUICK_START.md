# 🔌 Instagram API — Quick Start Guide (5 Minutes)

> **Purpose**: Complete Instagram Graph API integration with:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Instagram API — Quick Start Guide (5 Minutes) 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## What's New?

Complete Instagram Graph API integration with:
- OAuth 2.0 authentication
- Post to Feed, Stories, Reels
- Real-time analytics
- Automatic token refresh
- Multi-account support

---

## 1-Minute Setup

### Step 1: Update .env

```bash
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/sns/instagram/callback
```

### Step 2: Restart Flask

```bash
python start_platform.py
```

### Step 3: Done!

Instagram integration is live at `/api/sns/instagram`

---

## First Instagram Post (Code)

```python
from backend.services.instagram_api import InstagramAPI

# Initialize API
api = InstagramAPI('your_access_token')

# Post to feed
post_id = api.post_feed(
    image_url='https://example.com/photo.jpg',
    caption='My first Instagram post!',
    hashtags=['awesome', 'instagram']
)

print(f"Posted! ID: {post_id}")
```

---

## First Instagram Post (API)

```bash
# 1. Get auth URL
curl -X GET http://localhost:8000/api/sns/instagram/oauth/authorize \
  -H "Authorization: Bearer YOUR_JWT"

# 2. User logs in and grants permissions (done in browser)

# 3. Post to feed
curl -X POST http://localhost:8000/api/sns/instagram/posts \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/photo.jpg",
    "caption": "My first post!"
  }'
```

---

## Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sns/instagram/posts` | Create feed post |
| POST | `/api/sns/instagram/stories` | Create story |
| POST | `/api/sns/instagram/reels` | Create reel |
| GET | `/api/sns/instagram/{id}/insights` | Get post analytics |
| GET | `/api/sns/instagram/account/info` | Get account details |
| GET | `/api/sns/instagram/media` | List recent posts |
| GET | `/api/sns/instagram/accounts` | List your accounts |
| DELETE | `/api/sns/instagram/accounts/{id}` | Disconnect account |

---

## Key Methods

### Post Feed
```python
api.post_feed(
    image_url='https://...',
    caption='Hello Instagram!',  # Optional
    hashtags=['test', 'instagram']  # Optional
)
```

### Post Story
```python
api.post_story(
    image_url='https://...',
    text='Back soon!'  # Optional
)
```

### Post Reel
```python
api.post_reel(
    video_url='https://...',
    caption='Check this out!',  # Optional
    thumbnail_url='https://...'  # Optional
)
```

### Get Analytics
```python
insights = api.get_insights('post_id')
# Returns: {likes, comments, shares, reach, impressions, saved, engagement_rate}
```

### Get Account Info
```python
info = api.get_account_info()
# Returns: {id, username, followers_count, following_count, bio, account_type}
```

---

## Error Handling

```python
from backend.services.instagram_api import InstagramAPIError

try:
    api.post_feed(image_url, caption)
except InstagramAPIError as e:
    print(f"Error: {e}")
    # Handle: "Rate limit exceeded", "Token expired", etc.
```

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "App not configured" | Set INSTAGRAM_APP_ID in .env |
| "Invalid redirect URI" | Whitelist callback URL in Facebook app settings |
| "Token expired" | System auto-refreshes; if manual: `api.refresh_access_token()` |
| "Rate limit exceeded" | Wait 1 hour; Instagram limits: 200 calls/hour |
| "Invalid image format" | Use JPEG or PNG; min 320x320 pixels |

---

## Environment Variables

```
INSTAGRAM_APP_ID              Required  Your app ID from Facebook Developers
INSTAGRAM_APP_SECRET          Required  Your app secret
INSTAGRAM_REDIRECT_URI        Required  http://localhost:8000/api/sns/instagram/callback (or production URL)
```

---

## Database Fields (SNSAccount)

The system automatically stores:
- `access_token` - OAuth token (encrypted)
- `platform_user_id` - Instagram user ID
- `account_name` - Instagram username
- `followers_count` - Follower count
- `following_count` - Following count
- `account_type` - 'personal' or 'business'
- `token_expires_at` - Token expiry date

---

## Features

✅ **OAuth 2.0** - Secure user authentication
✅ **Feed Posts** - Images with captions & hashtags
✅ **Stories** - 24-hour ephemeral content
✅ **Reels** - Short-form video content
✅ **Analytics** - Likes, comments, reach, impressions
✅ **Token Refresh** - Auto-refresh expired tokens
✅ **Multi-Account** - Connect multiple Instagram accounts
✅ **Error Handling** - Comprehensive error messages
✅ **Rate Limiting** - Exponential backoff on limits

---

## File Locations

```
backend/services/instagram_api.py          Main service (440+ lines)
docs/instagram_api_integration.md          Full documentation
docs/instagram_api_examples.md             Code examples & test cases
docs/INSTAGRAM_QUICK_START.md              This file
```

---

## What's Included?

**Core Class:**
- `InstagramAPI` — Main API wrapper

**Routes (10):**
- OAuth authorize
- OAuth callback
- Create posts
- Create stories
- Create reels
- Get insights
- Get account info
- Get media
- List accounts
- Disconnect

**Error Handling:**
- Rate limiting (429)
- Token expiry (401)
- Permission denied (403)
- Connection errors
- Timeout handling

---

## Next Steps

1. **Configure App** - Set up Instagram app in Facebook Developers
2. **Set Credentials** - Add INSTAGRAM_APP_ID, SECRET to .env
3. **Authenticate** - User grants permissions via OAuth
4. **Post Content** - Use POST endpoints to publish
5. **Track Analytics** - Use GET /insights to monitor performance

---

## Real Example: Social Media Manager

```python
class SocialMediaManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.accounts = SNSAccount.query.filter_by(
            user_id=user_id,
            platform='instagram',
            is_active=True
        ).all()

    def post_to_all(self, image_url, caption, hashtags):
        """Post same content to all connected Instagram accounts"""
        results = {}

        for account in self.accounts:
            try:
                api = InstagramAPI(account.access_token)
                post_id = api.post_feed(image_url, caption, hashtags)
                results[account.account_name] = {
                    'status': 'success',
                    'post_id': post_id
                }
            except InstagramAPIError as e:
                results[account.account_name] = {
                    'status': 'failed',
                    'error': str(e)
                }

        return results

    def get_analytics(self):
        """Get analytics for all posts"""
        analytics = {}

        for account in self.accounts:
            api = InstagramAPI(account.access_token)
            posts, _ = api.get_media(limit=10)

            total_likes = sum(p['likes'] for p in posts)
            total_comments = sum(p['comments'] for p in posts)

            analytics[account.account_name] = {
                'likes': total_likes,
                'comments': total_comments,
                'posts': len(posts)
            }

        return analytics

# Usage
manager = SocialMediaManager(user_id=1)
results = manager.post_to_all(
    'https://example.com/image.jpg',
    'New product launch! 🚀',
    ['product', 'launch', 'sale']
)
print(results)
```

---

## Support

- **Full Docs:** See `instagram_api_integration.md`
- **Examples:** See `instagram_api_examples.md`
- **Code:** See `backend/services/instagram_api.py`
- **Issues:** Check error messages in response JSON

---

**Last Updated:** 2026-02-26 | **Status:** Production Ready