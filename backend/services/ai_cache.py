"""AI Response Cache — Reduces duplicate Claude API calls.

TTL-based in-memory cache with per-user isolation support for personalized
content. Global caching for platform-wide data (trending, posting times).

Thread-safe via threading.Lock.
"""
import hashlib
import json
import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger('ai_cache')


class AIResponseCache:
    """TTL-based cache for AI responses.

    Saves money by not calling Claude for identical or near-identical prompts.
    Supports per-user keys (set user_id kwarg) and global keys for shared data.
    """

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    # ------------------------------------------------------------------
    # Key construction
    # ------------------------------------------------------------------

    def _make_key(self, method: str, **kwargs) -> str:
        """Create a deterministic cache key from method name + params."""
        key_data = {'method': method, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    # ------------------------------------------------------------------
    # Read / write
    # ------------------------------------------------------------------

    def get(self, method: str, **kwargs) -> Optional[Any]:
        """Return cached value if still valid, else None."""
        key = self._make_key(method, **kwargs)
        with self._lock:
            entry = self._cache.get(key)
            if entry and time.time() < entry['expires']:
                self.hits += 1
                logger.debug("Cache HIT  method=%s key=%s", method, key[:8])
                return entry['data']
            self.misses += 1
            logger.debug("Cache MISS method=%s key=%s", method, key[:8])
            return None

    def set(self, method: str, data: Any, ttl: Optional[int] = None, **kwargs) -> None:
        """Store value with TTL (seconds). Uses default_ttl when ttl is None."""
        key = self._make_key(method, **kwargs)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._cache[key] = {
                'data': data,
                'expires': time.time() + effective_ttl,
                'created': time.time(),
                'method': method,
            }
        logger.debug("Cache SET  method=%s key=%s ttl=%ss", method, key[:8], effective_ttl)

    def invalidate(self, method: str, **kwargs) -> bool:
        """Remove a specific cache entry. Returns True if it existed."""
        key = self._make_key(method, **kwargs)
        with self._lock:
            existed = key in self._cache
            self._cache.pop(key, None)
        return existed

    def clear_expired(self) -> int:
        """Purge all expired entries. Returns count of entries removed."""
        now = time.time()
        with self._lock:
            before = len(self._cache)
            self._cache = {k: v for k, v in self._cache.items() if now < v['expires']}
            removed = before - len(self._cache)
        if removed:
            logger.info("Cache evicted %d expired entries", removed)
        return removed

    def clear_all(self) -> None:
        """Wipe the entire cache (e.g. for testing)."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    # ------------------------------------------------------------------
    # Stats / reporting
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return cache hit-rate statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0.0
            now = time.time()
            active = sum(1 for v in self._cache.values() if now < v['expires'])
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_pct': round(hit_rate, 1),
                'active_entries': active,
                'total_entries': len(self._cache),
            }


# ---------------------------------------------------------------------------
# TTL registry (seconds) — 0 means no caching
# ---------------------------------------------------------------------------
# Rules:
#   - User-generic / platform-wide data: long TTL (global cache key)
#   - User-specific analysis: short TTL (include user_id in cache key)
#   - Content generation: 0 (always fresh — user expects unique output)
# ---------------------------------------------------------------------------
CACHE_TTLS: dict[str, int] = {
    # SNS AI Engine methods
    'get_trending_topics':         1800,   # 30 min  — trends change slowly
    'analyze_best_posting_time':   3600,   # 1 hour  — stable platform data
    'generate_hashtags':           7200,   # 2 hours — hashtags stable
    'generate_content_calendar':      0,   # no cache — user-specific schedule
    'generate_content':               0,   # no cache — unique content expected
    'repurpose_content':              0,   # no cache — content-dependent
    'analyze_post_performance':    1800,   # 30 min  — per-post analysis
    # Claude AI service methods
    'generate_sns_content':           0,   # no cache — unique content
    'repurpose_content_claude':       0,   # no cache
    'analyze_competitor':          3600,   # 1 hour  — competitor data slow-changing
    'calculate_roi':                300,   # 5 min   — user-specific metrics
    'generate_review_response':       0,   # no cache — review-specific
    'analyze_nutrition':          86400,   # 24 hours — nutrition facts stable
    'recommend_recipes':           1800,   # 30 min
    'generate_bio_content':           0,   # no cache — brand-specific
}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
ai_cache = AIResponseCache(default_ttl=3600)
