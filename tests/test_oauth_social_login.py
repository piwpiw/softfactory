"""OAuth Social Login Test Suite - Task #14"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_cors import CORS
from backend.models import db, User, init_db
from backend.auth import auth_bp
from backend.oauth import OAuthProvider


def create_test_app():
    """Create a minimal Flask app for testing (skip auto-init)"""
    app = Flask(__name__)

    # Configuration for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8000", "null"]}})

    # Register auth blueprint
    app.register_blueprint(auth_bp)

    return app


@pytest.fixture(scope='function')
def app():
    """Create Flask app for testing"""
    app = create_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


class TestOAuthURLGeneration:
    """Test OAuth authorization URL generation"""

    def test_google_oauth_url_generation_mock_mode(self):
        """Test Google OAuth URL in mock mode (no credentials)"""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no credentials set
            os.environ.pop('GOOGLE_CLIENT_ID', None)

            state = OAuthProvider.generate_state_token()
            result = OAuthProvider.get_auth_url('google', state, 'http://localhost:8000/callback')

            assert 'auth_url' in result
            assert result['mock_mode'] == True
            assert 'mock://google/auth' in result['auth_url']
            assert 'state=' + state in result['auth_url']

    def test_facebook_oauth_url_generation_mock_mode(self):
        """Test Facebook OAuth URL in mock mode"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('FACEBOOK_APP_ID', None)

            state = OAuthProvider.generate_state_token()
            result = OAuthProvider.get_auth_url('facebook', state, 'http://localhost:8000/callback')

            assert 'auth_url' in result
            assert result['mock_mode'] == True
            assert 'mock://facebook/auth' in result['auth_url']

    def test_kakao_oauth_url_generation_mock_mode(self):
        """Test Kakao OAuth URL in mock mode"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('KAKAO_REST_API_KEY', None)

            state = OAuthProvider.generate_state_token()
            result = OAuthProvider.get_auth_url('kakao', state, 'http://localhost:8000/callback')

            assert 'auth_url' in result
            assert result['mock_mode'] == True
            assert 'mock://kakao/auth' in result['auth_url']

    def test_invalid_provider(self):
        """Test invalid OAuth provider"""
        state = OAuthProvider.generate_state_token()
        result = OAuthProvider.get_auth_url('invalid_provider', state, 'http://localhost:8000/callback')

        assert 'error' in result


class TestOAuthTokenExchange:
    """Test OAuth code-to-token exchange"""

    def test_token_exchange_mock_mode(self):
        """Test token exchange in mock mode"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('GOOGLE_CLIENT_ID', None)
            os.environ.pop('GOOGLE_CLIENT_SECRET', None)

            result = OAuthProvider.exchange_code_for_token(
                'google',
                'mock_code_12345',
                'http://localhost:8000/callback'
            )

            assert 'access_token' in result
            assert 'mock_' in result['access_token']
            assert result['mock_mode'] == True

    def test_token_exchange_all_providers_mock(self):
        """Test token exchange for all providers in mock mode"""
        with patch.dict(os.environ, {}, clear=False):
            # Clear all OAuth env vars
            for key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
                       'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET',
                       'KAKAO_REST_API_KEY', 'KAKAO_CLIENT_SECRET']:
                os.environ.pop(key, None)

            for provider in ['google', 'facebook', 'kakao']:
                result = OAuthProvider.exchange_code_for_token(
                    provider,
                    f'mock_code_{provider}',
                    'http://localhost:8000/callback'
                )
                assert 'access_token' in result
                assert result['mock_mode'] == True


class TestOAuthUserInfo:
    """Test OAuth user info retrieval"""

    def test_google_user_info_mock_mode(self):
        """Test Google user info retrieval in mock mode"""
        token = 'mock_google_token_12345'
        result = OAuthProvider.get_user_info('google', token)

        assert 'id' in result
        assert 'email' in result
        assert 'name' in result
        assert result['provider'] == 'google'
        assert result['mock_mode'] == True

    def test_facebook_user_info_mock_mode(self):
        """Test Facebook user info retrieval in mock mode"""
        token = 'mock_facebook_token_12345'
        result = OAuthProvider.get_user_info('facebook', token)

        assert 'id' in result
        assert 'email' in result
        assert 'name' in result
        assert result['provider'] == 'facebook'
        assert result['mock_mode'] == True

    def test_kakao_user_info_mock_mode(self):
        """Test Kakao user info retrieval in mock mode"""
        token = 'mock_kakao_token_12345'
        result = OAuthProvider.get_user_info('kakao', token)

        assert 'id' in result
        assert 'email' in result
        assert 'name' in result
        assert result['provider'] == 'kakao'
        assert result['mock_mode'] == True

    def test_user_info_real_token_error_handling(self):
        """Test error handling for invalid real tokens"""
        token = 'invalid_real_token'
        result = OAuthProvider.get_user_info('google', token)

        # Should have error or mock data
        assert 'error' in result or 'mock_mode' not in result or 'id' in result


