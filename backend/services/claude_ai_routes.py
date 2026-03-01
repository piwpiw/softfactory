"""Claude AI Routes — Flask Blueprint for AI-powered endpoints

Provides REST API endpoints for all Claude AI features:
- SNS content generation
- Content repurposing across platforms
- Competitor analysis
- Trending topics
- Review response generation
- Nutrition analysis
- Recipe recommendations
- Bio content generation
- ROI analysis
- Service status check
- AI usage statistics (admin)

v2.0 changes:
  - /api/ai/usage — new admin endpoint for cost monitoring
  - /api/ai/status — now includes cache stats
  - Long-response endpoints use stream_with_context for better UX
"""
import json
from flask import Blueprint, request, jsonify, g, stream_with_context, Response
from datetime import datetime
from ..auth import require_auth
from .claude_ai import claude_ai, usage_tracker

import logging

logger = logging.getLogger('claude_ai_routes')

claude_ai_bp = Blueprint('claude_ai', __name__, url_prefix='/api/ai')


# ================================================================
# POST /api/ai/generate-content — SNS Content Generation
# ================================================================

@claude_ai_bp.route('/generate-content', methods=['POST'])
@require_auth
def generate_content():
    """Generate SNS post content using Claude AI.

    Request body:
        platform (str, required): Target platform (instagram, tiktok, twitter, etc.)
        topic (str, required): Content topic/subject
        tone (str, optional): Writing tone (professional, casual, humorous, inspiring)
        language (str, optional): Output language code (ko, en, ja)
        content_type (str, optional): Post type (post, reel, story, thread)
        hashtag_count (int, optional): Number of hashtags (default 5)
        char_limit (int, optional): Max character count (0 = platform default)

    Returns:
        JSON with generated content, hashtags, tips
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    platform = data.get('platform')
    topic = data.get('topic')

    if not platform or not topic:
        return jsonify({'error': 'Missing required fields: platform, topic'}), 400

    user_id = getattr(g, 'user_id', None)

    result = claude_ai.generate_sns_content(
        platform=platform,
        topic=topic,
        tone=data.get('tone', 'professional'),
        language=data.get('language', 'ko'),
        content_type=data.get('content_type', 'post'),
        hashtag_count=data.get('hashtag_count', 5),
        char_limit=data.get('char_limit', 0),
        user_id=str(user_id) if user_id else None,
    )

    return jsonify({
        'success': True,
        'data': result,
        'platform': platform,
        'generated_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/repurpose — Content Repurposing
# ================================================================

@claude_ai_bp.route('/repurpose', methods=['POST'])
@require_auth
def repurpose():
    """Repurpose content across multiple platforms.

    Request body:
        content (str, required): Original content text
        source_platform (str, required): Original platform
        target_platforms (list[str], required): Platforms to adapt content for
        stream (bool, optional): Stream response chunks (default false)

    Returns:
        JSON with repurposed content for each target platform
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    content = data.get('content')
    source_platform = data.get('source_platform')
    target_platforms = data.get('target_platforms')

    if not content or not source_platform or not target_platforms:
        return jsonify({'error': 'Missing required fields: content, source_platform, target_platforms'}), 400

    if not isinstance(target_platforms, list) or len(target_platforms) == 0:
        return jsonify({'error': 'target_platforms must be a non-empty list'}), 400

    # Streaming path for many target platforms (>3)
    if data.get('stream') and len(target_platforms) > 3:
        def generate():
            result = claude_ai.repurpose_content(
                original_content=content,
                source_platform=source_platform,
                target_platforms=target_platforms,
            )
            payload = json.dumps({
                'success': True,
                'data': result,
                'source_platform': source_platform,
                'target_platforms': target_platforms,
                'generated_at': datetime.utcnow().isoformat(),
                'ai_powered': claude_ai.is_available(),
            }, ensure_ascii=False)
            yield payload

        return Response(
            stream_with_context(generate()),
            content_type='application/json',
        )

    result = claude_ai.repurpose_content(
        original_content=content,
        source_platform=source_platform,
        target_platforms=target_platforms,
    )

    return jsonify({
        'success': True,
        'data': result,
        'source_platform': source_platform,
        'target_platforms': target_platforms,
        'generated_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/analyze-competitor — Competitor Analysis (streaming)
# ================================================================

@claude_ai_bp.route('/analyze-competitor', methods=['POST'])
@require_auth
def analyze_competitor():
    """Analyze a competitor's social media presence.

    Request body:
        platform (str, required): Social media platform
        username (str, required): Competitor's username/handle
        context_data (dict, optional): Known metrics
        stream (bool, optional): Stream response (default false)

    Returns:
        JSON with competitor analysis, strengths, weaknesses, recommendations
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    platform = data.get('platform')
    username = data.get('username')

    if not platform or not username:
        return jsonify({'error': 'Missing required fields: platform, username'}), 400

    user_id = getattr(g, 'user_id', None)

    if data.get('stream'):
        def generate():
            result = claude_ai.analyze_competitor(
                platform=platform,
                username=username,
                context_data=data.get('context_data'),
                user_id=str(user_id) if user_id else None,
            )
            payload = json.dumps({
                'success': True,
                'data': result,
                'analyzed_at': datetime.utcnow().isoformat(),
                'ai_powered': claude_ai.is_available(),
            }, ensure_ascii=False)
            yield payload

        return Response(
            stream_with_context(generate()),
            content_type='application/json',
        )

    result = claude_ai.analyze_competitor(
        platform=platform,
        username=username,
        context_data=data.get('context_data'),
        user_id=str(user_id) if user_id else None,
    )

    return jsonify({
        'success': True,
        'data': result,
        'analyzed_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# GET /api/ai/trending — Trending Topics
# ================================================================

@claude_ai_bp.route('/trending', methods=['GET'])
@require_auth
def trending():
    """Get trending topics and hashtags for a platform.

    Query params:
        platform (str, required): Target platform
        category (str, optional): Content category filter
        language (str, optional): Content language (default 'ko')

    Returns:
        JSON with trending topics, hashtags, and posting recommendations
    """
    platform = request.args.get('platform')
    if not platform:
        return jsonify({'error': 'Missing required parameter: platform'}), 400

    result = claude_ai.get_trending_topics(
        platform=platform,
        category=request.args.get('category'),
        language=request.args.get('language', 'ko'),
    )

    return jsonify({
        'success': True,
        'data': result,
        'queried_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/review-response — Review Response Generation
# ================================================================

@claude_ai_bp.route('/review-response', methods=['POST'])
@require_auth
def review_response():
    """Generate a response to a customer review.

    Request body:
        review_text (str, required): The customer's review
        brand_name (str, optional): Brand name (default 'SoftFactory')
        tone (str, optional): Response tone (professional, warm, apologetic)
        review_rating (int, optional): Star rating 1-5

    Returns:
        JSON with crafted response, sentiment analysis, follow-up actions
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    review_text = data.get('review_text')
    if not review_text:
        return jsonify({'error': 'Missing required field: review_text'}), 400

    result = claude_ai.generate_review_response(
        review_text=review_text,
        brand_name=data.get('brand_name', 'SoftFactory'),
        tone=data.get('tone', 'professional'),
        review_rating=data.get('review_rating'),
    )

    return jsonify({
        'success': True,
        'data': result,
        'generated_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/nutrition-analysis — Nutrition Analysis
# ================================================================

@claude_ai_bp.route('/nutrition-analysis', methods=['POST'])
@require_auth
def nutrition_analysis():
    """Analyze nutritional content from ingredients.

    Request body:
        ingredients (list[str], required): List of ingredients with quantities
        servings (int, optional): Number of servings (default 1)
        dish_name (str, optional): Name of the dish

    Returns:
        JSON with nutritional breakdown, health notes, alternatives
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    ingredients = data.get('ingredients')
    if not ingredients or not isinstance(ingredients, list) or len(ingredients) == 0:
        return jsonify({'error': 'Missing or invalid field: ingredients (must be a non-empty list)'}), 400

    result = claude_ai.analyze_nutrition(
        ingredients=ingredients,
        servings=data.get('servings', 1),
        dish_name=data.get('dish_name'),
    )

    return jsonify({
        'success': True,
        'data': result,
        'analyzed_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/recipe-recommendations — Recipe Recommendations
# ================================================================

@claude_ai_bp.route('/recipe-recommendations', methods=['POST'])
@require_auth
def recipe_recommendations():
    """Get AI-powered recipe recommendations.

    Request body:
        preferences (dict, required): Preferences (cuisine, difficulty, time, ingredients_available)
        dietary_restrictions (list[str], optional): Dietary restrictions

    Returns:
        JSON with 3 personalized recipe recommendations
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    preferences = data.get('preferences')
    if not preferences or not isinstance(preferences, dict):
        return jsonify({'error': 'Missing or invalid field: preferences (must be a dict)'}), 400

    user_id = getattr(g, 'user_id', None)

    result = claude_ai.recommend_recipes(
        preferences=preferences,
        dietary_restrictions=data.get('dietary_restrictions'),
        user_id=str(user_id) if user_id else None,
    )

    return jsonify({
        'success': True,
        'data': result,
        'generated_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/generate-bio — Bio Content Generation
# ================================================================

@claude_ai_bp.route('/generate-bio', methods=['POST'])
@require_auth
def generate_bio():
    """Generate optimized link-in-bio content.

    Request body:
        name (str, required): Creator/brand name
        niche (str, required): Content niche
        platforms (list[str], required): Target platforms
        style (str, optional): Bio style (professional, creative, minimalist, fun)

    Returns:
        JSON with platform-specific bios, tagline, link suggestions
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name')
    niche = data.get('niche')
    platforms = data.get('platforms')

    if not name or not niche or not platforms:
        return jsonify({'error': 'Missing required fields: name, niche, platforms'}), 400

    if not isinstance(platforms, list) or len(platforms) == 0:
        return jsonify({'error': 'platforms must be a non-empty list'}), 400

    user_id = getattr(g, 'user_id', None)

    result = claude_ai.generate_bio_content(
        name=name,
        niche=niche,
        platforms=platforms,
        style=data.get('style', 'professional'),
        user_id=str(user_id) if user_id else None,
    )

    return jsonify({
        'success': True,
        'data': result,
        'generated_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# POST /api/ai/roi-analysis — ROI Analysis (streaming)
# ================================================================

@claude_ai_bp.route('/roi-analysis', methods=['POST'])
@require_auth
def roi_analysis():
    """AI-powered ROI analysis and optimization recommendations.

    Request body:
        metrics (dict, required): Engagement, reach, cost, revenue data
        stream (bool, optional): Stream response (default false)

    Returns:
        JSON with ROI calculation, benchmarks, insights, recommendations
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    metrics = data.get('metrics')
    if not metrics or not isinstance(metrics, dict):
        return jsonify({'error': 'Missing or invalid field: metrics (must be a dict)'}), 400

    user_id = getattr(g, 'user_id', None)

    if data.get('stream'):
        def generate():
            result = claude_ai.calculate_roi(
                metrics_data=metrics,
                user_id=str(user_id) if user_id else None,
            )
            payload = json.dumps({
                'success': True,
                'data': result,
                'analyzed_at': datetime.utcnow().isoformat(),
                'ai_powered': claude_ai.is_available(),
            }, ensure_ascii=False)
            yield payload

        return Response(
            stream_with_context(generate()),
            content_type='application/json',
        )

    result = claude_ai.calculate_roi(
        metrics_data=metrics,
        user_id=str(user_id) if user_id else None,
    )

    return jsonify({
        'success': True,
        'data': result,
        'analyzed_at': datetime.utcnow().isoformat(),
        'ai_powered': claude_ai.is_available(),
    }), 200


# ================================================================
# GET /api/ai/usage — AI Usage Statistics (admin only)
# ================================================================

@claude_ai_bp.route('/usage', methods=['GET'])
@require_auth
def ai_usage():
    """Return AI API usage statistics and estimated cost.

    Requires authentication. Admin-level data — exposes token usage.

    Returns:
        JSON with daily calls, token counts, cost estimate, per-method breakdown,
        and cache hit-rate statistics.
    """
    report = usage_tracker.report()

    # Attach cache stats if available
    cache_stats = None
    try:
        from .ai_cache import ai_cache
        cache_stats = ai_cache.stats()
    except ImportError:
        pass

    return jsonify({
        'success': True,
        'usage': report,
        'cache': cache_stats,
        'queried_at': datetime.utcnow().isoformat(),
    }), 200


# ================================================================
# GET /api/ai/status — AI Service Status
# ================================================================

@claude_ai_bp.route('/status', methods=['GET'])
def ai_status():
    """Check AI service availability and status.

    No authentication required (used by health checks).

    Returns:
        JSON with service status, model info, availability, cache stats
    """
    available = claude_ai.is_available()

    cache_stats = None
    try:
        from .ai_cache import ai_cache
        cache_stats = ai_cache.stats()
    except ImportError:
        pass

    return jsonify({
        'service': 'claude_ai',
        'available': available,
        'model': claude_ai.model,
        'status': 'operational' if available else 'fallback_mode',
        'cache': cache_stats,
        'endpoints': [
            'POST /api/ai/generate-content',
            'POST /api/ai/repurpose',
            'POST /api/ai/analyze-competitor',
            'GET  /api/ai/trending',
            'POST /api/ai/review-response',
            'POST /api/ai/nutrition-analysis',
            'POST /api/ai/recipe-recommendations',
            'POST /api/ai/generate-bio',
            'POST /api/ai/roi-analysis',
            'GET  /api/ai/usage',
            'GET  /api/ai/status',
        ],
        'timestamp': datetime.utcnow().isoformat(),
    }), 200
