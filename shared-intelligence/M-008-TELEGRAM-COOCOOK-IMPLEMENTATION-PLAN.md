# M-008: Telegram Bot Scheduler + CooCook API Enhancement Plan
> **Date:** 2026-02-26 | **Status:** PLANNING | **Token Budget:** 50-65K / 200K
> **Target Completion:** 4 hours | **Success Metric:** All tasks complete + tests passing

---

## Executive Summary

Two independent features to enhance SoftFactory platform:

1. **PART A: Telegram Bot Scheduler Integration** (1 hour) — Notify users of SNS publishing jobs via Telegram
2. **PART B: CooCook API Enhancement** (3 hours) — Build recipe search, nutrition calculator, shopping lists, and social feed

---

## PART A: Telegram Bot Scheduler Integration

### Current State
- **File:** `backend/scheduler.py:167` (TODO marker exists)
- **Current Logic:** SNS posts publish every 60 seconds; Telegram notification stub only logs
- **Problem:** Users don't know when jobs are scheduled or completed
- **Existing:** Sonolbot daemon running (piwpiwtelegrambot, allowed user: 7910169750)

### Architecture

```
User (SoftFactory UI)
  ↓
SNSPost scheduled for publish
  ↓
SNSScheduler (60s interval)
  ↓
[IF publish success]
  → SNSNotificationService
    → send_telegram_notification(user_id, message)
      → SNSSettings.telegram_chat_id lookup
      → TelegramBot.send_message()
        → daemon/telegram_notifier.py (HTTP webhook)
          → Sonolbot (8461725251)
          → User's Telegram (7910169750)
```

### Implementation Tasks

#### Task A.1: Extend SNSSettings Model
**File:** `backend/models.py:484`

```python
class SNSSettings(db.Model):
    # ... existing fields ...

    # NEW (Telegram integration)
    telegram_chat_id = db.Column(db.String(100), nullable=True)  # User's Telegram chat ID
    telegram_enabled = db.Column(db.Boolean, default=False)      # Toggle Telegram notifications
    timezone = db.Column(db.String(50), default='UTC')           # For scheduling
    notification_on_pending = db.Column(db.Boolean, default=True)  # Notify when job pending
    notification_on_complete = db.Column(db.Boolean, default=True)  # Notify on completion
    notification_on_error = db.Column(db.Boolean, default=True)    # Notify on failure
```

**Migration:** Add 4 new columns to existing table
**Test:** Verify backward compatibility (existing records unaffected)

---

#### Task A.2: Implement SNSNotificationService
**New File:** `backend/services/sns_notification.py`

```python
from datetime import datetime
from pytz import timezone as pytz_timezone
import logging

logger = logging.getLogger('sns.notifications')

class SNSNotificationService:
    """Centralized notification handler for SNS events"""

    def __init__(self, app):
        self.app = app

    def notify_job_scheduled(self, user_id: int, post_id: int, scheduled_at: datetime):
        """Notify user of upcoming scheduled job"""
        # Lookup user + SNSSettings
        # Format message with scheduled time (timezone-aware)
        # Call send_telegram_notification()
        pass

    def notify_job_published(self, user_id: int, post_id: int, platform: str, content: str, stats: dict):
        """Notify user of successful publication"""
        # Include content preview, platform, basic stats
        # Message format: HTML (bold, code formatting)
        pass

    def notify_job_failed(self, user_id: int, post_id: int, error: str, retry_count: int):
        """Notify user of job failure + retry status"""
        # Include error message, retry count, next attempt time
        pass

    def notify_pending_jobs(self, user_id: int, pending_count: int, next_run_time: datetime):
        """Daily summary of pending jobs"""
        # Count pending jobs, next run time, CTA button
        pass

    def _format_telegram_message(self, template: str, **kwargs) -> str:
        """Format message with HTML tags for Telegram"""
        # Support: <b>bold</b>, <i>italic</i>, <code>code</code>, <a href="...">link</a>
        pass

    def _format_time_user_timezone(self, dt: datetime, user_timezone: str) -> str:
        """Convert UTC time to user's timezone"""
        pass
```

**Integration Points:**
- Called from `scheduler.py:publish_scheduled_posts()`
- Called from `scheduler.py:notify_pending_jobs()` (new 30-min job)
- HTTP webhook to `daemon/telegram_notifier.py`

---

#### Task A.3: Update scheduler.py
**File:** `backend/scheduler.py`

Changes:
1. Replace `send_telegram_notification()` (lines 153-177) with call to SNSNotificationService
2. Add new background job: `notify_pending_jobs()` (30-min interval)
3. Update error handling to call `notify_job_failed()`
4. Add telemetry logging for delivery status