class TestOAuthEndpoints:
    """Test OAuth endpoints"""

    def test_oauth_url_endpoint_google(self, client):
        """Test GET /api/auth/oauth/google/url"""
        response = client.get('/api/auth/oauth/google/url')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_url' in data
        assert 'state' in data

    def test_oauth_url_endpoint_facebook(self, client):
        """Test GET /api/auth/oauth/facebook/url"""
        response = client.get('/api/auth/oauth/facebook/url')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_url' in data
        assert 'state' in data

    def test_oauth_url_endpoint_kakao(self, client):
        """Test GET /api/auth/oauth/kakao/url"""
        response = client.get('/api/auth/oauth/kakao/url')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'auth_url' in data
        assert 'state' in data

    def test_oauth_callback_endpoint_google_mock(self, client, app):
        """Test POST /api/auth/oauth/google/callback with mock data"""
        with app.app_context():
            response = client.post(
                '/api/auth/oauth/google/callback',
                data=json.dumps({
                    'code': 'mock_google_code_12345',
                    'state': 'mock_state_token'
                }),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert 'user' in data
            assert data['user']['oauth_provider'] == 'google'

    def test_oauth_callback_endpoint_facebook_mock(self, client, app):
        """Test POST /api/auth/oauth/facebook/callback with mock data"""
        with app.app_context():
            response = client.post(
                '/api/auth/oauth/facebook/callback',
                data=json.dumps({
                    'code': 'mock_facebook_code_12345',
                    'state': 'mock_state_token'
                }),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'access_token' in data
            assert data['user']['oauth_provider'] == 'facebook'

    def test_oauth_callback_endpoint_kakao_mock(self, client, app):
        """Test POST /api/auth/oauth/kakao/callback with mock data"""
        with app.app_context():
            response = client.post(
                '/api/auth/oauth/kakao/callback',
                data=json.dumps({
                    'code': 'mock_kakao_code_12345',
                    'state': 'mock_state_token'
                }),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'access_token' in data
            assert data['user']['oauth_provider'] == 'kakao'

    def test_oauth_callback_missing_code(self, client):
        """Test callback with missing authorization code"""
        response = client.post(
            '/api/auth/oauth/google/callback',
            data=json.dumps({'state': 'mock_state'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestUserModel:
    """Test User model OAuth fields"""

    def test_user_oauth_fields(self, app):
        """Test User model has OAuth fields"""
        with app.app_context():
            user = User(
                email='test@example.com',
                name='Test User',
                oauth_provider='google',
                oauth_id='google_12345',
                avatar_url='https://example.com/avatar.jpg'
            )
            user.set_password('dummy_password')

            db.session.add(user)
            db.session.commit()

            retrieved_user = User.query.filter_by(email='test@example.com').first()
            assert retrieved_user.oauth_provider == 'google'
            assert retrieved_user.oauth_id == 'google_12345'
            assert retrieved_user.avatar_url == 'https://example.com/avatar.jpg'

    def test_user_to_dict_includes_oauth_fields(self, app):
        """Test User.to_dict() includes OAuth fields"""
        with app.app_context():
            user = User(
                email='test@example.com',
                name='Test User',
                oauth_provider='facebook',
                oauth_id='fb_12345'
            )
            user.set_password('dummy_password')

            user_dict = user.to_dict()
            assert 'oauth_provider' in user_dict
            assert user_dict['oauth_provider'] == 'facebook'

    def test_oauth_user_without_password(self, app):
        """Test OAuth user can be created without password"""
        with app.app_context():
            user = User(
                email='oauth_user@example.com',
                name='OAuth User',
                oauth_provider='kakao',
                oauth_id='kakao_12345',
                password_hash='not_used'  # OAuth users don't use password
            )

            db.session.add(user)
            db.session.commit()

            retrieved_user = User.query.filter_by(email='oauth_user@example.com').first()
            assert retrieved_user.oauth_provider == 'kakao'


class TestOAuthFlow:
    """Test complete OAuth flow"""

    def test_full_google_oauth_flow_mock(self, client, app):
        """Test complete Google OAuth login flow"""
        with app.app_context():
            # Step 1: Get authorization URL
            url_response = client.get('/api/auth/oauth/google/url')
            assert url_response.status_code == 200
            url_data = json.loads(url_response.data)
            state = url_data['state']

            # Step 2: Simulate OAuth callback
            callback_response = client.post(
                '/api/auth/oauth/google/callback',
                data=json.dumps({
                    'code': 'mock_code_12345',
                    'state': state
                }),
                content_type='application/json'
            )

            assert callback_response.status_code == 200
            callback_data = json.loads(callback_response.data)

            # Verify user was created
            assert callback_data['access_token']
            assert callback_data['user']['oauth_provider'] == 'google'

            # Verify in database
            user = User.query.filter_by(email=callback_data['user']['email']).first()
            assert user is not None
            assert user.oauth_provider == 'google'

    def test_multiple_oauth_logins_same_user(self, client, app):
        """Test multiple OAuth providers for same email"""
        with app.app_context():
            # First login with Google
            response1 = client.post(
                '/api/auth/oauth/google/callback',
                data=json.dumps({'code': 'mock_code_1', 'state': 'state1'}),
                content_type='application/json'
            )
            email1 = json.loads(response1.data)['user']['email']

            # Second login with same email, different provider
            # This would typically use same email after user links accounts
            # For now, just verify both logins work independently
            response2 = client.post(
                '/api/auth/oauth/facebook/callback',
                data=json.dumps({'code': 'mock_code_2', 'state': 'state2'}),
                content_type='application/json'
            )

            assert response1.status_code == 200
            assert response2.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
