"""SNS Auto Service - Global SNS Automation Platform

32 API Endpoints covering:
- OAuth (3)
- Accounts (4)
- Posts (5)
- Analytics (3)
- Media (2)
- Templates (4)
- Inbox (3)
- Calendar (1)
- Campaigns (3)
- AI (3)
- Settings (2)
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import mimetypes
from werkzeug.utils import secure_filename

from backend.models import (
    db, SNSAccount, SNSPost, SNSCampaign, SNSTemplate, SNSAnalytics,
    SNSInboxMessage, SNSOAuthState, SNSSettings, User
)
from backend.auth import require_auth
from backend.services.sns_platforms import get_client
from backend.services.sns_cache import cache_get, cache_set, cache_invalidate

sns_bp = Blueprint('sns', __name__, url_prefix='/api/sns')

# Configuration
UPLOAD_FOLDER = 'D:/Project/uploads/sns/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============ OAUTH (3 endpoints) ============

@sns_bp.route('/oauth/<platform>/authorize', methods=['GET'])
@require_auth
def oauth_authorize(platform, user_id):
    """Initiate OAuth flow for platform"""
    if platform not in ['instagram', 'facebook', 'twitter', 'linkedin', 'tiktok', 'youtube', 'pinterest', 'threads', 'youtube_shorts']:
        return jsonify({'error': 'Invalid platform'}), 400

    try:
        client = get_client(platform)
        if not client:
            return jsonify({'error': f'Platform {platform} not supported'}), 400

        # Generate state token for CSRF prevention
        import secrets
        state_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        oauth_state = SNSOAuthState(
            user_id=user_id,
            platform=platform,
            state_token=state_token,
            expires_at=expires_at
        )
        db.session.add(oauth_state)
        db.session.commit()

        auth_url = client.get_auth_url()
        return jsonify({
            'auth_url': auth_url,
            'state': state_token,
            'platform': platform
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/oauth/<platform>/callback', methods=['GET'])
@require_auth
def oauth_callback(platform, user_id):
    """Handle OAuth callback and exchange code for token"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        return jsonify({'error': 'Missing code or state parameter'}), 400

    try:
        # Verify state token
        oauth_state = SNSOAuthState.query.filter_by(
            user_id=user_id,
            platform=platform,
            state_token=state
        ).first()

        if not oauth_state or oauth_state.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired state token'}), 401

        # Exchange code for token
        client = get_client(platform)
        token_response = client.exchange_code_for_token(code)

        if not token_response.get('access_token'):
            return jsonify({'error': 'Failed to obtain access token'}), 400

        # Save/update SNSAccount
        account = SNSAccount.query.filter_by(
            user_id=user_id,
            platform=platform,
            platform_user_id=token_response.get('platform_user_id')
        ).first()

        if not account:
            account = SNSAccount(
                user_id=user_id,
                platform=platform,
                account_name=token_response.get('account_name', f'{platform}_account'),
                platform_user_id=token_response.get('platform_user_id')
            )

        account.access_token = token_response['access_token']
        account.refresh_token = token_response.get('refresh_token')
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_response.get('expires_in', 5184000))
        account.profile_picture_url = token_response.get('profile_picture_url')
        account.followers_count = token_response.get('followers_count', 0)
        account.permissions_json = token_response.get('permissions', {})

        db.session.add(account)
        db.session.delete(oauth_state)
        db.session.commit()

        cache_invalidate(f'accounts:{user_id}')

        return jsonify({
            'success': True,
            'account': account.to_dict(),
            'message': f'{platform} account connected successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/oauth/<platform>/simulate-callback', methods=['GET'])
@require_auth
def oauth_simulate_callback(platform, user_id):
    """Simulate OAuth callback for demo/testing"""
    try:
        # Create or update account in simulation mode
        account = SNSAccount.query.filter_by(
            user_id=user_id,
            platform=platform
        ).first()

        if not account:
            account = SNSAccount(
                user_id=user_id,
                platform=platform,
                account_name=f'Demo {platform.title()} Account',
                platform_user_id=f'demo_{platform}_user_123'
            )

        # Set simulation mode tokens
        account.access_token = f'sim_{platform}_token_123'
        account.refresh_token = f'sim_{platform}_refresh_123'
        account.token_expires_at = datetime.utcnow() + timedelta(days=60)
        account.profile_picture_url = f'https://via.placeholder.com/150'
        account.followers_count = 1000 + hash(platform) % 10000
        account.account_type = 'business'

        db.session.add(account)
        db.session.commit()

        cache_invalidate(f'accounts:{user_id}')

        return jsonify({
            'success': True,
            'account': account.to_dict(),
            'message': f'{platform} account connected in simulation mode'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ ACCOUNTS (4 endpoints) ============

@sns_bp.route('/accounts', methods=['GET'])
@require_auth
def get_accounts(user_id):
    """List all SNS accounts for user"""
    try:
        # Check cache first
        cached = cache_get(f'accounts:{user_id}')
        if cached:
            return jsonify({'accounts': cached}), 200

        accounts = SNSAccount.query.filter_by(user_id=user_id).all()
        accounts_data = [acc.to_dict() for acc in accounts]

        # Cache for 2 minutes
        cache_set(f'accounts:{user_id}', accounts_data, ttl=120)

        return jsonify({'accounts': accounts_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/accounts', methods=['POST'])
@require_auth
def create_account(user_id):
    """Manually add SNS account"""
    data = request.json
    try:
        account = SNSAccount(
            user_id=user_id,
            platform=data.get('platform'),
            account_name=data.get('account_name'),
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token'),
            platform_user_id=data.get('platform_user_id'),
            profile_picture_url=data.get('profile_picture_url'),
            account_type=data.get('account_type', 'personal')
        )
        db.session.add(account)
        db.session.commit()

        cache_invalidate(f'accounts:{user_id}')

        return jsonify({'account': account.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/accounts/<int:account_id>', methods=['GET'])
@require_auth
def get_account(account_id, user_id):
    """Get specific account details"""
    try:
        account = SNSAccount.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        return jsonify({'account': account.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/accounts/<int:account_id>/reconnect', methods=['POST'])
@require_auth
def reconnect_account(account_id, user_id):
    """Reconnect expired token for account"""
    try:
        account = SNSAccount.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Check if token is expired
        if account.token_expires_at and account.token_expires_at > datetime.utcnow():
            return jsonify({'message': 'Token still valid'}), 200

        # Try to refresh token
        client = get_client(account.platform, account.refresh_token)
        result = client.refresh_token_if_expired(account.token_expires_at)

        if result:
            account.access_token = result['access_token']
            if 'refresh_token' in result:
                account.refresh_token = result['refresh_token']
            account.token_expires_at = datetime.utcnow() + timedelta(seconds=result.get('expires_in', 5184000))
            db.session.commit()
            cache_invalidate(f'accounts:{user_id}')

        return jsonify({'account': account.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ POSTS (6 endpoints) ============

@sns_bp.route('/posts', methods=['GET'])
@require_auth
def get_posts(user_id):
    """List all posts for user with filters"""
    status = request.args.get('status', None)  # draft, scheduled, published, failed
    platform = request.args.get('platform', None)
    limit = int(request.args.get('limit', 50))

    try:
        query = SNSPost.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)
        if platform:
            query = query.filter_by(platform=platform)

        posts = query.order_by(SNSPost.created_at.desc()).limit(limit).all()
        posts_data = [post.to_dict() for post in posts]

        return jsonify({'posts': posts_data, 'count': len(posts_data)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    """Create draft SNS post"""
    data = request.json
    try:
        account_ids = data.get('account_ids', [])
        if not account_ids:
            return jsonify({'error': 'At least one account required'}), 400

        posts_created = []
        for account_id in account_ids:
            account = SNSAccount.query.filter_by(id=account_id, user_id=user_id).first()
            if not account:
                continue

            post = SNSPost(
                user_id=user_id,
                account_id=account_id,
                content=data.get('content'),
                platform=account.platform,
                status='draft',
                media_urls=data.get('media_urls', []),
                hashtags=data.get('hashtags', []),
                link_url=data.get('link_url'),
                template_type=data.get('template_type')
            )
            db.session.add(post)
            posts_created.append(post)

        db.session.commit()
        cache_invalidate(f'posts:{user_id}')

        return jsonify({
            'posts': [post.to_dict() for post in posts_created],
            'count': len(posts_created)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/posts/bulk', methods=['POST'])
@require_auth
def bulk_create_posts(user_id):
    """Create multi-account post in one request"""
    data = request.json
    try:
        platforms = data.get('platforms', [])
        content = data.get('content')

        if not platforms or not content:
            return jsonify({'error': 'platforms and content required'}), 400

        posts_created = []
        for platform in platforms:
            accounts = SNSAccount.query.filter_by(user_id=user_id, platform=platform).all()

            for account in accounts:
                post = SNSPost(
                    user_id=user_id,
                    account_id=account.id,
                    content=content,
                    platform=platform,
                    status=data.get('status', 'draft'),
                    scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
                    media_urls=data.get('media_urls', []),
                    hashtags=data.get('hashtags', []),
                    link_url=data.get('link_url'),
                    campaign_id=data.get('campaign_id')
                )
                db.session.add(post)
                posts_created.append(post)

        db.session.commit()
        cache_invalidate(f'posts:{user_id}')

        return jsonify({
            'posts': [post.to_dict() for post in posts_created],
            'count': len(posts_created)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/posts/<int:post_id>', methods=['PUT'])
@require_auth
def update_post(post_id, user_id):
    """Update draft/scheduled post"""
    data = request.json
    try:
        post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        if post.status not in ['draft', 'scheduled']:
            return jsonify({'error': 'Can only edit draft or scheduled posts'}), 400

        post.content = data.get('content', post.content)
        post.media_urls = data.get('media_urls', post.media_urls)
        post.hashtags = data.get('hashtags', post.hashtags)
        post.link_url = data.get('link_url', post.link_url)

        if data.get('scheduled_at'):
            post.scheduled_at = datetime.fromisoformat(data['scheduled_at'])

        db.session.commit()
        cache_invalidate(f'posts:{user_id}')

        return jsonify({'post': post.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/posts/<int:post_id>/retry', methods=['POST'])
@require_auth
def retry_post(post_id, user_id):
    """Retry publishing failed post"""
    try:
        post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        if post.status != 'failed':
            return jsonify({'error': 'Only failed posts can be retried'}), 400

        post.status = 'scheduled'
        post.scheduled_at = datetime.utcnow()
        post.retry_count = 0
        post.error_message = None

        db.session.commit()
        cache_invalidate(f'posts:{user_id}')

        return jsonify({'post': post.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/posts/<int:post_id>/metrics', methods=['GET'])
@require_auth
def get_post_metrics(post_id, user_id):
    """Get performance metrics for published post"""
    try:
        post = SNSPost.query.filter_by(id=post_id, user_id=user_id).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        return jsonify({
            'post_id': post.id,
            'platform': post.platform,
            'likes': post.likes_count,
            'comments': post.comments_count,
            'views': post.views_count,
            'reach': post.reach,
            'published_at': post.published_at.isoformat() if post.published_at else None,
            'external_post_id': post.external_post_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ ANALYTICS (3 endpoints) ============

@sns_bp.route('/analytics', methods=['GET'])
@require_auth
def get_analytics(user_id):
    """Get aggregated analytics across all accounts"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        # Default to last 7 days
        if not end_date:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.fromisoformat(end_date).date()

        if not start_date:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.fromisoformat(start_date).date()

        # Get all accounts for user
        accounts = SNSAccount.query.filter_by(user_id=user_id).all()
        account_ids = [acc.id for acc in accounts]

        if not account_ids:
            return jsonify({
                'followers': 0,
                'engagement': 0,
                'reach': 0,
                'impressions': 0,
                'by_platform': {}
            }), 200

        # Aggregate analytics
        analytics = SNSAnalytics.query.filter(
            SNSAnalytics.account_id.in_(account_ids),
            SNSAnalytics.date >= start_date,
            SNSAnalytics.date <= end_date
        ).all()

        total_followers = sum(a.followers for a in analytics) or 0
        total_engagement = sum(a.total_engagement for a in analytics) or 0
        total_reach = sum(a.total_reach for a in analytics) or 0
        total_impressions = sum(a.total_impressions for a in analytics) or 0

        # By platform
        by_platform = {}
        for account in accounts:
            acc_analytics = [a for a in analytics if a.account_id == account.id]
            by_platform[account.platform] = {
                'followers': sum(a.followers for a in acc_analytics) or 0,
                'engagement': sum(a.total_engagement for a in acc_analytics) or 0,
                'reach': sum(a.total_reach for a in acc_analytics) or 0,
                'impressions': sum(a.total_impressions for a in acc_analytics) or 0,
            }

        return jsonify({
            'period': f'{start_date} to {end_date}',
            'followers': total_followers,
            'engagement': total_engagement,
            'reach': total_reach,
            'impressions': total_impressions,
            'by_platform': by_platform
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/analytics/accounts/<int:account_id>', methods=['GET'])
@require_auth
def get_account_analytics(account_id, user_id):
    """Get analytics for specific account"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        account = SNSAccount.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Default to last 7 days
        if not end_date:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.fromisoformat(end_date).date()

        if not start_date:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.fromisoformat(start_date).date()

        # Cache key
        cache_key = f'analytics:{account_id}:{start_date}:{end_date}'
        cached = cache_get(cache_key)
        if cached:
            return jsonify(cached), 200

        analytics = SNSAnalytics.query.filter(
            SNSAnalytics.account_id == account_id,
            SNSAnalytics.date >= start_date,
            SNSAnalytics.date <= end_date
        ).order_by(SNSAnalytics.date).all()

        data = {
            'account': account.to_dict(),
            'period': f'{start_date} to {end_date}',
            'total_followers': sum(a.followers for a in analytics) or 0,
            'total_engagement': sum(a.total_engagement for a in analytics) or 0,
            'total_reach': sum(a.total_reach for a in analytics) or 0,
            'total_impressions': sum(a.total_impressions for a in analytics) or 0,
            'daily': [a.to_dict() for a in analytics]
        }

        # Cache for 15 minutes
        cache_set(cache_key, data, ttl=900)

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/analytics/optimal-time/<int:account_id>', methods=['GET'])
@require_auth
def get_optimal_posting_time(account_id, user_id):
    """Get optimal posting time for account based on past engagement"""
    try:
        account = SNSAccount.query.filter_by(id=account_id, user_id=user_id).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Get posts from last 30 days
        posts = SNSPost.query.filter(
            SNSPost.account_id == account_id,
            SNSPost.status == 'published',
            SNSPost.published_at >= datetime.utcnow() - timedelta(days=30)
        ).all()

        if not posts:
            # Return default optimal times if no data
            return jsonify({
                'account_id': account_id,
                'optimal_time': '09:00',  # 9 AM default
                'confidence': 'low',
                'message': 'Not enough data - using default time'
            }), 200

        # Calculate average engagement by hour
        engagement_by_hour = {}
        for post in posts:
            if post.published_at:
                hour = post.published_at.hour
                engagement_by_hour[hour] = engagement_by_hour.get(hour, 0) + (post.likes_count + post.comments_count)

        if engagement_by_hour:
            optimal_hour = max(engagement_by_hour, key=engagement_by_hour.get)
            return jsonify({
                'account_id': account_id,
                'optimal_hour': optimal_hour,
                'optimal_time': f'{optimal_hour:02d}:00',
                'confidence': 'medium',
                'posts_analyzed': len(posts)
            }), 200

        return jsonify({'optimal_time': '09:00', 'confidence': 'low'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ MEDIA (2 endpoints) ============

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@sns_bp.route('/media/upload', methods=['POST'])
@require_auth
def upload_media(user_id):
    """Upload media file for SNS post"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {ALLOWED_EXTENSIONS}'}), 400

        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Max: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)

        # Return media URL
        media_url = f'/uploads/sns/{filename}'

        return jsonify({
            'filename': filename,
            'url': media_url,
            'size': file_size,
            'type': mimetypes.guess_type(filename)[0]
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/media', methods=['GET'])
@require_auth
def list_media(user_id):
    """List user's uploaded media files"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({'media': []}), 200

        files = os.listdir(UPLOAD_FOLDER)
        media = []

        for filename in sorted(files, reverse=True)[:100]:  # Last 100 files
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                media.append({
                    'filename': filename,
                    'url': f'/uploads/sns/{filename}',
                    'size': os.path.getsize(filepath),
                    'type': mimetypes.guess_type(filename)[0],
                    'uploaded_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })

        return jsonify({'media': media, 'count': len(media)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ TEMPLATES (4 endpoints) ============

@sns_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates(user_id):
    """Get user's templates + system templates"""
    platform = request.args.get('platform')

    try:
        # Get user's custom templates + system templates
        query = SNSTemplate.query.filter(
            (SNSTemplate.user_id == user_id) | (SNSTemplate.user_id == None)
        )

        if platform:
            query = query.filter((SNSTemplate.platform == platform) | (SNSTemplate.platform == 'all'))

        templates = query.all()
        templates_data = [t.to_dict() for t in templates]

        return jsonify({'templates': templates_data, 'count': len(templates_data)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/templates', methods=['POST'])
@require_auth
def create_template(user_id):
    """Create custom template"""
    data = request.json
    try:
        template = SNSTemplate(
            user_id=user_id,
            name=data.get('name'),
            platform=data.get('platform', 'all'),
            content_template=data.get('content_template'),
            hashtag_template=data.get('hashtag_template'),
            category=data.get('category')
        )
        db.session.add(template)
        db.session.commit()

        cache_invalidate(f'templates:{user_id}')

        return jsonify({'template': template.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/templates/<int:template_id>', methods=['PUT'])
@require_auth
def update_template(template_id, user_id):
    """Update custom template"""
    data = request.json
    try:
        template = SNSTemplate.query.filter_by(id=template_id, user_id=user_id).first()
        if not template:
            return jsonify({'error': 'Template not found'}), 404

        template.name = data.get('name', template.name)
        template.content_template = data.get('content_template', template.content_template)
        template.hashtag_template = data.get('hashtag_template', template.hashtag_template)
        template.category = data.get('category', template.category)

        db.session.commit()
        cache_invalidate(f'templates:{user_id}')

        return jsonify({'template': template.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id, user_id):
    """Delete custom template"""
    try:
        template = SNSTemplate.query.filter_by(id=template_id, user_id=user_id).first()
        if not template:
            return jsonify({'error': 'Template not found'}), 404

        db.session.delete(template)
        db.session.commit()

        cache_invalidate(f'templates:{user_id}')

        return jsonify({'message': 'Template deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ INBOX (3 endpoints) ============

@sns_bp.route('/inbox', methods=['GET'])
@require_auth
def get_inbox(user_id):
    """Get unified SNS inbox"""
    status = request.args.get('status')  # unread, read, all
    platform = request.args.get('platform')
    limit = int(request.args.get('limit', 50))

    try:
        query = SNSInboxMessage.query.filter_by(user_id=user_id)

        if status and status != 'all':
            query = query.filter_by(status=status)
        if platform:
            query = query.filter_by(account_id=SNSAccount.query.filter_by(platform=platform).with_entities(SNSAccount.id))

        messages = query.order_by(SNSInboxMessage.created_at.desc()).limit(limit).all()
        messages_data = [msg.to_dict() for msg in messages]

        unread_count = SNSInboxMessage.query.filter_by(user_id=user_id, status='unread').count()

        return jsonify({
            'messages': messages_data,
            'count': len(messages_data),
            'unread_count': unread_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/inbox/<int:message_id>/reply', methods=['POST'])
@require_auth
def reply_to_message(message_id, user_id):
    """Reply to inbox message"""
    data = request.json
    try:
        message = SNSInboxMessage.query.filter_by(id=message_id, user_id=user_id).first()
        if not message:
            return jsonify({'error': 'Message not found'}), 404

        account = SNSAccount.query.get(message.account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Publish reply via platform client
        client = get_client(account.platform, account.access_token)
        reply_result = client.reply_to_comment(message.external_id or message.id, data.get('reply_text'))

        if reply_result.get('success'):
            message.status = 'replied'
            db.session.commit()

        return jsonify({'reply': reply_result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/inbox/<int:message_id>/read', methods=['PUT'])
@require_auth
def mark_message_read(message_id, user_id):
    """Mark inbox message as read"""
    try:
        message = SNSInboxMessage.query.filter_by(id=message_id, user_id=user_id).first()
        if not message:
            return jsonify({'error': 'Message not found'}), 404

        message.status = 'read'
        db.session.commit()

        return jsonify({'message': message.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ CALENDAR (1 endpoint) ============

@sns_bp.route('/calendar', methods=['GET'])
@require_auth
def get_calendar(user_id):
    """Get scheduled posts for month view"""
    year = int(request.args.get('year', datetime.utcnow().year))
    month = int(request.args.get('month', datetime.utcnow().month))

    try:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        posts = SNSPost.query.filter(
            SNSPost.user_id == user_id,
            SNSPost.status == 'scheduled',
            SNSPost.scheduled_at >= start_date,
            SNSPost.scheduled_at < end_date
        ).all()

        # Group by day
        calendar = {}
        for post in posts:
            day = post.scheduled_at.day
            if day not in calendar:
                calendar[day] = []
            calendar[day].append(post.to_dict())

        return jsonify({
            'year': year,
            'month': month,
            'calendar': calendar,
            'total_scheduled': len(posts)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ CAMPAIGNS (3 endpoints) ============

@sns_bp.route('/campaigns', methods=['GET'])
@require_auth
def get_campaigns(user_id):
    """List all campaigns"""
    try:
        campaigns = SNSCampaign.query.filter_by(user_id=user_id).order_by(SNSCampaign.created_at.desc()).all()
        campaigns_data = [c.to_dict() for c in campaigns]

        return jsonify({'campaigns': campaigns_data, 'count': len(campaigns_data)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/campaigns', methods=['POST'])
@require_auth
def create_campaign(user_id):
    """Create campaign"""
    data = request.json
    try:
        campaign = SNSCampaign(
            user_id=user_id,
            name=data.get('name'),
            description=data.get('description'),
            target_platforms=data.get('target_platforms', []),
            status=data.get('status', 'active'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else datetime.utcnow(),
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(campaign)
        db.session.commit()

        return jsonify({'campaign': campaign.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/campaigns/<int:campaign_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_campaign(campaign_id, user_id):
    """Get, update, or delete campaign"""
    campaign = SNSCampaign.query.filter_by(id=campaign_id, user_id=user_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    try:
        if request.method == 'GET':
            return jsonify({'campaign': campaign.to_dict()}), 200

        elif request.method == 'PUT':
            data = request.json
            campaign.name = data.get('name', campaign.name)
            campaign.description = data.get('description', campaign.description)
            campaign.target_platforms = data.get('target_platforms', campaign.target_platforms)
            campaign.status = data.get('status', campaign.status)
            db.session.commit()
            return jsonify({'campaign': campaign.to_dict()}), 200

        elif request.method == 'DELETE':
            db.session.delete(campaign)
            db.session.commit()
            return jsonify({'message': 'Campaign deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ AI (3 endpoints) ============

@sns_bp.route('/ai/generate', methods=['POST'])
@require_auth
def ai_generate_content(user_id):
    """Generate content using Claude API"""
    data = request.json
    topic = data.get('topic', '')
    platform = data.get('platform', 'instagram')

    if not topic or len(topic) > 500:
        return jsonify({'error': 'Invalid topic (max 500 chars)'}), 400

    try:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            # Return template-based fallback
            return jsonify({
                'content': f'📱 Exciting news about {topic}! Check out what we have in store...',
                'hashtags': ['#newpost', '#trending', f'#{platform}'],
                'source': 'template',
                'message': 'API key not configured - using template'
            }), 200

        from anthropic import Anthropic
        client = Anthropic()

        system_prompt = f"""You are an expert {platform} content creator.
Generate engaging social media content for {platform} about: {topic}
- Keep it concise and platform-appropriate
- Maximum character limit for {platform}: refer to platform_char_limits
- Include relevant emojis
- Make it compelling and shareable"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Create a {platform} post about: {topic}"}
            ]
        )

        content = message.content[0].text

        return jsonify({
            'content': content,
            'hashtags': ['#newpost', f'#{platform}', '#trending'],
            'source': 'claude_ai'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'source': 'error'}), 500


@sns_bp.route('/ai/hashtags', methods=['POST'])
@require_auth
def ai_generate_hashtags(user_id):
    """Generate relevant hashtags"""
    data = request.json
    topic = data.get('topic', '')
    platform = data.get('platform', 'instagram')

    try:
        # Simple fallback hashtag generation
        words = topic.lower().split()[:3]
        hashtags = [f'#{word}' for word in words if len(word) > 2]
        hashtags += ['#trending', f'#{platform}', '#newpost']

        return jsonify({'hashtags': hashtags[:10]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/ai/optimize', methods=['POST'])
@require_auth
def ai_optimize_content(user_id):
    """Optimize content for specific platform"""
    data = request.json
    content = data.get('content', '')
    platform = data.get('platform', 'instagram')

    if not content:
        return jsonify({'error': 'Content required'}), 400

    try:
        # Platform-specific character limits
        platform_limits = {
            'instagram': 2200,
            'twitter': 280,
            'linkedin': 3000,
            'tiktok': 2200,
            'facebook': 63206,
            'pinterest': 500,
            'threads': 500,
            'youtube': 5000,
            'youtube_shorts': 2200
        }

        limit = platform_limits.get(platform, 2200)

        # Truncate if necessary
        if len(content) > limit:
            optimized = content[:limit-3] + '...'
        else:
            optimized = content

        return jsonify({
            'optimized_content': optimized,
            'platform': platform,
            'character_count': len(optimized),
            'character_limit': limit,
            'message': 'Content optimized for platform'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ SETTINGS (2 endpoints) ============

@sns_bp.route('/settings', methods=['GET'])
@require_auth
def get_settings(user_id):
    """Get user SNS settings"""
    try:
        settings = SNSSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            # Create default settings
            settings = SNSSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()

        return jsonify({'settings': settings.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sns_bp.route('/settings', methods=['PUT'])
@require_auth
def update_settings(user_id):
    """Update user SNS settings"""
    data = request.json
    try:
        settings = SNSSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = SNSSettings(user_id=user_id)

        settings.auto_optimal_time = data.get('auto_optimal_time', settings.auto_optimal_time)
        settings.engagement_notifications = data.get('engagement_notifications', settings.engagement_notifications)
        settings.auto_reply_enabled = data.get('auto_reply_enabled', settings.auto_reply_enabled)
        settings.banned_keywords = data.get('banned_keywords', settings.banned_keywords)

        db.session.add(settings)
        db.session.commit()

        return jsonify({'settings': settings.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
