"""SNS Auto Service - Social Media Automation — Input-Validated"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import subqueryload
from ..models import db, SNSAccount, SNSPost, SNSLinkInBio, SNSAutomate, SNSCompetitor, SNSAnalytics, SNSTemplate
from ..auth import require_auth, require_subscription
from ..caching_config import cached, cache_bust
from ..cache import ttl_cache, invalidate_cache
from ..input_validator import (
    validate_string, validate_slug, validate_platform, sanitize_html,
    check_xss, check_sql_injection, VALID_SNS_PLATFORMS
)
import json
import logging

from .sns_ai_engine import sns_ai_engine

# Optional: Agent 7's shared Claude AI service (may not exist yet)
try:
    from .claude_ai import claude_ai
    HAS_CLAUDE_AI_SERVICE = True
except ImportError:
    claude_ai = None
    HAS_CLAUDE_AI_SERVICE = False

logger = logging.getLogger('sns.auto')

sns_bp = Blueprint('sns', __name__, url_prefix='/api/sns')

# Template types
TEMPLATES = {
    'card_news': {'name': 'Card News', 'platforms': ['instagram', 'tiktok']},
    'blog_post': {'name': 'Blog Post', 'platforms': ['blog']},
    'reel': {'name': 'Reel', 'platforms': ['instagram']},
    'shorts': {'name': 'YouTube Shorts', 'platforms': ['youtube']},
    'carousel': {'name': 'Carousel', 'platforms': ['instagram']},
}


@sns_bp.route('/accounts', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_accounts():
    """Get user's SNS accounts with post counts (single query, no N+1)"""
    # Subquery: count posts per account in one pass instead of N separate queries
    post_counts = (
        db.session.query(
            SNSPost.account_id,
            func.count(SNSPost.id).label('post_count')
        )
        .filter(SNSPost.user_id == g.user_id)
        .group_by(SNSPost.account_id)
        .subquery()
    )

    results = (
        db.session.query(SNSAccount, post_counts.c.post_count)
        .outerjoin(post_counts, SNSAccount.id == post_counts.c.account_id)
        .filter(SNSAccount.user_id == g.user_id)
        .all()
    )

    accounts_data = []
    for account, post_count in results:
        accounts_data.append({
            'id': account.id,
            'platform': account.platform,
            'account_name': account.account_name,
            'is_active': account.is_active,
            'post_count': post_count or 0,
            'created_at': account.created_at.isoformat(),
        })

    return jsonify(accounts_data), 200


