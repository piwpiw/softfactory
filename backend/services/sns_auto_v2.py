"""SNS Auto Service v2.0 - Advanced Endpoints with Performance Optimization

Enhanced features:
- Pagination (cursor-based + field filtering)
- Advanced caching with invalidation
- Rate limiting by plan
- Error handling with retry
- Conditional requests (ETag)
- Monitoring & metrics
"""

from flask import Blueprint, request, jsonify, g, make_response
from datetime import datetime, timedelta
import json
from functools import wraps

from backend.models import (
    db, SNSAccount, SNSPost, SNSCampaign, SNSTemplate, SNSAnalytics,
    SNSInboxMessage, SNSOAuthState, SNSSettings, User
)
from backend.auth import require_auth, get_current_user
from backend.middleware.rate_limiter import rate_limit_by_plan
from backend.utils.cache_manager import (
    get_cache, cached_endpoint, conditional_response, ETagGenerator
)
from backend.utils.pagination import (
    CursorPagination, OffsetPagination, FieldFilter, PaginationMixin
)
from backend.utils.retry_handler import (
    retry_with_backoff, PlatformCircuitBreaker
)

sns_v2_bp = Blueprint('sns_v2', __name__, url_prefix='/api/v2/sns')


# ============ HELPER FUNCTIONS ============

def get_current_user_from_auth():
    """Get current user from JWT token"""
    try:
        return get_current_user()
    except:
        return None


def build_pagination_response(items, has_more=False, next_cursor=None, pagination_type='cursor'):
    """Build standardized pagination response"""
    return {
        'success': True,
        'data': items,
        'pagination': {
            'has_more': has_more,
            'next_cursor': next_cursor,
            'count': len(items)
        } if pagination_type == 'cursor' else {
            'page': pagination_type.get('page', 1),
            'per_page': len(items),
            'total': pagination_type.get('total', 0),
            'pages': pagination_type.get('pages', 1)
        }
    }


# ============ LINKINBIO ENDPOINTS (with optimization) ============

@sns_v2_bp.route('/linkinbio', methods=['GET'])
@require_auth
@cached_endpoint(ttl=300)
@rate_limit_by_plan
def get_linkinbio(user_id):
    """Get user's LinkInBio with pagination and field filtering"""
    try:
        # Parse pagination
        pagination_type = request.args.get('pagination', 'cursor')
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 100)  # Cap at 100

        # Parse field filter
        fields = FieldFilter.get_requested_fields()

        if pagination_type == 'cursor':
            cursor = request.args.get('cursor', type=int)
            query = SNSLinkInBio.query.filter_by(user_id=user_id).order_by(SNSLinkInBio.created_at.desc())

            if cursor:
                query = query.filter(SNSLinkInBio.id > cursor)

            items, has_more, next_cursor = CursorPagination.paginate_query(query, per_page, cursor)
            data = [FieldFilter.filter_dict(item.to_dict(), fields) for item in items]

            return build_pagination_response(data, has_more, next_cursor, 'cursor')
        else:
            page = request.args.get('page', 1, type=int)
            query = SNSLinkInBio.query.filter_by(user_id=user_id).order_by(SNSLinkInBio.created_at.desc())

            items, page, total, pages = OffsetPagination.paginate_query(query, page, per_page)
            data = [FieldFilter.filter_dict(item.to_dict(), fields) for item in items]

            return build_pagination_response(data, pagination_type={
                'page': page,
                'total': total,
                'pages': pages
            })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@sns_v2_bp.route('/linkinbio/<int:id>', methods=['GET'])
@require_auth
@conditional_response
def get_linkinbio_detail(id, user_id):
    """Get LinkInBio detail with ETag support"""
    try:
        linkinbio = SNSLinkInBio.query.filter_by(id=id, user_id=user_id).first_or_404()

        # Parse field filter
        fields = FieldFilter.get_requested_fields()
        data = FieldFilter.filter_dict(linkinbio.to_dict(), fields)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ POSTS ENDPOINTS (with pagination & caching) ============

