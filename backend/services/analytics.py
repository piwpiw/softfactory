"""Analytics Service"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json
from ..models import db, User, Subscription, Payment
from ..auth import require_auth
from ..utils.cache_manager import cache_get, cache_set
from ..cache import ttl_cache

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/advanced', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=60, key_prefix='analytics_advanced')
def get_advanced_analytics():
    """Advanced analytics (1-minute cache)"""
    metric = request.args.get('metric', 'revenue')
    period = request.args.get('period', '30')

    now = datetime.utcnow()
    start_date = now - timedelta(days=int(period))

    data_points = []
    current = start_date
    while current <= now:
        value = 0
        if metric == 'revenue':
            value = db.session.query(func.sum(Payment.amount)).filter(
                and_(Payment.status == 'completed', Payment.created_at >= current)
            ).scalar() or 0
        data_points.append({'timestamp': current.isoformat(), 'value': float(value)})
        current += timedelta(days=1)

    result = {'metric': metric, 'period': period, 'data': data_points}
    return jsonify(result), 200

@analytics_bp.route('/cohort', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=60, key_prefix='analytics_cohort')
def get_cohort_analysis():
    """Cohort analysis (1-minute cache)"""
    users = User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=180)).all()
    cohorts = {}
    for user in users:
        cohort_date = user.created_at.strftime('%Y-%m')
        if cohort_date not in cohorts:
            cohorts[cohort_date] = {'signup_date': cohort_date, 'total_users': 0}
        cohorts[cohort_date]['total_users'] += 1
    return jsonify(list(cohorts.values())), 200

@analytics_bp.route('/funnel', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=60, key_prefix='analytics_funnel')
def get_conversion_funnel():
    """Conversion funnel (1-minute cache)"""
    total_users = User.query.count()
    subscribed = Subscription.query.filter_by(status='active').count()
    paid = Payment.query.filter_by(status='completed').count()
    return jsonify([
        {'stage': 'Signups', 'users': total_users, 'conversion_rate': 100.0},
        {'stage': 'Subscribed', 'users': subscribed, 'conversion_rate': (subscribed/total_users*100) if total_users else 0},
        {'stage': 'Paid', 'users': paid, 'conversion_rate': (paid/subscribed*100) if subscribed else 0}
    ]), 200

@analytics_bp.route('/service-metrics', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=60, key_prefix='analytics_service_metrics')
def get_service_metrics():
    """Service metrics (1-minute cache)"""
    return jsonify({
        'coocook': {'name': 'CooCook', 'bookings': 0, 'revenue': 0},
        'sns_auto': {'name': 'SNS Auto', 'posts': 0, 'reach': 0}
    }), 200

@analytics_bp.route('/trends', methods=['GET'])
@require_auth
@ttl_cache(ttl_seconds=300, key_prefix='analytics_trends')
def get_market_trends():
    """Market trends (5-minute cache -- changes slowly)"""
    days = request.args.get('days', 30, type=int)
    return jsonify({
        'period': days,
        'average_daily_revenue': 100.0,
        'trend': 'up',
        'forecast_next_7_days': 700.0
    }), 200
