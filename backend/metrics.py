"""
Metrics and Health Check Endpoints for Monitoring
Provides /api/health, /api/metrics/prometheus, and /api/metrics/summary endpoints
"""

import psutil
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, g
from .models import db, User, Payment, Booking, SNSPost, Campaign, AIEmployee

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

# Global startup time (for uptime calculation)
_startup_time = time.time()
_request_count = 0
_error_count = 0


def increment_request_count():
    """Increment total request counter"""
    global _request_count
    _request_count += 1


def increment_error_count():
    """Increment error counter"""
    global _error_count
    _error_count += 1


def get_uptime_seconds():
    """Get application uptime in seconds"""
    return int(time.time() - _startup_time)


def get_memory_usage():
    """Get current process memory usage"""
    process = psutil.Process(os.getpid())
    return {
        'rss_mb': round(process.memory_info().rss / 1024 / 1024, 2),  # Resident set size
        'vms_mb': round(process.memory_info().vms / 1024 / 1024, 2),  # Virtual memory
        'percent': round(process.memory_percent(), 2)
    }


def get_cpu_usage():
    """Get CPU usage percentage"""
    return round(psutil.cpu_percent(interval=0.1), 2)


def check_database_health():
    """Check database connectivity"""
    try:
        # Try to query the database
        User.query.first()
        return {'status': 'healthy', 'latency_ms': 0}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def get_database_stats():
    """Get database statistics"""
    try:
        return {
            'users': User.query.count(),
            'payments': Payment.query.count(),
            'bookings': Booking.query.count(),
            'sns_posts': SNSPost.query.count(),
            'campaigns': Campaign.query.count(),
            'ai_employees': AIEmployee.query.count()
        }
    except Exception as e:
        return {'error': str(e)}


# ============ HEALTH CHECK ENDPOINTS ============

