# Claude API Integration Design — Sprint 2 Preparation
> **Status:** DESIGN (Not Implemented Yet) | **Date:** 2026-02-25
> **Scope:** Backend architecture for AI-powered suggestions across all SoftFactory services
> **Target Deployment:** Sprint 2 (TBD)

---

## Executive Summary

This document outlines the architectural design for integrating Anthropic's Claude API across SoftFactory's five core services. The integration enables AI-powered suggestions on every major user interaction, with cost control, safety checks, and graceful fallback when API unavailable.

**Key Design Principles:**
1. **Cost-Efficient:** Redis caching layer reduces API calls by 70%+ (estimated)
2. **Safe:** Content filtering + PII detection before sending to Claude
3. **Resilient:** Automatic fallback to static suggestions when API fails
4. **Observable:** Full cost tracking + usage monitoring
5. **Testable:** A/B testing framework for prompt optimization

---

## 1. Integration Points (5 Services × Use Cases)

### 1.1 CooCook — Chef Booking Platform

**AI Suggestion Points:**
| User Action | Claude Prompt | Output Type |
|-------------|---------------|------------|
| Browse chefs | "Best chef recommendations" based on user profile | List of 3-5 chef IDs with reasoning |
| Plan menu | "Menu curation" based on dietary + budget | Dish recommendations + timing |
| Post-booking review | "Review template generator" | Pre-filled review sections |

**Expected Engagement Uplift:** +25% (Chef page dwell time)
**Estimated API Calls/Month:** 800 (after 70% cache hit)

**Integration Points in Code:**
```
backend/services/coocook.py
├─ GET /api/coocook/chefs → Add 'ai_recommended' field
├─ GET /api/coocook/chefs/<id> → Add 'menu_suggestions' field
└─ POST /api/coocook/bookings/<id>/review → Suggest review template
```

---

### 1.2 SNS Auto — Social Media Automation

**AI Suggestion Points:**
| User Action | Claude Prompt | Output Type |
|-------------|---------------|------------|
| Create post | "Best posting times analysis" (platform + audience) | Optimal times + hashtags |
| Draft caption | "Caption generation" from product description | 3-5 caption variants |
| Campaign planning | "Content strategy" based on niche | Monthly content calendar |

**Expected Engagement Uplift:** +40% (Posts created)
**Estimated API Calls/Month:** 1,200 (after cache)

**Integration Points in Code:**
```
backend/services/sns_auto.py
├─ POST /api/sns/posts → Add 'ai_suggested_times' field
├─ POST /api/sns/posts → Add 'ai_captions' (3 variants)
└─ GET /api/sns/campaigns → Add 'ai_strategy' field
```

---

### 1.3 Review Campaign — Influencer Marketing

**AI Suggestion Points:**
| User Action | Claude Prompt | Output Type |
|-------------|---------------|------------|
| Create campaign | "Campaign strategy" (product category + budget) | Strategy outline + KPIs |
| Select influencers | "Influencer matching" (brand voice + audience) | Ranked influencer suggestions |
| Brief template | "Influencer brief generator" | Pre-written brief sections |

**Expected Engagement Uplift:** +35% (Campaigns created)
**Estimated API Calls/Month:** 600 (after cache)

**Integration Points in Code:**
```
backend/services/review.py
├─ POST /api/review/campaigns → Add 'ai_strategy' field
├─ GET /api/review/campaigns/<id> → Add 'ai_influencer_suggestions' field
└─ POST /api/review/campaigns/<id>/brief → Generate brief template
```

---

### 1.4 AI Automation — Business Process Automation

**AI Suggestion Points:**
| User Action | Claude Prompt | Output Type |
|-------------|---------------|------------|
| Create workflow | "Workflow optimization" (from use case) | Step-by-step optimization tips |
| Test scenario | "Code review" (for custom JS nodes) | Bug detection + improvements |
| Deploy automation | "Success metrics" (based on workflow type) | KPI suggestions + monitoring |

**Expected Engagement Uplift:** +30% (Advanced features used)
**Estimated API Calls/Month:** 500 (after cache)

**Integration Points in Code:**
```
backend/services/ai_automation.py
├─ POST /api/ai-automation/employees → Add 'ai_optimization_tips' field
├─ POST /api/ai-automation/scenarios → Code review suggestions
└─ GET /api/ai-automation/employees/<id> → Success metrics
```

---

### 1.5 WebApp Builder — Coding Bootcamp Platform

**AI Suggestion Points:**
| User Action | Claude Prompt | Output Type |
|-------------|---------------|------------|
| Course selection | "Learning path optimization" (skill level + goal) | Recommended course sequence |
| Assignment help | "Code explanation" (from student code) | Commented walkthrough |
| Project building | "Feature expansion ideas" (for bootcamp project) | 5 next-step ideas |

**Expected Engagement Uplift:** +20% (Project completion rate)
**Estimated API Calls/Month:** 900 (after cache)