```python
# In publish_scheduled_posts():
notification_service = SNSNotificationService(app)
notification_service.notify_job_published(
    user_id=post.user_id,
    post_id=post.id,
    platform=post.platform,
    content=post.content[:100],
    stats={'likes': post.likes_count, 'views': post.views_count}
)

# New 30-min job:
@scheduler.scheduled_job('interval', minutes=30)
def notify_pending_jobs():
    # Query SNSPost where status='scheduled' and scheduled_at <= now + 1 hour
    # Group by user_id
    # For each user with telegram_enabled, notify pending count
    pass
```

---

#### Task A.4: Create Telegram Configuration API
**File:** `backend/routes/sns_routes.py` (new endpoint)

```python
@sns_bp.route('/settings/telegram', methods=['GET'])
@require_auth
def get_telegram_settings():
    """Get user's Telegram notification settings"""
    settings = SNSSettings.query.get(g.user_id)
    return jsonify({
        'telegram_enabled': settings.telegram_enabled,
        'telegram_chat_id': settings.telegram_chat_id[:10] + '***' if settings.telegram_chat_id else None,
        'timezone': settings.timezone,
        'notifications': {
            'on_pending': settings.notification_on_pending,
            'on_complete': settings.notification_on_complete,
            'on_error': settings.notification_on_error
        }
    }), 200

@sns_bp.route('/settings/telegram', methods=['POST'])
@require_auth
def update_telegram_settings():
    """Update Telegram notification settings"""
    data = request.get_json()
    settings = SNSSettings.query.filter_by(user_id=g.user_id).first()

    # Validate chat_id format (numeric string or integer)
    if 'telegram_chat_id' in data:
        chat_id = str(data['telegram_chat_id'])
        if not chat_id.lstrip('-').isdigit():
            return jsonify({'error': 'Invalid chat ID format'}), 400
        settings.telegram_chat_id = chat_id

    settings.telegram_enabled = data.get('telegram_enabled', settings.telegram_enabled)
    settings.timezone = data.get('timezone', 'UTC')
    settings.notification_on_pending = data.get('notifications', {}).get('on_pending', True)
    settings.notification_on_complete = data.get('notifications', {}).get('on_complete', True)
    settings.notification_on_error = data.get('notifications', {}).get('on_error', True)

    db.session.commit()
    return jsonify({'message': 'Settings updated'}), 200

@sns_bp.route('/settings/telegram/test', methods=['POST'])
@require_auth
def test_telegram_connection():
    """Send test notification to verify Telegram is working"""
    settings = SNSSettings.query.filter_by(user_id=g.user_id).first()
    if not settings.telegram_chat_id:
        return jsonify({'error': 'Telegram chat ID not configured'}), 400

    service = SNSNotificationService(current_app)
    service.notify_job_published(
        user_id=g.user_id,
        post_id=0,
        platform='test',
        content='This is a test notification from SoftFactory SNS Auto',
        stats={'likes': 0, 'views': 0}
    )
    return jsonify({'message': 'Test notification sent'}), 200
```

---

#### Task A.5: Update daemon/telegram_notifier.py
**File:** `daemon/telegram_notifier.py` (existing)

**Current State:** Basic message routing
**Enhancement:** Add queue + retry logic for reliability

```python
# In telegram_notifier.py:

class TelegramNotificationQueue:
    """Queue for reliable Telegram message delivery"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.queue = []
        self.max_retries = 3

    def enqueue(self, chat_id: str, message: str, priority: str = 'normal'):
        """Add message to queue"""
        self.queue.append({
            'chat_id': chat_id,
            'message': message,
            'priority': priority,
            'retry_count': 0,
            'created_at': datetime.utcnow()
        })

    def process(self):
        """Send all queued messages with retry logic"""
        for item in self.queue:
            try:
                self.send_message(item['chat_id'], item['message'])
                self.queue.remove(item)
            except Exception as e:
                if item['retry_count'] < self.max_retries:
                    item['retry_count'] += 1
                else:
                    logger.error(f"Failed to send to {item['chat_id']}: {e}")
                    self.queue.remove(item)
```

---

#### Task A.6: Tests & Validation
**File:** `tests/integration/test_sns_notifications.py`

```python
def test_telegram_notification_scheduled():
    """Test notification when job is scheduled"""
    # Create user + SNSSettings with telegram_chat_id
    # Create SNSPost with scheduled_at = 5 minutes from now
    # Trigger publish_scheduled_posts() job
    # Verify notification was sent
    pass

def test_telegram_notification_completion():
    """Test notification when job completes"""
    # Create post, mark as published
    # Verify notification sent with stats
    pass

def test_timezone_conversion():
    """Test that times are converted to user's timezone"""
    # Set user timezone to Asia/Seoul
    # Verify scheduled time shows in Seoul time
    pass

def test_disable_notifications():
    """Test that disabled notifications are not sent"""
    # Set telegram_enabled = False
    # Trigger job completion
    # Verify no notification sent
    pass
```

