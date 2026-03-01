"""Advanced Cache Management for SNS Endpoints

Implements:
- Cache invalidation strategies
- Conditional requests (ETag)
- Cache warming
- Cache statistics
- Multi-tier caching
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, Callable
from functools import wraps
from flask import request, make_response, jsonify, g


class ETagGenerator:
    """Generate ETags for conditional requests"""

    @staticmethod
    def generate(data: Any) -> str:
        """Generate ETag from data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()

    @staticmethod
    def check_match(response_data: Any) -> bool:
        """Check if client's If-None-Match matches data"""
        client_etag = request.headers.get('If-None-Match')
        if not client_etag:
            return False

        current_etag = ETagGenerator.generate(response_data)
        return client_etag == current_etag


class CacheInvalidationStrategy:
    """Cache invalidation strategies"""

    # Define what data affects what cache keys
    INVALIDATION_MAP = {
        'post_created': [
            'analytics:*',
            'calendar:*',
            'trending:*'
        ],
        'post_updated': [
            'analytics:*',
            'calendar:*'
        ],
        'post_published': [
            'analytics:*',
            'trending:*'
        ],
        'account_connected': [
            'accounts:*',
            'analytics:*'
        ],
        'account_updated': [
            'accounts:*',
            'profile:*'
        ],
        'settings_changed': [
            'settings:*',
            'user_preferences:*'
        ]
    }

    def __init__(self, cache_backend):
        self.cache = cache_backend

    def invalidate(self, event_type: str, **kwargs) -> None:
        """Invalidate cache based on event"""
        if event_type not in self.INVALIDATION_MAP:
            return

        user_id = kwargs.get('user_id')
        patterns = self.INVALIDATION_MAP[event_type]

        for pattern in patterns:
            prefix = pattern.replace('*', '').rstrip(':')
            if user_id:
                prefix = f"{prefix}:{user_id}"

            self.cache.invalidate_by_prefix(prefix)

    @staticmethod
    def on_post_created(user_id: int, post_id: int):
        """Called when post is created"""
        return {
            'event': 'post_created',
            'user_id': user_id,
            'post_id': post_id
        }

    @staticmethod
    def on_account_connected(user_id: int, platform: str):
        """Called when account is connected"""
        return {
            'event': 'account_connected',
            'user_id': user_id,
            'platform': platform
        }


class CacheWarmer:
    """Pre-load frequently accessed data into cache"""

    def __init__(self, cache_backend):
        self.cache = cache_backend

    def warm_user_data(self, user_id: int, data_getter: Callable) -> None:
        """Pre-warm cache for user's common queries"""
        try:
            # Load trending data
            trending = data_getter('trending', user_id)
            self.cache.set(
                f'trending:{user_id}',
                trending,
                ttl=3600  # 1 hour
            )

            # Load user profile
            profile = data_getter('profile', user_id)
            self.cache.set(
                f'profile:{user_id}',
                profile,
                ttl=600  # 10 minutes
            )

            # Load recent posts metadata
            recent = data_getter('recent_posts_meta', user_id, limit=10)
            self.cache.set(
                f'recent_posts:{user_id}',
                recent,
                ttl=300  # 5 minutes
            )
        except Exception as e:
            print(f"Cache warming failed: {e}")

    def warm_global_data(self, data_getter: Callable) -> None:
        """Pre-warm global cached data"""
        try:
            # Platform statistics
            stats = data_getter('platform_stats')
            self.cache.set('platform:stats', stats, ttl=1800)

            # Popular hashtags
            hashtags = data_getter('popular_hashtags')
            self.cache.set('hashtags:popular', hashtags, ttl=3600)
        except Exception as e:
            print(f"Global cache warming failed: {e}")


class AdvancedCache:
    """Advanced caching with statistics and multi-tier support"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'sets': 0
        }
        self._invalidation_strategy = CacheInvalidationStrategy(self)
        self._warmer = CacheWarmer(self)

    def get(self, key: str) -> Optional[Any]:
        """Get from cache with statistics"""
        if key not in self._cache:
            self._stats['misses'] += 1
            return None

        value, expires_at = self._cache[key]

        # Check expiration
        if expires_at and datetime.utcnow() > expires_at:
            del self._cache[key]
            self._stats['misses'] += 1
            return None

        self._stats['hits'] += 1
        return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set in cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        self._cache[key] = (value, expires_at)
        self._stats['sets'] += 1

    def invalidate_by_prefix(self, prefix: str) -> None:
        """Invalidate all keys matching prefix"""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        self._stats['invalidations'] += len(keys_to_delete)

    def clear(self) -> None:
        """Clear entire cache"""
        self._cache.clear()

    def stats(self) -> dict:
        """Get cache statistics"""
        hit_rate = 0
        total_requests = self._stats['hits'] + self._stats['misses']
        if total_requests > 0:
            hit_rate = (self._stats['hits'] / total_requests) * 100

        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'invalidations': self._stats['invalidations'],
            'sets': self._stats['sets'],
            'keys_stored': len(self._cache)
        }

    def invalidate(self, event_type: str, **kwargs) -> None:
        """Use invalidation strategy"""
        self._invalidation_strategy.invalidate(event_type, **kwargs)

    def warm_user_data(self, user_id: int, data_getter: Callable) -> None:
        """Warm cache for user"""
        self._warmer.warm_user_data(user_id, data_getter)

    def warm_global_data(self, data_getter: Callable) -> None:
        """Warm global cache"""
        self._warmer.warm_global_data(data_getter)


# Global cache instance
_global_cache = AdvancedCache()


def conditional_response(f):
    """Decorator to add ETag support to responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response_data = f(*args, **kwargs)

        # If it's already a tuple (status code), extract data
        if isinstance(response_data, tuple):
            json_response = response_data[0]
            status_code = response_data[1] if len(response_data) > 1 else 200
        else:
            json_response = response_data
            status_code = 200

        # Generate ETag
        etag = ETagGenerator.generate(json_response)

        # Check If-None-Match
        if ETagGenerator.check_match(json_response):
            return '', 304

        response = make_response(json_response, status_code)
        response.headers['ETag'] = etag
        return response

    return decorated_function


def cached_endpoint(ttl: int = 300):
    """Decorator to cache entire endpoint response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Build cache key from endpoint and query params
            cache_key = f"{request.path}:{json.dumps(request.args)}"

            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                response = make_response(cached_value, 200)
                response.headers['X-Cache'] = 'HIT'
                return response

            # Call original function
            result = f(*args, **kwargs)

            # Cache the result
            if isinstance(result, dict):
                _global_cache.set(cache_key, result, ttl=ttl)
                response = make_response(result, 200)
                response.headers['X-Cache'] = 'MISS'
                return response

            return result

        return decorated_function
    return decorator


def get_cache() -> AdvancedCache:
    """Get global cache instance"""
    return _global_cache


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    return _global_cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache"""
    _global_cache.set(key, value, ttl)