**Integration Points in Code:**
```
backend/services/webapp_builder.py
├─ GET /api/webapp-builder/courses → Add 'ai_recommended_path' field
├─ POST /api/webapp-builder/assignments/<id>/help → Code explanation
└─ GET /api/webapp-builder/projects/<id> → Feature expansion ideas
```

---

## 2. Architecture Design

### 2.1 Module Structure

```
backend/
├── claude_integration.py        ← Main wrapper (Claude API + error handling)
├── prompts.py                   ← All 20+ prompt templates
├── cost_tracker.py              ← Usage logging + billing calculations
├── prompt_cache.py              ← Redis caching layer
├── safety_checks.py             ← Content filtering + PII detection
├── fallback_suggestions.py       ← Static suggestions (when API fails)
├── ab_testing.py                ← A/B testing framework for prompts
├── monitoring/
│   └── claude_metrics.py        ← Usage tracking + dashboards
└── services/
    ├── coocook.py               ← (modified: integrate AI suggestions)
    ├── sns_auto.py              ← (modified: integrate AI suggestions)
    ├── review.py                ← (modified: integrate AI suggestions)
    ├── ai_automation.py         ← (modified: integrate AI suggestions)
    └── webapp_builder.py        ← (modified: integrate AI suggestions)
```

### 2.2 API Wrapper Design (claude_integration.py)

**Class Structure:**
```python
class ClaudeAPIClient:
    """Main wrapper for Claude API integration"""

    def __init__(self, api_key: str, model: str = 'claude-3-5-sonnet'):
        """Initialize with API key and model"""
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key)

    def generate_suggestion(
        self,
        prompt_template: str,
        context: dict,
        service: str,
        use_case: str,
        timeout: int = 10,
        cache: bool = True
    ) -> dict:
        """
        Generate AI suggestion with caching and cost tracking.

        Args:
            prompt_template: Template name from prompts.py
            context: Dynamic data for prompt interpolation
            service: Service name (coocook, sns_auto, review, etc)
            use_case: Use case name for tracking
            timeout: Max seconds to wait for response
            cache: Use Redis cache if available

        Returns:
            {
                'success': bool,
                'suggestion': str | list,
                'cost': float (USD),
                'cached': bool,
                'model': str,
                'tokens': {'input': int, 'output': int}
            }
        """

    def batch_generate(
        self,
        requests: list[dict],
        parallel: bool = True
    ) -> list[dict]:
        """Batch process multiple requests"""

    def validate_before_send(self, text: str) -> dict:
        """Run safety checks before sending to Claude"""

    def estimate_cost(self, tokens_used: int) -> float:
        """Calculate USD cost for tokens used"""
```

**Key Methods:**
- `generate_suggestion()` — Main entry point (with caching + fallback)
- `batch_generate()` — For concurrent suggestions
- `validate_before_send()` — Content filtering
- `estimate_cost()` — Cost calculation
- `set_rate_limit()` — Quota management

---

### 2.3 Prompt Templates Design (prompts.py)

**Structure:**
```python
PROMPTS = {
    # CooCook
    'coocook_chef_recommendation': {
        'model': 'claude-3-5-sonnet',
        'max_tokens': 200,
        'template': """
        Based on the user profile:
        - Budget: {budget}
        - Cuisine preference: {cuisine}
        - Dietary restrictions: {dietary_restrictions}
        - Party size: {party_size}

        Recommend 3-5 chefs from the database. Return as JSON.
        """,
        'output_schema': {
            'type': 'array',
            'items': {
                'chef_id': 'int',
                'reasoning': 'str',
                'confidence': 'float'
            }
        },
        'cache_ttl': 3600,  # 1 hour
        'safety_level': 'low'
    },

    'coocook_menu_curation': {
        'model': 'claude-3-5-sonnet',
        'max_tokens': 500,
        'template': """
        Curate a menu for {guest_count} people:
        - Dietary restrictions: {dietary}
        - Cuisine type: {cuisine}
        - Occasion: {occasion}
        - Duration: {duration_hours} hours

        Suggest 5-7 dishes with timing and plating order.
        """,
        'output_schema': {...},
        'cache_ttl': 3600,
        'safety_level': 'low'
    },

    # SNS Auto
    'sns_posting_times': {
        'model': 'claude-3-5-sonnet',
        'max_tokens': 300,
        'template': """
        Analyze optimal posting times:
        - Platform: {platform}
        - Target audience: {audience}
        - Content type: {content_type}
        - User's timezone: {timezone}

        Return best times for this week as JSON with confidence scores.
        """,
        'output_schema': {...},
        'cache_ttl': 7200,  # 2 hours
        'safety_level': 'medium'
    },

    'sns_caption_generation': {
        'model': 'claude-3-5-sonnet',
        'max_tokens': 400,
        'template': """
        Generate 3 engaging captions for this post:
        - Product: {product_name}
        - Description: {product_desc}
        - Platform: {platform}
        - Tone: {brand_tone}

        Include relevant hashtags. Return as JSON array.
        """,
        'output_schema': {...},
        'cache_ttl': 1800,  # 30 min (content specific)
        'safety_level': 'medium'
    },

    # Review Campaign
    'review_campaign_strategy': {...},
    'review_influencer_matching': {...},
    'review_brief_generator': {...},

    # AI Automation
    'ai_workflow_optimization': {...},
    'ai_code_review': {...},
    'ai_success_metrics': {...},

    # WebApp Builder
    'webapp_learning_path': {...},
    'webapp_code_explanation': {...},
    'webapp_feature_ideas': {...},
}
```

