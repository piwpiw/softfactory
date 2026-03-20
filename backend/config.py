"""Application Configuration - Lazy Loading"""
import os
from urllib.parse import urlparse

class Config:
    """Configuration with runtime environment variable resolution"""

    # Convenience attributes used by create_app() — resolve env vars
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
    KAKAO_CLIENT_SECRET = os.getenv('KAKAO_CLIENT_SECRET')

    @staticmethod
    def get(key, default=''):
        """Runtime environment variable getter"""
        return os.getenv(key, default)

    @staticmethod
    def get_database_url() -> str:
        """Return a normalized database URL for runtime use.

        - `<...>` placeholder fragments are treated as unset
        - `postgres://` is normalized to `postgresql://`
        - placeholder tokens are discarded to avoid falling back to SQLite silently
        """
        raw = (os.getenv('DATABASE_URL') or '').strip()
        if not raw:
            return ''
        lowered = raw.lower()
        if '<' in raw or 'placeholder' in lowered or 'change_me' in lowered:
            return ''
        if raw.startswith('postgres://'):
            raw = raw.replace('postgres://', 'postgresql://', 1)
        return raw

    @staticmethod
    def is_database_url_safe(url: str) -> bool:
        """Validate that the DB URL is parsable and not an obvious local fallback."""
        if not url:
            return False
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        scheme = (parsed.scheme or '').lower()
        if not scheme:
            return False
        if scheme == 'sqlite' or scheme == 'sqlite3':
            return True
        if 'postgresql' in scheme or 'mysql' in scheme or 'mssql' in scheme:
            return bool(parsed.hostname)
        return False

    @staticmethod
    def get_database_backend(url: str | None = None) -> str:
        """Return the normalized backend label for diagnostics."""
        resolved = (url or Config.get_database_url() or '').strip()
        if not resolved:
            return 'unknown'

        try:
            parsed = urlparse(resolved)
        except Exception:
            return 'unknown'

        scheme = (parsed.scheme or '').lower()
        if scheme in {'sqlite', 'sqlite3'}:
            return 'sqlite'
        if scheme in {'postgresql', 'postgresql+psycopg2', 'postgres'} or scheme.startswith('postgresql'):
            return 'postgresql'
        if scheme.startswith('mysql'):
            return 'mysql'
        if scheme.startswith('mssql'):
            return 'mssql'
        return scheme or 'unknown'

    @staticmethod
    def _oauth_redirect(var_name, local_default):
        """Resolve OAuth redirect URI with production-safe fallback policy."""
        configured = os.getenv(var_name, '').strip()
        if configured:
            return configured
        if os.getenv('ENVIRONMENT', 'development').strip().lower() == 'production':
            return ''
        return local_default

    @staticmethod
    def get_oauth_config():
        """Get OAuth configuration at runtime"""
        return {
            'google': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': Config._oauth_redirect(
                    'GOOGLE_REDIRECT_URI',
                    'http://localhost:9000/api/auth/oauth/google/callback'
                ),
            },
            'facebook': {
                'client_id': os.getenv('FACEBOOK_APP_ID'),
                'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
                'redirect_uri': Config._oauth_redirect(
                    'FACEBOOK_REDIRECT_URI',
                    'http://localhost:9000/api/auth/oauth/facebook/callback'
                ),
            },
            'kakao': {
                'client_id': os.getenv('KAKAO_REST_API_KEY'),
                'client_secret': os.getenv('KAKAO_CLIENT_SECRET'),
                'redirect_uri': Config._oauth_redirect(
                    'KAKAO_REDIRECT_URI',
                    'http://localhost:9000/api/auth/oauth/kakao/callback'
                ),
            },
        }

    @staticmethod
    def get_stripe_config():
        """Get Stripe configuration at runtime"""
        return {
            'secret_key': os.getenv('STRIPE_SECRET_KEY'),
            'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
            'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET'),
        }
