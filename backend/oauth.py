"""OAuth 2.0 Social Login Integration"""
import os
import secrets
import requests
import json
import random
from datetime import datetime, timedelta
from urllib.parse import urlencode

# OAuth Provider Configuration
OAUTH_PROVIDERS = {
    'google': {
        'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'client_id_env': 'GOOGLE_CLIENT_ID',
        'client_secret_env': 'GOOGLE_CLIENT_SECRET',
        'scope': 'openid profile email',
    },
    'facebook': {
        'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'userinfo_url': 'https://graph.facebook.com/me?fields=id,name,email,picture',
        'client_id_env': 'FACEBOOK_APP_ID',
        'client_secret_env': 'FACEBOOK_APP_SECRET',
        'scope': 'public_profile email',
    },
    'kakao': {
        'auth_url': 'https://kauth.kakao.com/oauth/authorize',
        'token_url': 'https://kauth.kakao.com/oauth/token',
        'userinfo_url': 'https://kapi.kakao.com/v2/user/me',
        'client_id_env': 'KAKAO_REST_API_KEY',
        'client_secret_env': 'KAKAO_CLIENT_SECRET',
        'scope': 'openid profile account_email',
    }
}


class OAuthProvider:
    """Handles OAuth 2.0 flow for social login"""

    @staticmethod
    def generate_state_token() -> str:
        """Generate CSRF protection state token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_auth_url(provider: str, state: str, redirect_uri: str) -> dict:
        """Get OAuth provider's authorization URL"""
        if provider not in OAUTH_PROVIDERS:
            return {'error': f'Unknown provider: {provider}'}

        config = OAUTH_PROVIDERS[provider]
        client_id = os.getenv(config['client_id_env'])

        # Mock mode: return dummy URL if credentials not configured
        if not client_id:
            return {
                'auth_url': f'mock://{provider}/auth?state={state}',
                'state': state,
                'mock_mode': True
            }

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': config['scope'],
            'state': state,
        }

        # Provider-specific params
        if provider == 'google':
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'
        elif provider == 'facebook':
            params['display'] = 'popup'
        elif provider == 'kakao':
            params['nonce'] = secrets.token_urlsafe(16)

        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        return {'auth_url': auth_url, 'state': state}

    @staticmethod
    def exchange_code_for_token(provider: str, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token"""
        if provider not in OAUTH_PROVIDERS:
            return {'error': f'Unknown provider: {provider}'}

        config = OAUTH_PROVIDERS[provider]
        client_id = os.getenv(config['client_id_env'])
        client_secret = os.getenv(config['client_secret_env'])

        # Mock mode
        if not client_id or not client_secret:
            return {
                'access_token': f'mock_{provider}_token_{secrets.token_urlsafe(16)}',
                'token_type': 'Bearer',
                'mock_mode': True
            }

        try:
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }

            response = requests.post(config['token_url'], data=payload, timeout=10)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_user_info(provider: str, access_token: str) -> dict:
        """Fetch user info from OAuth provider"""
        if provider not in OAUTH_PROVIDERS:
            return {'error': f'Unknown provider: {provider}'}

        config = OAUTH_PROVIDERS[provider]

        # Mock mode
        if access_token.startswith('mock_'):
            mock_data = {
                'id': f'mock_{provider}_user_{random.randint(1000, 9999)}',
                'email': f'user+{secrets.token_hex(4)}@{provider}.local',
                'name': f'Test User ({provider.capitalize()})',
                'picture': None,
            }
            # Normalize and add mock flag
            result = OAuthProvider._normalize_user_info(provider, mock_data)
            result['mock_mode'] = True
            return result

        try:
            headers = {'Authorization': f'Bearer {access_token}'}

            # Kakao uses different header format
            if provider == 'kakao':
                headers = {'Authorization': f'Bearer {access_token}'}

            response = requests.get(config['userinfo_url'], headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Normalize response format across providers
            return OAuthProvider._normalize_user_info(provider, data)
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _normalize_user_info(provider: str, data: dict) -> dict:
        """Normalize user info across different OAuth providers"""
        if provider == 'google':
            return {
                'id': data.get('id'),
                'email': data.get('email'),
                'name': data.get('name'),
                'picture': data.get('picture'),
                'provider': 'google'
            }
        elif provider == 'facebook':
            picture_url = None
            picture = data.get('picture', {})
            if picture and isinstance(picture, dict):
                picture_url = picture.get('data', {}).get('url')

            return {
                'id': data.get('id'),
                'email': data.get('email'),
                'name': data.get('name'),
                'picture': picture_url,
                'provider': 'facebook'
            }
        elif provider == 'kakao':
            kakao_account = data.get('kakao_account', {})
            profile = kakao_account.get('profile', {})

            return {
                'id': str(data.get('id')),
                'email': kakao_account.get('email'),
                'name': profile.get('nickname'),
                'picture': profile.get('profile_image_url'),
                'provider': 'kakao'
            }
        else:
            return data

    @staticmethod
    def mock_oauth_user(provider: str) -> dict:
        """Generate mock OAuth user data for testing without credentials"""
        names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']
        import random
        name = random.choice(names)

        return {
            'id': f'mock_{provider}_{secrets.token_hex(8)}',
            'email': f'{name.lower()}@{provider}.local',
            'name': f'{name} ({provider.capitalize()})',
            'picture': None,
            'provider': provider,
            'mock_mode': True
        }