---

## PART B: CooCook API Enhancement

### Current State
- **Files:** `backend/services/coocook.py` (basic chef booking)
- **Progress:** 35% (only chef listing + booking implemented)
- **Missing:** Recipe management, nutrition, shopping lists, social features

### Architecture

```
CooCook Service Layers:

Layer 1: Recipe Management
├─ Recipe model (title, ingredients, nutrition, difficulty, time)
├─ RecipeReview (user ratings)
├─ Search API (keyword, filters, sorting)
└─ Caching (Redis, 15-min TTL)

Layer 2: Nutrition Calculator
├─ NutritionCalculator class
├─ Ingredient macros database
├─ Per-serving calculations
└─ Allergen detection

Layer 3: Shopping List
├─ ShoppingList model (items JSON array)
├─ Add/remove recipes
├─ Auto-consolidation (merge ingredients)
├─ Price comparison by market
├─ Export (PDF, CSV, Kakao)
└─ Share with groups

Layer 4: Social Feed
├─ UserFeed (follows, shares)
├─ Recipe sharing (public/private/group)
├─ Trending algorithm
├─ Notifications (new shares, engagement)
└─ Favorites + history

Integration:
├─ Existing chef booking (unchanged)
├─ User profiles (extend with preferences)
└─ Payment integration (subscription: coocook feature)
```

---

### PHASE 1: Recipes & Nutrition (1.5 hours)

#### Task B1.1: Extend Recipe Models
**File:** `backend/models.py` (new)

```python
class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = system recipe

    # Basic info
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'appetizer', 'main', 'dessert', 'side', 'beverage'
    cuisine_type = db.Column(db.String(50))  # 'korean', 'italian', 'asian', 'american'

    # Cooking metadata
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    prep_time_minutes = db.Column(db.Integer)  # Time to prep
    cook_time_minutes = db.Column(db.Integer)  # Time to cook
    servings = db.Column(db.Integer, default=4)

    # Content
    instructions = db.Column(db.Text, nullable=False)  # Step-by-step
    ingredients_json = db.Column(db.JSON, default=[])  # Array of {name, quantity, unit, calories, ...}
    nutrition_per_serving = db.Column(db.JSON, default={})  # {calories, protein, carbs, fat, fiber}
    allergens = db.Column(db.JSON, default=[])  # ['nuts', 'dairy', 'gluten', ...]

    # Media
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))

    # Ratings & engagement
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    reviews_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)

    # Status
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviews = db.relationship('RecipeReview', backref='recipe', lazy=True, cascade='all, delete-orphan')
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True, cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_recipe_category', 'category'),
        Index('idx_recipe_difficulty', 'difficulty'),
        Index('idx_recipe_cuisine', 'cuisine_type'),
        Index('idx_recipe_created', 'created_at'),
        Index('idx_recipe_rating', 'rating'),
        Index('idx_recipe_published', 'is_published'),
    )


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)

    # Ingredient details
    name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'cup', 'tbsp', 'tsp', 'gram', 'ml', 'piece'

    # Nutrition per ingredient
    calories = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    fiber_g = db.Column(db.Float, default=0)

    # Optional
    notes = db.Column(db.String(255))  # 'optional', 'fresh', 'chopped', etc.
    allergen_warning = db.Column(db.String(100))  # 'contains nuts', 'dairy-free alternative available'


class RecipeReview(db.Model):
    __tablename__ = 'recipe_reviews'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(120))
    comment = db.Column(db.Text)

    # Engagement
    helpful_count = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))  # User's photo of the dish

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='recipe_reviews')
```

---

#### Task B1.2: Nutrition Calculator Service
**New File:** `backend/services/nutrition_calculator.py`