**Prompt Design Principles:**
1. **Structured Output:** All prompts request JSON output with defined schemas
2. **Interpolation:** Use `{var}` placeholders for dynamic context
3. **Safety:** Include content restrictions in system prompt
4. **Context-Aware:** Include user tier/plan in prompt for personalization
5. **Idempotent:** Same input → Same output (deterministic)

---

### 2.4 Caching Layer Design (prompt_cache.py)

**Architecture:**
```python
class PromptCache:
    """Redis-based caching for suggestions"""

    def __init__(self, redis_url: str = 'redis://localhost:6379'):
        self.redis_client = redis.from_url(redis_url)

    def get(self, cache_key: str) -> dict | None:
        """Retrieve cached suggestion"""

    def set(self, cache_key: str, value: dict, ttl: int) -> bool:
        """Store suggestion with TTL"""

    def generate_key(
        self,
        service: str,
        use_case: str,
        context_hash: str
    ) -> str:
        """Generate consistent cache key"""

    def invalidate_user(self, user_id: int) -> int:
        """Clear all caches for a user (when profile changes)"""

    def get_stats(self) -> dict:
        """Return hit/miss statistics"""
```

**Cache Key Strategy:**
```python
cache_key = f"claude:{service}:{use_case}:{hash(context)}"
# Example: "claude:coocook:chef_rec:abc123def456"
```

**Cache TTL by Use Case:**
| Use Case | TTL | Reason |
|----------|-----|--------|
| Chef recommendations | 1 hour | User profile stable |
| SNS posting times | 2 hours | Platform patterns stable |
| Campaign strategy | 1 hour | Strategy stable |
| Code review | 30 min | Code changes frequently |
| Learning paths | 4 hours | Curriculum stable |

**Expected Cache Performance:**
- Hit rate: ~70% (same users re-query similar)
- API reduction: ~3,500 → 1,050 calls/month
- Cost savings: ~$3.50/month (typical usage)

---

### 2.5 Cost Tracking Design (cost_tracker.py)

**Cost Model:**
```python
PRICING = {
    'claude-3-5-sonnet': {
        'input': 0.003 / 1000,    # $0.003 per 1K input tokens
        'output': 0.015 / 1000,   # $0.015 per 1K output tokens
    },
    'claude-3-opus': {
        'input': 0.015 / 1000,    # $0.015 per 1K input tokens
        'output': 0.075 / 1000,   # $0.075 per 1K output tokens
    }
}
```

**Cost Tracker Class:**
```python
class CostTracker:
    """Track and forecast API usage costs"""

    def __init__(self, db_session):
        self.db = db_session

    def log_request(
        self,
        user_id: int,
        service: str,
        use_case: str,
        prompt: str,
        response: str,
        tokens_input: int,
        tokens_output: int,
        cached: bool
    ) -> dict:
        """Log API request to database"""
        cost = self.calculate_cost(tokens_input, tokens_output)
        return {
            'cost': cost,
            'tokens': tokens_input + tokens_output,
            'user_id': user_id,
            'service': service,
            'cached': cached
        }

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate USD cost for tokens"""

    def get_user_monthly_cost(self, user_id: int) -> float:
        """Get user's monthly spend on AI suggestions"""

    def get_service_monthly_cost(self, service: str) -> float:
        """Get service's monthly spend"""

    def forecast_monthly(self) -> float:
        """Forecast full month's cost based on daily average"""

    def get_stats(self) -> dict:
        """Return usage statistics"""
```

**Cost Database Schema:**
```python
class APIUsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service = db.Column(db.String(50))        # coocook, sns_auto, etc
    use_case = db.Column(db.String(100))      # chef_rec, posting_times, etc
    tokens_input = db.Column(db.Integer)
    tokens_output = db.Column(db.Integer)
    cost_usd = db.Column(db.Float)            # Calculated cost
    cached = db.Column(db.Boolean)            # Was this cached?
    response_time_ms = db.Column(db.Integer)
    success = db.Column(db.Boolean)
    error_message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service': self.service,
            'use_case': self.use_case,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'cost_usd': self.cost_usd,
            'cached': self.cached,
            'response_time_ms': self.response_time_ms,
            'success': self.success,
            'created_at': self.created_at.isoformat()
        }
```

**Monthly Cost Estimation:**
```
Base estimate (3,500 requests/month):
- Average tokens: 250 input, 150 output
- Avg cost per request: ~$0.00225 USD
- Monthly total: 3,500 × $0.00225 = ~$7.88

With 70% cache hit (1,050 requests):
- Monthly total: 1,050 × $0.00225 = ~$2.36

With enterprise volume (10K requests):
- Uncached: ~$22.50/month
- Cached: ~$6.75/month
```

