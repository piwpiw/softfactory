"""Twitter API v2 Integration Tests"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from backend.services.twitter_api import (
    TwitterAPI, TwitterAPIException, RateLimitException, RateLimiter, TwitterOAuth2
)


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under limit are allowed"""
        limiter = RateLimiter(max_requests=5, window_minutes=1)

        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked"""
        limiter = RateLimiter(max_requests=3, window_minutes=1)

        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is False
        assert limiter.is_allowed('endpoint1') is False

    def test_rate_limiter_separate_endpoints(self):
        """Test that endpoints have separate rate limits"""
        limiter = RateLimiter(max_requests=2, window_minutes=1)

        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint1') is True
        assert limiter.is_allowed('endpoint2') is True
        assert limiter.is_allowed('endpoint2') is True

        assert limiter.is_allowed('endpoint1') is False
        assert limiter.is_allowed('endpoint2') is False

    def test_get_remaining_count(self):
        """Test getting remaining request count"""
        limiter = RateLimiter(max_requests=5, window_minutes=1)

        limiter.is_allowed('endpoint1')
        remaining, reset_ts = limiter.get_remaining('endpoint1')
        assert remaining == 4
        assert isinstance(reset_ts, int)


class TestTwitterOAuth2:
    """Test OAuth 2.0 functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.oauth = TwitterOAuth2(
            client_id='test_client_id',
            client_secret='test_client_secret',
            redirect_uri='http://localhost/callback'
        )

    def test_generate_pkce_pair(self):
        """Test PKCE code pair generation"""
        code_verifier, code_challenge = self.oauth.generate_pkce_pair()

        assert len(code_verifier) > 0
        assert len(code_challenge) > 0
        assert isinstance(code_verifier, str)
        assert isinstance(code_challenge, str)

    def test_get_authorization_url(self):
        """Test authorization URL generation"""
        url, code_verifier = self.oauth.get_authorization_url('test_state')

        assert 'twitter.com/i/oauth2/authorize' in url
        assert 'client_id=test_client_id' in url
        assert 'state=test_state' in url
        assert 'code_challenge=' in url
        assert 'code_challenge_method=S256' in url
        assert len(code_verifier) > 0

    @patch('requests.post')
    def test_exchange_code_for_tokens(self, mock_post):
        """Test token exchange"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 7200,
            'token_type': 'Bearer',
            'scope': 'tweet.read tweet.write'
        }
        mock_post.return_value = mock_response

        result = self.oauth.exchange_code_for_tokens('test_code', 'test_verifier')

        assert result['access_token'] == 'test_access_token'
        assert result['refresh_token'] == 'test_refresh_token'
        assert result['expires_in'] == 7200
        assert 'expires_at' in result

    @patch('requests.post')
    def test_refresh_access_token(self, mock_post):
        """Test token refresh"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 7200
        }
        mock_post.return_value = mock_response

        result = self.oauth.refresh_access_token('old_refresh_token')

        assert result['access_token'] == 'new_access_token'
        assert 'expires_at' in result

    @patch('requests.post')
    def test_revoke_token(self, mock_post):
        """Test token revocation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.oauth.revoke_token('test_token')

        assert result is True


class TestTwitterAPI:
    """Test TwitterAPI client"""

    def setup_method(self):
        """Setup test fixtures"""
        self.client = TwitterAPI(
            access_token='test_token',
            client_id='test_client_id',
            client_secret='test_client_secret',
            redirect_uri='http://localhost/callback'
        )

    def test_initialization(self):
        """Test client initialization"""
        assert self.client.access_token == 'test_token'
        assert self.client.rate_limiter is not None
        assert self.client.oauth2 is not None

    def test_get_headers(self):
        """Test header generation"""
        headers = self.client._get_headers()

        assert headers['Authorization'] == 'Bearer test_token'
        assert headers['Content-Type'] == 'application/json'
        assert 'User-Agent' in headers

    @patch('requests.post')
    def test_post_tweet(self, mock_post):
        """Test posting a tweet"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response

        result = self.client.post_tweet('Hello Twitter!')

        assert result['success'] is True
        assert result['tweet_id'] == '1234567890'
        assert 'url' in result
        assert 'created_at' in result

    @patch('requests.post')
    def test_post_tweet_validates_length(self, mock_post):
        """Test tweet length validation"""
        with pytest.raises(ValueError):
            self.client.post_tweet('x' * 281)

    @patch('requests.post')
    def test_post_thread(self, mock_post):
        """Test posting a thread"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {'id': str(i)}
        }
        mock_post.return_value = mock_response

        tweets = ['Tweet 1', 'Tweet 2', 'Tweet 3']
        result = self.client.post_thread(tweets)

        assert result['success'] is True
        assert result['thread_count'] == 3
        assert len(result['tweets']) == 3

    @patch('requests.post')
    def test_post_thread_validates_count(self, mock_post):
        """Test thread count validation"""
        tweets = ['Tweet ' + str(i) for i in range(101)]

        with pytest.raises(ValueError):
            self.client.post_thread(tweets)

    @patch('requests.delete')
    def test_delete_tweet(self, mock_delete):
        """Test deleting a tweet"""
        mock_response = MagicMock()
        mock_delete.return_value = mock_response

        result = self.client.delete_tweet('1234567890')

        assert result is True

    @patch('requests.get')
    def test_get_tweet(self, mock_get):
        """Test getting tweet details"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'id': '1234567890',
                'text': 'Hello Twitter!',
                'created_at': '2026-02-26T15:00:00Z',
                'public_metrics': {
                    'like_count': 100,
                    'retweet_count': 50,
                    'reply_count': 20,
                    'quote_count': 10,
                    'impression_count': 5000,
                    'bookmark_count': 75
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_tweet('1234567890')

        assert result['tweet_id'] == '1234567890'
        assert result['likes'] == 100
        assert result['impressions'] == 5000

    @patch('requests.post')
    @patch('requests.get')
    def test_like_tweet(self, mock_get, mock_post):
        """Test liking a tweet"""
        # Mock get_account_info
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            'data': {
                'id': '123456',
                'username': 'testuser',
                'name': 'Test User'
            }
        }
        mock_get.return_value = mock_get_response

        # Mock post response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'data': {'liked': True}
        }
        mock_post.return_value = mock_post_response

        result = self.client.like_tweet('1234567890')

        assert result['success'] is True
        assert result['tweet_id'] == '1234567890'

    @patch('requests.get')
    def test_get_account_info(self, mock_get):
        """Test getting account info"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'id': '123456',
                'username': 'testuser',
                'name': 'Test User',
                'description': 'A test user',
                'location': 'San Francisco',
                'verified': True,
                'created_at': '2015-01-01T00:00:00Z',
                'public_metrics': {
                    'followers_count': 10000,
                    'following_count': 500,
                    'tweet_count': 5000
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_account_info(use_cache=False)

        assert result['user_id'] == '123456'
        assert result['username'] == 'testuser'
        assert result['followers'] == 10000
        assert result['verified'] is True

    @patch('requests.get')
    def test_get_account_info_caching(self, mock_get):
        """Test account info caching"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'id': '123456',
                'username': 'testuser',
                'name': 'Test User',
                'public_metrics': {
                    'followers_count': 10000,
                    'following_count': 500,
                    'tweet_count': 5000
                }
            }
        }
        mock_get.return_value = mock_response

        # First call - should hit API
        result1 = self.client.get_account_info(use_cache=True)
        call_count_1 = mock_get.call_count

        # Second call - should use cache
        result2 = self.client.get_account_info(use_cache=True)
        call_count_2 = mock_get.call_count

        assert result1 == result2
        assert call_count_2 == call_count_1  # No additional API call

    @patch('requests.get')
    def test_search_tweets(self, mock_get):
        """Test searching tweets"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '1',
                    'text': 'Tweet 1',
                    'created_at': '2026-02-26T15:00:00Z',
                    'public_metrics': {
                        'like_count': 10,
                        'retweet_count': 5,
                        'reply_count': 2
                    }
                },
                {
                    'id': '2',
                    'text': 'Tweet 2',
                    'created_at': '2026-02-26T14:00:00Z',
                    'public_metrics': {
                        'like_count': 20,
                        'retweet_count': 8,
                        'reply_count': 3
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_tweets('twitter api', max_results=10)

        assert len(result) == 2
        assert result[0]['tweet_id'] == '1'
        assert result[0]['likes'] == 10

    def test_rate_limit_status(self):
        """Test rate limit status"""
        status = self.client.get_rate_limit_status()

        assert 'remaining_requests' in status
        assert 'max_requests' in status
        assert 'window_minutes' in status
        assert 'reset_at' in status

    @patch('requests.get')
    def test_health_check_success(self, mock_get):
        """Test health check success"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'id': '123456',
                'username': 'testuser',
                'name': 'Test User',
                'public_metrics': {
                    'followers_count': 10000,
                    'following_count': 500,
                    'tweet_count': 5000
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.health_check()

        assert result is True

    @patch('requests.get')
    def test_health_check_failure(self, mock_get):
        """Test health check failure"""
        mock_get.side_effect = Exception('Connection error')

        result = self.client.health_check()

        assert result is False

    def test_rate_limit_exception_on_exceeded(self):
        """Test that rate limit exception is raised when limit exceeded"""
        limiter = RateLimiter(max_requests=1, window_minutes=1)
        self.client.rate_limiter = limiter

        # First request should succeed
        limiter.is_allowed('test')

        # Second request should raise exception
        with pytest.raises(RateLimitException):
            self.client._check_rate_limit('test')


class TestTwitterAPIErrors:
    """Test error handling"""

    def setup_method(self):
        """Setup test fixtures"""
        self.client = TwitterAPI(access_token='test_token')

    @patch('requests.post')
    def test_http_error_handling(self, mock_post):
        """Test HTTP error handling"""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'errors': [{'message': 'Unauthorized'}]
        }
        mock_response.text = 'Unauthorized'
        mock_response.raise_for_status.side_effect = HTTPError('401 Unauthorized')

        mock_post.return_value = mock_response

        with pytest.raises(TwitterAPIException):
            self.client._request('POST', '/tweets', data={'text': 'test'})

    @patch('requests.get')
    def test_timeout_handling(self, mock_get):
        """Test timeout handling"""
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout('Request timeout')

        with pytest.raises(TwitterAPIException):
            self.client._request('GET', '/users/me')

    @patch('requests.post')
    def test_json_parsing_error(self, mock_post):
        """Test JSON parsing error handling"""
        import json

        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        mock_post.return_value = mock_response

        with pytest.raises(TwitterAPIException):
            self.client._request('POST', '/tweets', data={'text': 'test'})


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
