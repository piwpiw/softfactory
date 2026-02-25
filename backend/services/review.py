"""Review Campaign Service - Influencer & Reviewer Campaigns"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from sqlalchemy import and_
from ..models import db, Campaign, CampaignApplication
from ..auth import require_auth, require_subscription

review_bp = Blueprint('review', __name__, url_prefix='/api/review')


@review_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """List campaigns with filters"""
    query = Campaign.query.filter_by(status='active')

    # Filters
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    if category:
        query = query.filter_by(category=category)

    # Filter by deadline (not expired)
    query = query.filter(Campaign.deadline >= datetime.utcnow())

    result = query.order_by(Campaign.created_at.desc()).paginate(page=page, per_page=per_page)

    campaigns_data = []
    for campaign in result.items:
        app_count = CampaignApplication.query.filter_by(campaign_id=campaign.id).count()
        campaigns_data.append({
            'id': campaign.id,
            'title': campaign.title,
            'product_name': campaign.product_name,
            'category': campaign.category,
            'reward_type': campaign.reward_type,
            'reward_value': campaign.reward_value,
            'max_reviewers': campaign.max_reviewers,
            'applications_count': app_count,
            'deadline': campaign.deadline.isoformat(),
            'created_at': campaign.created_at.isoformat(),
        })

    return jsonify({
        'campaigns': campaigns_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@review_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign_detail(campaign_id):
    """Get campaign details"""
    campaign = Campaign.query.get(campaign_id)

    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    app_count = CampaignApplication.query.filter_by(campaign_id=campaign.id).count()

    return jsonify({
        'id': campaign.id,
        'title': campaign.title,
        'description': campaign.description,
        'product_name': campaign.product_name,
        'category': campaign.category,
        'reward_type': campaign.reward_type,
        'reward_value': campaign.reward_value,
        'max_reviewers': campaign.max_reviewers,
        'applications_count': app_count,
        'spots_available': max(0, campaign.max_reviewers - app_count),
        'deadline': campaign.deadline.isoformat(),
        'status': campaign.status,
        'created_at': campaign.created_at.isoformat(),
    }), 200


@review_bp.route('/campaigns', methods=['POST'])
@require_auth
@require_subscription('review')
def create_campaign():
    """Create campaign (campaign creator)"""
    data = request.get_json()

    required = ['title', 'product_name', 'category', 'reward_type', 'reward_value', 'max_reviewers', 'deadline']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        deadline = datetime.fromisoformat(data['deadline'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid deadline format'}), 400

    campaign = Campaign(
        creator_id=g.user_id,
        title=data['title'],
        product_name=data['product_name'],
        description=data.get('description', ''),
        category=data['category'],
        reward_type=data['reward_type'],
        reward_value=data['reward_value'],
        max_reviewers=int(data['max_reviewers']),
        deadline=deadline,
        status='active'
    )

    db.session.add(campaign)
    db.session.commit()

    return jsonify({
        'id': campaign.id,
        'message': 'Campaign created successfully'
    }), 201


@review_bp.route('/campaigns/<int:campaign_id>/apply', methods=['POST'])
@require_auth
def apply_campaign(campaign_id):
    """Apply to campaign (reviewer)"""
    campaign = Campaign.query.get(campaign_id)

    if not campaign or campaign.status != 'active':
        return jsonify({'error': 'Campaign not found or closed'}), 404

    if campaign.deadline < datetime.utcnow():
        return jsonify({'error': 'Campaign deadline passed'}), 400

    # Check if already applied
    existing = CampaignApplication.query.filter_by(
        campaign_id=campaign_id,
        user_id=g.user_id
    ).first()

    if existing:
        return jsonify({'error': 'Already applied to this campaign'}), 400

    # Check if spots available
    app_count = CampaignApplication.query.filter_by(campaign_id=campaign_id).count()
    if app_count >= campaign.max_reviewers:
        return jsonify({'error': 'Campaign is full'}), 400

    data = request.get_json()

    required = ['message']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    application = CampaignApplication(
        campaign_id=campaign_id,
        user_id=g.user_id,
        message=data['message'],
        sns_link=data.get('sns_link'),
        follower_count=data.get('follower_count', 0),
        status='pending'
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({
        'id': application.id,
        'message': 'Application submitted successfully'
    }), 201


@review_bp.route('/my-campaigns', methods=['GET'])
@require_auth
@require_subscription('review')
def get_my_campaigns():
    """Get user's created campaigns"""
    campaigns = Campaign.query.filter_by(creator_id=g.user_id).all()

    campaigns_data = []
    for campaign in campaigns:
        app_count = CampaignApplication.query.filter_by(campaign_id=campaign.id).count()
        campaigns_data.append({
            'id': campaign.id,
            'title': campaign.title,
            'product_name': campaign.product_name,
            'category': campaign.category,
            'max_reviewers': campaign.max_reviewers,
            'applications_count': app_count,
            'deadline': campaign.deadline.isoformat(),
            'status': campaign.status,
        })

    return jsonify(campaigns_data), 200


@review_bp.route('/my-applications', methods=['GET'])
@require_auth
def get_my_applications():
    """Get user's campaign applications"""
    applications = CampaignApplication.query.filter_by(user_id=g.user_id).all()

    apps_data = []
    for app in applications:
        apps_data.append({
            'id': app.id,
            'campaign_title': app.campaign.title,
            'product_name': app.campaign.product_name,
            'reward_value': app.campaign.reward_value,
            'status': app.status,
            'applied_at': app.created_at.isoformat(),
        })

    return jsonify(apps_data), 200


@review_bp.route('/campaigns/<int:campaign_id>/applications', methods=['GET'])
@require_auth
@require_subscription('review')
def get_campaign_applications(campaign_id):
    """Get applications for a campaign (creator only)"""
    campaign = Campaign.query.get(campaign_id)

    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    if campaign.creator_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    applications = CampaignApplication.query.filter_by(campaign_id=campaign_id).all()

    apps_data = []
    for app in applications:
        apps_data.append({
            'id': app.id,
            'user_name': app.user.name,
            'user_email': app.user.email,
            'message': app.message,
            'sns_link': app.sns_link,
            'follower_count': app.follower_count,
            'status': app.status,
        })

    return jsonify(apps_data), 200


@review_bp.route('/applications/<int:application_id>', methods=['PUT'])
@require_auth
@require_subscription('review')
def update_application(application_id):
    """Approve or reject application"""
    application = CampaignApplication.query.get(application_id)

    if not application:
        return jsonify({'error': 'Application not found'}), 404

    if application.campaign.creator_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json()
    if 'status' in data:
        if data['status'] not in ['pending', 'approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400

        application.status = data['status']
        db.session.commit()

    return jsonify({'message': 'Application updated'}), 200
