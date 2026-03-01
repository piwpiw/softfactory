"""Backend Utilities Package

Utility modules for advanced features:
- cache_manager: Advanced caching with invalidation
- pagination: Cursor and offset-based pagination
- retry_handler: Exponential backoff and circuit breaker
"""

from .cache_manager import (
    AdvancedCache,
    ETagGenerator,
    CacheInvalidationStrategy,
    CacheWarmer,
    get_cache,
    conditional_response,
    cached_endpoint
)

from .pagination import (
    CursorPagination,
    OffsetPagination,
    FieldFilter,
    PaginationMixin
)

from .retry_handler import (
    ErrorCategory,
    ErrorHandler,
    ExponentialBackoff,
    CircuitBreaker,
    RetryWithBackoff,
    PlatformCircuitBreaker,
    retry_with_backoff,
    with_circuit_breaker
)

__all__ = [
    # Cache
    'AdvancedCache',
    'ETagGenerator',
    'CacheInvalidationStrategy',
    'CacheWarmer',
    'get_cache',
    'conditional_response',
    'cached_endpoint',

    # Pagination
    'CursorPagination',
    'OffsetPagination',
    'FieldFilter',
    'PaginationMixin',

    # Retry/Circuit Breaker
    'ErrorCategory',
    'ErrorHandler',
    'ExponentialBackoff',
    'CircuitBreaker',
    'RetryWithBackoff',
    'PlatformCircuitBreaker',
    'retry_with_backoff',
    'with_circuit_breaker'
]