```python
from typing import Dict, List
import logging

logger = logging.getLogger('coocook.nutrition')

class NutritionCalculator:
    """Calculate nutrition facts for recipes"""

    # Nutrition database (simplified; in production would be external API)
    NUTRITION_DB = {
        'chicken breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
        'rice (cooked)': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
        'olive oil': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100, 'fiber': 0},
        'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.4},
        # ... extend with 100+ common ingredients
    }

    # Unit conversions to grams
    UNIT_CONVERSIONS = {
        'cup': 240,
        'tbsp': 15,
        'tsp': 5,
        'gram': 1,
        'ml': 1,  # Assume 1:1 for liquids
        'piece': 100,  # Average
    }

    @classmethod
    def calculate_recipe_nutrition(cls, ingredients: List[Dict], servings: int = 4) -> Dict:
        """
        Calculate nutrition facts for recipe per serving.

        Args:
            ingredients: [
                {'name': 'chicken', 'quantity': 500, 'unit': 'gram', 'calories': 825, ...},
                ...
            ]
            servings: Number of servings

        Returns:
            {
                'calories': 450,
                'protein': 45,
                'carbs': 30,
                'fat': 12,
                'fiber': 5,
                'vitamins': {...},
                'minerals': {...}
            } per serving
        """
        total = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
        }

        for ingredient in ingredients:
            # Convert quantity to grams
            qty_grams = ingredient['quantity'] * cls.UNIT_CONVERSIONS.get(ingredient['unit'], 1)

            # Lookup ingredient nutrition or use provided
            if 'calories' in ingredient:
                total['calories'] += ingredient['calories']
                total['protein'] += ingredient.get('protein_g', 0)
                total['carbs'] += ingredient.get('carbs_g', 0)
                total['fat'] += ingredient.get('fat_g', 0)
                total['fiber'] += ingredient.get('fiber_g', 0)
            else:
                # Try to lookup from DB
                key = ingredient['name'].lower()
                if key in cls.NUTRITION_DB:
                    nutrition = cls.NUTRITION_DB[key]
                    # Scale by quantity (assuming DB values are per 100g)
                    scale = qty_grams / 100
                    total['calories'] += nutrition['calories'] * scale
                    total['protein'] += nutrition['protein'] * scale
                    total['carbs'] += nutrition['carbs'] * scale
                    total['fat'] += nutrition['fat'] * scale
                    total['fiber'] += nutrition['fiber'] * scale

        # Divide by servings for per-serving values
        per_serving = {}
        for key, value in total.items():
            per_serving[key] = round(value / servings, 1)

        return per_serving

    @classmethod
    def check_allergens(cls, ingredients: List[Dict]) -> List[str]:
        """Detect allergens in recipe"""
        allergen_keywords = {
            'nut': ['nut', 'peanut', 'almond', 'walnut', 'pecan'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt'],
            'gluten': ['wheat', 'bread', 'flour', 'pasta'],
            'soy': ['soy', 'tofu', 'edamame'],
            'fish': ['fish', 'salmon', 'tuna', 'anchovy'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster'],
            'egg': ['egg', 'eggy'],
            'sesame': ['sesame', 'tahini'],
        }

        detected = []
        for ingredient in ingredients:
            name = ingredient['name'].lower()
            for allergen, keywords in allergen_keywords.items():
                if any(kw in name for kw in keywords):
                    detected.append(allergen)
                    break

        return list(set(detected))
```

---

#### Task B1.3: Advanced Recipe Search API
**File:** `backend/services/coocook.py` (extend existing)

