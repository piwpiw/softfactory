"""Telegram Bot integration routes for account linking and notifications."""

from datetime import datetime, timedelta
import logging
import os
import secrets

from flask import Blueprint, jsonify, request, g

from backend.auth import require_auth
from backend.models import db, SNSSettings
from backend.telegram_service import TelegramService, TELEGRAM_BOT_TOKEN

logger = logging.getLogger("telegram_routes")

telegram_bp = Blueprint("telegram", __name__, url_prefix="/api/telegram")

TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "piwpiwtelegrambot").strip()
TELEGRAM_LINK_TTL_MINUTES = int(os.getenv("TELEGRAM_LINK_TTL_MINUTES", "30"))

# Temporary linking token store.
# Token is only used long enough for the user to open Telegram and send /start.
_LINKING_TOKENS = {}


def _mask_chat_id(chat_id):
    value = str(chat_id or "").strip()
    if len(value) <= 4:
        return value or None
    return f"{value[:2]}***{value[-2:]}"


def _purge_expired_tokens(now=None):
    current = now or datetime.utcnow()
    expired = [
        token
        for token, payload in _LINKING_TOKENS.items()
        if payload.get("expires_at") and payload["expires_at"] <= current
    ]
    for token in expired:
        _LINKING_TOKENS.pop(token, None)


def _ensure_sns_settings(user_id):
    sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()
    if not sns_settings:
        sns_settings = SNSSettings(user_id=user_id)
        db.session.add(sns_settings)
    return sns_settings


def _complete_link(token, chat_id):
    _purge_expired_tokens()
    token_data = _LINKING_TOKENS.get(token)
    if not token_data:
        return None, "invalid_or_expired"

    user_id = token_data["user_id"]
    sns_settings = _ensure_sns_settings(user_id)
    sns_settings.telegram_chat_id = str(chat_id)
    sns_settings.telegram_enabled = True
    db.session.commit()

    _LINKING_TOKENS[token]["linked_chat_id"] = str(chat_id)
    _LINKING_TOKENS[token]["linked_at"] = datetime.utcnow()
    _LINKING_TOKENS[token]["status"] = "linked"

    return user_id, None


@telegram_bp.route("/link-account", methods=["GET"])
@require_auth
def link_account():
    """Generate a Telegram deep-link for the current user."""
    try:
        user_id = g.user_id
        _purge_expired_tokens()

        token = f"user_{user_id}_{secrets.token_urlsafe(18)}"
        expires_at = datetime.utcnow() + timedelta(minutes=TELEGRAM_LINK_TTL_MINUTES)
        _LINKING_TOKENS[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "linked_chat_id": None,
            "linked_at": None,
            "status": "pending",
        }

        linking_url = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={token}"

        logger.info("[TELEGRAM] Generated linking URL for user %s", user_id)

        return jsonify({
            "status": "success",
            "linking_url": linking_url,
            "token": token,
            "bot_username": TELEGRAM_BOT_USERNAME,
            "expires_at": expires_at.isoformat(),
            "instructions": (
                "링크를 눌러 Telegram bot을 열고 /start를 보내세요. "
                "메시지를 보내면 이 페이지에서 새로고침 없이도 연결 상태를 확인할 수 있습니다."
            ),
        }), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Error generating linking URL: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@telegram_bp.route("/verify-link", methods=["POST"])
def verify_link():
    """Manual fallback endpoint to complete a Telegram link using token + chat_id."""
    try:
        data = request.get_json() or {}
        token = str(data.get("token", "")).strip()
        chat_id = str(data.get("chat_id", "")).strip()

        if not token or not chat_id:
            return jsonify({"error": "Missing token or chat_id"}), 400

        user_id, error = _complete_link(token, chat_id)
        if error:
            return jsonify({"error": "Invalid or expired token"}), 400

        TelegramService.send_message(
            chat_id,
            "<b>Telegram 연동이 완료되었습니다.</b>\n\n이제 SNS 게시 성공/실패 알림을 Telegram으로 받을 수 있습니다.",
            parse_mode="HTML",
        )

        logger.info("[TELEGRAM] Completed manual link for user %s", user_id)
        return jsonify({
            "status": "success",
            "message": "Telegram account linked successfully",
            "telegram_enabled": True,
        }), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Error verifying link: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@telegram_bp.route("/status", methods=["GET"])
