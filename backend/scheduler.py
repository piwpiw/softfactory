"""APScheduler Background Job Runner for SNS Publishing"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

logger = logging.getLogger('sns.scheduler')


class SNSScheduler:
    """Background scheduler for publishing SNS posts at scheduled times"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.is_running = False

    def start(self, app: Flask):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        with app.app_context():
            # Add job to check and publish scheduled posts every 60 seconds
            self.scheduler.add_job(
                func=publish_scheduled_posts,
                args=[app],
                trigger="interval",
                seconds=60,
                id='publish_scheduled_posts',
                name='Publish scheduled SNS posts',
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("SNS Scheduler started - checking scheduled posts every 60 seconds")

    def stop(self):
        """Stop the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("SNS Scheduler stopped")


def publish_scheduled_posts(app: Flask):
    """
    Check for posts ready to publish (scheduled_at <= now, status='scheduled')
    and publish them to their respective platforms.

    This runs every 60 seconds as a background job.
    """
    from backend.models import db, SNSPost, SNSAccount, SNSAnalytics
    from backend.services.sns_platforms import get_client
    from datetime import datetime, timedelta
    import os

    try:
        with app.app_context():
            # Find all posts ready to publish
            now = datetime.utcnow()
            posts_to_publish = SNSPost.query.filter(
                SNSPost.status == 'scheduled',
                SNSPost.scheduled_at <= now,
                SNSPost.retry_count < 3
            ).all()

            if not posts_to_publish:
                return

            logger.info(f"Found {len(posts_to_publish)} posts ready to publish")

            for post in posts_to_publish:
                try:
                    # Get the account
                    account = SNSAccount.query.get(post.account_id)
                    if not account or not account.is_active:
                        post.status = 'failed'
                        post.error_message = 'Account inactive or deleted'
                        db.session.add(post)
                        continue

                    # Get platform client
                    client = get_client(
                        post.platform,
                        access_token=account.access_token,
                        refresh_token=account.refresh_token,
                        simulation_mode=True  # Default to simulation until API keys are set
                    )

                    if not client:
                        raise ValueError(f"Unknown platform: {post.platform}")

                    # Publish post
                    result = client.post_content(
                        content=post.content,
                        media_urls=post.media_urls or [],
                        hashtags=post.hashtags or [],
                        link_url=post.link_url
                    )

                    if result.get('success'):
                        # Update post as published
                        post.status = 'published'
                        post.published_at = datetime.utcnow()
                        post.external_post_id = result.get('external_post_id')
                        logger.info(f"Post {post.id} published to {post.platform}")

                        # Notify via Telegram if available
                        try:
                            send_telegram_notification(
                                app,
                                post.user_id,
                                f"SNS Post Published: {post.platform} - {post.content[:50]}..."
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send Telegram notification: {e}")

                    else:
                        # Retry with exponential backoff
                        post.retry_count += 1
                        if post.retry_count >= 3:
                            post.status = 'failed'
                            post.error_message = f"Max retries exceeded: {result.get('error', 'Unknown error')}"
                            logger.error(f"Post {post.id} failed after 3 retries: {post.error_message}")
                        else:
                            logger.warning(f"Post {post.id} retry {post.retry_count}/3: {result.get('error')}")

                        post.error_message = result.get('error', 'Unknown error')

                    db.session.add(post)

                except Exception as e:
                    logger.error(f"Error publishing post {post.id}: {str(e)}", exc_info=True)
                    post.retry_count += 1
                    post.error_message = str(e)[:500]

                    if post.retry_count >= 3:
                        post.status = 'failed'
                        logger.error(f"Post {post.id} failed after 3 retries")

                    db.session.add(post)

            db.session.commit()
            logger.info(f"Finished publishing batch - {len(posts_to_publish)} posts processed")

    except Exception as e:
        logger.error(f"Critical error in publish_scheduled_posts: {str(e)}", exc_info=True)


def send_telegram_notification(app: Flask, user_id: int, message: str):
    """
    Send notification via Telegram if user has allowed chat ID configured.

    Note: This will be integrated with daemon/handlers/sns_handler.py in Phase 4
    """
    from backend.models import db, User
    import os

    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return

        # TODO: Get user's Telegram chat ID from SNSSettings or user profile
        # For now, send to admin bot
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

        if not bot_token or not admin_chat_id:
            return

        # This will be implemented in daemon/telegram_notifier.py
        # For now, just log it
        logger.info(f"[TELEGRAM] To chat {admin_chat_id}: {message}")


# Global scheduler instance
sns_scheduler = SNSScheduler()


def init_scheduler(app: Flask):
    """Initialize and start the scheduler in Flask app context"""
    sns_scheduler.start(app)
    logger.info("SNS Scheduler initialized and started")
