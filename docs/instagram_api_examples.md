# 🔌 Instagram API — Practical Examples & Test Cases

> **Purpose**: **Step 1: Get Authorization URL**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Instagram API — Practical Examples & Test Cases 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Quick Start Examples

### 1. OAuth Flow (Browser-Based)

**Step 1: Get Authorization URL**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/oauth/authorize" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "auth_url": "https://api.instagram.com/oauth/authorize?client_id=123456789&redirect_uri=http://localhost:8000/api/sns/instagram/callback&scope=instagram_basic,instagram_graph_user_profile,instagram_graph_user_media&response_type=code"
}
```

**Step 2: User Authorization**
- Open `auth_url` in browser
- User logs in with Instagram credentials
- Grants permissions
- Redirected to callback with `code` parameter

**Step 3: System Handles Exchange**
- System receives `code` in callback
- Exchanges for `access_token`
- Saves to database (SNSAccount)
- Returns success response

---

### 2. Post to Instagram Feed

**Test Case: Simple Post**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/posts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/product.jpg",
    "caption": "Check out this amazing product! 🚀",
    "hashtags": ["marketing", "instagood", "socialmedia"]
  }'
```

**Response (201):**
```json
{
  "message": "Post created successfully",
  "post_id": "17892456789123456",
  "db_id": 42
}
```

**Test Case: Post Without Hashtags**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/posts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/photo.jpg",
    "caption": "Beautiful sunset at the beach"
  }'
```

**Test Case: Error Handling - Missing Required Field**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/posts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "caption": "No image provided"
  }'
```

**Response (400):**
```json
{
  "error": "account_id and image_url are required"
}
```

---

### 3. Post to Instagram Story

**Test Case: Story with Text**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/stories" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/story.jpg",
    "text": "Back in 5 minutes!"
  }'
```

**Response (201):**
```json
{
  "message": "Story created successfully",
  "story_id": "17892456789123789"
}
```

**Test Case: Story Without Text**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/stories" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "image_url": "https://example.com/story.jpg"
  }'
```

---

### 4. Post to Instagram Reels

**Test Case: Reel with Video**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/reels" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "video_url": "https://example.com/tutorial.mp4",
    "caption": "Quick tutorial! Check it out 👇 #tutorial #reels",
    "thumbnail_url": "https://example.com/thumbnail.jpg"
  }'
```

**Response (201):**
```json
{
  "message": "Reel created successfully",
  "reel_id": "17892456789123999",
  "db_id": 43
}
```

**Test Case: Reel Without Thumbnail**
```bash
curl -X POST "http://localhost:8000/api/sns/instagram/reels" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "video_url": "https://example.com/video.mp4",
    "caption": "Amazing content! #reels"
  }'
```

---

### 5. Get Post Insights

**Test Case: Fetch Analytics for Published Post**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/42/insights" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json"
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

**Test Case: Insights for Non-Existent Post**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/99999/insights" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (404):**
```json
{
  "error": "Post not found"
}
```

---

### 6. Get Account Information

**Test Case: Fetch Account Info**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/account/info?account_id=1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (200):**
```json
{
  "id": "123456789",
  "username": "john_doe",
  "name": "John Doe",
  "bio": "Marketing expert 🚀\nEntrepreneur | Content Creator",
  "followers_count": 15420,
  "following_count": 850,
  "profile_picture_url": "https://instagram.fxxx-1.fna.fbcdn.net/v/...",
  "website": "https://johndoe.com",
  "account_type": "business"
}
```

---

### 7. Get Recent Media

**Test Case: Fetch 25 Recent Posts**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/media?account_id=1&limit=25" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200):**
```json
{
  "posts": [
    {
      "id": "17892456789123456",
      "caption": "Great day at the office!",
      "media_type": "IMAGE",
      "media_url": "https://instagram.fxxx-1.fna.fbcdn.net/v/...",
      "timestamp": "2026-02-26T10:30:00Z",
      "likes": 245,
      "comments": 18
    },
    {
      "id": "17892456789123457",
      "caption": "Tutorial time!",
      "media_type": "REELS",
      "media_url": "https://instagram.fxxx-1.fna.fbcdn.net/v/...",
      "timestamp": "2026-02-26T09:15:00Z",
      "likes": 512,
      "comments": 45
    }
  ],
  "next_cursor": "QASFZ5U5E6CZ2s..."
}
```

**Test Case: Pagination**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/media?account_id=1&limit=10&after=QASFZ5U5E6CZ2s..." \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### 8. List Connected Accounts

**Test Case: Get All Instagram Accounts**
```bash
curl -X GET "http://localhost:8000/api/sns/instagram/accounts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
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
    "profile_picture_url": "https://instagram.fxxx-1.fna.fbcdn.net/v/...",
    "account_type": "business",
    "followers_count": 15420,
    "following_count": 850,
    "token_expires_at": "2026-04-26T00:00:00Z",
    "created_at": "2026-02-26T10:00:00Z"
  },
  {
    "id": 2,
    "platform": "instagram",
    "account_name": "marketing_team",
    "is_active": true,
    "platform_user_id": "987654321",
    "profile_picture_url": "https://instagram.fxxx-1.fna.fbcdn.net/v/...",
    "account_type": "business",
    "followers_count": 45230,
    "following_count": 1200,
    "token_expires_at": "2026-04-27T00:00:00Z",
    "created_at": "2026-02-25T14:30:00Z"
  }
]
```

---

### 9. Disconnect Account

**Test Case: Remove Instagram Account**
```bash
curl -X DELETE "http://localhost:8000/api/sns/instagram/accounts/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response (200):**
```json
{
  "message": "Account disconnected successfully"
}
```

