"""
Metrics Service — Enhanced Prometheus Integration
Provides additional metrics beyond Flask's built-in telemetry
"""

import time
import threading
from contextlib import contextmanager
from typing import Dict, Optional
from functools import wraps

# Thread-safe metric storage
_METRICS_LOCK = threading.Lock()

class MetricsCollector:
    """Collects application metrics for Prometheus export"""

    def __init__(self):
        self._lock = threading.Lock()
        self.db_query_metrics = {}  # endpoint → {count, total_ms, errors}
        self.cache_metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }
        self.auth_metrics = {
            'successful_logins': 0,
            'failed_logins': 0,
            'token_validations': 0,
            'token_failures': 0,
        }
        self.email_metrics = {
            'sent': 0,
            'failed': 0,
        }
        self.notification_metrics = {
            'sent': 0,
            'failed': 0,
        }

    def record_db_query(self, endpoint: str, duration_ms: float, error: bool = False):
        """Record database query metrics"""
        with self._lock:
            if endpoint not in self.db_query_metrics:
                self.db_query_metrics[endpoint] = {'count': 0, 'total_ms': 0, 'errors': 0}

            self.db_query_metrics[endpoint]['count'] += 1
            self.db_query_metrics[endpoint]['total_ms'] += duration_ms
            if error:
                self.db_query_metrics[endpoint]['errors'] += 1

    def record_cache_hit(self):
        """Record cache hit"""
        with self._lock:
            self.cache_metrics['hits'] += 1

    def record_cache_miss(self):
        """Record cache miss"""
        with self._lock:
            self.cache_metrics['misses'] += 1

    def record_cache_eviction(self):
        """Record cache eviction"""
        with self._lock:
            self.cache_metrics['evictions'] += 1

    def record_successful_login(self):
        """Record successful login"""
        with self._lock:
            self.auth_metrics['successful_logins'] += 1

    def record_failed_login(self):
        """Record failed login"""
        with self._lock:
            self.auth_metrics['failed_logins'] += 1

    def record_token_validation(self, success: bool = True):
        """Record token validation attempt"""
        with self._lock:
            if success:
                self.auth_metrics['token_validations'] += 1
            else:
                self.auth_metrics['token_failures'] += 1

    def record_email_sent(self, success: bool = True):
        """Record email send attempt"""
        with self._lock:
            if success:
                self.email_metrics['sent'] += 1
            else:
                self.email_metrics['failed'] += 1

    def record_notification_sent(self, success: bool = True):
        """Record notification send attempt"""
        with self._lock:
            if success:
                self.notification_metrics['sent'] += 1
            else:
                self.notification_metrics['failed'] += 1

    def get_snapshot(self) -> Dict:
        """Get current metrics snapshot"""
        with self._lock:
            return {
                'db_query_metrics': dict(self.db_query_metrics),
                'cache_metrics': dict(self.cache_metrics),
                'auth_metrics': dict(self.auth_metrics),
                'email_metrics': dict(self.email_metrics),
                'notification_metrics': dict(self.notification_metrics),
            }

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        snap = self.get_snapshot()
        lines = []

        # Database query metrics
        lines.append('# HELP db_query_count Total database queries by endpoint')
        lines.append('# TYPE db_query_count counter')
        for endpoint, data in snap['db_query_metrics'].items():
            lines.append(f'db_query_count{{endpoint="{endpoint}"}} {data["count"]}')

        lines.append('# HELP db_query_duration_ms Average query duration')
        lines.append('# TYPE db_query_duration_ms gauge')
        for endpoint, data in snap['db_query_metrics'].items():
            if data['count'] > 0:
                avg_ms = data['total_ms'] / data['count']
                lines.append(f'db_query_duration_ms{{endpoint="{endpoint}"}} {avg_ms:.2f}')

        lines.append('# HELP db_query_errors Database query errors')
        lines.append('# TYPE db_query_errors counter')
        for endpoint, data in snap['db_query_metrics'].items():
            if data['errors'] > 0:
                lines.append(f'db_query_errors{{endpoint="{endpoint}"}} {data["errors"]}')

        # Cache metrics
        lines.append('# HELP cache_hits_total Cache hits')
        lines.append('# TYPE cache_hits_total counter')
        lines.append(f'cache_hits_total {snap["cache_metrics"]["hits"]}')

        lines.append('# HELP cache_misses_total Cache misses')
        lines.append('# TYPE cache_misses_total counter')
        lines.append(f'cache_misses_total {snap["cache_metrics"]["misses"]}')

        lines.append('# HELP cache_evictions_total Cache evictions')
        lines.append('# TYPE cache_evictions_total counter')
        lines.append(f'cache_evictions_total {snap["cache_metrics"]["evictions"]}')

        if snap['cache_metrics']['hits'] + snap['cache_metrics']['misses'] > 0:
            hit_ratio = (snap['cache_metrics']['hits'] /
                         (snap['cache_metrics']['hits'] + snap['cache_metrics']['misses']))
            lines.append('# HELP cache_hit_ratio Cache hit ratio')
            lines.append('# TYPE cache_hit_ratio gauge')
            lines.append(f'cache_hit_ratio {hit_ratio:.2%}')

        # Authentication metrics
        lines.append('# HELP auth_successful_logins Total successful logins')
        lines.append('# TYPE auth_successful_logins counter')
        lines.append(f'auth_successful_logins {snap["auth_metrics"]["successful_logins"]}')

        lines.append('# HELP auth_failed_logins Total failed login attempts')
        lines.append('# TYPE auth_failed_logins counter')
        lines.append(f'auth_failed_logins {snap["auth_metrics"]["failed_logins"]}')

        lines.append('# HELP auth_token_validations Token validation attempts')
        lines.append('# TYPE auth_token_validations counter')
        lines.append(f'auth_token_validations {snap["auth_metrics"]["token_validations"]}')

        lines.append('# HELP auth_token_failures Token validation failures')
        lines.append('# TYPE auth_token_failures counter')
        lines.append(f'auth_token_failures {snap["auth_metrics"]["token_failures"]}')

        # Email metrics
        lines.append('# HELP email_sent_total Emails successfully sent')
        lines.append('# TYPE email_sent_total counter')
        lines.append(f'email_sent_total {snap["email_metrics"]["sent"]}')

        lines.append('# HELP email_failed_total Failed email attempts')
        lines.append('# TYPE email_failed_total counter')
        lines.append(f'email_failed_total {snap["email_metrics"]["failed"]}')

        # Notification metrics
        lines.append('# HELP notification_sent_total Notifications successfully sent')
        lines.append('# TYPE notification_sent_total counter')
        lines.append(f'notification_sent_total {snap["notification_metrics"]["sent"]}')

        lines.append('# HELP notification_failed_total Failed notification attempts')
        lines.append('# TYPE notification_failed_total counter')
        lines.append(f'notification_failed_total {snap["notification_metrics"]["failed"]}')

        return '\n'.join(lines)


# Global instance
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Get the global metrics collector"""
    return _collector


@contextmanager
def measure_db_query(endpoint: str):
    """Context manager to measure database query duration"""
    start_time = time.time()
    error = False
    try:
        yield
    except Exception:
        error = True
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        _collector.record_db_query(endpoint, duration_ms, error)


def record_db_query_decorator(endpoint: Optional[str] = None):
    """Decorator to record database query metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query_endpoint = endpoint or func.__name__
            with measure_db_query(query_endpoint):
                return func(*args, **kwargs)
        return wrapper
    return decorator
