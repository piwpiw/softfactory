"""Platform Management Routes"""
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from datetime import datetime
import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .models import db, Product, Subscription, User, Payment, ApprovalQueueItem, ApprovalQueueEvent, Notification
from .auth import require_auth, require_admin

platform_bp = Blueprint('platform', __name__, url_prefix='/api/platform')
logger = logging.getLogger('platform_routes')


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def _record_approval_queue_event(item, event_type, *, actor_user_id=None, summary=None, metadata=None, persist_item_ref=True):
    if not item:
        return None
    event = ApprovalQueueEvent(
        item_id=item.id if persist_item_ref else None,
        queue_key=item.queue_key,
        user_id=item.user_id,
        actor_user_id=actor_user_id,
        service=item.service,
        title=item.title,
        event_type=event_type,
        status=item.status,
        approver_role=item.approver_role,
        summary=summary or item.summary or '',
        metadata_json=metadata or {},
    )
    db.session.add(event)
    return event


def _approval_queue_summary_query(query):
    items = query.all()
    by_status = {}
    by_service = {}
    for item in items:
        by_status[item.status] = by_status.get(item.status, 0) + 1
        by_service[item.service] = by_service.get(item.service, 0) + 1
    return {
        'total': len(items),
        'byStatus': by_status,
        'byService': by_service,
        'updatedAt': datetime.utcnow().isoformat(),
    }


def _build_approval_notification(event_type, item_payload):
    event_map = {
        'created': ('승인 큐 등록', '새 승인 작업이 등록되었습니다.'),
        'updated': ('승인 큐 업데이트', '승인 작업 정보가 업데이트되었습니다.'),
        'status_changed': ('승인 상태 변경', '승인 작업 상태가 변경되었습니다.'),
        'deleted': ('승인 큐 제거', '승인 작업이 큐에서 제거되었습니다.'),
    }
    title, prefix = event_map.get(event_type, ('승인 큐 알림', '승인 큐 이벤트가 발생했습니다.'))
    item_title = item_payload.get('title') or '제목 없음'
    status = item_payload.get('status') or 'queued'
    message = f'{prefix} {item_title} ({status})'
    return title, message


