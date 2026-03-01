"""
Notification Service — Real-time event management for WebSocket + Email

FEATURES:
- Create notifications in database
- Broadcast to WebSocket clients
- Send email notifications
- Notification preferences management
- Read/unread tracking
- Archive old notifications

ENDPOINTS:
  GET  /api/notifications               — List user's notifications
  POST /api/notifications               — Create notification
  GET  /api/notifications/{id}          — Get notification details
  PUT  /api/notifications/{id}/read     — Mark as read
  POST /api/notifications/read-all      — Mark all as read
  DELETE /api/notifications/{id}        — Delete notification
  GET  /api/notifications/stats         — Get unread count

WebSocket EVENTS:
  emit: notification_created
  emit: notification_read
  emit: notification_deleted
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

from ..models import db, Notification, User
from ..auth import require_auth, require_subscription
from ..input_validator import validate_string

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def create_notification(user_id: int, notification_type: str, title: str,
                       message: str, action_url: str = None, icon: str = None,
                       metadata: dict = None, broadcast: bool = True) -> Notification:
    """
    Create a notification for a user.

    Args:
        user_id: User ID to notify
        notification_type: Type of notification ('sns_publish', 'like', 'comment', etc.)
        title: Notification title
        message: Notification message body
        action_url: Optional URL for user to take action
        icon: Optional Material icon name
        metadata: Optional dict with extra data
        broadcast: Whether to broadcast via WebSocket

    Returns:
        Notification instance
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=validate_string(title, max_length=255),
        message=validate_string(message, max_length=5000),
        action_url=action_url,
        icon=icon,
        metadata=metadata
    )
    db.session.add(notification)
    db.session.commit()

    # Broadcast via WebSocket if available
    if broadcast:
        try:
            from ..websocket_server import broadcast_notification
            broadcast_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url
            )
        except Exception as e:
            import logging
            logging.getLogger('notifications').warning(f'WebSocket broadcast failed: {e}')

    return notification


def send_notification_email(user_id: int, title: str, message: str, action_url: str = None) -> bool:
    """Send notification via email."""
    try:
        user = User.query.get(user_id)
        if not user:
            return False

        from .email_service import send_email

        email_body = f"""
        <h2>{title}</h2>
        <p>{message}</p>
        """

        if action_url:
            email_body += f'<p><a href="{action_url}">View More</a></p>'

        return send_email(
            recipient=user.email,
            subject=title,
            html_body=email_body
        )
    except Exception as e:
        import logging
        logging.getLogger('notifications').error(f'Email notification failed: {e}')
        return False


# ============================================================================
# API ENDPOINTS
# ============================================================================

@notifications_bp.route('', methods=['GET'])
@require_auth
def list_notifications():
    """Get user's notifications with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = Notification.query.filter_by(user_id=g.user_id)

    if unread_only:
        query = query.filter_by(is_read=False)

    total = query.count()
    notifications = query.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=per_page
    ).items

    return jsonify({
        'status': 'success',
        'data': [n.to_dict() for n in notifications],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200


@notifications_bp.route('/<int:notification_id>', methods=['GET'])
@require_auth
def get_notification(notification_id):
    """Get specific notification."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=g.user_id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({
        'status': 'success',
        'data': notification.to_dict()
    }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@require_auth
def mark_as_read(notification_id):
    """Mark notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=g.user_id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()

    # Broadcast read event
    try:
        from ..websocket_server import socketio
        socketio.emit('notification_read', {
            'notification_id': notification_id,
            'timestamp': datetime.utcnow().isoformat()
        }, to=f'user_{g.user_id}_notifications', namespace='/notifications')
    except Exception:
        pass

    return jsonify({
        'status': 'success',
        'data': notification.to_dict()
    }), 200


@notifications_bp.route('/read-all', methods=['POST'])
@require_auth
def mark_all_as_read():
    """Mark all notifications as read."""
    unread_notifications = Notification.query.filter_by(
        user_id=g.user_id,
        is_read=False
    ).all()

    now = datetime.utcnow()
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = now

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Marked {len(unread_notifications)} notifications as read'
    }), 200


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@require_auth
def delete_notification(notification_id):
    """Delete a notification."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=g.user_id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    db.session.delete(notification)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Notification deleted'
    }), 200


