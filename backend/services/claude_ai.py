"""Claude AI Service — Real Anthropic API Integration for SoftFactory Platform

Provides AI-powered content generation, analysis, and recommendations using
the Claude API with tiered model selection for cost efficiency.

Optimizations (v2.0):
  - Tiered model routing: haiku / sonnet / opus per task complexity
  - TTL-based response caching via ai_cache.AIResponseCache
  - Compressed prompts (40-60% shorter than v1.0)
  - Per-method max_tokens caps
  - AIUsageTracker for cost monitoring

All methods include fallback responses when the API key is missing or the
API is unreachable, so the platform never hard-fails on AI features.
"""
import os
import re
import json
import logging
import time
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger('claude_ai')

# ---------------------------------------------------------------------------
# Model tiers
# ---------------------------------------------------------------------------
MODELS = {
    'fast':     'claude-haiku-4-5-20251001',  # Simple: hashtags, quick lookups
    'balanced': 'claude-sonnet-4-6',           # Medium: content generation
    'powerful': 'claude-opus-4-6',             # Complex: deep analysis (sparingly)
}

# Task → model tier mapping
TASK_MODELS: dict[str, str] = {
    'generate_hashtags':        'fast',
    'get_trending_topics':      'fast',
    'analyze_best_posting_time':'fast',
    'generate_review_response': 'fast',
    'analyze_nutrition':        'fast',
    'recommend_recipes':        'fast',
    'generate_bio_content':     'fast',
    'generate_sns_content':     'balanced',
    'repurpose_content':        'balanced',
    'generate_content_calendar':'balanced',
    'analyze_competitor':       'balanced',
    'calculate_roi':            'balanced',
    'analyze_post_performance': 'balanced',
}

# Per-method max_tokens caps
MAX_TOKENS_BY_METHOD: dict[str, int] = {
    'generate_hashtags':         200,
    'get_trending_topics':       500,
    'analyze_best_posting_time': 300,
    'generate_review_response':  400,
    'analyze_nutrition':         800,
    'recommend_recipes':         600,
    'generate_bio_content':      400,
    'generate_sns_content':      800,
    'repurpose_content':        1500,
    'generate_content_calendar':2000,
    'analyze_competitor':       1000,
    'calculate_roi':             600,
    'analyze_post_performance':  700,
}