@require_auth
def telegram_status():
    """Get Telegram connection status for the current user."""
    try:
        user_id = g.user_id
        _purge_expired_tokens()

        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()
        pending_token = next(
            (
                {"token": token, **payload}
                for token, payload in _LINKING_TOKENS.items()
                if payload.get("user_id") == user_id and payload.get("status") == "pending"
            ),
            None,
        )

        if not sns_settings or not sns_settings.telegram_enabled or not sns_settings.telegram_chat_id:
            response = {
                "telegram_enabled": False,
                "bot_configured": bool(TELEGRAM_BOT_USERNAME),
                "bot_can_send": bool(TELEGRAM_BOT_TOKEN),
                "bot_username": TELEGRAM_BOT_USERNAME,
                "message": "Telegram account not linked.",
            }
            if pending_token:
                response["link_pending"] = True
                response["pending_expires_at"] = pending_token["expires_at"].isoformat()
            return jsonify(response), 200

        return jsonify({
            "telegram_enabled": True,
            "bot_configured": bool(TELEGRAM_BOT_USERNAME),
            "bot_can_send": bool(TELEGRAM_BOT_TOKEN),
            "bot_username": TELEGRAM_BOT_USERNAME,
            "telegram_chat_id": sns_settings.telegram_chat_id,
            "masked_chat_id": _mask_chat_id(sns_settings.telegram_chat_id),
            "linked_at": sns_settings.created_at.isoformat() if sns_settings.created_at else None,
            "message": "Telegram account linked.",
        }), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Error getting status: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@telegram_bp.route("/unlink-account", methods=["POST"])
@require_auth
def unlink_account():
    """Disconnect Telegram notifications for the current user."""
    try:
        user_id = g.user_id
        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()
        if not sns_settings:
            return jsonify({"error": "SNSSettings not found"}), 404

        sns_settings.telegram_chat_id = None
        sns_settings.telegram_enabled = False
        db.session.commit()

        for token, payload in list(_LINKING_TOKENS.items()):
            if payload.get("user_id") == user_id:
                _LINKING_TOKENS.pop(token, None)

        logger.info("[TELEGRAM] Unlinked Telegram account for user %s", user_id)
        return jsonify({
            "status": "success",
            "message": "Telegram account unlinked successfully",
        }), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Error unlinking account: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@telegram_bp.route("/send-test-message", methods=["POST"])
@require_auth
def send_test_message():
    """Send a test Telegram message to the current user."""
    try:
        user_id = g.user_id
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({"error": "Telegram bot token is not configured on the server"}), 503

        sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()
        if not sns_settings or not sns_settings.telegram_enabled or not sns_settings.telegram_chat_id:
            return jsonify({"error": "Telegram not enabled for this user"}), 400

        success = TelegramService.send_message(
            sns_settings.telegram_chat_id,
            "<b>테스트 메시지</b>\n\nTelegram 연동이 정상적으로 동작합니다.",
            parse_mode="HTML",
        )
        if not success:
            return jsonify({"error": "Failed to send test message"}), 500

        logger.info("[TELEGRAM] Test message sent to user %s", user_id)
        return jsonify({
            "status": "success",
            "message": "Test message sent successfully",
        }), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Error sending test message: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@telegram_bp.route("/webhook", methods=["POST"])
def telegram_webhook():
    """Handle Telegram bot updates for /start deep-link account linking."""
    try:
        data = request.get_json() or {}
        message = data.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = str(message.get("text") or "").strip()

        if not chat_id or not text.startswith("/start"):
            return jsonify({"status": "ignored"}), 200

        parts = text.split(maxsplit=1)
        token = parts[1].strip() if len(parts) > 1 else ""
        if not token:
            TelegramService.send_message(
                str(chat_id),
                "<b>연동 토큰이 없습니다.</b>\n\nSoftFactory에서 다시 연결 링크를 생성해 주세요.",
                parse_mode="HTML",
            )
            return jsonify({"status": "missing_token"}), 200

        user_id, error = _complete_link(token, chat_id)
        if error:
            TelegramService.send_message(
                str(chat_id),
                "<b>연결 링크가 만료되었거나 유효하지 않습니다.</b>\n\nSoftFactory 설정 화면에서 새 링크를 다시 생성해 주세요.",
                parse_mode="HTML",
            )
            return jsonify({"status": "invalid_token"}), 200

        TelegramService.send_message(
            str(chat_id),
            "<b>SoftFactory Telegram 연동이 완료되었습니다.</b>\n\n이제 SNS 자동화 알림을 이 채팅에서 받을 수 있습니다.",
            parse_mode="HTML",
        )

        logger.info("[TELEGRAM] Webhook linked chat %s to user %s", chat_id, user_id)
        return jsonify({"status": "linked"}), 200
    except Exception as exc:
        logger.error("[TELEGRAM] Webhook error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500
