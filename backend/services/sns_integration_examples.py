"""SNS Endpoints Integration Examples

Demonstrates best practices for using the optimized v2 API:
- Pagination patterns
- Caching strategies
- Rate limit handling
- Error recovery
"""

from datetime import datetime, timedelta
from backend.utils.cache_manager import get_cache, CacheWarmer, CacheInvalidationStrategy
from backend.utils.pagination import CursorPagination, OffsetPagination, FieldFilter
from backend.utils.retry_handler import PlatformCircuitBreaker, ErrorHandler
import logging

logger = logging.getLogger(__name__)


# ============ EXAMPLE 1: Fetch All Posts (Efficient Pagination) ============

def fetch_all_posts_cursor_pagination(client, user_id, per_page=100):
    """
    Fetch all user posts using cursor pagination.

    Advantages:
    - O(1) database queries
    - Handles real-time insertions
    - Memory efficient

    Typical usage: Loading posts feed
    """
    all_posts = []
    cursor = None

    while True:
        # Build request parameters
        params = {
            'pagination': 'cursor',
            'per_page': min(per_page, 100),  # Cap at 100
        }

        if cursor:
            params['cursor'] = cursor

        # Fetch page
        response = client.get(f'/api/v2/sns/posts', params=params)

        if response.status_code != 200:
            logger.error(f"Failed to fetch posts: {response.status_code}")
            break

        data = response.json()
        all_posts.extend(data['data'])

        # Check if more pages
        if not data['pagination']['has_more']:
            break

        cursor = data['pagination']['next_cursor']
        logger.info(f"Fetched {len(all_posts)} posts so far...")

    logger.info(f"Total posts fetched: {len(all_posts)}")
    return all_posts


# ============ EXAMPLE 2: Field Filtering (Reduce Bandwidth) ============

def fetch_posts_minimal(client, user_id):
    """
    Fetch only essential fields to reduce bandwidth.

    Mobile apps use this to minimize data transfer.

    Bandwidth savings: ~80%
    """
    params = {
        'pagination': 'cursor',
        'per_page': 50,
        'fields': 'id,title,published_at,engagement_count'  # Only these
    }

    response = client.get('/api/v2/sns/posts', params=params)
    return response.json()


def fetch_posts_full(client, user_id):
    """
    Fetch all fields for detailed view.

    Desktop/rich clients use this.
    """
    response = client.get('/api/v2/sns/posts', params={'per_page': 50})
    return response.json()


# ============ EXAMPLE 3: Smart Caching ============

def get_analytics_with_cache(client, user_id, start_date, end_date):
    """
    Get analytics with intelligent caching.

    The API automatically caches analytics for 10 minutes.
    Subsequent requests to same date range return instantly.
    """
    cache = get_cache()
    cache_key = f"analytics:{user_id}:{start_date}:{end_date}"

    # Check local cache first
    cached = cache.get(cache_key)
    if cached:
        logger.info("Returning cached analytics")
        return cached

    # Fetch from API
    params = {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }

    response = client.get('/api/v2/sns/analytics', params=params)
    analytics = response.json()

    # Cache for future use
    cache.set(cache_key, analytics, ttl=600)  # 10 minutes

    return analytics


def invalidate_analytics_cache(user_id):
    """
    Manually invalidate analytics cache when new post is published.

    This ensures next fetch returns fresh data.
    """
    cache = get_cache()
    cache.invalidate('post_published', user_id=user_id)
    logger.info(f"Invalidated analytics cache for user {user_id}")


# ============ EXAMPLE 4: Rate Limit Handling ============

def fetch_with_rate_limit_handling(client, endpoint, params=None):
    """
    Fetch data with graceful rate limit handling.

    When hitting rate limit, back off and retry.
    """
    import time

    for attempt in range(3):
        response = client.get(endpoint, params=params)

        if response.status_code == 429:
            # Hit rate limit
            reset_in = int(response.headers.get('X-RateLimit-Reset', 60))
            logger.warning(f"Rate limited. Waiting {reset_in}s before retry...")
            time.sleep(reset_in)
            continue

        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code}")
            return None

        remaining = response.headers.get('X-RateLimit-Remaining')
        logger.info(f"API calls remaining: {remaining}")

        return response.json()

    logger.error("Max retries exceeded")
    return None


def batch_requests_respecting_limits(client, endpoints, max_requests_per_minute=10):
    """
    Fetch multiple endpoints while respecting rate limits.

    Useful for syncing multiple data sources.
    """
    import time
    from collections import deque

    request_times = deque(maxlen=max_requests_per_minute)
    results = []

    for endpoint in endpoints:
        # Check if we need to throttle
        now = time.time()
        if len(request_times) == max_requests_per_minute:
            oldest = request_times[0]
            if now - oldest < 60:
                wait_time = 60 - (now - oldest)
                logger.info(f"Throttling: waiting {wait_time:.1f}s")
                time.sleep(wait_time)

        # Make request
        response = client.get(endpoint)
        request_times.append(time.time())

        if response.status_code == 200:
            results.append(response.json())
        else:
            logger.error(f"Failed to fetch {endpoint}: {response.status_code}")

    return results


# ============ EXAMPLE 5: Error Recovery with Retries ============