---

### 2.6 Safety Checks Design (safety_checks.py)

**Safety Pipeline:**
```python
class SafetyValidator:
    """Multi-layer safety checks before Claude API"""

    def validate(self, context: dict) -> dict:
        """Run all safety checks"""
        return {
            'pii_detected': self.check_pii(context),
            'contains_sensitive': self.check_sensitive_content(context),
            'injection_risk': self.check_prompt_injection(context),
            'safe_to_send': all([
                not self.check_pii(context),
                not self.check_sensitive_content(context),
                not self.check_prompt_injection(context)
            ])
        }

    def check_pii(self, context: dict) -> bool:
        """Detect personal identifiable information"""
        # Phone numbers, emails, SSN, credit cards, etc
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',      # SSN
            r'\b\d{16}\b',                  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
        ]

    def check_sensitive_content(self, context: dict) -> bool:
        """Detect sensitive business data"""
        keywords = [
            'password', 'secret', 'api_key', 'private_key',
            'salary', 'bank_account', 'social_security'
        ]

    def check_prompt_injection(self, context: dict) -> bool:
        """Detect prompt injection attacks"""
        injection_signals = [
            'ignore previous instructions',
            'override system prompt',
            'forget about your instructions'
        ]
```

**Safety Levels:**
| Level | Checks | Use Cases |
|-------|--------|-----------|
| **LOW** | Prompt injection only | Chef recommendations, menu ideas |
| **MEDIUM** | PII + Injection | Social media captions, campaign briefs |
| **HIGH** | All checks + custom validation | Code review, workflow optimization |

---

### 2.7 Fallback Design (fallback_suggestions.py)

**Fallback Strategy:**
When Claude API unavailable (timeout, rate limit, error):
1. Check cache for previous response
2. Return static/template suggestions
3. Log fallback usage
4. Notify user: "Suggestion generated from templates"

```python
class FallbackSuggestions:
    """Static suggestions when API fails"""

    @staticmethod
    def coocook_chef_recommendation(context: dict) -> list:
        """Return top-rated chefs matching cuisine"""
        # Database query: SELECT * FROM chefs WHERE cuisine_type = context['cuisine']
        # ORDER BY rating DESC LIMIT 5

    @staticmethod
    def sns_posting_times(context: dict) -> dict:
        """Return platform average best times"""
        # Based on industry research: Instagram 11am-1pm, TikTok 6pm-10pm, etc

    @staticmethod
    def review_campaign_strategy(context: dict) -> str:
        """Return template strategy outline"""
        return """
        Campaign Strategy Template:
        1. Define target audience
        2. Set measurable KPIs
        3. Create influencer brief
        4. Plan content timeline
        """

    @staticmethod
    def ai_workflow_optimization(context: dict) -> str:
        """Return generic optimization tips"""
        return """
        Workflow Optimization Tips:
        1. Reduce manual data entry (bottleneck)
        2. Add conditional logic for edge cases
        3. Implement error handling
        4. Set up notifications for failures
        """

    @staticmethod
    def webapp_learning_path(context: dict) -> list:
        """Return recommended course sequence"""
        # Static: Beginner → HTML/CSS → JavaScript → Backend → Deploy
```

**Fallback Triggers:**
- API timeout > 10 seconds
- Rate limit error (429)
- Server error (5xx)
- Network error
- Circuit breaker open (>5 consecutive failures)

---

### 2.8 A/B Testing Framework (ab_testing.py)

**A/B Testing Design:**
```python
class ABTestingFramework:
    """Compare prompt variants for effectiveness"""

    def __init__(self, db_session):
        self.db = db_session

    def create_experiment(
        self,
        name: str,
        service: str,
        use_case: str,
        variant_a_prompt: str,
        variant_b_prompt: str,
        metrics: list[str]  # 'engagement', 'adoption', 'satisfaction'
    ) -> dict:
        """Create new A/B test"""

    def assign_variant(self, user_id: int, experiment_id: int) -> str:
        """Assign user to A or B variant (50/50 split)"""

    def log_result(
        self,
        user_id: int,
        experiment_id: int,
        variant: str,
        metric: str,
        value: float
    ) -> None:
        """Log metric outcome"""

    def get_results(self, experiment_id: int) -> dict:
        """Analyze A/B test results"""
        return {
            'experiment_id': experiment_id,
            'variant_a': {
                'adoption_rate': 0.45,  # % of users who used suggestion
                'engagement': 8.3,      # Avg engagement score (1-10)
                'satisfaction': 4.2,    # Avg satisfaction score
                'sample_size': 250
            },
            'variant_b': {...},
            'winner': 'variant_b',
            'confidence': 0.95,  # Statistical significance
            'recommendation': 'Roll out variant_b to all users'
        }
```

**A/B Testing Metrics:**
| Metric | Definition | Target |
|--------|-----------|--------|
| Adoption | % users who accept suggestion | > 30% |
| Engagement | Time spent with suggestion | > 5s average |
| Satisfaction | Post-interaction satisfaction score | > 3.5/5 |
| Conversion | Did suggestion lead to action? | > 25% |

