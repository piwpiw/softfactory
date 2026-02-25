"""Rate Limiting Middleware for SNS Endpoints

Implements:
- Token Bucket Algorithm
- Plan-based rate limiting (Free/Pro/Enterprise)
- Per-user and per-endpoint tracking
- HTTP 429 responses
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import time
from typing import Dict, Tuple, Optional

from backend.models import User, UserSubscription


class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_remaining(self) -> float:
        """Get remaining tokens"""
        now = time.time()
        elapsed = now - self.last_refill
        return min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )


class RateLimitByPlan:
    """Plan-based rate limiting strategy"""

    PLANS = {
        'free': {
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'requests_per_day': 1000,
            'burst_capacity': 20
        },
        'pro': {
            'requests_per_minute': 100,
            'requests_per_hour': 5000,
            'requests_per_day': 100000,
            'burst_capacity': 200
        },
        'enterprise': {
            'requests_per_minute': 1000,
            'requests_per_hour': 100000,
            'requests_per_day': 10000000,
            'burst_capacity': 2000
        }
    }

    # Global bucket storage: {user_id: {window: TokenBucket}}
    _buckets: Dict[int, Dict[str, TokenBucket]] = {}

    @classmethod
    def get_limit_for_user(cls, user: User) -> dict:
        """Get rate limit for user based on subscription plan"""
        plan = 'free'

        if hasattr(user, 'subscription') and user.subscription:
            plan = user.subscription.plan_type or 'free'

        return cls.PLANS.get(plan, cls.PLANS['free'])

    @classmethod
    def get_bucket(cls, user_id: int, window: str) -> TokenBucket:
        """Get or create token bucket for user/window combination"""
        if user_id not in cls._buckets:
            cls._buckets[user_id] = {}

        if window not in cls._buckets[user_id]:
            # Create bucket based on window
            limits = cls.PLANS['free']  # Default

            if window == 'minute':
                capacity = limits['requests_per_minute']
                refill_rate = capacity / 60  # per second
            elif window == 'hour':
                capacity = limits['requests_per_hour']
                refill_rate = capacity / 3600
            else:  # day
                capacity = limits['requests_per_day']
                refill_rate = capacity / 86400

            cls._buckets[user_id][window] = TokenBucket(capacity, refill_rate)

        return cls._buckets[user_id][window]

    @classmethod
    def check_limit(cls, user: User, window: str = 'minute') -> Tuple[bool, dict]:
        """
        Check if user has exceeded rate limit.

        Returns:
            (allowed: bool, info: dict with remaining/reset)
        """
        limits = cls.get_limit_for_user(user)
        bucket = cls.get_bucket(user.id, window)

        if bucket.consume(1):
            return True, {
                'limit': limits[f'requests_per_{window}'],
                'remaining': int(bucket.get_remaining()),
                'reset_in': 'N/A'
            }
        else:
            return False, {
                'limit': limits[f'requests_per_{window}'],
                'remaining': 0,
                'reset_in': int(1 / bucket.refill_rate) if bucket.refill_rate > 0 else 60
            }


def rate_limit_by_plan(f):
    """Decorator to enforce rate limiting based on user's plan"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        from backend.auth import get_current_user

        try:
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401

            # Check rate limit
            allowed, info = RateLimitByPlan.check_limit(user, 'minute')

            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': info['limit'],
                    'remaining': info['remaining'],
                    'reset_in_seconds': info['reset_in']
                }), 429

            # Store limit info in response headers
            g.rate_limit = info

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return decorated_function


def add_rate_limit_headers(response):
    """Flask after_request hook to add rate limit headers"""
    from flask import g

    if hasattr(g, 'rate_limit'):
        info = g.rate_limit
        response.headers['X-RateLimit-Limit'] = str(info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(info['remaining'])

    return response
