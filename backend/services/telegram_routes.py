"""Telegram Bot Integration Routes — Account linking & notifications.

Endpoints:
  - GET /api/telegram/link-account → Generate linking URL
  - POST /api/telegram/verify-link → Verify & save chat_id
  - GET /api/telegram/status → Check Telegram connection status
"""

import logging
import os
import secrets
from flask import Blueprint, jsonify, request
from backend.models import db, SNSSettings, User
from backend.auth import require_auth
from backend.telegram_service import TelegramService

logger = logging.getLogger('telegram_routes')

telegram_bp = Blueprint('telegram', __name__, url_prefix='/api/telegram')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_USERNAME = 'piwpiwtelegrambot'  # Replace with actual bot username

# In-memory store of linking tokens (user_id -> token)
# In production, use Redis or database
_LINKING_TOKENS = {}


@telegram_bp.route('/link-account', methods=['GET'])
@require_auth
def link_account():
    """Generate Telegram account linking URL.

    Returns a URL that user can visit to link their Telegram account.
    User clicks the link, opens Telegram, and sends a message.

    Response:
    {
        "status": "success",
        "linking_url": "https://t.me/piwpiwtelegrambot?start=user_abc123",
        "token": "user_abc123",
        "instructions": "Click the link to open Telegram and send /start"
    }
    """
    try:
        user_id = request.g.user_id

        # Generate a unique linking token
        token = f"user_{user_id}_{secrets.token_hex(16)}"
        _LINKING_TOKENS[token] = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
        }

        # Telegram deep link
        linking_url = f'https://t.me/{TELEGRAM_BOT_USERNAME}?start={token}'

        logger.info(f'[TELEGRAM] Generated linking URL for user {user_id}: {token}')

        return jsonify({
            'status': 'success',
            'linking_url': linking_url,
            'token': token,
            'instructions': 'Click the link to open Telegram and send /start to the bot to complete linking.',
            'bot_username': TELEGRAM_BOT_USERNAME,
        }), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Error generating linking URL: {e}')
        return jsonify({'error': str(e)}), 500


@telegram_bp.route('/verify-link', methods=['POST'])
@require_auth
def verify_link():
    """Verify Telegram chat_id and save to SNSSettings.

    Expected request body:
    {
        "token": "user_abc123...",
        "chat_id": "7910169750"
    }

    This endpoint is called after user sends /start to the Telegram bot.
    The bot verifies the token and calls this endpoint with the user's chat_id.

    Response:
    {
        "status": "success",
        "message": "Telegram account linked successfully",
        "telegram_enabled": true
    }
    """
    try:
        user_id = request.g.user_id
        data = request.get_json() or {}

        token = data.get('token', '')
        chat_id = data.get('chat_id', '')

        if not token or not chat_id:
            return jsonify({'error': 'Missing token or chat_id'}), 400

        # Verify token
        if token not in _LINKING_TOKENS:
            logger.warning(f'[TELEGRAM] Invalid linking token: {token}')
            return jsonify({'error': 'Invalid or expired token'}), 400

        token_data = _LINKING_TOKENS[token]

        # Verify token belongs to this user
        if token_data['user_id'] != user_id:
            logger.warning(f'[TELEGRAM] Token user mismatch: {user_id} vs {token_data["user_id"]}')
            return jsonify({'error': 'Token does not belong to this user'}), 403

        # Get or create SNSSettings
        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()
        if not sns_settings:
            sns_settings = SNSSettings(user_id=user_id)
            db.session.add(sns_settings)

        # Save chat_id and enable Telegram notifications
        sns_settings.telegram_chat_id = chat_id
        sns_settings.telegram_enabled = True

        db.session.commit()

        # Clean up token
        del _LINKING_TOKENS[token]

        # Send confirmation message to user
        TelegramService.send_message(
            chat_id,
            '✅ <b>계정이 연동되었습니다!</b>\n\n'
            'SNS 게시물 성공/실패 알림을 Telegram에서 받을 수 있습니다.',
            parse_mode='HTML'
        )

        logger.info(f'[TELEGRAM] Successfully linked account for user {user_id}: {chat_id}')

        return jsonify({
            'status': 'success',
            'message': 'Telegram account linked successfully',
            'telegram_enabled': True,
        }), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Error verifying link: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@telegram_bp.route('/status', methods=['GET'])