# ---------------------------------------------------------------------------
# Usage tracker
# ---------------------------------------------------------------------------
class AIUsageTracker:
    """Track API usage for cost monitoring."""

    # Anthropic pricing (per 1M tokens, USD)
    _PRICE = {
        'fast':     {'input': 0.25,  'output': 1.25},
        'balanced': {'input': 3.00,  'output': 15.00},
        'powerful': {'input': 15.00, 'output': 75.00},
    }

    def __init__(self) -> None:
        self.daily_calls: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.calls_by_method: dict[str, int] = {}
        self.tokens_by_tier: dict[str, dict] = {
            'fast':     {'input': 0, 'output': 0},
            'balanced': {'input': 0, 'output': 0},
            'powerful': {'input': 0, 'output': 0},
        }
        self._reset_time: float = time.time()

    def track(
        self,
        method: str,
        tier: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self.daily_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.calls_by_method[method] = self.calls_by_method.get(method, 0) + 1
        if tier in self.tokens_by_tier:
            self.tokens_by_tier[tier]['input'] += input_tokens
            self.tokens_by_tier[tier]['output'] += output_tokens

    def estimated_cost_usd(self) -> float:
        total = 0.0
        for tier, counts in self.tokens_by_tier.items():
            prices = self._PRICE.get(tier, self._PRICE['fast'])
            total += (counts['input'] / 1_000_000) * prices['input']
            total += (counts['output'] / 1_000_000) * prices['output']
        return round(total, 6)

    def report(self) -> dict:
        return {
            'daily_calls': self.daily_calls,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'estimated_cost_usd': self.estimated_cost_usd(),
            'calls_by_method': self.calls_by_method,
            'tokens_by_tier': self.tokens_by_tier,
            'tracking_since': datetime.utcfromtimestamp(self._reset_time).isoformat(),
        }


# Module-level singleton
usage_tracker = AIUsageTracker()


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------
class ClaudeAIService:
    """Real Claude AI integration with tiered models, caching, and usage tracking."""

    def __init__(self):
        self.client = None
        # Default model (used for _call_claude when no method is specified)
        self.model = MODELS['fast']
        self._init_client()
        # Lazy import cache to avoid circular imports
        self._cache = None

    def _get_cache(self):
        if self._cache is None:
            try:
                from .ai_cache import ai_cache, CACHE_TTLS
                self._cache = ai_cache
                self._cache_ttls = CACHE_TTLS
            except ImportError:
                self._cache = None
        return self._cache

    def _init_client(self):
        """Initialize the Anthropic client from environment variable."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key and api_key.startswith('sk-ant-'):
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
                logger.info("Claude AI service initialized (tiered model routing active)")
            except Exception as e:
                logger.error("Failed to initialize Anthropic client: %s", e)
                self.client = None
        else:
            logger.warning("ANTHROPIC_API_KEY not set or invalid — AI features will use fallback")

    def is_available(self) -> bool:
        """Check if the Claude API client is ready."""
        return self.client is not None

    # ----------------------------------------------------------------
    # Model selector
    # ----------------------------------------------------------------

    def _model_for(self, method: str) -> str:
        tier = TASK_MODELS.get(method, 'fast')
        return MODELS[tier]

    def _tier_for(self, method: str) -> str:
        return TASK_MODELS.get(method, 'fast')

    # ================================================================
    # SNS Content Generation
    # ================================================================

    def generate_sns_content(
        self,
        platform: str,
        topic: str,
        tone: str = 'professional',
        language: str = 'ko',
        content_type: str = 'post',
        hashtag_count: int = 5,
        char_limit: int = 0,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate SNS post content using Claude (balanced tier)."""
        method = 'generate_sns_content'
        cache = self._get_cache()
        if cache:
            ttl = self._cache_ttls.get(method, 0)
            if ttl > 0:
                cached = cache.get(method, platform=platform, topic=topic,
                                   tone=tone, language=language,
                                   content_type=content_type,
                                   hashtag_count=hashtag_count,
                                   user_id=user_id)
                if cached is not None:
                    return cached

        platform_limits = {
            'twitter': 280, 'instagram': 2200, 'tiktok': 2200,
            'linkedin': 3000, 'facebook': 63206, 'threads': 500, 'blog': 10000,
        }
        effective_limit = char_limit or platform_limits.get(platform, 2200)
        lang_map = {'ko': 'Korean', 'en': 'English', 'ja': 'Japanese', 'zh': 'Chinese'}
        lang_name = lang_map.get(language, language)

        system = "SNS content expert. Respond valid JSON only."
        prompt = (
            f"{platform} {content_type} | Topic: {topic} | Tone: {tone} | "
            f"Lang: {lang_name} | MaxChars: {effective_limit} | Tags: {hashtag_count}\n"
            f'JSON: {{"content":"","hashtags":[],"caption":"","best_posting_time":"","engagement_tips":[]}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True,
                                   method=method)
        if isinstance(result, dict) and 'content' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 0)
                if ttl > 0:
                    cache.set(method, result, ttl=ttl, platform=platform,
                              topic=topic, tone=tone, language=language,
                              content_type=content_type,
                              hashtag_count=hashtag_count, user_id=user_id)
            return result

        return self._fallback_sns_content(platform, topic, tone, language, hashtag_count)

    # ================================================================
    # Content Repurposing
    # ================================================================

    def repurpose_content(
        self,
        original_content: str,
        source_platform: str,
        target_platforms: List[str],
    ) -> Dict[str, Any]:
        """Repurpose content across multiple platforms (balanced tier)."""
        method = 'repurpose_content'
        system = "Cross-platform content adapter. Respond valid JSON only."
        platforms_str = ', '.join(target_platforms)
        prompt = (
            f"Repurpose {source_platform} content for: {platforms_str}\n"
            f'Original: """{original_content[:500]}"""\n'
            f"Limits: twitter=280, instagram=2200, linkedin=3000, tiktok=2200, facebook=63206\n"
            f'JSON: {{"repurposed":{{"<platform>":{{"content":"","hashtags":[],"notes":""}}}},"strategy_notes":""}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'repurposed' in result:
            return result

        return self._fallback_repurpose(original_content, source_platform, target_platforms)

    # ================================================================
    # Competitor Analysis
    # ================================================================

    def analyze_competitor(
        self,
        platform: str,
        username: str,
        context_data: Optional[Dict] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a competitor account (balanced tier, 1-hour cache)."""
        method = 'analyze_competitor'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, platform=platform, username=username,
                               user_id=user_id)
            if cached is not None:
                return cached

        system = "Competitive social media analyst. Respond valid JSON only."
        ctx_str = f"\nMetrics: {json.dumps(context_data, ensure_ascii=False)}" if context_data else ""
        prompt = (
            f"Analyze {platform} @{username} as competitor.{ctx_str}\n"
            f'JSON: {{"account":"{username}","platform":"{platform}","analysis":{{"content_strategy":"","target_audience":"","posting_frequency":"","engagement_style":""}},'
            f'"strengths":[],"weaknesses":[],"opportunities":[],"recommendations":[],"competitive_score":0,"threat_level":""}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'analysis' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 3600)
                cache.set(method, result, ttl=ttl, platform=platform,
                          username=username, user_id=user_id)
            return result

        return self._fallback_competitor(platform, username)

    # ================================================================
    # Trending Topics
    # ================================================================

    def get_trending_topics(
        self,
        platform: str,
        category: Optional[str] = None,
        language: str = 'ko',
    ) -> Dict[str, Any]:
        """Get trending topics (fast tier, 30-min global cache)."""
        method = 'get_trending_topics'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, platform=platform, category=category,
                               language=language)
            if cached is not None:
                return cached

        lang_map = {'ko': 'Korean', 'en': 'English', 'ja': 'Japanese'}
        lang_name = lang_map.get(language, language)
        cat_str = f" [{category}]" if category else ""

        system = "Social media trend analyst. Respond valid JSON only."
        prompt = (
            f"Trending on {platform}{cat_str} for {lang_name} market. "
            f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
            f'JSON: {{"platform":"{platform}","language":"{language}","trending_topics":['
            f'{{"topic":"","description":"","engagement_score":0,"content_ideas":[]}}],'
            f'"trending_hashtags":[{{"hashtag":"","estimated_reach":"","competition":""}}],'
            f'"recommended_formats":[],"best_posting_times":[],"category":"{category or "general"}"}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'trending_topics' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 1800)
                cache.set(method, result, ttl=ttl, platform=platform,
                          category=category, language=language)
            return result

        return self._fallback_trending(platform, category, language)

    # ================================================================
    # Review Response Generation
    # ================================================================

    def generate_review_response(
        self,
        review_text: str,
        brand_name: str = 'SoftFactory',
        tone: str = 'professional',
        review_rating: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a customer review response (fast tier, no cache)."""
        method = 'generate_review_response'
        rating_ctx = f" | Rating: {review_rating}/5" if review_rating else ""
        system = "Customer relations expert. Respond valid JSON only."
        prompt = (
            f"Review response for {brand_name} | Tone: {tone}{rating_ctx}\n"
            f'Review: """{review_text[:400]}"""\n'
            f'JSON: {{"response":"","sentiment":"","sentiment_score":0,'
            f'"key_topics":[],"urgency":"","follow_up_actions":[],"tone_used":"{tone}","alternative_responses":[]}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'response' in result:
            return result

        return self._fallback_review_response(review_text, brand_name, tone)

    # ================================================================
    # Nutrition Analysis
    # ================================================================

    def analyze_nutrition(
        self,
        ingredients: List[str],
        servings: int = 1,
        dish_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze nutrition from ingredients (fast tier, 24-hour cache)."""
        method = 'analyze_nutrition'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, ingredients=sorted(ingredients),
                               servings=servings, dish_name=dish_name)
            if cached is not None:
                return cached

        ings_str = ', '.join(ingredients[:20])  # cap at 20 items
        dish_ctx = f" for '{dish_name}'" if dish_name else ""
        system = "Nutritionist. Respond valid JSON only."
        prompt = (
            f"Nutrition{dish_ctx} | Servings: {servings} | Ingredients: {ings_str}\n"
            f'JSON: {{"dish_name":"{dish_name or "Custom Recipe"}","servings":{servings},'
            f'"per_serving":{{"calories":0,"protein_g":0,"carbohydrates_g":0,"fat_g":0,'
            f'"fiber_g":0,"sodium_mg":0,"sugar_g":0}},'
            f'"vitamins_minerals":[],"health_notes":[],"dietary_tags":[],'
            f'"healthier_alternatives":[],"allergens":[]}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'per_serving' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 86400)
                cache.set(method, result, ttl=ttl,
                          ingredients=sorted(ingredients),
                          servings=servings, dish_name=dish_name)
            return result

        return self._fallback_nutrition(ingredients, servings, dish_name)

    # ================================================================
    # Recipe Recommendations
    # ================================================================

    def recommend_recipes(
        self,
        preferences: Dict[str, Any],
        dietary_restrictions: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recommend recipes (fast tier, 30-min user-keyed cache)."""
        method = 'recommend_recipes'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, preferences=preferences,
                               restrictions=dietary_restrictions,
                               user_id=user_id)
            if cached is not None:
                return cached

        restrictions_str = ', '.join(dietary_restrictions) if dietary_restrictions else 'none'
        prefs_str = json.dumps(preferences, ensure_ascii=False)
        system = "Professional chef & recipe curator. Respond valid JSON only."
        prompt = (
            f"3 recipe recommendations | Restrictions: {restrictions_str}\n"
            f"Prefs: {prefs_str}\n"
            f'JSON: {{"recipes":[{{"name_ko":"","name_en":"","difficulty":"","prep_time_min":0,'
            f'"cook_time_min":0,"servings":0,"ingredients":[],"instructions":[],'
            f'"nutrition_highlights":[],"chef_tips":[],"tags":[]}}],'
            f'"dietary_match":true,"recommendations_note":""}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'recipes' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 1800)
                cache.set(method, result, ttl=ttl, preferences=preferences,
                          restrictions=dietary_restrictions, user_id=user_id)
            return result

        return self._fallback_recipes(preferences, dietary_restrictions)

    # ================================================================
    # Bio Content Generation
    # ================================================================

    def generate_bio_content(
        self,
        name: str,
        niche: str,
        platforms: List[str],
        style: str = 'professional',
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate link-in-bio content (fast tier, no cache — brand-specific)."""
        method = 'generate_bio_content'
        platforms_str = ', '.join(platforms)
        system = "Personal branding expert. Respond valid JSON only."
        prompt = (
            f"Bio for {name} | Niche: {niche} | Platforms: {platforms_str} | Style: {style}\n"
            f"Limits: Instagram=150, TikTok=80, Twitter=160, LinkedIn=2600\n"
            f'JSON: {{"brand_name":"{name}","niche":"{niche}","tagline":"",'
            f'"bios":{{"<platform>":{{"bio_text":"","char_count":0,"headline":"","cta":""}}}},'
            f'"link_suggestions":[],"branding_tips":[]}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'bios' in result:
            return result

        return self._fallback_bio(name, niche, platforms, style)

    # ================================================================
    # ROI Analysis
    # ================================================================

    def calculate_roi(
        self,
        metrics_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """AI-powered ROI analysis (balanced tier, 5-min user-keyed cache)."""
        method = 'calculate_roi'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, metrics=metrics_data, user_id=user_id)
            if cached is not None:
                return cached

        metrics_str = json.dumps(metrics_data, ensure_ascii=False)
        system = "Digital marketing ROI analyst. Respond valid JSON only."
        prompt = (
            f"ROI analysis | Metrics: {metrics_str}\n"
            f'JSON: {{"roi_percentage":0,"roi_summary":"","cost_analysis":{{"cost_per_engagement":0,'
            f'"cost_per_reach":0,"cost_per_conversion":0,"efficiency_rating":""}},'
            f'"benchmarks":{{"industry_avg_roi":0,"performance_vs_benchmark":"","percentile":0}},'
            f'"insights":[],"recommendations":[],"budget_suggestions":{{"current_allocation":"",'
            f'"recommended_changes":[],"projected_roi_improvement":""}}}}'
        )

        result = self._call_claude(prompt, system=system, json_mode=True, method=method)
        if isinstance(result, dict) and 'roi_percentage' in result:
            if cache:
                ttl = self._cache_ttls.get(method, 300)
                cache.set(method, result, ttl=ttl, metrics=metrics_data,
                          user_id=user_id)
            return result

        return self._fallback_roi(metrics_data)

    # ================================================================
    # Core API call — tiered model + usage tracking
    # ================================================================

    def _call_claude(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: Optional[int] = None,
        method: str = '',
    ) -> Any:
        """Core Claude API call with tiered model, usage tracking, and error handling.

        Args:
            prompt: User message prompt
            system: Optional system prompt
            json_mode: If True, attempt to parse JSON from response
            max_tokens: Override max tokens (uses per-method cap if not set)
            method: Method name for tier routing and token tracking

        Returns:
            Parsed JSON dict (if json_mode), raw text string, or fallback
        """
        if not self.client:
            logger.warning("Claude client not initialized, using fallback")
            return self._fallback_response(prompt)

        model = self._model_for(method) if method else self.model
        tier = self._tier_for(method) if method else 'fast'
        effective_max_tokens = (
            max_tokens
            or MAX_TOKENS_BY_METHOD.get(method, 1000)
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs: Dict[str, Any] = {
                "model": model,
                "max_tokens": effective_max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)
            text = response.content[0].text

            # Track usage
            usage = getattr(response, 'usage', None)
            if usage:
                usage_tracker.track(
                    method=method or 'unknown',
                    tier=tier,
                    input_tokens=getattr(usage, 'input_tokens', 0),
                    output_tokens=getattr(usage, 'output_tokens', 0),
                )

            if json_mode:
                return self._extract_json(text)

            return text

        except Exception as e:
            error_str = str(e)
            if 'rate_limit' in error_str.lower() or '429' in error_str:
                logger.warning("Claude API rate limited: %s", e)
            elif 'authentication' in error_str.lower() or '401' in error_str:
                logger.error("Claude API authentication failed: %s", e)
            elif 'overloaded' in error_str.lower() or '529' in error_str:
                logger.warning("Claude API overloaded: %s", e)
            else:
                logger.error("Claude API error: %s", e)

            return self._fallback_response(prompt)

    def _extract_json(self, text: str) -> Any:
        """Extract and parse JSON from Claude's response text."""
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            pass

        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except (json.JSONDecodeError, ValueError):
                pass

        logger.warning("Could not extract JSON from Claude response")
        return {"raw_text": text, "_parse_error": True}

    # ================================================================
    # Fallback Responses (when API is unavailable)
    # ================================================================

    def _fallback_response(self, prompt: str) -> Dict[str, Any]:
        return {
            "message": "AI service temporarily unavailable. Please try again later.",
            "fallback": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_sns_content(
        self, platform: str, topic: str, tone: str, language: str, hashtag_count: int,
    ) -> Dict[str, Any]:
        tone_map = {
            'professional': 'professionally crafted',
            'casual': 'casually written',
            'humorous': 'lighthearted',
            'inspiring': 'inspiring',
        }
        tone_desc = tone_map.get(tone, 'professionally crafted')
        hashtags = [f"#{topic.replace(' ', '')}", "#SoftFactory", "#SNSAuto",
                    "#ContentCreation", "#Marketing"][:hashtag_count]

        if language == 'ko':
            content = (
                f"{topic}에 대한 {tone_desc} 콘텐츠입니다.\n\n"
                f"AI 서비스가 일시적으로 사용 불가하여 기본 콘텐츠가 생성되었습니다.\n"
                f"{' '.join(hashtags)}"
            )
        else:
            content = (
                f"A {tone_desc} post about {topic}.\n\n"
                f"AI service temporarily unavailable — default content generated.\n"
                f"{' '.join(hashtags)}"
            )

        return {
            "content": content,
            "hashtags": hashtags,
            "caption": f"{topic} - {platform} content",
            "best_posting_time": "Weekday 6-9 PM",
            "engagement_tips": [
                "Add a compelling visual or image",
                "Engage with comments within the first hour",
                "Use platform-specific features (Stories, Reels, etc.)",
            ],
            "fallback": True,
        }

    def _fallback_repurpose(
        self, original_content: str, source_platform: str, target_platforms: List[str],
    ) -> Dict[str, Any]:
        repurposed = {}
        limits = {
            'twitter': 270, 'instagram': 2200, 'tiktok': 2200,
            'linkedin': 3000, 'facebook': 63206, 'threads': 500,
        }

        for platform in target_platforms:
            limit = limits.get(platform, 2200)
            truncated = original_content[:limit]
            if len(original_content) > limit:
                truncated = truncated[:limit - 3] + "..."

            if platform == 'twitter':
                text = truncated[:270]
            elif platform == 'linkedin':
                text = f"Insight: {truncated}\n\nWhat are your thoughts? #business #growth"
            elif platform == 'instagram':
                text = f"{truncated}\n\n#content #marketing #socialmedia"
            elif platform == 'tiktok':
                text = f"{truncated[:200]}\n\nFull content in bio! #trending #fyp"
            else:
                text = truncated

            repurposed[platform] = {
                "content": text,
                "hashtags": ["#content", "#crosspost"],
                "notes": "Auto-adapted (AI unavailable)",
            }

        return {
            "repurposed": repurposed,
            "strategy_notes": "AI service temporarily unavailable. Basic adaptation applied.",
            "fallback": True,
        }

    def _fallback_competitor(self, platform: str, username: str) -> Dict[str, Any]:
        return {
            "account": username,
            "platform": platform,
            "analysis": {
                "content_strategy": "Analysis unavailable — AI service temporarily offline",
                "target_audience": "Unable to determine without AI analysis",
                "posting_frequency": "Unknown",
                "engagement_style": "Unknown",
            },
            "strengths": ["Active presence on the platform"],
            "weaknesses": ["Detailed analysis requires AI service"],
            "opportunities": ["Monitor this account manually for now"],
            "recommendations": [
                "Try again when AI service is available for full analysis",
                "Manually review their recent posts and engagement patterns",
                "Track their posting frequency over the next week",
            ],
            "competitive_score": 5.0,
            "threat_level": "unknown",
            "fallback": True,
        }

    def _fallback_trending(
        self, platform: str, category: Optional[str], language: str,
    ) -> Dict[str, Any]:
        default_topics = {
            'instagram': ['AI Technology', 'Digital Marketing', 'Content Creation', 'E-commerce', 'Wellness'],
            'tiktok': ['Entertainment', 'Comedy', 'Education', 'Gaming', 'Lifestyle'],
            'twitter': ['Technology', 'News', 'Business', 'Science', 'Culture'],
            'linkedin': ['Business Strategy', 'Career Growth', 'Innovation', 'Leadership', 'AI'],
        }
        topics = default_topics.get(platform, ['General', 'Technology', 'Business', 'Culture', 'Lifestyle'])

        return {
            "platform": platform,
            "language": language,
            "trending_topics": [
                {
                    "topic": t,
                    "description": f"Trending in {platform}",
                    "engagement_score": 7.0,
                    "content_ideas": [f"Create a post about {t}", f"Share your perspective on {t}"],
                }
                for t in topics
            ],
            "trending_hashtags": [
                {"hashtag": f"#{t.replace(' ', '')}", "estimated_reach": "10K-50K", "competition": "medium"}
                for t in topics
            ],
            "recommended_formats": ["carousel", "short video", "infographic"],
            "best_posting_times": ["Weekday 7-9 AM", "Weekday 6-8 PM"],
            "category": category or "general",
            "fallback": True,
        }

    def _fallback_review_response(
        self, review_text: str, brand_name: str, tone: str,
    ) -> Dict[str, Any]:
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'poor', 'disappointed',
                          '별로', '나쁜', '실망', '최악', '안좋']
        positive_words = ['great', 'amazing', 'excellent', 'love', 'best', 'perfect', 'wonderful',
                          '좋은', '최고', '훌륭', '완벽', '사랑']

        review_lower = review_text.lower()
        neg_count = sum(1 for w in negative_words if w in review_lower)
        pos_count = sum(1 for w in positive_words if w in review_lower)

        if neg_count > pos_count:
            sentiment = "negative"
            response = (
                f"Thank you for your feedback. We're sorry to hear about your experience. "
                f"At {brand_name}, we take all feedback seriously and are working to improve. "
                f"Please reach out to our support team so we can make this right."
            )
        elif pos_count > neg_count:
            sentiment = "positive"
            response = (
                f"Thank you so much for your kind words! We're thrilled you had a great experience "
                f"with {brand_name}. Your support means the world to us. "
                f"We look forward to serving you again!"
            )
        else:
            sentiment = "neutral"
            response = (
                f"Thank you for taking the time to share your thoughts about {brand_name}. "
                f"We appreciate your feedback and always strive to improve our service."
            )

        return {
            "response": response,
            "sentiment": sentiment,
            "sentiment_score": 0.3 if sentiment == "negative" else (0.8 if sentiment == "positive" else 0.5),
            "key_topics": ["customer experience"],
            "urgency": "high" if sentiment == "negative" else "low",
            "follow_up_actions": [
                "Review the feedback internally",
                "Consider reaching out personally to the customer",
            ],
            "tone_used": tone,
            "alternative_responses": [],
            "fallback": True,
        }

    def _fallback_nutrition(
        self, ingredients: List[str], servings: int, dish_name: Optional[str],
    ) -> Dict[str, Any]:
        return {
            "dish_name": dish_name or "Custom Recipe",
            "servings": servings,
            "per_serving": {
                "calories": 0, "protein_g": 0, "carbohydrates_g": 0,
                "fat_g": 0, "fiber_g": 0, "sodium_mg": 0, "sugar_g": 0,
            },
            "vitamins_minerals": [],
            "health_notes": [
                "AI nutrition analysis is temporarily unavailable.",
                "Please try again later for detailed nutritional breakdown.",
            ],
            "dietary_tags": [],
            "healthier_alternatives": [],
            "allergens": [],
            "fallback": True,
            "ingredient_count": len(ingredients),
        }

    def _fallback_recipes(
        self, preferences: Dict, dietary_restrictions: Optional[List[str]],
    ) -> Dict[str, Any]:
        return {
            "recipes": [
                {
                    "name_ko": "기본 레시피",
                    "name_en": "Default Recipe",
                    "difficulty": "easy",
                    "prep_time_min": 10,
                    "cook_time_min": 20,
                    "servings": 2,
                    "ingredients": [{"item": "Please try again when AI is available", "amount": "-", "notes": ""}],
                    "instructions": ["AI recipe service temporarily unavailable. Please try again later."],
                    "nutrition_highlights": [],
                    "chef_tips": ["Try again when AI service is available for personalized recommendations"],
                    "tags": ["fallback"],
                }
            ],
            "dietary_match": False,
            "recommendations_note": "AI service temporarily unavailable. Default recipe shown.",
            "fallback": True,
        }

    def _fallback_bio(
        self, name: str, niche: str, platforms: List[str], style: str,
    ) -> Dict[str, Any]:
        bios = {}
        for platform in platforms:
            bios[platform] = {
                "bio_text": f"{name} | {niche}",
                "char_count": len(f"{name} | {niche}"),
                "headline": f"{name} - {niche} Creator",
                "cta": "Link below for more!",
            }

        return {
            "brand_name": name,
            "niche": niche,
            "tagline": f"{name} | Empowering through {niche}",
            "bios": bios,
            "link_suggestions": [
                {"title": "Portfolio", "type": "portfolio", "priority": 1},
                {"title": "Contact", "type": "social", "priority": 2},
            ],
            "branding_tips": [
                "Keep your bio concise and keyword-rich",
                "Include a clear call-to-action",
                "Use emojis sparingly for visual appeal",
            ],
            "fallback": True,
        }

    def _fallback_roi(self, metrics_data: Dict) -> Dict[str, Any]:
        total_cost = metrics_data.get('total_cost', 0) or metrics_data.get('estimated_cost', 100)
        total_revenue = metrics_data.get('total_revenue', 0) or metrics_data.get('estimated_revenue', 0)
        engagement = metrics_data.get('total_engagement', 0)

        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0

        return {
            "roi_percentage": round(roi, 2),
            "roi_summary": "Basic ROI calculation (AI analysis unavailable)",
            "cost_analysis": {
                "cost_per_engagement": round(total_cost / max(engagement, 1), 2),
                "cost_per_reach": 0,
                "cost_per_conversion": 0,
                "efficiency_rating": "unknown",
            },
            "benchmarks": {
                "industry_avg_roi": 120.0,
                "performance_vs_benchmark": "unknown (AI analysis required)",
                "percentile": 0,
            },
            "insights": [
                "AI analysis temporarily unavailable",
                "Basic ROI calculated from provided metrics",
            ],
            "recommendations": [
                {
                    "action": "Retry when AI service is available for detailed analysis",
                    "expected_impact": "Full insights and optimization suggestions",
                    "priority": "high",
                    "effort": "low",
                }
            ],
            "budget_suggestions": {
                "current_allocation": f"Total cost: ${total_cost}",
                "recommended_changes": ["AI analysis needed for specific recommendations"],
                "projected_roi_improvement": "Unknown",
            },
            "fallback": True,
        }


# ================================================================
# Global singleton instance
# ================================================================
claude_ai = ClaudeAIService()
