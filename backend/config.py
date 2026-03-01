"""Application Configuration - Lazy Loading"""
import os
from pathlib import Path

class Config:
    """Configuration with runtime environment variable resolution"""

    # Fallback demo credentials
    DEMO_GOOGLE_CLIENT_ID = '847528942891-5h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x.apps.googleusercontent.com'
    DEMO_GOOGLE_CLIENT_SECRET = 'GOCSPX-8h6v0j8t2k9n4m1p3q6r9s2t5u'
    DEMO_FACEBOOK_APP_ID = '1234567890123456'
    DEMO_FACEBOOK_APP_SECRET = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
    DEMO_KAKAO_REST_API_KEY = '1234567890abcdefghijklmnopqrstuv'
    DEMO_KAKAO_CLIENT_SECRET = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'

    # Convenience attributes used by create_app() — resolve env vars with demo fallback
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') or DEMO_GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET') or DEMO_GOOGLE_CLIENT_SECRET
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID') or DEMO_FACEBOOK_APP_ID
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET') or DEMO_FACEBOOK_APP_SECRET
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY') or DEMO_KAKAO_REST_API_KEY
    KAKAO_CLIENT_SECRET = os.getenv('KAKAO_CLIENT_SECRET') or DEMO_KAKAO_CLIENT_SECRET

    @staticmethod
    def get(key, default=''):
        """Runtime environment variable getter"""
        return os.getenv(key, default)

    @staticmethod
    def get_oauth_config():
        """Get OAuth configuration at runtime"""
        return {
            'google': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID') or Config.DEMO_GOOGLE_CLIENT_ID,
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET') or Config.DEMO_GOOGLE_CLIENT_SECRET,
                'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:9000/api/auth/oauth/google/callback'),
            },
            'facebook': {
                'client_id': os.getenv('FACEBOOK_APP_ID') or Config.DEMO_FACEBOOK_APP_ID,
                'client_secret': os.getenv('FACEBOOK_APP_SECRET') or Config.DEMO_FACEBOOK_APP_SECRET,
                'redirect_uri': os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:9000/api/auth/oauth/facebook/callback'),
            },
            'kakao': {
                'client_id': os.getenv('KAKAO_REST_API_KEY') or Config.DEMO_KAKAO_REST_API_KEY,
                'client_secret': os.getenv('KAKAO_CLIENT_SECRET') or Config.DEMO_KAKAO_CLIENT_SECRET,
                'redirect_uri': os.getenv('KAKAO_REDIRECT_URI', 'http://localhost:9000/api/auth/oauth/kakao/callback'),
            },
        }

    @staticmethod
    def get_stripe_config():
        """Get Stripe configuration at runtime"""
        return {
            'secret_key': os.getenv('STRIPE_SECRET_KEY') or 'sk_test_51NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i',
            'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY') or 'pk_test_51NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i',
            'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET') or 'whsec_1NxYzKL8h6v0j8t2k9n4m1p3q6r9s2t5u8v1w4x9y2z3a4b5c6d7e8f9g0h1i',
        }
