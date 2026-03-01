"""Alert Service — Telegram notifications for critical production events.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables.
If either is missing the service logs a warning and every ``send_alert``
call becomes a no-op so the rest of the application is unaffected.

Usage:
    from backend.services.alert_service import alert_service

    alert_service.send_alert('Title', 'Details', level='error')
    alert_service.alert_high_error_rate(150, 60)
    alert_service.alert_payment_failed(user_id=7, amount=9900, error='card_declined')
"""

import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Emoji prefixes for each severity level
_LEVEL_EMOJI = {
    'info':     'ℹ️',
    'warning':  '⚠️',
    'error':    '🔴',
    'critical': '🚨',
    'success':  '✅',
}

_TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'


class AlertService:
    """Send structured alerts to a Telegram chat."""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        self.chat_id   = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        self._enabled  = bool(self.bot_token and self.chat_id)
        if not self._enabled:
            logger.warning(
                'AlertService: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — '
                'Telegram alerts are disabled.'
            )

    # ------------------------------------------------------------------
    # Core send method
    # ------------------------------------------------------------------

    def send_alert(self, title: str, message: str, level: str = 'info') -> bool:
        """Send a formatted alert to the configured Telegram chat.

        Args:
            title:   Short summary shown in bold.
            message: Detailed description (Markdown supported).
            level:   One of 'info', 'warning', 'error', 'critical', 'success'.

        Returns:
            True if the message was delivered, False otherwise.
        """
        if not self._enabled:
            logger.debug(f'[AlertService] Alert suppressed (no Telegram config): {title}')
            return False

        emoji = _LEVEL_EMOJI.get(level.lower(), 'ℹ️')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        text = (
            f'{emoji} *[SoftFactory] {title}*\n'
            f'```\n{message}\n```\n'
            f'_Level: {level.upper()} | {timestamp}_'
        )

        try:
            url = _TELEGRAM_API.format(token=self.bot_token)
            resp = requests.post(
                url,
                json={
                    'chat_id':    self.chat_id,
                    'text':       text,
                    'parse_mode': 'Markdown',
                },
                timeout=5,  # Never block requests for longer than 5 s
            )
            if not resp.ok:
                logger.warning(
                    f'AlertService: Telegram API error {resp.status_code}: {resp.text[:200]}'
                )
                return False
            return True
        except requests.exceptions.Timeout:
            logger.warning('AlertService: Telegram request timed out')
            return False
        except Exception as exc:
            logger.warning(f'AlertService: Failed to send alert — {exc}')
            return False

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    def alert_high_error_rate(self, error_count: int, window_seconds: int) -> bool:
        """Alert when the HTTP 5xx error rate is abnormally high.

        Args:
            error_count:    Number of errors observed in the window.
            window_seconds: Length of the sliding window in seconds.
        """
        rate_per_min = round(error_count / max(window_seconds / 60, 1), 1)
        return self.send_alert(
            title='High Error Rate Detected',
            message=(
                f'Errors in last {window_seconds}s: {error_count}\n'
                f'Rate: ~{rate_per_min} errors/min\n'
                f'Action: Check /api/admin/metrics and application logs.'
            ),
            level='error',
        )

    def alert_slow_response(self, endpoint: str, avg_ms: float) -> bool:
        """Alert when an endpoint average response time exceeds the SLA.

        Args:
            endpoint: Flask endpoint name or URL path.
            avg_ms:   Average response time in milliseconds.
        """
        return self.send_alert(
            title='Slow Response Detected',
            message=(
                f'Endpoint : {endpoint}\n'
                f'Avg time : {avg_ms:.0f} ms  (SLA: 1 000 ms)\n'
                f'Action   : Check DB queries and CPU load.'
            ),
            level='warning',
        )

    def alert_db_connection_failed(self) -> bool:
        """Alert when the database becomes unreachable."""
        return self.send_alert(
            title='Database Connection Failed',
            message=(
                'The application cannot reach the database.\n'
                'Health endpoint is returning 503.\n'
                'Action: Verify DB process and connection string.'
            ),
            level='critical',
        )

    def alert_payment_failed(self, user_id: int, amount: int, error: str) -> bool:
        """Alert when a payment processing error occurs.

        Args:
            user_id: Internal user ID (never include email / PII here).
            amount:  Amount in smallest currency unit (e.g. Korean Won).
            error:   Error code or short description from the payment gateway.
        """
        return self.send_alert(
            title='Payment Processing Failed',
            message=(
                f'User ID : {user_id}\n'
                f'Amount  : ₩{amount:,}\n'
                f'Error   : {error}\n'
                f'Action  : Review Stripe dashboard and payment logs.'
            ),
            level='error',
        )

    def alert_deployment(self, version: str, environment: str, success: bool) -> bool:
        """Alert on deployment completion.

        Args:
            version:     Application version string (e.g. '1.2.3').
            environment: Target environment ('production', 'staging', …).
            success:     Whether the deployment succeeded.
        """
        level = 'success' if success else 'critical'
        status_text = 'SUCCEEDED' if success else 'FAILED'
        return self.send_alert(
            title=f'Deployment {status_text}',
            message=(
                f'Version     : {version}\n'
                f'Environment : {environment}\n'
                f'Status      : {status_text}\n'
                + ('' if success else 'Action: Roll back immediately and check deploy logs.')
            ),
            level=level,
        )


# Module-level singleton — import and use directly.
alert_service = AlertService()
