"""Search API Routes - Full-Featured Search Endpoints.

Handles recipe, SNS post, and user searches with advanced filtering and
defensive input validation for reliability.
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from ..auth import require_auth
from .elasticsearch_service import get_search_manager
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

VALID_SEARCH_INDEXES = {'recipes', 'sns_posts', 'users'}
VALID_SORT_OPTIONS = {'relevance', 'rating', 'popularity', 'newest'}
AUTOCOMPLETE_FIELDS = {
    'recipes': ['title', 'ingredients', 'tags'],
    'sns_posts': ['content', 'caption', 'hashtags'],
    'users': ['name', 'email'],
}
FACET_FIELDS = {
    'recipes': ['difficulty', 'tags', 'cuisine_type'],
    'sns_posts': ['platform', 'hashtags'],
    'users': ['role'],
}
ADVANCED_FIELDS = {
    'recipes': {'title', 'content', 'tags', 'difficulty', 'cooking_time', 'rating'},
    'sns_posts': {'content', 'caption', 'hashtags', 'platform', 'engagement_rate'},
    'users': {'name', 'email', 'bio', 'role'},
}
ADVANCED_OPERATORS = {'must', 'should', 'gte', 'lte'}

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def _search_manager_or_503():
    """Return search manager or a 503 response tuple if unavailable."""
    try:
        return get_search_manager(), None
    except RuntimeError:
        return None, (jsonify({'error': 'Search service not available'}), 503)


def _safe_int(value, default, minimum=1, maximum=None):
    """Parse integer input safely and clamp to a range."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    if maximum is not None and parsed > maximum:
        return maximum
    return parsed


def _error_response(message, status_code, details=None):
    """Build a safe error response."""
    if details:
        logger.warning('%s: %s', message, details)
    return jsonify({'error': message}), status_code


