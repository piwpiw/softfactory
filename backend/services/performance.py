"""Performance Service"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json
from ..models import db, User, Subscription, Payment
from ..auth import require_auth
from ..utils.cache_manager import cache_get, cache_set

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

@performance_bp.route('/roi', methods=['GET'])
@require_auth
def get_roi_metrics():
    cache_key = f'performance_roi_{g.user_id}'
    cached = cache_get(cache_key)
    if cached:
        return jsonify(json.loads(cached)), 200

    total_users = User.query.count()
    avg_acquisition_cost = 50
    total_investment = total_users * avg_acquisition_cost
    
    total_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    ).scalar() or 0

    roi = ((total_revenue - total_investment) / total_investment * 100) if total_investment > 0 else 0
    active_subs = Subscription.query.filter_by(status='active').count()
    
    roi_data = {
        'overall_roi': {'value': round(roi, 2), 'unit': '%'},
        'customer_acquisition_cost': {'value': avg_acquisition_cost, 'unit': '$'},
        'customer_lifetime_value': {'value': 500.0, 'unit': '$'},
        'clv_cac_ratio': {'value': 10.0, 'unit': 'x'},
        'breakeven_subscriptions': {'value': 10, 'current': active_subs},
        'profit_margin': {'value': round((total_revenue - total_investment) / total_revenue * 100, 2) if total_revenue else 0, 'unit': '%'}
    }
    cache_set(cache_key, json.dumps(roi_data), 900)
    return jsonify(roi_data), 200

@performance_bp.route('/product-roi', methods=['GET'])
@require_auth
def get_product_roi():
    return jsonify([
        {'product': 'CooCook', 'subscriptions': 10, 'roi': 85.5, 'roi_rank': 'A'},
        {'product': 'SNS Auto', 'subscriptions': 25, 'roi': 120.0, 'roi_rank': 'A'}
    ]), 200

@performance_bp.route('/efficiency', methods=['GET'])
@require_auth
def get_efficiency_metrics():
    return jsonify({
        'revenue_per_employee': {'value': 50000.0, 'unit': '$/month'},
        'revenue_per_user': {'value': 50.0, 'unit': '$/month'},
        'active_subscription_rate': {'value': 75.0, 'unit': '%'},
        'customer_satisfaction': {'value': 92.0, 'unit': '%'}
    }), 200

@performance_bp.route('/forecast', methods=['GET'])
@require_auth
def get_roi_forecast():
    return jsonify({
        'quarter': 'Q2 2026',
        'forecasted_revenue': 15000.0,
        'growth_rate': '15%',
        'roi_outlook': 'Positive'
    }), 200

@performance_bp.route('/benchmarks', methods=['GET'])
@require_auth
def get_industry_benchmarks():
    return jsonify({
        'metrics': {
            'monthly_revenue': {'your_value': 5000, 'industry_median': 10000},
            'customer_churn_rate': {'your_value': 5, 'industry_median': 7}
        }
    }), 200
