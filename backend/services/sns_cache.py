"""Simple in-memory caching for SNS analytics and frequently accessed data

Phase 1: In-memory cache (dict-based)
Phase 2: Redis cache (production)
"""

import time
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

# Global in-memory cache
_CACHE: Dict[str, tuple] = {}  # {key: (value, expires_at)}


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache if not expired.

    Args:
        key: Cache key

    Returns:
        Cached value or None if expired/not found
    """
    if key not in _CACHE:
        return None

    value, expires_at = _CACHE[key]

    # Check if expired
    if expires_at and datetime.utcnow() > expires_at:
        del _CACHE[key]
        return None

    return value


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """
    Set value in cache with TTL.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default 5 minutes)
    """
    expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
    _CACHE[key] = (value, expires_at)


def cache_invalidate(prefix: str) -> None:
    """
    Invalidate all cache keys matching prefix.

    Args:
        prefix: Key prefix to match (e.g., 'accounts:123' removes all keys starting with 'accounts:123')
    """
    keys_to_delete = [key for key in _CACHE.keys() if key.startswith(prefix)]
    for key in keys_to_delete:
        del _CACHE[key]


def cache_clear() -> None:
    """Clear entire cache"""
    _CACHE.clear()


def cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    total_keys = len(_CACHE)
    expired_keys = 0

    for key, (value, expires_at) in _CACHE.items():
        if expires_at and datetime.utcnow() > expires_at:
            expired_keys += 1

    return {
        'total_keys': total_keys,
        'expired_keys': expired_keys,
        'active_keys': total_keys - expired_keys,
    }


# Decorators for easy caching

def cached(ttl: int = 300):
    """Decorator to cache function results

    Usage:
    @cached(ttl=600)
    def expensive_function(user_id):
        return get_analytics(user_id)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached_value = cache_get(cache_key)

            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator
