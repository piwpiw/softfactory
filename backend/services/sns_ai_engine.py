"""SNS AI Engine — Real AI-powered content generation for social media.

Uses the Anthropic Claude API with tiered model selection for cost efficiency:
  - fast tier  (haiku): hashtags, posting times, trending
  - balanced tier (sonnet): content generation, calendars, repurposing, analysis

Optimizations (v2.0):
  - Tiered model routing per task complexity
  - TTL-based response caching via ai_cache.AIResponseCache
  - Compressed prompts (40-60% shorter than v1.0)
  - Per-method max_tokens caps
  - Usage tracking forwarded to claude_ai.usage_tracker

All methods include graceful fallback to template-based responses when
the API is unavailable or raises an error.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger('sns.ai')

# ---------------------------------------------------------------------------
# Try to import anthropic
# ---------------------------------------------------------------------------
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger.warning("anthropic package not installed, using fallback AI")


# ---------------------------------------------------------------------------
# Model tiers — shared with claude_ai to stay consistent
# ---------------------------------------------------------------------------
_MODELS = {
    'fast':     'claude-haiku-4-5-20251001',
    'balanced': 'claude-sonnet-4-6',
    'powerful': 'claude-opus-4-6',
}

_TASK_TIERS: dict[str, str] = {
    'generate_hashtags':          'fast',
    'analyze_best_posting_time':  'fast',
    'get_trending_topics':        'fast',
    'analyze_post_performance':   'balanced',
    'generate_content':           'balanced',
    'repurpose_content':          'balanced',
    'generate_content_calendar':  'balanced',
}

_MAX_TOKENS: dict[str, int] = {
    'generate_hashtags':          200,
    'analyze_best_posting_time':  300,
    'get_trending_topics':        500,
    'analyze_post_performance':   700,
    'generate_content':           800,
    'repurpose_content':         1500,
    'generate_content_calendar': 2000,
}


class SNSAIEngine:
    """Dedicated AI engine for SNS content operations."""

    PLATFORM_SPECS: Dict[str, dict] = {
        'instagram': {
            'char_limit': 2200, 'hashtag_limit': 30, 'best_hashtags': 5,
            'style': 'Visual-first, emoji-rich, story-driven captions',
        },
        'twitter':  {'char_limit': 280,   'thread_supported': True,
                     'style': 'Concise, punchy, conversation-starting'},
        'facebook': {'char_limit': 63206, 'style': 'Community-oriented, shareable, longer-form OK'},
        'tiktok':   {'char_limit': 4000,  'video_only': True,
                     'style': 'Trendy, hook-driven, Gen-Z friendly captions'},
        'linkedin': {'char_limit': 3000,  'professional_tone': True,
                     'style': 'Professional thought-leadership, data-driven insights'},
        'youtube':  {'title_limit': 100,  'desc_limit': 5000,
                     'style': 'SEO-optimized titles, detailed descriptions with timestamps'},
        'pinterest':{'title_limit': 100,  'desc_limit': 500,
                     'style': 'Keyword-rich, inspirational, actionable'},
        'threads':  {'char_limit': 500,   'style': 'Conversational, opinion-driven, Twitter-like brevity'},
    }

    TONE_MAP = {
        'professional':  'Professional and authoritative',
        'casual':        'Casual and friendly',
        'humorous':      'Witty and humorous',
        'inspiring':     'Inspiring and motivational',
        'educational':   'Educational and informative',
        'promotional':   'Promotional but not pushy',
        'storytelling':  'Narrative storytelling',
    }

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self):
        self._client: Optional[Anthropic] = None
        self._api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self._cache = None
        self._cache_ttls: dict = {}

    def _get_cache(self):
        if self._cache is None:
            try:
                from .ai_cache import ai_cache, CACHE_TTLS
                self._cache = ai_cache
                self._cache_ttls = CACHE_TTLS
            except ImportError:
                pass
        return self._cache

    @property
    def client(self) -> Optional[Anthropic]:
        """Lazy-init the Anthropic client."""
        if self._client is None and HAS_ANTHROPIC and self._api_key:
            try:
                self._client = Anthropic(api_key=self._api_key)
            except Exception as exc:
                logger.error("Failed to initialise Anthropic client: %s", exc)
        return self._client

    @property
    def is_available(self) -> bool:
        return self.client is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _call_claude(self, system_prompt: str, user_prompt: str,
                     method: str = '',
                     max_tokens: int = None) -> Optional[str]:
        """Make a single Claude API call using the correct model tier.

        Returns the text response or None on failure.
        """
        if not self.is_available:
            return None

        tier = _TASK_TIERS.get(method, 'fast')
        model = _MODELS[tier]
        effective_max_tokens = max_tokens or _MAX_TOKENS.get(method, 1024)

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=effective_max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = response.content[0].text

            # Forward usage to shared tracker
            usage = getattr(response, 'usage', None)
            if usage:
                try:
                    from .claude_ai import usage_tracker
                    usage_tracker.track(
                        method=method or 'sns_engine',
                        tier=tier,
                        input_tokens=getattr(usage, 'input_tokens', 0),
                        output_tokens=getattr(usage, 'output_tokens', 0),
                    )
                except ImportError:
                    pass

            return text
        except Exception as exc:
            logger.error("Claude API call failed (method=%s): %s", method, exc)
            return None

    def _parse_json_response(self, text: Optional[str]) -> Optional[dict]:
        """Attempt to parse JSON from Claude's response."""
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            first_nl = cleaned.index('\n') if '\n' in cleaned else 3
            cleaned = cleaned[first_nl + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from AI response")
            return None

    def _platform_context(self, platform: str) -> str:
        """Build a compact platform context line for prompts."""
        spec = self.PLATFORM_SPECS.get(platform, {})
        parts = [f"{platform}"]
        if 'char_limit' in spec:
            parts.append(f"chars={spec['char_limit']}")
        if 'hashtag_limit' in spec:
            parts.append(f"hashtags<={spec['hashtag_limit']}")
        return ' | '.join(parts)

    # ==================================================================
    # Method 1: generate_content
    # ==================================================================
    def generate_content(
        self,
        platform: str,
        topic: str,
        tone: str = 'professional',
        language: str = 'ko',
        content_type: str = 'post',
    ) -> dict:
        """Generate platform-specific social media content using Claude AI.

        Returns a dict with keys: content, hashtags, posting_tips, preview, ai_generated.
        """
        method = 'generate_content'
        cache = self._get_cache()
        # Content is always fresh (no caching)

        tone_desc = self.TONE_MAP.get(tone, tone)
        pctx = self._platform_context(platform)
        lang_name = 'Korean' if language == 'ko' else 'English' if language == 'en' else language

        system_prompt = (
            "SNS content expert. "
            'Respond valid JSON: {"content":"","hashtags":[],"posting_tips":[],"preview":""}.'
        )
        user_prompt = (
            f"{content_type} | {pctx} | Topic: {topic} | Tone: {tone_desc} | Lang: {lang_name}\n"
            f"5-10 hashtags. 2-3 tips. Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'content' in parsed:
            return {
                'content':      parsed.get('content', ''),
                'hashtags':     parsed.get('hashtags', []),
                'posting_tips': parsed.get('posting_tips', []),
                'preview':      parsed.get('preview', ''),
                'ai_generated': True,
            }

        return self._fallback_generate_content(platform, topic, tone, language, content_type)

    def _fallback_generate_content(self, platform, topic, tone, language, content_type):
        tone_desc = self.TONE_MAP.get(tone, tone)
        spec = self.PLATFORM_SPECS.get(platform, {})
        char_limit = spec.get('char_limit', 280)

        if language == 'ko':
            content = (
                f"{tone_desc} 톤으로 작성된 '{topic}' 관련 {platform} 콘텐츠입니다. "
                f"이 콘텐츠는 AI가 일시적으로 사용 불가하여 템플릿으로 생성되었습니다."
            )
        else:
            content = (
                f"Here is a {tone_desc.lower()} {content_type} about '{topic}' for {platform}. "
                f"This content was generated using a template because the AI service is temporarily unavailable."
            )

        content = content[:char_limit]
        return {
            'content':      content,
            'hashtags':     [f'#{topic.replace(" ", "")}', f'#{platform}', '#SNSAuto', '#SoftFactory', '#Marketing'],
            'posting_tips': [
                f'Best posting time for {platform}: check the best-time endpoint',
                'Use high-quality visuals to boost engagement',
                'Engage with comments within the first hour',
            ],
            'preview':      f'{content_type.title()} about {topic} for {platform}',
            'ai_generated': False,
        }

    # ==================================================================
    # Method 2: repurpose_content
    # ==================================================================
    def repurpose_content(
        self,
        original_content: str,
        source_platform: str,
        target_platforms: List[str],
    ) -> dict:
        """Adapt content from one platform to multiple target platforms."""
        method = 'repurpose_content'
        targets_ctx = ' / '.join(self._platform_context(p) for p in target_platforms)

        system_prompt = (
            "Content repurposing expert. "
            'Respond ONLY JSON: {"<platform>":{"content":"","hashtags":[],"notes":""}}.'
        )
        user_prompt = (
            f"From {source_platform} to: {targets_ctx}\n"
            f'Original: """{original_content[:400]}"""\n'
            f"Respect char limits. Keep core message. Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and any(p in parsed for p in target_platforms):
            result = {}
            for p in target_platforms:
                entry = parsed.get(p, {})
                result[p] = {
                    'content':      entry.get('content', original_content[:self.PLATFORM_SPECS.get(p, {}).get('char_limit', 280)]),
                    'hashtags':     entry.get('hashtags', []),
                    'notes':        entry.get('notes', ''),
                    'ai_generated': True,
                }
            return result

        return self._fallback_repurpose(original_content, source_platform, target_platforms)

    def _fallback_repurpose(self, original_content, source_platform, target_platforms):
        result = {}
        for platform in target_platforms:
            spec = self.PLATFORM_SPECS.get(platform, {})
            char_limit = spec.get('char_limit', 280)

            if platform == 'instagram':
                adapted = f"{original_content[:min(len(original_content), 180)]}...\n\n#socialmedia #content #marketing"
            elif platform == 'twitter':
                adapted = original_content[:270]
            elif platform == 'tiktok':
                adapted = f"{original_content[:100]}... Full content in bio! #trending"
            elif platform == 'linkedin':
                adapted = f"Thought: {original_content[:180]}\n\nWhat's your take? #business #leadership"
            elif platform == 'threads':
                adapted = original_content[:490]
            elif platform == 'youtube':
                adapted = f"Title: {original_content[:95]}\n\nDescription:\n{original_content[:500]}"
            elif platform == 'pinterest':
                adapted = original_content[:490]
            else:
                adapted = original_content[:char_limit]

            result[platform] = {
                'content':      adapted,
                'hashtags':     [f'#{platform}', '#SNSAuto'],
                'notes':        f'Template-adapted from {source_platform} (AI unavailable)',
                'ai_generated': False,
            }
        return result

    # ==================================================================
    # Method 3: generate_hashtags
    # ==================================================================
    def generate_hashtags(
        self,
        content: str,
        platform: str,
        count: int = 10,
    ) -> dict:
        """Generate relevant hashtags for the given content and platform (fast tier)."""
        method = 'generate_hashtags'
        cache = self._get_cache()
        if cache:
            ttl = self._cache_ttls.get(method, 7200)
            if ttl > 0:
                # Include content hash for precision but keep key small
                import hashlib
                content_sig = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
                cached = cache.get(method, platform=platform, count=count, sig=content_sig)
                if cached is not None:
                    return cached

        system_prompt = (
            "Hashtag strategist. "
            'Respond ONLY JSON: {"hashtags":[],"popular":[],"niche":[],"strategy":""}.'
        )
        user_prompt = (
            f"{platform} | Need {count} hashtags\n"
            f'Content: """{content[:300]}"""\n'
            f"Mix popular + niche tags. Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'hashtags' in parsed:
            result = {
                'hashtags':     parsed.get('hashtags', [])[:count],
                'popular':      parsed.get('popular', []),
                'niche':        parsed.get('niche', []),
                'strategy':     parsed.get('strategy', ''),
                'ai_generated': True,
            }
            if cache:
                import hashlib
                content_sig = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
                ttl = self._cache_ttls.get(method, 7200)
                cache.set(method, result, ttl=ttl, platform=platform,
                          count=count, sig=content_sig)
            return result

        return {
            'hashtags': [
                '#SNSAuto', '#SoftFactory', '#DigitalMarketing',
                '#ContentCreator', '#SocialMedia', f'#{platform}',
                '#Marketing', '#Growth', '#Engagement', '#Strategy',
            ][:count],
            'popular':      ['#SocialMedia', '#Marketing', '#ContentCreator'],
            'niche':        ['#SNSAuto', '#SoftFactory'],
            'strategy':     'Template hashtags generated (AI unavailable). Replace with content-specific tags.',
            'ai_generated': False,
        }

    # ==================================================================
    # Method 4: analyze_best_posting_time
    # ==================================================================
    def analyze_best_posting_time(
        self,
        platform: str,
        audience_timezone: str = 'Asia/Seoul',
    ) -> dict:
        """AI-generated posting time recommendations (fast tier, 1-hour global cache)."""
        method = 'analyze_best_posting_time'
        cache = self._get_cache()
        if cache:
            ttl = self._cache_ttls.get(method, 3600)
            cached = cache.get(method, platform=platform, tz=audience_timezone)
            if cached is not None:
                return cached

        system_prompt = (
            "Social media posting time expert. "
            'Respond ONLY JSON: {"best_times":[{"day":"","time":"","engagement_score":0}],'
            '"explanation":"","weekly_schedule":{}}.'
        )
        user_prompt = (
            f"{platform} | TZ: {audience_timezone}\n"
            f"5+ optimal slots. Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'best_times' in parsed:
            result = {
                'best_times':      parsed.get('best_times', []),
                'explanation':     parsed.get('explanation', ''),
                'weekly_schedule': parsed.get('weekly_schedule', {}),
                'platform':        platform,
                'timezone':        audience_timezone,
                'ai_generated':    True,
            }
            if cache:
                ttl = self._cache_ttls.get(method, 3600)
                cache.set(method, result, ttl=ttl, platform=platform,
                          tz=audience_timezone)
            return result

        # Fallback: well-known engagement windows
        fallback_times = {
            'instagram': [
                {'day': 'Monday', 'time': '11:00', 'engagement_score': 8},
                {'day': 'Wednesday', 'time': '11:00', 'engagement_score': 9},
                {'day': 'Friday', 'time': '10:00', 'engagement_score': 8},
                {'day': 'Saturday', 'time': '09:00', 'engagement_score': 7},
                {'day': 'Sunday', 'time': '18:00', 'engagement_score': 7},
            ],
            'twitter': [
                {'day': 'Monday', 'time': '08:00', 'engagement_score': 8},
                {'day': 'Tuesday', 'time': '09:00', 'engagement_score': 8},
                {'day': 'Wednesday', 'time': '12:00', 'engagement_score': 9},
                {'day': 'Thursday', 'time': '09:00', 'engagement_score': 8},
                {'day': 'Friday', 'time': '09:00', 'engagement_score': 7},
            ],
            'linkedin': [
                {'day': 'Tuesday', 'time': '10:00', 'engagement_score': 9},
                {'day': 'Wednesday', 'time': '12:00', 'engagement_score': 8},
                {'day': 'Thursday', 'time': '10:00', 'engagement_score': 9},
                {'day': 'Friday', 'time': '09:00', 'engagement_score': 7},
                {'day': 'Saturday', 'time': '10:00', 'engagement_score': 6},
            ],
        }
        default_times = [
            {'day': 'Monday', 'time': '09:00', 'engagement_score': 7},
            {'day': 'Wednesday', 'time': '12:00', 'engagement_score': 8},
            {'day': 'Friday', 'time': '17:00', 'engagement_score': 7},
            {'day': 'Saturday', 'time': '10:00', 'engagement_score': 6},
            {'day': 'Sunday', 'time': '19:00', 'engagement_score': 6},
        ]

        return {
            'best_times':      fallback_times.get(platform, default_times),
            'explanation':     f'General best posting times for {platform} (AI unavailable). Times in {audience_timezone}.',
            'weekly_schedule': {},
            'platform':        platform,
            'timezone':        audience_timezone,
            'ai_generated':    False,
        }

    # ==================================================================
    # Method 5: generate_content_calendar
    # ==================================================================
    def generate_content_calendar(
        self,
        topics: List[str],
        platforms: List[str],
        duration_days: int = 30,
        posts_per_week: int = 5,
        language: str = 'ko',
    ) -> dict:
        """Generate a full content calendar across platforms (balanced tier, no cache)."""
        method = 'generate_content_calendar'
        lang_name = 'Korean' if language == 'ko' else 'English' if language == 'en' else language
        topics_str = ', '.join(topics)
        platforms_str = ', '.join(platforms)

        system_prompt = (
            "Social media content planner. "
            'Respond ONLY JSON: {"calendar":[{"date":"YYYY-MM-DD","platform":"","topic":"",'
            '"content_type":"","title":"","notes":""}],"summary":{"total_posts":0,'
            '"platforms_covered":[],"topics_covered":[],"content_types_used":[]}}.'
        )
        user_prompt = (
            f"{duration_days}-day calendar | {posts_per_week} posts/wk | Lang: {lang_name}\n"
            f"Topics: {topics_str} | Platforms: {platforms_str}\n"
            f"Start: {datetime.utcnow().strftime('%Y-%m-%d')} | "
            f"Mix content types (post/reel/story/carousel/article/thread). Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'calendar' in parsed:
            return {
                'calendar':       parsed.get('calendar', []),
                'summary':        parsed.get('summary', {}),
                'duration_days':  duration_days,
                'posts_per_week': posts_per_week,
                'ai_generated':   True,
            }

        return self._fallback_calendar(topics, platforms, duration_days, posts_per_week)

    def _fallback_calendar(self, topics, platforms, duration_days, posts_per_week):
        content_types = ['post', 'reel', 'story', 'carousel', 'article', 'thread']
        calendar = []
        start_date = datetime.utcnow()
        total_posts = int(duration_days / 7 * posts_per_week)

        for i in range(total_posts):
            day_offset = int(i * (duration_days / max(total_posts, 1)))
            post_date = start_date + timedelta(days=day_offset)
            topic = topics[i % len(topics)] if topics else 'General'
            platform = platforms[i % len(platforms)] if platforms else 'instagram'
            ctype = content_types[i % len(content_types)]

            calendar.append({
                'date':         post_date.strftime('%Y-%m-%d'),
                'platform':     platform,
                'topic':        topic,
                'content_type': ctype,
                'title':        f'{ctype.title()}: {topic}',
                'notes':        'Template-generated entry (AI unavailable)',
            })

        return {
            'calendar':       calendar,
            'summary': {
                'total_posts':          len(calendar),
                'platforms_covered':    list(set(platforms)),
                'topics_covered':       list(set(topics)),
                'content_types_used':   list(set(content_types[:len(calendar)])),
            },
            'duration_days':  duration_days,
            'posts_per_week': posts_per_week,
            'ai_generated':   False,
        }

    # ==================================================================
    # Method 6: analyze_post_performance
    # ==================================================================
    def analyze_post_performance(self, post_data: dict) -> dict:
        """AI analysis of post metrics (balanced tier, 30-min per-post cache)."""
        method = 'analyze_post_performance'
        cache = self._get_cache()
        if cache:
            import hashlib
            post_sig = hashlib.md5(
                json.dumps(post_data, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()[:12]
            cached = cache.get(method, sig=post_sig)
            if cached is not None:
                return cached

        platform = post_data.get('platform', 'unknown')
        system_prompt = (
            "Social media analytics expert. "
            'Respond ONLY JSON: {"score":0,"strengths":[],"improvements":[],'
            '"recommendations":[],"benchmark_comparison":""}.'
        )
        user_prompt = (
            f"Analyze {platform} post performance:\n"
            f"Likes:{post_data.get('likes',0)} Comments:{post_data.get('comments',0)} "
            f"Shares:{post_data.get('shares',0)} Reach:{post_data.get('reach',0)} "
            f"Engagement:{post_data.get('engagement_rate',0)}% "
            f"Followers:{post_data.get('followers',0)}\n"
            f'Content: """{str(post_data.get("content",""))[:200]}"""\n'
            f"Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'score' in parsed:
            result = {
                'score':                parsed.get('score', 50),
                'strengths':            parsed.get('strengths', []),
                'improvements':         parsed.get('improvements', []),
                'recommendations':      parsed.get('recommendations', []),
                'benchmark_comparison': parsed.get('benchmark_comparison', ''),
                'ai_generated':         True,
            }
            if cache:
                import hashlib
                post_sig = hashlib.md5(
                    json.dumps(post_data, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest()[:12]
                ttl = self._cache_ttls.get(method, 1800)
                cache.set(method, result, ttl=ttl, sig=post_sig)
            return result

        # Fallback: rule-based scoring
        likes = post_data.get('likes', 0)
        comments = post_data.get('comments', 0)
        shares = post_data.get('shares', 0)
        engagement_rate = post_data.get('engagement_rate', 0)

        score = min(100, int(
            (min(likes, 1000) / 10) +
            (min(comments, 200) / 4) +
            (min(shares, 100) / 2) +
            (min(engagement_rate, 10) * 5)
        ))

        return {
            'score':       max(score, 10),
            'strengths':   [
                'Content was published successfully',
                f'Received {likes} likes' if likes > 0 else 'Post is live',
            ],
            'improvements': [
                'Consider posting at optimal times for your audience',
                'Try adding more engaging visuals',
                'Experiment with different content formats',
            ],
            'recommendations': [
                'Use the content calendar feature for consistent posting',
                'Analyze top-performing posts for patterns',
                'Engage with comments within the first hour of posting',
            ],
            'benchmark_comparison': 'Template analysis (AI unavailable). Connect AI for detailed insights.',
            'ai_generated':         False,
        }

    # ==================================================================
    # Method 7: get_trending_topics
    # ==================================================================
    def get_trending_topics(
        self,
        platform: str,
        category: Optional[str] = None,
        language: str = 'ko',
    ) -> dict:
        """Generate current trending topics (fast tier, 30-min global cache)."""
        method = 'get_trending_topics'
        cache = self._get_cache()
        if cache:
            cached = cache.get(method, platform=platform, category=category,
                               language=language)
            if cached is not None:
                return cached

        lang_name = 'Korean' if language == 'ko' else 'English' if language == 'en' else language
        cat_str = f" [{category}]" if category else ""

        system_prompt = (
            "Social media trend analyst. "
            'Respond ONLY JSON: {"hashtags":[],"topics":[],"engagement_score":0,"insights":""}.'
        )
        user_prompt = (
            f"Trending on {platform}{cat_str} | {lang_name} market\n"
            f"5-10 hashtags. 5 topics. Engagement potential 1-10. Respond ONLY JSON."
        )

        raw = self._call_claude(system_prompt, user_prompt, method=method)
        parsed = self._parse_json_response(raw)

        if parsed and 'topics' in parsed:
            result = {
                'hashtags':        parsed.get('hashtags', []),
                'topics':          parsed.get('topics', []),
                'engagement_score':parsed.get('engagement_score', 7),
                'insights':        parsed.get('insights', ''),
                'platform':        platform,
                'ai_generated':    True,
            }
            if cache:
                ttl = self._cache_ttls.get(method, 1800)
                cache.set(method, result, ttl=ttl, platform=platform,
                          category=category, language=language)
            return result

        # Fallback: static data
        fallback_data = {
            'instagram': {
                'hashtags': ['#ai2026', '#socialmedia', '#contentcreator', '#digitalmarketing', '#influencer',
                             '#reels', '#trending', '#instagood', '#photooftheday', '#viral'],
                'topics': ['AI and Technology', 'Digital Marketing', 'E-commerce', 'Sustainability', 'Wellness'],
                'engagement_score': 8.5,
            },
            'tiktok': {
                'hashtags': ['#foryoupage', '#trending', '#challenge', '#viral', '#comedy',
                             '#fyp', '#duet', '#tutorial', '#lifehack', '#dance'],
                'topics': ['Entertainment', 'Comedy', 'Education', 'Gaming', 'Lifestyle'],
                'engagement_score': 9.2,
            },
            'twitter': {
                'hashtags': ['#tech', '#news', '#AI', '#startup', '#innovation',
                             '#trending', '#opinion', '#thread', '#breaking', '#viral'],
                'topics': ['Breaking News', 'Technology', 'AI/ML', 'Startups', 'Entertainment'],
                'engagement_score': 7.8,
            },
            'linkedin': {
                'hashtags': ['#business', '#career', '#leadership', '#innovation', '#entrepreneur',
                             '#hiring', '#networking', '#management', '#growth', '#ai'],
                'topics': ['Business', 'Career Development', 'Leadership', 'Industry News', 'Entrepreneurship'],
                'engagement_score': 7.2,
            },
            'facebook': {
                'hashtags': ['#family', '#lifestyle', '#community', '#deals', '#entertainment',
                             '#shopping', '#local', '#events', '#recipes', '#diy'],
                'topics': ['Lifestyle', 'Community', 'Entertainment', 'Shopping', 'Family'],
                'engagement_score': 6.9,
            },
        }
        default = {
            'hashtags': ['#trending', '#social', '#content', '#marketing', '#digital'],
            'topics': ['Social Media', 'Content Creation', 'Digital Marketing', 'Technology', 'Lifestyle'],
            'engagement_score': 7.0,
        }
        data = fallback_data.get(platform, default)
        data['platform'] = platform
        data['insights'] = f'Static trending data for {platform} (AI unavailable). Refresh later for AI-powered insights.'
        data['ai_generated'] = False
        return data


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
sns_ai_engine = SNSAIEngine()
