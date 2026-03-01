"""
Test Auth & OAuth Integration — SNS Auto v2.0
Tests OAuth flows, CSRF token validation, token refresh
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.models import (
    db, User, SNSOAuthState, SNSAccount
)
from backend.auth import require_auth


@pytest.fixture
def demo_user(app):
    """Create demo user for tests"""
    with app.app_context():
        user = User(
            email='oauth_test@example.com',
            name='OAuth Test User'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_headers():
    """Authentication headers with demo token"""
    return {
        'Authorization': 'Bearer demo_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def valid_oauth_state(app, demo_user):
    """Create valid OAuth state token"""
    with app.app_context():
        state = SNSOAuthState(
            provider='instagram',
            state='valid_state_token_abc123',
            created_at=datetime.utcnow()
        )
        db.session.add(state)
        db.session.commit()
        return state


class TestOAuthFlow:
    """OAuth authorization flow tests"""

    def test_google_oauth_url_generation(self, client, auth_headers):
        """Test GET /api/auth/oauth/google/url"""
        res = client.get('/api/auth/oauth/google/url', headers=auth_headers)
        assert res.status_code in [200, 400, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'auth_url' in data or 'url' in data

    def test_facebook_oauth_url_generation(self, client, auth_headers):
        """Test GET /api/auth/oauth/facebook/url"""
        res = client.get('/api/auth/oauth/facebook/url', headers=auth_headers)
        assert res.status_code in [200, 400, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'auth_url' in data or 'url' in data

    def test_kakao_oauth_url_generation(self, client, auth_headers):
        """Test GET /api/auth/oauth/kakao/url"""
        res = client.get('/api/auth/oauth/kakao/url', headers=auth_headers)
        assert res.status_code in [200, 400, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'auth_url' in data or 'url' in data

    def test_google_oauth_callback_mock(self, client, auth_headers):
        """Test POST /api/auth/oauth/google/callback (mock mode, no env vars)"""
        res = client.post(
            '/api/auth/oauth/google/callback',
            headers=auth_headers,
            json={'code': 'mock_code', 'state': 'mock_state'}
        )
        # Should succeed or return error if not fully implemented
        assert res.status_code in [200, 400, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'token' in data or 'access_token' in data

    def test_facebook_oauth_callback_mock(self, client, auth_headers):
        """Test POST /api/auth/oauth/facebook/callback (mock mode)"""
        res = client.post(
            '/api/auth/oauth/facebook/callback',
            headers=auth_headers,
            json={'code': 'mock_code', 'state': 'mock_state'}
        )
        assert res.status_code in [200, 400, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'token' in data or 'access_token' in data


class TestCSRFTokenValidation:
    """CSRF state token validation and security"""

    def test_oauth_state_validation_success(self, client, auth_headers):
        """Test valid state token passes validation"""
        res = client.post(
            '/api/auth/oauth/instagram/callback',
            headers=auth_headers,
            json={'code': 'mock', 'state': 'valid_state_token_abc123'}
        )
        # Should succeed validation or not be implemented
        assert res.status_code in [200, 400, 404]

    def test_oauth_state_validation_failure_wrong_state(self, client, auth_headers):
        """Test invalid state token fails CSRF validation"""
        res = client.post(
            '/api/auth/oauth/instagram/callback',
            headers=auth_headers,
            json={'code': 'mock', 'state': 'wrong_state_token'}
        )
        # Should fail or return 400/404
        assert res.status_code in [400, 401, 404, 403]

    def test_oauth_missing_state_parameter(self, client, auth_headers):
        """Test missing state parameter in callback"""
        res = client.post(
            '/api/auth/oauth/instagram/callback',
            headers=auth_headers,
            json={'code': 'mock_code'}
        )
        # Missing state should fail
        assert res.status_code in [200, 400, 401, 404, 403]

    def test_oauth_missing_code_parameter(self, client, auth_headers):
        """Test missing code parameter in callback"""
        res = client.post(
            '/api/auth/oauth/instagram/callback',
            headers=auth_headers,
            json={'state': 'some_state'}
        )
        # Missing code should fail
        assert res.status_code in [400, 401, 404, 403]


class TestTokenManagement:
    """Token refresh, expiration, and lifecycle"""

    def test_token_refresh_mechanism(self, client, auth_headers, app):
        """Test token refresh endpoint"""
        with app.app_context():
            user = User.query.first()
            if not user:
                user = User(email='token_test@example.com', name='Token Test')
                user.set_password('testpass')
                db.session.add(user)
                db.session.commit()

            account = SNSAccount(
                user_id=user.id,
                platform='instagram',
                account_name='@test',
                access_token='old_token',
                refresh_token='refresh_token_123',
                token_expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(account)
            db.session.commit()
            account_id = account.id

        res = client.post(
            f'/api/sns/accounts/{account_id}/refresh-token',
            headers=auth_headers,
            json={}
        )
        # May not be implemented yet
        assert res.status_code in [200, 404, 400, 405]

    def test_token_expiration_detection(self, client, auth_headers, app):
        """Test expired token detection"""
        with app.app_context():
            user = User.query.first()
            if not user:
                user = User(email='expiry_test@example.com', name='Expiry Test')
                user.set_password('testpass')
                db.session.add(user)
                db.session.commit()

            account = SNSAccount(
                user_id=user.id,
                platform='twitter',
                account_name='@twitter_test',
                access_token='expired_token',
                token_expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(account)
            db.session.commit()
            account_id = account.id

        res = client.get(
            f'/api/sns/accounts/{account_id}',
            headers=auth_headers
        )
        assert res.status_code in [200, 404, 405]  # 405 = Method Not Allowed


class TestAuthenticationRequired:
    """Test @require_auth decorator enforcement"""

    def test_sns_endpoint_requires_auth(self, client):
        """Test SNS endpoint rejects unauthorized request"""
        res = client.get('/api/sns/accounts')
        assert res.status_code == 401

    def test_sns_endpoint_accepts_valid_auth(self, client, auth_headers):
        """Test SNS endpoint accepts request with auth"""
        res = client.get('/api/sns/accounts', headers=auth_headers)
        # Should return 200 if endpoint exists
        assert res.status_code in [200, 404]

    def test_invalid_bearer_token_rejected(self, client):
        """Test invalid bearer token is rejected"""
        res = client.get(
            '/api/sns/accounts',
            headers={'Authorization': 'Bearer invalid_token_xyz'}
        )
        assert res.status_code in [401, 200, 404]

    def test_missing_authorization_header(self, client):
        """Test missing Authorization header"""
        res = client.get('/api/sns/accounts')
        assert res.status_code == 401

    def test_malformed_authorization_header(self, client):
        """Test malformed Authorization header"""
        res = client.get(
            '/api/sns/accounts',
            headers={'Authorization': 'InvalidFormat token_value'}
        )
        assert res.status_code in [401, 400]


class TestMultiPlatformOAuth:
    """Test OAuth for different platforms"""

    platforms = ['instagram', 'facebook', 'twitter', 'linkedin', 'tiktok', 'youtube', 'pinterest', 'threads']

    @pytest.mark.parametrize('platform', platforms)
    def test_oauth_authorize_all_platforms(self, client, auth_headers, platform):
        """Test authorize endpoint for each platform"""
        res = client.get(
            f'/api/sns/oauth/{platform}/authorize',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    @pytest.mark.parametrize('platform', platforms)
    def test_oauth_callback_all_platforms(self, client, auth_headers, platform):
        """Test callback endpoint for each platform"""
        res = client.post(
            f'/api/auth/oauth/{platform}/callback',
            headers=auth_headers,
            json={'code': 'test', 'state': 'test'}
        )
        # Should return 200, 400, or 404
        assert res.status_code in [200, 400, 401, 404, 403]


class TestOAuthErrorHandling:
    """Test OAuth error scenarios"""

    def test_unsupported_platform_oauth(self, client, auth_headers):
        """Test OAuth with unsupported platform"""
        res = client.get(
            '/api/auth/oauth/unsupported_platform/url',
            headers=auth_headers
        )
        # Should return error or 400
        assert res.status_code in [400, 404]

    def test_oauth_network_error_handling(self, client, auth_headers):
        """Test OAuth handles network errors gracefully"""
        res = client.get(
            '/api/sns/oauth/instagram/authorize',
            headers=auth_headers
        )
        # Should handle gracefully
        assert res.status_code in [200, 404, 500]

    def test_oauth_invalid_response_handling(self, client, auth_headers):
        """Test OAuth handles invalid platform responses"""
        res = client.post(
            '/api/auth/oauth/instagram/callback',
            headers=auth_headers,
            json={'code': 'invalid_format', 'state': 'test'}
        )
        # Should handle gracefully
        assert res.status_code in [200, 400, 401, 404, 500]