```python
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import redis
import json

coocook_bp = Blueprint('coocook', __name__, url_prefix='/api/coocook')

# Redis cache
cache = None

@coocook_bp.before_request
def init_cache():
    global cache
    if cache is None:
        cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@coocook_bp.route('/recipes', methods=['GET'])
def search_recipes():
    """
    Advanced recipe search with filters and sorting.

    Query params:
    - keyword: Search in title/description/ingredients
    - ingredients: Comma-separated list (AND logic)
    - difficulty: easy|medium|hard
    - max_time: Maximum cooking time (minutes)
    - category: appetizer|main|dessert|side|beverage
    - cuisine: korean|italian|asian|american
    - min_rating: Minimum rating (1-5)
    - sort_by: popularity|rating|time|newest (default: popularity)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    """

    # Build cache key
    cache_key = f"recipe_search:{request.query_string.decode()}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(json.loads(cached)), 200

    # Start query
    query = Recipe.query.filter_by(is_published=True)

    # Keyword search
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        query = query.filter(
            or_(
                Recipe.title.ilike(f'%{keyword}%'),
                Recipe.description.ilike(f'%{keyword}%'),
            )
        )

    # Ingredient filter (AND logic)
    ingredients = request.args.get('ingredients', '').strip()
    if ingredients:
        ingredient_list = [ing.strip() for ing in ingredients.split(',')]
        # Subquery: recipes that contain ALL ingredients
        for ingredient in ingredient_list:
            query = query.join(RecipeIngredient).filter(
                RecipeIngredient.name.ilike(f'%{ingredient}%')
            )

    # Difficulty filter
    difficulty = request.args.get('difficulty')
    if difficulty in ['easy', 'medium', 'hard']:
        query = query.filter_by(difficulty=difficulty)

    # Max cooking time
    max_time = request.args.get('max_time', type=int)
    if max_time:
        query = query.filter(Recipe.cook_time_minutes <= max_time)

    # Category & cuisine
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)

    cuisine = request.args.get('cuisine')
    if cuisine:
        query = query.filter_by(cuisine_type=cuisine)

    # Rating filter
    min_rating = request.args.get('min_rating', type=float)
    if min_rating:
        query = query.filter(Recipe.rating >= min_rating)

    # Sorting
    sort_by = request.args.get('sort_by', 'popularity')
    if sort_by == 'rating':
        query = query.order_by(Recipe.rating.desc())
    elif sort_by == 'time':
        query = query.order_by(Recipe.cook_time_minutes.asc())
    elif sort_by == 'newest':
        query = query.order_by(Recipe.created_at.desc())
    else:  # popularity
        query = query.order_by((Recipe.favorite_count + Recipe.rating_count).desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    result = query.paginate(page=page, per_page=per_page)

    recipes_data = [
        {
            'id': r.id,
            'title': r.title,
            'category': r.category,
            'difficulty': r.difficulty,
            'cook_time': r.cook_time_minutes,
            'rating': r.rating,
            'reviews_count': r.reviews_count,
            'image_url': r.image_url,
            'cuisine': r.cuisine_type,
        }
        for r in result.items
    ]

    response = {
        'recipes': recipes_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page,
    }

    # Cache for 15 minutes
    cache.setex(cache_key, 900, json.dumps(response))

    return jsonify(response), 200


@coocook_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """Get full recipe details including nutrition and reviews"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    # Fetch ingredients with nutrition
    ingredients = []
    total_nutrition = NutritionCalculator.calculate_recipe_nutrition(
        [
            {
                'name': ing.name,
                'quantity': ing.quantity,
                'unit': ing.unit,
                'calories': ing.calories,
                'protein_g': ing.protein_g,
                'carbs_g': ing.carbs_g,
                'fat_g': ing.fat_g,
                'fiber_g': ing.fiber_g,
            }
            for ing in recipe.ingredients
        ],
        servings=recipe.servings
    )

    # Top reviews
    top_reviews = RecipeReview.query.filter_by(recipe_id=recipe_id).order_by(
        RecipeReview.helpful_count.desc()
    ).limit(5).all()

    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'description': recipe.description,
        'category': recipe.category,
        'cuisine': recipe.cuisine_type,
        'difficulty': recipe.difficulty,
        'prep_time': recipe.prep_time_minutes,
        'cook_time': recipe.cook_time_minutes,
        'servings': recipe.servings,
        'ingredients': [
            {
                'name': ing.name,
                'quantity': ing.quantity,
                'unit': ing.unit,
                'notes': ing.notes,
                'allergen': ing.allergen_warning,
            }
            for ing in recipe.ingredients
        ],
        'instructions': recipe.instructions,
        'nutrition_per_serving': total_nutrition,
        'allergens': NutritionCalculator.check_allergens([
            {'name': ing.name} for ing in recipe.ingredients
        ]),
        'rating': recipe.rating,
        'reviews_count': recipe.reviews_count,
        'image_url': recipe.image_url,
        'video_url': recipe.video_url,
        'reviews': [
            {
                'id': r.id,
                'user': r.user.name,
                'rating': r.rating,
                'comment': r.comment,
                'helpful': r.helpful_count,
            }
            for r in top_reviews
        ],
    }), 200


@coocook_bp.route('/recipes/<int:recipe_id>/reviews', methods=['POST'])
@require_auth
def add_recipe_review(recipe_id):
    """Add a review for a recipe"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    data = request.get_json()
    if not data.get('rating') or not (1 <= data['rating'] <= 5):
        return jsonify({'error': 'Rating must be 1-5'}), 400

    review = RecipeReview(
        recipe_id=recipe_id,
        user_id=g.user_id,
        rating=data['rating'],
        title=data.get('title'),
        comment=data.get('comment'),
        image_url=data.get('image_url'),
    )

    db.session.add(review)

    # Update recipe rating
    all_reviews = RecipeReview.query.filter_by(recipe_id=recipe_id).all()
    recipe.rating = sum(r.rating for r in all_reviews) / len(all_reviews)
    recipe.reviews_count = len(all_reviews)

    db.session.commit()

    # Clear recipe detail cache
    cache.delete(f"recipe:{recipe_id}:detail")

    return jsonify({'message': 'Review added', 'id': review.id}), 201
```

---

#### Task B1.4: Tests
**File:** `tests/integration/test_coocook_recipes.py`

```python
def test_recipe_search_by_keyword():
    """Test recipe search by keyword"""
    # Create test recipes
    # Search by keyword
    # Verify results
    pass

def test_recipe_search_with_filters():
    """Test recipe search with multiple filters"""
    # Create recipes with various difficulties/times
    # Search with filters: difficulty=easy, max_time=30
    # Verify results match criteria
    pass

def test_nutrition_calculation():
    """Test nutrition calculator accuracy"""
    # Create recipe with known ingredients
    # Calculate nutrition
    # Verify against expected values (95%+ accuracy)
    pass

def test_allergen_detection():
    """Test allergen detection"""
    # Recipe with peanuts + milk
    # Verify allergens detected
    pass

def test_recipe_caching():
    """Test that search results are cached"""
    # First search
    # Second identical search should hit cache
    # Verify cache TTL (15 minutes)
    pass
```

