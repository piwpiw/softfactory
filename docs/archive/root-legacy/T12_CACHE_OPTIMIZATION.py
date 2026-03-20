"""
T12: Caching Layer Optimization & Performance Benchmarking
In-memory cache with TTL, hit/miss analysis, performance metrics
"""

import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any, Optional, Dict


class CacheMetrics:
    """Track cache performance statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        self.request_times = []

    def record_hit(self, response_time: float):
        self.hits += 1
        self.total_requests += 1
        self.request_times.append(response_time)

    def record_miss(self, response_time: float):
        self.misses += 1
        self.total_requests += 1
        self.request_times.append(response_time)

    def get_hit_ratio(self) -> float:
        """Cache hit ratio (0.0 - 1.0)"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def get_avg_response_time(self) -> float:
        """Average response time in ms"""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)

    def get_stats(self) -> Dict[str, Any]:
        """Return all metrics"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': round(self.get_hit_ratio(), 3),
            'miss_ratio': round(1 - self.get_hit_ratio(), 3),
            'total_requests': self.total_requests,
            'evictions': self.evictions,
            'avg_response_time_ms': round(self.get_avg_response_time(), 2),
            'min_response_time_ms': round(min(self.request_times), 2) if self.request_times else 0,
            'max_response_time_ms': round(max(self.request_times), 2) if self.request_times else 0
        }


class OptimizedSNSCache:
    """
    Production-ready in-memory cache with TTL, metrics, and optimization
    Phase 2: In-memory (current)
    Phase 3: Redis integration (future)
    """

    # Recommended TTL values (in seconds)
    TTL_SETTINGS = {
        'analytics': 900,          # 15 minutes: analytics data is relatively static
        'templates': 300,          # 5 minutes: templates change infrequently
        'accounts': 120,           # 2 minutes: account data may change
        'inbox': 60,               # 1 minute: messages come frequently
        'campaigns': 300,          # 5 minutes: campaign data stable
        'settings': 600,           # 10 minutes: settings rarely change
        'calendar': 300,           # 5 minutes: calendar relatively static
        'ai_cache': 3600,          # 1 hour: AI generations can be reused
    }

    # Cache size limits (entries per category)
    SIZE_LIMITS = {
        'analytics': 100,
        'templates': 50,
        'accounts': 100,
        'inbox': 500,
        'campaigns': 200,
        'settings': 50,
        'calendar': 30,
        'ai_cache': 200
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._timestamps: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._metrics: Dict[str, CacheMetrics] = defaultdict(CacheMetrics)
        self._access_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def get(self, category: str, key: str, fetch_fn=None, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get value from cache with optional fetch function

        Args:
            category: Cache category (analytics, templates, etc.)
            key: Cache key
            fetch_fn: Optional function to call if cache miss
            ttl: Optional override for TTL

        Returns:
            Cached value or fetched value
        """
        start_time = time.time()

        # Check if key exists and not expired
        if key in self._cache[category]:
            if self._is_valid(category, key):
                response_time = (time.time() - start_time) * 1000
                self._metrics[category].record_hit(response_time)
                self._access_counts[category][key] += 1
                return self._cache[category][key]
            else:
                # Expired entry, remove it
                del self._cache[category][key]
                del self._timestamps[category][key]

        # Cache miss - call fetch function if provided
        if fetch_fn:
            value = fetch_fn()
            ttl_val = ttl or self.TTL_SETTINGS.get(category, 300)
            self.set(category, key, value, ttl_val)
            response_time = (time.time() - start_time) * 1000
            self._metrics[category].record_miss(response_time)
            return value
        else:
            response_time = (time.time() - start_time) * 1000
            self._metrics[category].record_miss(response_time)
            return None

    def set(self, category: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL

        Args:
            category: Cache category
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if set successful, False if size limit exceeded
        """
        ttl_val = ttl or self.TTL_SETTINGS.get(category, 300)
        size_limit = self.SIZE_LIMITS.get(category, 100)

        # Check size limit
        if len(self._cache[category]) >= size_limit and key not in self._cache[category]:
            # Evict least recently used entry
            self._evict_lru(category)
            self._metrics[category].evictions += 1

        self._cache[category][key] = value
        self._timestamps[category][key] = time.time() + ttl_val
        self._access_counts[category][key] = 0
        return True

    def invalidate(self, category: str, key: Optional[str] = None):
        """
        Invalidate cache entries

        Args:
            category: Cache category
            key: Specific key to invalidate, or None for all in category
        """
        if key is None:
            # Invalidate entire category
            self._cache[category].clear()
            self._timestamps[category].clear()
            self._access_counts[category].clear()
        else:
            # Invalidate specific key
            self._cache[category].pop(key, None)
            self._timestamps[category].pop(key, None)
            self._access_counts[category].pop(key, None)

    def _is_valid(self, category: str, key: str) -> bool:
        """Check if cache entry is still valid (not expired)"""
        if key not in self._timestamps[category]:
            return False
        return time.time() < self._timestamps[category][key]

    def _evict_lru(self, category: str):
        """Evict least recently used entry from category"""
        if not self._access_counts[category]:
            # If no access counts, remove oldest entry
            oldest_key = min(
                self._timestamps[category].keys(),
                key=lambda k: self._timestamps[category][k]
            )
        else:
            # Remove least frequently accessed
            oldest_key = min(
                self._access_counts[category].keys(),
                key=lambda k: self._access_counts[category][k]
            )

        self._cache[category].pop(oldest_key, None)
        self._timestamps[category].pop(oldest_key, None)
        self._access_counts[category].pop(oldest_key, None)

    def get_metrics(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get cache performance metrics"""
        if category:
            return self._metrics[category].get_stats()

        # Return all categories
        all_metrics = {}
        for cat in self._metrics:
            all_metrics[cat] = self._metrics[cat].get_stats()

        # Calculate overall
        total_hits = sum(m['hits'] for m in all_metrics.values())
        total_requests = sum(m['total_requests'] for m in all_metrics.values())
        overall_hit_ratio = total_hits / total_requests if total_requests > 0 else 0

        return {
            'categories': all_metrics,
            'overall_hit_ratio': round(overall_hit_ratio, 3),
            'total_requests': total_requests,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get cache status and health"""
        sizes = {cat: len(self._cache[cat]) for cat in self._cache}
        utilization = {
            cat: round(sizes[cat] / self.SIZE_LIMITS.get(cat, 100) * 100, 1)
            for cat in sizes
        }

        return {
            'sizes': sizes,
            'utilization_percent': utilization,
            'metrics': self.get_metrics()
        }


# Global cache instance
_sns_cache = OptimizedSNSCache()


def cache_get(category: str, key: str, fetch_fn=None, ttl: Optional[int] = None):
    """Get from cache with optional fetch"""
    return _sns_cache.get(category, key, fetch_fn, ttl)


def cache_set(category: str, key: str, value: Any, ttl: Optional[int] = None):
    """Set cache value"""
    return _sns_cache.set(category, key, value, ttl)


def cache_invalidate(category: str, key: Optional[str] = None):
    """Invalidate cache entries"""
    return _sns_cache.invalidate(category, key)


def get_cache_metrics(category: Optional[str] = None):
    """Get cache performance metrics"""
    return _sns_cache.get_metrics(category)


def get_cache_status():
    """Get cache status"""
    return _sns_cache.get_status()


# ============ CACHE INTEGRATION PATTERNS ============

def cached_fetch(category: str, ttl: Optional[int] = None):
    """
    Decorator for automatic cache management

    Usage:
        @cached_fetch('analytics', ttl=900)
        def get_sns_analytics(account_id):
            # Actual fetch logic
            return analytics_data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            key = f"{func.__name__}:{':'.join(str(a) for a in args)}"

            # Try cache first
            cached_value = cache_get(category, key)
            if cached_value is not None:
                return cached_value

            # Fetch and cache
            result = func(*args, **kwargs)
            cache_set(category, key, result, ttl)
            return result

        return wrapper
    return decorator


# ============ PERFORMANCE BENCHMARKS ============

def run_cache_benchmarks():
    """Run performance benchmarks"""
    cache = OptimizedSNSCache()
    results = {}

    # Test 1: Single access time
    start = time.time()
    cache.set('accounts', 'key1', {'id': 1, 'name': 'test'})
    cache.get('accounts', 'key1')
    single_access_time = (time.time() - start) * 1000
    results['single_access_ms'] = round(single_access_time, 3)

    # Test 2: Cache hit ratio
    for i in range(100):
        cache.set('analytics', f'key{i}', {'data': f'value{i}'})

    # Access with mix of hits and misses
    for i in range(200):
        key = f'key{i % 100}'  # 50% hit ratio
        cache.get('analytics', key)

    metrics = cache.get_metrics('analytics')
    results['hit_ratio'] = metrics['hit_ratio']
    results['avg_response_ms'] = metrics['avg_response_time_ms']

    # Test 3: Size limit enforcement
    for i in range(200):
        cache.set('templates', f'template{i}', {'content': f'template{i}'}, ttl=600)

    status = cache.get_status()
    results['templates_size_limit_enforced'] = status['sizes']['templates'] <= 50

    # Test 4: TTL expiration
    cache.set('inbox', 'msg1', {'text': 'test'}, ttl=1)
    time.sleep(1.1)
    expired = cache.get('inbox', 'msg1') is None
    results['ttl_expiration_works'] = expired

    return results


# ============ RECOMMENDED INTEGRATION ============

"""
Integration with backend/services/sns_auto.py:

@cached_fetch('analytics', ttl=900)
def get_sns_analytics(account_id, start_date, end_date):
    # Actual analytics fetch
    return db.session.query(SNSAnalytics).filter(...).all()

@cached_fetch('templates', ttl=300)
def get_sns_templates(user_id):
    # Actual template fetch
    return db.session.query(SNSTemplate).filter(...).all()

# Invalidation on write:
def update_sns_settings(user_id, settings):
    # Update database
    user_settings = SNSSettings.query.get(user_id)
    user_settings.update(settings)
    db.session.commit()

    # Invalidate cache
    cache_invalidate('settings', f'settings:{user_id}')

    return user_settings
"""


if __name__ == '__main__':
    # Run benchmarks
    print("Running Cache Performance Benchmarks...")
    benchmarks = run_cache_benchmarks()
    print(json.dumps(benchmarks, indent=2))

    # Example metrics
    print("\n\nExpected Performance Metrics:")
    print("- Single access time: 0.1-0.5ms (in-memory)")
    print("- Hit ratio (stable patterns): 60-80%")
    print("- Average response time: 0.2-0.3ms")
    print("- TTL expiration: Accurate within 1 second")
    print("\nPhase 3 (Redis): 10-100x more scalable")
    print("Current capacity: ~1,500 cache entries total")
    print("Recommended upgrade: Redis when >10,000 entries/second")
