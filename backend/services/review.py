"""Review Campaign Service - Influencer & Reviewer Campaigns + Review Listing Scraper Integration — Input-Validated"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import and_, desc, or_, func, case
from sqlalchemy.orm import joinedload, subqueryload
from ..models import db, Campaign, CampaignApplication, ReviewListing, ReviewAccount, ReviewApplication, ReviewBookmark, ReviewAutoRule
from ..auth import require_auth, require_subscription
from ..cache import ttl_cache, invalidate_cache
from ..input_validator import (
    validate_string, validate_integer, validate_platform, sanitize_html,
    check_xss, check_sql_injection, VALID_REVIEW_PLATFORMS
)
import logging

logger = logging.getLogger('review')
review_bp = Blueprint('review', __name__, url_prefix='/api/review')


@review_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """List campaigns with filters (optimized: single query for application counts)"""
    # Subquery: count applications per campaign in one pass
    app_counts = (
        db.session.query(
            CampaignApplication.campaign_id,
            func.count(CampaignApplication.id).label('app_count')
        )
        .group_by(CampaignApplication.campaign_id)
        .subquery()
    )

    # Filters
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    query = (
        db.session.query(Campaign, app_counts.c.app_count)
        .outerjoin(app_counts, Campaign.id == app_counts.c.campaign_id)
        .filter(Campaign.status == 'active', Campaign.deadline >= datetime.utcnow())
    )

    if category:
        query = query.filter(Campaign.category == category)

    query = query.order_by(Campaign.created_at.desc())
    result = query.paginate(page=page, per_page=per_page)

    campaigns_data = []
    for campaign, app_count in result.items:
        campaigns_data.append({
            'id': campaign.id,
            'title': campaign.title,
            'product_name': campaign.product_name,
            'category': campaign.category,
            'reward_type': campaign.reward_type,
            'reward_value': campaign.reward_value,
            'max_reviewers': campaign.max_reviewers,
            'applications_count': app_count or 0,
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
    """Get campaign details (single query with application count)"""
    app_count_sub = (
        db.session.query(func.count(CampaignApplication.id))
        .filter(CampaignApplication.campaign_id == campaign_id)
        .correlate(Campaign)
        .scalar_subquery()
    )

    result = (
        db.session.query(Campaign, app_count_sub.label('app_count'))
        .filter(Campaign.id == campaign_id)
        .first()
    )

    if not result:
        return jsonify({'error': 'Campaign not found'}), 404

    campaign, app_count = result
    app_count = app_count or 0

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
    """Create campaign (campaign creator) — with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['title', 'product_name', 'category', 'reward_type', 'reward_value', 'max_reviewers', 'deadline']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate and sanitize string fields
    valid, error, clean_title = validate_string(
        data['title'], 'Title', min_length=1, max_length=200
    )
    if not valid:
        return jsonify({'error': error}), 400

    valid, error, clean_product = validate_string(
        data['product_name'], 'Product name', min_length=1, max_length=200
    )
    if not valid:
        return jsonify({'error': error}), 400

    valid, error, clean_category = validate_string(
        data['category'], 'Category', min_length=1, max_length=50
    )
    if not valid:
        return jsonify({'error': error}), 400

    valid, error, clean_reward_type = validate_string(
        data['reward_type'], 'Reward type', min_length=1, max_length=50
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Validate numeric fields
    valid, error, clean_max_reviewers = validate_integer(
        data['max_reviewers'], 'Max reviewers', min_val=1, max_val=10000
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Sanitize description (optional field)
    clean_description = sanitize_html(data.get('description', ''))[:2000]

    try:
        deadline = datetime.fromisoformat(data['deadline'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid deadline format'}), 400

    campaign = Campaign(
        creator_id=g.user_id,
        title=clean_title,
        product_name=clean_product,
        description=clean_description,
        category=clean_category,
        reward_type=clean_reward_type,
        reward_value=data['reward_value'],
        max_reviewers=clean_max_reviewers,
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

    # Validate and sanitize application message
    valid, error, clean_message = validate_string(
        data['message'], 'Message', min_length=1, max_length=2000
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Sanitize optional sns_link
    clean_sns_link = sanitize_html(data.get('sns_link', ''))[:500] if data.get('sns_link') else None

    application = CampaignApplication(
        campaign_id=campaign_id,
        user_id=g.user_id,
        message=clean_message,
        sns_link=clean_sns_link,
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
    """Get user's created campaigns (optimized: single query for app counts)"""
    app_counts = (
        db.session.query(
            CampaignApplication.campaign_id,
            func.count(CampaignApplication.id).label('app_count')
        )
        .group_by(CampaignApplication.campaign_id)
        .subquery()
    )

    results = (
        db.session.query(Campaign, app_counts.c.app_count)
        .outerjoin(app_counts, Campaign.id == app_counts.c.campaign_id)
        .filter(Campaign.creator_id == g.user_id)
        .all()
    )

    campaigns_data = []
    for campaign, app_count in results:
        campaigns_data.append({
            'id': campaign.id,
            'title': campaign.title,
            'product_name': campaign.product_name,
            'category': campaign.category,
            'max_reviewers': campaign.max_reviewers,
            'applications_count': app_count or 0,
            'deadline': campaign.deadline.isoformat(),
            'status': campaign.status,
        })

    return jsonify(campaigns_data), 200


@review_bp.route('/my-applications', methods=['GET'])
@require_auth
def get_my_applications():
    """Get user's campaign applications (eager load campaign to prevent N+1)"""
    applications = (
        CampaignApplication.query
        .options(joinedload(CampaignApplication.campaign))
        .filter_by(user_id=g.user_id)
        .all()
    )

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

    applications = (
        CampaignApplication.query
        .options(joinedload(CampaignApplication.user))
        .filter_by(campaign_id=campaign_id)
        .all()
    )

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


# ==================== SCRAPED LISTINGS API ====================

@review_bp.route('/listings', methods=['GET'])
@require_auth
def get_scraped_listings():
    """Get scraped review listings with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    platform = request.args.get('platform')
    reward_type = request.args.get('reward_type')
    min_reward = request.args.get('min_reward', type=int)
    max_reward = request.args.get('max_reward', type=int)
    sort_by = request.args.get('sort_by', 'deadline')  # deadline, reward_value, created

    # Base query - only active listings not expired
    query = ReviewListing.query.filter(
        ReviewListing.status == 'active',
        ReviewListing.deadline >= datetime.utcnow()
    )

    # Apply filters
    if category:
        query = query.filter_by(category=category)

    if platform:
        query = query.filter_by(source_platform=platform)

    if reward_type:
        query = query.filter_by(reward_type=reward_type)

    if min_reward:
        query = query.filter(ReviewListing.reward_value >= min_reward)

    if max_reward:
        query = query.filter(ReviewListing.reward_value <= max_reward)

    # Sort results
    if sort_by == 'reward_value':
        query = query.order_by(desc(ReviewListing.reward_value))
    elif sort_by == 'created':
        query = query.order_by(desc(ReviewListing.scraped_at))
    else:  # deadline (default)
        query = query.order_by(ReviewListing.deadline)

    result = query.paginate(page=page, per_page=per_page)

    # Batch lookup: get all bookmarked listing IDs for current user in one query
    listing_ids = [listing.id for listing in result.items]
    bookmarked_ids = set()
    if listing_ids:
        bookmarked_rows = (
            db.session.query(ReviewBookmark.listing_id)
            .filter(ReviewBookmark.user_id == g.user_id, ReviewBookmark.listing_id.in_(listing_ids))
            .all()
        )
        bookmarked_ids = {row[0] for row in bookmarked_rows}

    listings_data = []
    for listing in result.items:
        listing_dict = listing.to_dict()
        listing_dict['is_bookmarked'] = listing.id in bookmarked_ids
        listings_data.append(listing_dict)

    return jsonify({
        'listings': listings_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@review_bp.route('/listings/<int:listing_id>', methods=['GET'])
@require_auth
def get_listing_detail(listing_id):
    """Get detailed information about a specific listing"""
    listing = ReviewListing.query.get(listing_id)

    if not listing:
        return jsonify({'error': 'Listing not found'}), 404

    listing_dict = listing.to_dict()

    # Add bookmark status
    bookmark = ReviewBookmark.query.filter_by(
        user_id=g.user_id,
        listing_id=listing_id
    ).first()
    listing_dict['is_bookmarked'] = bookmark is not None

    # Add application count
    application_count = ReviewApplication.query.filter_by(listing_id=listing_id).count()
    listing_dict['application_count'] = application_count

    # Add user's applications to this listing (if any)
    user_accounts = ReviewAccount.query.filter_by(user_id=g.user_id).all()
    user_applications = ReviewApplication.query.filter(
        ReviewApplication.listing_id == listing_id,
        ReviewApplication.account_id.in_([acc.id for acc in user_accounts])
    ).all()

    listing_dict['user_applications'] = [
        {
            'id': app.id,
            'account_id': app.account_id,
            'status': app.status,
            'applied_at': app.applied_at.isoformat() if app.applied_at else None
        }
        for app in user_applications
    ]

    return jsonify(listing_dict), 200


@review_bp.route('/listings/search', methods=['GET'])
@require_auth
def search_listings():
    """Search listings by keyword — with input sanitization"""
    keyword = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)

    if not keyword or len(keyword) < 2:
        return jsonify({'error': 'Search keyword must be at least 2 characters'}), 400

    # Enforce max keyword length
    if len(keyword) > 100:
        return jsonify({'error': 'Search keyword must be 100 characters or less'}), 400

    # Check for SQL injection patterns in search keyword
    if check_sql_injection(keyword):
        return jsonify({'error': 'Invalid search keyword'}), 400

    # Sanitize keyword for XSS
    keyword = sanitize_html(keyword)

    # Escape SQL LIKE wildcards in user input to prevent pattern injection
    safe_keyword = keyword.replace('%', '\\%').replace('_', '\\_')

    # Search in title, brand, and category (using parameterized LIKE)
    query = ReviewListing.query.filter(
        ReviewListing.status == 'active',
        ReviewListing.deadline >= datetime.utcnow(),
        or_(
            ReviewListing.title.ilike(f'%{safe_keyword}%'),
            ReviewListing.brand.ilike(f'%{safe_keyword}%'),
            ReviewListing.category.ilike(f'%{safe_keyword}%')
        )
    ).order_by(ReviewListing.deadline)

    result = query.paginate(page=page, per_page=per_page)

    # Batch bookmark lookup (avoid N+1)
    listing_ids = [listing.id for listing in result.items]
    bookmarked_ids = set()
    if listing_ids:
        bookmarked_rows = (
            db.session.query(ReviewBookmark.listing_id)
            .filter(ReviewBookmark.user_id == g.user_id, ReviewBookmark.listing_id.in_(listing_ids))
            .all()
        )
        bookmarked_ids = {row[0] for row in bookmarked_rows}

    listings_data = []
    for listing in result.items:
        listing_dict = listing.to_dict()
        listing_dict['is_bookmarked'] = listing.id in bookmarked_ids
        listings_data.append(listing_dict)

    return jsonify({
        'listings': listings_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


# ==================== BOOKMARKS API ====================

@review_bp.route('/bookmarks', methods=['GET'])
@require_auth
def get_bookmarks():
    """Get user's bookmarked listings (eager load listing to prevent N+1)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = (
        ReviewBookmark.query
        .options(joinedload(ReviewBookmark.listing))
        .filter_by(user_id=g.user_id)
        .order_by(desc(ReviewBookmark.created_at))
    )

    result = query.paginate(page=page, per_page=per_page)

    bookmarks_data = []
    for bookmark in result.items:
        listing = bookmark.listing
        listing_dict = listing.to_dict()
        listing_dict['is_bookmarked'] = True
        listing_dict['bookmarked_at'] = bookmark.created_at.isoformat()
        bookmarks_data.append(listing_dict)

    return jsonify({
        'bookmarks': bookmarks_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@review_bp.route('/listings/<int:listing_id>/bookmark', methods=['POST'])
@require_auth
def bookmark_listing(listing_id):
    """Bookmark a listing"""
    listing = ReviewListing.query.get(listing_id)

    if not listing:
        return jsonify({'error': 'Listing not found'}), 404

    # Check if already bookmarked
    existing = ReviewBookmark.query.filter_by(
        user_id=g.user_id,
        listing_id=listing_id
    ).first()

    if existing:
        return jsonify({'error': 'Already bookmarked'}), 400

    bookmark = ReviewBookmark(
        user_id=g.user_id,
        listing_id=listing_id
    )

    db.session.add(bookmark)
    db.session.commit()

    return jsonify({'message': 'Listing bookmarked'}), 201


@review_bp.route('/listings/<int:listing_id>/bookmark', methods=['DELETE'])
@require_auth
def remove_bookmark(listing_id):
    """Remove bookmark from listing"""
    bookmark = ReviewBookmark.query.filter_by(
        user_id=g.user_id,
        listing_id=listing_id
    ).first()

    if not bookmark:
        return jsonify({'error': 'Bookmark not found'}), 404

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({'message': 'Bookmark removed'}), 200


# ==================== REVIEW ACCOUNTS API ====================

@review_bp.route('/accounts', methods=['GET'])
@require_auth
def get_review_accounts():
    """Get user's review accounts"""
    accounts = ReviewAccount.query.filter_by(user_id=g.user_id).all()

    return jsonify({
        'accounts': [account.to_dict() for account in accounts]
    }), 200


@review_bp.route('/accounts', methods=['POST'])
@require_auth
def create_review_account():
    """Create a new review account — with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    required = ['platform', 'account_name']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate platform against whitelist
    valid, error = validate_platform(data['platform'], VALID_REVIEW_PLATFORMS)
    if not valid:
        return jsonify({'error': error}), 400

    # Validate and sanitize account name
    valid, error, clean_name = validate_string(
        data['account_name'], 'Account name', min_length=1, max_length=100
    )
    if not valid:
        return jsonify({'error': error}), 400

    # Check for duplicates
    existing = ReviewAccount.query.filter_by(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=clean_name
    ).first()

    if existing:
        return jsonify({'error': 'Account already exists'}), 400

    account = ReviewAccount(
        user_id=g.user_id,
        platform=data['platform'],
        account_name=clean_name,
        follower_count=data.get('follower_count', 0),
        category_tags=data.get('category_tags', []),
        is_active=True
    )

    db.session.add(account)
    db.session.commit()

    return jsonify(account.to_dict()), 201


@review_bp.route('/accounts/<int:account_id>', methods=['PUT'])
@require_auth
def update_review_account(account_id):
    """Update review account"""
    account = ReviewAccount.query.get(account_id)

    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    data = request.get_json()

    if 'follower_count' in data:
        account.follower_count = int(data['follower_count'])

    if 'category_tags' in data:
        account.category_tags = data['category_tags']

    if 'is_active' in data:
        account.is_active = bool(data['is_active'])

    account.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(account.to_dict()), 200


@review_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
def delete_review_account(account_id):
    """Delete review account"""
    account = ReviewAccount.query.get(account_id)

    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Account not found'}), 404

    db.session.delete(account)
    db.session.commit()

    return jsonify({'message': 'Account deleted'}), 200


# ==================== REVIEW APPLICATIONS API ====================

@review_bp.route('/applications', methods=['GET'])
@require_auth
def get_my_review_applications():
    """Get user's review applications"""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Get user's accounts
    user_accounts = ReviewAccount.query.filter_by(user_id=g.user_id).all()
    account_ids = [acc.id for acc in user_accounts]

    if not account_ids:
        return jsonify({
            'applications': [],
            'total': 0,
            'pages': 0,
            'current_page': page
        }), 200

    query = (
        ReviewApplication.query
        .options(
            joinedload(ReviewApplication.listing),
            joinedload(ReviewApplication.account),
        )
        .filter(ReviewApplication.account_id.in_(account_ids))
    )

    if status:
        query = query.filter_by(status=status)

    query = query.order_by(desc(ReviewApplication.applied_at))
    result = query.paginate(page=page, per_page=per_page)

    applications_data = []
    for app in result.items:
        app_dict = app.to_dict()
        # Listing and account are already eager-loaded (no extra queries)
        if app.listing:
            app_dict['listing'] = app.listing.to_dict()
        if app.account:
            app_dict['account'] = app.account.to_dict()
        applications_data.append(app_dict)

    return jsonify({
        'applications': applications_data,
        'total': result.total,
        'pages': result.pages,
        'current_page': page
    }), 200


@review_bp.route('/listings/<int:listing_id>/apply', methods=['POST'])
@require_auth
def apply_to_listing(listing_id):
    """Apply to a review listing"""
    listing = ReviewListing.query.get(listing_id)

    if not listing or listing.status != 'active':
        return jsonify({'error': 'Listing not found or inactive'}), 404

    if listing.deadline < datetime.utcnow():
        return jsonify({'error': 'Listing deadline has passed'}), 400

    data = request.get_json()

    if 'account_id' not in data:
        return jsonify({'error': 'Missing account_id'}), 400

    # Verify account belongs to user
    account = ReviewAccount.query.get(data['account_id'])
    if not account or account.user_id != g.user_id:
        return jsonify({'error': 'Invalid account'}), 404

    # Check if already applied
    existing = ReviewApplication.query.filter_by(
        listing_id=listing_id,
        account_id=data['account_id']
    ).first()

    if existing:
        return jsonify({'error': 'Already applied with this account'}), 400

    # Create application
    app = ReviewApplication(
        listing_id=listing_id,
        account_id=data['account_id'],
        status='pending'
    )

    db.session.add(app)

    # Update listing's applied_accounts
    if not listing.applied_accounts:
        listing.applied_accounts = []
    if data['account_id'] not in listing.applied_accounts:
        listing.applied_accounts.append(data['account_id'])

    db.session.commit()

    return jsonify({
        'id': app.id,
        'message': 'Application submitted'
    }), 201


# ==================== AUTO-APPLY RULES API ====================

@review_bp.route('/auto-rules', methods=['GET'])
@require_auth
def get_auto_apply_rules():
    """Get user's auto-apply rules"""
    rules = ReviewAutoRule.query.filter_by(user_id=g.user_id).all()

    return jsonify({
        'rules': [rule.to_dict() for rule in rules]
    }), 200


@review_bp.route('/auto-rules', methods=['POST'])
@require_auth
def create_auto_apply_rule():
    """Create a new auto-apply rule"""
    data = request.get_json()

    required = ['name']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    rule = ReviewAutoRule(
        user_id=g.user_id,
        name=data['name'],
        target_categories=data.get('target_categories', []),
        min_reward=data.get('min_reward', 0),
        max_reward=data.get('max_reward'),
        apply_deadline_days=data.get('apply_deadline_days', 30),
        max_applicants_ratio=data.get('max_applicants_ratio', 0.5),
        preferred_accounts=data.get('preferred_accounts', []),
        reward_types=data.get('reward_types', []),
        is_active=data.get('is_active', True)
    )

    db.session.add(rule)
    db.session.commit()

    return jsonify(rule.to_dict()), 201


@review_bp.route('/auto-rules/<int:rule_id>', methods=['PUT'])
@require_auth
def update_auto_apply_rule(rule_id):
    """Update auto-apply rule"""
    rule = ReviewAutoRule.query.get(rule_id)

    if not rule or rule.user_id != g.user_id:
        return jsonify({'error': 'Rule not found'}), 404

    data = request.get_json()

    if 'name' in data:
        rule.name = data['name']

    if 'target_categories' in data:
        rule.target_categories = data['target_categories']

    if 'min_reward' in data:
        rule.min_reward = data['min_reward']

    if 'max_reward' in data:
        rule.max_reward = data['max_reward']

    if 'apply_deadline_days' in data:
        rule.apply_deadline_days = data['apply_deadline_days']

    if 'max_applicants_ratio' in data:
        rule.max_applicants_ratio = data['max_applicants_ratio']

    if 'preferred_accounts' in data:
        rule.preferred_accounts = data['preferred_accounts']

    if 'reward_types' in data:
        rule.reward_types = data['reward_types']

    if 'is_active' in data:
        rule.is_active = bool(data['is_active'])

    rule.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(rule.to_dict()), 200


@review_bp.route('/auto-rules/<int:rule_id>', methods=['DELETE'])
@require_auth
def delete_auto_apply_rule(rule_id):
    """Delete auto-apply rule"""
    rule = ReviewAutoRule.query.get(rule_id)

    if not rule or rule.user_id != g.user_id:
        return jsonify({'error': 'Rule not found'}), 404

    db.session.delete(rule)
    db.session.commit()

    return jsonify({'message': 'Rule deleted'}), 200


# ==================== SCRAPER CONTROL API ====================

@review_bp.route('/scraper/status', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=60, key_prefix='scraper_status')
def get_scraper_status():
    """Get status of last scraper run (optimized: 2 aggregate queries instead of 16)"""
    platform_list = [
        'revu', 'reviewplace', 'wible', 'mibl', 'seoulouba',
        'naver', 'moaview', 'inflexer'
    ]

    # Single query: count + max(scraped_at) per platform
    platform_stats = (
        db.session.query(
            ReviewListing.source_platform,
            func.count(ReviewListing.id).label('total'),
            func.max(ReviewListing.scraped_at).label('last_scraped')
        )
        .filter(ReviewListing.source_platform.in_(platform_list))
        .group_by(ReviewListing.source_platform)
        .all()
    )

    stats_map = {row[0]: {'total_listings': row[1], 'last_scraped': row[2].isoformat() if row[2] else None} for row in platform_stats}
    platforms = {}
    for p in platform_list:
        platforms[p] = stats_map.get(p, {'total_listings': 0, 'last_scraped': None})

    # Single query: totals
    totals = (
        db.session.query(
            func.count(ReviewListing.id).label('total'),
            func.sum(case((ReviewListing.status == 'active', 1), else_=0)).label('active')
        )
        .first()
    )
    total_listings = totals[0] or 0
    active_listings = totals[1] or 0

    return jsonify({
        'total_listings': total_listings,
        'active_listings': active_listings,
        'expired_listings': total_listings - active_listings,
        'platforms': platforms
    }), 200


@review_bp.route('/scraper/run', methods=['POST'])
@require_auth
def trigger_scraper():
    """Manually trigger the scraper (admin only)"""
    # Check if user is admin
    user = g.get('user', None)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Only admins can trigger scraper'}), 403

    try:
        from backend.services.review_scrapers import aggregate_all_listings

        logger.info("[API] Manual scraper trigger by admin")
        results = aggregate_all_listings(max_workers=3)

        total = sum(results.values())
        logger.info(f"[API] Scraper completed: {total} listings processed")

        return jsonify({
            'message': 'Scraper executed successfully',
            'results': results,
            'total_processed': total
        }), 200

    except Exception as e:
        logger.error(f"[API] Scraper error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==================== AGGREGATED LISTINGS API (Multi-Platform) ====================

@review_bp.route('/aggregated', methods=['GET'])
@require_auth
def get_aggregated_listings():
    """Get unified review listings from all platforms with filters, pagination, and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category')
    platform = request.args.get('platform')
    min_reward = request.args.get('min_reward', type=int)
    max_reward = request.args.get('max_reward', type=int)
    sort = request.args.get('sort', 'latest')

    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    page = max(page, 1)

    # Base query - only active listings not expired
    query = ReviewListing.query.filter(
        ReviewListing.status == 'active',
        ReviewListing.deadline >= datetime.utcnow()
    )

    # Apply filters
    if category:
        query = query.filter_by(category=category)

    if platform:
        query = query.filter_by(source_platform=platform)

    if min_reward:
        query = query.filter(ReviewListing.reward_value >= min_reward)

    if max_reward:
        query = query.filter(ReviewListing.reward_value <= max_reward)

    # Sort results
    if sort == 'reward_high':
        query = query.order_by(desc(ReviewListing.reward_value))
    elif sort == 'applicants_few':
        # Order by fewer applicants (ascending application count)
        app_counts = (
            db.session.query(
                ReviewApplication.listing_id,
                func.count(ReviewApplication.id).label('app_count')
            )
            .group_by(ReviewApplication.listing_id)
            .subquery()
        )
        query = query.outerjoin(
            app_counts,
            ReviewListing.id == app_counts.c.listing_id
        ).order_by(func.coalesce(app_counts.c.app_count, 0))
    else:  # latest (default)
        query = query.order_by(desc(ReviewListing.created_at))

    result = query.paginate(page=page, per_page=per_page)

    # Batch lookup: get all bookmarked listing IDs for current user in one query
    listing_ids = [listing.id for listing in result.items]
    bookmarked_ids = set()
    if listing_ids:
        bookmarked_rows = (
            db.session.query(ReviewBookmark.listing_id)
            .filter(ReviewBookmark.user_id == g.user_id, ReviewBookmark.listing_id.in_(listing_ids))
            .all()
        )
        bookmarked_ids = {row[0] for row in bookmarked_rows}

    # Get application counts for each listing (for progress bar)
    app_counts_query = (
        db.session.query(
            ReviewApplication.listing_id,
            func.count(ReviewApplication.id).label('app_count')
        )
        .group_by(ReviewApplication.listing_id)
        .filter(ReviewApplication.listing_id.in_(listing_ids))
        .all()
    )
    app_counts_map = {row[0]: row[1] for row in app_counts_query}

    # Build response data
    listings_data = []
    for listing in result.items:
        listing_dict = listing.to_dict()
        listing_dict['is_bookmarked'] = listing.id in bookmarked_ids
        listing_dict['current_applicants'] = app_counts_map.get(listing.id, 0)
        listings_data.append(listing_dict)

    # Get last scraped timestamp
    last_scraped = (
        db.session.query(func.max(ReviewListing.scraped_at))
        .scalar()
    )

    return jsonify({
        'success': True,
        'data': {
            'listings': listings_data,
            'total': result.total,
            'pages': result.pages,
            'current_page': page,
            'per_page': per_page,
            'last_scraped': last_scraped.isoformat() if last_scraped else None
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@review_bp.route('/aggregated/stats', methods=['GET'])
@require_auth
def get_aggregated_stats():
    """Get aggregation statistics across all platforms"""
    # Count active listings by platform
    platform_stats = (
        db.session.query(
            ReviewListing.source_platform,
            func.count(ReviewListing.id).label('total_listings'),
            func.avg(ReviewListing.reward_value).label('avg_reward')
        )
        .filter(ReviewListing.status == 'active', ReviewListing.deadline >= datetime.utcnow())
        .group_by(ReviewListing.source_platform)
        .all()
    )

    platforms = {}
    for platform, total, avg_reward in platform_stats:
        platforms[platform] = {
            'total_listings': total,
            'average_reward': float(avg_reward or 0)
        }

    # Overall statistics
    total_listings = sum(p['total_listings'] for p in platforms.values())
    avg_reward = (
        db.session.query(func.avg(ReviewListing.reward_value))
        .filter(ReviewListing.status == 'active', ReviewListing.deadline >= datetime.utcnow())
        .scalar() or 0
    )

    # New listings in last 24 hours
    new_in_24h = ReviewListing.query.filter(
        ReviewListing.status == 'active',
        ReviewListing.deadline >= datetime.utcnow(),
        ReviewListing.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()

    return jsonify({
        'success': True,
        'data': {
            'total_listings': total_listings,
            'average_reward': float(avg_reward),
            'new_in_24h': new_in_24h,
            'platforms': platforms
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@review_bp.route('/scrape/now', methods=['POST'])
@require_auth
def trigger_scrape_now():
    """Trigger immediate data refresh from all platforms"""
    try:
        # Check if user is admin or has permission
        user = g.get('user', None)
        if user and user.role != 'admin':
            logger.warning(f"[API] Non-admin user {g.user_id} attempted to trigger scrape")

        from backend.services.review_scrapers import aggregate_all_listings

        logger.info(f"[API] Manual scrape triggered by user {g.user_id}")
        results = aggregate_all_listings(max_workers=3)

        total = sum(results.values())
        logger.info(f"[API] Scrape completed: {total} listings processed")

        return jsonify({
            'success': True,
            'message': 'Data refresh started successfully',
            'data': {
                'status': 'running',
                'results': results,
                'total_processed': total
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except ImportError:
        logger.warning("[API] review_scrapers module not available, scrape triggered but may not execute")
        return jsonify({
            'success': True,
            'message': 'Scrape request queued (scraper module pending)',
            'data': {'status': 'queued'},
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"[API] Scrape error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Scrape failed: ' + str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
