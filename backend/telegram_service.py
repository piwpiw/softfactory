"""Telegram Bot Service — Send SNS notifications via Telegram.

Handles:
  - Account linking (URL generation & verification)
  - Telegram notifications (post success/failure, daily summaries)
  - Message formatting with emojis
"""

import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger('telegram_service')

# Telegram Bot API endpoint
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'


class TelegramService:
    """Service for sending Telegram notifications to users."""

    @staticmethod
    def send_message(chat_id: str, text: str, parse_mode: str = 'HTML') -> bool:
        """Send a message via Telegram Bot API.

        Args:
            chat_id: Telegram chat ID
            text: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'

        Returns:
            True if successful, False otherwise
        """
        if not TELEGRAM_BOT_TOKEN or not chat_id:
            logger.warning(f'[TELEGRAM] Missing token or chat_id: {chat_id}')
            return False

        try:
            url = f'{TELEGRAM_API_URL}/sendMessage'
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f'[TELEGRAM] Message sent to {chat_id}')
                return True
            else:
                logger.error(f'[TELEGRAM] Failed to send message: {response.status_code} - {response.text}')
                return False

        except Exception as e:
            logger.error(f'[TELEGRAM] Error sending message: {e}')
            return False

    @staticmethod
    def notify_post_success(chat_id: str, platform: str, post_content: str, likes: int = 0, comments: int = 0, post_url: str = '') -> bool:
        """Send SNS post success notification.

        Format:
        ✅ SNS 게시 완료
        📱 Instagram: [링크]
        👥 좋아요: 1,234 | 댓글: 56
        """
        emoji_map = {
            'instagram': '📸',
            'twitter': '𝕏',
            'facebook': 'f',
            'linkedin': '🔗',
            'tiktok': '🎵',
            'youtube': '▶️',
            'threads': '🧵',
        }

        emoji = emoji_map.get(platform.lower(), '📱')

        message = f"""✅ <b>SNS 게시 완료</b>

{emoji} <b>{platform.title()}</b>
📝 <code>{post_content[:100]}{'...' if len(post_content) > 100 else ''}</code>"""

        if post_url:
            message += f'\n🔗 <a href="{post_url}">게시물 보기</a>'

        if likes > 0 or comments > 0:
            message += f'\n👥 좋아요: {likes:,} | 댓글: {comments:,}'

        message += f'\n⏰ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC'

        return TelegramService.send_message(chat_id, message, parse_mode='HTML')

    @staticmethod
    def notify_post_failure(chat_id: str, platform: str, error_message: str) -> bool:
        """Send SNS post failure notification."""
        message = f"""❌ <b>SNS 게시 실패</b>

📱 플랫폼: {platform.title()}
⚠️ 오류: <code>{error_message[:200]}</code>
⏰ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC

<i>자세한 내용은 대시보드에서 확인하세요.</i>"""

        return TelegramService.send_message(chat_id, message, parse_mode='HTML')

    @staticmethod
    def notify_daily_summary(chat_id: str, summary_data: Dict[str, Any]) -> bool:
        """Send daily SNS summary report.

        summary_data structure:
        {
            'total_posts': int,
            'successful_posts': int,
            'failed_posts': int,
            'total_engagement': int,
            'platforms': {
                'instagram': {'posts': int, 'likes': int, 'comments': int},
                ...
            }
        }
        """
        message = f"""📊 <b>일일 SNS 리포트</b>

📝 게시물: {summary_data.get('total_posts', 0)}개
✅ 성공: {summary_data.get('successful_posts', 0)}개
❌ 실패: {summary_data.get('failed_posts', 0)}개
👥 총 참여: {summary_data.get('total_engagement', 0):,}

"""

        # Add per-platform stats
        platforms = summary_data.get('platforms', {})
        if platforms:
            message += '<b>플랫폼별 통계:</b>\n'
            emoji_map = {
                'instagram': '📸',
                'twitter': '𝕏',
                'facebook': 'f',
                'linkedin': '🔗',
                'tiktok': '🎵',
            }
            for platform, stats in platforms.items():
                emoji = emoji_map.get(platform.lower(), '📱')
                message += f'{emoji} {platform.title()}: {stats.get("posts", 0)} 게시 | 👥 {stats.get("engagement", 0):,}\n'

        message += f'\n⏰ {datetime.utcnow().strftime("%Y-%m-%d")}'

        return TelegramService.send_message(chat_id, message, parse_mode='HTML')

    @staticmethod
    def notify_automation_executed(chat_id: str, automation_name: str, platforms: list, execution_time: str = None) -> bool:
        """Notify user when SNS automation rule is executed."""
        platforms_text = ', '.join([p.title() for p in platforms]) if platforms else 'Unknown'

        message = f"""🤖 <b>자동화 규칙 실행</b>

📋 규칙: <b>{automation_name}</b>
📱 플랫폼: {platforms_text}
✅ 상태: 완료"""

        if execution_time:
            message += f'\n⏰ 실행 시간: {execution_time}'

        message += f'\n📅 {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC'

        return TelegramService.send_message(chat_id, message, parse_mode='HTML')

    @staticmethod
    def send_link_account_url(chat_id: str, link_url: str) -> bool:
        """Send account linking URL to user."""
        message = f"""🔗 <b>Telegram 계정 연동</b>

아래 버튼을 클릭하여 계정을 연동하세요:

<a href="{link_url}">계정 연동하기</a>

또는 직접 이 URL을 열기:
<code>{link_url}</code>

연동 후에는 SNS 게시물 성공/실패 알림을 Telegram에서 받을 수 있습니다."""

        return TelegramService.send_message(chat_id, message, parse_mode='HTML')


def send_sns_notification(user_id: int, notification_type: str, data: Dict[str, Any]) -> bool:
    """High-level function to send SNS notifications based on type.

    Types:
      - post_success: SNS post published successfully
      - post_failure: SNS post publication failed
      - automation_executed: Automation rule executed
      - daily_summary: Daily report
    """
    from backend.models import db, SNSSettings

    # Get user's Telegram settings
    sns_settings = SNSSettings.query.filter_by(user_id=user_id).first()

    if not sns_settings or not sns_settings.telegram_enabled or not sns_settings.telegram_chat_id:
        logger.debug(f'[TELEGRAM] Telegram not enabled for user {user_id}')
        return False

    chat_id = sns_settings.telegram_chat_id

    try:
        if notification_type == 'post_success':
            return TelegramService.notify_post_success(
                chat_id,
                data.get('platform', 'unknown'),
                data.get('content', ''),
                data.get('likes', 0),
                data.get('comments', 0),
                data.get('post_url', ''),
            )
        elif notification_type == 'post_failure':
            return TelegramService.notify_post_failure(
                chat_id,
                data.get('platform', 'unknown'),
                data.get('error', 'Unknown error'),
            )
        elif notification_type == 'automation_executed':
            return TelegramService.notify_automation_executed(
                chat_id,
                data.get('automation_name', 'Unknown'),
                data.get('platforms', []),
                data.get('execution_time', None),
            )
        elif notification_type == 'daily_summary':
            return TelegramService.notify_daily_summary(chat_id, data)
        else:
            logger.warning(f'[TELEGRAM] Unknown notification type: {notification_type}')
            return False

    except Exception as e:
        logger.error(f'[TELEGRAM] Error in send_sns_notification: {e}', exc_info=True)
        return False