---

### 2.9 Monitoring Design (monitoring/claude_metrics.py)

**Prometheus-Compatible Metrics:**
```python
class ClaudeMetrics:
    """Track API performance and costs"""

    # Counters
    requests_total = Counter(
        'claude_requests_total',
        'Total API requests',
        ['service', 'use_case', 'status']
    )

    tokens_total = Counter(
        'claude_tokens_total',
        'Total tokens used',
        ['type']  # 'input' or 'output'
    )

    cost_total = Counter(
        'claude_cost_usd_total',
        'Total cost in USD',
        ['service']
    )

    # Histograms
    response_time = Histogram(
        'claude_response_time_seconds',
        'API response time',
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
    )

    # Gauges
    cache_hit_rate = Gauge(
        'claude_cache_hit_rate',
        'Percentage of cache hits'
    )

    rate_limit_remaining = Gauge(
        'claude_rate_limit_remaining',
        'Remaining API calls in window'
    )
```

**Dashboard Requirements:**
```
Grafana Dashboard: "Claude API Integration"
├─ Panels:
│  ├─ Total Requests (24h)
│  ├─ API Cost (24h, by service)
│  ├─ Response Time (p50, p95, p99)
│  ├─ Cache Hit Rate (%)
│  ├─ Success Rate (%)
│  ├─ Errors (timeout, rate limit, server error)
│  └─ Tokens Used (input vs output)
└─ Alerts:
   ├─ Cost exceeds $10/day
   ├─ Response time > 5s
   ├─ Success rate < 95%
   └─ Cache hit rate < 50%
```

---

## 3. Integration Pattern (Service Layer Changes)

### 3.1 Example: CooCook Service Integration

**Before:**
```python
@coocook_bp.route('/chefs', methods=['GET'])
def get_chefs():
    """List chefs with filters"""
    query = Chef.query.filter_by(is_active=True)
    # ... filtering logic ...
    return jsonify({'chefs': chefs_data}), 200
```

**After:**
```python
from backend.claude_integration import ClaudeAPIClient
from backend.safety_checks import SafetyValidator
from backend.cost_tracker import CostTracker

claude_client = ClaudeAPIClient(api_key=os.getenv('ANTHROPIC_API_KEY'))
safety = SafetyValidator()
cost_tracker = CostTracker(db)

@coocook_bp.route('/chefs', methods=['GET'])
@require_auth
def get_chefs():
    """List chefs with AI recommendations"""
    user_id = g.user_id
    query = Chef.query.filter_by(is_active=True)

    # ... existing filtering logic ...

    chefs_data = []
    for chef in result.items:
        chefs_data.append({
            'id': chef.id,
            'name': chef.name,
            # ... existing fields ...
        })

    # 🆕 ADD AI RECOMMENDATIONS
    try:
        # Build context for Claude
        context = {
            'user_id': user_id,
            'cuisine_preference': request.args.get('cuisine'),
            'budget': request.args.get('budget', 'medium'),
            'party_size': request.args.get('party_size', 2),
            'chefs_available': [c['id'] for c in chefs_data[:20]]
        }

        # Safety check before API call
        safety_result = safety.validate(context)
        if not safety_result['safe_to_send']:
            app.logger.warning(f"Safety check failed: {safety_result}")
            # Skip AI suggestions if unsafe
        else:
            # Call Claude API
            suggestion = claude_client.generate_suggestion(
                prompt_template='coocook_chef_recommendation',
                context=context,
                service='coocook',
                use_case='chef_listing',
                cache=True
            )

            if suggestion['success']:
                # Add to response
                return jsonify({
                    'chefs': chefs_data,
                    'total': result.total,
                    'pages': result.pages,
                    'ai_recommended_ids': suggestion['suggestion'],  # [chef_id, ...]
                    'ai_meta': {
                        'cached': suggestion['cached'],
                        'cost': suggestion['cost'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }), 200
            else:
                # Fallback to chefs without recommendations
                app.logger.error(f"Claude API failed: {suggestion.get('error')}")

    except Exception as e:
        app.logger.exception(f"AI integration error: {e}")
        # Return normal response without AI suggestions

    return jsonify({
        'chefs': chefs_data,
        'total': result.total,
        'pages': result.pages
    }), 200
```

**Key Integration Points:**
1. Import Claude client + safety checks
2. Build context dict from request + user data
3. Validate before API call
4. Call `generate_suggestion()` with caching
5. Add AI data to response (optional field)
6. Fallback gracefully if API fails
7. Log cost + metrics

---

### 3.2 API Response Changes

**CooCook Chefs Listing (with AI):**
```json
{
  "chefs": [
    {"id": 1, "name": "Chef Alice", "rating": 4.8, ...},
    {"id": 2, "name": "Chef Bob", "rating": 4.6, ...}
  ],
  "total": 45,
  "pages": 5,
  "ai_recommended_ids": [1, 5, 12],
  "ai_meta": {
    "cached": true,
    "cost": 0.00225,
    "timestamp": "2026-02-25T14:30:00Z"
  }
}
```