@sns_v2_bp.route('/posts', methods=['GET'])
@require_auth
@cached_endpoint(ttl=300)
@rate_limit_by_plan
def get_posts(user_id):
    """Get user's posts with advanced pagination"""
    try:
        # Pagination
        pagination_type = request.args.get('pagination', 'cursor')
        per_page = min(request.args.get('per_page', 50, type=int), 100)

        # Filters
        platform_filter = request.args.get('platform')
        status_filter = request.args.get('status')  # draft, scheduled, published
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Build query
        query = SNSPost.query.filter_by(user_id=user_id)

        if platform_filter:
            query = query.filter_by(platform=platform_filter)
        if status_filter:
            query = query.filter_by(status=status_filter)
        if date_from:
            query = query.filter(SNSPost.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(SNSPost.created_at <= datetime.fromisoformat(date_to))

        query = query.order_by(SNSPost.created_at.desc())

        # Pagination
        if pagination_type == 'cursor':
            cursor = request.args.get('cursor', type=int)
            items, has_more, next_cursor = CursorPagination.paginate_query(query, per_page, cursor)
            return build_pagination_response(
                [item.to_dict() for item in items],
                has_more,
                next_cursor,
                'cursor'
            )
        else:
            page = request.args.get('page', 1, type=int)
            items, page, total, pages = OffsetPagination.paginate_query(query, page, per_page)
            return build_pagination_response(
                [item.to_dict() for item in items],
                pagination_type={'page': page, 'total': total, 'pages': pages}
            )

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@sns_v2_bp.route('/posts/<int:post_id>/retry', methods=['POST'])
@require_auth
@rate_limit_by_plan
def retry_post(post_id, user_id):
    """Retry publishing failed post with exponential backoff"""
    try:
        post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first_or_404()

        if post.status == 'published':
            return jsonify({'error': 'Post already published', 'success': False}), 400

        # Use retry handler
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def publish_with_retry():
            # Simulate platform publishing with circuit breaker
            platform = post.platform
            return PlatformCircuitBreaker.call_with_circuit_break(
                platform,
                lambda: {'success': True, 'platform_id': f'post_{post.id}'}
            )

        result = publish_with_retry()

        # Update post
        post.status = 'published'
        post.published_at = datetime.utcnow()
        db.session.commit()

        # Invalidate cache
        get_cache().invalidate('post_published', user_id=user_id)

        return jsonify({'success': True, 'data': post.to_dict()})

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ ANALYTICS ENDPOINTS (with caching) ============

@sns_v2_bp.route('/analytics', methods=['GET'])
@require_auth
@cached_endpoint(ttl=600)
@rate_limit_by_plan
def get_analytics(user_id):
    """Get aggregated analytics with caching"""
    try:
        # Date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()

        # Query analytics
        analytics = SNSAnalytics.query.filter_by(user_id=user_id).filter(
            SNSAnalytics.date >= start_date,
            SNSAnalytics.date <= end_date
        ).all()

        # Aggregate
        total_followers = sum(a.followers for a in analytics) if analytics else 0
        total_engagement = sum(a.engagement for a in analytics) if analytics else 0
        total_reach = sum(a.reach for a in analytics) if analytics else 0

        # By platform
        by_platform = {}
        for a in analytics:
            if a.platform not in by_platform:
                by_platform[a.platform] = {'followers': 0, 'engagement': 0, 'reach': 0}
            by_platform[a.platform]['followers'] += a.followers
            by_platform[a.platform]['engagement'] += a.engagement
            by_platform[a.platform]['reach'] += a.reach

        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'totals': {
                    'followers': total_followers,
                    'engagement': total_engagement,
                    'reach': total_reach
                },
                'by_platform': by_platform,
                'average_engagement_rate': (
                    (total_engagement / total_reach * 100) if total_reach > 0 else 0
                )
            }
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ ACCOUNTS ENDPOINTS (with cache invalidation) ============

@sns_v2_bp.route('/accounts', methods=['GET'])
@require_auth
@cached_endpoint(ttl=300)
@rate_limit_by_plan
def get_accounts(user_id):
    """Get connected accounts with field filtering"""
    try:
        # Pagination
        per_page = min(request.args.get('per_page', 50, type=int), 100)

        # Field filter
        fields = FieldFilter.get_requested_fields()

        # Query
        accounts = SNSAccount.query.filter_by(user_id=user_id).all()
        data = [FieldFilter.filter_dict(acc.to_dict(), fields) for acc in accounts]

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@sns_v2_bp.route('/accounts', methods=['POST'])
@require_auth
@rate_limit_by_plan
def create_account(user_id):
    """Create account and invalidate cache"""
    try:
        data = request.get_json()

        account = SNSAccount(
            user_id=user_id,
            platform=data['platform'],
            account_name=data['account_name']
        )

        db.session.add(account)
        db.session.commit()

        # Invalidate cache
        get_cache().invalidate('accounts', user_id=user_id)
        get_cache().invalidate('analytics', user_id=user_id)

        return jsonify({'success': True, 'data': account.to_dict()}), 201

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ CACHE MANAGEMENT ENDPOINTS ============

@sns_v2_bp.route('/cache/stats', methods=['GET'])
@require_auth
def get_cache_stats(user_id):
    """Get cache statistics (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403

        stats = get_cache().stats()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@sns_v2_bp.route('/cache/invalidate', methods=['POST'])
@require_auth
def invalidate_cache(user_id):
    """Manually invalidate cache"""
    try:
        data = request.get_json()
        event_type = data.get('event')

        if not event_type:
            return jsonify({'error': 'Missing event parameter', 'success': False}), 400

        get_cache().invalidate(event_type, user_id=user_id)

        return jsonify({
            'success': True,
            'message': f'Cache invalidated for {event_type}'
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ CIRCUIT BREAKER STATUS ============

@sns_v2_bp.route('/health/circuit-breaker', methods=['GET'])
@require_auth
def get_circuit_breaker_status(user_id):
    """Get status of all circuit breakers"""
    try:
        status = PlatformCircuitBreaker.get_status()

        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============ API VERSIONING ============

# Note: Keep v1 endpoints working for backward compatibility
# v2 endpoints are enhanced with better pagination, caching, and error handling