---

### PHASE 2: Shopping List & Feed (1.5 hours)

#### Task B2.1: Shopping List Models
**File:** `backend/models.py` (extend)

```python
class ShoppingList(db.Model):
    __tablename__ = 'shopping_lists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False, default='My Shopping List')
    description = db.Column(db.Text)

    # Items stored as JSON for flexibility
    items = db.Column(db.JSON, default=[])  # [{name, quantity, unit, checked, price_estimate, store}]

    # Metadata
    shared_with = db.Column(db.JSON, default=[])  # List of user IDs shared with
    is_shareable = db.Column(db.Boolean, default=False)  # Share with family/group

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFavorite(db.Model):
    __tablename__ = 'user_favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_favorites', 'user_id', 'recipe_id'),
    )


class UserFollowing(db.Model):
    __tablename__ = 'user_following'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_following', 'follower_id', 'following_id'),
    )


class RecipeShare(db.Model):
    __tablename__ = 'recipe_shares'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Who shared

    visibility = db.Column(db.String(20), default='private')  # private, public, group
    shared_with = db.Column(db.JSON, default=[])  # List of user IDs if group
    caption = db.Column(db.Text)  # Why they're sharing

    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

#### Task B2.2: Shopping List Service
**File:** `backend/services/coocook.py` (extend)

```python
@coocook_bp.route('/shopping-lists', methods=['GET'])
@require_auth
def get_shopping_lists():
    """Get user's shopping lists"""
    lists = ShoppingList.query.filter_by(user_id=g.user_id).all()
    return jsonify([
        {
            'id': sl.id,
            'title': sl.title,
            'item_count': len(sl.items),
            'checked_count': sum(1 for item in sl.items if item.get('checked')),
            'created_at': sl.created_at.isoformat(),
        }
        for sl in lists
    ]), 200


@coocook_bp.route('/shopping-lists', methods=['POST'])
@require_auth
def create_shopping_list():
    """Create a new shopping list"""
    data = request.get_json()
    sl = ShoppingList(
        user_id=g.user_id,
        title=data.get('title', 'My Shopping List'),
        description=data.get('description'),
    )
    db.session.add(sl)
    db.session.commit()
    return jsonify({'id': sl.id, 'message': 'Shopping list created'}), 201


@coocook_bp.route('/shopping-lists/<int:list_id>/add-recipe', methods=['POST'])
@require_auth
def add_recipe_to_shopping_list(list_id):
    """Add recipe ingredients to shopping list"""
    sl = ShoppingList.query.filter_by(id=list_id, user_id=g.user_id).first()
    if not sl:
        return jsonify({'error': 'Shopping list not found'}), 404

    data = request.get_json()
    recipe_id = data.get('recipe_id')
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    # Add recipe ingredients
    for ingredient in recipe.ingredients:
        item = {
            'name': ingredient.name,
            'quantity': ingredient.quantity,
            'unit': ingredient.unit,
            'checked': False,
        }
        sl.items.append(item)

    # Auto-consolidate: merge duplicate ingredients
    _consolidate_shopping_list(sl)

    db.session.commit()
    return jsonify({'message': f'Added {len(recipe.ingredients)} items'}), 200


def _consolidate_shopping_list(shopping_list: ShoppingList):
    """Merge duplicate ingredients in shopping list"""
    consolidated = {}
    for item in shopping_list.items:
        key = item['name'].lower()
        if key in consolidated:
            # Add quantities if same unit
            if consolidated[key]['unit'] == item['unit']:
                consolidated[key]['quantity'] += item['quantity']
        else:
            consolidated[key] = item.copy()

    shopping_list.items = list(consolidated.values())


@coocook_bp.route('/shopping-lists/<int:list_id>/export', methods=['GET'])
@require_auth
def export_shopping_list(list_id):
    """Export shopping list as PDF or CSV"""
    sl = ShoppingList.query.filter_by(id=list_id, user_id=g.user_id).first()
    if not sl:
        return jsonify({'error': 'Shopping list not found'}), 404

    format_type = request.args.get('format', 'csv')  # csv or pdf

    if format_type == 'pdf':
        # Generate PDF using reportlab or weasyprint
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.drawString(50, 750, f"Shopping List: {sl.title}")

        y = 700
        for item in sl.items:
            text = f"{item['name']} - {item['quantity']} {item['unit']}"
            c.drawString(50, y, text)
            y -= 20

        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename="shopping-list.pdf"'
        }

    elif format_type == 'csv':
        import csv
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Item', 'Quantity', 'Unit', 'Checked'])
        for item in sl.items:
            writer.writerow([
                item['name'],
                item['quantity'],
                item['unit'],
                'Yes' if item.get('checked') else 'No'
            ])

        csv_buffer.seek(0)
        return csv_buffer.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="shopping-list.csv"'
        }
