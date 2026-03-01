# API Endpoint Quick Reference — SoftFactory v2.0
> **Complete endpoint listing with methods, paths, and integrations**
>
> **Updated:** 2026-02-26 | **Endpoints:** 100+ | **Format:** [METHOD] /path → Description

---

## QUICK INDEX

- [Authentication (12 endpoints)](#authentication)
- [SNS Automation (25+ endpoints)](#sns-automation)
- [Payment System (15+ endpoints)](#payment-system)
- [File Storage (6 endpoints)](#file-storage)
- [Review Aggregation (20+ endpoints)](#review-aggregation)
- [CooCook Platform (33+ endpoints)](#coocook-platform)
- [Real-time Events (28+ WebSocket events)](#real-time-websocket-events)
- [Admin & Monitoring (30+ endpoints)](#admin--monitoring)
- [Search & Discovery (10+ endpoints)](#search--discovery)
- [i18n & Localization (6 endpoints)](#i18n--localization)
- [RBAC & Permissions (16+ endpoints)](#rbac--permissions)

---

## AUTHENTICATION

### Basic Auth (12 endpoints)

```
POST   /api/auth/register                Email/password signup
POST   /api/auth/login                   Email/password login
POST   /api/auth/refresh                 Refresh JWT token
POST   /api/auth/logout                  Invalidate tokens
GET    /api/auth/user                    Get current user
POST   /api/auth/verify-2fa              Verify TOTP code
POST   /api/auth/2fa/setup               Enable 2FA
GET    /api/auth/2fa/backup-codes        Get backup codes
POST   /api/auth/password/reset          Request password reset
PUT    /api/auth/password/reset/<token>  Complete password reset
PUT    /api/auth/profile                 Update user profile
DELETE /api/auth/account                 Delete account permanently
```

### OAuth Social Login (6 endpoints)

```
GET    /api/auth/oauth/google/url        → auth_url, state_token
GET    /api/auth/oauth/google/callback   → access_token, refresh_token
GET    /api/auth/oauth/facebook/url      → auth_url, state_token
GET    /api/auth/oauth/facebook/callback → access_token, refresh_token
GET    /api/auth/oauth/kakao/url         → auth_url, state_token
GET    /api/auth/oauth/kakao/callback    → access_token, refresh_token
```

### Mock OAuth (for testing without credentials)

```
GET    /api/auth/oauth/mock              → Generates test user + tokens
POST   /api/auth/oauth/mock/login        → Login with mock email
```

---

## SNS AUTOMATION

### Posts (10 endpoints)

```
POST   /api/sns/posts                    Create post
  Body: { platforms: ['instagram','twitter'], content, image_url?, scheduled_at? }
  Response: { post_id, status: 'draft|scheduled|published', created_at }

PUT    /api/sns/posts/<id>               Edit post (before publishing)
GET    /api/sns/posts                    List user's posts (paginated)
  Query: ?limit=20&offset=0&platform=instagram&status=published
GET    /api/sns/posts/<id>               Get post details
DELETE /api/sns/posts/<id>               Delete post
GET    /api/sns/posts/<id>/comments      Get post comments
POST   /api/sns/posts/<id>/comments      Comment on post
GET    /api/sns/posts/<id>/likes         Get post likers
POST   /api/sns/posts/<id>/like          Like post
```

### AI Content Generation (5 endpoints)

```
POST   /api/sns/ai/generate              Generate content from topic
  Body: { topic, platforms: [], tone: 'casual|professional|funny', language: 'ko|en|ja|zh' }
  Response: { content, hashtags[], estimated_engagement }

POST   /api/sns/ai/repurpose            Convert content between formats
  Body: { original_content, source_platform, target_platform }
  Response: { repurposed_content, changes_made[] }

POST   /api/sns/ai/hashtag-recommend    Suggest hashtags
  Body: { content, platform, max_hashtags: 30 }
  Response: { hashtags[], trending_hashtags[], estimated_reach }

POST   /api/sns/ai/caption-generate     Create captions for images
  Body: { image_url, platform, style: 'formal|casual|humorous' }
  Response: { captions: ['caption1', 'caption2', ...] }

POST   /api/sns/ai/best-time            Determine optimal posting time
  Body: { platform, audience_country: 'KR|US|JP', content_type: 'reel|post|story' }
  Response: { best_time: 'HH:MM', confidence: 0.87, reasoning: '...' }
```

### Automation & Scheduling (6 endpoints)

```
POST   /api/sns/automate                 Create auto-posting schedule
  Body: { topic, platforms: [], frequency: 'daily|weekly|monthly', description }
  Response: { automation_id, next_run, status: 'active|paused' }

GET    /api/sns/automate                 List automation rules
GET    /api/sns/automate/<id>            Get automation details
PUT    /api/sns/automate/<id>            Update automation
DELETE /api/sns/automate/<id>            Stop automation
POST   /api/sns/automate/<id>/run        Trigger immediately
```

### Monetization (9 endpoints)

```
GET    /api/sns/analytics                Overall analytics dashboard
  Response: { total_posts, total_engagement, total_reach, growth_rate, top_performers[] }

GET    /api/sns/linkinbio                Get all links-in-bio
POST   /api/sns/linkinbio                Create new link
  Body: { title, url, icon_type, position }
  Response: { link_id, slug, click_count, created_at }

GET    /api/sns/linkinbio/<id>/stats     Click statistics for link
  Response: { total_clicks, clicks_by_date[], clicks_by_platform[], referrers[] }

PUT    /api/sns/linkinbio/<id>           Update link
DELETE /api/sns/linkinbio/<id>           Delete link

GET    /api/sns/roi                      ROI calculation
  Body: { start_date, end_date, campaign_type }
  Response: { total_revenue_krw, total_spend_krw, roi_percentage, roas }

GET    /api/sns/trending                 Trending topics & hashtags
  Query: ?platform=instagram&language=ko&limit=10
  Response: { trending_topics[], volume[], growth_rate[] }

POST   /api/sns/competitor               Add competitor for tracking
GET    /api/sns/competitor/<id>/analysis Get competitor analytics
  Response: { follower_count, avg_engagement, posting_frequency, top_posts[] }
```

---

## PAYMENT SYSTEM

### Subscription Plans (3 endpoints)

```
GET    /api/payment/plans                List active subscription plans
  Response: [{ plan_id, name, slug, monthly_price_krw, annual_price_krw, features[], max_projects }]

POST   /api/payment/subscribe            Create subscription
  Body: { plan_id|plan_slug, billing_period: 'monthly|annual', stripe_token }
  Response: { subscription_id, status: 'active', next_billing_date, amount_krw }

GET    /api/payment/subscriptions        Get user's subscriptions
PUT    /api/payment/subscriptions/<id>   Update subscription (plan change, payment method)
DELETE /api/payment/subscriptions/<id>   Cancel subscription
```

### Invoicing (8 endpoints)

```
POST   /api/payment/invoice              Generate invoice
  Body: { order_id?, items: [{ description, quantity, price_krw }], tax_percent: 10, due_days: 30 }
  Response: { invoice_id, invoice_number: 'YYYYMMDD-XXXX', pdf_url, stripe_invoice_url, total_krw }

GET    /api/payment/invoices             List invoices (paginated)
GET    /api/payment/invoices/<id>        Get invoice details
PUT    /api/payment/invoices/<id>/status Update status ('draft|issued|paid|canceled')
POST   /api/payment/invoices/<id>/send   Send invoice by email
GET    /api/payment/invoices/<id>/pdf    Download PDF
DELETE /api/payment/invoices/<id>        Delete invoice (draft only)

POST   /api/payment/webhook              Stripe webhook receiver (charge.succeeded, etc.)
```

### Payment History (2 endpoints)

```
GET    /api/payment/history              Combined invoices + payments view
  Query: ?status=paid|pending&start_date=2026-01-01&end_date=2026-12-31&limit=50
  Response: { total, history: [{ id, type: 'invoice|payment', date, amount_krw, status }] }

GET    /api/payment/statements           Monthly statement (invoice aggregation)
```

### Orders (2 endpoints)

```
POST   /api/orders                       Create order
  Body: { items: [{ product_id, quantity, price_krw }], billing_address, shipping_address }
  Response: { order_id, order_number, status: 'pending', total_krw, created_at }

GET    /api/orders/<id>                  Get order details
```

---

## FILE STORAGE

### Upload & Management (6 endpoints)

```
POST   /api/files/upload                 Upload file to S3 (50MB max)
  Body: FormData { file, category: 'image|video|document' }
  Response: { file_id, file_key, original_filename, file_size, cdn_url, s3_url, uploaded_at }

GET    /api/files                        List user's files (paginated)
  Query: ?category=image&limit=20&sort=-created_at
  Response: { total, files: [{ file_id, filename, size, category, cdn_url, uploaded_at }] }

GET    /api/files/<id>                   Get file metadata
GET    /api/files/<id>/preview           Get thumbnail (150x150px for images)

POST   /api/files/presigned-url          Generate time-limited download URL
  Body: { file_id, expires_in_hours: 24 }
  Response: { presigned_url, expires_at }

DELETE /api/files/<id>                   Delete file from S3 & database
```

---

## REVIEW AGGREGATION

### Listings (6 endpoints)

```
GET    /api/review/aggregated            Get all listings from all platforms
  Query: ?platform=revu|reviewplace&category=&min_reward_krw=0&sort=-reward_value&limit=20
  Response: { total, listings: [{ listing_id, source_platform, title, reward_krw, deadline, max_applicants }] }

POST   /api/review/scrape/now            Trigger immediate scraping
  Response: { scraper_status: 'running|queued', estimated_time_seconds }

GET    /api/review/scrape/status         Check scraping status
  Response: { platform, last_scrape_time, next_scrape_time, listings_found, last_error }

POST   /api/review/listings/<id>/bookmark → Bookmark listing
DELETE /api/review/listings/<id>/bookmark → Remove bookmark

GET    /api/review/listings/bookmarked   → Get bookmarked listings
```

### Applications (8 endpoints)

```
GET    /api/review/applications          List user's applications
  Query: ?status=applied|selected|rejected|pending&sort=-applied_at
  Response: { total, applications: [{ app_id, listing_title, status, applied_at, reward_krw }] }

POST   /api/review/applications          Apply to listing
  Body: { listing_id, account_id }
  Response: { application_id, status: 'pending', applied_at }

GET    /api/review/applications/<id>     Get application details
PUT    /api/review/applications/<id>     Update application (status, notes)

POST   /api/review/applications/<id>/review → Submit review (with URL)
  Body: { review_url, review_content }
  Response: { application_id, status: 'review_submitted', verified_at }

GET    /api/review/applications/<id>/status → Check selection status
DELETE /api/review/applications/<id>     → Withdraw application
```

### Accounts (6 endpoints)

```
GET    /api/review/accounts              List managed accounts
  Response: { accounts: [{ account_id, platform, account_name, follower_count, success_rate }] }

POST   /api/review/accounts              Add new account
  Body: { platform: 'naver|instagram|blog|youtube', account_name, auth_token }
  Response: { account_id, status: 'verified|pending', created_at }

GET    /api/review/accounts/<id>         Get account details
PUT    /api/review/accounts/<id>         Update account (name, visibility, etc.)
DELETE /api/review/accounts/<id>         Remove account
GET    /api/review/accounts/<id>/stats   Account performance stats
```

### Auto-Apply Rules (6 endpoints)

```
GET    /api/review/auto-apply/rules      List auto-apply rules
POST   /api/review/auto-apply/rules      Create rule
  Body: { name, categories: [], min_reward_krw, max_applicants, preferred_accounts: [], is_active }
  Response: { rule_id, created_at, matches_pending }

GET    /api/review/auto-apply/rules/<id> Get rule details
PUT    /api/review/auto-apply/rules/<id> Update rule
DELETE /api/review/auto-apply/rules/<id> Delete rule

POST   /api/review/auto-apply/run        Run auto-apply now
  Response: { applications_created, accounts_used, next_run }

GET    /api/review/auto-apply/history    View past auto-apply executions
```

### Analytics (3 endpoints)

```
GET    /api/review/dashboard             Statistics
  Response: { total_applications, selection_rate, total_rewards_krw, pending_reviews }

GET    /api/review/analytics             Performance metrics
  Response: { applications_by_platform, success_by_category, earnings_by_source, trends }

GET    /api/review/success-rate          Per-platform success rates
  Response: [{ platform, success_rate, applications_count, avg_reward_krw }]
```

---

## COOCOOK PLATFORM

### Recipes (20+ endpoints)

```
GET    /api/recipes                      Search recipes
  Query: ?q=&category=&cuisine=&difficulty=&prep_time_min=0&limit=20
  Response: { total, recipes: [{ recipe_id, title, image, difficulty, prep_time_mins, ratings }] }

GET    /api/recipes/<id>                 Recipe details (full)
  Response: { recipe_id, title, ingredients, instructions, nutrition, reviews, ratings }

POST   /api/recipes                      Create recipe (creator only)
  Body: { title, ingredients: [{ name, quantity, unit }], instructions: [], nutrition_data }
  Response: { recipe_id, slug, created_at, status: 'draft|published' }

PUT    /api/recipes/<id>                 Edit recipe
DELETE /api/recipes/<id>                 Delete recipe

GET    /api/recipes/<id>/nutrition       Nutrition breakdown
  Response: { calories, protein_g, carbs_g, fat_g, fiber_g, allergens: [] }

GET    /api/recipes/<id>/reviews         Recipe reviews/ratings
POST   /api/recipes/<id>/reviews         Submit review
  Body: { rating: 1-5, review_text, image_url }

GET    /api/recipes/trending             Trending recipes
GET    /api/recipes/new                  Recently added recipes
GET    /api/recipes/<id>/similar         Similar recipes
```

### Shopping List (8 endpoints)

```
GET    /api/shopping-list                Get shopping lists
POST   /api/shopping-list                Create list
  Body: { name, items: [] }
  Response: { list_id, created_at, item_count }

GET    /api/shopping-list/<id>           List details
PUT    /api/shopping-list/<id>           Update list
DELETE /api/shopping-list/<id>           Delete list

POST   /api/shopping-list/<id>/items     Add item to list
PUT    /api/shopping-list/<id>/items/<iid> Update item (mark as bought)
DELETE /api/shopping-list/<id>/items/<iid> Remove item

POST   /api/shopping-list/add-recipe     Add all recipe ingredients
  Body: { list_id, recipe_id }
  Response: { list_id, items_added, total_estimated_cost_krw }

GET    /api/shopping-list/<id>/costs     Estimated cost by store
  Response: [{ store, total_cost_krw, items_price_breakdown }]
```

### Social (4 endpoints)

```
GET    /api/coocook/feed                 Activity feed
GET    /api/coocook/chefs                Chef profiles
POST   /api/coocook/chefs/<id>/follow    Follow chef
DELETE /api/coocook/chefs/<id>/follow    Unfollow chef
```

---

## REAL-TIME WEBSOCKET EVENTS

### SNS Namespace: `/sns`

```javascript
// Emitted by server
socket.on('post:created', { post_id, user_id, platform, created_at })
socket.on('post:published', { post_id, platform, published_at, reach })
socket.on('post:scheduled', { post_id, scheduled_time, platforms })

socket.on('engagement:liked', { post_id, liker_id, total_likes })
socket.on('engagement:commented', { post_id, commenter_id, comment_text })
socket.on('engagement:shared', { post_id, sharer_id })

socket.on('comment:replied', { original_comment_id, reply_id, reply_text })
socket.on('comment:liked', { comment_id, total_likes })

socket.on('analytics:updated', { post_id, metrics: { likes, comments, shares, reach, impressions } })
socket.on('post:scheduled', { automation_id, next_post_details })
socket.on('trending:updated', { platform, trending_topics: [], trending_hashtags: [] })
```

### Orders Namespace: `/orders`

```javascript
socket.on('order:created', { order_id, customer_id, total_krw, items_count })
socket.on('order:updated', { order_id, status: 'pending|processing|shipped|delivered' })
socket.on('order:shipped', { order_id, tracking_number, estimated_delivery })

socket.on('invoice:generated', { invoice_id, order_id, pdf_url })
socket.on('invoice:sent', { invoice_id, recipient_email })

socket.on('payment:received', { payment_id, invoice_id, amount_krw })
socket.on('subscription:renewed', { subscription_id, next_billing_date })
socket.on('refund:initiated', { order_id, amount_krw })
```

### Chat Namespace: `/chat`

```javascript
socket.on('message:new', { message_id, sender_id, content, timestamp })
socket.on('message:edited', { message_id, new_content, edited_at })
socket.on('message:deleted', { message_id, deleted_at })

socket.on('typing:indicator', { user_id, is_typing: boolean })
socket.on('thread:created', { thread_id, first_message_id })
socket.on('thread:updated', { thread_id, message_count })
```

### Notifications Namespace: `/notifications`

```javascript
socket.on('push:received', { notification_id, title, body, action_url })
socket.on('status:updated', { resource_type, resource_id, status })
socket.on('alert:triggered', { alert_id, severity: 'info|warning|critical', message })
socket.on('email:sent', { email_id, recipient, subject, sent_at })
```

---

## ADMIN & MONITORING

### Users (10 endpoints)

```
GET    /api/admin/users                  List all users (admin only)
  Query: ?role=&status=active&sort=-created_at&limit=50
  Response: { total, users: [{ user_id, email, name, role, status, created_at, last_login }] }

GET    /api/admin/users/<id>             User details
PUT    /api/admin/users/<id>             Update user (name, email, status)
DELETE /api/admin/users/<id>             Deactivate user
PUT    /api/admin/users/<id>/role        Change user role
  Body: { role_id|role_name }

POST   /api/admin/users/<id>/impersonate → Login as user (for support)
GET    /api/admin/users/<id>/activities  → User activity log
GET    /api/admin/users/<id>/subscriptions → User's subscriptions
```

### Subscriptions (8 endpoints)

```
GET    /api/admin/subscriptions          All subscriptions (paginated)
  Query: ?status=active|canceled&sort=-created_at&limit=100
  Response: { total, subscriptions: [{ subscription_id, user_id, plan_name, status, amount_krw, next_billing_date }] }

GET    /api/admin/subscriptions/stats    Subscription metrics
  Response: { active_count, canceled_count, mrr_krw, churn_rate, plan_mix }

GET    /api/admin/subscriptions/<id>     Subscription details
PUT    /api/admin/subscriptions/<id>     Modify subscription (plan, pause, etc.)
DELETE /api/admin/subscriptions/<id>     Force cancel (with refund reason)

POST   /api/admin/subscriptions/<id>/refund → Issue refund
GET    /api/admin/subscriptions/churn-analysis → Predict churn
```

### Metrics & Analytics (10 endpoints)

```
GET    /api/admin/metrics/revenue        Revenue KPIs (MRR, ARR, ARPU)
  Response: { total_mrr_krw, total_arr_krw, avg_revenue_per_user, growth_rate_pct }

GET    /api/admin/metrics/users          User metrics
  Response: { total_users, new_users_7d, active_users, churn_rate, retention_rate }

GET    /api/admin/metrics/engagement     Engagement metrics
  Response: { total_posts, avg_engagement_rate, trending_content, user_activity }

GET    /api/admin/metrics/health         System health
  Response: { api_uptime_pct, error_rate, avg_response_time_ms, database_health, redis_health }

GET    /api/admin/metrics/reviews        Review program metrics
GET    /api/admin/metrics/sns            SNS analytics (per platform)
GET    /api/admin/analytics/cohort       Cohort analysis
GET    /api/admin/analytics/funnel       Conversion funnel
GET    /api/admin/analytics/retention    Retention curves
GET    /api/admin/analytics/ltv          Lifetime value calculation
```

### Audit & Compliance (8 endpoints)

```
GET    /api/admin/audit-logs             Action history (GDPR/compliance)
  Query: ?resource_type=&action=&user_id=&date_from=&date_to=
  Response: { total, logs: [{ user_id, action, resource, resource_id, timestamp, ip_address }] }

GET    /api/admin/audit-logs/export      Download logs (CSV/JSON)
GET    /api/admin/audit-logs/<id>        Single log entry details

POST   /api/admin/gdpr/data-export       Export user data (for user)
POST   /api/admin/gdpr/data-delete       Schedule account deletion

GET    /api/admin/compliance/report      Compliance report
GET    /api/admin/security/report        Security audit report
```

### Content Moderation (6 endpoints)

```
GET    /api/admin/flagged-content        Reported posts/comments
  Query: ?status=pending|approved|rejected&priority=high
  Response: { total, items: [{ report_id, content_id, reason, reported_by, created_at }] }

GET    /api/admin/flagged-content/<id>   Report details
PUT    /api/admin/flagged-content/<id>   Approve/reject
  Body: { action: 'approve|reject', reason_for_rejection }

POST   /api/admin/flagged-content/<id>/remove → Remove content
POST   /api/admin/users/<uid>/ban        Ban user
```

---

## SEARCH & DISCOVERY

### Full-Text Search (6 endpoints)

```
POST   /api/search/full-text             Full-text search across content
  Body: { q: 'search query', platform: 'instagram|twitter', category: '', limit: 20 }
  Response: { total, results: [{ id, type, title, excerpt, relevance_score, published_at }] }

GET    /api/search/autocomplete          Search suggestions
  Query: ?q=&platform=&limit=10
  Response: { suggestions: [{ text, count, type: 'post|user|tag' }] }

GET    /api/search/facets                Faceted navigation
  Response: { categories: [...], platforms: [...], date_ranges: [...], users: [...] }

POST   /api/search/saved                 Save search query
  Body: { query_text, name, is_public }
  Response: { saved_search_id, created_at }

GET    /api/search/saved                 List saved searches
GET    /api/search/trending              Trending search queries
  Query: ?language=ko&platform=instagram&days=7
  Response: { queries: [{ text, volume, growth_rate }] }
```

---

## i18n & LOCALIZATION

### Translations (6 endpoints)

```
GET    /api/i18n/languages               Supported languages
  Response: { languages: [{ code: 'ko', name: 'Korean', native_name: '한국어', flag_emoji: '🇰🇷' }] }

GET    /api/i18n/strings/<lang>          All strings for language
  Query: ?module=&limit=1000
  Response: { total, strings: [{ key, value, last_updated }] }

GET    /api/i18n/strings/<lang>/<key>    Single translation
  Response: { key, value, language, last_updated_by }

POST   /api/i18n/strings                 Add/update translation (admin)
  Body: { language, translations: { key: 'value', ... } }
  Response: { updated_count, errors: [] }

GET    /api/i18n/coverage                Translation coverage report
  Response: { languages: { ko: 100%, en: 95%, ja: 80%, zh: 70% }, missing_keys: [] }

GET    /api/i18n/download/<lang>         Download language pack
```

---

## RBAC & PERMISSIONS

### Role Management (6 endpoints)

```
GET    /api/rbac/roles                   List all roles
  Response: { roles: [{ role_id, name, description, permission_count, user_count }] }

POST   /api/rbac/roles                   Create custom role
  Body: { name, description, permissions: ['SNS_READ', 'SNS_WRITE', ...] }
  Response: { role_id, created_at }

GET    /api/rbac/roles/<id>              Role details (with permissions)
PUT    /api/rbac/roles/<id>              Update role
DELETE /api/rbac/roles/<id>              Delete role (if no users assigned)
GET    /api/rbac/permissions             List all available permissions
```

### User Role Assignment (6 endpoints)

```
GET    /api/rbac/users/<id>/roles        User's roles
  Response: { roles: [{ role_id, role_name, assigned_at, assigned_by }] }

POST   /api/rbac/users/<id>/roles        Assign role to user
  Body: { role_id|role_name, expires_at?: date }
  Response: { user_id, roles: [...], updated_at }

DELETE /api/rbac/users/<id>/roles/<rid>  Remove role from user
GET    /api/rbac/users/<id>/permissions  Effective permissions (all roles merged)
POST   /api/rbac/users/<id>/permissions  Override specific permission
```

### Audit & Compliance (4 endpoints)

```
GET    /api/rbac/audit                   Access audit logs
  Query: ?action=&user_id=&date_from=&date_to=
  Response: { logs: [{ user_id, action, resource, ip_address, timestamp }] }

GET    /api/rbac/audit/<id>              Single audit entry
POST   /api/rbac/audit/export            Export audit logs

GET    /api/rbac/access-report           Who has access to what
  Response: { users: [{ user_id, email, roles, effective_permissions, access_level }] }
```

---

## HTTP STATUS CODES REFERENCE

| Code | Meaning | Usage |
|------|---------|-------|
| **200** | OK | Successful GET, PUT, DELETE |
| **201** | Created | Successful POST (new resource created) |
| **204** | No Content | Successful DELETE (no response body) |
| **400** | Bad Request | Invalid input, validation error |
| **401** | Unauthorized | Missing/invalid JWT token |
| **403** | Forbidden | User lacks required permissions |
| **404** | Not Found | Resource not found |
| **409** | Conflict | Resource already exists (e.g., duplicate email) |
| **422** | Unprocessable Entity | Validation error with details |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server error (check logs) |
| **503** | Service Unavailable | Service temporarily down |

---

## AUTHENTICATION HEADER

All endpoints (except `/api/auth/register`, `/api/auth/login`, `/api/payment/webhook`) require:

```
Authorization: Bearer <JWT_TOKEN>

Example:
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8000/api/auth/user
```

---

## PAGINATION STANDARD

List endpoints support pagination via query parameters:

```
GET /api/path?limit=20&offset=0&sort=-created_at

limit:  Items per page (default: 20, max: 100)
offset: Starting position (default: 0)
sort:   Sort field (prefix with - for descending, default: -created_at)

Response format:
{
  "total": 1500,
  "limit": 20,
  "offset": 0,
  "items": [...]
}
```

---

## RATE LIMITING

Default limits (adjustable via admin panel):

```
Standard User:   60 requests/minute, 1000 requests/hour
Premium User:    300 requests/minute, 10000 requests/hour
Admin:           No limit

Response headers:
X-RateLimit-Limit:       60
X-RateLimit-Remaining:   45
X-RateLimit-Reset:       1645900000
```

---

**Total Endpoints Documented:** 100+
**Last Updated:** 2026-02-26
**Version:** 1.0
