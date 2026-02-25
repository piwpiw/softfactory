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