**All service responses follow same pattern:**
- Base data unchanged
- AI suggestions as optional fields
- `ai_meta` object with cost/cache info
- Backward compatible (clients ignore AI fields if not needed)

---

## 4. Database Schema Changes

### 4.1 New Tables

```python
# 1. API Usage Log (for cost tracking)
class APIUsageLog(db.Model):
    __tablename__ = 'api_usage_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service = db.Column(db.String(50), nullable=False)
    use_case = db.Column(db.String(100), nullable=False)
    tokens_input = db.Column(db.Integer)
    tokens_output = db.Column(db.Integer)
    cost_usd = db.Column(db.Float)
    cached = db.Column(db.Boolean, default=False)
    response_time_ms = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 2. A/B Test Experiments
class ABTestExperiment(db.Model):
    __tablename__ = 'ab_test_experiments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    service = db.Column(db.String(50))
    use_case = db.Column(db.String(100))
    variant_a_prompt = db.Column(db.Text)
    variant_b_prompt = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

# 3. A/B Test Results
class ABTestResult(db.Model):
    __tablename__ = 'ab_test_results'
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('ab_test_experiments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    variant = db.Column(db.String(1))  # A or B
    metric = db.Column(db.String(50))  # engagement, adoption, satisfaction
    value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 4. Prompt Templates (for versioning)
class PromptTemplate(db.Model):
    __tablename__ = 'prompt_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    service = db.Column(db.String(50))
    use_case = db.Column(db.String(100))
    template_text = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 5. Configuration & Environment

### 5.1 Environment Variables

```bash
# .env file (add to existing)

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Redis (for caching)
REDIS_URL=redis://localhost:6379/1

# Cost & Usage
CLAUDE_MONTHLY_BUDGET=500  # Max spend per month
CLAUDE_DAILY_BUDGET=20     # Max spend per day
CLAUDE_RATE_LIMIT=100      # Max requests per minute

# Features
CLAUDE_INTEGRATION_ENABLED=true
CLAUDE_CACHING_ENABLED=true
CLAUDE_SAFETY_CHECKS_ENABLED=true
CLAUDE_AB_TESTING_ENABLED=true
CLAUDE_FALLBACK_ENABLED=true

# Monitoring
CLAUDE_METRICS_ENABLED=true
CLAUDE_COST_TRACKING_ENABLED=true
```

### 5.2 Configuration Class

```python
# backend/config.py (add to existing)

class ClaudeConfig:
    """Claude API configuration"""
    API_KEY = os.getenv('ANTHROPIC_API_KEY')
    MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

    # Budgets
    MONTHLY_BUDGET = float(os.getenv('CLAUDE_MONTHLY_BUDGET', '500'))
    DAILY_BUDGET = float(os.getenv('CLAUDE_DAILY_BUDGET', '20'))
    RATE_LIMIT = int(os.getenv('CLAUDE_RATE_LIMIT', '100'))  # req/min

    # Features
    INTEGRATION_ENABLED = os.getenv('CLAUDE_INTEGRATION_ENABLED', 'true').lower() == 'true'
    CACHING_ENABLED = os.getenv('CLAUDE_CACHING_ENABLED', 'true').lower() == 'true'
    SAFETY_CHECKS_ENABLED = os.getenv('CLAUDE_SAFETY_CHECKS_ENABLED', 'true').lower() == 'true'
    AB_TESTING_ENABLED = os.getenv('CLAUDE_AB_TESTING_ENABLED', 'true').lower() == 'true'
    FALLBACK_ENABLED = os.getenv('CLAUDE_FALLBACK_ENABLED', 'true').lower() == 'true'

    # Monitoring
    METRICS_ENABLED = os.getenv('CLAUDE_METRICS_ENABLED', 'true').lower() == 'true'
    COST_TRACKING_ENABLED = os.getenv('CLAUDE_COST_TRACKING_ENABLED', 'true').lower() == 'true'
```

---

## 6. Testing Strategy

### 6.1 Unit Tests Structure

```python
# tests/unit/test_claude_integration.py

class TestClaudeAPIClient:
    """Test API wrapper"""

    def test_generate_suggestion_success(self):
        """Test successful suggestion generation"""

    def test_generate_suggestion_with_cache_hit(self):
        """Test cache hit returns cached response"""

    def test_generate_suggestion_with_fallback(self):
        """Test fallback when API fails"""

    def test_cost_calculation_accuracy(self):
        """Test cost calculation matches pricing model"""

    def test_safety_checks_reject_pii(self):
        """Test PII detection works"""

    def test_rate_limiting(self):
        """Test rate limit enforcement"""

# tests/unit/test_safety_checks.py
class TestSafetyValidator:
    """Test safety checks"""

    def test_pii_detection_email(self):
        """Detect email addresses"""

    def test_pii_detection_ssn(self):
        """Detect SSN patterns"""

    def test_prompt_injection_detection(self):
        """Detect prompt injection attempts"""