---

## Python Client Examples

### Example 1: Direct Class Usage

```python
from backend.services.instagram_api import InstagramAPI, InstagramAPIError

# Initialize
api = InstagramAPI('your_access_token_here')

# Get account info
try:
    info = api.get_account_info()
    print(f"Account: {info['username']}")
    print(f"Followers: {info['followers_count']}")
except InstagramAPIError as e:
    print(f"Error: {e}")

# Post to feed
try:
    post_id = api.post_feed(
        'https://example.com/image.jpg',
        'Check out this amazing product!',
        ['marketing', 'instagood']
    )
    print(f"Posted! ID: {post_id}")
except InstagramAPIError as e:
    print(f"Post failed: {e}")

# Get insights
try:
    insights = api.get_insights('17892456789123456')
    print(f"Likes: {insights['likes']}")
    print(f"Engagement: {insights['engagement_rate']}%")
except InstagramAPIError as e:
    print(f"Insights error: {e}")
```

### Example 2: Flask Route Handler

```python
from flask import request, jsonify
from backend.models import db, SNSAccount, SNSPost
from backend.services.instagram_api import InstagramAPI, InstagramAPIError

@app.route('/api/sns/instagram/batch-post', methods=['POST'])
@require_auth
def batch_post_to_instagram():
    """Post same content to multiple accounts"""
    data = request.get_json()
    image_url = data.get('image_url')
    caption = data.get('caption')
    hashtags = data.get('hashtags', [])

    # Get user's Instagram accounts
    accounts = SNSAccount.query.filter_by(
        user_id=g.user_id,
        platform='instagram',
        is_active=True
    ).all()

    results = []
    for account in accounts:
        try:
            api = InstagramAPI(account.access_token)
            post_id = api.post_feed(image_url, caption, hashtags)

            # Save to database
            post = SNSPost(
                user_id=g.user_id,
                account_id=account.id,
                platform='instagram',
                content=caption,
                media_url=image_url,
                status='published',
                platform_post_id=post_id,
                published_at=datetime.utcnow()
            )
            db.session.add(post)

            results.append({
                'account': account.account_name,
                'status': 'success',
                'post_id': post_id
            })
        except InstagramAPIError as e:
            results.append({
                'account': account.account_name,
                'status': 'failed',
                'error': str(e)
            })

    db.session.commit()
    return jsonify(results), 207
```

### Example 3: Scheduled Analytics Updates

```python
from apscheduler.schedulers.background import BackgroundScheduler
from backend.models import SNSPost, SNSAnalytics

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour='0,6,12,18')  # Every 6 hours
def update_instagram_analytics():
    """Update analytics for all published Instagram posts"""

    # Get posts from last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    posts = SNSPost.query.filter(
        SNSPost.platform == 'instagram',
        SNSPost.status == 'published',
        SNSPost.published_at > cutoff
    ).all()

    for post in posts:
        account = post.account
        if not account or not account.access_token:
            continue

        try:
            api = InstagramAPI(account.access_token)
            insights = api.get_insights(post.platform_post_id)

            # Update or create analytics
            analytics = SNSAnalytics.query.filter_by(
                post_id=post.id
            ).first()

            if not analytics:
                analytics = SNSAnalytics(post_id=post.id)

            analytics.likes = insights.get('likes', 0)
            analytics.comments = insights.get('comments', 0)
            analytics.shares = insights.get('shares', 0)
            analytics.reach = insights.get('reach', 0)
            analytics.updated_at = datetime.utcnow()

            db.session.add(analytics)
        except Exception as e:
            logger.error(f"Failed to update analytics for post {post.id}: {e}")
            continue

    db.session.commit()
    logger.info(f"Updated analytics for {len(posts)} posts")

scheduler.start()
```