```

---

#### Task B2.3: Social Feed & Sharing
**File:** `backend/services/coocook.py` (extend)

```python
@coocook_bp.route('/feed', methods=['GET'])
@require_auth
def get_feed():
    """Get personalized recipe feed from following + trending"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Get users this user is following
    following_ids = [
        uf.following_id
        for uf in UserFollowing.query.filter_by(follower_id=g.user_id).all()
    ]

    # Get recent recipe shares from following
    shared_recipes = RecipeShare.query.filter(
        RecipeShare.user_id.in_(following_ids),
        RecipeShare.visibility.in_(['public', 'group'])
    ).order_by(RecipeShare.created_at.desc()).paginate(page=page, per_page=per_page)

    # Get trending recipes
    trending = Recipe.query.order_by(
        (Recipe.favorite_count + Recipe.rating_count).desc()
    ).limit(5).all()

    feed_items = []
    for share in shared_recipes.items:
        recipe = Recipe.query.get(share.recipe_id)
        user = User.query.get(share.user_id)
        feed_items.append({
            'type': 'recipe_share',
            'recipe': {
                'id': recipe.id,
                'title': recipe.title,
                'image_url': recipe.image_url,
            },
            'shared_by': user.name,
            'caption': share.caption,
            'likes': share.likes,
            'comments': share.comments_count,
            'timestamp': share.created_at.isoformat(),
        })

    return jsonify({
        'feed': feed_items,
        'trending': [
            {'id': r.id, 'title': r.title, 'rating': r.rating}
            for r in trending
        ],
        'total': shared_recipes.total,
        'pages': shared_recipes.pages,
    }), 200


@coocook_bp.route('/recipes/<int:recipe_id>/share', methods=['POST'])
@require_auth
def share_recipe(recipe_id):
    """Share a recipe to feed"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    data = request.get_json()
    share = RecipeShare(
        recipe_id=recipe_id,
        user_id=g.user_id,
        visibility=data.get('visibility', 'private'),
        caption=data.get('caption'),
        shared_with=data.get('shared_with', []),
    )
    db.session.add(share)
    db.session.commit()

    return jsonify({'message': 'Recipe shared', 'id': share.id}), 201


