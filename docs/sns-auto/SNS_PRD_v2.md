# SNS Automation v2.0 — Product Requirements Document
> **Status:** In Development | **Version:** 2.0 | **Target:** 2026-03-15 | **Team Lead:** Team A (Business Strategy)

## 1. Executive Summary

**SNS Auto v2.0** is a comprehensive global SNS automation platform supporting 9 international SNS platforms (Instagram, Facebook, Twitter, LinkedIn, TikTok, YouTube, Pinterest, Threads, YouTube Shorts) with advanced features including:
- OAuth-based account authentication (security-first)
- Multi-platform simultaneous publishing
- AI-powered content generation
- Advanced analytics & engagement tracking
- Unified inbox management
- Campaign coordination
- Template system with placeholders
- Optimal posting time detection
- Integration with Telegram notifications

**Business Goal:** Enable users to manage all SNS accounts from a single dashboard with minimal effort, matching Buffer.com & Hootsuite feature parity.

---

## 2. Product Vision

### Success Metrics (12 months)
- **Monthly Active Users:** 5,000 → 50,000
- **Accounts per User:** Avg 3.2 (multi-platform strategy)
- **Daily Posts:** 10,000 → 100,000
- **Platform Coverage:** 9 platforms (100% of major SNS)
- **Feature Adoption:** AI Generate 60%, Analytics 80%, Campaigns 40%

### Competitive Analysis

| Feature | Buffer | Hootsuite | Later | Meta Business Suite | **SNS Auto v2.0** |
|---------|--------|-----------|-------|-------------------|---|
| Platforms | 6 | 7 | 5 | 3 | **9** |
| AI Content Gen | Yes (paid) | Yes (paid) | No | No | **Yes (built-in)** |
| Multi-schedule | Yes | Yes | Yes | Limited | **Yes** |
| Analytics | Good | Excellent | Good | Basic | **Very Good** |
| Team Collaboration | Limited | Yes | Yes | Yes | **Planned v2.1** |
| Price | $5-$99 | $19-$739 | $15-$30 | Free | **$49/month** |

---

## 3. Feature Breakdown

### 3.1 Core Publishing (Must-Have)
- [x] Create multi-platform posts in one editor
- [x] Schedule posts with timezone support
- [x] Publish to 9 platforms simultaneously
- [x] Media upload (images, video, carousel)
- [x] Hashtag management & suggestions
- [x] URL shortening & tracking
- [x] Draft/Schedule/Publish workflow

### 3.2 OAuth & Account Management (Security-First)
- [x] Secure OAuth login for all 9 platforms
- [x] Token refresh automation (background job)
- [x] Permission scopes: read, write, analytics, messaging
- [x] Account health monitoring
- [x] Connection status & expiry warnings
- [x] Quick reconnect UI

### 3.3 Analytics & Insights (Competitive Edge)
- [x] Real-time engagement metrics (likes, comments, views, reach)
- [x] Historical analytics with date range selection
- [x] Per-post performance dashboard
- [x] Follower growth tracking
- [x] Optimal posting time detection (ML-based)
- [x] Engagement rate calculation
- [x] Export analytics (CSV/PDF)

### 3.4 Unified Inbox (Unique Value)
- [x] Centralized message center (DMs, comments, mentions)
- [x] Multi-account conversation threading
- [x] Smart filtering (unread, by platform, by sender)
- [x] Inline reply with platform-appropriate formatting
- [x] Read/unread status tracking

### 3.5 AI Content Generation (Differentiator)
- [x] AI topic → content generation (Claude API)
- [x] AI hashtag suggestions
- [x] AI content optimization for each platform
- [x] Tone adjustment (professional, casual, humorous, inspirational)
- [x] Graceful fallback (if API key missing, use templates)

### 3.6 Campaign Management (Organization)
- [x] Multi-post campaign coordination
- [x] Campaign scheduling (start/end dates)
- [x] Post grouping by campaign
- [x] Campaign-level analytics aggregation

### 3.7 Templates (Efficiency)
- [x] System templates (pre-built by team)
- [x] Custom templates (user-created)
- [x] Placeholder variables ({brand}, {promo_code}, etc.)
- [x] Platform-specific templates
- [x] Template categories (promotional, educational, engagement)

### 3.8 Settings & Preferences
- [x] Auto-optimal time posting (enabled/disabled)
- [x] Engagement notifications
- [x] Auto-reply to comments (enable/disable)
- [x] Banned keywords (content moderation)

### 3.9 Telegram Integration
- [x] Real-time publishing notifications
- [x] Daily summary reports
- [x] Status alerts (failed posts, token expiry)

---

## 4. Technical Architecture

