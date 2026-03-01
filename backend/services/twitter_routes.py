"""Twitter API v2 Routes — 10 endpoints for complete integration"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from ..models import db, SNSAccount, SNSPost, SNSAnalytics, SNSOAuthState, User
from ..auth import require_auth, require_subscription
from ..input_validator import validate_string, sanitize_html
import json
import logging
import os
import secrets

from .twitter_api import TwitterAPI, TwitterAPIException, RateLimitException

logger = logging.getLogger('twitter.routes')

twitter_bp = Blueprint('twitter', __name__, url_prefix='/api/sns/twitter')


class TwitterServiceError(Exception):
    """Twitter service error"""
    pass


# ==================== HELPER FUNCTIONS ====================

def _get_twitter_client(access_token: str) -> TwitterAPI:
    """Create Twitter API client from access token"""
    return TwitterAPI(
        access_token=access_token,
        client_id=os.getenv('TWITTER_CLIENT_ID'),
        client_secret=os.getenv('TWITTER_CLIENT_SECRET'),
        redirect_uri=os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/api/sns/twitter/oauth/callback'),
    )


def _get_user_twitter_account(user_id: int, account_id: Optional[int] = None) -> SNSAccount:
    """Get Twitter account for user, validating ownership"""
    if account_id:
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=user_id,
            platform='twitter'
        ).first()
    else:
        account = SNSAccount.query.filter_by(
            user_id=user_id,
            platform='twitter',
            is_active=True
        ).first()

    if not account:
        raise TwitterServiceError('Twitter account not found or not owned by user')
    return account


# ==================== OAUTH 2.0 ENDPOINTS ====================

@twitter_bp.route('/oauth/authorize', methods=['GET'])
@require_auth
def oauth_authorize():
    """
    Initiate OAuth 2.0 authorization flow.

    Returns:
        JSON with authorization_url and state
    """
    try:
        state = secrets.token_urlsafe(32)
        client = TwitterAPI(
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret=os.getenv('TWITTER_CLIENT_SECRET'),
            redirect_uri=os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/api/sns/twitter/oauth/callback'),
        )

        auth_url, code_verifier = client.get_oauth_url(state)

        # Store state and code_verifier in DB (expires in 10 minutes)
        oauth_state = SNSOAuthState(
            user_id=g.user_id,
            platform='twitter',
            state=state,
            code_verifier=code_verifier,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.session.add(oauth_state)
        db.session.commit()

        return jsonify({
            'authorization_url': auth_url,
            'state': state,
        }), 200

    except Exception as e:
        logger.error(f"OAuth authorize error: {e}")
        return jsonify({'error': 'Failed to generate authorization URL'}), 500


@twitter_bp.route('/oauth/callback', methods=['GET'])
@require_auth
def oauth_callback():
    """
    Handle OAuth 2.0 callback from Twitter.

    Query params:
        code: Authorization code
        state: State token (CSRF protection)

    Returns:
        JSON with success status and account info
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')

        if not code or not state:
            return jsonify({'error': 'Missing code or state parameter'}), 400

        # Verify state
        oauth_state = SNSOAuthState.query.filter_by(
            user_id=g.user_id,
            platform='twitter',
            state=state,
        ).first()

        if not oauth_state or oauth_state.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired state'}), 400

        code_verifier = oauth_state.code_verifier

        # Exchange code for tokens
        client = TwitterAPI(
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret=os.getenv('TWITTER_CLIENT_SECRET'),
            redirect_uri=os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/api/sns/twitter/oauth/callback'),
        )

        token_data = client.exchange_oauth_code(code, code_verifier)

        # Get user info from Twitter
        client_with_token = _get_twitter_client(token_data['access_token'])
        user_info = client_with_token.get_account_info()

        # Store/update Twitter account
        account = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='twitter',
            account_name=user_info['username'],
        ).first()

        if not account:
            account = SNSAccount(
                user_id=g.user_id,
                platform='twitter',
                account_name=user_info['username'],
                external_account_id=user_info['user_id'],
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_expires_at=token_data['expires_at'],
                is_active=True,
            )
            db.session.add(account)
        else:
            account.external_account_id = user_info['user_id']
            account.access_token = token_data['access_token']
            account.refresh_token = token_data.get('refresh_token')
            account.token_expires_at = token_data['expires_at']
            account.is_active = True

        db.session.commit()

        # Delete used state
        db.session.delete(oauth_state)
        db.session.commit()

        return jsonify({
            'success': True,
            'account_id': account.id,
            'username': user_info['username'],
            'followers': user_info['followers'],
            'message': 'Twitter account linked successfully',
        }), 200

    except TwitterAPIException as e:
        logger.error(f"Twitter API error during callback: {e}")
        return jsonify({'error': 'Failed to exchange authorization code'}), 400
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({'error': 'Failed to complete authorization'}), 500


