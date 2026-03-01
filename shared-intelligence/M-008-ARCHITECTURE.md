# M-008 Architecture & Data Flow
> **Detailed system design** | Reference for implementation

---

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SoftFactory Platform                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Web UI (75 HTML pages)                 │   │
│  │  - SoftFactory Platform                                 │   │
│  │  - SNS Auto (M-006)                                     │   │
│  │  - CooCook (M-002) ← NEW                                │   │
│  │  - Review Platform                                      │   │
│  │  - AI Automation                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓ API calls                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Flask API Server (app.py)                  │   │
│  │                                                          │   │
│  │  ┌──────────────────┐  ┌──────────────────┐            │   │
│  │  │  SNS Auto        │  │  CooCook         │            │   │
│  │  │  Services        │  │  Services (NEW)  │            │   │
│  │  │  - Platforms     │  │  - Recipes       │            │   │
│  │  │  - Scheduling    │  │  - Nutrition     │            │   │
│  │  │  - Analytics     │  │  - Shopping      │            │   │
│  │  │  - Telegram      │  │  - Feed          │            │   │
│  │  └──────────────────┘  └──────────────────┘            │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓ Database calls                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │    SQLAlchemy ORM Layer (models.py)                      │   │
│  │                                                          │   │
│  │  Users, Subscriptions, SNS*, Chef, Booking, Recipe*    │   │
│  │  ShoppingList, RecipeShare, UserFavorite, etc.         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓ SQL                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SQLite / PostgreSQL                         │   │
│  │  (Dev: sqlite:///D:/Project/platform.db)               │   │
│  │  (Prod: PostgreSQL connection)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Background Jobs (APScheduler)                  │   │
│  │  - publish_scheduled_posts() — every 60s                │   │
│  │  - notify_pending_jobs() — every 30m (NEW)              │   │
│  │  - scrape_review_listings() — every 4h                  │   │
│  │  - check_auto_apply_rules() — every 30m                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓ Telegram                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        Caching Layer (Redis)                             │   │
│  │  - Recipe search results (15-min TTL)                    │   │
│  │  - User feed (5-min TTL)                                │   │
│  │  - Analytics (1-hour TTL)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Telegram Bot Integration                         │   │
│  │  - daemon/telegram_notifier.py                           │   │
│  │  - bot token: 8461725251                                │   │
│  │  - allowed user: 7910169750                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## PART A: Telegram Notification Flow

### Sequence Diagram: SNS Post Publishing → Telegram Alert

```
User                Web UI              API Server         SQLite        Telegram
│                     │                    │                 │               │
├─ Schedule SNS Post ─→│                    │                 │               │
│                     ├─ POST /api/sns/posts ──→              │               │
│                     │                    │                 │               │
│                     │                    ├─ Save post (status='scheduled')  │
│                     │                    └──→ INSERT into SNSPost          │
│                     │                    │                 │               │
│                     │              [60-second wait]         │               │
│                     │                    │                 │               │
│                     │              APScheduler             │               │
│                     │           publish_scheduled_posts()   │               │
│                     │                    │                 │               │
│                     │                    ├─ SELECT posts WHERE             │
│                     │                    │   status='scheduled' AND         │
│                     │                    │   scheduled_at <= now            │
│                     │                    │←─────────────────┤               │
│                     │                    │ [Found 1 post]  │               │
│                     │                    │                 │               │
│                     │    SNS Platform (simulation)          │               │
│                     │                    │                 │               │
│                     │              [Instagram API call]     │               │
│                     │                    │                 │               │
│                     │     [SUCCESS: returns external_post_id]│            │
│                     │                    │                 │               │
│                     │           Update post status          │               │
│                     │                    │                 │               │
│                     │                    ├─ UPDATE SNSPost SET            │
│                     │                    │   status='published',            │
│                     │                    │   published_at=now               │
│                     │                    │─────────────────→│               │
│                     │                    │                 ├─ Commit       │
│                     │                    │                 │               │
│                     │         SNSNotificationService        │               │
│                     │         notify_job_published()        │               │
│                     │                    │                 │               │
│                     │           ┌─ Lookup SNSSettings       │               │
│                     │           │  (telegram_chat_id=7910169750)           │
│                     │           │  (telegram_enabled=True)  │               │
│                     │           └─ Format message:          │               │
│                     │              "<b>SNS Post Published</b>│               │
│                     │               Platform: Instagram       │               │
│                     │               Content: 'Delicious food...'│           │
│                     │               Likes: 12 👍"             │               │
│                     │                    │                 │               │
│                     │           TelegramBot.send_message() │               │
│                     │           (chat_id='7910169750',      │               │
│                     │            message=<HTML formatted>)  │               │
│                     │                    │                 │               │
│                     │────────────────────────────────────────────→ @piwpiwtelegrambot │
│                     │                    │                 │               │
│                     │←─────────────────────────────────────────── OK (message_id=123) │
│                     │                    │                 │               │
└─ [Telegram popup alert on user's phone]──┘                 │               │
```

### Data Model: SNSSettings (Extended)

```python
SNSSettings {
    id: int                        # Primary key
    user_id: int (FK)              # Foreign key to User

    # Existing fields
    auto_optimal_time: bool        # Auto-post at optimal time
    engagement_notifications: bool # Notify on engagement
    auto_reply_enabled: bool       # Auto-reply to comments
    banned_keywords: JSON          # Keywords to avoid

    # NEW fields (M-008)
    telegram_chat_id: str          # User's Telegram ID (e.g., "7910169750")
    telegram_enabled: bool         # Toggle all Telegram notifications
    timezone: str                  # User's timezone (e.g., "Asia/Seoul")
    notification_on_pending: bool  # Notify when job pending (30 min before)
    notification_on_complete: bool # Notify when job published
    notification_on_error: bool    # Notify when job fails
}
```

### SNSNotificationService Class

```python
class SNSNotificationService:

    def __init__(self, app):
        self.app = app
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    # Event: Job scheduled
    def notify_job_scheduled(user_id: int, post_id: int, scheduled_at: datetime):
        # Lookup user timezone
        # Convert scheduled_at to user's TZ
        # Message: "📅 Scheduled: Instagram post will publish at 3:00 PM KST"
        # Send via Telegram

    # Event: Job published successfully
    def notify_job_published(user_id: int, post_id: int, platform: str, content: str, stats: dict):
        # Message format:
        # "✅ Instagram Post Published
        #  Your post got 12 👍 | 3 💬 | 1 ↗️"
        # Send via Telegram

    # Event: Job failed (with retry info)
    def notify_job_failed(user_id: int, post_id: int, error: str, retry_count: int):
        # Message format:
        # "❌ Failed to publish (Attempt 1/3)
        #  Error: 'Invalid media format'
        #  Retrying at: 3:05 PM KST"
        # Send via Telegram

    # Background job: Summarize pending jobs (30-min interval)
    def notify_pending_jobs(user_id: int, pending_count: int, next_run_time: datetime):
        # Message format:
        # "⏳ 5 posts waiting to publish
        #  Next run: 3:00 PM KST
        #  [View Pending] [Publish Now]"
        # Send via Telegram

    # Helper: Format times considering user timezone
    def _format_time_user_timezone(dt: datetime, user_timezone: str) -> str:
        # Input: datetime(2026-02-26, 15:00, UTC), timezone="Asia/Seoul"
        # Output: "3:00 PM KST" or "3:00 PM (Seoul time)"

    # Helper: Format message with HTML tags
    def _format_telegram_message(template: str, **kwargs) -> str:
        # Telegram supports HTML:
        # <b>bold</b>, <i>italic</i>, <code>code</code>, <a href="...">link</a>
```

### New Background Job: notify_pending_jobs()

```python
# Added to scheduler.py init_scheduler()

@scheduler.scheduled_job('interval', minutes=30)
def notify_pending_jobs(app: Flask):
    """
    Every 30 minutes: Check for pending SNS posts and notify users.
    Reduces notification spam while keeping users informed.
    """
    with app.app_context():
        from backend.models import db, SNSPost, SNSSettings, User
        from datetime import datetime, timedelta

        # Find all users with pending posts
        pending_posts = SNSPost.query.filter(
            SNSPost.status == 'scheduled',
            SNSPost.scheduled_at > datetime.utcnow(),
            SNSPost.scheduled_at <= datetime.utcnow() + timedelta(hours=1)
        ).all()

        # Group by user_id
        posts_by_user = {}
        for post in pending_posts:
            if post.user_id not in posts_by_user:
                posts_by_user[post.user_id] = []
            posts_by_user[post.user_id].append(post)

        # Notify each user
        for user_id, posts in posts_by_user.items():
            settings = SNSSettings.query.filter_by(user_id=user_id).first()

            if not settings or not settings.telegram_enabled or not settings.notification_on_pending:
                continue

            notification_service = SNSNotificationService(current_app)

            # Find next scheduled time
            next_run = min(post.scheduled_at for post in posts)

            notification_service.notify_pending_jobs(
                user_id=user_id,
                pending_count=len(posts),
                next_run_time=next_run
            )

        logger.info(f"[TELEGRAM] Pending job notifications sent to {len(posts_by_user)} users")
```

---

## PART B1: Recipe Search Architecture

### Data Model: Recipe System

```
Recipe
├─ id: int (PK)
├─ user_id: int (FK) [NULL = system recipe]
├─ title: str (indexed, full-text searchable)
├─ description: text (indexed)
├─ category: str (indexed) — appetizer|main|dessert|side|beverage
├─ cuisine_type: str (indexed) — korean|italian|asian|american
├─ difficulty: str (indexed) — easy|medium|hard
├─ prep_time_minutes: int
├─ cook_time_minutes: int (indexed)
├─ servings: int
├─ instructions: text
├─ ingredients_json: JSON []
├─ nutrition_per_serving: JSON {calories, protein, carbs, fat, fiber}
├─ allergens: JSON [] — detected allergens
├─ image_url: str
├─ video_url: str
├─ rating: float (indexed)
├─ rating_count: int
├─ reviews_count: int
├─ favorite_count: int
├─ is_published: bool (indexed)
├─ created_at: datetime (indexed)
└─ updated_at: datetime

RecipeIngredient
├─ id: int (PK)
├─ recipe_id: int (FK)
├─ name: str
├─ quantity: float
├─ unit: str — cup|tbsp|tsp|gram|ml|piece
├─ calories: float (per 100g)
├─ protein_g: float
├─ carbs_g: float
├─ fat_g: float
├─ fiber_g: float
└─ notes: str — optional|fresh|chopped

RecipeReview
├─ id: int (PK)
├─ recipe_id: int (FK)
├─ user_id: int (FK)
├─ rating: int (1-5, indexed)
├─ title: str
├─ comment: text
├─ helpful_count: int
├─ image_url: str (user's photo)
└─ created_at: datetime
```

### Search API: Request/Response Flow

```
GET /api/coocook/recipes?keyword=pad%20thai&difficulty=medium&max_time=30&sort_by=rating

┌─ Flask Route Handler ──────────────────┐
│                                        │
│  1. Build cache key:                   │
│     "recipe_search:{query_string}"     │
│                                        │
│  2. Check Redis cache                  │
│     ├─ HIT: Return cached results      │
│     └─ MISS: Continue to DB            │
│                                        │
│  3. Build SQL query:                   │
│     SELECT * FROM recipes              │
│     WHERE is_published=true             │
│     AND (title LIKE '%pad thai%' OR     │
│          description LIKE '%pad thai%') │
│     AND difficulty='medium'             │
│     AND cook_time_minutes <= 30         │
│     ORDER BY rating DESC                │
│     LIMIT 20 OFFSET 0                   │
│                                        │
│  4. Execute query (< 100ms with index) │
│                                        │
│  5. Format response JSON                │
│                                        │
│  6. Cache result (15-min TTL)          │
│     cache.setex(cache_key, 900, ...)   │
│                                        │
│  7. Return to client                   │
│                                        │
└────────────────────────────────────────┘

Response (HTTP 200):
{
  "recipes": [
    {
      "id": 1,
      "title": "Pad Thai",
      "category": "main",
      "difficulty": "medium",
      "cook_time": 25,
      "rating": 4.8,
      "reviews_count": 145,
      "image_url": "https://..."
    },
    ...
  ],
  "total": 342,
  "pages": 18,
  "current_page": 1
}
```

### Nutrition Calculator: Algorithm

```
Input:
  ingredients=[
    {name: "chicken breast", quantity: 500, unit: "gram"},
    {name: "rice (cooked)", quantity: 2, unit: "cup"},
    {name: "broccoli", quantity: 200, unit: "gram"}
  ]
  servings=4

Process:
  1. For each ingredient:
     a. Convert quantity to grams
        - "gram" → multiply by 1
        - "cup" → multiply by 240
        - "tbsp" → multiply by 15
        - "piece" → multiply by 100

     b. Lookup nutrition (per 100g)
        - chicken breast: {cal:165, pro:31, carbs:0, fat:3.6, fiber:0}
        - rice: {cal:130, pro:2.7, carbs:28, fat:0.3, fiber:0.4}
        - broccoli: {cal:34, pro:2.8, carbs:7, fat:0.4, fiber:2.4}

     c. Scale by ingredient quantity
        - chicken: 500g ÷ 100g × {165, 31, ...} = {825, 155, 0, 18, 0}
        - rice: 2×240g ÷ 100g × {130, 2.7, ...} = {624, 12.96, 134.4, 1.44, 1.92}
        - broccoli: 200g ÷ 100g × {34, 2.8, ...} = {68, 5.6, 14, 0.8, 4.8}

  2. Sum total
     Total = {1517, 173.56, 148.4, 20.24, 6.72} (entire recipe)

  3. Divide by servings
     Per-serving = {1517÷4, 173.56÷4, ...} = {379.25, 43.39, 37.1, 5.06, 1.68}

  4. Round to 1 decimal place
     Final = {379.3, 43.4, 37.1, 5.1, 1.7}

Output:
  {
    "calories": 379.3,
    "protein": 43.4,
    "carbs": 37.1,
    "fat": 5.1,
    "fiber": 1.7
  } per serving
```

### Cache Strategy

```
Cache Key:    "recipe_search:keyword=pad%20thai&difficulty=medium&..."
TTL:          15 minutes (900 seconds)
Storage:      Redis (key-value store)
Eviction:     LRU (Least Recently Used)

Benefits:
- First search (keyword="pad thai"): DB hit (100ms)
- Second identical search (within 15 min): Cache hit (5ms) ✓ 20x faster
- Search results stable for 15 minutes (acceptable staleness)

Invalidation:
- When new recipe added: Clear category cache
- When recipe rating updated: Clear recipe detail + feed cache
- Manual: Admin can clear all caches
```

---

## PART B2: Shopping List & Social Feed

### Shopping List: Data Model & Consolidation

```
ShoppingList
├─ id: int (PK)
├─ user_id: int (FK)
├─ title: str
├─ description: text
├─ items: JSON []
│  └─ {
│      name: "chicken breast",
│      quantity: 1000,
│      unit: "gram",
│      checked: false,
│      price_estimate: 8.99,
│      store: "Costco"
│    }
├─ shared_with: JSON [] — [user_id, user_id, ...]
├─ is_shareable: bool
├─ created_at: datetime
└─ updated_at: datetime

Consolidation Logic:
─────────────────────

Input: [
  {name: "chicken", quantity: 500, unit: "gram"},
  {name: "Chicken", quantity: 200, unit: "gram"},  ← DUPLICATE (case-insensitive)
  {name: "broccoli", quantity: 1, unit: "cup"}
]

Process:
  1. Group by name (case-insensitive)
     "chicken" → [500g, 200g]
     "broccoli" → [1 cup]

  2. Sum quantities (if same unit)
     "chicken": 500 + 200 = 700g
     "broccoli": 1 cup

  3. Remove duplicates
     Result: [
       {name: "chicken", quantity: 700, unit: "gram"},
       {name: "broccoli", quantity: 1, unit: "cup"}
     ]

Benefits:
- Users don't see duplicates when adding multiple recipes
- Grocery shopping becomes efficient (1 chicken purchase, not 3)
```

### Export Workflow: PDF Generation

```
GET /api/coocook/shopping-lists/1/export?format=pdf

┌─ Flask Route Handler ──────────────────┐
│                                        │
│  1. Lookup shopping list               │
│  2. Validate ownership (user_id match) │
│  3. Create PDF buffer (in-memory)      │
│  4. Add header: "Shopping List: ..."   │
│  5. Add items (with checkboxes)        │
│     • [ ] Chicken - 700g               │
│     • [ ] Broccoli - 1 cup             │
│     • [ ] Oil - 2 tbsp                 │
│     ...                                │
│  6. Add footer (date, store, total $)  │
│  7. Return PDF as attachment           │
│     Headers:                           │
│       Content-Type: application/pdf    │
│       Content-Disposition:             │
│         attachment; filename="list.pdf"│
│                                        │
└────────────────────────────────────────┘

Result: User downloads shopping-list.pdf → can print or share
```

### Social Feed: Following + Sharing Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    Social Network Model                        │
│                                                                │
│  User A                          User B                        │
│  ├─ Following: [B, C, D]        ├─ Following: [A, E]         │
│  └─ Followers: [B, E]           └─ Followers: [A, D]         │
│                                                                │
│                    RecipeShare Records                         │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  RecipeShare(id=1):                                            │
│  ├─ recipe_id: 5                                              │
│  ├─ user_id: B                                                │
│  ├─ visibility: "public"        ✅ Visible to all followers    │
│  ├─ caption: "Amazing carbonara!"                             │
│  └─ likes: 12                                                 │
│                                                                │
│  RecipeShare(id=2):                                            │
│  ├─ recipe_id: 10                                             │
│  ├─ user_id: C                                                │
│  ├─ visibility: "group"         ← Only shared_with sees       │
│  ├─ shared_with: [A, D, E]                                    │
│  ├─ caption: "Family Sunday dinner"                           │
│  └─ likes: 3                                                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Feed Generation (For User A):

GET /api/coocook/feed?page=1&per_page=20

  ├─ Find users A is following: [B, C, D]
  ├─ Get their public/group shares (past week):
  │  ├─ B's shares (visibility=public): 2 items
  │  ├─ C's shares (in shared_with=[A,...]): 1 item
  │  └─ D's shares: 0 items
  ├─ Get trending recipes (any user, high rating): 5 items
  ├─ Merge & sort by recency
  ├─ Return 20-item feed with metadata (likes, comments)
  └─ Cache for 5 minutes
```

### Data Models: Social Relationships

```
UserFollowing:
  follower_id → User A
  following_id → User B
  created_at: datetime

  [One-to-many: User can follow many users]

UserFavorite:
  user_id → User A
  recipe_id → Recipe 5
  created_at: datetime

  [Track favorite recipes for personalization]

RecipeShare:
  recipe_id → Recipe 5
  user_id → User B (who shared)
  visibility: "public|private|group"
  shared_with: [user_id, user_id, ...] (if group)
  caption: "User's reason for sharing"
  likes: 12
  created_at: datetime

  [Public sharing with social features]
```

---

## Database Schema: Complete View

```sql
-- Existing tables (unchanged)
users (id, email, name, password_hash, ...)
subscriptions (id, user_id, service, ...)
sns_accounts (id, user_id, platform, ...)
sns_posts (id, user_id, account_id, content, scheduled_at, ...)
chefs (id, user_id, name, cuisine_type, ...)
bookings (id, user_id, chef_id, booking_date, ...)

-- NEW tables (M-008)

-- Telegram integration
ALTER TABLE sns_settings ADD COLUMN (
  telegram_chat_id VARCHAR(100),
  telegram_enabled BOOLEAN DEFAULT FALSE,
  timezone VARCHAR(50) DEFAULT 'UTC',
  notification_on_pending BOOLEAN DEFAULT TRUE,
  notification_on_complete BOOLEAN DEFAULT TRUE,
  notification_on_error BOOLEAN DEFAULT TRUE
);

-- CooCook recipes
CREATE TABLE recipes (
  id INT PRIMARY KEY,
  user_id INT (NULL = system recipe),
  title VARCHAR(200) NOT NULL,
  description TEXT,
  category VARCHAR(50),
  cuisine_type VARCHAR(50),
  difficulty VARCHAR(20) DEFAULT 'medium',
  prep_time_minutes INT,
  cook_time_minutes INT,
  servings INT DEFAULT 4,
  instructions TEXT,
  ingredients_json JSON,
  nutrition_per_serving JSON,
  allergens JSON,
  image_url VARCHAR(500),
  rating FLOAT DEFAULT 0,
  rating_count INT DEFAULT 0,
  is_published BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT NOW(),
  KEY idx_title (title),
  KEY idx_category (category),
  KEY idx_rating (rating),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE recipe_ingredients (
  id INT PRIMARY KEY,
  recipe_id INT NOT NULL,
  name VARCHAR(120),
  quantity FLOAT,
  unit VARCHAR(20),
  calories FLOAT,
  protein_g FLOAT,
  carbs_g FLOAT,
  fat_g FLOAT,
  fiber_g FLOAT,
  notes VARCHAR(255),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

CREATE TABLE recipe_reviews (
  id INT PRIMARY KEY,
  recipe_id INT NOT NULL,
  user_id INT NOT NULL,
  rating INT,
  title VARCHAR(120),
  comment TEXT,
  helpful_count INT DEFAULT 0,
  created_at DATETIME DEFAULT NOW(),
  KEY idx_rating (rating),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Shopping lists
CREATE TABLE shopping_lists (
  id INT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(200),
  items JSON,
  shared_with JSON,
  created_at DATETIME DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Social features
CREATE TABLE user_favorites (
  id INT PRIMARY KEY,
  user_id INT NOT NULL,
  recipe_id INT NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  KEY idx_user_recipe (user_id, recipe_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

CREATE TABLE user_following (
  id INT PRIMARY KEY,
  follower_id INT NOT NULL,
  following_id INT NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  KEY idx_following (follower_id, following_id),
  FOREIGN KEY (follower_id) REFERENCES users(id),
  FOREIGN KEY (following_id) REFERENCES users(id)
);

CREATE TABLE recipe_shares (
  id INT PRIMARY KEY,
  recipe_id INT NOT NULL,
  user_id INT NOT NULL,
  visibility VARCHAR(20) DEFAULT 'private',
  shared_with JSON,
  caption TEXT,
  likes INT DEFAULT 0,
  comments_count INT DEFAULT 0,
  created_at DATETIME DEFAULT NOW(),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Caching & Performance Strategy

```
Component          Cache Layer    TTL      Hit Rate   Optimization
─────────────────────────────────────────────────────────────────
Recipe search      Redis          15 min   High ✓     Full-text index
Feed generation    Redis          5 min    Medium     Pagination
Nutrition calc     Memory         ∞        N/A        In-process
Trending recipes   Redis          1 hour   Medium     Batch update
User favorites     DB (indexed)   ∞        N/A        Query index
Ingredient lookup  Memory         ∞        N/A        Loaded at startup
```

---

## Error Handling & Validation

### Input Validation

```python
# Recipe creation
Recipe.title:       required, 1-200 chars ✓
Recipe.difficulty: enum(easy|medium|hard) ✓
Recipe.servings:   int, 1-10 ✓
Recipe.ingredients: JSON array, max 50 items ✓

RecipeIngredient.quantity: float, > 0 ✓
RecipeIngredient.unit:     enum(cup|tbsp|tsp|gram|ml|piece) ✓

RecipeReview.rating: int, 1-5 ✓
RecipeReview.comment: max 1000 chars ✓

ShoppingList.title: required, 1-200 chars ✓
ShoppingList.items: JSON, max 200 items ✓
```

### Error Responses

```
HTTP 400 Bad Request:
  {"error": "Missing required field: title"}

HTTP 404 Not Found:
  {"error": "Recipe not found"}

HTTP 403 Forbidden:
  {"error": "Not authorized to access this shopping list"}

HTTP 500 Server Error:
  {"error": "Failed to calculate nutrition. Please try again."}
```

---

## Monitoring & Logging

```python
# SNS Notifications
[TELEGRAM] To chat 7910169750: "✅ Instagram Post Published..."
[TELEGRAM-QUEUE] Enqueued message_id=123 (priority=high)
[TELEGRAM-DELIVERY] Message delivered (attempt=1, latency=250ms)

# Recipe Service
[RECIPE-SEARCH] Query: keyword='pad thai', difficulty='medium'
[RECIPE-SEARCH-CACHE-HIT] Returned 342 results from cache (TTL=815s)
[RECIPE-NUTRITION] Calculated 379.3 cal/serving in 45ms

# Shopping List
[SHOPPING-CONSOLIDATION] Merged 2 duplicate items (chicken)
[SHOPPING-EXPORT] Generated PDF (5 items, 2.3 KB, 180ms)

# Feed
[FEED-GENERATION] User #1234: 8 following users, 12 recipe shares, 5 trending
[FEED-GENERATION-CACHE-HIT] Returned 20-item feed from cache
```

---

**This architecture supports:**
- ✅ Real-time Telegram notifications for SNS publishing
- ✅ Fast recipe search with filtering & caching
- ✅ Accurate nutrition calculations
- ✅ Efficient shopping list management
- ✅ Social features (following, sharing, trending)
- ✅ Production-grade error handling & monitoring

