"""
SNS Scheduled Post Publisher

Runs as a background thread or can be called from a cron/APScheduler job.
Polls for `status='scheduled'` posts whose `scheduled_at` <= now and publishes them.

Usage (Flask app factory):
    from backend.services.sns_scheduler import start_scheduler
    start_scheduler(app)

Or via APScheduler / cron, call `run_scheduled_posts(app)` directly.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger('sns.scheduler')


def run_scheduled_posts(app) -> dict:
    """
    Find and publish all overdue scheduled posts.
    Must be called inside Flask app context (or pass app for context push).

    Returns summary dict: {processed, published, failed, skipped}
    """
    from .sns_platforms import get_client as get_platform_client

    summary = {'processed': 0, 'published': 0, 'failed': 0, 'skipped': 0}

    with app.app_context():
        from ..models import db, SNSPost, SNSAccount

        now = datetime.utcnow()
        due_posts = (
            SNSPost.query
            .filter(SNSPost.status == 'scheduled')
            .filter(SNSPost.scheduled_at <= now)
            .all()
        )

        if not due_posts:
            logger.debug(f"[scheduler] No scheduled posts due at {now.isoformat()}")
            return summary

        logger.info(f"[scheduler] Processing {len(due_posts)} scheduled posts")

        for post in due_posts:
            summary['processed'] += 1
            account: Optional[SNSAccount] = SNSAccount.query.get(post.account_id)

            if not account or not account.is_active:
                logger.warning(f"[scheduler] Post {post.id}: account missing or inactive — skipping")
                summary['skipped'] += 1
                continue

            simulation = not account.access_token
            client = get_platform_client(
                post.platform,
                access_token=account.access_token,
                refresh_token=account.refresh_token,
                simulation_mode=simulation,
                site_url=getattr(account, 'site_url', None),
                wp_username=getattr(account, 'wp_username', None),
            )

            if client is None:
                logger.warning(f"[scheduler] Post {post.id}: no client for '{post.platform}' — skipping")
                summary['skipped'] += 1
                continue

            try:
                result = client.post_content(
                    content=post.content,
                    media_urls=post.media_urls or [],
                    hashtags=post.hashtags or [],
                    link_url=post.link_url,
                )

                if result.get('success'):
                    post.status = 'published'
                    post.published_at = datetime.utcnow()
                    post.external_post_id = result.get('external_post_id', '')
                    summary['published'] += 1
                    logger.info(f"[scheduler] Post {post.id} published → {result.get('url', '')}")
                else:
                    post.status = 'failed'
                    post.error_message = result.get('error', 'Unknown error')
                    post.retry_count = (post.retry_count or 0) + 1
                    summary['failed'] += 1
                    logger.error(f"[scheduler] Post {post.id} failed: {post.error_message}")

            except Exception as e:
                post.status = 'failed'
                post.error_message = str(e)
                post.retry_count = (post.retry_count or 0) + 1
                summary['failed'] += 1
                logger.error(f"[scheduler] Post {post.id} exception: {e}")

        db.session.commit()

    logger.info(f"[scheduler] Done: {summary}")
    return summary


def start_scheduler(app, interval_seconds: int = 60):
    """
    Start a background daemon thread that checks for scheduled posts every `interval_seconds`.

    Call once from the Flask app factory after db.create_all().
    The thread is daemonized so it stops when the main process exits.
    """
    def _loop():
        logger.info(f"[scheduler] Started — checking every {interval_seconds}s")
        while True:
            try:
                run_scheduled_posts(app)
            except Exception as e:
                logger.error(f"[scheduler] Unhandled error in scheduler loop: {e}")
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, name='sns-scheduler', daemon=True)
    t.start()
    logger.info(f"[scheduler] Background thread started (tid={t.ident})")
    return t