# tests/unit/test_prompts.py
class TestPromptTemplates:
    """Test prompt templates"""

    def test_all_prompts_have_schema(self):
        """All prompts define output schema"""

    def test_prompt_interpolation(self):
        """Variables correctly interpolated"""

    def test_prompt_length_within_limits(self):
        """Prompts respect token limits"""

# tests/unit/test_cost_tracker.py
class TestCostTracker:
    """Test cost tracking"""

    def test_cost_calculation(self):
        """Cost formula matches pricing"""

    def test_user_monthly_cost(self):
        """Aggregate user costs correctly"""

    def test_forecast_accuracy(self):
        """Daily → monthly forecast reasonable"""
```

### 6.2 Integration Tests

```python
# tests/integration/test_claude_service_integration.py

class TestCooCookWithClaude:
    """Test CooCook service with Claude integration"""

    def test_get_chefs_with_ai_recommendations(self):
        """GET /api/coocook/chefs returns ai_recommended_ids"""

    def test_ai_recommendations_in_response_schema(self):
        """Response matches new schema"""

    def test_fallback_when_api_unavailable(self):
        """Works without Claude when API down"""

class TestCachedResponses:
    """Test caching behavior"""

    def test_identical_request_uses_cache(self):
        """Second request hits cache"""

    def test_cache_ttl_respected(self):
        """Cached response expires after TTL"""
```

### 6.3 Load Tests

```python
# tests/performance/test_claude_load.py

class TestClaudeLoadPerformance:
    """Test API performance under load"""

    def test_100_concurrent_requests(self):
        """Handle 100 simultaneous requests"""

    def test_cache_reduces_latency(self):
        """Cache hit latency < 50ms"""

    def test_cost_stays_within_budget(self):
        """Load test stays under daily budget"""
```

---

## 7. Deployment Plan (Sprint 2)

### 7.1 Phased Rollout

**Phase 1: Internal Testing (Week 1)**
- Deploy to staging environment
- Run all test suites
- A/B test with internal team (50 users)
- Monitor for 24 hours

**Phase 2: Canary Deployment (Week 2)**
- Deploy to production with feature flag
- Enable for 5% of users
- Monitor metrics: latency, cost, errors
- Confirm fallback works

**Phase 3: Gradual Rollout (Week 3)**
- Enable for 25% → 50% → 100% users
- Daily budget checks
- Cost monitoring

**Phase 4: Optimization (Week 4)**
- Analyze A/B test results
- Adjust prompts based on feedback
- Optimize caching strategy
- Document lessons learned

---

### 7.2 Feature Flags (for safe deployment)

```python
# backend/feature_flags.py

class FeatureFlags:
    """Feature flags for Claude integration"""

    CLAUDE_INTEGRATION_ENABLED = {
        'description': 'Enable Claude API integration globally',
        'default': False,
        'services': ['coocook', 'sns_auto', 'review', 'ai_automation', 'webapp_builder']
    }

    CLAUDE_SUGGESTIONS_COOCOOK = {
        'description': 'Enable AI suggestions in CooCook',
        'default': False,
        'percentage': 0  # 0-100 for gradual rollout
    }

    CLAUDE_CACHING_ENABLED = {
        'description': 'Enable Redis caching',
        'default': False
    }

    @classmethod
    def is_enabled(cls, flag_name: str, user_id: int = None) -> bool:
        """Check if feature flag is enabled"""
        # Implement with feature flag service (LaunchDarkly, Split.io, etc)
