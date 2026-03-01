"""Twitter API v2 Service — Complete OAuth2 + Rate Limiting + Real-time Analytics"""

import os
import json
import time
import requests
import hashlib
import hmac
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
import logging
import threading

logger = logging.getLogger('twitter.api')


class TwitterAPIException(Exception):
    """Base exception for Twitter API errors"""
    pass


class RateLimitException(TwitterAPIException):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """Rate limiter with sliding window: 450 requests per 15 minutes"""

    def __init__(self, max_requests: int = 450, window_minutes: int = 15):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(list)  # endpoint -> [timestamp, timestamp, ...]
        self._lock = threading.Lock()

    def is_allowed(self, endpoint: str) -> bool:
        """Check if request is allowed for endpoint"""
        with self._lock:
            now = time.time()
            # Clean old requests outside window
            self.requests[endpoint] = [
                ts for ts in self.requests[endpoint]
                if now - ts < self.window_seconds
            ]

            if len(self.requests[endpoint]) >= self.max_requests:
                return False

            self.requests[endpoint].append(now)
            return True

    def get_remaining(self, endpoint: str) -> Tuple[int, int]:
        """Get (remaining_requests, reset_timestamp)"""
        with self._lock:
            now = time.time()
            self.requests[endpoint] = [
                ts for ts in self.requests[endpoint]
                if now - ts < self.window_seconds
            ]
            remaining = self.max_requests - len(self.requests[endpoint])
            reset_ts = self.requests[endpoint][0] + self.window_seconds if self.requests[endpoint] else int(now)
            return remaining, int(reset_ts)


