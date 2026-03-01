"""Admin API Routes — User Management, Subscriptions, Metrics, Audit Logs"""
from flask import Blueprint, jsonify, request, g
from ..auth import require_auth, require_admin
from .admin_service import AdminService
from ..models import db, User, Subscription, Payment, SNSAccount, Campaign

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ===== USER MANAGEMENT ENDPOINTS =====

@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def get_users():
    """Retrieve paginated users with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')

    result = AdminService.get_users(
        page=page,
        per_page=per_page,
        search=search,
        role=role if role else None,
        status=status if status else None
    )

    return jsonify(result), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user_detail(user_id):
    """Retrieve full user details"""
    user = AdminService.get_user_detail(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@require_auth
@require_admin
def update_user_role(user_id):
    """Change user role"""
    data = request.json
    new_role = data.get('role')

    if new_role not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400

    user = AdminService.update_user_role(user_id, new_role, g.user.id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user), 200


@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@require_auth
@require_admin
def toggle_user_active(user_id):
    """Enable/disable user account"""
    data = request.json
    is_active = data.get('is_active', True)

    user = AdminService.toggle_user_active(user_id, is_active, g.user.id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user), 200


@admin_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@require_auth
@require_admin
def unlock_user(user_id):
    """Remove account lockout"""
    user = AdminService.unlock_user(user_id, g.user.id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_user(user_id):
    """Delete user"""
    if user_id == g.user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    result = AdminService.delete_user(user_id, g.user.id)
    if not result:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(result), 200


@admin_bp.route('/users/bulk-delete', methods=['POST'])
@require_auth
@require_admin
def bulk_delete_users():
    """Delete multiple users"""
    data = request.json
    user_ids = data.get('user_ids', [])

    if not user_ids:
        return jsonify({'error': 'No users specified'}), 400

    # Prevent self-deletion
    if g.user.id in user_ids:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    result = AdminService.bulk_delete_users(user_ids, g.user.id)
    return jsonify(result), 200


# ===== SUBSCRIPTION/PRODUCT ENDPOINTS =====

@admin_bp.route('/subscriptions', methods=['GET'])
@require_auth
@require_admin
def get_subscriptions():
    """Retrieve subscriptions with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_id = request.args.get('user_id', type=int)
    product_id = request.args.get('product_id', type=int)
    status = request.args.get('status', '')

    result = AdminService.get_subscriptions(
        page=page,
        per_page=per_page,
        user_id=user_id,
        product_id=product_id,
        status=status if status else None
    )

    return jsonify(result), 200


@admin_bp.route('/products', methods=['GET'])
@require_auth
@require_admin
def get_products():
    """Retrieve all products"""
    include_inactive = request.args.get('include_inactive', False, type=bool)
    products = AdminService.get_products(include_inactive=include_inactive)
    return jsonify({'products': products}), 200


@admin_bp.route('/products', methods=['POST'])
@require_auth
@require_admin
def create_product():
    """Create new product"""
    data = request.json
    required = ['slug', 'name', 'monthly_price']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    product = AdminService.create_product(
        slug=data['slug'],
        name=data['name'],
        monthly_price=data['monthly_price'],
        annual_price=data.get('annual_price'),
        description=data.get('description'),
        icon=data.get('icon')
    )

    return jsonify(product), 201


@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@require_auth
@require_admin
def update_product(product_id):
    """Update product details"""
    data = request.json

    product = AdminService.update_product(product_id, **data)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(product), 200


@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_product(product_id):
    """Soft delete product"""
    result = AdminService.delete_product(product_id)
    if not result:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(result), 200


# ===== SYSTEM METRICS ENDPOINTS =====

@admin_bp.route('/stats', methods=['GET'])
@require_auth
@require_admin
def get_system_stats():
    """Retrieve overall system metrics"""
    stats = AdminService.get_system_stats()
    return jsonify({'stats': stats}), 200


@admin_bp.route('/revenue', methods=['GET'])
@require_auth
@require_admin
def get_revenue_stats():
    """Retrieve revenue breakdown"""
    days = request.args.get('days', 30, type=int)
    stats = AdminService.get_revenue_stats(days=days)

    return jsonify({
        'revenue_7d': stats['daily'].get(
            (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'), 0
        ),
        'revenue_30d': sum(stats['daily'].values()),
        'revenue_alltime': stats['total'],
        'by_product': stats['by_product']
    }), 200


@admin_bp.route('/user-stats', methods=['GET'])
@require_auth
@require_admin
def get_user_stats():
    """Retrieve user growth and distribution stats"""
    stats = AdminService.get_user_stats()
    return jsonify(stats), 200


# ===== AUDIT LOG ENDPOINTS =====

@admin_bp.route('/audit-logs', methods=['GET'])
@require_auth
@require_admin
def get_audit_logs():
    """Retrieve audit logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    action = request.args.get('action', '')
    admin_id = request.args.get('admin_id', type=int)

    result = AdminService.get_audit_logs(
        page=page,
        per_page=per_page,
        action=action if action else None,
        admin_id=admin_id
    )

    return jsonify(result), 200


# ===== SNS MONITORING ENDPOINTS =====

@admin_bp.route('/sns-accounts', methods=['GET'])
@require_auth
@require_admin
def get_sns_accounts():
    """Retrieve SNS accounts summary"""
    limit = request.args.get('limit', 50, type=int)
    accounts = AdminService.get_sns_accounts_summary(limit=limit)
    return jsonify({'accounts': accounts}), 200


# ===== CAMPAIGN MONITORING ENDPOINTS =====

@admin_bp.route('/campaigns', methods=['GET'])
@require_auth
@require_admin
def get_campaigns():
    """Retrieve campaigns summary"""
    limit = request.args.get('limit', 50, type=int)
    campaigns = AdminService.get_campaigns_summary(limit=limit)
    return jsonify({'campaigns': campaigns}), 200


# ===== PAYMENTS ENDPOINT =====

@admin_bp.route('/payments', methods=['GET'])
@require_auth
@require_admin
def get_payments():
    """Retrieve recent payments"""
    limit = request.args.get('limit', 20, type=int)

    payments = Payment.query.order_by(Payment.created_at.desc()).limit(limit).all()

    return jsonify([
        {
            'id': p.id,
            'user_id': p.user_id,
            'product': p.product.name if p.product else 'N/A',
            'amount': p.amount,
            'status': p.status,
            'created_at': p.created_at.isoformat()
        }
        for p in payments
    ]), 200


# ===== EXPORT ENDPOINTS =====

@admin_bp.route('/export/users', methods=['GET'])
@require_auth
@require_admin
def export_users():
    """Export users as CSV"""
    csv_data = AdminService.export_users_csv()
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=users.csv'
    }


@admin_bp.route('/export/payments', methods=['GET'])
@require_auth
@require_admin
def export_payments():
    """Export payments as CSV"""
    csv_data = AdminService.export_payments_csv()
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=payments.csv'
    }


# Import required modules for revenue endpoint
from datetime import datetime, timedelta

__all__ = ['admin_bp']