def publish_post_with_retry(platform, content, max_retries=3):
    """
    Publish post with automatic retry and circuit breaker.

    Handles:
    - Transient failures (temporary network issue)
    - Permanent failures (no retry)
    - Rate limits (exponential backoff)
    - Service unavailable (circuit breaker)
    """
    import random
    import time

    backoff = ExponentialBackoff(base_delay=1.0, max_delay=30.0)

    for attempt in range(max_retries):
        try:
            # Check circuit breaker
            breaker = PlatformCircuitBreaker.get_breaker(platform)
            if not breaker.can_execute():
                logger.error(f"Circuit breaker OPEN for {platform}")
                return None

            # Attempt to publish
            result = _do_publish(platform, content)

            breaker.record_success()
            return result

        except Exception as e:
            # Categorize error
            error_category = ErrorHandler.categorize_error(e)
            should_retry = ErrorHandler.should_retry(error_category, attempt, max_retries)

            if not should_retry:
                logger.error(f"Not retrying {error_category.name}: {e}")
                breaker.record_failure()
                return None

            if attempt < max_retries - 1:
                # Exponential backoff
                delay = backoff.calculate_delay(attempt)
                logger.warning(f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"Max retries exceeded for {platform}")
                breaker.record_failure()

    return None


def _do_publish(platform, content):
    """Actual platform publishing logic"""
    # This would call the actual platform API
    pass


# ============ EXAMPLE 6: Cache Warming ============

def warm_cache_on_user_login(user_id, client):
    """
    Pre-warm cache with frequently accessed data when user logs in.

    This reduces latency for first requests and peak load.
    """
    cache = get_cache()

    def data_getter(data_type, uid, **kwargs):
        """Helper to fetch data from API"""
        if data_type == 'trending':
            return client.get(f'/api/v2/sns/trending?user_id={uid}').json()
        elif data_type == 'profile':
            return client.get(f'/api/v2/sns/profile?user_id={uid}').json()
        elif data_type == 'recent_posts_meta':
            limit = kwargs.get('limit', 10)
            return client.get(f'/api/v2/sns/posts?per_page={limit}&fields=id,title,published_at').json()

    # Warm cache
    warmer = CacheWarmer(cache)
    warmer.warm_user_data(user_id, data_getter)

    logger.info(f"Cache warmed for user {user_id}")


# ============ EXAMPLE 7: Concurrent Pagination ============

def fetch_posts_from_multiple_platforms_parallel(client, platforms, per_page=50):
    """
    Fetch posts from multiple platforms in parallel.

    Uses pagination to handle large result sets efficiently.
    """
    import concurrent.futures

    def fetch_platform_posts(platform):
        all_posts = []
        cursor = None

        while True:
            params = {
                'platform': platform,
                'pagination': 'cursor',
                'per_page': per_page
            }

            if cursor:
                params['cursor'] = cursor

            response = client.get('/api/v2/sns/posts', params=params)

            if response.status_code != 200:
                break

            data = response.json()
            all_posts.extend(data['data'])

            if not data['pagination']['has_more']:
                break

            cursor = data['pagination']['next_cursor']

        return platform, all_posts

    # Fetch in parallel
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as executor:
        futures = {
            executor.submit(fetch_platform_posts, platform): platform
            for platform in platforms
        }

        for future in concurrent.futures.as_completed(futures):
            platform, posts = future.result()
            results[platform] = posts

    return results


# ============ EXAMPLE 8: Cache Statistics for Monitoring ============

def log_cache_performance():
    """
    Log cache hit/miss statistics for monitoring.

    Use this to identify optimization opportunities.
    """
    cache = get_cache()
    stats = cache.stats()

    logger.info(f"Cache Performance:")
    logger.info(f"  Hits: {stats['hits']}")
    logger.info(f"  Misses: {stats['misses']}")
    logger.info(f"  Hit Rate: {stats['hit_rate']}")
    logger.info(f"  Invalidations: {stats['invalidations']}")
    logger.info(f"  Keys Stored: {stats['keys_stored']}")

    # Alert if hit rate drops
    hit_rate = float(stats['hit_rate'].rstrip('%'))
    if hit_rate < 60:
        logger.warning("Cache hit rate below 60% — consider adjusting TTLs or warming cache more frequently")


# ============ MAIN EXECUTION EXAMPLE ============

def main():
    """Complete workflow example"""
    import requests

    # Setup
    client = requests.Session()
    client.headers['Authorization'] = 'Bearer token_here'
    user_id = 123

    logger.basicConfig(level=logging.INFO)

    # 1. Warm cache on startup
    logger.info("=== Step 1: Warming cache ===")
    warm_cache_on_user_login(user_id, client)

    # 2. Fetch posts efficiently
    logger.info("\n=== Step 2: Fetching posts (pagination) ===")
    posts = fetch_posts_minimal(client, user_id)
    logger.info(f"Fetched {len(posts['data'])} posts")

    # 3. Get analytics
    logger.info("\n=== Step 3: Fetching analytics ===")
    analytics = get_analytics_with_cache(
        client, user_id,
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    logger.info(f"Analytics: {analytics}")

    # 4. Check rate limits
    logger.info("\n=== Step 4: Checking rate limits ===")
    response = client.get('http://localhost:8000/api/v2/sns/cache/stats')
    logger.info(f"Rate limit info in headers: {dict(response.headers)}")

    # 5. Log cache stats
    logger.info("\n=== Step 5: Cache statistics ===")
    log_cache_performance()


if __name__ == '__main__':
    main()