### Example 4: Error Handling & Token Refresh

```python
def post_with_auto_refresh(account, image_url, caption, hashtags):
    """Post with automatic token refresh on expiry"""

    try:
        api = InstagramAPI(account.access_token)
        post_id = api.post_feed(image_url, caption, hashtags)
        return post_id, None

    except InstagramAPIError as e:
        if "token" in str(e).lower() or "401" in str(e):
            logger.info(f"Token expired for account {account.id}, refreshing...")

            try:
                # Refresh token
                new_token = api.refresh_access_token(account.access_token)
                account.access_token = new_token
                account.token_expires_at = datetime.utcnow() + timedelta(days=60)
                db.session.commit()

                logger.info(f"Token refreshed for account {account.id}")

                # Retry post
                api = InstagramAPI(new_token)
                post_id = api.post_feed(image_url, caption, hashtags)
                return post_id, None

            except Exception as refresh_error:
                logger.error(f"Token refresh failed: {refresh_error}")
                return None, f"Token refresh failed: {refresh_error}"
        else:
            return None, str(e)
```

---

## Error Scenarios & Handling

### Scenario 1: Rate Limit (429)

**Error:**
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

**Handling:**
```python
import time

def post_with_retry(api, image_url, caption, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api.post_feed(image_url, caption)
        except InstagramAPIError as e:
            if "rate limit" in str(e).lower():
                wait_time = (2 ** attempt) * 60  # Exponential backoff
                logger.info(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise InstagramAPIError("Max retries exceeded")
```

### Scenario 2: Invalid Credentials

**Error:**
```json
{
  "error": "Access token expired. Please re-authenticate."
}
```

**Handling:**
```python
# Redirect user to OAuth flow
return {
    'error': 'Authentication required',
    'action': 'redirect',
    'auth_url': '/api/sns/instagram/oauth/authorize'
}, 401
```

### Scenario 3: Invalid Image Format

**Error:**
```json
{
  "error": "Invalid image format. Supported: JPEG, PNG"
}
```

**Handling:**
```python
from PIL import Image
import requests
from io import BytesIO

def validate_image_url(image_url):
    try:
        response = requests.get(image_url, timeout=5)
        img = Image.open(BytesIO(response.content))
        if img.format not in ['JPEG', 'PNG']:
            raise ValueError(f"Unsupported format: {img.format}")
        if img.size[0] < 320 or img.size[1] < 320:
            raise ValueError("Image too small (min 320x320)")
        return True
    except Exception as e:
        raise InstagramAPIError(f"Invalid image: {e}")
```

---

## Testing with Postman

### Environment Variables

```json
{
  "variables": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "type": "string"
    },
    {
      "key": "jwt_token",
      "value": "eyJhbGciOiJIUzI1NiIs...",
      "type": "string"
    },
    {
      "key": "account_id",
      "value": "1",
      "type": "number"
    }
  ]
}
```

### Create Feed Post Request

```
POST {{base_url}}/api/sns/instagram/posts
Authorization: Bearer {{jwt_token}}

{
  "account_id": {{account_id}},
  "image_url": "https://example.com/image.jpg",
  "caption": "Test post from Postman",
  "hashtags": ["test", "postman"]
}
```

---

## Performance Benchmarks

| Operation | Avg Time | Max Time |
|-----------|----------|----------|
| Authenticate | 1.2s | 2.5s |
| Post Feed | 0.8s | 1.5s |
| Post Story | 0.6s | 1.2s |
| Post Reel | 2.1s | 4.0s |
| Get Insights | 0.5s | 0.9s |
| Get Account Info | 0.4s | 0.8s |
| Get Media (25 items) | 0.7s | 1.3s |

---

**Last Updated:** 2026-02-26