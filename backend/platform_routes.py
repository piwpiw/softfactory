"""Platform Management Routes"""
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from .models import db, Product, Subscription, User, Payment
from .auth import require_auth, require_admin

platform_bp = Blueprint('platform', __name__, url_prefix='/api/platform')


@platform_bp.route('/products', methods=['GET'])
def get_products():
    """Get all active products"""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([p.to_dict() for p in products]), 200


@platform_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    """Get user dashboard - subscribed vs available services"""
    # Get user's subscriptions
    subscriptions = Subscription.query.filter_by(
        user_id=g.user_id,
        status='active'
    ).all()

    subscribed_products = {s.product_id: s.to_dict() for s in subscriptions}

    # Get all products
    all_products = Product.query.filter_by(is_active=True).all()

    products_data = []
    for product in all_products:
        product_dict = product.to_dict()
        product_dict['subscribed'] = product.id in subscribed_products
        if product.id in subscribed_products:
            product_dict['subscription'] = subscribed_products[product.id]
        products_data.append(product_dict)

    return jsonify({
        'user': g.user.to_dict(),
        'products': products_data,
        'subscription_count': len(subscriptions)
    }), 200


@platform_bp.route('/admin/users', methods=['GET'])
@require_auth
@require_admin
def get_users():
    """Get all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    users = User.query.paginate(page=page, per_page=per_page)

    users_data = [u.to_dict() for u in users.items]

    # Add subscription info
    for user_dict in users_data:
        user_subs = Subscription.query.filter_by(
            user_id=user_dict['id'],
            status='active'
        ).count()
        user_dict['active_subscriptions'] = user_subs

    return jsonify({
        'users': users_data,
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    }), 200


@platform_bp.route('/admin/revenue', methods=['GET'])
@require_auth
@require_admin
def get_revenue():
    """Get revenue statistics (admin only)"""
    # MRR (Monthly Recurring Revenue)
    active_subs = Subscription.query.filter_by(status='active').all()
    mrr = 0
    for sub in active_subs:
        price = sub.product.monthly_price if sub.plan_type == 'monthly' else sub.product.annual_price / 12
        mrr += price

    # ARR (Annual Recurring Revenue)
    arr = mrr * 12

    # Total Revenue (all completed payments)
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(
        status='completed'
    ).scalar() or 0

    # Revenue by product
    revenue_by_product = []
    products = Product.query.all()
    for product in products:
        product_subs = Subscription.query.filter_by(
            product_id=product.id,
            status='active'
        ).count()
        product_mrr = product_subs * product.monthly_price
        revenue_by_product.append({
            'product_name': product.name,
            'subscriptions': product_subs,
            'monthly_revenue': product_mrr
        })

    return jsonify({
        'mrr': round(mrr, 2),
        'arr': round(arr, 2),
        'total_revenue': round(total_revenue, 2),
        'total_users': User.query.count(),
        'active_subscriptions': len(active_subs),
        'revenue_by_product': revenue_by_product
    }), 200


@platform_bp.route('/admin/executive-dashboard', methods=['GET'])
@require_auth
@require_admin
def get_executive_dashboard():
    """Get comprehensive executive dashboard metrics (CEO level)"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_, or_

    # Time periods
    today = datetime.utcnow().date()
    month_start = datetime(today.year, today.month, 1)
    month_ago = today - timedelta(days=30)
    quarter_ago = today - timedelta(days=90)

    # === KPI METRICS ===
    # Monthly Revenue
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.status == 'completed',
            Payment.created_at >= month_start
        )
    ).scalar() or 0

    # Previous month revenue for comparison
    prev_month_start = month_start - timedelta(days=1)
    prev_month_start = datetime(prev_month_start.year, prev_month_start.month, 1)
    prev_month_end = month_start - timedelta(days=1)
    prev_monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.status == 'completed',
            Payment.created_at >= prev_month_start,
            Payment.created_at <= prev_month_end
        )
    ).scalar() or 0

    # Growth rate
    growth_rate = 0
    if prev_monthly_revenue > 0:
        growth_rate = ((monthly_revenue - prev_monthly_revenue) / prev_monthly_revenue) * 100

    # Active users
    active_users = User.query.filter_by(is_active=True).count()
    active_users_month_ago = User.query.filter(
        User.created_at >= month_ago,
        User.is_active == True
    ).count()

    # ROI calculation (total revenue vs total users * CAC)
    total_users = User.query.count()
    cac = 580000  # Customer Acquisition Cost (static for now)
    ltv = 2800000  # Lifetime Value (static for now)
    roi = ((ltv - cac) / cac) * 100 if cac > 0 else 0

    # === REVENUE TRENDS (Monthly) ===
    revenue_trends = []
    for i in range(6):
        month_date = today - timedelta(days=30 * (5 - i))
        month_start_check = datetime(month_date.year, month_date.month, 1)
        if i == 5:
            month_end_check = datetime(today.year, today.month, 1)
        else:
            month_end_check = month_start_check + timedelta(days=32)
            month_end_check = datetime(month_end_check.year, month_end_check.month, 1)

        month_rev = db.session.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == 'completed',
                Payment.created_at >= month_start_check,
                Payment.created_at < month_end_check
            )
        ).scalar() or 0
        revenue_trends.append(round(month_rev, 2))

    # === SERVICE DISTRIBUTION ===
    service_distribution = []
    products = Product.query.filter_by(is_active=True).all()
    for product in products:
        product_subs = Subscription.query.filter_by(
            product_id=product.id,
            status='active'
        ).count()
        service_distribution.append({
            'name': product.name,
            'users': product_subs,
            'revenue': round(product_subs * product.monthly_price, 2)
        })

    # === REGIONAL DISTRIBUTION (Simulated) ===
    regional_data = [
        {'region': '서울', 'revenue': 580000, 'users': 2450},
        {'region': '경기', 'revenue': 420000, 'users': 1850},
        {'region': '인천', 'revenue': 350000, 'users': 1520},
        {'region': '부산', 'revenue': 280000, 'users': 1100},
        {'region': '대구', 'revenue': 240000, 'users': 900},
    ]

    # === CHURN & RETENTION METRICS ===
    churn_rate = 2.3  # percent
    retention_rate = 97.7  # percent
    avg_subscription_length = 14.2  # months

    # === SUBSCRIPTION BREAKDOWN ===
    basic_subs = Subscription.query.filter(
        and_(Subscription.status == 'active', Subscription.plan_type == 'basic')
    ).count()
    premium_subs = Subscription.query.filter(
        and_(Subscription.status == 'active', Subscription.plan_type == 'premium')
    ).count()
    enterprise_subs = Subscription.query.filter(
        and_(Subscription.status == 'active', Subscription.plan_type == 'enterprise')
    ).count()

    # === DAY COMPARISON (Yesterday vs Today) ===
    yesterday = today - timedelta(days=1)
    yesterday_revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.status == 'completed',
            Payment.created_at >= datetime.combine(yesterday, datetime.min.time()),
            Payment.created_at < datetime.combine(today, datetime.min.time())
        )
    ).scalar() or 0

    today_revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.status == 'completed',
            Payment.created_at >= datetime.combine(today, datetime.min.time())
        )
    ).scalar() or 0

    # Hourly comparison data (simulated)
    hourly_comparison = {
        'yesterday': [42000, 52000, 48000, 61000, 55000],
        'today': [52000, 62000, 58000, 71000, 68000]
    }

    return jsonify({
        'kpis': {
            'monthly_revenue': round(monthly_revenue, 2),
            'growth_rate': round(growth_rate, 1),
            'active_users': active_users,
            'roi': round(roi, 1)
        },
        'revenue_trends': revenue_trends,
        'service_distribution': service_distribution,
        'regional_distribution': regional_data,
        'metrics': {
            'churn_rate': churn_rate,
            'retention_rate': retention_rate,
            'avg_subscription_length': avg_subscription_length,
            'cac': cac,
            'ltv': ltv
        },
        'subscription_breakdown': {
            'basic': basic_subs,
            'premium': premium_subs,
            'enterprise': enterprise_subs,
            'total': basic_subs + premium_subs + enterprise_subs
        },
        'daily_comparison': {
            'yesterday': round(yesterday_revenue, 2),
            'today': round(today_revenue, 2),
            'hourly': hourly_comparison
        }
    }), 200
