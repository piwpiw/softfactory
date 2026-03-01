"""
SoftFactory — Startup Configuration Validator
Validates required and recommended environment variables on app start.
Call validate_config(app) inside create_app() before returning.
"""
import os
import logging

logger = logging.getLogger('config_validator')

# Variables that MUST be set in production (app will warn loudly if missing)
REQUIRED_PROD = [
    'JWT_SECRET',
    'DATABASE_URL',
]

# Variables that are strongly recommended for full functionality
RECOMMENDED = [
    'ANTHROPIC_API_KEY',   # AI features (Claude)
    'SENTRY_DSN',          # Error monitoring
    'EMAIL_PROVIDER',      # Transactional email (SendGrid etc.)
    'STRIPE_SECRET_KEY',   # Payment processing
    'REDIS_URL',           # Token blacklist / rate limiting at scale
    'CORS_ALLOWED_ORIGIN', # Production frontend domain
]

# Variables required only for specific features (warn if feature is likely in use)
FEATURE_SPECIFIC = {
    'GOOGLE_CLIENT_ID':      'Google OAuth login',
    'FACEBOOK_APP_ID':       'Facebook OAuth login',
    'KAKAO_REST_API_KEY':    'Kakao OAuth login',
    'TELEGRAM_BOT_TOKEN':    'Telegram bot notifications',
    'SENDGRID_API_KEY':      'Email delivery via SendGrid',
    'AWS_ACCESS_KEY_ID':     'AWS services (S3 file storage etc.)',
}


def validate_config(app) -> None:
    """
    Validate application configuration on startup.

    In production mode: logs ERROR for missing REQUIRED_PROD variables.
    In all modes: logs WARNING for missing RECOMMENDED variables.

    Args:
        app: Flask application instance
    """
    is_production = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    env_label = 'PRODUCTION' if is_production else 'DEVELOPMENT'

    logger.info(f'[ConfigValidator] Running in {env_label} mode — checking configuration...')

    issues_found = False

    # ---- Check required production variables ----
    if is_production:
        missing_required = [var for var in REQUIRED_PROD if not os.getenv(var)]
        if missing_required:
            issues_found = True
            for var in missing_required:
                logger.error(
                    f'[ConfigValidator] CRITICAL: Required environment variable "{var}" is not set. '
                    f'The application may not function correctly in production.'
                )
            # In production, raise an exception to prevent silent failures
            raise EnvironmentError(
                f'Missing required production environment variables: {", ".join(missing_required)}. '
                f'Set these variables before starting the application in production.'
            )
    else:
        # In development, only warn about missing required vars
        missing_required = [var for var in REQUIRED_PROD if not os.getenv(var)]
        if missing_required:
            for var in missing_required:
                logger.warning(
                    f'[ConfigValidator] WARNING: "{var}" is not set. '
                    f'Using development defaults — do NOT use in production.'
                )

    # ---- Check recommended variables ----
    missing_recommended = [var for var in RECOMMENDED if not os.getenv(var)]
    if missing_recommended:
        issues_found = True
        logger.warning(
            f'[ConfigValidator] Recommended variables not set: {", ".join(missing_recommended)}. '
            f'Some features may be unavailable.'
        )
        for var in missing_recommended:
            _log_recommended_hint(var)

    # ---- Check feature-specific variables ----
    missing_features = {
        var: feature
        for var, feature in FEATURE_SPECIFIC.items()
        if not os.getenv(var)
    }
    if missing_features:
        logger.info(
            f'[ConfigValidator] Feature-specific variables not configured: '
            + ', '.join(f'{v} ({f})' for v, f in missing_features.items())
        )

    # ---- Summary ----
    if not issues_found:
        logger.info('[ConfigValidator] All required and recommended variables are set.')
    else:
        logger.warning(
            '[ConfigValidator] Configuration check complete with warnings. '
            'Review the log messages above.'
        )


def _log_recommended_hint(var: str) -> None:
    """Log a helpful hint for a missing recommended variable."""
    hints = {
        'ANTHROPIC_API_KEY': (
            'Get your API key at https://console.anthropic.com — required for AI automation features.'
        ),
        'SENTRY_DSN': (
            'Create a Sentry project at https://sentry.io — strongly recommended for production error tracking.'
        ),
        'EMAIL_PROVIDER': (
            'Set to "sendgrid" or "smtp". Required for welcome emails, password reset, and account deletion confirmation.'
        ),
        'STRIPE_SECRET_KEY': (
            'Get your key at https://dashboard.stripe.com — required for subscription billing.'
        ),
        'REDIS_URL': (
            'Set to redis://localhost:6379 (local) or a managed Redis URL. '
            'Required for distributed rate limiting and token blacklisting in multi-process deployments.'
        ),
        'CORS_ALLOWED_ORIGIN': (
            'Set to your production frontend URL (e.g. https://softfactory.kr) to lock down CORS.'
        ),
    }
    hint = hints.get(var)
    if hint:
        logger.info(f'[ConfigValidator]   Hint for {var}: {hint}')
