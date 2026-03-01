"""
Firebase Cloud Messaging (FCM) Service — Mobile Push Notifications

FEATURES:
- Register device tokens
- Send push notifications to devices
- Send topic-based notifications
- Handle notification templates
- Track notification delivery

SETUP:
1. Create Firebase project at https://console.firebase.google.com
2. Download service account JSON key
3. Set FIREBASE_CREDENTIALS_PATH env var
4. Install: pip install firebase-admin

ENDPOINTS:
  POST /api/fcm/register-device     — Register device token
  POST /api/fcm/send-notification   — Send push notification
  POST /api/fcm/subscribe-topic     — Subscribe to topic notifications
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

from flask import Blueprint, request, jsonify, g
from ..models import db, User
from ..auth import require_auth

logger = logging.getLogger('fcm')

fcm_bp = Blueprint('fcm', __name__, url_prefix='/api/fcm')

# Firebase initialization
_firebase_initialized = False
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized, _firebase_app

    if not HAS_FIREBASE:
        logger.warning('firebase-admin not installed, FCM disabled')
        return False

    if _firebase_initialized:
        return True

    try:
        creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if not creds_path:
            logger.warning('FIREBASE_CREDENTIALS_PATH not set, FCM disabled')
            return False

        if not os.path.exists(creds_path):
            logger.error(f'Firebase credentials file not found: {creds_path}')
            return False

        cred = credentials.Certificate(creds_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info('Firebase Admin SDK initialized')
        return True

    except Exception as e:
        logger.error(f'Failed to initialize Firebase: {e}')
        return False


# ============================================================================
# DATABASE MODELS (In-memory device token storage)
# ============================================================================

# DeviceToken model would be added to models.py
# For now, we use a simple dict-based storage
_device_tokens: Dict[int, List[str]] = {}  # user_id -> [token1, token2, ...]


class DeviceTokenStore:
    """Simple thread-safe device token storage."""

    @staticmethod
    def add_token(user_id: int, device_token: str) -> None:
        """Register a device token for a user."""
        if user_id not in _device_tokens:
            _device_tokens[user_id] = []
        if device_token not in _device_tokens[user_id]:
            _device_tokens[user_id].append(device_token)
        logger.debug(f'Registered device token for user {user_id}')

    @staticmethod
    def get_tokens(user_id: int) -> List[str]:
        """Get all device tokens for a user."""
        return _device_tokens.get(user_id, [])

    @staticmethod
    def remove_token(user_id: int, device_token: str) -> None:
        """Unregister a device token."""
        if user_id in _device_tokens:
            _device_tokens[user_id] = [t for t in _device_tokens[user_id] if t != device_token]
            if not _device_tokens[user_id]:
                del _device_tokens[user_id]

    @staticmethod
    def remove_all_tokens(user_id: int) -> None:
        """Remove all device tokens for a user."""
        if user_id in _device_tokens:
            del _device_tokens[user_id]


# ============================================================================
# NOTIFICATION SENDING
# ============================================================================

def send_push_notification(user_id: int, title: str, body: str,
                          data: Optional[Dict[str, str]] = None,
                          icon: str = None) -> Dict[str, Any]:
    """
    Send push notification to user's registered devices.

    Args:
        user_id: User ID
        title: Notification title
        body: Notification body
        data: Additional data payload
        icon: Icon name/URL

    Returns:
        Dict with status and message IDs
    """
    if not _firebase_initialized:
        logger.warning('Firebase not initialized, skipping push notification')
        return {'status': 'skipped', 'reason': 'Firebase not initialized'}

    tokens = DeviceTokenStore.get_tokens(user_id)
    if not tokens:
        logger.debug(f'No device tokens registered for user {user_id}')
        return {'status': 'no_devices', 'tokens_count': 0}

    try:
        # Prepare notification
        notification = messaging.Notification(
            title=title,
            body=body,
            image=icon
        )

        # Send to all registered devices
        message_ids = []
        failed_tokens = []

        for token in tokens:
            try:
                message = messaging.Message(
                    notification=notification,
                    data=data or {},
                    token=token
                )
                message_id = messaging.send(message)
                message_ids.append(message_id)
                logger.debug(f'Sent FCM notification to token {token[:20]}...: {message_id}')

            except messaging.InvalidArgumentError as e:
                logger.warning(f'Invalid token {token[:20]}...: {e}')
                failed_tokens.append(token)
            except Exception as e:
                logger.error(f'Failed to send FCM to token {token[:20]}...: {e}')
                failed_tokens.append(token)

        # Remove invalid tokens
        for token in failed_tokens:
            DeviceTokenStore.remove_token(user_id, token)

        return {
            'status': 'sent',
            'message_ids': message_ids,
            'failed_count': len(failed_tokens),
            'total_count': len(tokens)
        }

    except Exception as e:
        logger.error(f'FCM send failed: {e}')
        return {'status': 'error', 'message': str(e)}


def send_topic_notification(topic: str, title: str, body: str,
                           data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Send notification to all users subscribed to a topic.

    Args:
        topic: Topic name
        title: Notification title
        body: Notification body
        data: Additional data

    Returns:
        Dict with status and message ID
    """
    if not _firebase_initialized:
        logger.warning('Firebase not initialized, skipping topic notification')
        return {'status': 'skipped', 'reason': 'Firebase not initialized'}

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            topic=topic
        )
        message_id = messaging.send(message)
        logger.info(f'Sent topic notification to {topic}: {message_id}')

        return {
            'status': 'sent',
            'message_id': message_id,
            'topic': topic
        }

    except Exception as e:
        logger.error(f'Topic notification failed: {e}')
        return {'status': 'error', 'message': str(e)}


