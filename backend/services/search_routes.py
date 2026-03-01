"""Search API Routes - Full-Featured Search Endpoints
Handles recipe, SNS post, and user searches with advanced filtering
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from ..auth import require_auth
from .elasticsearch_service import get_search_manager
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.before_request
def before_search_request():
    """Validate search is available"""
    try:
        get_search_manager()
    except RuntimeError:
        return jsonify({'error': 'Search service not available'}), 503


@search_bp.route('', methods=['POST'])
@require_auth
def search():
    """
    Full-text search across indices

    POST /api/search
    {
        "query": "pasta recipe",
        "index": "recipes",  # 'recipes', 'sns_posts', 'users'
        "filters": {
            "difficulty": "easy",
            "cooking_time_max": 30,
            "calories_range": [100, 500],
            "rating_min": 4.0,
            "tags": ["vegetarian", "quick"]
        },
        "sort": "relevance",  # 'relevance', 'rating', 'popularity', 'newest'
        "page": 1,
        "per_page": 20
    }
    """
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        index = data.get('index', 'recipes')
        filters = data.get('filters', {})
        sort = data.get('sort', 'relevance')
        page = max(1, int(data.get('page', 1)))
        per_page = min(100, int(data.get('per_page', 20)))

        if not query:
            return jsonify({'error': 'Query required'}), 400

        if index not in ['recipes', 'sns_posts', 'users']:
            return jsonify({'error': 'Invalid index'}), 400

        search_manager = get_search_manager()
        user_id = request.g.user.id

        # Execute search
        if index == 'recipes':
            results = search_manager.search_recipes(query, filters, page, sort)
        elif index == 'sns_posts':
            results = search_manager.search_posts(query, filters.get('platform'),
                                                  filters.get('date_range'), page)
        else:  # users
            results = search_manager.search_users(query, filters.get('role'), page)

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
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed', 'message': str(e)}), 500


@search_bp.route('/autocomplete', methods=['GET'])
@require_auth
def autocomplete():
    """
    Autocomplete suggestions for search fields

    GET /api/search/autocomplete?q=pas&field=title&index=recipes
    """
    try:
        q = request.args.get('q', '').strip()
        field = request.args.get('field', 'title')
        index = request.args.get('index', 'recipes')
        limit = min(20, int(request.args.get('limit', 10)))

        if not q or len(q) < 2:
            return jsonify({'suggestions': []}), 200

        if index not in ['recipes', 'sns_posts', 'users']:
            return jsonify({'error': 'Invalid index'}), 400

        search_manager = get_search_manager()

        # Map fields based on index
        field_map = {
            'recipes': ['title', 'ingredients', 'tags'],
            'sns_posts': ['content', 'caption', 'hashtags'],
            'users': ['name', 'email']
        }

        if field not in field_map.get(index, []):
            field = field_map.get(index, ['content'])[0]

        suggestions = search_manager.autocomplete(index, field, q, limit)

        return jsonify({
            'query': q,
            'field': field,
            'suggestions': suggestions
        }), 200

    except Exception as e:
        logger.error(f"Autocomplete error: {str(e)}")
        return jsonify({'error': 'Autocomplete failed'}), 500


@search_bp.route('/facets', methods=['GET'])
@require_auth
def get_facets():
    """
    Get available filter values (facets) for the current search

    GET /api/search/facets?index=recipes&field=tags&q=pasta
    """
    try:
        index = request.args.get('index', 'recipes')
        field = request.args.get('field', 'tags')
        q = request.args.get('q', '')

        if index not in ['recipes', 'sns_posts', 'users']:
            return jsonify({'error': 'Invalid index'}), 400

        # Validate field based on index
        valid_fields = {
            'recipes': ['difficulty', 'tags', 'cuisine_type'],
            'sns_posts': ['platform', 'hashtags'],
            'users': ['role']
        }

        if field not in valid_fields.get(index, []):
            return jsonify({'error': 'Invalid field for index'}), 400

        search_manager = get_search_manager()
        facets = search_manager.get_facets(index, field, q)

        return jsonify({
            'index': index,
            'field': field,
            'facets': facets,
            'total': len(facets)
        }), 200

    except Exception as e:
        logger.error(f"Facets error: {str(e)}")
        return jsonify({'error': 'Failed to get facets'}), 500


@search_bp.route('/history', methods=['GET'])
@require_auth
def search_history():
    """
    Get user's search history for personalization

    GET /api/search/history?limit=10
    """
    try:
        limit = min(50, int(request.args.get('limit', 10)))
        user_id = request.g.user.id

        search_manager = get_search_manager()
        history = search_manager.get_search_suggestions(user_id, limit)

        return jsonify({
            'history': history,
            'total': len(history)
        }), 200

    except Exception as e:
        logger.error(f"History error: {str(e)}")
        return jsonify({'error': 'Failed to get search history'}), 500


@search_bp.route('/trending', methods=['GET'])
@require_auth
def trending_searches():
    """
    Get trending search queries

    GET /api/search/trending?days=7&limit=20
    """
    try:
        from ..models import db, SearchHistory

        days = int(request.args.get('days', 7))
        limit = min(100, int(request.args.get('limit', 20)))

        since = datetime.utcnow() - timedelta(days=days)

        # Get most frequent queries from SearchHistory
        trending = db.session.query(
            SearchHistory.query,
            SearchHistory.index,
            db.func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.created_at >= since
        ).group_by(
            SearchHistory.query,
            SearchHistory.index
        ).order_by(
            db.desc('count')
        ).limit(limit).all()

        return jsonify({
            'days': days,
            'trending': [
                {
                    'query': q,
                    'index': idx,
                    'count': cnt
                }
                for q, idx, cnt in trending
            ],
            'total': len(trending)
        }), 200

    except Exception as e:
        logger.error(f"Trending searches error: {str(e)}")
        return jsonify({'error': 'Failed to get trending searches'}), 500


@search_bp.route('/advanced', methods=['POST'])
@require_auth
def advanced_search():
    """
    Advanced search with complex filters and boolean operators

    POST /api/search/advanced
    {
        "queries": [
            {"field": "title", "value": "pasta", "operator": "must"},
            {"field": "difficulty", "value": "easy", "operator": "must"},
            {"field": "rating", "value": 4.0, "operator": "gte"}
        ],
        "index": "recipes",
        "sort": "relevance"
    }
    """
    try:
        data = request.get_json() or {}
        queries = data.get('queries', [])
        index = data.get('index', 'recipes')
        sort = data.get('sort', 'relevance')
        page = max(1, int(data.get('page', 1)))

        if not queries:
            return jsonify({'error': 'At least one query is required'}), 400

        search_manager = get_search_manager()
        user_id = request.g.user.id

        # Build advanced ES query
        must_clauses = []
        filter_clauses = []

        for q in queries:
            field = q.get('field')
            value = q.get('value')
            operator = q.get('operator', 'must')

            if operator == 'must':
                must_clauses.append({'match': {field: value}})
            elif operator == 'should':
                must_clauses.append({'match': {field: value}})
            elif operator == 'gte':
                filter_clauses.append({'range': {field: {'gte': value}}})
            elif operator == 'lte':
                filter_clauses.append({'range': {field: {'lte': value}}})

        es_query = {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses
                }
            }
        }

        results = search_manager.es.search(
            index=index,
            body=es_query,
            size=20,
            from_=(page - 1) * 20
        )

        formatted = search_manager._format_results(results)

        return jsonify({
            'total': formatted['total'],
            'results': formatted['results'],
            'took_ms': formatted['took']
        }), 200

    except Exception as e:
        logger.error(f"Advanced search error: {str(e)}")
        return jsonify({'error': 'Advanced search failed'}), 500


@search_bp.route('/similar', methods=['GET'])
@require_auth
def similar_items():
    """
    Find items similar to a given item

    GET /api/search/similar?index=recipes&id=123
    """
    try:
        index = request.args.get('index', 'recipes')
        item_id = request.args.get('id')

        if not item_id:
            return jsonify({'error': 'Item ID required'}), 400

        search_manager = get_search_manager()

        # Use more_like_this query
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
        logger.error(f"Similar items error: {str(e)}")
        return jsonify({'error': 'Similar items search failed'}), 500


# Add route to app
def register_search_routes(app):
    """Register search blueprint with Flask app"""
    app.register_blueprint(search_bp)
