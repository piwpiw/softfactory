"""Dashboard Service"""
from flask import Blueprint, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json
from ..models import db, User, Subscription, Payment, Product
from ..auth import require_auth
from ..utils.cache_manager import cache_get, cache_set
from ..cache import ttl_cache

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/kpis', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=30, key_prefix='dashboard_kpis')
def get_kpis():
    """Dashboard KPIs (30-second cache)"""
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(Payment.status == 'completed', Payment.created_at >= month_ago)
    ).scalar() or 0

    kpis = {'revenue': {'value': round(revenue, 2), 'unit': '$'}}
    return jsonify(kpis), 200

@dashboard_bp.route('/charts', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=30, key_prefix='dashboard_charts')
def get_charts():
    """Dashboard charts (30-second cache)"""
    return jsonify({'revenue_trend': {'labels': ['Jan', 'Feb'], 'datasets': []}}), 200

@dashboard_bp.route('/summary', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=30, key_prefix='dashboard_summary')
def get_dashboard_summary():
    """Dashboard summary (30-second cache)"""
    total_users = User.query.count()
    active_subs = Subscription.query.filter_by(status='active').count()
    return jsonify({'total_users': total_users, 'active_subscriptions': active_subs}), 200
