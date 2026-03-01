# 🔌 Telegram Bot Scheduler Integration — API Documentation

> **Purpose**: Complete Telegram integration for SNS automation platform. Users receive real-time Telegram notifications when:
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Telegram Bot Scheduler Integration — API Documentation 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Overview

Complete Telegram integration for SNS automation platform. Users receive real-time Telegram notifications when:
- SNS posts are published successfully
- SNS posts fail to publish
- Automation rules execute
- Daily summary reports at 9 AM UTC

## Architecture

### Components

1. **telegram_service.py** — Core notification service
   - `TelegramService` class with static methods for sending formatted messages
   - Supports all Telegram message types (text, links, formatting)
   - Graceful error handling

2. **telegram_routes.py** — Flask Blueprint with 5 endpoints
   - Account linking / unlinking
   - Status verification
   - Test message sending

3. **scheduler.py** — Enhanced with Telegram integration
   - `execute_scheduled_posts()` sends notifications on success/failure
   - `send_daily_telegram_summary()` runs daily at 9 AM UTC
   - Integrated error handling

4. **models.py** — SNSSettings model enhancement
   - New fields: `telegram_chat_id`, `telegram_enabled`
   - Backward compatible (nullable fields)

5. **app.py** — Blueprint registration
   - Registers `telegram_bp` with Flask app

## API Endpoints

All endpoints require authentication via `@require_auth` decorator (JWT token in header).

### 1. GET /api/telegram/link-account

Generate a Telegram account linking URL.

**Request:**
```
GET /api/telegram/link-account
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "linking_url": "https://t.me/piwpiwtelegrambot?start=user_123_abc456...",
  "token": "user_123_abc456...",
  "instructions": "Click the link to open Telegram and send /start to the bot to complete linking.",
  "bot_username": "piwpiwtelegrambot"
}
```

**Process:**
1. User calls this endpoint
2. Receive linking URL with unique token
3. User clicks URL (opens Telegram)
4. User sends `/start` command to bot
5. Bot forwards chat_id to verify endpoint

### 2. POST /api/telegram/verify-link

Verify Telegram linking and save chat_id to SNSSettings.

**Request:**
```json
{
  "token": "user_123_abc456...",
  "chat_id": "7910169750"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Telegram account linked successfully",
  "telegram_enabled": true
}
```

**Process:**
1. Bot receives user's chat_id
2. Bot calls this endpoint with token + chat_id
3. Endpoint verifies token (token must exist and belong to authenticated user)
4. Saves chat_id to SNSSettings
5. Sends confirmation message to user via Telegram

### 3. GET /api/telegram/status

Check Telegram connection status for current user.

**Request:**
```
GET /api/telegram/status
Authorization: Bearer <JWT_TOKEN>
```

**Response (Linked):**
```json
{
  "telegram_enabled": true,
  "telegram_chat_id": "7910169750",
  "linked_at": "2026-02-26T10:30:00"
}
```

**Response (Not Linked):**
```json
{
  "telegram_enabled": false,
  "message": "Telegram account not linked. Use /link-account endpoint to connect."
}
```

### 4. POST /api/telegram/send-test-message

Send a test message to verify Telegram connection.

**Request:**
```
POST /api/telegram/send-test-message
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test message sent successfully"
}
```

**Message sent to user:**
```
🧪 테스트 메시지

Telegram 연동이 정상적으로 작동합니다! ✅
```

### 5. POST /api/telegram/unlink-account

Unlink Telegram account.

**Request:**
```
POST /api/telegram/unlink-account
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Telegram account unlinked successfully"
}
```

## Notification Types

### 1. Post Success Notification

**Trigger:** SNS post published successfully

**Format:**
```
✅ SNS 게시 완료

📸 Instagram
📝 [Post content preview...]
🔗 [Link to post]
👥 좋아요: 1,234 | 댓글: 56
⏰ 2026-02-26 10:30:00 UTC
```

**Code:**
```python
send_sns_notification(user_id, 'post_success', {
    'platform': 'instagram',
    'content': 'Post content here...',
    'likes': 1234,
    'comments': 56,
    'post_url': 'https://instagram.com/p/...'
})
```

### 2. Post Failure Notification

**Trigger:** SNS post publication failed

**Format:**
```
❌ SNS 게시 실패

📱 플랫폼: Instagram
⚠️ 오류: [Error message]
⏰ 2026-02-26 10:30:00 UTC

자세한 내용은 대시보드에서 확인하세요.
```

**Code:**
```python
send_sns_notification(user_id, 'post_failure', {
    'platform': 'instagram',
    'error': 'Connection timeout'
})
```

### 3. Automation Executed Notification

**Trigger:** SNS automation rule executed successfully

**Format:**
```
🤖 자동화 규칙 실행

📋 규칙: [Rule name]
📱 플랫폼: Instagram, Twitter
✅ 상태: 완료
⏰ 실행 시간: 2026-02-26 10:30:00 UTC
📅 2026-02-26 10:30:00 UTC
```

**Code:**
```python
send_sns_notification(user_id, 'automation_executed', {
    'automation_name': 'Daily Instagram Post',
    'platforms': ['instagram', 'twitter'],
    'execution_time': '2026-02-26 10:30:00 UTC'
})
```

### 4. Daily Summary Notification

**Trigger:** Scheduled daily at 9 AM UTC

**Format:**
```
📊 일일 SNS 리포트

📝 게시물: 5개
✅ 성공: 5개
❌ 실패: 0개
👥 총 참여: 2,345

플랫폼별 통계:
📸 Instagram: 3 게시 | 👥 1,234
🐦 Twitter: 2 게시 | 👥 1,111

📅 2026-02-26
```

**Code:**
```python
send_sns_notification(user_id, 'daily_summary', {
    'total_posts': 5,
    'successful_posts': 5,
    'failed_posts': 0,
    'total_engagement': 2345,
    'platforms': {
        'instagram': {'posts': 3, 'engagement': 1234},
        'twitter': {'posts': 2, 'engagement': 1111}
    }
})
```

## Scheduler Integration

### execute_scheduled_posts() — Enhanced

When SNS posts or automation rules execute:
- If successful: Sends `automation_executed` notification
- If failed: Sends `post_failure` notification with error details
- All Telegram errors logged (non-blocking)

```python
# Line 605-613 in scheduler.py
send_sns_notification(
    rule.user_id,
    'automation_executed',
    {
        'automation_name': rule.name or f'Auto-rule {rule.id}',
        'platforms': platforms,
        'execution_time': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
    }
)
```

### send_daily_telegram_summary() — New Job

Runs daily at 9 AM UTC (CronTrigger).

**Process:**
1. Query all users with `telegram_enabled = True`
2. For each user, aggregate yesterday's posts
3. Calculate metrics: success/fail count, engagement
4. Group by platform with per-platform engagement
5. Send summary via `send_sns_notification()`

**Configuration:**
```python
# In init_scheduler()
scheduler.add_job(
    send_daily_telegram_summary,
    CronTrigger(hour=9, minute=0),
    id='telegram_daily_summary',
    name='Telegram Daily Summary',
    replace_existing=True,
    kwargs={'app': app},
)
```

## Database Changes

### SNSSettings Model Update

**New Fields:**
```python
telegram_chat_id = db.Column(db.String(100), nullable=True)  # User's Telegram chat ID
telegram_enabled = db.Column(db.Boolean, default=False)  # Enable/disable notifications
```

**Updated to_dict():**
```python
def to_dict(self):
    return {
        # ... existing fields ...
        'telegram_chat_id': self.telegram_chat_id,
        'telegram_enabled': self.telegram_enabled,
    }
```

## Configuration

### Required Environment Variables

