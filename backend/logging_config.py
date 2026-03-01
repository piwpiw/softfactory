"""
Structured Logging Configuration for SoftFactory
Provides JSON-formatted logs with request tracking, correlation IDs, and metrics
"""

import logging
import json
import time
import uuid
from datetime import datetime
from functools import wraps
from flask import request, g
from pythonjsonlogger import jsonlogger


class RequestIdFilter(logging.Filter):
    """Filter to inject request ID (correlation ID) into log records"""

    def filter(self, record):
        if hasattr(g, 'request_id'):
            record.request_id = g.request_id
        else:
            record.request_id = getattr(request, 'request_id', 'N/A')
        return True


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with consistent field names"""

    def add_fields(self, log_record, record, message_dict):
        super(JSONFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        log_record['level'] = record.levelname

        # Add module and function info
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line_number'] = record.lineno

        # Add request context if available
        if hasattr(g, 'request_id'):
            log_record['request_id'] = g.request_id
        if hasattr(g, 'user_id'):
            log_record['user_id'] = g.user_id


def configure_logging(app, log_file='logs/app.log', debug=False):
    """
    Configure structured JSON logging for the Flask application

    Args:
        app: Flask application instance
        log_file: Path to log file (creates directory if missing)
        debug: Enable debug-level logging
    """
    import os

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Remove default Flask logger handlers
    app.logger.handlers.clear()

    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    app.logger.setLevel(log_level)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = JSONFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RequestIdFilter())
    app.logger.addHandler(file_handler)

    # Console handler for development (also JSON)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(file_formatter)
    console_handler.addFilter(RequestIdFilter())
    if debug:
        app.logger.addHandler(console_handler)

    # Set werkzeug logger level (Flask's underlying server)
    logging.getLogger('werkzeug').setLevel(logging.WARNING if not debug else logging.DEBUG)

    return app.logger


def request_logging_middleware(app):
    """
    Middleware to log all HTTP requests with timing and status

    Logs:
    - request_id (unique correlation ID)
    - method, path, query_string
    - request body (if present)
    - response status and size
    - latency (ms)
    - user_id (if authenticated)
    """

    @app.before_request
    def before_request():
        """Generate request ID and start timing"""
        g.request_id = str(uuid.uuid4())[:8]
        g.request_start_time = time.time()

        # Log incoming request
        app.logger.info(
            'Request received',
            extra={
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8') if request.query_string else '',
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string if request.user_agent else ''
            }
        )

    @app.after_request
    def after_request(response):
        """Log response with timing"""
        if hasattr(g, 'request_start_time'):
            latency_ms = (time.time() - g.request_start_time) * 1000
        else:
            latency_ms = 0

        # Determine if response is error
        log_level = 'ERROR' if response.status_code >= 500 else \
                   'WARNING' if response.status_code >= 400 else 'INFO'

        app.logger.log(
            getattr(logging, log_level),
            f'Request completed: {response.status_code}',
            extra={
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'content_length': response.content_length or 0,
                'latency_ms': round(latency_ms, 2),
                'request_id': g.request_id
            }
        )

        # Add request ID to response headers for client-side tracing
        response.headers['X-Request-Id'] = g.request_id

        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log unhandled exceptions"""
        app.logger.exception(
            'Unhandled exception',
            extra={
                'method': request.method,
                'path': request.path,
                'error_type': type(e).__name__,
                'request_id': g.request_id
            }
        )
        raise


def setup_metrics_collection(app):
    """
    Setup metrics collection for Prometheus
    Tracks: request count, latency, error rate by endpoint
    """

    metrics = {
        'requests_total': {},          # {method}_{path}: count
        'request_latency_ms': {},      # {method}_{path}: [latencies]
        'requests_by_status': {},      # {status}: count
        'requests_by_user': {},        # {user_id}: count
    }

    @app.before_request
    def collect_request_metrics():
        g.metrics_start = time.time()

    @app.after_request
    def collect_response_metrics(response):
        if not hasattr(g, 'metrics_start'):
            return response

        latency_ms = (time.time() - g.metrics_start) * 1000
        endpoint_key = f"{request.method}_{request.path}"
        status_key = response.status_code

        # Count requests
        metrics['requests_total'][endpoint_key] = \
            metrics['requests_total'].get(endpoint_key, 0) + 1

        # Track latencies
        if endpoint_key not in metrics['request_latency_ms']:
            metrics['request_latency_ms'][endpoint_key] = []
        metrics['request_latency_ms'][endpoint_key].append(latency_ms)

        # Count by status
        metrics['requests_by_status'][status_key] = \
            metrics['requests_by_status'].get(status_key, 0) + 1

        # Count by user
        if hasattr(g, 'user_id'):
            metrics['requests_by_user'][g.user_id] = \
                metrics['requests_by_user'].get(g.user_id, 0) + 1

        return response

    return metrics


def setup_logging(app):
    """
    Setup logging for the Flask application

    Args:
        app: Flask application instance
    """
    # Configure JSON logging
    json_handler = logging.StreamHandler()
    json_formatter = JSONFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    json_handler.setFormatter(json_formatter)
    json_handler.addFilter(RequestIdFilter())

    # Add handlers to app logger
    if app.logger.hasHandlers() is False:
        app.logger.addHandler(json_handler)
        app.logger.setLevel(logging.INFO)

    # Setup metrics collection
    setup_metrics_collection(app)

    return app


def get_logger(name):
    """
    Get a configured logger for a module

    Usage:
        from backend.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info('Event', extra={'key': 'value'})
    """
    return logging.getLogger(name)