@coocook_bp.route('/users/<int:user_id>/follow', methods=['POST'])
@require_auth
def follow_user(user_id):
    """Follow a user"""
    if user_id == g.user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing = UserFollowing.query.filter_by(
        follower_id=g.user_id,
        following_id=user_id
    ).first()

    if existing:
        return jsonify({'error': 'Already following'}), 400

    follow = UserFollowing(follower_id=g.user_id, following_id=user_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({'message': f'Now following {user.name}'}), 201


@coocook_bp.route('/recipes/<int:recipe_id>/favorite', methods=['POST'])
@require_auth
def favorite_recipe(recipe_id):
    """Add recipe to favorites"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404

    existing = UserFavorite.query.filter_by(
        user_id=g.user_id,
        recipe_id=recipe_id
    ).first()

    if existing:
        return jsonify({'error': 'Already favorited'}), 400

    fav = UserFavorite(user_id=g.user_id, recipe_id=recipe_id)
    db.session.add(fav)

    recipe.favorite_count += 1

    db.session.commit()

    return jsonify({'message': 'Added to favorites', 'favorite_count': recipe.favorite_count}), 201


@coocook_bp.route('/favorites', methods=['GET'])
@require_auth
def get_favorites():
    """Get user's favorite recipes"""
    favorites = UserFavorite.query.filter_by(user_id=g.user_id).all()
    recipes = [Recipe.query.get(fav.recipe_id) for fav in favorites]

    return jsonify([
        {
            'id': r.id,
            'title': r.title,
            'category': r.category,
            'rating': r.rating,
            'image_url': r.image_url,
        }
        for r in recipes if r
    ]), 200
```

---

## Implementation Timeline

| Phase | Task | Duration | Status | Notes |
|-------|------|----------|--------|-------|
| A | SNSSettings extension | 10 min | 🟡 TODO | Database migration required |
| A | SNSNotificationService | 20 min | 🟡 TODO | HTML formatting for Telegram |
| A | scheduler.py updates | 15 min | 🟡 TODO | Replace stub function |
| A | API endpoints | 10 min | 🟡 TODO | Test endpoint included |
| A | daemon integration | 5 min | 🟡 TODO | Existing daemon, light touch |
| A | Tests & validation | 10 min | 🟡 TODO | Unit + integration tests |
| **PART A TOTAL** | | **1 hour** | | |
| | | | | |
| B1 | Recipe models | 15 min | 🟡 TODO | 3 models: Recipe, RecipeIngredient, RecipeReview |
| B1 | Nutrition calculator | 20 min | 🟡 TODO | 95%+ accuracy target |
| B1 | Search API | 25 min | 🟡 TODO | Caching layer required |
| B1 | Tests | 10 min | 🟡 TODO | 5+ test cases |
| **PART B1 TOTAL** | | **1.5 hours** | | |
| | | | | |
| B2 | Shopping list models | 10 min | 🟡 TODO | JSON items array |
| B2 | Shopping list service | 25 min | 🟡 TODO | Export to PDF/CSV |
| B2 | Social feed + sharing | 20 min | 🟡 TODO | Following, sharing, trending |
| B2 | Tests | 10 min | 🟡 TODO | 5+ test cases |
| **PART B2 TOTAL** | | **1.5 hours** | | |
| | | | | |
| **GRAND TOTAL** | | **4 hours** | **0% Complete** | |

---

## Success Criteria

### PART A
- [ ] SNSSettings has telegram_chat_id + telegram_enabled fields
- [ ] Telegram notifications sent on job publish (with preview)
- [ ] Telegram notifications sent on job failure (with retry count)
- [ ] 30-min pending job notification working
- [ ] Test notification API endpoint working
- [ ] All tests passing (unit + integration)

### PART B
- [ ] Recipe search with filters: keyword, difficulty, time, category, rating
- [ ] Nutrition calculator with 95%+ accuracy
- [ ] Shopping list: create, add recipes, consolidate, export (PDF/CSV)
- [ ] Social feed: following, sharing, trending, favorites
- [ ] All tests passing (30+ test cases)
- [ ] Performance: search < 1 second (cached), feed < 500ms

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Telegram API rate limits | 🔴 HIGH | Implement queue + retry with exponential backoff |
| Nutrition DB incomplete | 🟡 MEDIUM | Start with 50 common ingredients, expand iteratively |
| Recipe search performance | 🟡 MEDIUM | Redis caching (15-min TTL), full-text index on title/description |
| Model migrations | 🟡 MEDIUM | Use Flask-Migrate, test migrations in dev first |
| Token overflow | 🔴 HIGH | Stop immediately at 80% budget (160K tokens); cut B2 if needed |

---

## Dependencies

**External:**
- Redis (localhost:6379) — for recipe search caching
- Telegram Bot API — already configured (piwpiwtelegrambot)

**Internal:**
- Existing User + SNSSettings models
- Existing SNSPost + scheduler infrastructure
- Existing daemon/telegram_notifier.py

**Python packages (already installed):**
- Flask, SQLAlchemy, APScheduler
- redis, requests (for Telegram API)
- reportlab (for PDF export, if not installed: `pip install reportlab`)

---

## Files to Create/Modify

### Create (New)
- `/backend/services/sns_notification.py` — Notification service
- `/backend/services/nutrition_calculator.py` — Nutrition calculator
- `/tests/integration/test_sns_notifications.py` — Telegram notification tests
- `/tests/integration/test_coocook_recipes.py` — Recipe search tests

### Modify (Existing)
- `/backend/models.py` — Add 7 new models (SNSSettings extensions, Recipe*, Shopping*, User*)
- `/backend/scheduler.py` — Replace send_telegram_notification() stub
- `/backend/services/coocook.py` — Extend with 12+ new API endpoints
- `/backend/auth.py` — Add `require_auth` decorator (if not already there)
- `/backend/app.py` — Register SNSNotificationService in app context

---

## Token Budget Allocation

```
PART A: Telegram Bot Scheduler
├─ Planning & design: 2K
├─ SNSSettings model: 1.5K
├─ SNSNotificationService: 3K
├─ scheduler.py updates: 1.5K
├─ API endpoints: 1K
├─ Tests: 2K
└─ SUBTOTAL: 12K

PART B: CooCook Enhancement
├─ Recipe models: 2K
├─ Nutrition calculator: 3.5K
├─ Search API: 5K
├─ Shopping list: 4K
├─ Social feed: 4K
├─ Tests: 5K
└─ SUBTOTAL: 25K

TOTAL: 37K (18.5% of 200K budget)
REMAINING: 163K (81.5%)
```

---

## Next Steps

1. **Start PART A** (Task #22): Extend SNSSettings, implement notification service
2. **Start PART B1** (Task #23): Recipe models, nutrition calculator, search API
3. **Start PART B2** (Task #24): Shopping lists, social feed, sharing
4. **Validation & Testing:** Run full integration tests, verify performance benchmarks
5. **Deployment:** Create migration scripts, deploy to production
6. **Documentation:** API docs, user guides, integration guide

---

**Author:** Claude Code v2.1.55 | **Governance:** CLAUDE.md v3.0 | **Date:** 2026-02-26