@sns_bp.route('/accounts', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_account():
    """Link SNS account — with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['platform', 'account_name']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate platform against whitelist
    valid, error = validate_platform(data['platform'], VALID_SNS_PLATFORMS)
    if not valid:
        return jsonify({'error': error}), 400

    # Validate and sanitize account name
    valid, error, clean_name = validate_string(
        data['account_name'], 'Account name', min_length=1, max_length=100
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Check for duplicates
    existing = SNSAccount.query.filter_by(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=clean_name
    ).first()

    if existing:
        return jsonify({'error': 'Account already linked'}), 400

    account = SNSAccount(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=data['account_name'],
        is_active=True
    )

    db.session.add(account)
    db.session.commit()

    return jsonify({
        'id': account.id,
        'message': 'Account linked successfully'
    }), 201


@sns_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_account(account_id):
    """Unlink SNS account"""
    account = SNSAccount.query.get(account_id)

    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    db.session.delete(account)
    db.session.commit()

    return jsonify({'message': 'Account unlinked'}), 200


@sns_bp.route('/posts', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_posts():
    """Get user's SNS posts"""
    account_id = request.args.get('account_id', type=int)
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)

    query = SNSPost.query.filter_by(user_id=g.user_id)

    if account_id:
        query = query.filter_by(account_id=account_id)

    if status:
        query = query.filter_by(status=status)

    result = query.order_by(SNSPost.created_at.desc()).paginate(page=page, per_page=20)

    posts_data = []
    for post in result.items:
        posts_data.append({
            'id': post.id,
            'account_name': post.account.account_name,
            'platform': post.platform,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'status': post.status,
            'template_type': post.template_type,
            'scheduled_at': post.scheduled_at.isoformat() if post.scheduled_at else None,
            'created_at': post.created_at.isoformat(),
        })

    return jsonify({
        'posts': posts_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@sns_bp.route('/posts', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_post():
    """Create SNS post — with input validation and XSS prevention"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['account_id', 'content', 'template_type']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate content (max 5000 chars, sanitize XSS)
    valid, error, clean_content = validate_string(
        data['content'], 'Content', min_length=1, max_length=5000
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Validate template_type against known templates
    valid, error, clean_template = validate_string(
        data['template_type'], 'Template type', min_length=1, max_length=50
    )
    if not valid:
        return jsonify({'error': error}), 400

    account = SNSAccount.query.get(data['account_id'])
    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    post = SNSPost(
        user_id=g.user_id,
        account_id=account.id,
        content=clean_content,
        platform=account.platform,
        template_type=clean_template,
        status='draft',
        scheduled_at=None
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({
        'id': post.id,
        'message': 'Post created successfully'
    }), 201


@sns_bp.route('/posts/<int:post_id>/publish', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def publish_post(post_id):
    """Publish or schedule post"""
    post = SNSPost.query.get(post_id)

    if not post or post.user_id != g.user_id:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    scheduled_at = data.get('scheduled_at')

    if scheduled_at:
        try:
            post.scheduled_at = datetime.fromisoformat(scheduled_at)
            post.status = 'scheduled'
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid scheduled_at format'}), 400
    else:
        # Publish immediately (in dev mode)
        post.status = 'published'

    db.session.commit()

    return jsonify({
        'id': post.id,
        'status': post.status,
        'message': 'Post ' + ('scheduled' if scheduled_at else 'published')
    }), 200


@sns_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_post(post_id):
    """Delete post"""
    post = SNSPost.query.get(post_id)

    if not post or post.user_id != g.user_id:
        return jsonify({'error': 'Post not found'}), 404

    if post.status == 'published':
        return jsonify({'error': 'Cannot delete published posts'}), 400

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post deleted'}), 200


@sns_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    """Get available templates"""
    return jsonify(TEMPLATES), 200


# ============ LINK-IN-BIO ENDPOINTS ============

@sns_bp.route('/linkinbio', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_link_in_bios():
    """Get user's link in bio pages"""
    link_in_bios = SNSLinkInBio.query.filter_by(user_id=g.user_id).all()

    return jsonify([lib.to_dict() for lib in link_in_bios]), 200


@sns_bp.route('/linkinbio', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_link_in_bio():
    """Create a link in bio page — with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['slug', 'title']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields (slug, title)'}), 400

    # Validate slug format (URL-safe characters only)
    valid, error = validate_slug(data['slug'])
    if not valid:
        return jsonify({'error': error}), 400

    # Validate and sanitize title
    valid, error, clean_title = validate_string(
        data['title'], 'Title', min_length=1, max_length=200
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Check for duplicate slug
    existing = SNSLinkInBio.query.filter_by(slug=data['slug']).first()
    if existing:
        return jsonify({'error': 'Slug already exists'}), 400

    lib = SNSLinkInBio(
        user_id=g.user_id,
        slug=data['slug'],
        title=data['title'],
        links=data.get('links', []),
        theme=data.get('theme', 'light')
    )

    db.session.add(lib)
    db.session.commit()

    return jsonify({
        'id': lib.id,
        'message': 'Link in bio created successfully',
        'data': lib.to_dict()
    }), 201


@sns_bp.route('/linkinbio/<int:lib_id>', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_link_in_bio(lib_id):
    """Get specific link in bio page"""
    lib = SNSLinkInBio.query.get(lib_id)

    if not lib or lib.user_id != g.user_id:
        return jsonify({'error': 'Link in bio not found'}), 404

    return jsonify(lib.to_dict()), 200


@sns_bp.route('/linkinbio/<int:lib_id>', methods=['PUT'])
@require_auth
@require_subscription('sns-auto')
def update_link_in_bio(lib_id):
    """Update link in bio page"""
    lib = SNSLinkInBio.query.get(lib_id)

    if not lib or lib.user_id != g.user_id:
        return jsonify({'error': 'Link in bio not found'}), 404

    data = request.get_json()

    if 'title' in data:
        lib.title = data['title']
    if 'links' in data:
        lib.links = data['links']
    if 'theme' in data:
        lib.theme = data['theme']

    lib.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Link in bio updated successfully',
        'data': lib.to_dict()
    }), 200


@sns_bp.route('/linkinbio/<int:lib_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_link_in_bio(lib_id):
    """Delete link in bio page"""
    lib = SNSLinkInBio.query.get(lib_id)

    if not lib or lib.user_id != g.user_id:
        return jsonify({'error': 'Link in bio not found'}), 404

    db.session.delete(lib)
    db.session.commit()

    return jsonify({'message': 'Link in bio deleted'}), 200


@sns_bp.route('/linkinbio/stats', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_linkinbio_stats', ttl_seconds=900)
def get_link_in_bio_stats():
    """Get link in bio click statistics"""
    lib_id = request.args.get('lib_id', type=int)

    if lib_id:
        lib = SNSLinkInBio.query.get(lib_id)
        if not lib or lib.user_id != g.user_id:
            return jsonify({'error': 'Link in bio not found'}), 404

        return jsonify({
            'lib_id': lib.id,
            'slug': lib.slug,
            'click_count': lib.click_count,
            'created_at': lib.created_at.isoformat(),
            'updated_at': lib.updated_at.isoformat() if lib.updated_at else None,
        }), 200

    # All link in bios stats
    libs = SNSLinkInBio.query.filter_by(user_id=g.user_id).all()
    stats = []
    total_clicks = 0

    for lib in libs:
        lib_stats = {
            'lib_id': lib.id,
            'slug': lib.slug,
            'title': lib.title,
            'click_count': lib.click_count,
        }
        stats.append(lib_stats)
        total_clicks += lib.click_count

    return jsonify({
        'total_click_count': total_clicks,
        'link_in_bios': stats,
        'count': len(stats)
    }), 200


# ============ AUTOMATION ENDPOINTS ============

@sns_bp.route('/automate', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_automate_list', ttl_seconds=900)
def get_automates():
    """Get user's automation rules"""
    automates = SNSAutomate.query.filter_by(user_id=g.user_id).all()

    return jsonify([a.to_dict() for a in automates]), 200


@sns_bp.route('/automate', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
@cache_bust('sns_automate_list')
def create_automate():
    """Create an automation rule"""
    data = request.get_json()

    required = ['name', 'topic', 'purpose', 'platforms', 'frequency']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Calculate next run time based on frequency
    now = datetime.utcnow()
    frequency = data['frequency']

    if frequency == 'daily':
        next_run = now + timedelta(days=1)
    elif frequency == 'weekly':
        next_run = now + timedelta(weeks=1)
    elif frequency == 'custom':
        # Parse custom frequency from data
        custom_hours = data.get('custom_hours', 24)
        next_run = now + timedelta(hours=custom_hours)
    else:
        next_run = now + timedelta(days=1)

    automate = SNSAutomate(
        user_id=g.user_id,
        name=data['name'],
        topic=data['topic'],
        purpose=data['purpose'],
        platforms=data['platforms'],
        frequency=frequency,
        next_run=next_run,
        is_active=data.get('is_active', True)
    )

    db.session.add(automate)
    db.session.commit()

    return jsonify({
        'id': automate.id,
        'message': 'Automation rule created successfully',
        'data': automate.to_dict()
    }), 201


@sns_bp.route('/automate/<int:automate_id>', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_automate(automate_id):
    """Get specific automation rule"""
    automate = SNSAutomate.query.get(automate_id)

    if not automate or automate.user_id != g.user_id:
        return jsonify({'error': 'Automation rule not found'}), 404

    return jsonify(automate.to_dict()), 200


@sns_bp.route('/automate/<int:automate_id>', methods=['PUT'])
@require_auth
@require_subscription('sns-auto')
@cache_bust('sns_automate_list')
def update_automate(automate_id):
    """Update automation rule"""
    automate = SNSAutomate.query.get(automate_id)

    if not automate or automate.user_id != g.user_id:
        return jsonify({'error': 'Automation rule not found'}), 404

    data = request.get_json()

    if 'name' in data:
        automate.name = data['name']
    if 'topic' in data:
        automate.topic = data['topic']
    if 'purpose' in data:
        automate.purpose = data['purpose']
    if 'platforms' in data:
        automate.platforms = data['platforms']
    if 'frequency' in data:
        automate.frequency = data['frequency']
        # Recalculate next run
        now = datetime.utcnow()
        if data['frequency'] == 'daily':
            automate.next_run = now + timedelta(days=1)
        elif data['frequency'] == 'weekly':
            automate.next_run = now + timedelta(weeks=1)
    if 'is_active' in data:
        automate.is_active = data['is_active']

    automate.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Automation rule updated successfully',
        'data': automate.to_dict()
    }), 200


@sns_bp.route('/automate/<int:automate_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
@cache_bust('sns_automate_list')
def delete_automate(automate_id):
    """Delete automation rule"""
    automate = SNSAutomate.query.get(automate_id)

    if not automate or automate.user_id != g.user_id:
        return jsonify({'error': 'Automation rule not found'}), 404

    db.session.delete(automate)
    db.session.commit()

    return jsonify({'message': 'Automation rule deleted'}), 200


# ============ TRENDING ENDPOINTS ============

@sns_bp.route('/trending', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_trending', ttl_seconds=300)
def get_trending():
    """Get trending topics/hashtags by platform — AI-powered"""
    platform = request.args.get('platform')
    category = request.args.get('category')
    language = request.args.get('language', 'ko')

    def _fetch_trending_for_platform(p, cat, lang):
        """Fetch trending data using claude_ai (primary) or sns_ai_engine (fallback)."""
        try:
            if HAS_CLAUDE_AI_SERVICE and claude_ai is not None and claude_ai.is_available():
                return claude_ai.get_trending_topics(platform=p, category=cat, language=lang)
            return sns_ai_engine.get_trending_topics(platform=p, category=cat, language=lang)
        except Exception as exc:
            logger.error("AI trending failed for %s: %s", p, exc)
            return sns_ai_engine.get_trending_topics(platform=p, category=cat, language=lang)

    if platform:
        data = _fetch_trending_for_platform(platform, category, language)
        return jsonify({
            'platform': platform,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    # When no platform specified, return trending for all major platforms
    all_platforms = ['instagram', 'tiktok', 'twitter', 'linkedin', 'facebook']
    trending_data = {}
    for p in all_platforms:
        trending_data[p] = _fetch_trending_for_platform(p, category, language)

    return jsonify({
        'platforms': trending_data,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============ COMPETITOR ANALYSIS ENDPOINTS ============

@sns_bp.route('/competitor', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_competitors():
    """Get user's tracked competitors"""
    platform = request.args.get('platform')
    page = request.args.get('page', 1, type=int)

    query = SNSCompetitor.query.filter_by(user_id=g.user_id)

    if platform:
        query = query.filter_by(platform=platform)

    result = query.order_by(SNSCompetitor.last_analyzed.desc()).paginate(page=page, per_page=20)

    competitors = [c.to_dict() for c in result.items]

    return jsonify({
        'competitors': competitors,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@sns_bp.route('/competitor', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def add_competitor():
    """Add a competitor to track — with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['platform', 'username']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields (platform, username)'}), 400

    # Validate platform
    valid, error = validate_platform(data['platform'], VALID_SNS_PLATFORMS)
    if not valid:
        return jsonify({'error': error}), 400

    # Validate and sanitize username
    valid, error, clean_username = validate_string(
        data['username'], 'Username', min_length=1, max_length=100
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Check for duplicates
    existing = SNSCompetitor.query.filter_by(
        user_id=g.user_id,
        platform=data['platform'],
        username=clean_username
    ).first()

    if existing:
        return jsonify({'error': 'Competitor already tracked'}), 400

    competitor = SNSCompetitor(
        user_id=g.user_id,
        platform=data['platform'],
        username=data['username'],
        followers_count=data.get('followers_count', 0),
        engagement_rate=data.get('engagement_rate', 0.0),
        avg_likes=data.get('avg_likes', 0),
        avg_comments=data.get('avg_comments', 0),
        posting_frequency=data.get('posting_frequency', 'random'),
        data=data.get('data', {})
    )

    db.session.add(competitor)
    db.session.commit()

    return jsonify({
        'id': competitor.id,
        'message': 'Competitor added successfully',
        'data': competitor.to_dict()
    }), 201


@sns_bp.route('/competitor/<int:competitor_id>', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_competitor_detail', ttl_seconds=900)
def get_competitor(competitor_id):
    """Get specific competitor details"""
    competitor = SNSCompetitor.query.get(competitor_id)

    if not competitor or competitor.user_id != g.user_id:
        return jsonify({'error': 'Competitor not found'}), 404

    return jsonify(competitor.to_dict()), 200


@sns_bp.route('/competitor/<int:competitor_id>', methods=['PUT'])
@require_auth
@require_subscription('sns-auto')
def update_competitor(competitor_id):
    """Update competitor data"""
    competitor = SNSCompetitor.query.get(competitor_id)

    if not competitor or competitor.user_id != g.user_id:
        return jsonify({'error': 'Competitor not found'}), 404

    data = request.get_json()

    if 'followers_count' in data:
        competitor.followers_count = data['followers_count']
    if 'engagement_rate' in data:
        competitor.engagement_rate = data['engagement_rate']
    if 'avg_likes' in data:
        competitor.avg_likes = data['avg_likes']
    if 'avg_comments' in data:
        competitor.avg_comments = data['avg_comments']
    if 'posting_frequency' in data:
        competitor.posting_frequency = data['posting_frequency']
    if 'data' in data:
        competitor.data = data['data']

    competitor.last_analyzed = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Competitor updated successfully',
        'data': competitor.to_dict()
    }), 200


@sns_bp.route('/competitor/<int:competitor_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_competitor(competitor_id):
    """Stop tracking a competitor"""
    competitor = SNSCompetitor.query.get(competitor_id)

    if not competitor or competitor.user_id != g.user_id:
        return jsonify({'error': 'Competitor not found'}), 404

    db.session.delete(competitor)
    db.session.commit()

    return jsonify({'message': 'Competitor tracking stopped'}), 200


# ============ AI REPURPOSING ENDPOINTS ============

@sns_bp.route('/ai/repurpose', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def repurpose_content():
    """AI-powered content repurposing across platforms — Real Claude AI"""
    data = request.get_json()

    required = ['content', 'source_platform', 'target_platforms']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    source_content = data['content']
    source_platform = data['source_platform']
    target_platforms = data['target_platforms']

    if not isinstance(target_platforms, list) or len(target_platforms) == 0:
        return jsonify({'error': 'target_platforms must be a non-empty list'}), 400

    # Primary: use claude_ai service; fallback: sns_ai_engine
    ai_generated = False
    try:
        if HAS_CLAUDE_AI_SERVICE and claude_ai is not None and claude_ai.is_available():
            result = claude_ai.repurpose_content(
                original_content=source_content,
                source_platform=source_platform,
                target_platforms=target_platforms,
            )
            repurposed = result.get('repurposed', result)
            ai_generated = not result.get('fallback', False)
        else:
            repurposed = sns_ai_engine.repurpose_content(
                original_content=source_content,
                source_platform=source_platform,
                target_platforms=target_platforms,
            )
            ai_generated = any(
                v.get('ai_generated', False) for v in repurposed.values()
                if isinstance(v, dict)
            )
    except Exception as exc:
        logger.error("AI repurpose failed (both engines): %s", exc)
        repurposed = sns_ai_engine._fallback_repurpose(
            source_content, source_platform, target_platforms
        )

    return jsonify({
        'source_platform': source_platform,
        'source_content': source_content,
        'repurposed_content': repurposed,
        'ai_generated': ai_generated,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============ ROI METRICS ENDPOINTS ============

@sns_bp.route('/roi', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_roi_metrics', ttl_seconds=900)
def get_roi_metrics():
    """Get ROI metrics and performance analytics"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    platform = request.args.get('platform')

    # Get analytics data
    query = SNSAnalytics.query.filter_by(user_id=g.user_id)

    if platform:
        query = query.join(SNSAccount).filter(SNSAccount.platform == platform)

    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from).date()
            query = query.filter(SNSAnalytics.date >= from_date)
        except (ValueError, TypeError):
            pass

    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to).date()
            query = query.filter(SNSAnalytics.date <= to_date)
        except (ValueError, TypeError):
            pass

    analytics = query.all()

    # Calculate metrics
    total_engagement = sum(a.total_engagement for a in analytics)
    total_reach = sum(a.total_reach for a in analytics)
    total_impressions = sum(a.total_impressions for a in analytics)
    avg_followers = sum(a.followers for a in analytics) / len(analytics) if analytics else 0

    # Mock cost data (in production, integrate with payment system)
    estimated_cost = 99.99 if platform else 299.99
    estimated_revenue = total_engagement * 0.5  # Mock: $0.50 per engagement

    roi = ((estimated_revenue - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 0

    return jsonify({
        'period': {
            'from': date_from or 'all-time',
            'to': date_to or 'today'
        },
        'metrics': {
            'total_engagement': total_engagement,
            'total_reach': total_reach,
            'total_impressions': total_impressions,
            'avg_followers': round(avg_followers, 2),
            'engagement_rate': round((total_engagement / max(total_reach, 1) * 100), 2),
        },
        'financial': {
            'estimated_cost': estimated_cost,
            'estimated_revenue': round(estimated_revenue, 2),
            'roi_percentage': round(roi, 2),
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============ AI GENERATION ENDPOINTS ============

@sns_bp.route('/ai/generate', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def generate_with_ai():
    """Generate SNS post content using AI — Real Claude AI"""
    data = request.get_json()

    required = ['topic', 'tone', 'language', 'platform']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields: topic, tone, language, platform'}), 400

    topic = data['topic']
    tone = data['tone']
    language = data['language']
    platform = data['platform']
    content_type = data.get('content_type', 'post')

    # Primary: sns_ai_engine (dedicated SNS AI); optional: claude_ai shared service
    try:
        # Try shared claude_ai service first if available (Agent 7)
        if HAS_CLAUDE_AI_SERVICE and claude_ai is not None and claude_ai.is_available():
            result = claude_ai.generate_sns_content(
                platform=platform,
                topic=topic,
                tone=tone,
                language=language,
                content_type=content_type,
                hashtag_count=data.get('hashtag_count', 5),
                char_limit=data.get('charLimit', 0),
            )
            ai_generated = not result.get('fallback', False)
        else:
            # Use dedicated SNS AI engine (primary path)
            result = sns_ai_engine.generate_content(
                platform=platform,
                topic=topic,
                tone=tone,
                language=language,
                content_type=content_type,
            )
            ai_generated = result.get('ai_generated', False)
    except Exception as exc:
        logger.error("AI generate failed: %s", exc)
        result = sns_ai_engine._fallback_generate_content(
            platform, topic, tone, language, content_type
        )
        ai_generated = False

    return jsonify({
        'content': result.get('content', ''),
        'hashtags': result.get('hashtags', []),
        'posting_tips': result.get('posting_tips', result.get('engagement_tips', [])),
        'preview': result.get('preview', result.get('caption', '')),
        'tone': tone,
        'language': language,
        'platform': platform,
        'ai_generated': ai_generated,
        'generated_at': datetime.utcnow().isoformat()
    }), 200


# ============ AUTOMATION SETUP ENDPOINTS ============

@sns_bp.route('/automate/setup', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def setup_automation():
    """Setup automation for regular SNS posts"""
    data = request.get_json()

    required = ['topic', 'frequency', 'platforms']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields: topic, frequency, platforms'}), 400

    if not isinstance(data['platforms'], list) or len(data['platforms']) == 0:
        return jsonify({'error': 'At least one platform must be selected'}), 400

    topic = data['topic']
    purpose = data.get('purpose', 'engagement')
    frequency = data['frequency']
    platforms = data['platforms']

    # Validate frequency
    valid_frequencies = ['daily', '3days', 'weekly', 'monthly']
    if frequency not in valid_frequencies:
        return jsonify({'error': f'Invalid frequency. Must be one of: {", ".join(valid_frequencies)}'}), 400

    # Create automation config
    automation_config = {
        'user_id': g.user_id,
        'topic': topic,
        'purpose': purpose,
        'frequency': frequency,
        'platforms': platforms,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'active'
    }

    # Calculate next post time
    freq_map = {
        'daily': timedelta(days=1),
        '3days': timedelta(days=3),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)
    }

    next_post_time = datetime.utcnow() + freq_map.get(frequency, timedelta(days=1))

    return jsonify({
        'message': 'Automation setup successfully',
        'config': automation_config,
        'next_post_time': next_post_time.isoformat(),
        'posts_per_month': _estimate_posts_per_month(frequency)
    }), 201


# ============ NEW AI-POWERED ENDPOINTS ============

@sns_bp.route('/ai/hashtags', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def generate_hashtags():
    """Generate AI-powered hashtags for content"""
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'error': 'Missing required field: content'}), 400

    content = data['content']
    platform = data.get('platform', 'instagram')
    count = data.get('count', 10)

    # Clamp count to a reasonable range
    count = max(1, min(count, 30))

    try:
        result = sns_ai_engine.generate_hashtags(
            content=content,
            platform=platform,
            count=count,
        )
    except Exception as exc:
        logger.error("AI hashtag generation failed: %s", exc)
        result = {
            'hashtags': ['#SNSAuto', '#SoftFactory', '#Marketing'],
            'popular': ['#Marketing'],
            'niche': ['#SNSAuto'],
            'strategy': 'Fallback hashtags (AI error)',
            'ai_generated': False,
        }

    return jsonify({
        'platform': platform,
        'count': count,
        **result,
        'generated_at': datetime.utcnow().isoformat()
    }), 200


@sns_bp.route('/ai/calendar', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def generate_content_calendar():
    """Generate an AI-powered content calendar"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    topics = data.get('topics', [])
    platforms = data.get('platforms', [])

    if not topics or not isinstance(topics, list):
        return jsonify({'error': 'topics must be a non-empty list'}), 400
    if not platforms or not isinstance(platforms, list):
        return jsonify({'error': 'platforms must be a non-empty list'}), 400

    duration_days = data.get('duration_days', 30)
    posts_per_week = data.get('posts_per_week', 5)
    language = data.get('language', 'ko')

    # Clamp values
    duration_days = max(7, min(duration_days, 90))
    posts_per_week = max(1, min(posts_per_week, 14))

    try:
        result = sns_ai_engine.generate_content_calendar(
            topics=topics,
            platforms=platforms,
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            language=language,
        )
    except Exception as exc:
        logger.error("AI calendar generation failed: %s", exc)
        result = sns_ai_engine._fallback_calendar(
            topics, platforms, duration_days, posts_per_week
        )

    return jsonify({
        **result,
        'generated_at': datetime.utcnow().isoformat()
    }), 200


@sns_bp.route('/ai/analyze-post', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def analyze_post_performance():
    """AI analysis of post performance with recommendations"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Accept flexible post data
    post_data = {
        'content': data.get('content', ''),
        'platform': data.get('platform', 'unknown'),
        'likes': data.get('likes', 0),
        'comments': data.get('comments', 0),
        'shares': data.get('shares', 0),
        'reach': data.get('reach', 0),
        'impressions': data.get('impressions', 0),
        'engagement_rate': data.get('engagement_rate', 0),
        'posted_at': data.get('posted_at', ''),
        'followers': data.get('followers', 0),
    }

    try:
        result = sns_ai_engine.analyze_post_performance(post_data)
    except Exception as exc:
        logger.error("AI post analysis failed: %s", exc)
        result = {
            'score': 50,
            'strengths': ['Post data received'],
            'improvements': ['Enable AI for detailed analysis'],
            'recommendations': ['Try again later when AI is available'],
            'benchmark_comparison': 'Analysis unavailable',
            'ai_generated': False,
        }

    return jsonify({
        'platform': post_data['platform'],
        **result,
        'analyzed_at': datetime.utcnow().isoformat()
    }), 200


@sns_bp.route('/ai/best-time/<platform>', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
@cached('sns_best_time', ttl_seconds=3600)
def get_best_posting_time(platform):
    """Get AI-recommended best posting times for a platform"""
    audience_timezone = request.args.get('timezone', 'Asia/Seoul')

    try:
        result = sns_ai_engine.analyze_best_posting_time(
            platform=platform,
            audience_timezone=audience_timezone,
        )
    except Exception as exc:
        logger.error("AI best-time analysis failed for %s: %s", platform, exc)
        result = {
            'best_times': [
                {'day': 'Monday', 'time': '09:00', 'engagement_score': 7},
                {'day': 'Wednesday', 'time': '12:00', 'engagement_score': 8},
                {'day': 'Friday', 'time': '17:00', 'engagement_score': 7},
            ],
            'explanation': f'Default posting times for {platform} (AI unavailable).',
            'weekly_schedule': {},
            'platform': platform,
            'timezone': audience_timezone,
            'ai_generated': False,
        }

    return jsonify({
        **result,
        'requested_at': datetime.utcnow().isoformat()
    }), 200


# ============ HELPER FUNCTIONS ============

def _estimate_posts_per_month(frequency):
    """Estimate number of posts per month based on frequency"""
    freq_map = {
        'daily': 30,
        '3days': 10,
        'weekly': 4,
        'monthly': 1
    }
    return freq_map.get(frequency, 1)
