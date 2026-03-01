"""Monitoring & Error Tracking — Sentry integration + sensitive-data scrubbing.

Usage:
    from .monitoring import init_sentry
    init_sentry(app)   # called once inside create_app()

Sentry is optional: if SENTRY_DSN is not set the function returns silently so
the rest of the application works without any change.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Fields whose values must be redacted before being sent to Sentry
_SENSITIVE_KEYS = frozenset({
    'password', 'password_hash', 'passwd', 'secret', 'token',
    'access_token', 'refresh_token', 'authorization', 'auth',
    'credit_card', 'card_number', 'cvv', 'ssn', 'api_key',
    'stripe_token', 'jwt', 'session', 'cookie',
})

_REDACTED = '[REDACTED]'


def _scrub_dict(obj, depth=0):
    """Recursively scrub sensitive keys from a dict / list structure.

    Stops recursing at depth 10 to avoid unbounded work on deeply nested
    Sentry event payloads.
    """
    if depth > 10:
        return obj
    if isinstance(obj, dict):
        return {
            k: _REDACTED if k.lower() in _SENSITIVE_KEYS else _scrub_dict(v, depth + 1)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub_dict(item, depth + 1) for item in obj]
    return obj


def filter_sensitive_data(event, hint):
    """Sentry ``before_send`` hook — strip passwords, tokens, etc.

    Modifies the event in-place and returns it.  Returning ``None`` would
    drop the event entirely; we never do that here so every error is still
    reported (just without sensitive values).
    """
    # Scrub request body / form data
    request_info = event.get('request', {})
    if 'data' in request_info:
        request_info['data'] = _scrub_dict(request_info['data'])
    # Scrub query-string parameters
    if 'query_string' in request_info:
        request_info['query_string'] = _scrub_dict(request_info['query_string'])
    # Scrub request headers (e.g. Authorization)
    if 'headers' in request_info:
        request_info['headers'] = _scrub_dict(request_info['headers'])
    # Scrub any extra context attached by application code
    if 'extra' in event:
        event['extra'] = _scrub_dict(event['extra'])
    # Scrub exception values that might contain passwords in message strings
    for exc in event.get('exception', {}).get('values', []):
        val = exc.get('value', '')
        if isinstance(val, str):
            for key in _SENSITIVE_KEYS:
                # Very basic pattern: "password=abc123" → "password=[REDACTED]"
                import re
                val = re.sub(
                    rf'(?i)({key})\s*[:=]\s*\S+',
                    rf'\1={_REDACTED}',
                    val,
                )
            exc['value'] = val
    return event


def init_sentry(app):
    """Initialise Sentry SDK for the Flask application.

    Safe to call when SENTRY_DSN is absent — logs an info message and returns.

    Args:
        app: Flask application instance (used for logger and config).
    """
    dsn = os.getenv('SENTRY_DSN', '').strip()
    if not dsn:
        app.logger.info(
            'Sentry DSN not configured — error tracking disabled. '
            'Set SENTRY_DSN environment variable to enable.'
        )
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(transaction_style='url'),
                SqlalchemyIntegration(),
            ],
            # Capture 10 % of transactions for performance monitoring.
            # Increase in production once baseline is established.
            traces_sample_rate=0.1,
            # Capture 10 % of profiling sessions alongside traces.
            profiles_sample_rate=0.1,
            environment=os.getenv('ENVIRONMENT', 'development'),
            release=os.getenv('APP_VERSION', '1.0.0'),
            before_send=filter_sensitive_data,
            # Attach user context from g.user when available
            send_default_pii=False,  # Never send PII by default
        )
        app.logger.info(
            f"Sentry initialised (env={os.getenv('ENVIRONMENT', 'development')}, "
            f"release={os.getenv('APP_VERSION', '1.0.0')})"
        )
    except ImportError:
        app.logger.warning(
            'sentry-sdk package not installed. '
            'Run: pip install "sentry-sdk[flask]>=1.40.0"'
        )
    except Exception as exc:  # pragma: no cover
        # Never let Sentry initialisation crash the application
        app.logger.error(f'Sentry initialisation failed: {exc}')
