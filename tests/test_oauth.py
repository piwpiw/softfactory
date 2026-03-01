"""OAuth Social Login Tests"""
import pytest
import os
from datetime import datetime
from backend.app import create_app
from backend.models import db, User
from backend.oauth import OAuthProvider


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestOAuthProvider:
    """Test OAuth provider utilities"""

    def test_generate_state_token(self):
        """Test state token generation"""
        state1 = OAuthProvider.generate_state_token()
        state2 = OAuthProvider.generate_state_token()

        assert len(state1) > 20
        assert len(state2) > 20
        assert state1 != state2

    def test_get_auth_url_mock_mode(self):
        """Test getting auth URL in mock mode (no credentials)"""
        state = OAuthProvider.generate_state_token()
        result = OAuthProvider.get_auth_url('google', state, 'http://localhost:8000/callback')

        assert 'auth_url' in result
        assert 'state' in result
        assert result['state'] == state
        assert result.get('mock_mode') == True

    def test_get_auth_url_invalid_provider(self):
        """Test with invalid provider"""
        state = OAuthProvider.generate_state_token()
        result = OAuthProvider.get_auth_url('invalid', state, 'http://localhost:8000/callback')

        assert 'error' in result

    def test_exchange_code_mock_mode(self):
        """Test code exchange in mock mode"""
        result = OAuthProvider.exchange_code_for_token('google', 'mock_code', 'http://localhost:8000/callback')

        assert 'access_token' in result
        assert result['token_type'] == 'Bearer'
        assert result.get('mock_mode') == True

    def test_get_user_info_mock_token(self):
        """Test getting user info with mock token"""
        result = OAuthProvider.get_user_info('google', 'mock_google_token_abc')

        assert 'id' in result
        assert 'email' in result
        assert 'name' in result
        assert result.get('mock_mode') == True
        assert result['provider'] == 'google'

    def test_normalize_user_info_google(self):
        """Test Google user info normalization"""
        data = {
            'id': '123456',
            'email': 'user@gmail.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg'
        }
        result = OAuthProvider._normalize_user_info('google', data)

        assert result['id'] == '123456'
        assert result['email'] == 'user@gmail.com'
        assert result['name'] == 'Test User'
        assert result['picture'] == 'https://example.com/picture.jpg'
        assert result['provider'] == 'google'

    def test_mock_oauth_user(self):
        """Test mock user generation"""
        for provider in ['google', 'facebook', 'kakao']:
            user = OAuthProvider.mock_oauth_user(provider)

            assert 'id' in user
            assert 'email' in user
            assert 'name' in user
            assert user['provider'] == provider
            assert user['mock_mode'] == True


class TestOAuthEndpoints:
    """Test OAuth endpoints"""

    def test_get_oauth_url_endpoint(self, client):
        """Test GET /api/auth/oauth/<provider>/url"""
        response = client.get('/api/auth/oauth/google/url')

        assert response.status_code == 200
        data = response.get_json()
        assert 'auth_url' in data
        assert 'state' in data

    def test_get_oauth_url_all_providers(self, client):
        """Test OAuth URL endpoint for all providers"""
        for provider in ['google', 'facebook', 'kakao']:
            response = client.get(f'/api/auth/oauth/{provider}/url')
            assert response.status_code == 200
            data = response.get_json()
            assert 'auth_url' in data
            assert 'state' in data

    def test_get_oauth_url_invalid_provider(self, client):
        """Test with invalid provider"""
        response = client.get('/api/auth/oauth/invalid/url')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_oauth_callback_missing_code(self, client):
        """Test callback without code parameter"""
        response = client.get('/api/auth/oauth/google/callback?state=test')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_oauth_callback_with_provider_error(self, client):
        """Test callback with provider error"""
        response = client.get('/api/auth/oauth/google/callback?error=access_denied')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_oauth_callback_mock_flow(self, client, app):
        """Test OAuth callback with mock mode"""
        with app.app_context():
            # Get auth URL first to get state
            response = client.get('/api/auth/oauth/google/url')
            data = response.get_json()
            state = data['state']

            # Call callback with mock parameters
            response = client.get(f'/api/auth/oauth/google/callback?code=mock_code&state={state}')

            # Should create new user
            assert response.status_code == 200
            data = response.get_json()
            assert 'access_token' in data
            assert 'user' in data
            assert data['oauth_provider'] == 'google'

            # Verify user was created
            user = User.query.filter_by(oauth_provider='google').first()
            assert user is not None
            assert user.oauth_id is not None

    def test_oauth_user_creation_and_linking(self, client, app):
        """Test OAuth user creation and account linking"""
        with app.app_context():
            # Create user via OAuth
            response = client.get('/api/auth/oauth/google/url')
            data = response.get_json()
            state = data['state']

            response = client.get(f'/api/auth/oauth/google/callback?code=mock_code&state={state}')
            assert response.status_code == 200
            data = response.get_json()

            # Verify user exists
            user = User.query.filter_by(oauth_provider='google').first()
            assert user is not None
            assert user.oauth_id is not None
            assert 'avatar_url' in user.to_dict()

    def test_user_model_oauth_fields(self, app):
        """Test User model has OAuth fields"""
        with app.app_context():
            # Create test user
            user = User(
                email='oauth@test.com',
                name='OAuth User',
                oauth_provider='google',
                oauth_id='google_123',
                avatar_url='https://example.com/avatar.jpg'
            )
            user.set_password('test123')

            db.session.add(user)
            db.session.commit()

            # Verify fields
            retrieved = User.query.filter_by(email='oauth@test.com').first()
            assert retrieved.oauth_provider == 'google'
            assert retrieved.oauth_id == 'google_123'
            assert retrieved.avatar_url == 'https://example.com/avatar.jpg'

            # Verify to_dict includes avatar_url
            user_dict = retrieved.to_dict()
            assert 'avatar_url' in user_dict
            assert user_dict['avatar_url'] == 'https://example.com/avatar.jpg'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
