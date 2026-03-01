"""Simple In-Memory Rate Limiter

Production-grade rate limiting without external dependencies (no Redis needed).
Implements sliding-window counters for both IP-based and user-based rate limiting.

Usage:
    from backend.rate_limiter import RateLimiter, rate_limit

    # As decorator
    @rate_limit(max_requests=5, window_seconds=60, key_func='ip')
    def login():
        ...

    # Direct usage
    limiter = RateLimiter()
    allowed, info = limiter.check('login:192.168.1.1', max_requests=5, window_seconds=60)
"""

import time
import threading
from functools import wraps
from flask import request, jsonify, g
from typing import Tuple, Callable, Optional


class RateLimiter:
    """Thread-safe in-memory sliding-window rate limiter.

    Stores timestamps of requests per key and evicts expired entries
    on each check to prevent unbounded memory growth.
    """

    def __init__(self):
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        # Periodic cleanup threshold - clean up keys with no recent activity
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def check(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, dict]:
        """Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier (e.g., 'login:192.168.1.1' or 'api:user_42')
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict with limit/remaining/retry_after)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Periodic cleanup of stale keys
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup(cutoff)
                self._last_cleanup = now

            # Get or create the request timestamp list for this key
            if key not in self._store:
                self._store[key] = []

            # Evict expired timestamps (sliding window)
            self._store[key] = [ts for ts in self._store[key] if ts > cutoff]

            current_count = len(self._store[key])

            if current_count < max_requests:
                # Allowed - record this request
                self._store[key].append(now)
                return True, {
                    'limit': max_requests,
                    'remaining': max_requests - current_count - 1,
                    'retry_after': 0,
                    'window': window_seconds,
                }
            else:
                # Denied - calculate when the oldest request in window expires
                oldest = self._store[key][0] if self._store[key] else now
                retry_after = int(oldest + window_seconds - now) + 1
                return False, {
                    'limit': max_requests,
                    'remaining': 0,
                    'retry_after': max(1, retry_after),
                    'window': window_seconds,
                }

    def reset(self, key: str):
        """Reset rate limit for a specific key (e.g., on successful login)."""
        with self._lock:
            self._store.pop(key, None)

    def _cleanup(self, cutoff: float):
        """Remove keys with no recent activity to prevent memory growth."""
        keys_to_remove = []
        for key, timestamps in self._store.items():
            # Remove expired timestamps
            self._store[key] = [ts for ts in timestamps if ts > cutoff]
            # Mark empty keys for removal
            if not self._store[key]:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._store[key]


# Global singleton instance
_limiter = RateLimiter()


def get_client_ip() -> str:
    """Get the real client IP, respecting X-Forwarded-For header."""
    # Check for proxy headers (common in production behind nginx/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        # Take the first IP (client IP) from the chain
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


def rate_limit(max_requests: int = 100, window_seconds: int = 60,
               key_func: str = 'ip', error_message: Optional[str] = None):
    """Decorator to apply rate limiting to Flask endpoints.

    Args:
        max_requests: Maximum requests allowed in the window
        window_seconds: Time window in seconds
        key_func: How to identify the requester:
            - 'ip': Rate limit by client IP address
            - 'user': Rate limit by authenticated user ID
            - 'ip_and_endpoint': Rate limit by IP + endpoint combination
        error_message: Custom error message for 429 response
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Build the rate limit key
            if key_func == 'user':
                user_id = getattr(g, 'user_id', None)
                if user_id:
                    key = f"user:{user_id}:{request.endpoint}"
                else:
                    key = f"ip:{get_client_ip()}:{request.endpoint}"
            elif key_func == 'ip_and_endpoint':
                key = f"ip:{get_client_ip()}:{request.endpoint}"
            else:  # 'ip'
                key = f"ip:{get_client_ip()}"

            allowed, info = _limiter.check(key, max_requests, window_seconds)

            if not allowed:
                msg = error_message or 'Rate limit exceeded. Please try again later.'
                response = jsonify({
                    'error': msg,
                    'error_code': 'RATE_LIMITED',
                    'retry_after': info['retry_after'],
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(info['retry_after'])
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                return response

            # Execute the endpoint and add rate limit headers to response
            result = f(*args, **kwargs)

            # Add rate limit headers to successful responses
            if isinstance(result, tuple):
                response_obj, status_code = result[0], result[1]
            else:
                response_obj = result
                status_code = 200

            # Only add headers if response_obj is a Flask Response
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Limit'] = str(info['limit'])
                response_obj.headers['X-RateLimit-Remaining'] = str(info['remaining'])

            return result

        return decorated
    return decorator


def get_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _limiter
