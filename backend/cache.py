"""Lightweight In-Memory TTL Cache for SoftFactory

Provides simple response caching without external dependencies (no Redis needed).
Uses threading locks for safe concurrent access in production WSGI servers.

Usage:
    from backend.cache import ttl_cache, invalidate_cache

    @app.route('/api/data')
    @ttl_cache(ttl_seconds=300, key_prefix='data')
    def get_data():
        return jsonify({...}), 200

    # Invalidate on writes:
    @app.route('/api/data', methods=['POST'])
    @invalidate_cache('data')
    def create_data():
        ...
"""

import time
import hashlib
import threading
from functools import wraps
from flask import request, g, jsonify


class TTLCache:
    """Thread-safe in-memory cache with TTL expiration and size limits."""

    def __init__(self, max_entries=1024):
        self._store = {}  # key -> (value, expire_time)
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}

    def get(self, key):
        """Get value if it exists and has not expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats['misses'] += 1
                return None
            value, expire_time = entry
            if time.time() > expire_time:
                del self._store[key]
                self._stats['misses'] += 1
                return None
            self._stats['hits'] += 1
            return value

    def set(self, key, value, ttl_seconds):
        """Store value with TTL. Evicts oldest entries if over capacity."""
        with self._lock:
            # Evict expired entries when approaching capacity
            if len(self._store) >= self._max_entries:
                self._evict_expired()
            # If still at capacity, evict oldest entries
            if len(self._store) >= self._max_entries:
                self._evict_oldest(len(self._store) // 4)
            self._store[key] = (value, time.time() + ttl_seconds)

    def invalidate_prefix(self, prefix):
        """Remove all entries whose key starts with the given prefix."""
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]
                self._stats['evictions'] += 1

    def clear(self):
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def stats(self):
        """Return cache statistics."""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0.0
            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'hit_rate_pct': round(hit_rate, 2),
                'entries': len(self._store),
            }

    def _evict_expired(self):
        """Remove all expired entries (caller must hold lock)."""
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
            self._stats['evictions'] += 1

    def _evict_oldest(self, count):
        """Remove the N entries with the earliest expiry (caller must hold lock)."""
        sorted_keys = sorted(self._store, key=lambda k: self._store[k][1])
        for k in sorted_keys[:count]:
            del self._store[k]
            self._stats['evictions'] += 1


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_cache = TTLCache(max_entries=2048)


def _build_cache_key(prefix):
    """Build a deterministic cache key from prefix + request path + query + user."""
    parts = [prefix, request.path]
    if request.query_string:
        parts.append(request.query_string.decode('utf-8', errors='replace'))
    # Include user_id so different users get different cache entries
    user_id = getattr(g, 'user_id', None)
    if user_id is not None:
        parts.append(str(user_id))
    raw = '|'.join(parts)
    return prefix + ':' + hashlib.md5(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def ttl_cache(ttl_seconds=300, key_prefix='default'):
    """Decorator that caches the full Flask response tuple (json_data, status_code).

    Must be placed AFTER @require_auth (closer to function) so that g.user_id
    is available when the cache key is built.

    Args:
        ttl_seconds: Time-to-live in seconds.
        key_prefix: Prefix for the cache key (used for targeted invalidation).
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = _build_cache_key(key_prefix)
            cached = _cache.get(cache_key)
            if cached is not None:
                data, status = cached
                response = jsonify(data)
                response.headers['X-Cache'] = 'HIT'
                return response, status

            result = f(*args, **kwargs)

            # Normalise the return value
            if isinstance(result, tuple):
                response_obj, status_code = result[0], result[1] if len(result) > 1 else 200
            else:
                response_obj, status_code = result, 200

            # Only cache successful (2xx) JSON responses
            if 200 <= status_code < 300:
                try:
                    if hasattr(response_obj, 'get_json'):
                        json_data = response_obj.get_json()
                    elif isinstance(response_obj, dict):
                        json_data = response_obj
                    else:
                        json_data = None

                    if json_data is not None:
                        _cache.set(cache_key, (json_data, status_code), ttl_seconds)
                except Exception:
                    pass  # Don't let cache errors break the endpoint

            return result

        return wrapper
    return decorator


def invalidate_cache(prefix):
    """Decorator that invalidates all cache entries matching prefix after the
    wrapped function executes successfully.

    Typically applied to write endpoints (POST/PUT/DELETE).
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            # Only invalidate on success
            status = 200
            if isinstance(result, tuple) and len(result) > 1:
                status = result[1]
            if 200 <= status < 300:
                _cache.invalidate_prefix(prefix)
            return result
        return wrapper
    return decorator


def get_cache():
    """Return the global cache instance (for stats, manual operations)."""
    return _cache