### 4.1 Frontend Architecture
```
web/sns-auto/
├── index.html (Dashboard + navigation)
├── create.html (Post editor)
├── schedule.html (Calendar view)
├── analytics.html (Metrics dashboard)
├── accounts.html (Account management)
├── settings.html (User preferences)
├── templates.html (Template manager)
├── inbox.html (Unified inbox) — NEW
├── campaigns.html (Campaign manager) — NEW
└── api.js (API client, 57 functions)
```

### 4.2 Backend Architecture
```
backend/
├── app.py (Flask entry point)
├── models.py (Database schemas)
├── auth.py (JWT, @require_auth decorator)
├── services/
│   ├── sns_auto.py (32 endpoints, ~900 lines)
│   ├── sns_cache.py (Caching layer)
│   ├── sns_platforms/
│   │   ├── __init__.py (Platform factory)
│   │   ├── base_client.py (Abstract base)
│   │   ├── instagram_client.py
│   │   ├── facebook_client.py
│   │   ├── twitter_client.py
│   │   ├── linkedin_client.py
│   │   ├── tiktok_client.py
│   │   ├── youtube_client.py
│   │   ├── pinterest_client.py
│   │   └── threads_client.py
│   └── scheduler.py (Background job runner)
├── uploads/sns/ (Media storage)
└── database.py (SQLAlchemy models)
```

### 4.3 Database Schema (v2.0)
**9 Tables added/modified:**
- `sns_accounts` — expanded with OAuth fields
- `sns_posts` — expanded with analytics fields
- `sns_campaigns` — NEW (campaign coordination)
- `sns_templates` — NEW (reusable templates)
- `sns_analytics` — NEW (daily snapshots)
- `sns_inbox_messages` — NEW (unified inbox)
- `sns_oauth_states` — NEW (CSRF prevention)
- `sns_settings` — NEW (user preferences)

### 4.4 API Endpoints (32 endpoints)

#### OAuth (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/oauth/{platform}/authorize` | Initiate OAuth flow |
| GET | `/oauth/{platform}/callback` | OAuth callback handler |
| GET | `/oauth/{platform}/simulate-callback` | Demo mode callback |

#### Accounts (4)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/accounts` | List all accounts |
| POST | `/accounts` | Add new account |
| GET | `/accounts/{id}` | Get account details |
| POST | `/accounts/{id}/reconnect` | Reconnect expired token |

#### Posts (5)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/posts` | List all posts |
| POST | `/posts` | Create draft post |
| POST | `/posts/bulk` | Create multi-account post |
| PUT | `/posts/{id}` | Update post |
| POST | `/posts/{id}/retry` | Retry failed post |
| GET | `/posts/{id}/metrics` | Get post metrics |

#### Analytics (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/analytics` | Aggregated metrics (all accounts) |
| GET | `/analytics/accounts/{id}` | Account-specific metrics |
| GET | `/analytics/optimal-time/{id}` | Optimal posting time for account |

#### Media (2)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/media/upload` | Upload image/video |
| GET | `/media` | List uploaded media |

#### Templates (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/templates` | List templates |
| POST | `/templates` | Create custom template |
| PUT | `/templates/{id}` | Update template |
| DELETE | `/templates/{id}` | Delete template |

#### Inbox (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/inbox` | List inbox messages |
| POST | `/inbox/{id}/reply` | Reply to message |
| PUT | `/inbox/{id}/read` | Mark as read |

#### Calendar (1)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/calendar` | Get scheduled posts (month view) |

#### Campaigns (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/campaigns` | List campaigns |
| POST | `/campaigns` | Create campaign |
| GET | `/campaigns/{id}` | Get campaign details |
| PUT | `/campaigns/{id}` | Update campaign |
| DELETE | `/campaigns/{id}` | Delete campaign |

#### AI (3)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ai/generate` | Generate content from topic |
| POST | `/ai/hashtags` | Generate hashtags |
| POST | `/ai/optimize` | Optimize content for platform |

#### Settings (2)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/settings` | Get user settings |
| PUT | `/settings` | Update settings |

---

## 5. User Workflows

### Workflow 1: Schedule Multi-Platform Post
```
1. User navigates to create.html
2. Selects multiple accounts (Instagram, TikTok, LinkedIn)
3. Writes content with character count feedback
4. Uploads media (checked for size & type)
5. Adds hashtags (AI suggestions optional)
6. Schedules for next Monday 9:00 AM
7. System confirms scheduled post appears on schedule.html calendar
8. At scheduled time, scheduler.py publishes to all platforms
9. User receives Telegram notification: "Post published: 3 accounts, 250 likes in 1 hour"
```

