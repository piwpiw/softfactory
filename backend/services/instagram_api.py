"""Instagram Real API Integration Service (v1.0) — Production-Ready"""
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from functools import wraps
from urllib.parse import urlencode
import os
from flask import Blueprint, request, jsonify, g, session
from sqlalchemy import func

from ..models import db, SNSAccount, SNSPost, SNSAnalytics, User
from ..auth import require_auth, require_subscription
from ..input_validator import validate_string, validate_slug

logger = logging.getLogger('instagram.api')

# Instagram Graph API Base URL
INSTAGRAM_GRAPH_API_URL = "https://graph.instagram.com/v18.0"

# Configuration from environment
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID', '')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET', '')
INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI', 'http://localhost:8000/api/sns/instagram/callback')

# Blueprint
instagram_bp = Blueprint('instagram', __name__, url_prefix='/api/sns/instagram')


class InstagramAPIError(Exception):
    """Instagram API specific exception"""
    pass


class InstagramAPI:
    """Instagram Real API Integration"""

    def __init__(self, access_token: str):
        """Initialize with access token"""
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SoftFactory-Instagram/1.0',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str,
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     files: Optional[Dict] = None,
                     timeout: int = 30) -> Dict:
        """Make authenticated request to Instagram API with error handling"""
        url = f"{INSTAGRAM_GRAPH_API_URL}{endpoint}"

        # Add access token to params
        if params is None:
            params = {}
        params['access_token'] = self.access_token

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, data=data, files=files, timeout=timeout)
            else:
                raise InstagramAPIError(f"Unsupported HTTP method: {method}")

            # Handle HTTP errors
            if response.status_code == 429:
                raise InstagramAPIError("Rate limit exceeded. Please try again later.")
            elif response.status_code == 401:
                raise InstagramAPIError("Access token expired. Please re-authenticate.")
            elif response.status_code == 403:
                raise InstagramAPIError("Permission denied. Check account permissions.")
            elif not response.ok:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                raise InstagramAPIError(error_msg)

            return response.json()

        except requests.exceptions.Timeout:
            raise InstagramAPIError("Request timeout. Please try again.")
        except requests.exceptions.ConnectionError:
            raise InstagramAPIError("Connection error. Please check your internet connection.")
        except json.JSONDecodeError:
            raise InstagramAPIError("Invalid response from Instagram API.")

    def authenticate(self, code: str) -> Tuple[str, Dict]:
        """
        Exchange authorization code for access token (OAuth 2.0)
        Returns: (access_token, user_info)
        """
        token_url = "https://graph.instagram.com/v18.0/oauth/access_token"

        payload = {
            'client_id': INSTAGRAM_APP_ID,
            'client_secret': INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': INSTAGRAM_REDIRECT_URI,
            'code': code
        }

        try:
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            access_token = token_data.get('access_token')
            user_id = token_data.get('user_id')

            if not access_token or not user_id:
                raise InstagramAPIError("Failed to obtain access token")

            # Get user info
            user_info = self.get_account_info()
            user_info['user_id'] = user_id

            return access_token, user_info

        except requests.exceptions.RequestException as e:
            raise InstagramAPIError(f"Authentication failed: {str(e)}")

    def get_account_info(self) -> Dict:
        """
        Get Instagram account information
        Returns: {username, followers, following, bio, profile_picture_url, ...}
        """
        try:
            # Get me endpoint
            response = self._make_request(
                'GET',
                '/me',
                params={
                    'fields': 'id,username,name,biography,followers_count,follows_count,ig_metadata,profile_picture_url,website'
                }
            )

            return {
                'id': response.get('id'),
                'username': response.get('username'),
                'name': response.get('name'),
                'bio': response.get('biography', ''),
                'followers_count': response.get('followers_count', 0),
                'following_count': response.get('follows_count', 0),
                'profile_picture_url': response.get('profile_picture_url'),
                'website': response.get('website'),
                'account_type': 'business' if response.get('ig_metadata', {}).get('account_type') == 'BUSINESS' else 'personal'
            }

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to get account info: {str(e)}")

    def post_feed(self, image_url: str, caption: str = '', hashtags: Optional[List[str]] = None) -> str:
        """
        Post to Instagram feed (requires business/creator account)
        Returns: post_id
        """
        if not image_url:
            raise InstagramAPIError("image_url is required")

        # Build caption with hashtags
        full_caption = caption
        if hashtags:
            hashtag_str = ' '.join([f"#{tag.lstrip('#')}" for tag in hashtags])
            full_caption = f"{caption} {hashtag_str}".strip()

        try:
            # Get Instagram Business Account ID (IG User ID)
            account_info = self._make_request('GET', '/me', params={'fields': 'id'})
            ig_user_id = account_info.get('id')

            # Create media container (for scheduled posting)
            container_response = self._make_request(
                'POST',
                f'/{ig_user_id}/media',
                data={
                    'image_url': image_url,
                    'caption': full_caption,
                    'media_type': 'IMAGE'
                }
            )

            container_id = container_response.get('id')
            if not container_id:
                raise InstagramAPIError("Failed to create media container")

            # Publish immediately
            publish_response = self._make_request(
                'POST',
                f'/{ig_user_id}/media_publish',
                data={'creation_id': container_id}
            )

            post_id = publish_response.get('id')
            if not post_id:
                raise InstagramAPIError("Failed to publish post")

            return post_id

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to post to feed: {str(e)}")

    def post_story(self, image_url: str, text: str = '') -> str:
        """
        Post to Instagram story
        Returns: story_id
        """
        if not image_url:
            raise InstagramAPIError("image_url is required")

        try:
            account_info = self._make_request('GET', '/me', params={'fields': 'id'})
            ig_user_id = account_info.get('id')

            story_response = self._make_request(
                'POST',
                f'/{ig_user_id}/stories',
                data={
                    'image_url': image_url,
                    'story_sticker_ids': json.dumps([]) if text else None,
                    'caption': text
                }
            )

            story_id = story_response.get('id')
            if not story_id:
                raise InstagramAPIError("Failed to create story")

            return story_id

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to post story: {str(e)}")

    def post_reel(self, video_url: str, caption: str = '', thumbnail_url: Optional[str] = None) -> str:
        """
        Post to Instagram reels (requires business/creator account)
        Returns: reel_id
        """
        if not video_url:
            raise InstagramAPIError("video_url is required")

        try:
            account_info = self._make_request('GET', '/me', params={'fields': 'id'})
            ig_user_id = account_info.get('id')

            payload = {
                'video_url': video_url,
                'caption': caption,
                'media_type': 'REELS'
            }

            if thumbnail_url:
                payload['thumbnail_url'] = thumbnail_url

            reel_response = self._make_request(
                'POST',
                f'/{ig_user_id}/media',
                data=payload
            )

            container_id = reel_response.get('id')
            if not container_id:
                raise InstagramAPIError("Failed to create reel container")

            # Publish reel
            publish_response = self._make_request(
                'POST',
                f'/{ig_user_id}/media_publish',
                data={'creation_id': container_id}
            )

            reel_id = publish_response.get('id')
            if not reel_id:
                raise InstagramAPIError("Failed to publish reel")

            return reel_id

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to post reel: {str(e)}")

    def get_insights(self, post_id: str) -> Dict:
        """
        Get post insights (likes, comments, shares, reach, etc.)
        Returns: {likes, comments, shares, reach, impressions, ...}
        """
        if not post_id:
            raise InstagramAPIError("post_id is required")

        try:
            insights_response = self._make_request(
                'GET',
                f'/{post_id}/insights',
                params={
                    'metric': 'engagement,impressions,reach,saved',
                    'breakdown': 'action_type'
                }
            )

            metrics = {}
            for data_point in insights_response.get('data', []):
                metric_name = data_point.get('name')
                metric_values = data_point.get('values', [{}])
                metric_value = metric_values[0].get('value', 0) if metric_values else 0
                metrics[metric_name] = metric_value

            return {
                'likes': metrics.get('engagement', 0),
                'comments': metrics.get('engagement', 0),
                'shares': metrics.get('engagement', 0),
                'reach': metrics.get('reach', 0),
                'impressions': metrics.get('impressions', 0),
                'saved': metrics.get('saved', 0),
                'engagement_rate': self._calculate_engagement_rate(
                    metrics.get('engagement', 0),
                    metrics.get('impressions', 1)
                )
            }

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to get insights: {str(e)}")

    def get_media(self, limit: int = 25, after: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
        """
        Get user's recent posts
        Returns: (posts, next_cursor)
        """
        try:
            params = {
                'fields': 'id,caption,media_type,media_url,timestamp,like_count,comments_count',
                'limit': limit
            }

            if after:
                params['after'] = after

            response = self._make_request(
                'GET',
                '/me/media',
                params=params
            )

            posts = []
            for item in response.get('data', []):
                posts.append({
                    'id': item.get('id'),
                    'caption': item.get('caption', ''),
                    'media_type': item.get('media_type'),
                    'media_url': item.get('media_url'),
                    'timestamp': item.get('timestamp'),
                    'likes': item.get('like_count', 0),
                    'comments': item.get('comments_count', 0)
                })

            # Get next page cursor
            paging = response.get('paging', {})
            next_cursor = paging.get('cursors', {}).get('after')

            return posts, next_cursor

        except InstagramAPIError:
            raise
        except Exception as e:
            raise InstagramAPIError(f"Failed to get media: {str(e)}")

    def refresh_access_token(self, long_lived_token: str) -> str:
        """
        Refresh long-lived access token (valid for 60 days)
        Returns: new access token
        """
        try:
            refresh_url = f"{INSTAGRAM_GRAPH_API_URL}/refresh_access_token"
            payload = {
                'grant_type': 'ig_refresh_token',
                'access_token': long_lived_token
            }

            response = requests.post(refresh_url, params=payload, timeout=30)
            response.raise_for_status()

            new_token = response.json().get('access_token')
            if not new_token:
                raise InstagramAPIError("Failed to refresh token")

            return new_token

        except requests.exceptions.RequestException as e:
            raise InstagramAPIError(f"Token refresh failed: {str(e)}")

    @staticmethod
    def _calculate_engagement_rate(engagement: int, impressions: int) -> float:
        """Calculate engagement rate"""
        if impressions == 0:
            return 0.0
        return round((engagement / impressions) * 100, 2)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@instagram_bp.route('/oauth/authorize', methods=['GET'])
@require_auth
def instagram_oauth_authorize():
    """Initiate Instagram OAuth flow"""
    try:
        if not INSTAGRAM_APP_ID:
            return jsonify({'error': 'Instagram app not configured'}), 500

        auth_url = (
            'https://api.instagram.com/oauth/authorize'
            f'?client_id={INSTAGRAM_APP_ID}'
            f'&redirect_uri={INSTAGRAM_REDIRECT_URI}'
            '&scope=instagram_basic,instagram_graph_user_profile,instagram_graph_user_media'
            '&response_type=code'
        )

        return jsonify({'auth_url': auth_url}), 200

    except Exception as e:
        logger.error(f"OAuth authorize error: {str(e)}")
        return jsonify({'error': 'Failed to initiate OAuth flow'}), 500


@instagram_bp.route('/callback', methods=['GET'])
@require_auth
def instagram_oauth_callback():
    """Handle Instagram OAuth callback"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400

        # Exchange code for token
        instagram = InstagramAPI('')  # Temp instance to use authenticate method
        access_token, user_info = instagram.authenticate(code)

        # Save to database
        account = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='instagram',
            platform_user_id=user_info['id']
        ).first()

        if not account:
            account = SNSAccount(
                user_id=g.user_id,
                platform='instagram',
                account_name=user_info['username'],
                platform_user_id=user_info['id'],
                account_type=user_info.get('account_type', 'personal')
            )

        account.access_token = access_token
        account.profile_picture_url = user_info.get('profile_picture_url')
        account.followers_count = user_info.get('followers_count', 0)
        account.following_count = user_info.get('following_count', 0)
        account.token_expires_at = datetime.utcnow() + timedelta(days=60)
        account.is_active = True

        db.session.add(account)
        db.session.commit()

        return jsonify({
            'message': 'Instagram account connected successfully',
            'account': account.to_dict()
        }), 201

    except InstagramAPIError as e:
        logger.error(f"Instagram authentication error: {str(e)}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({'error': 'Failed to process callback'}), 500


@instagram_bp.route('/posts', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_instagram_post():
    """Create Instagram post (feed)"""
    try:
        data = request.get_json()

        # Validation
        account_id = data.get('account_id')
        image_url = validate_string(data.get('image_url', ''), 'image_url', min_len=10, max_len=2000)
        caption = validate_string(data.get('caption', ''), 'caption', max_len=2200)
        hashtags = data.get('hashtags', [])

        if not account_id or not image_url:
            return jsonify({'error': 'account_id and image_url are required'}), 400

        # Get account
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Instagram account not found'}), 404

        if not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Post to Instagram
        instagram = InstagramAPI(account.access_token)
        try:
            post_id = instagram.post_feed(image_url, caption, hashtags)
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                # Try to refresh token
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    post_id = instagram.post_feed(image_url, caption, hashtags)
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed. Please re-authenticate.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        # Save post record
        sns_post = SNSPost(
            user_id=g.user_id,
            account_id=account_id,
            platform='instagram',
            content=caption,
            media_url=image_url,
            status='published',
            platform_post_id=post_id,
            published_at=datetime.utcnow()
        )
        db.session.add(sns_post)
        db.session.commit()

        return jsonify({
            'message': 'Post created successfully',
            'post_id': post_id,
            'db_id': sns_post.id
        }), 201

    except Exception as e:
        logger.error(f"Create post error: {str(e)}")
        return jsonify({'error': 'Failed to create post'}), 500


@instagram_bp.route('/stories', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_instagram_story():
    """Create Instagram story"""
    try:
        data = request.get_json()

        # Validation
        account_id = data.get('account_id')
        image_url = validate_string(data.get('image_url', ''), 'image_url', min_len=10, max_len=2000)
        text = validate_string(data.get('text', ''), 'text', max_len=100)

        if not account_id or not image_url:
            return jsonify({'error': 'account_id and image_url are required'}), 400

        # Get account
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Instagram account not found'}), 404

        if not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Post story
        instagram = InstagramAPI(account.access_token)
        try:
            story_id = instagram.post_story(image_url, text)
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    story_id = instagram.post_story(image_url, text)
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed. Please re-authenticate.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        return jsonify({
            'message': 'Story created successfully',
            'story_id': story_id
        }), 201

    except Exception as e:
        logger.error(f"Create story error: {str(e)}")
        return jsonify({'error': 'Failed to create story'}), 500


@instagram_bp.route('/reels', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_instagram_reel():
    """Create Instagram reel"""
    try:
        data = request.get_json()

        # Validation
        account_id = data.get('account_id')
        video_url = validate_string(data.get('video_url', ''), 'video_url', min_len=10, max_len=2000)
        caption = validate_string(data.get('caption', ''), 'caption', max_len=2200)
        thumbnail_url = data.get('thumbnail_url')

        if not account_id or not video_url:
            return jsonify({'error': 'account_id and video_url are required'}), 400

        # Get account
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Instagram account not found'}), 404

        if not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Post reel
        instagram = InstagramAPI(account.access_token)
        try:
            reel_id = instagram.post_reel(video_url, caption, thumbnail_url)
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    reel_id = instagram.post_reel(video_url, caption, thumbnail_url)
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed. Please re-authenticate.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        # Save reel record
        sns_post = SNSPost(
            user_id=g.user_id,
            account_id=account_id,
            platform='instagram',
            content=caption,
            media_url=video_url,
            status='published',
            platform_post_id=reel_id,
            published_at=datetime.utcnow()
        )
        db.session.add(sns_post)
        db.session.commit()

        return jsonify({
            'message': 'Reel created successfully',
            'reel_id': reel_id,
            'db_id': sns_post.id
        }), 201

    except Exception as e:
        logger.error(f"Create reel error: {str(e)}")
        return jsonify({'error': 'Failed to create reel'}), 500


@instagram_bp.route('/<int:post_id>/insights', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_post_insights(post_id):
    """Get Instagram post insights"""
    try:
        # Get post from database
        sns_post = SNSPost.query.filter_by(
            id=post_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not sns_post or not sns_post.platform_post_id:
            return jsonify({'error': 'Post not found'}), 404

        # Get account
        account = sns_post.account
        if not account or not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Fetch insights
        instagram = InstagramAPI(account.access_token)
        try:
            insights = instagram.get_insights(sns_post.platform_post_id)
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    insights = instagram.get_insights(sns_post.platform_post_id)
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        # Save to analytics
        analytics = SNSAnalytics.query.filter_by(
            post_id=post_id
        ).first()

        if not analytics:
            analytics = SNSAnalytics(post_id=post_id)

        analytics.likes = insights.get('likes', 0)
        analytics.comments = insights.get('comments', 0)
        analytics.shares = insights.get('shares', 0)
        analytics.reach = insights.get('reach', 0)
        analytics.updated_at = datetime.utcnow()

        db.session.add(analytics)
        db.session.commit()

        return jsonify(insights), 200

    except Exception as e:
        logger.error(f"Get insights error: {str(e)}")
        return jsonify({'error': 'Failed to fetch insights'}), 500


@instagram_bp.route('/account/info', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_instagram_account_info():
    """Get Instagram account information"""
    try:
        account_id = request.args.get('account_id', type=int)

        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        # Get account
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Instagram account not found'}), 404

        if not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Fetch account info
        instagram = InstagramAPI(account.access_token)
        try:
            info = instagram.get_account_info()
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    info = instagram.get_account_info()
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        # Update database
        account.followers_count = info.get('followers_count', 0)
        account.following_count = info.get('following_count', 0)
        db.session.commit()

        return jsonify(info), 200

    except Exception as e:
        logger.error(f"Get account info error: {str(e)}")
        return jsonify({'error': 'Failed to fetch account info'}), 500


@instagram_bp.route('/media', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_instagram_media():
    """Get user's recent Instagram posts"""
    try:
        account_id = request.args.get('account_id', type=int)
        limit = request.args.get('limit', 25, type=int)
        after = request.args.get('after')

        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        if limit > 100:
            limit = 100

        # Get account
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Instagram account not found'}), 404

        if not account.access_token:
            return jsonify({'error': 'Account not authenticated'}), 401

        # Fetch media
        instagram = InstagramAPI(account.access_token)
        try:
            posts, next_cursor = instagram.get_media(limit, after)
        except InstagramAPIError as e:
            if "token" in str(e).lower():
                try:
                    account.access_token = instagram.refresh_access_token(account.access_token)
                    db.session.commit()
                    posts, next_cursor = instagram.get_media(limit, after)
                except InstagramAPIError:
                    return jsonify({'error': 'Token refresh failed.'}), 401
            else:
                return jsonify({'error': str(e)}), 400

        return jsonify({
            'posts': posts,
            'next_cursor': next_cursor
        }), 200

    except Exception as e:
        logger.error(f"Get media error: {str(e)}")
        return jsonify({'error': 'Failed to fetch media'}), 500


@instagram_bp.route('/accounts', methods=['GET'])
@require_auth
def get_instagram_accounts():
    """Get user's Instagram accounts"""
    try:
        accounts = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='instagram'
        ).all()

        return jsonify([account.to_dict() for account in accounts]), 200

    except Exception as e:
        logger.error(f"Get accounts error: {str(e)}")
        return jsonify({'error': 'Failed to fetch accounts'}), 500


@instagram_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
def disconnect_instagram_account(account_id):
    """Disconnect Instagram account"""
    try:
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='instagram'
        ).first()

        if not account:
            return jsonify({'error': 'Account not found'}), 404

        db.session.delete(account)
        db.session.commit()

        return jsonify({'message': 'Account disconnected successfully'}), 200

    except Exception as e:
        logger.error(f"Disconnect account error: {str(e)}")
        return jsonify({'error': 'Failed to disconnect account'}), 500
