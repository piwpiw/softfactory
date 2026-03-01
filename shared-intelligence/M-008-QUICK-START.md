# 📘 M-008 Quick Start Guide

> **Purpose**: **PART A** (1 hour): Integrate Telegram notifications for SNS publishing jobs
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 M-008 Quick Start Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Telegram Bot Scheduler + CooCook API Enhancement** | Start here

---

## The Ask (Summary)

**PART A** (1 hour): Integrate Telegram notifications for SNS publishing jobs
**PART B** (3 hours): Build recipe management, nutrition calculator, shopping lists, social feed for CooCook

---

## PART A: Telegram Notifications (1 Hour)

### What's Currently Missing
```
User creates SNS post → schedules for 3pm → posts publishes → USER DOESN'T KNOW ❌
```

### What We're Building
```
User creates SNS post → schedules for 3pm → posts publishes → Telegram alert ✅
"Your post to Instagram was published! 👍 12 likes"
```

### 3-Step Implementation

**Step 1: Extend Database**
```python
# backend/models.py:484 — SNSSettings class
# ADD 4 new fields:
- telegram_chat_id: str (user's Telegram ID)
- telegram_enabled: bool (toggle notifications)
- timezone: str (user's timezone for formatting times)
- notification_on_complete/error/pending: bool (granular control)
```

**Step 2: Create Notification Service**
```python
# NEW: backend/services/sns_notification.py
class SNSNotificationService:
    def notify_job_published(user_id, post_id, platform, content, stats)
    def notify_job_failed(user_id, post_id, error, retry_count)
    def notify_pending_jobs(user_id, pending_count, next_run)
```

**Step 3: Update Scheduler**
```python
# backend/scheduler.py:113
# Replace stub send_telegram_notification()
# Add 30-min background job: notify_pending_jobs()
```

**Quick Win:** Test Telegram connection
```
POST /api/sns-settings/telegram/test
→ Telegram pops a message
```

---

## PART B: CooCook Enhancement (3 Hours)

### What's Currently Missing
```
Only: List chefs + book them
Missing: Recipes, nutrition, shopping lists, social feed
```

### What We're Building

#### Phase 1: Recipes (1.5 hours)
```
GET /api/coocook/recipes?
    keyword=pad thai&
    difficulty=medium&
    max_time=30&
    cuisine=asian&
    sort_by=rating

Response:
[
  {
    "title": "Pad Thai",
    "difficulty": "medium",
    "cook_time": 25,
    "rating": 4.8,
    "image_url": "..."
  }
]
```

**Models to Create:**
- `Recipe` — title, ingredients (JSON), instructions, nutrition, difficulty, time
- `RecipeIngredient` — name, quantity, unit, calories, protein, carbs, fat
- `RecipeReview` — user ratings + comments

**Service:**
```python
NutritionCalculator.calculate_recipe_nutrition(ingredients, servings=4)
→ {'calories': 450, 'protein': 45, 'carbs': 30, 'fat': 12, 'fiber': 5}
```

#### Phase 2: Shopping Lists + Social (1.5 hours)
```
# Shopping List
POST /api/coocook/shopping-lists
POST /api/coocook/shopping-lists/1/add-recipe?recipe_id=5
→ Auto-consolidates: merge 2x "chicken" → "chicken × 2"

GET /api/coocook/shopping-lists/1/export?format=pdf
→ Pretty PDF for printing

# Social Feed
POST /api/coocook/recipes/5/share?visibility=public&caption="Love this!"
GET /api/coocook/feed → See friends' recipe shares
POST /api/coocook/users/123/follow → Follow friend's recipes
```

**Models:**
- `ShoppingList` — items (JSON array), consolidation logic
- `UserFavorite` — favorite recipes
- `RecipeShare` — recipe sharing with privacy controls
- `UserFollowing` — follow users

---

## File Structure (Before & After)

### Current
```
backend/models.py           — 12 models (User, Chef, Booking, SNS*, Review*)
backend/services/coocook.py — 50 lines (chef listing + booking only)
```

### After
```
backend/models.py
├─ NEW: Recipe, RecipeIngredient, RecipeReview
├─ NEW: ShoppingList, UserFavorite, RecipeShare, UserFollowing
└─ EXTEND: SNSSettings (+4 columns)

backend/services/coocook.py      — 400+ lines (recipes, shopping, feed)
backend/services/sns_notification.py — 150 lines (NEW — Telegram service)
backend/services/nutrition_calculator.py — 100 lines (NEW — Nutrition engine)

tests/integration/
├─ test_sns_notifications.py — Telegram tests
└─ test_coocook_recipes.py — Recipe/shopping/feed tests
```

---

## Implementation Checklist