@metrics_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Used by load balancers and monitoring systems for liveness probe

    Returns: 200 if healthy, 503 if not
    """
    db_health = check_database_health()

    overall_status = 'healthy' if db_health['status'] == 'healthy' else 'degraded'

    return jsonify({
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'uptime_seconds': get_uptime_seconds(),
        'database': db_health['status'],
        'api': 'ok'
    }), 200 if overall_status == 'healthy' else 503


@metrics_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint
    Kubernetes-compatible readiness probe
    Indicates if service is ready to accept traffic

    Checks:
    - Database is accessible
    - Critical services initialized
    """
    try:
        # Check database
        db_health = check_database_health()
        if db_health['status'] != 'healthy':
            return jsonify({'ready': False, 'reason': 'Database unavailable'}), 503

        return jsonify({
            'ready': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200

    except Exception as e:
        return jsonify({'ready': False, 'error': str(e)}), 503


@metrics_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    Liveness check endpoint
    Kubernetes-compatible liveness probe
    Indicates if service process is still running (minimal checks)
    """
    return jsonify({
        'alive': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'pid': os.getpid()
    }), 200


# ============ DETAILED METRICS ENDPOINTS ============

@metrics_bp.route('/summary', methods=['GET'])
def metrics_summary():
    """
    Comprehensive metrics summary endpoint
    Shows system health, performance, and database statistics

    Format: application/json (not Prometheus format)
    """
    memory_info = get_memory_usage()
    db_stats = get_database_stats()
    cpu_info = get_cpu_usage()

    return jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'uptime': {
            'seconds': get_uptime_seconds(),
            'human_readable': _format_uptime(get_uptime_seconds())
        },
        'system': {
            'cpu_percent': cpu_info,
            'memory': memory_info,
            'process_id': os.getpid()
        },
        'application': {
            'requests_total': _request_count,
            'errors_total': _error_count,
            'error_rate': round(_error_count / max(_request_count, 1) * 100, 2)
        },
        'database': {
            'status': check_database_health()['status'],
            'stats': db_stats
        }
    }), 200


@metrics_bp.route('/prometheus', methods=['GET'])
def prometheus_metrics():
    """
    Prometheus-format metrics endpoint
    Compatible with Prometheus scrape configuration

    Metrics exported:
    - softfactory_up (gauge: 1=healthy, 0=unhealthy)
    - softfactory_uptime_seconds
    - softfactory_requests_total
    - softfactory_errors_total
    - softfactory_memory_rss_mb
    - softfactory_memory_percent
    - softfactory_cpu_percent
    - softfactory_database_users
    - softfactory_database_payments
    - softfactory_database_bookings
    """
    memory_info = get_memory_usage()
    db_stats = get_database_stats()
    db_health = check_database_health()
    cpu_info = get_cpu_usage()

    # Build Prometheus metrics output
    metrics_output = []

    # Add HELP and TYPE for each metric
    metrics_output.append('# HELP softfactory_up Application health status (1=healthy)')
    metrics_output.append('# TYPE softfactory_up gauge')
    metrics_output.append(f'softfactory_up {1 if db_health["status"] == "healthy" else 0}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_uptime_seconds Application uptime in seconds')
    metrics_output.append('# TYPE softfactory_uptime_seconds gauge')
    metrics_output.append(f'softfactory_uptime_seconds {get_uptime_seconds()}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_requests_total Total HTTP requests received')
    metrics_output.append('# TYPE softfactory_requests_total counter')
    metrics_output.append(f'softfactory_requests_total {_request_count}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_errors_total Total HTTP errors (5xx, 4xx)')
    metrics_output.append('# TYPE softfactory_errors_total counter')
    metrics_output.append(f'softfactory_errors_total {_error_count}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_memory_rss_mb Resident set size in MB')
    metrics_output.append('# TYPE softfactory_memory_rss_mb gauge')
    metrics_output.append(f'softfactory_memory_rss_mb {memory_info["rss_mb"]}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_memory_percent Memory usage percentage')
    metrics_output.append('# TYPE softfactory_memory_percent gauge')
    metrics_output.append(f'softfactory_memory_percent {memory_info["percent"]}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_cpu_percent CPU usage percentage')
    metrics_output.append('# TYPE softfactory_cpu_percent gauge')
    metrics_output.append(f'softfactory_cpu_percent {cpu_info}')
    metrics_output.append('')

    # Database record counts
    metrics_output.append('# HELP softfactory_database_users Total registered users')
    metrics_output.append('# TYPE softfactory_database_users gauge')
    metrics_output.append(f'softfactory_database_users {db_stats.get("users", 0)}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_database_payments Total payments')
    metrics_output.append('# TYPE softfactory_database_payments gauge')
    metrics_output.append(f'softfactory_database_payments {db_stats.get("payments", 0)}')
    metrics_output.append('')

    metrics_output.append('# HELP softfactory_database_bookings Total bookings')
    metrics_output.append('# TYPE softfactory_database_bookings gauge')
    metrics_output.append(f'softfactory_database_bookings {db_stats.get("bookings", 0)}')
    metrics_output.append('')

    return '\n'.join(metrics_output), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@metrics_bp.route('/errors', methods=['GET'])
def error_metrics():
    """
    Error rate metrics endpoint
    Shows error counts and rates
    """
    total_requests = max(_request_count, 1)

    return jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'total_requests': _request_count,
        'total_errors': _error_count,
        'error_rate_percent': round(_error_count / total_requests * 100, 2),
        'success_rate_percent': round((total_requests - _error_count) / total_requests * 100, 2)
    }), 200


def _format_uptime(seconds):
    """Format uptime in human-readable format"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f'{days}d')
    if hours > 0:
        parts.append(f'{hours}h')
    if minutes > 0:
        parts.append(f'{minutes}m')
    if secs > 0 or not parts:
        parts.append(f'{secs}s')

    return ' '.join(parts)


def register_metrics_middleware(app):
    """Register middleware to track request/error counts"""
    @app.before_request
    def before_request_metrics():
        increment_request_count()

    @app.after_request
    def after_request_metrics(response):
        # Count 4xx and 5xx responses as errors
        if response.status_code >= 400:
            increment_error_count()
        return response