# ==================== TWEET ENDPOINTS ====================

@twitter_bp.route('/tweets', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def post_tweet():
    """
    POST /api/sns/twitter/tweets

    Post a single tweet.

    Request body:
    {
        "account_id": 123,
        "text": "Hello Twitter!",
        "media_ids": ["123456"],  # optional
        "reply_to_tweet_id": "789",  # optional
        "quote_tweet_id": "456",  # optional
        "schedule_at": "2025-02-27T10:00:00Z"  # optional, future timestamp
    }

    Returns:
        JSON with tweet_id, url, status
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate required fields
        if not data.get('text'):
            return jsonify({'error': 'Tweet text is required'}), 400

        account_id = data.get('account_id')
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        # Get Twitter account
        account = _get_user_twitter_account(g.user_id, account_id)

        # Validate tweet text
        valid, error, clean_text = validate_string(
            data['text'], 'Tweet text', min_length=1, max_length=280
        )
        if not valid:
            return jsonify({'error': error}), 400

        # Check scheduling
        schedule_at = data.get('schedule_at')
        status = 'scheduled' if schedule_at else 'published'

        if schedule_at:
            scheduled_dt = datetime.fromisoformat(schedule_at.replace('Z', '+00:00'))
            if scheduled_dt <= datetime.utcnow():
                return jsonify({'error': 'Scheduled time must be in the future'}), 400

        # Prepare Twitter API client
        client = _get_twitter_client(account.access_token)

        # Post tweet or schedule
        if schedule_at:
            # Store as scheduled post in DB
            sns_post = SNSPost(
                user_id=g.user_id,
                account_id=account.id,
                platform='twitter',
                content=clean_text,
                status='scheduled',
                scheduled_at=scheduled_dt,
                media_urls=data.get('media_ids', []),
                hashtags=data.get('hashtags', []),
            )
            db.session.add(sns_post)
            db.session.commit()

            return jsonify({
                'success': True,
                'post_id': sns_post.id,
                'text': clean_text,
                'status': 'scheduled',
                'scheduled_at': scheduled_dt.isoformat(),
            }), 201

        else:
            # Post immediately
            result = client.post_tweet(
                text=clean_text,
                media_ids=data.get('media_ids'),
                reply_to_tweet_id=data.get('reply_to_tweet_id'),
                quote_tweet_id=data.get('quote_tweet_id'),
            )

            # Store in DB
            sns_post = SNSPost(
                user_id=g.user_id,
                account_id=account.id,
                platform='twitter',
                content=clean_text,
                external_post_id=result['tweet_id'],
                status='published',
                published_at=datetime.utcnow(),
                media_urls=data.get('media_ids', []),
                hashtags=data.get('hashtags', []),
            )
            db.session.add(sns_post)
            db.session.commit()

            return jsonify({
                'success': True,
                'post_id': sns_post.id,
                'tweet_id': result['tweet_id'],
                'url': result['url'],
                'status': 'published',
                'created_at': result['created_at'],
            }), 201

    except RateLimitException as e:
        logger.warning(f"Rate limit exceeded: {e}")
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to post tweet'}), 400
    except Exception as e:
        logger.error(f"Post tweet error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/threads', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def post_thread():
    """
    POST /api/sns/twitter/threads

    Post a thread of tweets.

    Request body:
    {
        "account_id": 123,
        "tweets": [
            "First tweet (280 chars max)",
            "Second tweet (280 chars max)",
            "..."
        ]
    }

    Returns:
        JSON with all tweet IDs and URLs
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        account_id = data.get('account_id')
        tweets = data.get('tweets', [])

        if not account_id or not tweets:
            return jsonify({'error': 'account_id and tweets array are required'}), 400

        if len(tweets) > 100:
            return jsonify({'error': 'Thread cannot exceed 100 tweets'}), 400

        # Get Twitter account
        account = _get_user_twitter_account(g.user_id, account_id)

        # Validate all tweets
        for i, tweet_text in enumerate(tweets):
            if len(tweet_text) > 280:
                return jsonify({'error': f'Tweet {i + 1} exceeds 280 characters'}), 400

        # Post thread
        client = _get_twitter_client(account.access_token)
        result = client.post_thread(tweets)

        # Store in DB
        for i, tweet_data in enumerate(result['tweets']):
            sns_post = SNSPost(
                user_id=g.user_id,
                account_id=account.id,
                platform='twitter',
                content=tweets[i],
                external_post_id=tweet_data['tweet_id'],
                status='published',
                published_at=datetime.utcnow(),
            )
            db.session.add(sns_post)

        db.session.commit()

        return jsonify({
            'success': True,
            'thread_count': result['thread_count'],
            'tweets': result['tweets'],
            'created_at': result['created_at'],
        }), 201

    except RateLimitException:
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to post thread'}), 400
    except Exception as e:
        logger.error(f"Post thread error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/tweets/<tweet_id>/delete', methods=['DELETE'])
@require_auth
def delete_tweet(tweet_id):
    """Delete a tweet"""
    try:
        sns_post = SNSPost.query.filter_by(
            external_post_id=tweet_id,
            user_id=g.user_id,
            platform='twitter'
        ).first()

        if not sns_post:
            return jsonify({'error': 'Tweet not found'}), 404

        account = SNSAccount.query.get(sns_post.account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        client = _get_twitter_client(account.access_token)
        client.delete_tweet(tweet_id)

        sns_post.status = 'deleted'
        db.session.commit()

        return jsonify({'success': True, 'message': 'Tweet deleted'}), 200

    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to delete tweet'}), 400
    except Exception as e:
        logger.error(f"Delete tweet error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== ENGAGEMENT ENDPOINTS ====================

@twitter_bp.route('/<tweet_id>/like', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def like_tweet(tweet_id):
    """
    POST /api/sns/twitter/{tweet_id}/like

    Like a tweet.

    Returns:
        JSON with success status
    """
    try:
        account_id = request.json.get('account_id')
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        account = _get_user_twitter_account(g.user_id, account_id)
        client = _get_twitter_client(account.access_token)

        result = client.like_tweet(tweet_id)

        return jsonify(result), 200

    except RateLimitException:
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to like tweet'}), 400
    except Exception as e:
        logger.error(f"Like tweet error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/<tweet_id>/retweet', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def retweet_endpoint(tweet_id):
    """
    POST /api/sns/twitter/{tweet_id}/retweet

    Retweet a tweet.
    """
    try:
        account_id = request.json.get('account_id')
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        account = _get_user_twitter_account(g.user_id, account_id)
        client = _get_twitter_client(account.access_token)

        result = client.retweet(tweet_id)

        return jsonify(result), 200

    except RateLimitException:
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to retweet'}), 400
    except Exception as e:
        logger.error(f"Retweet error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/<tweet_id>/bookmark', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def bookmark_tweet_endpoint(tweet_id):
    """
    POST /api/sns/twitter/{tweet_id}/bookmark

    Bookmark a tweet.
    """
    try:
        account_id = request.json.get('account_id')
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        account = _get_user_twitter_account(g.user_id, account_id)
        client = _get_twitter_client(account.access_token)

        result = client.bookmark_tweet(tweet_id)

        return jsonify(result), 200

    except RateLimitException:
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to bookmark'}), 400
    except Exception as e:
        logger.error(f"Bookmark error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== ANALYTICS ENDPOINTS ====================

@twitter_bp.route('/<tweet_id>/insights', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_tweet_insights(tweet_id):
    """
    GET /api/sns/twitter/{tweet_id}/insights

    Get real-time insights for a specific tweet.

    Returns:
        JSON with likes, retweets, replies, impressions, etc.
    """
    try:
        account_id = request.args.get('account_id')
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        account = _get_user_twitter_account(g.user_id, int(account_id))
        client = _get_twitter_client(account.access_token)

        result = client.get_tweet(tweet_id)

        return jsonify(result), 200

    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to fetch tweet insights'}), 400
    except Exception as e:
        logger.error(f"Get tweet insights error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/account/insights', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_account_insights():
    """
    GET /api/sns/twitter/account/insights

    Get account-level analytics.

    Query params:
        account_id: Twitter account ID
        days: Number of days to analyze (default 7)

    Returns:
        JSON with followers, engagement, impressions, top tweets, etc.
    """
    try:
        account_id = request.args.get('account_id')
        days = int(request.args.get('days', 7))

        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400

        account = _get_user_twitter_account(g.user_id, int(account_id))
        client = _get_twitter_client(account.access_token)

        insights = client.get_insights(days=days)

        # Store in analytics DB (daily snapshot)
        analytics = SNSAnalytics(
            user_id=g.user_id,
            account_id=account.id,
            date=datetime.utcnow().date(),
            followers=insights['followers'],
            total_engagement=insights['total_engagement'],
            total_reach=0,  # Not available in this API call
            total_impressions=insights['total_impressions'],
        )
        db.session.merge(analytics)  # Merge to avoid duplicate key errors
        db.session.commit()

        return jsonify(insights), 200

    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to fetch account insights'}), 400
    except Exception as e:
        logger.error(f"Get account insights error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/trends', methods=['GET'])
@require_auth
def get_trends():
    """
    GET /api/sns/twitter/trends

    Get trending topics worldwide (or by location).

    Query params:
        woeid: Where On Earth ID (1 = worldwide, optional)

    Returns:
        JSON with trending topics and tweet volumes
    """
    try:
        woeid = int(request.args.get('woeid', 1))

        # Use first active account for API call
        account = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='twitter',
            is_active=True
        ).first()

        if not account:
            return jsonify({'error': 'No active Twitter account found'}), 404

        client = _get_twitter_client(account.access_token)
        trends = client.get_trending_topics(location_woeid=woeid)

        return jsonify({'trends': trends}), 200

    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to fetch trends'}), 400
    except Exception as e:
        logger.error(f"Get trends error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== ACCOUNT MANAGEMENT ENDPOINTS ====================

@twitter_bp.route('/accounts', methods=['GET'])
@require_auth
def get_twitter_accounts():
    """Get user's linked Twitter accounts with current status"""
    try:
        accounts = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='twitter'
        ).all()

        accounts_data = []
        for account in accounts:
            try:
                client = _get_twitter_client(account.access_token)
                user_info = client.get_account_info()
                status = 'active'
            except:
                status = 'inactive'
                user_info = {'followers': 0}

            accounts_data.append({
                'id': account.id,
                'username': account.account_name,
                'followers': user_info.get('followers', 0),
                'is_active': account.is_active,
                'linked_at': account.created_at.isoformat(),
                'status': status,
            })

        return jsonify(accounts_data), 200

    except Exception as e:
        logger.error(f"Get accounts error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
def unlink_twitter_account(account_id):
    """Unlink a Twitter account"""
    try:
        account = SNSAccount.query.filter_by(
            id=account_id,
            user_id=g.user_id,
            platform='twitter'
        ).first()

        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Revoke token
        try:
            client = _get_twitter_client(account.access_token)
            client.revoke_token()
        except:
            pass  # Token may already be revoked

        db.session.delete(account)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Account unlinked'}), 200

    except Exception as e:
        logger.error(f"Unlink account error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/account/info', methods=['GET'])
@require_auth
def get_account_info():
    """
    GET /api/sns/twitter/account/info

    Get authenticated user's profile information.

    Query params:
        account_id: Twitter account ID (optional, uses first active if not provided)

    Returns:
        JSON with user profile, followers, verification status, etc.
    """
    try:
        account_id = request.args.get('account_id')

        account = _get_user_twitter_account(g.user_id, int(account_id) if account_id else None)
        client = _get_twitter_client(account.access_token)

        user_info = client.get_account_info()

        return jsonify(user_info), 200

    except TwitterServiceError as e:
        logger.error(f"Service error: {e}")
        return jsonify({'error': str(e)}), 404
    except TwitterAPIException as e:
        logger.error(f"Twitter API error: {e}")
        return jsonify({'error': 'Failed to fetch account info'}), 400
    except Exception as e:
        logger.error(f"Get account info error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== UTILITY ENDPOINTS ====================

@twitter_bp.route('/rate-limit', methods=['GET'])
@require_auth
def get_rate_limit_status():
    """
    GET /api/sns/twitter/rate-limit

    Get current rate limit status.

    Returns:
        JSON with remaining requests, reset time, etc.
    """
    try:
        account_id = request.args.get('account_id')

        account = _get_user_twitter_account(g.user_id, int(account_id) if account_id else None)
        client = _get_twitter_client(account.access_token)

        status = client.get_rate_limit_status()

        return jsonify(status), 200

    except TwitterServiceError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Rate limit status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@twitter_bp.route('/health', methods=['GET'])
@require_auth
def health_check():
    """
    GET /api/sns/twitter/health

    Check if Twitter API connection is working.
    """
    try:
        account = SNSAccount.query.filter_by(
            user_id=g.user_id,
            platform='twitter',
            is_active=True
        ).first()

        if not account:
            return jsonify({'status': 'no_account'}), 200

        client = _get_twitter_client(account.access_token)
        is_healthy = client.health_check()

        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
