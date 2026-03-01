"""Search Administration - Index management endpoints
Provides admin endpoints for reindexing, clearing, and monitoring search indices
"""

from flask import Blueprint, request, jsonify
from ..auth import require_admin
from .elasticsearch_service import get_search_manager
from .search_indexer import index_all, index_recipes, index_sns_posts, index_users
import logging

logger = logging.getLogger(__name__)

search_admin_bp = Blueprint('search_admin', __name__, url_prefix='/api/admin/search')


@search_admin_bp.route('/indices', methods=['GET'])
@require_admin
def list_indices():
    """Get status of all search indices"""
    try:
        search_manager = get_search_manager()

        indices = ['recipes', 'sns_posts', 'users']
        status = {}

        for index in indices:
            try:
                # Get index stats
                stats = search_manager.es.es.indices.stats(index=index)
                count_response = search_manager.es.es.count(index=index)

                status[index] = {
                    'exists': True,
                    'doc_count': count_response.get('count', 0),
                    'store_size': stats['indices'][index]['primaries']['store']['size_in_bytes']
                }
            except:
                status[index] = {
                    'exists': False,
                    'doc_count': 0,
                    'store_size': 0
                }

        return jsonify({
            'indices': status,
            'total_docs': sum(s['doc_count'] for s in status.values())
        }), 200

    except Exception as e:
        logger.error(f"Failed to list indices: {str(e)}")
        return jsonify({'error': 'Failed to get index status'}), 500


@search_admin_bp.route('/reindex', methods=['POST'])
@require_admin
def reindex():
    """Reindex all content from database"""
    try:
        data = request.get_json() or {}
        scope = data.get('scope', 'all')  # 'all', 'recipes', 'posts', 'users'

        if scope == 'recipes':
            result = index_recipes()
        elif scope == 'posts':
            result = index_sns_posts()
        elif scope == 'users':
            result = index_users()
        else:
            result = index_all()

        return jsonify({
            'status': 'success',
            'scope': scope,
            'indexed': result if isinstance(result, dict) else {'count': result}
        }), 200

    except Exception as e:
        logger.error(f"Reindex failed: {str(e)}")
        return jsonify({'error': 'Reindex failed', 'message': str(e)}), 500


@search_admin_bp.route('/clear', methods=['POST'])
@require_admin
def clear_index():
    """Clear all documents from an index"""
    try:
        data = request.get_json() or {}
        index = data.get('index', 'recipes')

        if index not in ['recipes', 'sns_posts', 'users']:
            return jsonify({'error': 'Invalid index'}), 400

        search_manager = get_search_manager()

        # Delete all docs with a delete_by_query
        query = {'query': {'match_all': {}}}
        response = search_manager.es.es.delete_by_query(index=index, body=query)

        return jsonify({
            'status': 'success',
            'index': index,
            'deleted': response.get('deleted', 0)
        }), 200

    except Exception as e:
        logger.error(f"Clear index failed: {str(e)}")
        return jsonify({'error': 'Clear failed'}), 500


@search_admin_bp.route('/reset', methods=['POST'])
@require_admin
def reset_indices():
    """Drop and recreate all indices (full reset)"""
    try:
        search_manager = get_search_manager()

        for index in ['recipes', 'sns_posts', 'users']:
            search_manager.delete_index(index)

        # Recreate indices
        search_manager.create_indices()

        return jsonify({
            'status': 'success',
            'message': 'All indices reset successfully'
        }), 200

    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        return jsonify({'error': 'Reset failed'}), 500


@search_admin_bp.route('/stats', methods=['GET'])
@require_admin
def search_stats():
    """Get search performance and usage statistics"""
    try:
        from ..models import db, SearchHistory
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get search statistics from database
        days = int(request.args.get('days', 7))
        since = datetime.utcnow() - timedelta(days=days)

        # Total searches
        total = db.session.query(func.count(SearchHistory.id)).filter(
            SearchHistory.created_at >= since
        ).scalar() or 0

        # By index
        by_index = db.session.query(
            SearchHistory.index,
            func.count(SearchHistory.id).label('count'),
            func.avg(SearchHistory.result_count).label('avg_results')
        ).filter(
            SearchHistory.created_at >= since
        ).group_by(
            SearchHistory.index
        ).all()

        # Popular queries
        popular = db.session.query(
            SearchHistory.query,
            func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.created_at >= since
        ).group_by(
            SearchHistory.query
        ).order_by(
            func.count(SearchHistory.id).desc()
        ).limit(20).all()

        return jsonify({
            'period_days': days,
            'total_searches': total,
            'by_index': [
                {
                    'index': idx,
                    'count': cnt,
                    'avg_results': float(avg_res or 0)
                }
                for idx, cnt, avg_res in by_index
            ],
            'popular_queries': [
                {'query': q, 'count': c}
                for q, c in popular
            ]
        }), 200

    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500


@search_admin_bp.route('/health', methods=['GET'])
@require_admin
def search_health():
    """Check Elasticsearch cluster health"""
    try:
        search_manager = get_search_manager()

        # Get cluster health
        health = search_manager.es.es.cluster.health()

        # Get indices status
        indices_status = search_manager.es.es.indices.status()

        return jsonify({
            'cluster': {
                'status': health.get('status'),  # green, yellow, red
                'active_shards': health.get('active_shards'),
                'nodes': health.get('number_of_nodes'),
                'data_nodes': health.get('number_of_data_nodes')
            },
            'indices': {
                'total': len(indices_status.get('indices', {})),
                'healthy': health.get('status') == 'green'
            }
        }), 200

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'error': 'Elasticsearch not available',
            'message': str(e)
        }), 503


def register_search_admin(app):
    """Register search admin blueprint"""
    app.register_blueprint(search_admin_bp)
