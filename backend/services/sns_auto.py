"""SNS Auto Service - Social Media Automation"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..models import db, SNSAccount, SNSPost
from ..auth import require_auth, require_subscription

sns_bp = Blueprint('sns', __name__, url_prefix='/api/sns')

# Template types
TEMPLATES = {
    'card_news': {'name': 'Card News', 'platforms': ['instagram', 'tiktok']},
    'blog_post': {'name': 'Blog Post', 'platforms': ['blog']},
    'reel': {'name': 'Reel', 'platforms': ['instagram']},
    'shorts': {'name': 'YouTube Shorts', 'platforms': ['youtube']},
    'carousel': {'name': 'Carousel', 'platforms': ['instagram']},
}


@sns_bp.route('/accounts', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_accounts():
    """Get user's SNS accounts"""
    accounts = SNSAccount.query.filter_by(user_id=g.user_id).all()

    accounts_data = []
    for account in accounts:
        post_count = SNSPost.query.filter_by(account_id=account.id).count()
        accounts_data.append({
            'id': account.id,
            'platform': account.platform,
            'account_name': account.account_name,
            'is_active': account.is_active,
            'post_count': post_count,
            'created_at': account.created_at.isoformat(),
        })

    return jsonify(accounts_data), 200


@sns_bp.route('/accounts', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_account():
    """Link SNS account"""
    data = request.get_json()

    required = ['platform', 'account_name']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check for duplicates
    existing = SNSAccount.query.filter_by(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=data['account_name']
    ).first()

    if existing:
        return jsonify({'error': 'Account already linked'}), 400

    account = SNSAccount(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=data['account_name'],
        is_active=True
    )

    db.session.add(account)
    db.session.commit()

    return jsonify({
        'id': account.id,
        'message': 'Account linked successfully'
    }), 201


@sns_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_account(account_id):
    """Unlink SNS account"""
    account = SNSAccount.query.get(account_id)

    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    db.session.delete(account)
    db.session.commit()

    return jsonify({'message': 'Account unlinked'}), 200


@sns_bp.route('/posts', methods=['GET'])
@require_auth
@require_subscription('sns-auto')
def get_posts():
    """Get user's SNS posts"""
    account_id = request.args.get('account_id', type=int)
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)

    query = SNSPost.query.filter_by(user_id=g.user_id)

    if account_id:
        query = query.filter_by(account_id=account_id)

    if status:
        query = query.filter_by(status=status)

    result = query.order_by(SNSPost.created_at.desc()).paginate(page=page, per_page=20)

    posts_data = []
    for post in result.items:
        posts_data.append({
            'id': post.id,
            'account_name': post.account.account_name,
            'platform': post.platform,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'status': post.status,
            'template_type': post.template_type,
            'scheduled_at': post.scheduled_at.isoformat() if post.scheduled_at else None,
            'created_at': post.created_at.isoformat(),
        })

    return jsonify({
        'posts': posts_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@sns_bp.route('/posts', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def create_post():
    """Create SNS post"""
    data = request.get_json()

    required = ['account_id', 'content', 'template_type']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    account = SNSAccount.query.get(data['account_id'])
    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    post = SNSPost(
        user_id=g.user_id,
        account_id=account.id,
        content=data['content'],
        platform=account.platform,
        template_type=data['template_type'],
        status='draft',
        scheduled_at=None
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({
        'id': post.id,
        'message': 'Post created successfully'
    }), 201


@sns_bp.route('/posts/<int:post_id>/publish', methods=['POST'])
@require_auth
@require_subscription('sns-auto')
def publish_post(post_id):
    """Publish or schedule post"""
    post = SNSPost.query.get(post_id)

    if not post or post.user_id != g.user_id:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    scheduled_at = data.get('scheduled_at')

    if scheduled_at:
        try:
            post.scheduled_at = datetime.fromisoformat(scheduled_at)
            post.status = 'scheduled'
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid scheduled_at format'}), 400
    else:
        # Publish immediately (in dev mode)
        post.status = 'published'

    db.session.commit()

    return jsonify({
        'id': post.id,
        'status': post.status,
        'message': 'Post ' + ('scheduled' if scheduled_at else 'published')
    }), 200


@sns_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
@require_subscription('sns-auto')
def delete_post(post_id):
    """Delete post"""
    post = SNSPost.query.get(post_id)

    if not post or post.user_id != g.user_id:
        return jsonify({'error': 'Post not found'}), 404

    if post.status == 'published':
        return jsonify({'error': 'Cannot delete published posts'}), 400

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post deleted'}), 200


@sns_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    """Get available templates"""
    return jsonify(TEMPLATES), 200
