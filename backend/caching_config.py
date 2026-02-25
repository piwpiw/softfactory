"""Caching Configuration & Implementation"""
import json
import hashlib
from datetime import datetime, timedelta
from flask import request, g
from functools import wraps
import os
from pathlib import Path

class CacheManager:
    """Simple in-memory and file-based cache with TTL support"""

    def __init__(self):
        self.memory_cache = {}
        self.cache_dir = Path(__file__).parent.parent / '.cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.hit_count = 0
        self.miss_count = 0

    def _get_cache_key(self, key_prefix, *args, **kwargs):
        """Generate cache key from prefix and arguments"""
        combined = f"{key_prefix}:" + json.dumps({
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }, sort_keys=True)
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, key):
        """Get value from cache"""
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if datetime.utcnow() < entry['expires']:
                self.hit_count += 1
                return entry['value']
            else:
                del self.memory_cache[key]

        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                if datetime.fromisoformat(data['expires']) > datetime.utcnow():
                    self.hit_count += 1
                    # Load into memory for next hit
                    self.memory_cache[key] = {
                        'value': data['value'],
                        'expires': datetime.fromisoformat(data['expires'])
                    }
                    return data['value']
                else:
                    cache_file.unlink()
            except Exception:
                pass

        self.miss_count += 1
        return None

    def set(self, key, value, ttl_seconds=3600):
        """Set value in cache with TTL"""
        expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        # Store in memory
        self.memory_cache[key] = {
            'value': value,
            'expires': expires
        }

        # Store in file for persistence
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'value': value,
                    'expires': expires.isoformat()
                }, f)
        except Exception as e:
            print(f"Failed to write cache file: {e}")

    def delete(self, key):
        """Delete value from cache"""
        if key in self.memory_cache:
            del self.memory_cache[key]

        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()

    def clear(self):
        """Clear all cache"""
        self.memory_cache.clear()
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()

    def get_stats(self):
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total,
            'cached_items': len(self.memory_cache)
        }

# Global cache instance
_cache_manager = CacheManager()

def cached(key_prefix, ttl_seconds=3600):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            cache_key = _cache_manager._get_cache_key(key_prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = _cache_manager.get(cache_key)
            if cached_value is not None:
                g.cache_hits = getattr(g, 'cache_hits', 0) + 1
                return cached_value

            # Call function and cache result
            result = f(*args, **kwargs)
            _cache_manager.set(cache_key, result, ttl_seconds)
            return result

        return decorated
    return decorator

def cache_bust(key_prefix):
    """Decorator to invalidate cache after function execution"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Execute function first
            result = f(*args, **kwargs)

            # Invalidate related cache entries
            try:
                pattern = f"{key_prefix}:*"
                for cache_file in _cache_manager.cache_dir.glob('*.json'):
                    if key_prefix in cache_file.stem:
                        cache_file.unlink()
            except Exception as e:
                print(f"Failed to bust cache: {e}")

            return result
        return decorated
    return decorator

def register_cache_routes(app):
    """Register cache management endpoints"""

    @app.route('/api/cache/stats')
    def get_cache_stats():
        """Get cache statistics"""
        from flask import jsonify
        return jsonify(_cache_manager.get_stats()), 200

    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear all cache"""
        from flask import jsonify
        from .auth import require_auth, require_admin

        @require_auth
        @require_admin
        def _clear():
            _cache_manager.clear()
            return jsonify({'status': 'success', 'message': 'Cache cleared'}), 200

        return _clear()

    @app.route('/api/cache/warmup', methods=['POST'])
    def warmup_cache():
        """Warm up cache with common queries"""
        from flask import jsonify

        try:
            # Pre-populate cache with common queries
            results = []

            # Cache products
            from .models import Product
            products = Product.query.filter_by(is_active=True).all()
            _cache_manager.set('products:all', [p.to_dict() for p in products], ttl_seconds=3600)
            results.append('products:all')

            return jsonify({
                'status': 'success',
                'items_warmed': results,
                'count': len(results)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# HTTP-level caching headers
def add_cache_headers(response, cache_control='public, max-age=3600'):
    """Add HTTP cache headers to response"""
    response.headers['Cache-Control'] = cache_control
    response.headers['Pragma'] = 'cache'
    return response

def add_etag(response):
    """Add ETag header to response for conditional requests"""
    if response.is_json and hasattr(response, 'get_json'):
        try:
            data = response.get_json()
            if data:
                etag = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                response.headers['ETag'] = f'"{etag}"'
        except:
            pass
    return response

# Response compression configuration
COMPRESSION_CONFIG = {
    'MIN_SIZE_BYTES': 500,  # Minimum size to compress
    'COMPRESSION_LEVEL': 6,  # gzip compression level (1-9, 6 is default)
    'MIME_TYPES': [
        'text/plain',
        'text/html',
        'text/xml',
        'text/javascript',
        'application/json',
        'application/javascript',
        'application/xml+rss',
        'application/atom+xml'
    ]
}