Already present in `.env`:
```
TELEGRAM_BOT_TOKEN=8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM
```

### Telegram Bot Setup

1. Bot username: `@piwpiwtelegrambot`
2. Bot ID: `8461725251`
3. Token stored in `TELEGRAM_BOT_TOKEN` environment variable
4. Allowed users: Any user can link their account (secured by JWT auth)

## Error Handling

### Graceful Degradation

- Telegram send failures don't block SNS posting
- All Telegram errors logged with context
- Failed notifications don't affect job execution
- Users can unlink if needed

### Retry Logic

- No automatic retry (Telegram API is highly reliable)
- Failed sends logged in job history
- Can manually trigger daily summary via `GET /scheduler/jobs/{id}/trigger`

## Testing

### Manual Testing

```bash
# 1. Get linking URL
curl -X GET http://localhost:8000/api/telegram/link-account \
  -H "Authorization: Bearer <JWT_TOKEN>"

# 2. Check status
curl -X GET http://localhost:8000/api/telegram/status \
  -H "Authorization: Bearer <JWT_TOKEN>"

# 3. Send test message
curl -X POST http://localhost:8000/api/telegram/send-test-message \
  -H "Authorization: Bearer <JWT_TOKEN>"

# 4. Unlink account
curl -X POST http://localhost:8000/api/telegram/unlink-account \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Integration Testing

1. Create test SNS post with automation rule
2. Trigger `execute_scheduled_posts` job
3. Verify Telegram notification received
4. Check scheduler history: `GET /api/admin/scheduler/status`

## Security

### Authentication

- All endpoints require valid JWT token
- Token verified via `@require_auth` decorator
- Chat ID belongs to authenticated user only

### Data Protection

- Chat IDs stored in database (encrypted in production)
- Linking tokens are single-use and time-limited
- Tokens stored in-memory (cleared after use)

### Rate Limiting

- Telegram API: 30 msg/sec per chat (bot token specific)
- No local rate limiting (low-risk endpoint)

## Deployment Checklist

- [x] Models updated (telegram_chat_id, telegram_enabled)
- [x] telegram_service.py created
- [x] telegram_routes.py with 5 endpoints
- [x] scheduler.py enhanced with Telegram notifications
- [x] Daily summary job added (9 AM UTC)
- [x] app.py blueprint registered
- [x] Error handling integrated
- [x] Documentation complete

## Future Enhancements

1. **Webhook Mode** — Use webhook instead of polling for incoming messages
2. **Inline Buttons** — Add quick-action buttons (View Post, Retry, Disable)
3. **Message Editing** — Edit live notification with updated metrics
4. **File Uploads** — Send post screenshots/previews
5. **Custom Time Zones** — Per-user daily summary time
6. **Notification Preferences** — Mute/unmute specific event types
7. **Redis Linking** — Move linking tokens to Redis for durability
8. **Telegram Groups** — Support group notifications for team accounts

## Support

**Issue?** Check:
1. TELEGRAM_BOT_TOKEN is valid in .env
2. Bot is accessible: `https://api.telegram.org/botTOKEN/getMe`
3. Chat ID format is correct (digits only)
4. User has Telegram notifications enabled
5. Check scheduler job history for errors

**Debug Mode:** Set `LOG_LEVEL=DEBUG` in .env

## Files Modified/Created

```
backend/
├── telegram_service.py          [NEW] Core notification service
├── services/
│   └── telegram_routes.py       [NEW] Flask Blueprint with 5 endpoints
├── scheduler.py                 [MODIFIED] Enhanced with Telegram notifications
├── models.py                    [MODIFIED] SNSSettings: add telegram_chat_id, telegram_enabled
└── app.py                       [MODIFIED] Import & register telegram_bp

docs/
└── TELEGRAM_BOT_INTEGRATION.md  [NEW] This file
```

---

**Status:** Production Ready
**Last Updated:** 2026-02-26
**Version:** 1.0