@notifications_bp.route('/stats', methods=['GET'])
@require_auth
def get_notification_stats():
    """Get notification statistics."""
    total = Notification.query.filter_by(user_id=g.user_id).count()
    unread = Notification.query.filter_by(user_id=g.user_id, is_read=False).count()

    # Get by type
    type_stats = {}
    notification_types = db.session.query(
        Notification.notification_type,
        db.func.count(Notification.id).label('count')
    ).filter_by(user_id=g.user_id).group_by(Notification.notification_type).all()

    for ntype, count in notification_types:
        type_stats[ntype] = count

    return jsonify({
        'status': 'success',
        'data': {
            'total': total,
            'unread': unread,
            'by_type': type_stats
        }
    }), 200


# ============================================================================
# NOTIFICATION BUILDERS (for services)
# ============================================================================

def notify_sns_publish_start(user_id: int, post_id: int, platforms: list) -> None:
    """Notify when SNS publish starts."""
    create_notification(
        user_id=user_id,
        notification_type='sns_publish_start',
        title='Publishing...',
        message=f'Publishing to {", ".join(platforms)}',
        action_url=f'/sns/posts/{post_id}',
        icon='upload',
        metadata={'post_id': post_id, 'platforms': platforms}
    )


def notify_sns_publish_success(user_id: int, post_id: int, platforms: list) -> None:
    """Notify when SNS publish succeeds."""
    create_notification(
        user_id=user_id,
        notification_type='sns_publish_success',
        title='Published Successfully',
        message=f'Your post was published to {", ".join(platforms)}',
        action_url=f'/sns/posts/{post_id}',
        icon='check_circle',
        metadata={'post_id': post_id, 'platforms': platforms}
    )


def notify_sns_publish_failed(user_id: int, post_id: int, platform: str, error: str) -> None:
    """Notify when SNS publish fails."""
    create_notification(
        user_id=user_id,
        notification_type='sns_publish_failed',
        title='Publishing Failed',
        message=f'Failed to publish to {platform}: {error}',
        action_url=f'/sns/posts/{post_id}',
        icon='error',
        metadata={'post_id': post_id, 'platform': platform, 'error': error}
    )


def notify_post_liked(user_id: int, liker_name: str, post_id: int) -> None:
    """Notify when post is liked."""
    create_notification(
        user_id=user_id,
        notification_type='post_liked',
        title='Post Liked',
        message=f'{liker_name} liked your post',
        action_url=f'/sns/posts/{post_id}',
        icon='favorite',
        metadata={'post_id': post_id, 'liker_name': liker_name}
    )


def notify_post_commented(user_id: int, commenter_name: str, post_id: int, comment: str = None) -> None:
    """Notify when post is commented on."""
    create_notification(
        user_id=user_id,
        notification_type='post_commented',
        title='New Comment',
        message=f'{commenter_name} commented: {comment[:100] if comment else ""}',
        action_url=f'/sns/posts/{post_id}',
        icon='comment',
        metadata={'post_id': post_id, 'commenter_name': commenter_name}
    )


def notify_order_status_changed(user_id: int, order_id: int, status: str) -> None:
    """Notify when order status changes."""
    status_messages = {
        'pending': 'Your order is pending',
        'confirmed': 'Your order has been confirmed',
        'shipped': 'Your order has been shipped',
        'delivered': 'Your order has been delivered',
        'cancelled': 'Your order has been cancelled'
    }

    create_notification(
        user_id=user_id,
        notification_type='order_status_changed',
        title='Order Status Updated',
        message=status_messages.get(status, f'Order status: {status}'),
        action_url=f'/orders/{order_id}',
        icon='shopping_cart',
        metadata={'order_id': order_id, 'status': status}
    )


def notify_shipment_update(user_id: int, order_id: int, location: str, carrier: str = None) -> None:
    """Notify about shipment tracking update."""
    create_notification(
        user_id=user_id,
        notification_type='shipment_update',
        title='Shipment Update',
        message=f'Your package is at {location}',
        action_url=f'/orders/{order_id}',
        icon='local_shipping',
        metadata={'order_id': order_id, 'location': location, 'carrier': carrier}
    )


def notify_delivery_confirmed(user_id: int, order_id: int) -> None:
    """Notify when delivery is confirmed."""
    create_notification(
        user_id=user_id,
        notification_type='delivery_confirmed',
        title='Delivery Confirmed',
        message='Your order has been delivered successfully',
        action_url=f'/orders/{order_id}',
        icon='done_all',
        metadata={'order_id': order_id}
    )


def notify_new_message(user_id: int, from_user_name: str, message_preview: str = None) -> None:
    """Notify about new chat message."""
    create_notification(
        user_id=user_id,
        notification_type='new_message',
        title='New Message',
        message=f'{from_user_name}: {message_preview or "sent you a message"}',
        action_url='/chat',
        icon='message',
        metadata={'from_user_name': from_user_name}
    )