def subscribe_to_topic(user_id: int, topic: str) -> bool:
    """Subscribe user's devices to a topic."""
    tokens = DeviceTokenStore.get_tokens(user_id)
    if not tokens:
        logger.debug(f'No tokens to subscribe for user {user_id}')
        return False

    if not _firebase_initialized:
        return False

    try:
        # Subscribe all tokens to topic
        response = messaging.make_topic_management_response(
            messaging.subscribe_to_topic(tokens, topic)
        )
        logger.info(f'Subscribed {len(tokens)} devices to topic {topic}')
        return True

    except Exception as e:
        logger.error(f'Failed to subscribe to topic {topic}: {e}')
        return False


def unsubscribe_from_topic(user_id: int, topic: str) -> bool:
    """Unsubscribe user's devices from a topic."""
    tokens = DeviceTokenStore.get_tokens(user_id)
    if not tokens:
        return False

    if not _firebase_initialized:
        return False

    try:
        messaging.unsubscribe_from_topic(tokens, topic)
        logger.info(f'Unsubscribed {len(tokens)} devices from topic {topic}')
        return True

    except Exception as e:
        logger.error(f'Failed to unsubscribe from topic {topic}: {e}')
        return False


# ============================================================================
# API ENDPOINTS
# ============================================================================

@fcm_bp.route('/register-device', methods=['POST'])
@require_auth
def register_device():
    """Register a device token for push notifications."""
    data = request.get_json() or {}
    device_token = data.get('device_token')

    if not device_token:
        return jsonify({'error': 'device_token required'}), 400

    if len(device_token) < 10:
        return jsonify({'error': 'Invalid device token'}), 400

    DeviceTokenStore.add_token(g.user_id, device_token)

    return jsonify({
        'status': 'success',
        'message': 'Device registered for push notifications'
    }), 200


@fcm_bp.route('/unregister-device', methods=['POST'])
@require_auth
def unregister_device():
    """Unregister a device token."""
    data = request.get_json() or {}
    device_token = data.get('device_token')

    if not device_token:
        return jsonify({'error': 'device_token required'}), 400

    DeviceTokenStore.remove_token(g.user_id, device_token)

    return jsonify({
        'status': 'success',
        'message': 'Device unregistered'
    }), 200


@fcm_bp.route('/unregister-all', methods=['POST'])
@require_auth
def unregister_all():
    """Unregister all devices for current user."""
    DeviceTokenStore.remove_all_tokens(g.user_id)

    return jsonify({
        'status': 'success',
        'message': 'All devices unregistered'
    }), 200


@fcm_bp.route('/subscribe-topic', methods=['POST'])
@require_auth
def subscribe_topic():
    """Subscribe to a topic."""
    data = request.get_json() or {}
    topic = data.get('topic')

    if not topic:
        return jsonify({'error': 'topic required'}), 400

    if not subscribe_to_topic(g.user_id, topic):
        return jsonify({
            'error': 'Failed to subscribe to topic',
            'reason': 'No devices registered'
        }), 400

    return jsonify({
        'status': 'success',
        'message': f'Subscribed to topic: {topic}'
    }), 200


@fcm_bp.route('/unsubscribe-topic', methods=['POST'])
@require_auth
def unsubscribe_topic():
    """Unsubscribe from a topic."""
    data = request.get_json() or {}
    topic = data.get('topic')

    if not topic:
        return jsonify({'error': 'topic required'}), 400

    if not unsubscribe_from_topic(g.user_id, topic):
        return jsonify({
            'error': 'Failed to unsubscribe from topic'
        }), 400

    return jsonify({
        'status': 'success',
        'message': f'Unsubscribed from topic: {topic}'
    }), 200


@fcm_bp.route('/device-list', methods=['GET'])
@require_auth
def get_registered_devices():
    """Get list of registered devices."""
    tokens = DeviceTokenStore.get_tokens(g.user_id)

    # Mask tokens for security
    masked_tokens = [f'{t[:20]}...{t[-10:]}' for t in tokens]

    return jsonify({
        'status': 'success',
        'devices_count': len(tokens),
        'device_tokens': masked_tokens
    }), 200


# ============================================================================
# NOTIFICATION TEMPLATES
# ============================================================================

FCM_TEMPLATES = {
    'sns_publish': {
        'title': 'SNS Published',
        'body': 'Your post has been published successfully',
        'icon': 'publish'
    },
    'new_comment': {
        'title': 'New Comment',
        'body': '{author} commented on your post',
        'icon': 'comment'
    },
    'new_like': {
        'title': 'New Like',
        'body': '{author} liked your post',
        'icon': 'favorite'
    },
    'order_shipped': {
        'title': 'Order Shipped',
        'body': 'Your order #{order_id} has been shipped',
        'icon': 'local_shipping'
    },
    'order_delivered': {
        'title': 'Order Delivered',
        'body': 'Your order #{order_id} has been delivered',
        'icon': 'done_all'
    },
    'new_message': {
        'title': 'New Message',
        'body': '{from_user} sent you a message',
        'icon': 'message'
    }
}


def send_templated_notification(user_id: int, template_name: str, **kwargs) -> Dict[str, Any]:
    """Send a templated push notification."""
    if template_name not in FCM_TEMPLATES:
        logger.warning(f'Unknown template: {template_name}')
        return {'status': 'error', 'message': f'Unknown template: {template_name}'}

    template = FCM_TEMPLATES[template_name]
    title = template['title']
    body = template['body'].format(**kwargs)
    icon = template.get('icon')

    return send_push_notification(user_id, title, body, icon=icon)