@search_bp.route('', methods=['POST'])
@require_auth
def search():
    """
    Full-text search across indices.

    POST /api/search
    {
        "query": "pasta recipe",
        "index": "recipes",
        "filters": {
            "difficulty": "easy",
            "cooking_time_max": 30,
            "calories_range": [100, 500],
            "rating_min": 4.0,
            "tags": ["vegetarian", "quick"]
        },
        "sort": "relevance",
        "page": 1,
        "per_page": 20
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return _error_response('Invalid request payload', 400)

        query = (data.get('query') or '').strip()
        index = data.get('index', 'recipes')
        filters = data.get('filters', {})
        sort = data.get('sort', 'relevance')
        page = _safe_int(data.get('page', 1), 1, minimum=1)
        per_page = _safe_int(data.get('per_page', DEFAULT_PER_PAGE),
                             DEFAULT_PER_PAGE,
                             minimum=1,
                             maximum=MAX_PER_PAGE)

        if not query:
            return _error_response('Query required', 400)
        if index not in VALID_SEARCH_INDEXES:
            return _error_response('Invalid index', 400)
        if sort not in VALID_SORT_OPTIONS:
            return _error_response('Invalid sort', 400)
        if not isinstance(filters, dict):
            return _error_response('filters must be an object', 400)

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable

        user_id = g.user.id

        if index == 'recipes':
            results = search_manager.search_recipes(
                query=query,
                filters=filters,
                page=page,
                sort=sort,
                per_page=per_page,
            )
        elif index == 'sns_posts':
            results = search_manager.search_posts(
                query=query,
                platform=filters.get('platform'),
                date_range=filters.get('date_range'),
                page=page,
                per_page=per_page,
            )
        else:
            results = search_manager.search_users(
                query=query,
                role=filters.get('role'),
                page=page,
                per_page=per_page,
            )

        # Save search history
        search_manager.save_search_history(user_id, query, index, results.get('total', 0))

        return jsonify({
            'query': query,
            'index': index,
            'total': results['total'],
            'page': page,
            'per_page': per_page,
            'results': results['results'],
            'took_ms': results['took']
        }), 200

    except Exception as e:
        logger.error('Search error: %s', e)
        return _error_response('Search failed', 500)


@search_bp.route('/autocomplete', methods=['GET'])
@require_auth
def autocomplete():
    """
    Autocomplete suggestions for search fields.

    GET /api/search/autocomplete?q=pas&field=title&index=recipes
    """
    try:
        q = (request.args.get('q') or '').strip()
        field = request.args.get('field', 'title')
        index = request.args.get('index', 'recipes')
        limit = _safe_int(request.args.get('limit', 10), 10, minimum=1, maximum=20)

        if not q or len(q) < 2:
            return jsonify({'suggestions': []}), 200
        if index not in VALID_SEARCH_INDEXES:
            return _error_response('Invalid index', 400)

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable

        if field not in AUTOCOMPLETE_FIELDS.get(index, []):
            field = AUTOCOMPLETE_FIELDS.get(index, ['content'])[0]

        suggestions = search_manager.autocomplete(index, field, q, limit)

        return jsonify({
            'query': q,
            'field': field,
            'suggestions': suggestions
        }), 200

    except Exception as e:
        logger.error('Autocomplete error: %s', e)
        return _error_response('Autocomplete failed', 500)


@search_bp.route('/facets', methods=['GET'])
@require_auth
def get_facets():
    """
    Get available filter values (facets) for the current search.

    GET /api/search/facets?index=recipes&field=tags&q=pasta
    """
    try:
        index = request.args.get('index', 'recipes')
        field = request.args.get('field', 'tags')
        q = request.args.get('q', '')

        if index not in VALID_SEARCH_INDEXES:
            return _error_response('Invalid index', 400)
        if field not in FACET_FIELDS.get(index, []):
            return _error_response('Invalid field for index', 400)

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable

        facets = search_manager.get_facets(index, field, q)
        return jsonify({
            'index': index,
            'field': field,
            'facets': facets,
            'total': len(facets)
        }), 200

    except Exception as e:
        logger.error('Facets error: %s', e)
        return _error_response('Failed to get facets', 500)


@search_bp.route('/history', methods=['GET'])
@require_auth
def search_history():
    """
    Get user's search history for personalization.

    GET /api/search/history?limit=10
    """
    try:
        limit = _safe_int(request.args.get('limit', 10), 10, minimum=1, maximum=50)
        user_id = g.user.id

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable

        history = search_manager.get_search_suggestions(user_id, limit)
        return jsonify({'history': history, 'total': len(history)}), 200

    except Exception as e:
        logger.error('History error: %s', e)
        return _error_response('Failed to get search history', 500)


@search_bp.route('/trending', methods=['GET'])
@require_auth
def trending_searches():
    """
    Get trending search queries.

    GET /api/search/trending?days=7&limit=20
    """
    try:
        from ..models import db, SearchHistory

        days = _safe_int(request.args.get('days', 7), 7, minimum=1, maximum=365)
        limit = _safe_int(request.args.get('limit', 20), 20, minimum=1, maximum=100)
        since = datetime.utcnow() - timedelta(days=days)
        query_text_col = SearchHistory.__table__.c['query']

        trending = db.session.query(
            query_text_col.label('query'),
            SearchHistory.index,
            db.func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.created_at >= since
        ).group_by(
            query_text_col,
            SearchHistory.index
        ).order_by(
            db.desc('count')
        ).limit(limit).all()

        return jsonify({
            'days': days,
            'trending': [{'query': q, 'index': idx, 'count': cnt} for q, idx, cnt in trending],
            'total': len(trending)
        }), 200

    except Exception as e:
        logger.error('Trending searches error: %s', e)
        return _error_response('Failed to get trending searches', 500)


@search_bp.route('/advanced', methods=['POST'])
@require_auth
def advanced_search():
    """
    Advanced search with complex filters and boolean operators.

    POST /api/search/advanced
    {
        "queries": [
            {"field": "title", "value": "pasta", "operator": "must"},
            {"field": "difficulty", "value": "easy", "operator": "must"},
            {"field": "rating", "value": 4.0, "operator": "gte"}
        ],
        "index": "recipes",
        "sort": "relevance",
        "page": 1,
        "per_page": 20
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return _error_response('Invalid request payload', 400)

        queries = data.get('queries', [])
        index = data.get('index', 'recipes')
        sort = data.get('sort', 'relevance')
        page = _safe_int(data.get('page', 1), 1, minimum=1)
        per_page = _safe_int(data.get('per_page', DEFAULT_PER_PAGE),
                             DEFAULT_PER_PAGE,
                             minimum=1,
                             maximum=MAX_PER_PAGE)

        if not isinstance(queries, list) or not queries:
            return _error_response('At least one query is required', 400)
        if index not in VALID_SEARCH_INDEXES:
            return _error_response('Invalid index', 400)
        if sort not in VALID_SORT_OPTIONS:
            return _error_response('Invalid sort', 400)

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable
        _ = g.user.id

        must_clauses = []
        filter_clauses = []

        for q in queries:
            if not isinstance(q, dict):
                return _error_response('Each query must be an object', 400)
            field = q.get('field')
            value = q.get('value')
            operator = q.get('operator', 'must')

            if field not in ADVANCED_FIELDS.get(index, set()):
                return _error_response('Invalid query field', 400)
            if operator not in ADVANCED_OPERATORS:
                return _error_response('Invalid query operator', 400)
            if operator in ('must', 'should'):
                if value in (None, ''):
                    continue
                must_clauses.append({'match': {field: value}})
            elif operator == 'gte':
                filter_clauses.append({'range': {field: {'gte': value}}})
            elif operator == 'lte':
                filter_clauses.append({'range': {field: {'lte': value}}})

        if not must_clauses and not filter_clauses:
            return _error_response('No usable query clauses', 400)

        es_query = {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses,
                }
            }
        }

        from_offset = (page - 1) * per_page
        results = search_manager.es.search(
            index=index,
            body=es_query,
            size=per_page,
            from_=from_offset
        )
        formatted = search_manager._format_results(results)

        return jsonify({
            'total': formatted['total'],
            'results': formatted['results'],
            'took_ms': formatted['took'],
            'page': page,
            'per_page': per_page,
        }), 200

    except Exception as e:
        logger.error('Advanced search error: %s', e)
        return _error_response('Advanced search failed', 500)


@search_bp.route('/similar', methods=['GET'])
@require_auth
def similar_items():
    """
    Find items similar to a given item.

    GET /api/search/similar?index=recipes&id=123
    """
    try:
        index = request.args.get('index', 'recipes')
        item_id = request.args.get('id')

        if not item_id:
            return _error_response('Item ID required', 400)
        if index not in VALID_SEARCH_INDEXES:
            return _error_response('Invalid index', 400)

        search_manager, unavailable = _search_manager_or_503()
        if unavailable:
            return unavailable

        query = {
            'query': {
                'more_like_this': {
                    'fields': ['title', 'content', 'tags', 'ingredients'],
                    'like': [{'_index': index, '_id': item_id}],
                    'min_term_freq': 1,
                    'max_query_terms': 12
                }
            }
        }

        results = search_manager.search(index, query, size=10)
        formatted = search_manager._format_results(results)

        return jsonify({
            'similar_to_id': item_id,
            'results': formatted['results']
        }), 200

    except Exception as e:
        logger.error('Similar items error: %s', e)
        return _error_response('Similar items search failed', 500)


def register_search_routes(app):
    """Register search blueprint with Flask app."""
    app.register_blueprint(search_bp)
