"""Application Configuration - Lazy Loading"""
import os
from pathlib import Path

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
