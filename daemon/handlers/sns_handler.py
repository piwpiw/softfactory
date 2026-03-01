"""
T13: Telegram SNS Handler — Real-time SNS Automation Status Alerts
Sends post status, analytics, and alerts via Telegram bot
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.app import app, db
from backend.models import (
    SNSPost, SNSAccount, SNSAnalytics, SNSInboxMessage, User
)


class SNSHandler:
    """Handle SNS-related Telegram commands and notifications"""

    def __init__(self, telegram_api_token: str, chat_id: int):
        self.telegram_api_token = telegram_api_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{telegram_api_token}"

    # ============ TELEGRAM SEND ============

    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send message to Telegram chat

        Args:
            text: Message content (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'

        Returns:
            True if successful
        """
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[SNS_HANDLER] Send failed: {e}")
            return False

    def send_notification(self, title: str, message: str, status: str = 'info') -> bool:
        """
        Send formatted notification

        Args:
            title: Notification title
            message: Notification message
            status: 'info', 'success', 'warning', 'error'

        Returns:
            True if successful
        """
        icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        icon = icons.get(status, 'ℹ️')
        text = f"<b>{icon} {title}</b>\n{message}"
        return self.send_message(text)

    # ============ SNS STATUS COMMANDS ============

    def cmd_sns_status(self, user_id: Optional[int] = None) -> bool:
        """
        /sns-status - Show today's SNS status
        Lists scheduled posts, published posts, pending actions
        """
        try:
            with app.app_context():
                today = datetime.utcnow().date()
                start_of_day = datetime.combine(today, datetime.min.time())
                end_of_day = datetime.combine(today, datetime.max.time())

                # Get today's posts by status
                published = SNSPost.query.filter(
                    SNSPost.status == 'published',
                    SNSPost.published_at >= start_of_day,
                    SNSPost.published_at <= end_of_day
                ).count()

                scheduled = SNSPost.query.filter(
                    SNSPost.status == 'scheduled',
                    SNSPost.scheduled_at >= start_of_day,
                    SNSPost.scheduled_at <= end_of_day
                ).count()

                failed = SNSPost.query.filter(
                    SNSPost.status == 'failed',
                    SNSPost.created_at >= start_of_day
                ).count()

                # Get unread messages
                unread_messages = SNSInboxMessage.query.filter(
                    SNSInboxMessage.status == 'unread'
                ).count()

                # Format message
                status_text = f"""<b>📊 SNS Status Report - {today.strftime('%Y-%m-%d')}</b>

<b>Today's Activity:</b>
✅ Published: {published} posts
📅 Scheduled: {scheduled} posts
❌ Failed: {failed} posts

<b>Messages:</b>
💬 Unread: {unread_messages} messages

<b>Connected Accounts:</b>
"""
                # Add account details
                accounts = SNSAccount.query.filter(SNSAccount.is_active == True).all()
                for acc in accounts:
                    status_text += f"\n• {acc.platform.upper()}: @{acc.account_name} ({acc.followers_count} followers)"

                if not accounts:
                    status_text += "\n• No connected accounts"

                return self.send_message(status_text)
        except Exception as e:
            print(f"[SNS_HANDLER] Status command failed: {e}")
            return self.send_notification(
                'Error',
                f'Failed to get SNS status: {str(e)}',
                'error'
            )

    def cmd_sns_analytics(self, days: int = 7, user_id: Optional[int] = None) -> bool:
        """
        /sns-analytics - Show last 7 days of analytics
        Displays engagement, reach, and growth metrics
        """
        try:
            with app.app_context():
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

                # Get analytics
                total_posts = SNSPost.query.filter(
                    SNSPost.status == 'published',
                    SNSPost.published_at >= start_date
                ).count()

                total_engagement = db.session.query(
                    db.func.sum(SNSPost.likes_count)
                ).filter(
                    SNSPost.published_at >= start_date
                ).scalar() or 0

                total_reach = db.session.query(
                    db.func.sum(SNSPost.reach)
                ).filter(
                    SNSPost.published_at >= start_date
                ).scalar() or 0

                # Get top post
                top_post = SNSPost.query.filter(
                    SNSPost.published_at >= start_date
                ).order_by(SNSPost.likes_count.desc()).first()

                # Format message
                analytics_text = f"""<b>📈 SNS Analytics (Last {days} Days)</b>

<b>Overview:</b>
📱 Total Posts: {total_posts}
❤️ Total Engagement: {total_engagement:,}
📊 Total Reach: {total_reach:,}

<b>Average per Post:</b>
• Engagement: {total_engagement // max(total_posts, 1)} per post
• Reach: {total_reach // max(total_posts, 1)} per post

<b>Top Performing Post:</b>
"""
                if top_post:
                    analytics_text += f"""
• Content: {top_post.content[:60]}...
• Platform: {top_post.platform.upper()}
• Likes: {top_post.likes_count}
• Reach: {top_post.reach}
"""
                else:
                    analytics_text += "\n• No posts published in this period"

                return self.send_message(analytics_text)
        except Exception as e:
            print(f"[SNS_HANDLER] Analytics command failed: {e}")
            return self.send_notification(
                'Error',
                f'Failed to get analytics: {str(e)}',
                'error'
            )

    # ============ SNS EVENT NOTIFICATIONS ============

    def notify_post_published(self, post_id: int, platform: str, account_name: str) -> bool:
        """
        Notify when post is published successfully

        Args:
            post_id: Post ID
            platform: SNS platform
            account_name: Account name
        """
        text = f"""<b>✅ Post Published</b>

Platform: <b>{platform.upper()}</b>
Account: <b>{account_name}</b>
Post ID: <code>{post_id}</code>
Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}

Monitoring engagement...
"""
        return self.send_message(text)

    def notify_post_failed(self, post_id: int, platform: str, error: str) -> bool:
        """
        Notify when post fails to publish

        Args:
            post_id: Post ID
            platform: SNS platform
            error: Error message
        """
        text = f"""<b>❌ Post Publishing Failed</b>

Platform: <b>{platform.upper()}</b>
Post ID: <code>{post_id}</code>
Error: <code>{error[:100]}</code>

<b>Action Required:</b>
Review and retry post manually or fix credentials.
"""
        return self.send_notification(
            'Post Failed',
            text,
            'error'
        )

    def notify_new_message(self, sender: str, message_type: str, preview: str) -> bool:
        """
        Notify new SNS message (DM, comment, mention)

        Args:
            sender: Sender name
            message_type: 'dm', 'comment', 'mention'
            preview: Message preview
        """
        icons = {
            'dm': '💬',
            'comment': '💭',
            'mention': '👋'
        }
        icon = icons.get(message_type, '📨')

        text = f"""<b>{icon} New Message</b>

From: <b>{sender}</b>
Type: {message_type.upper()}

<b>Message:</b>
{preview[:150]}

💡 Use /sns-status to see all messages
"""
        return self.send_message(text)

    def notify_engagement_milestone(self, account: str, metric: str, value: int, threshold: int) -> bool:
        """
        Notify when engagement reaches milestone

        Args:
            account: Account name
            metric: 'followers', 'engagement', 'reach'
            value: Current value
            threshold: Milestone threshold
        """
        text = f"""<b>🎉 Engagement Milestone</b>

Account: <b>{account}</b>
Metric: {metric.upper()}
Value: <code>{value:,}</code>
Milestone: <code>{threshold:,}</code>

Keep up the great work! 🚀
"""
        return self.send_notification(
            'Milestone Reached',
            text,
            'success'
        )

    def notify_token_expiring(self, platform: str, account: str, days_left: int) -> bool:
        """
        Notify when OAuth token is about to expire

        Args:
            platform: SNS platform
            account: Account name
            days_left: Days until expiration
        """
        text = f"""<b>⚠️ Token Expiring Soon</b>

Platform: <b>{platform.upper()}</b>
Account: <b>{account}</b>
Days Left: <code>{days_left}</code>

⏰ Action Required: Reconnect account to continue posting
Use /accounts in SNS Auto to reconnect.
"""
        return self.send_notification(
            'Token Expiring',
            text,
            'warning'
        )

    # ============ SCHEDULED REPORTS ============

    def send_daily_summary(self) -> bool:
        """
        Send daily summary report
        Called once per day
        """
        return self.cmd_sns_status()

    def send_weekly_analytics(self) -> bool:
        """
        Send weekly analytics report
        Called once per week
        """
        return self.cmd_sns_analytics(days=7)

    def send_monthly_performance(self) -> bool:
        """
        Send monthly performance report
        Called once per month
        """
        return self.cmd_sns_analytics(days=30)