def _send_approval_queue_webhook(event_type, item_payload, owner_user_id, actor_user_id):
    contract = item_payload.get('contract') or {}
    webhook_url = (contract.get('webhook_url') or os.getenv('APPROVAL_QUEUE_WEBHOOK_URL') or '').strip()
    if not webhook_url:
        return False

    body = json.dumps({
        'event_type': event_type,
        'queue_item': item_payload,
        'owner_user_id': owner_user_id,
        'actor_user_id': actor_user_id,
        'sent_at': datetime.utcnow().isoformat(),
    }).encode('utf-8')
    request_obj = Request(
        webhook_url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(request_obj, timeout=5) as response:
            return 200 <= getattr(response, 'status', 200) < 300
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        logger.warning('approval queue webhook dispatch failed: %s', exc)
        return False


def _dispatch_approval_queue_side_effects(event_type, item_payload, owner_user_id, actor_user_id):
    if not owner_user_id:
        return

    title, message = _build_approval_notification(event_type, item_payload)
    notification = Notification(
        user_id=owner_user_id,
        notification_type='approval_queue',
        title=title,
        message=message,
        action_url=item_payload.get('sourceUrl') or '/ai-automation/index.html',
        icon='approval',
        extra_data={
            'eventType': event_type,
            'queueKey': item_payload.get('id'),
            'service': item_payload.get('service'),
            'status': item_payload.get('status'),
            'actorUserId': actor_user_id,
        }
    )
    db.session.add(notification)
    db.session.commit()
    _send_approval_queue_webhook(event_type, item_payload, owner_user_id, actor_user_id)


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


@platform_bp.route('/approval-queue', methods=['GET'])
@require_auth
def get_approval_queue():
    items = (
        ApprovalQueueItem.query
        .filter_by(user_id=g.user_id)
        .order_by(ApprovalQueueItem.updated_at.desc(), ApprovalQueueItem.created_at.desc())
        .all()
    )
    return jsonify({'items': [item.to_dict() for item in items]}), 200


@platform_bp.route('/approval-queue/summary', methods=['GET'])
@require_auth
def get_approval_queue_summary():
    summary = _approval_queue_summary_query(
        ApprovalQueueItem.query.filter_by(user_id=g.user_id)
    )
    return jsonify(summary), 200


@platform_bp.route('/admin/approval-queue', methods=['GET'])
@require_auth
@require_admin
def get_admin_approval_queue():
    items = (
        ApprovalQueueItem.query
        .order_by(ApprovalQueueItem.updated_at.desc(), ApprovalQueueItem.created_at.desc())
        .all()
    )
    return jsonify({'items': [item.to_dict() for item in items]}), 200


@platform_bp.route('/admin/approval-queue/events', methods=['GET'])
@require_auth
@require_admin
def get_admin_approval_queue_events():
    limit = request.args.get('limit', 20, type=int)
    limit = max(1, min(limit, 100))
    events = (
        ApprovalQueueEvent.query
        .order_by(ApprovalQueueEvent.created_at.desc(), ApprovalQueueEvent.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify({'items': [event.to_dict() for event in events]}), 200


@platform_bp.route('/admin/approval-queue/summary', methods=['GET'])
@require_auth
@require_admin
def get_admin_approval_queue_summary():
    summary = _approval_queue_summary_query(ApprovalQueueItem.query)
    return jsonify(summary), 200


@platform_bp.route('/approval-queue', methods=['POST'])
@require_auth
def upsert_approval_queue_item():
    payload = request.get_json(silent=True) or {}
    queue_key = (payload.get('id') or '').strip()
    service = (payload.get('service') or '').strip()
    title = (payload.get('title') or '').strip()
    if not queue_key or not service or not title:
        return jsonify({'error': 'id, service, title are required'}), 400

    item = ApprovalQueueItem.query.filter_by(user_id=g.user_id, queue_key=queue_key).first()
    is_new = item is None
    if not item:
        item = ApprovalQueueItem(user_id=g.user_id, queue_key=queue_key)
        db.session.add(item)

    item.service = service
    item.title = title
    item.status = (payload.get('status') or 'queued').strip()
    item.owner = payload.get('owner') or getattr(g.user, 'email', None)
    item.approval_mode = (payload.get('approvalMode') or 'approve-before-publish').strip()
    item.approver_role = (payload.get('approverRole') or 'admin').strip()
    item.channels = payload.get('channels') if isinstance(payload.get('channels'), list) else []
    item.account_ids = payload.get('accountIds') if isinstance(payload.get('accountIds'), list) else []
    item.scheduled_at = _parse_iso_datetime(payload.get('scheduledAt'))
    item.source_url = payload.get('sourceUrl') or ''
    item.summary = payload.get('summary') or ''
    item.contract_json = payload.get('contract') if isinstance(payload.get('contract'), dict) else None
    item.metadata_json = payload.get('metadata') if isinstance(payload.get('metadata'), dict) else {}

    db.session.flush()
    _record_approval_queue_event(
        item,
        'created' if is_new else 'updated',
        actor_user_id=g.user_id,
        metadata={
            'status': item.status,
            'channels': item.channels or [],
            'accountIds': item.account_ids or [],
        },
    )
    db.session.commit()
    item_payload = item.to_dict()
    _dispatch_approval_queue_side_effects(
        'created' if is_new else 'updated',
        item_payload,
        item.user_id,
        g.user_id,
    )
    return jsonify(item_payload), 200


@platform_bp.route('/approval-queue/<string:queue_key>/status', methods=['POST'])
@require_auth
def update_approval_queue_status(queue_key):
    payload = request.get_json(silent=True) or {}
    status = (payload.get('status') or '').strip()
    if not status:
        return jsonify({'error': 'status is required'}), 400

    item = ApprovalQueueItem.query.filter_by(user_id=g.user_id, queue_key=queue_key).first()
    if not item:
        return jsonify({'error': 'queue item not found'}), 404
    previous_status = item.status
    item.status = status
    item.updated_at = datetime.utcnow()
    _record_approval_queue_event(
        item,
        'status_changed',
        actor_user_id=g.user_id,
        metadata={
            'previousStatus': previous_status,
            'nextStatus': status,
        },
    )
    db.session.commit()
    item_payload = item.to_dict()
    _dispatch_approval_queue_side_effects(
        'status_changed',
        item_payload,
        item.user_id,
        g.user_id,
    )
    return jsonify(item_payload), 200


@platform_bp.route('/approval-queue/<string:queue_key>', methods=['DELETE'])
@require_auth
def delete_approval_queue_item(queue_key):
    item = ApprovalQueueItem.query.filter_by(user_id=g.user_id, queue_key=queue_key).first()
    if not item:
        return jsonify({'error': 'queue item not found'}), 404

    snapshot = item.to_dict()
    _record_approval_queue_event(
        item,
        'deleted',
        actor_user_id=g.user_id,
        summary=snapshot.get('summary') or item.summary or '',
        persist_item_ref=False,
        metadata={
            'status': item.status,
            'channels': item.channels or [],
            'accountIds': item.account_ids or [],
        },
    )
    owner_user_id = item.user_id
    db.session.delete(item)
    db.session.commit()
    _dispatch_approval_queue_side_effects(
        'deleted',
        snapshot,
        owner_user_id,
        g.user_id,
    )
    return jsonify({'ok': True, 'id': queue_key}), 200


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