### Workflow 2: Unified Inbox Management
```
1. User navigates to inbox.html
2. Sees 47 unread comments across Instagram & TikTok
3. Filters by platform (Instagram) → 23 comments
4. Clicks comment from @follower_123
5. Sees comment thread + inline reply field
6. Types reply, hits send
7. Backend posts reply using Instagram API
8. Message marked as read, notification sent to user
```

### Workflow 3: AI-Powered Content Generation
```
1. User on create.html clicks "AI Generate"
2. Enters topic: "New product launch - eco-friendly water bottle"
3. Selects platform: Instagram
4. Clicks "Generate"
5. AI returns:
   - Content: "🌍 Meet GreenFlow... [compelling copy]"
   - Hashtags: ["#EcoFriendly", "#Sustainable", ...]
6. User reviews, adjusts tone to "professional"
7. Adds media, schedules
```

### Workflow 4: Analytics Dashboard
```
1. User navigates to analytics.html
2. Selects date range: Last 7 days
3. Selects account: Instagram (default: all)
4. Sees 4 metric cards:
   - Total engagement: 1,234 (↑ 15%)
   - Total reach: 45,678 (↑ 8%)
   - Total impressions: 234,567
   - Follower growth: +123
5. Scrolls to chart: Engagement by day (line chart)
6. Hovers over day 3: "1,234 engagements (423 likes, 567 comments, 244 shares)"
7. Exports report as CSV
```

---

## 6. Non-Functional Requirements

### 6.1 Performance
- API response time: <500ms (p95)
- Dashboard load time: <2s
- Analytics query (full history): <3s
- Media upload: <30s for 50MB file

### 6.2 Security
- All tokens encrypted at rest (AES-256)
- OAuth state tokens expire after 10 minutes
- JWT tokens expire after 24 hours
- Rate limiting: 100 requests/minute per user
- Input validation on all endpoints (XSS, SQL injection prevention)
- File upload: whitelist MIME types, scan for viruses
- HTTPS only in production

### 6.3 Reliability
- 99.5% uptime SLA
- All posts logged (audit trail)
- Failed posts auto-retry (max 3 attempts with exponential backoff)
- Database backups: daily (full), hourly (incremental)

### 6.4 Scalability
- Support 100,000 concurrent users
- 1M posts/day without latency degradation
- Caching layer (Redis): 15-min TTL for analytics

---

## 7. Timeline & Milestones

| Phase | Target Date | Deliverables |
|-------|------------|--------------|
| **v2.0 Core** | 2026-03-15 | OAuth, publishing, scheduler, analytics, inbox, campaigns |
| **v2.1 Team** | 2026-04-15 | Team collaboration, comment assignment, shared assets |
| **v2.2 Advancedx | 2026-05-15 | Webhook receivers, auto-reply, content moderation, competitor tracking |
| **v3.0 Enterprise** | 2026-07-01 | SSO, audit logs, advanced reporting, API for integrations |

---

## 8. Success Criteria

✅ All 32 endpoints implemented & tested
✅ 9 platform clients working (mock/live)
✅ UI responsive on mobile (320px+)
✅ 100+ unit/integration tests passing
✅ 0 Critical security issues (OWASP Top 10)
✅ Scheduler running 24/7 with zero data loss
✅ Analytics accurate within 1-hour lag
✅ Zero tokens leaked in logs/errors
✅ Full audit trail of all post modifications

---

## 9. Open Questions & Assumptions

### Assumptions
1. Users have valid OAuth credentials for platforms
2. Instagram provides analytics API access (may require Business account)
3. TikTok API available (requires developer approval)
4. Pinterest API access granted
5. Threads API available (currently limited beta)

### Open Items (To Be Resolved)
1. Which platforms support webhook receivers? (for real-time updates)
2. Should we support private accounts? (limited APIs)
3. Multi-language support scope? (Phase 2.1?)
4. Video transcoding for platform-specific requirements?

---

## 10. Acceptance Criteria Checklist

- [ ] All 32 endpoints return correct status codes
- [ ] OAuth flow works for all 9 platforms (mock mode)
- [ ] Posts published to live platforms (demo account)
- [ ] Scheduler runs every 60 seconds without errors
- [ ] Analytics update within 15 minutes of post interaction
- [ ] Telegram notifications received in real-time
- [ ] UI passes accessibility testing (WCAG 2.1 AA)
- [ ] Performance tests pass (load test: 1000 users)
- [ ] Security audit: 0 Critical, ≤3 High
- [ ] Documentation: API docs complete, User guide ready

---

**Approved by:** Team A (Business Strategy)
**Last updated:** 2026-02-25