# ============ GLOBAL HANDLER INSTANCE ============

# These will be initialized by daemon_service.py
_sns_handler: Optional[SNSHandler] = None


def init_sns_handler(telegram_api_token: str, chat_id: int):
    """Initialize SNS handler"""
    global _sns_handler
    _sns_handler = SNSHandler(telegram_api_token, chat_id)
    print(f"[SNS_HANDLER] Initialized for chat {chat_id}")


def get_sns_handler() -> Optional[SNSHandler]:
    """Get SNS handler instance"""
    return _sns_handler


# ============ EVENT HOOKS FOR SCHEDULER ============

def on_post_published(post_id: int, platform: str, account_name: str):
    """Called when post is published by scheduler"""
    if _sns_handler:
        _sns_handler.notify_post_published(post_id, platform, account_name)


def on_post_failed(post_id: int, platform: str, error: str):
    """Called when post publishing fails"""
    if _sns_handler:
        _sns_handler.notify_post_failed(post_id, platform, error)


def on_new_message(sender: str, message_type: str, preview: str):
    """Called when new message arrives"""
    if _sns_handler:
        _sns_handler.notify_new_message(sender, message_type, preview)


def on_engagement_milestone(account: str, metric: str, value: int, threshold: int):
    """Called when engagement reaches milestone"""
    if _sns_handler:
        _sns_handler.notify_engagement_milestone(account, metric, value, threshold)


def on_token_expiring(platform: str, account: str, days_left: int):
    """Called when OAuth token is about to expire"""
    if _sns_handler:
        _sns_handler.notify_token_expiring(platform, account, days_left)


if __name__ == '__main__':
    # Example usage
    handler = SNSHandler(
        telegram_api_token='YOUR_TOKEN_HERE',
        chat_id=YOUR_CHAT_ID_HERE
    )

    # Test commands
    print("Testing SNS Handler...")
    handler.cmd_sns_status()
    handler.cmd_sns_analytics(days=7)

    # Test notifications
    handler.notify_post_published(1, 'instagram', '@myaccount')
    handler.notify_new_message('John Doe', 'dm', 'Love your content!')
    handler.notify_engagement_milestone('@myaccount', 'followers', 5000, 5000)