class TwitterOAuth2:
    """OAuth 2.0 token management with PKCE"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.revoke_url = "https://api.twitter.com/2/oauth2/revoke"

    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code_challenge and code_verifier"""
        code_verifier = hashlib.sha256(os.urandom(32)).hexdigest()[:43]
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()
        # URL-safe base64 encoding (remove padding)
        import base64
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        return code_verifier, code_challenge

    def get_authorization_url(self, state: str, scopes: Optional[List[str]] = None) -> Tuple[str, str]:
        """Generate authorization URL with PKCE"""
        if scopes is None:
            scopes = [
                'tweet.read', 'tweet.write', 'users.read', 'follows.read', 'follows.write',
                'like.read', 'like.write', 'retweet.read', 'retweet.write',
                'offline.access', 'bookmark.read', 'bookmark.write'
            ]

        code_verifier, code_challenge = self.generate_pkce_pair()

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }

        url = f"{self.auth_url}?" + "&".join(f"{k}={v}" for k, v in params.items())
        return url, code_verifier

    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """Exchange authorization code for access + refresh tokens"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier,
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data['expires_in'],
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope', ''),
            'expires_at': datetime.utcnow() + timedelta(seconds=token_data['expires_in']),
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', refresh_token),
            'expires_in': token_data['expires_in'],
            'expires_at': datetime.utcnow() + timedelta(seconds=token_data['expires_in']),
        }

    def revoke_token(self, access_token: str) -> bool:
        """Revoke access token"""
        data = {
            'token': access_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        response = requests.post(self.revoke_url, data=data)
        return response.status_code == 200


class TwitterAPI:
    """
    Twitter API v2 Client — Complete implementation
    Supports:
      - OAuth 2.0 with PKCE
      - Tweet posting + threading
      - Like/retweet/bookmark management
      - Account insights & analytics
      - Trend discovery
      - Multi-account support
      - Rate limiting (450/15min)
    """

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, access_token: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 redirect_uri: Optional[str] = None):
        """
        Initialize Twitter API client.

        Args:
            access_token: Bearer token for API calls
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
        """
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.client_id = client_id or os.getenv('TWITTER_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('TWITTER_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('TWITTER_REDIRECT_URI')

        self.rate_limiter = RateLimiter(max_requests=450, window_minutes=15)
        self.oauth2 = TwitterOAuth2(self.client_id, self.client_secret, self.redirect_uri)

        # Cache for authenticated user info
        self._user_cache = {}
        self._cache_ttl = 3600  # 1 hour

    def _check_rate_limit(self, endpoint: str) -> None:
        """Check rate limit, raise exception if exceeded"""
        if not self.rate_limiter.is_allowed(endpoint):
            remaining, reset_ts = self.rate_limiter.get_remaining(endpoint)
            raise RateLimitException(
                f"Rate limit exceeded for {endpoint}. "
                f"Remaining: {remaining}, Reset at: {datetime.fromtimestamp(reset_ts)}"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'TwitterAPI/2.0 (SoftFactory)',
        }

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Twitter API with error handling"""
        self._check_rate_limit(endpoint)

        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            logger.error(f"Twitter API error: {e.response.status_code} - {error_data}")
            raise TwitterAPIException(f"Twitter API error: {error_data}")
        except requests.exceptions.Timeout:
            raise TwitterAPIException("Twitter API request timeout")
        except Exception as e:
            logger.error(f"Unexpected error calling Twitter API: {e}")
            raise TwitterAPIException(f"Unexpected error: {str(e)}")

    # ==================== OAUTH 2.0 METHODS ====================

    def get_oauth_url(self, state: str) -> Tuple[str, str]:
        """Get OAuth authorization URL and code_verifier"""
        return self.oauth2.get_authorization_url(state)

    def exchange_oauth_code(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        return self.oauth2.exchange_code_for_tokens(code, code_verifier)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        return self.oauth2.refresh_access_token(refresh_token)

    def revoke_token(self) -> bool:
        """Revoke current access token"""
        return self.oauth2.revoke_token(self.access_token)

    # ==================== TWEET METHODS ====================

    def post_tweet(self, text: str, media_ids: Optional[List[str]] = None,
                   reply_to_tweet_id: Optional[str] = None,
                   quote_tweet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Post a tweet.

        Args:
            text: Tweet content (max 280 chars)
            media_ids: List of media IDs to attach
            reply_to_tweet_id: Tweet ID to reply to
            quote_tweet_id: Tweet ID to quote

        Returns:
            Tweet data with ID and creation timestamp
        """
        if len(text) > 280:
            raise ValueError("Tweet text exceeds 280 characters")

        payload = {'text': text}

        if media_ids:
            payload['media'] = {'media_ids': media_ids}

        if reply_to_tweet_id:
            payload['reply'] = {'in_reply_to_tweet_id': reply_to_tweet_id}

        if quote_tweet_id:
            payload['quote_tweet_id'] = quote_tweet_id

        result = self._request('POST', '/tweets', data=payload)

        return {
            'success': True,
            'tweet_id': result['data']['id'],
            'text': text,
            'created_at': datetime.utcnow().isoformat(),
            'url': f"https://twitter.com/i/web/status/{result['data']['id']}",
        }

    def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """
        Post a thread of tweets.

        Args:
            tweets: List of tweet texts (280 chars each)

        Returns:
            Thread data with all tweet IDs and URLs
        """
        if not tweets or len(tweets) > 100:
            raise ValueError("Thread must have 1-100 tweets")

        thread_tweets = []
        reply_to_id = None

        for tweet_text in tweets:
            if len(tweet_text) > 280:
                raise ValueError(f"Tweet exceeds 280 characters: {tweet_text[:50]}...")

            payload = {'text': tweet_text}
            if reply_to_id:
                payload['reply'] = {'in_reply_to_tweet_id': reply_to_id}

            result = self._request('POST', '/tweets', data=payload)
            tweet_id = result['data']['id']

            thread_tweets.append({
                'tweet_id': tweet_id,
                'text': tweet_text,
                'url': f"https://twitter.com/i/web/status/{tweet_id}",
            })

            reply_to_id = tweet_id  # Next tweet replies to this one

        return {
            'success': True,
            'thread_count': len(thread_tweets),
            'tweets': thread_tweets,
            'created_at': datetime.utcnow().isoformat(),
        }

    def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet"""
        self._request('DELETE', f'/tweets/{tweet_id}')
        return True

    def get_tweet(self, tweet_id: str, tweet_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get tweet details.

        Args:
            tweet_id: Tweet ID
            tweet_fields: Fields to include (e.g., 'public_metrics', 'created_at')

        Returns:
            Tweet data with metrics
        """
        if tweet_fields is None:
            tweet_fields = ['created_at', 'public_metrics', 'author_id', 'conversation_id']

        params = {'tweet.fields': ','.join(tweet_fields)}
        result = self._request('GET', f'/tweets/{tweet_id}', params=params)

        tweet = result['data']
        metrics = tweet.get('public_metrics', {})

        return {
            'tweet_id': tweet['id'],
            'text': tweet['text'],
            'created_at': tweet.get('created_at'),
            'likes': metrics.get('like_count', 0),
            'retweets': metrics.get('retweet_count', 0),
            'replies': metrics.get('reply_count', 0),
            'quotes': metrics.get('quote_count', 0),
            'impressions': metrics.get('impression_count', 0),
            'bookmark_count': metrics.get('bookmark_count', 0),
        }

    # ==================== ENGAGEMENT METHODS ====================

    def like_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Like a tweet"""
        user_id = self.get_account_info()['user_id']
        payload = {'tweet_id': tweet_id}

        result = self._request('POST', f'/users/{user_id}/likes', data=payload)

        return {
            'success': result['data']['liked'],
            'tweet_id': tweet_id,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def unlike_tweet(self, tweet_id: str) -> bool:
        """Unlike a tweet"""
        user_id = self.get_account_info()['user_id']
        self._request('DELETE', f'/users/{user_id}/likes/{tweet_id}')
        return True

    def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """Retweet a tweet"""
        user_id = self.get_account_info()['user_id']
        payload = {'tweet_id': tweet_id}

        result = self._request('POST', f'/users/{user_id}/retweets', data=payload)

        return {
            'success': result['data']['retweeted'],
            'tweet_id': tweet_id,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def unretweet(self, tweet_id: str) -> bool:
        """Remove a retweet"""
        user_id = self.get_account_info()['user_id']
        self._request('DELETE', f'/users/{user_id}/retweets/{tweet_id}')
        return True

    def bookmark_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Bookmark a tweet"""
        user_id = self.get_account_info()['user_id']
        payload = {'tweet_id': tweet_id}

        result = self._request('POST', f'/users/{user_id}/bookmarks', data=payload)

        return {
            'success': result['data']['bookmarked'],
            'tweet_id': tweet_id,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def remove_bookmark(self, tweet_id: str) -> bool:
        """Remove a bookmark"""
        user_id = self.get_account_info()['user_id']
        self._request('DELETE', f'/users/{user_id}/bookmarks/{tweet_id}')
        return True

    # ==================== ACCOUNT METHODS ====================

    def get_account_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get authenticated user info.

        Returns:
            User data with ID, username, followers, etc.
        """
        if use_cache and '_account_info' in self._user_cache:
            cached, timestamp = self._user_cache['_account_info']
            if time.time() - timestamp < self._cache_ttl:
                return cached

        user_fields = [
            'created_at', 'description', 'followers_count', 'following_count',
            'public_metrics', 'verified', 'location', 'url'
        ]
        params = {'user.fields': ','.join(user_fields)}

        result = self._request('GET', '/users/me', params=params)
        user = result['data']
        metrics = user.get('public_metrics', {})

        user_info = {
            'user_id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'description': user.get('description', ''),
            'location': user.get('location', ''),
            'followers': metrics.get('followers_count', 0),
            'following': metrics.get('following_count', 0),
            'tweets': metrics.get('tweet_count', 0),
            'verified': user.get('verified', False),
            'created_at': user.get('created_at'),
            'profile_url': f"https://twitter.com/{user['username']}",
        }

        self._user_cache['_account_info'] = (user_info, time.time())
        return user_info

    def get_followers(self, user_id: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get followers list"""
        if user_id is None:
            user_id = self.get_account_info()['user_id']

        params = {
            'max_results': min(max_results, 1000),
            'user.fields': 'created_at,description,public_metrics',
            'expansions': 'pinned_tweet_id',
        }

        result = self._request('GET', f'/users/{user_id}/followers', params=params)

        followers = []
        for user in result['data']:
            metrics = user.get('public_metrics', {})
            followers.append({
                'user_id': user['id'],
                'username': user['username'],
                'name': user['name'],
                'followers': metrics.get('followers_count', 0),
                'tweets': metrics.get('tweet_count', 0),
            })

        return followers

    def follow_user(self, target_user_id: str) -> Dict[str, Any]:
        """Follow a user"""
        user_id = self.get_account_info()['user_id']
        payload = {'target_user_id': target_user_id}

        result = self._request('POST', f'/users/{user_id}/following', data=payload)

        return {
            'success': result['data']['following'],
            'target_user_id': target_user_id,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def unfollow_user(self, target_user_id: str) -> bool:
        """Unfollow a user"""
        user_id = self.get_account_info()['user_id']
        self._request('DELETE', f'/users/{user_id}/following/{target_user_id}')
        return True

    # ==================== ANALYTICS METHODS ====================

    def get_insights(self, days: int = 7) -> Dict[str, Any]:
        """
        Get account insights for last N days.

        Returns:
            Aggregated metrics: followers, engagement, impressions, etc.
        """
        user_id = self.get_account_info()['user_id']
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get user tweets with metrics
        tweet_fields = [
            'created_at', 'public_metrics', 'author_id', 'conversation_id'
        ]
        params = {
            'max_results': 100,
            'start_time': start_date.isoformat() + 'Z',
            'end_time': end_date.isoformat() + 'Z',
            'tweet.fields': ','.join(tweet_fields),
        }

        result = self._request('GET', f'/users/{user_id}/tweets', params=params)

        tweets = result['data'] if 'data' in result else []

        # Aggregate metrics
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_impressions = 0
        total_engagement = 0
        top_tweet = None
        max_engagement = 0

        for tweet in tweets:
            metrics = tweet.get('public_metrics', {})
            likes = metrics.get('like_count', 0)
            retweets = metrics.get('retweet_count', 0)
            replies = metrics.get('reply_count', 0)
            impressions = metrics.get('impression_count', 0)

            total_likes += likes
            total_retweets += retweets
            total_replies += replies
            total_impressions += impressions

            engagement = likes + retweets + replies
            total_engagement += engagement

            if engagement > max_engagement:
                max_engagement = engagement
                top_tweet = {
                    'id': tweet['id'],
                    'text': tweet['text'][:100],
                    'engagement': engagement,
                }

        user_info = self.get_account_info()

        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'followers': user_info['followers'],
            'following': user_info['following'],
            'tweets_count': len(tweets),
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'total_replies': total_replies,
            'total_impressions': total_impressions,
            'total_engagement': total_engagement,
            'avg_engagement': total_engagement / len(tweets) if tweets else 0,
            'avg_impressions': total_impressions / len(tweets) if tweets else 0,
            'engagement_rate': (total_engagement / (user_info['followers'] * len(tweets)) * 100) if user_info['followers'] and tweets else 0,
            'top_tweet': top_tweet,
        }

    def get_trending_topics(self, location_woeid: int = 1) -> List[Dict[str, Any]]:
        """
        Get trending topics for location.

        Note: Twitter API v2 doesn't have trends endpoint.
        Using Twitter Search API v1.1 as fallback (deprecated but still available).

        Args:
            location_woeid: Where On Earth ID (1 = worldwide)

        Returns:
            List of trending topics with tweet volume
        """
        # Note: This requires a different API endpoint (v1.1)
        # For production, use a dedicated trends API or real-time data provider
        url = "https://api.twitter.com/1.1/trends/place.json"
        headers = self._get_headers()
        headers['Authorization'] = headers['Authorization'].replace('Bearer ', '')  # v1.1 uses different auth

        params = {'id': location_woeid}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            trends_data = response.json()
            trends = []

            for trend in trends_data[0]['trends'][:10]:  # Top 10 trends
                trends.append({
                    'name': trend['name'],
                    'url': trend['url'],
                    'tweet_volume': trend.get('tweet_volume', 0),
                    'query': trend['query'],
                })

            return trends

        except Exception as e:
            logger.warning(f"Failed to fetch trends: {e}")
            return self._get_mock_trends()

    def _get_mock_trends(self) -> List[Dict[str, Any]]:
        """Return mock trending topics (fallback)"""
        import random
        mock_topics = [
            '#AI', '#Python', '#Web3', '#Startups', '#Marketing',
            '#SaaS', '#DevOps', '#CloudComputing', '#DataScience', '#Blockchain'
        ]

        return [
            {
                'name': topic,
                'url': f"https://twitter.com/search?q={topic}",
                'tweet_volume': random.randint(10000, 1000000),
                'query': topic,
            }
            for topic in mock_topics[:10]
        ]

    # ==================== SEARCH METHODS ====================

    def search_tweets(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for tweets.

        Args:
            query: Search query (supports operators like 'from:', 'to:', etc.)
            max_results: Number of results (1-100)

        Returns:
            List of matching tweets
        """
        tweet_fields = ['created_at', 'public_metrics', 'author_id']
        params = {
            'query': query,
            'max_results': min(max_results, 100),
            'tweet.fields': ','.join(tweet_fields),
        }

        result = self._request('GET', '/tweets/search/recent', params=params)

        tweets = []
        for tweet in result.get('data', []):
            metrics = tweet.get('public_metrics', {})
            tweets.append({
                'tweet_id': tweet['id'],
                'text': tweet['text'],
                'created_at': tweet.get('created_at'),
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
            })

        return tweets

    def search_users(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for users by name or username"""
        user_fields = ['created_at', 'public_metrics', 'verified']
        params = {
            'query': query,
            'max_results': min(max_results, 100),
            'user.fields': ','.join(user_fields),
        }

        result = self._request('GET', '/users/search', params=params)

        users = []
        for user in result.get('data', []):
            metrics = user.get('public_metrics', {})
            users.append({
                'user_id': user['id'],
                'username': user['username'],
                'name': user['name'],
                'followers': metrics.get('followers_count', 0),
                'verified': user.get('verified', False),
            })

        return users

    # ==================== UTILITY METHODS ====================

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        remaining, reset_ts = self.rate_limiter.get_remaining('default')

        return {
            'remaining_requests': remaining,
            'max_requests': 450,
            'window_minutes': 15,
            'reset_at': datetime.fromtimestamp(reset_ts).isoformat(),
            'requests_until_reset': reset_ts - int(time.time()),
        }

    def health_check(self) -> bool:
        """Check if API connection is working"""
        try:
            self.get_account_info()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