```

---

## 8. Success Metrics & KPIs

### 8.1 Business Metrics

| Metric | Target | Baseline | Measurement |
|--------|--------|----------|-------------|
| Feature Adoption | > 40% of users | 0% | % users accepting AI suggestions |
| Engagement Uplift | +25% | 0% | Page dwell time, interactions per session |
| Cost/User | < $0.02 | N/A | Total cost / active users |
| Fallback Rate | < 5% | N/A | % requests failing gracefully |

### 8.2 Technical Metrics

| Metric | Target | SLA | Alert |
|--------|--------|-----|-------|
| API Success Rate | > 95% | > 99% | < 95% |
| Response Time (p95) | < 2s | < 3s | > 3s |
| Cache Hit Rate | > 70% | N/A | < 50% |
| Daily Cost | < $20 | < $500/mo | > $20 |

---

## 9. Risk Analysis & Mitigation

### 9.1 Identified Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Budget Overrun** | HIGH | Daily budget monitoring + alerts + auto-disable |
| **API Reliability** | MEDIUM | Fallback suggestions + circuit breaker |
| **Latency Impact** | MEDIUM | Async calls + caching + feature flag |
| **PII Leakage** | HIGH | Safety checks + audit logging + data retention policy |
| **Poor Suggestion Quality** | MEDIUM | A/B testing + user feedback loop + prompt versioning |
| **Rate Limiting** | LOW | Request queuing + backoff strategy |

### 9.2 Contingency Plans

**If daily budget exceeded:**
```
1. Alert ops team immediately
2. Reduce suggestion frequency (50% of users)
3. Disable least-effective use cases
4. Auto-disable if > 150% of budget
```

**If API reliability drops below 90%:**
```
1. Enable circuit breaker (fail to fallback)
2. Reduce cache TTL (more fresh responses)
3. Trigger investigation ticket
4. Notify users of degraded service
```

**If latency > 5 seconds:**
```
1. Enable async suggestion generation
2. Return suggestions in background
3. Increase cache TTL
4. Reduce batch sizes
```

---

## 10. Documentation Requirements

### 10.1 Developer Documentation

1. **API Wrapper Usage Guide** — How to call Claude from services
2. **Prompt Template Guide** — How to add new prompts
3. **Cost Tracking Guide** — How to monitor spending
4. **Safety Checks Guide** — PII/injection detection
5. **Caching Strategy** — Cache key design + TTL strategy
6. **Testing Guide** — Unit/integration test patterns

### 10.2 Operations Documentation

1. **Monitoring Dashboard** — Grafana dashboard setup
2. **Alert Configuration** — Budget/latency/error alerts
3. **Incident Response** — What to do when API fails
4. **Cost Forecasting** — Monthly spend estimation
5. **Feature Flag Operations** — Enable/disable prompts by service

---

## 11. Estimated Effort & Timeline

### 11.1 Development Effort

| Component | Effort | Dependencies |
|-----------|--------|--------------|
| API Wrapper (claude_integration.py) | 1 week | None |
| Prompt Templates (prompts.py) | 1 week | API wrapper |
| Caching Layer (prompt_cache.py) | 3 days | API wrapper |
| Safety Checks (safety_checks.py) | 4 days | None |
| Cost Tracking (cost_tracker.py) | 3 days | Database |
| Service Integration (5 services) | 5 days | All above |
| Testing (unit + integration) | 1 week | All above |
| Documentation | 4 days | All above |
| **TOTAL** | **~4.5 weeks** | |

### 11.2 Sprint 2 Timeline

```
Week 1: API Wrapper + Prompts + Safety (Core components)
Week 2: Caching + Cost Tracking + Service Integration (Coocook + SNS)
Week 3: Service Integration (Review + AI Auto + WebApp) + Testing
Week 4: A/B Testing + Monitoring + Documentation + Deployment Prep
```

---

## 12. Future Enhancements (Post-Sprint 2)

1. **Streaming Responses** — Real-time suggestion generation
2. **Custom Model Fine-Tuning** — Optimize prompts for SoftFactory domain
3. **Multi-Model Strategy** — Use Claude + GPT-4 + others
4. **User Preferences** — Let users customize AI suggestion frequency
5. **Feedback Loop** — Users rate suggestions → improve prompts
6. **Analytics Dashboard** — Self-serve usage analytics for admins

---

## Appendix A: Cost Breakdown

### Monthly Cost Estimation (1,000 active users)

```
Scenario 1: No Caching
├─ 3,500 requests/month × $0.00225/request = $7.88
└─ Total: ~$8/month

Scenario 2: With 70% Cache Hit (RECOMMENDED)
├─ 1,050 requests/month × $0.00225/request = $2.36
└─ Total: ~$2-3/month

Scenario 3: Enterprise (10,000 requests)
├─ Without cache: ~$22.50/month
└─ With 70% cache: ~$6.75/month

Annual Projection (Scenario 2):
├─ Claude API: ~$30
├─ Redis (cache): ~$10/month = $120/year
├─ Monitoring: ~$5/month = $60/year
└─ **TOTAL: ~$210/year**
```

---

## Appendix B: Prompt Examples

### Example 1: CooCook Chef Recommendation

```
System: You are a helpful assistant for a chef booking platform.
Your role is to recommend chefs based on user preferences.

User Context:
- Budget: medium ($100-200 per session)
- Cuisine preference: Italian
- Dietary restrictions: vegetarian
- Party size: 4 people
- Available chefs: [1, 5, 12, 18, 22]

Task: Recommend 3-5 chefs from the available list that best match
the user's preferences. Explain your reasoning.

Return as JSON:
{
  "recommendations": [
    {
      "chef_id": 1,
      "reasoning": "Italian cuisine expert with vegetarian experience",
      "confidence": 0.95
    }
  ]
}
```

### Example 2: SNS Auto Posting Times

```
System: You are a social media expert. Your role is to recommend
optimal posting times for maximum engagement.

Context:
- Platform: Instagram
- Target audience: women 25-35, interested in home decor
- Content type: carousel post
- User timezone: US Eastern

Task: Analyze optimal posting times for this week considering:
1. Peak activity times on the platform
2. User's audience demographics
3. Content type engagement patterns

Return as JSON:
{
  "recommendations": [
    {
      "day": "Monday",
      "time": "11:00",
      "confidence": 0.85,
      "reasoning": "High engagement for visual content"
    }
  ]
}
```

---

**Design Status:** ✅ COMPLETE
**Ready for Implementation:** Yes
**Next Step:** Create backend/claude_integration.py module

