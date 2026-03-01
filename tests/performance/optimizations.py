"""
Performance Optimization Implementations for SoftFactory Flask API
Implements caching, query optimization, and other improvements
"""

from flask_caching import Cache
from flask import Flask
from sqlalchemy import event
from sqlalchemy.orm import Session
from typing import List, Tuple


class CacheConfiguration:
    """Flask-Caching configuration for different cache types"""

    # In-memory cache config (good for development and small deployments)
    SIMPLE_CACHE_CONFIG = {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300,
    }

    # Redis cache config (production recommended)
    REDIS_CACHE_CONFIG = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': 'redis://localhost:6379/0',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'softfactory:',
    }

    @staticmethod
    def get_cache_config(use_redis: bool = False):
        """Get cache configuration"""
        return (
            CacheConfiguration.REDIS_CACHE_CONFIG
            if use_redis
            else CacheConfiguration.SIMPLE_CACHE_CONFIG
        )


class QueryOptimizer:
    """Database query optimization techniques"""

    @staticmethod
    def detect_n_plus_one(app: Flask):
        """
        Detect N+1 query patterns in SQLAlchemy
        Logs multiple queries for the same relationship
        """

        query_history = {}

        @event.listens_for(Session, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            # Track query execution
            query_key = statement.split()[0:3]  # Get first 3 words to identify pattern
            query_str = " ".join(query_key)

            if query_str not in query_history:
                query_history[query_str] = 0
            query_history[query_str] += 1

        return query_history

    @staticmethod
    def optimize_chef_list_query():
        """
        Optimized chef listing query with eager loading
        Original: N+1 when accessing chef.bookings
        Optimized: Uses joinedload to fetch bookings in single query
        """
        from sqlalchemy.orm import joinedload
        from backend.models import Chef

        # ❌ BEFORE (N+1 problem):
        # chefs = Chef.query.filter_by(is_active=True).all()
        # for chef in chefs:
        #     count = len(chef.bookings)  # Each chef triggers another query!

        # ✅ AFTER (eager loading):
        query = Chef.query.options(joinedload('bookings')).filter_by(is_active=True)
        return query

    @staticmethod
    def add_database_indexes():
        """
        Index recommendations for common query patterns
        These should be applied via database migrations
        """
        index_recommendations = [
            {
                'table': 'chefs',
                'column': 'is_active',
                'reason': 'Filtered in every GET /chefs request'
            },
            {
                'table': 'chefs',
                'column': 'cuisine_type',
                'reason': 'Filtered by cuisine in chef list'
            },
            {
                'table': 'bookings',
                'column': 'user_id',
                'reason': 'Filtered when getting user bookings'
            },
            {
                'table': 'bookings',
                'column': 'chef_id',
                'reason': 'Filtered when getting chef bookings'
            },
            {
                'table': 'sns_posts',
                'column': 'status',
                'reason': 'Filtered by draft/published status'
            },
            {
                'table': 'users',
                'column': 'email',
                'reason': 'Already indexed - good for auth'
            },
        ]
        return index_recommendations


class ResponseOptimization:
    """Response payload and serialization optimizations"""

    @staticmethod
    def create_optimized_chef_response(chef):
        """
        Optimized chef response - only essential fields
        Reduces JSON payload size
        """
        return {
            'id': chef.id,
            'name': chef.name,
            'cuisine': chef.cuisine_type,
            'location': chef.location,
            'price': chef.price_per_session,
            'rating': chef.rating,
            'reviews': chef.rating_count,
        }

    @staticmethod
    def get_compression_headers() -> dict:
        """Headers to enable gzip compression"""
        return {
            'Content-Encoding': 'gzip',
            'Vary': 'Accept-Encoding',
        }


class CachingStrategies:
    """Caching strategies for different endpoint types"""

    # Static data that rarely changes
    STATIC_CACHE_TIMEOUT = 3600  # 1 hour

    # List endpoints - medium volatility
    LIST_CACHE_TIMEOUT = 300  # 5 minutes

    # Detail endpoints - may change more frequently
    DETAIL_CACHE_TIMEOUT = 600  # 10 minutes

    # User-specific data - shorter TTL
    USER_CACHE_TIMEOUT = 60  # 1 minute

    @staticmethod
    def get_cache_decorator(timeout: int):
        """
        Factory for creating cache decorators
        Usage:
            @get_cache_decorator(300)
            def my_endpoint():
                ...
        """
        def decorator(timeout_seconds):
            def actual_decorator(f):
                from functools import wraps
                @wraps(f)
                def wrapped(*args, **kwargs):
                    # Cache implementation would go here
                    return f(*args, **kwargs)
                return wrapped
            return actual_decorator(timeout_seconds)
        return decorator


def create_optimized_app(app: Flask) -> Flask:
    """
    Apply all optimizations to Flask app
    """

    # 1. Initialize caching
    cache_config = CacheConfiguration.get_cache_config(use_redis=False)
    cache = Cache(app, config=cache_config)

    # 2. Enable compression
    from flask_compress import Compress
    Compress(app)

    # 3. Add query optimization tracking (development only)
    if app.debug:
        print("🔍 Query optimization tracking enabled")
        QueryOptimizer.detect_n_plus_one(app)

    # 4. Add response header optimizations
    @app.after_request
    def optimize_response(response):
        # Add cache control headers for static assets
        if response.content_type and 'image' in response.content_type:
            response.cache_control.max_age = 86400  # 24 hours for images
        elif response.content_type == 'application/json':
            response.cache_control.public = True
            response.cache_control.max_age = 300  # 5 minutes for JSON
        return response

    return cache


# Sample Flask Blueprint with caching applied
def create_optimized_coocook_blueprint(cache):
    """
    Create optimized version of CooCook blueprint with caching
    """
    from flask import Blueprint, request, jsonify
    from backend.models import db, Chef
    from sqlalchemy.orm import joinedload

    optimized_bp = Blueprint('coocook_optimized', __name__, url_prefix='/api/coocook')

    @optimized_bp.route('/chefs', methods=['GET'])
    @cache.cached(timeout=CachingStrategies.LIST_CACHE_TIMEOUT,
                   query_string=True)  # Include query params in cache key
    def get_chefs_optimized():
        """Optimized chef list with eager loading and caching"""

        query = Chef.query.options(joinedload('bookings')).filter_by(is_active=True)

        # Filters
        cuisine = request.args.get('cuisine')
        location = request.args.get('location')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)

        if cuisine:
            query = query.filter_by(cuisine_type=cuisine)

        if location:
            query = query.filter(Chef.location.ilike(f'%{location}%'))

        # Pagination
        result = query.paginate(page=page, per_page=per_page)

        # Use optimized response
        chefs_data = [ResponseOptimization.create_optimized_chef_response(chef)
                      for chef in result.items]

        return jsonify({
            'chefs': chefs_data,
            'pagination': {
                'total': result.total,
                'pages': result.pages,
                'page': page,
            }
        }), 200

    @optimized_bp.route('/chefs/<int:chef_id>', methods=['GET'])
    @cache.cached(timeout=CachingStrategies.DETAIL_CACHE_TIMEOUT)
    def get_chef_detail_optimized(chef_id):
        """Optimized chef detail endpoint"""

        chef = Chef.query.options(joinedload('bookings')).get(chef_id)

        if not chef or not chef.is_active:
            return jsonify({'error': 'Chef not found'}), 404

        return jsonify(ResponseOptimization.create_optimized_chef_response(chef)), 200

    return optimized_bp


if __name__ == "__main__":
    print("Performance Optimization Module")
    print("=" * 60)

    print("\n📊 Index Recommendations:")
    for idx in QueryOptimizer.add_database_indexes():
        print(f"  - {idx['table']}.{idx['column']}: {idx['reason']}")

    print("\n⏱️  Cache Timeout Strategies:")
    print(f"  - Static content: {CachingStrategies.STATIC_CACHE_TIMEOUT}s")
    print(f"  - List endpoints: {CachingStrategies.LIST_CACHE_TIMEOUT}s")
    print(f"  - Detail endpoints: {CachingStrategies.DETAIL_CACHE_TIMEOUT}s")
    print(f"  - User-specific: {CachingStrategies.USER_CACHE_TIMEOUT}s")

    print("\n✅ Optimization strategies defined and ready to implement")
