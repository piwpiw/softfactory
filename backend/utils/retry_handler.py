"""Retry and Error Handling for SNS API Calls

Implements:
- Exponential backoff retry
- Circuit breaker pattern
- Graceful degradation
- Error categorization
"""

import time
import random
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categorize errors for retry decisions"""
    RETRYABLE = 1      # Temporary failure - retry
    PERMANENT = 2      # Permanent failure - don't retry
    RATE_LIMIT = 3     # Rate limited - retry with backoff
    NETWORK = 4        # Network error - retry
    AUTH = 5           # Authentication error - don't retry


class ErrorHandler:
    """Categorize and handle API errors"""

    @staticmethod
    def categorize_error(error: Exception, status_code: Optional[int] = None) -> ErrorCategory:
        """Categorize error for retry decision"""
        error_msg = str(error).lower()

        # Rate limit errors
        if status_code == 429 or 'rate' in error_msg:
            return ErrorCategory.RATE_LIMIT

        # Network errors
        if status_code in [408, 502, 503, 504] or any(x in error_msg for x in ['connection', 'timeout', 'network']):
            return ErrorCategory.NETWORK

        # Authentication errors
        if status_code in [401, 403] or any(x in error_msg for x in ['unauthorized', 'forbidden', 'invalid_token']):
            return ErrorCategory.AUTH

        # Server errors (retryable)
        if status_code and status_code >= 500:
            return ErrorCategory.RETRYABLE

        # Client errors (not retryable)
        if status_code and 400 <= status_code < 500:
            return ErrorCategory.PERMANENT

        return ErrorCategory.RETRYABLE

    @staticmethod
    def should_retry(category: ErrorCategory, attempt: int, max_retries: int) -> bool:
        """Determine if error should be retried"""
        if attempt >= max_retries:
            return False

        if category == ErrorCategory.PERMANENT or category == ErrorCategory.AUTH:
            return False

        return True


class ExponentialBackoff:
    """Exponential backoff with jitter"""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, multiplier: float = 2.0):
        """
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Multiplier for each retry
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt number (0-indexed)"""
        delay = self.base_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)

        # Add jitter (±10%)
        jitter = delay * 0.1 * (2 * random.random() - 1)
        return delay + jitter

    def sleep(self, attempt: int) -> None:
        """Sleep before retry"""
        delay = self.calculate_delay(attempt)
        logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1})")
        time.sleep(delay)


class CircuitBreaker:
    """Circuit breaker pattern for failing services"""

    class State(Enum):
        CLOSED = 1      # Normal operation
        OPEN = 2        # Failing - reject requests
        HALF_OPEN = 3   # Testing recovery

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        """
        Args:
            failure_threshold: Failures before opening circuit
            reset_timeout: Seconds before trying recovery
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self.state = self.State.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    def record_success(self) -> None:
        """Record successful call"""
        self.failure_count = 0
        self.success_count += 1

        if self.state == self.State.HALF_OPEN:
            self.state = self.State.CLOSED
            logger.info("Circuit breaker CLOSED (recovered)")

    def record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

    def can_execute(self) -> bool:
        """Check if request should be allowed"""
        if self.state == self.State.CLOSED:
            return True

        if self.state == self.State.OPEN:
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = self.State.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker HALF_OPEN (testing recovery)")
                return True
            return False

        # HALF_OPEN - allow one request
        return True

    def get_state(self) -> str:
        """Get current state"""
        return self.state.name


class RetryWithBackoff:
    """Retry decorator with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 exception_types: tuple = (Exception,)):
        self.max_retries = max_retries
        self.backoff = ExponentialBackoff(base_delay=base_delay)
        self.exception_types = exception_types

    def __call__(self, f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(self.max_retries):
                try:
                    return f(*args, **kwargs)
                except self.exception_types as e:
                    last_exception = e
                    status_code = getattr(e, 'status_code', None)

                    category = ErrorHandler.categorize_error(e, status_code)
                    should_retry = ErrorHandler.should_retry(category, attempt, self.max_retries)

                    if not should_retry:
                        logger.error(f"Not retrying {category.name} error: {e}")
                        raise

                    if attempt < self.max_retries - 1:
                        self.backoff.sleep(attempt)
                    else:
                        logger.error(f"Max retries exceeded for {f.__name__}")

            raise last_exception

        return wrapper


class PlatformCircuitBreaker:
    """Manage circuit breakers for different platforms"""

    _breakers: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_breaker(cls, platform: str) -> CircuitBreaker:
        """Get or create circuit breaker for platform"""
        if platform not in cls._breakers:
            cls._breakers[platform] = CircuitBreaker(
                failure_threshold=5,
                reset_timeout=60
            )
        return cls._breakers[platform]

    @classmethod
    def call_with_circuit_break(cls, platform: str, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection"""
        breaker = cls.get_breaker(platform)

        if not breaker.can_execute():
            raise Exception(f"Circuit breaker for {platform} is OPEN")

        try:
            result = func(*args, **kwargs)
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise

    @classmethod
    def get_status(cls) -> Dict[str, str]:
        """Get status of all circuit breakers"""
        return {platform: breaker.get_state() for platform, breaker in cls._breakers.items()}


# Convenience decorators

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for automatic retry"""
    return RetryWithBackoff(max_retries=max_retries, base_delay=base_delay)


def with_circuit_breaker(platform: str):
    """Decorator for circuit breaker protection"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return PlatformCircuitBreaker.call_with_circuit_break(platform, f, *args, **kwargs)
        return wrapper
    return decorator