### PART A
- [ ] Add 4 columns to SNSSettings (telegram_chat_id, etc.)
- [ ] Create SNSNotificationService class
- [ ] Update scheduler.py's send_telegram_notification()
- [ ] Create API endpoints for Telegram settings + test
- [ ] Add 30-min job for pending notifications
- [ ] Write tests (5+)
- [ ] Verify Telegram messages arrive

### PART B1: Recipes
- [ ] Create Recipe model (12 fields)
- [ ] Create RecipeIngredient model (8 fields)
- [ ] Create RecipeReview model (6 fields)
- [ ] Implement NutritionCalculator class (accuracy 95%+)
- [ ] Build search API with filters + caching
- [ ] Write tests (5+)

### PART B2: Shopping & Feed
- [ ] Create ShoppingList model + consolidation logic
- [ ] Implement shopping list CRUD + export (PDF/CSV)
- [ ] Create UserFavorite, RecipeShare, UserFollowing models
- [ ] Build feed API (following + trending)
- [ ] Implement share + follow + favorite APIs
- [ ] Write tests (5+)

---

## API Reference (New Endpoints)

### Telegram Settings
```
GET    /api/sns-settings/telegram
POST   /api/sns-settings/telegram
POST   /api/sns-settings/telegram/test
```

### Recipes
```
GET    /api/coocook/recipes?keyword=...&difficulty=...&sort_by=...
GET    /api/coocook/recipes/{id}
POST   /api/coocook/recipes/{id}/reviews
GET    /api/coocook/recipes/trending
```

### Shopping Lists
```
GET    /api/coocook/shopping-lists
POST   /api/coocook/shopping-lists
POST   /api/coocook/shopping-lists/{id}/add-recipe
DELETE /api/coocook/shopping-lists/{id}
GET    /api/coocook/shopping-lists/{id}/export?format=pdf|csv
```

### Social
```
POST   /api/coocook/recipes/{id}/share
POST   /api/coocook/recipes/{id}/favorite
POST   /api/coocook/users/{id}/follow
GET    /api/coocook/feed
GET    /api/coocook/favorites
```

---

## Key Patterns

### 1. Decorators (Auth)
```python
@require_auth  # Check JWT token
def my_route():
    user_id = g.user_id  # From g context
```

### 2. Database Relationships
```python
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredients = db.relationship('RecipeIngredient', lazy=True)
    # Then: recipe.ingredients returns list of objects
```

### 3. JSON Storage (Flexible)
```python
ingredients_json = db.Column(db.JSON, default=[])
# Can store complex structures without creating 10 tables
# Just validate structure on insert
```

### 4. Caching
```python
cache = redis.Redis(host='localhost', port=6379)
cache.setex('key', 900, value)  # 15-minute TTL
```

### 5. Error Handling
```python
return jsonify({'error': 'Chef not found'}), 404
return jsonify({'message': 'Booking created', 'id': booking.id}), 201
```

---

## Testing Approach

### Unit Tests (Fast, No DB)
```python
def test_nutrition_calculation():
    result = NutritionCalculator.calculate_recipe_nutrition(
        ingredients=[...],
        servings=4
    )
    assert result['calories'] == 450
    assert result['protein'] == 45
```

### Integration Tests (Slow, Real DB)
```python
def test_recipe_search_with_cache(client):
    # Create test recipe
    # First search hits DB
    # Second search hits cache
    # Verify cache works
```

---

## Performance Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| Recipe search | < 1s | Redis caching (15-min TTL) |
| Feed loading | < 500ms | Indexed queries, pagination |
| Nutrition calc | < 100ms | In-memory calculations |
| Shopping export | < 2s | Streaming, no large loads |

---

## Token Budget

```
PART A: 12K (Telegram notifications)
PART B1: 13K (Recipes + nutrition)
PART B2: 12K (Shopping + feed)
TOTAL: 37K / 200K (18.5%)
REMAINING: 163K
```

---

## Risks to Watch

1. **Telegram API rate limits** → Implement queue + retry
2. **Nutrition DB incomplete** → Start with 50 common ingredients, expand
3. **Model migration** → Test in dev, use Flask-Migrate
4. **Performance** → Profile early (caching layer is critical)

---

## Success Criteria

- All new endpoints working + tested
- No breaking changes to existing code
- All tests passing (30+ test cases)
- Performance targets met (search < 1s, feed < 500ms)
- Telegram notifications arriving correctly
- Shopping list consolidation working (merge duplicates)

---

## Get Started

1. Read full plan: `/shared-intelligence/M-008-TELEGRAM-COOCOOK-IMPLEMENTATION-PLAN.md`
2. Start Task #22: Telegram Bot Scheduler Integration
3. Follow checklist above
4. Update cost-log as you complete tasks
5. Commit after each major feature

**Estimated Time:** 4 hours total
**Expected Tokens:** 37K (18.5% of budget)

---

**Questions?** Check the full implementation plan for detailed code examples, architecture diagrams, and testing strategies.