@require_auth
def telegram_status():
    """Get Telegram connection status for current user.

    Response:
    {
        "telegram_enabled": true,
        "telegram_chat_id": "7910169750",
        "linked_at": "2026-02-26T10:30:00"
    }

    If not linked:
    {
        "telegram_enabled": false,
        "message": "Telegram account not linked. Use /link-account endpoint."
    }
    """
    try:
        user_id = request.g.user_id

        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()

        if not sns_settings or not sns_settings.telegram_enabled:
            return jsonify({
                'telegram_enabled': False,
                'message': 'Telegram account not linked. Use /link-account endpoint to connect.',
            }), 200

        return jsonify({
            'telegram_enabled': True,
            'telegram_chat_id': sns_settings.telegram_chat_id,
            'linked_at': sns_settings.created_at.isoformat() if sns_settings.created_at else None,
        }), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Error getting status: {e}')
        return jsonify({'error': str(e)}), 500


@telegram_bp.route('/unlink-account', methods=['POST'])
@require_auth
def unlink_account():
    """Unlink Telegram account from SNSSettings.

    Response:
    {
        "status": "success",
        "message": "Telegram account unlinked successfully"
    }
    """
    try:
        user_id = request.g.user_id

        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()

        if not sns_settings:
            return jsonify({'error': 'SNSSettings not found'}), 404

        sns_settings.telegram_chat_id = None
        sns_settings.telegram_enabled = False

        db.session.commit()

        logger.info(f'[TELEGRAM] Unlinked Telegram account for user {user_id}')

        return jsonify({
            'status': 'success',
            'message': 'Telegram account unlinked successfully',
        }), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Error unlinking account: {e}')
        return jsonify({'error': str(e)}), 500


@telegram_bp.route('/send-test-message', methods=['POST'])
@require_auth
def send_test_message():
    """Send a test message to verify Telegram connection.

    Response:
    {
        "status": "success",
        "message": "Test message sent successfully"
    }
    """
    try:
        user_id = request.g.user_id

        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()

        if not sns_settings or not sns_settings.telegram_enabled:
            return jsonify({'error': 'Telegram not enabled for this user'}), 400

        chat_id = sns_settings.telegram_chat_id

        # Send test message
        success = TelegramService.send_message(
            chat_id,
            '🧪 <b>테스트 메시지</b>\n\n'
            'Telegram 연동이 정상적으로 작동합니다! ✅',
            parse_mode='HTML'
        )

        if not success:
            return jsonify({'error': 'Failed to send test message'}), 500

        logger.info(f'[TELEGRAM] Test message sent to user {user_id}')

        return jsonify({
            'status': 'success',
            'message': 'Test message sent successfully',
        }), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Error sending test message: {e}')
        return jsonify({'error': str(e)}), 500


# Webhook endpoint for receiving messages from Telegram bot
# (Not needed if using polling; implement if using webhook mode)
@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Receive updates from Telegram Bot API (if webhook mode is enabled).

    This is called by Telegram when user sends a message to the bot.
    """
    try:
        data = request.get_json() or {}

        # Handle /start command from new users
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            if text.startswith('/start'):
                # Extract token from message
                parts = text.split()
                if len(parts) > 1:
                    token = parts[1]
                    # Send response message with verification endpoint
                    TelegramService.send_message(
                        chat_id,
                        '🔗 <b>계정 연동 중...</b>\n\n'
                        '이 메시지를 받으셨다면 계정 연동이 거의 완료되었습니다. '
                        '대시보드로 돌아가 연동을 완료해주세요.',
                        parse_mode='HTML'
                    )

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f'[TELEGRAM] Webhook error: {e}')
        return jsonify({'error': str(e)}), 500


# Add this import at the top
from datetime import datetime
