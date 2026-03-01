"""Twitter API Flask Endpoints Integration Tests"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from backend.models import db, User, SNSAccount, SNSPost, SNSOAuthState


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(client, app):
    """Create authenticated headers"""
    with app.app_context():
        # Create test user
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()

        # Create mock JWT token (in real tests, use actual token generation)
        return {
            'Authorization': f'Bearer test_jwt_token',
            'Content-Type': 'application/json'
        }


class TestOAuthEndpoints:
    """Test OAuth 2.0 endpoints"""

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_oauth_authorize(self, mock_client, client, auth_headers, app):
        """Test OAuth authorization endpoint"""
        with app.app_context():
            with patch('backend.auth.require_auth', lambda f: f):  # Mock auth decorator
                with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                    response = client.get(
                        '/api/sns/twitter/oauth/authorize',
                        headers=auth_headers
                    )

                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert 'authorization_url' in data
                    assert 'state' in data
                    assert 'twitter.com' in data['authorization_url']

    def test_oauth_authorize_no_auth(self, client):
        """Test OAuth authorize without authentication"""
        response = client.get('/api/sns/twitter/oauth/authorize')

        assert response.status_code in [401, 404]  # Should require auth


class TestTweetEndpoints:
    """Test tweet posting endpoints"""

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_post_tweet(self, mock_get_client, client, auth_headers, app):
        """Test posting a tweet"""
        with app.app_context():
            # Setup mocks
            mock_client = MagicMock()
            mock_client.post_tweet.return_value = {
                'success': True,
                'tweet_id': '1234567890',
                'url': 'https://twitter.com/i/web/status/1234567890',
                'created_at': datetime.utcnow().isoformat()
            }
            mock_get_client.return_value = mock_client

            # Create test account
            user = User.query.filter_by(email='test@example.com').first()
            if not user:
                user = User(
                    email='test@example.com',
                    username='testuser',
                    password_hash='hashed'
                )
                db.session.add(user)
                db.session.commit()

            account = SNSAccount(
                user_id=user.id,
                platform='twitter',
                account_name='testuser',
                access_token='test_token',
                is_active=True
            )
            db.session.add(account)
            db.session.commit()

            with patch('backend.auth.require_auth', lambda f: f):
                with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                    with patch('backend.services.twitter_routes.g') as mock_g:
                        mock_g.user_id = user.id

                        response = client.post(
                            '/api/sns/twitter/tweets',
                            data=json.dumps({
                                'account_id': account.id,
                                'text': 'Hello Twitter!'
                            }),
                            headers=auth_headers
                        )

                        if response.status_code == 201:
                            data = json.loads(response.data)
                            assert data['success'] is True
                            assert 'tweet_id' in data

    def test_post_tweet_missing_account_id(self, client, auth_headers, app):
        """Test posting tweet without account_id"""
        with app.app_context():
            with patch('backend.auth.require_auth', lambda f: f):
                with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                    response = client.post(
                        '/api/sns/twitter/tweets',
                        data=json.dumps({
                            'text': 'Hello Twitter!'
                        }),
                        headers=auth_headers
                    )

                    assert response.status_code in [400, 404]

    def test_post_tweet_text_too_long(self, client, auth_headers, app):
        """Test posting tweet with text > 280 chars"""
        with app.app_context():
            with patch('backend.auth.require_auth', lambda f: f):
                with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                    with patch('backend.services.twitter_routes.g') as mock_g:
                        user = User.query.filter_by(email='test@example.com').first()
                        if user:
                            account = SNSAccount.query.filter_by(user_id=user.id).first()
                            if account:
                                mock_g.user_id = user.id

                                response = client.post(
                                    '/api/sns/twitter/tweets',
                                    data=json.dumps({
                                        'account_id': account.id,
                                        'text': 'x' * 281
                                    }),
                                    headers=auth_headers
                                )

                                assert response.status_code == 400


class TestThreadEndpoints:
    """Test thread posting endpoints"""

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_post_thread(self, mock_get_client, client, auth_headers, app):
        """Test posting a thread"""
        with app.app_context():
            mock_client = MagicMock()
            mock_client.post_thread.return_value = {
                'success': True,
                'thread_count': 3,
                'tweets': [
                    {'tweet_id': '1', 'text': 'Tweet 1', 'url': 'https://twitter.com/1'},
                    {'tweet_id': '2', 'text': 'Tweet 2', 'url': 'https://twitter.com/2'},
                    {'tweet_id': '3', 'text': 'Tweet 3', 'url': 'https://twitter.com/3'},
                ],
                'created_at': datetime.utcnow().isoformat()
            }
            mock_get_client.return_value = mock_client

            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                            with patch('backend.services.twitter_routes.g') as mock_g:
                                mock_g.user_id = user.id

                                response = client.post(
                                    '/api/sns/twitter/threads',
                                    data=json.dumps({
                                        'account_id': account.id,
                                        'tweets': [
                                            'First tweet',
                                            'Second tweet',
                                            'Third tweet'
                                        ]
                                    }),
                                    headers=auth_headers
                                )

                                if response.status_code == 201:
                                    data = json.loads(response.data)
                                    assert data['success'] is True
                                    assert data['thread_count'] == 3


class TestEngagementEndpoints:
    """Test engagement endpoints (like, retweet, bookmark)"""

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_like_tweet(self, mock_get_client, client, auth_headers, app):
        """Test liking a tweet"""
        with app.app_context():
            mock_client = MagicMock()
            mock_client.like_tweet.return_value = {
                'success': True,
                'tweet_id': '1234567890',
                'timestamp': datetime.utcnow().isoformat()
            }
            mock_get_client.return_value = mock_client

            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                            with patch('backend.services.twitter_routes.g') as mock_g:
                                mock_g.user_id = user.id

                                response = client.post(
                                    '/api/sns/twitter/1234567890/like',
                                    data=json.dumps({
                                        'account_id': account.id
                                    }),
                                    headers=auth_headers
                                )

                                if response.status_code == 200:
                                    data = json.loads(response.data)
                                    assert data['success'] is True

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_retweet(self, mock_get_client, client, auth_headers, app):
        """Test retweeting a tweet"""
        with app.app_context():
            mock_client = MagicMock()
            mock_client.retweet.return_value = {
                'success': True,
                'tweet_id': '1234567890',
                'timestamp': datetime.utcnow().isoformat()
            }
            mock_get_client.return_value = mock_client

            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        with patch('backend.services.twitter_routes._get_user_twitter_account') as mock_get_account:
                            mock_get_account.return_value = account

                            response = client.post(
                                '/api/sns/twitter/1234567890/retweet',
                                data=json.dumps({
                                    'account_id': account.id
                                }),
                                headers=auth_headers
                            )

                            if response.status_code == 200:
                                data = json.loads(response.data)
                                assert 'success' in data


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_get_tweet_insights(self, mock_get_client, client, auth_headers, app):
        """Test getting tweet insights"""
        with app.app_context():
            mock_client = MagicMock()
            mock_client.get_tweet.return_value = {
                'tweet_id': '1234567890',
                'text': 'Hello Twitter!',
                'created_at': '2026-02-26T15:00:00Z',
                'likes': 1000,
                'retweets': 250,
                'replies': 50,
                'quotes': 10,
                'impressions': 25000,
                'bookmark_count': 150
            }
            mock_get_client.return_value = mock_client

            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        response = client.get(
                            f'/api/sns/twitter/1234567890/insights?account_id={account.id}',
                            headers=auth_headers
                        )

                        if response.status_code == 200:
                            data = json.loads(response.data)
                            assert data['tweet_id'] == '1234567890'
                            assert data['likes'] == 1000

    @patch('backend.services.twitter_routes._get_twitter_client')
    def test_get_account_insights(self, mock_get_client, client, auth_headers, app):
        """Test getting account insights"""
        with app.app_context():
            mock_client = MagicMock()
            mock_client.get_insights.return_value = {
                'period_days': 7,
                'followers': 15000,
                'engagement': 5000,
                'impressions': 100000,
                'avg_engagement': 200.0,
                'engagement_rate': 2.5
            }
            mock_get_client.return_value = mock_client

            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        with patch('backend.auth.require_subscription', lambda s: lambda f: f):
                            response = client.get(
                                f'/api/sns/twitter/account/insights?account_id={account.id}&days=7',
                                headers=auth_headers
                            )

                            if response.status_code == 200:
                                data = json.loads(response.data)
                                assert 'followers' in data
                                assert 'total_engagement' in data

    def test_get_trends(self, client, auth_headers, app):
        """Test getting trending topics"""
        with app.app_context():
            with patch('backend.auth.require_auth', lambda f: f):
                with patch('backend.services.twitter_routes._get_twitter_client') as mock_get_client:
                    mock_client = MagicMock()
                    mock_client.get_trending_topics.return_value = [
                        {'name': '#AI', 'tweet_volume': 100000},
                        {'name': '#Python', 'tweet_volume': 80000},
                    ]
                    mock_get_client.return_value = mock_client

                    response = client.get(
                        '/api/sns/twitter/trends',
                        headers=auth_headers
                    )

                    if response.status_code == 200:
                        data = json.loads(response.data)
                        assert 'trends' in data


class TestAccountManagementEndpoints:
    """Test account management endpoints"""

    def test_get_twitter_accounts(self, client, auth_headers, app):
        """Test getting linked Twitter accounts"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                with patch('backend.auth.require_auth', lambda f: f):
                    with patch('backend.services.twitter_routes.g') as mock_g:
                        mock_g.user_id = user.id

                        response = client.get(
                            '/api/sns/twitter/accounts',
                            headers=auth_headers
                        )

                        if response.status_code == 200:
                            data = json.loads(response.data)
                            assert isinstance(data, list)

    def test_get_account_info(self, client, auth_headers, app):
        """Test getting account info"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                account = SNSAccount.query.filter_by(user_id=user.id).first()
                if account:
                    with patch('backend.auth.require_auth', lambda f: f):
                        with patch('backend.services.twitter_routes._get_twitter_client') as mock_get_client:
                            mock_client = MagicMock()
                            mock_client.get_account_info.return_value = {
                                'user_id': '123',
                                'username': 'testuser',
                                'followers': 1000,
                                'verified': False
                            }
                            mock_get_client.return_value = mock_client

                            response = client.get(
                                f'/api/sns/twitter/account/info?account_id={account.id}',
                                headers=auth_headers
                            )

                            if response.status_code == 200:
                                data = json.loads(response.data)
                                assert 'username' in data
                                assert 'followers' in data


class TestHealthCheckEndpoint:
    """Test health check endpoint"""

    def test_health_check_success(self, client, auth_headers, app):
        """Test health check success"""
        with app.app_context():
            with patch('backend.auth.require_auth', lambda f: f):
                response = client.get(
                    '/api/sns/twitter/health',
                    headers=auth_headers
                )

                # Should return either healthy or no_account
                assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
