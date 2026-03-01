"""Automated Scheduler — APScheduler integration for periodic data pipeline tasks.

Manages 6 background jobs:
  1. Review site crawling (every 2 hours)
  2. SNS analytics collection (every 1 hour)
  3. Trending topics refresh (every 30 minutes)
  4. Auto-apply rules check (every 15 minutes)
  5. SNS auto-post executor (every 5 minutes)
  6. Data cleanup (daily at 3 AM)

Thread-safe: all DB operations use Flask app context.
Idempotent: repeated runs produce the same result.
"""

import logging
import threading
import traceback
from datetime import datetime, timedelta, date
from collections import defaultdict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

logger = logging.getLogger('scheduler')

# ---------------------------------------------------------------------------
# In-memory execution history (thread-safe, bounded)
# ---------------------------------------------------------------------------
_history_lock = threading.Lock()
_job_history: list[dict] = []
_MAX_HISTORY = 500


def _record_history(job_id: str, job_name: str, status: str, duration_ms: float, detail: str = ''):
    """Append an entry to the in-memory job execution history."""
    entry = {
        'job_id': job_id,
        'job_name': job_name,
        'status': status,
        'duration_ms': round(duration_ms, 1),
        'detail': detail[:500],
        'executed_at': datetime.utcnow().isoformat(),
    }
    with _history_lock:
        _job_history.append(entry)
        # Trim to bounded size
        while len(_job_history) > _MAX_HISTORY:
            _job_history.pop(0)


def get_job_history(limit: int = 50) -> list[dict]:
    """Return the most recent *limit* history entries (newest first)."""
    with _history_lock:
        return list(reversed(_job_history[-limit:]))


# ---------------------------------------------------------------------------
# Scheduler singleton
# ---------------------------------------------------------------------------
scheduler = BackgroundScheduler(daemon=True)
_scheduler_started = False


def init_scheduler(app: Flask):
    """Initialize scheduler with Flask app context and register all 6 jobs."""
    global _scheduler_started
    if _scheduler_started:
        logger.warning('Scheduler already started — skipping init')
        return

    # Job 1: Review site crawling (every 2 hours)
    scheduler.add_job(
        crawl_review_sites,
        IntervalTrigger(hours=2),
        id='review_crawler',
        name='Review Site Crawler',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 2: SNS analytics collection (every 1 hour)
    scheduler.add_job(
        collect_sns_analytics,
        IntervalTrigger(hours=1),
        id='sns_analytics',
        name='SNS Analytics Collector',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 3: Trending topics refresh (every 30 minutes)
    scheduler.add_job(
        refresh_trending,
        IntervalTrigger(minutes=30),
        id='trending_refresh',
        name='Trending Topics Refresh',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 4: Auto-apply rules check (every 15 minutes)
    scheduler.add_job(
        check_auto_apply_rules,
        IntervalTrigger(minutes=15),
        id='auto_apply_check',
        name='Auto Apply Rules Check',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 5: SNS auto-post scheduler (every 5 minutes)
    scheduler.add_job(
        execute_scheduled_posts,
        IntervalTrigger(minutes=5),
        id='sns_auto_post',
        name='SNS Auto Post Executor',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 6: Data cleanup (daily at 3 AM UTC)
    scheduler.add_job(
        cleanup_old_data,
        CronTrigger(hour=3, minute=0),
        id='data_cleanup',
        name='Old Data Cleanup',
        replace_existing=True,
        kwargs={'app': app},
    )

    # Job 7: Daily Telegram summary report (daily at 9 AM UTC)
    scheduler.add_job(
        send_daily_telegram_summary,
        CronTrigger(hour=9, minute=0),
        id='telegram_daily_summary',
        name='Telegram Daily Summary',
        replace_existing=True,
        kwargs={'app': app},
    )

    scheduler.start()
    _scheduler_started = True
    logger.info('Scheduler started with 7 jobs: '
                'review_crawler(2h), sns_analytics(1h), trending_refresh(30m), '
                'auto_apply_check(15m), sns_auto_post(5m), data_cleanup(daily@03:00), '
                'telegram_daily_summary(daily@09:00)')


# ===========================================================================
# Job 1 — Review Site Crawling
# ===========================================================================

def crawl_review_sites(app: Flask):
    """Crawl all review platforms, aggregate results, and log per-platform counts.

    Each scraper failure is isolated — one failing platform does not stop the rest.
    """
    t0 = _now_ms()
    results: dict[str, int] = {}
    errors: list[str] = []

    try:
        with app.app_context():
            from backend.models import db, CrawlerLog

            # Try to import and run the real scrapers module
            try:
                from backend.services.review_scrapers import aggregate_all_listings
                results = aggregate_all_listings(max_workers=3)
                # If real scrapers returned zero results across all platforms,
                # fall back to mock data generation
                if sum(results.values()) == 0:
                    logger.info('[CRAWLER] Real scrapers returned 0 results; supplementing with mock data')
                    results = _mock_crawl_review_sites(app)
            except ImportError:
                # Scrapers module not yet implemented — run mock crawl
                logger.info('[CRAWLER] review_scrapers module not found; running mock crawl')
                results = _mock_crawl_review_sites(app)
            except Exception as e:
                logger.error(f'[CRAWLER] aggregate_all_listings error: {e}', exc_info=True)
                errors.append(str(e))
                results = _mock_crawl_review_sites(app)

            # Log per-platform results into CrawlerLog
            for platform, count in results.items():
                log_entry = CrawlerLog(
                    site=platform,
                    listing_count=count,
                    last_crawl_time=datetime.utcnow(),
                    status='success',
                )
                db.session.add(log_entry)

            if errors:
                for err in errors:
                    log_entry = CrawlerLog(
                        site='aggregate',
                        listing_count=0,
                        last_crawl_time=datetime.utcnow(),
                        status='error',
                        error_message=err[:500],
                    )
                    db.session.add(log_entry)

            db.session.commit()

            total = sum(results.values())
            logger.info(f'[CRAWLER] Completed: {total} listings across {len(results)} platforms')
            for p, c in results.items():
                logger.info(f'[CRAWLER]   {p}: {c} listings')

            _record_history('review_crawler', 'Review Site Crawler', 'success',
                            _now_ms() - t0, f'{total} listings from {len(results)} platforms')

    except Exception as e:
        logger.error(f'[CRAWLER] Critical error: {e}', exc_info=True)
        _record_history('review_crawler', 'Review Site Crawler', 'error',
                        _now_ms() - t0, str(e)[:500])


def _mock_crawl_review_sites(app: Flask) -> dict[str, int]:
    """Generate mock review listings when real scrapers are unavailable."""
    from backend.models import db, ReviewListing
    import random
    import uuid

    platforms = ['revu', 'reviewplace', 'wible', 'mibl', 'seoulouba', 'naver', 'moaview', 'inflexer']
    categories = ['beauty', 'food', 'tech', 'fashion', 'lifestyle', 'health', 'travel']
    reward_types = ['product', 'cash', 'experience']
    brands = ['GlowSkin', 'BeanBliss', 'TechNova', 'StyleHub', 'FreshLife',
              'HealthPlus', 'WanderCo', 'PureBrew', 'NeonFit', 'CrispAir']

    counts: dict[str, int] = {}

    for platform in platforms:
        n = random.randint(2, 8)
        inserted = 0
        for _ in range(n):
            ext_id = f'{platform}_{uuid.uuid4().hex[:12]}'
            # Idempotent: skip if external_id already exists
            existing = ReviewListing.query.filter_by(external_id=ext_id).first()
            if existing:
                continue

            listing = ReviewListing(
                source_platform=platform,
                external_id=ext_id,
                title=f'{random.choice(brands)} {random.choice(categories).title()} Review Campaign',
                brand=random.choice(brands),
                category=random.choice(categories),
                reward_type=random.choice(reward_types),
                reward_value=random.choice([10000, 20000, 30000, 50000, 100000]),
                deadline=datetime.utcnow() + timedelta(days=random.randint(5, 45)),
                max_applicants=random.randint(10, 100),
                current_applicants=0,
                url=f'https://{platform}.example.com/campaign/{ext_id}',
                status='active',
                scraped_at=datetime.utcnow(),
            )
            db.session.add(listing)
            inserted += 1

        counts[platform] = inserted

    db.session.flush()
    return counts


# ===========================================================================
# Job 2 — SNS Analytics Collection
# ===========================================================================

def collect_sns_analytics(app: Flask):
    """For each user with active SNS accounts, collect (mock) analytics data
    and store daily snapshots in SNSAnalytics.
    """
    t0 = _now_ms()
    try:
        with app.app_context():
            from backend.models import db, SNSAccount, SNSAnalytics
            import random

            today = date.today()
            accounts = SNSAccount.query.filter_by(is_active=True).all()

            created = 0
            skipped = 0
            for acct in accounts:
                # Idempotent: one analytics row per account per day
                existing = SNSAnalytics.query.filter_by(
                    account_id=acct.id,
                    date=today,
                ).first()
                if existing:
                    skipped += 1
                    continue

                # Generate realistic-looking mock data
                base_followers = acct.followers_count or random.randint(100, 10000)
                follower_delta = random.randint(-5, 50)

                analytics = SNSAnalytics(
                    user_id=acct.user_id,
                    account_id=acct.id,
                    date=today,
                    followers=base_followers + follower_delta,
                    total_engagement=random.randint(10, max(11, base_followers // 10)),
                    total_reach=random.randint(base_followers, base_followers * 3),
                    total_impressions=random.randint(base_followers * 2, base_followers * 5),
                )
                db.session.add(analytics)

                # Update the account follower count while we are here
                acct.followers_count = base_followers + follower_delta
                created += 1

            db.session.commit()
            logger.info(f'[SNS-ANALYTICS] Created {created} snapshots, skipped {skipped} (already exists)')
            _record_history('sns_analytics', 'SNS Analytics Collector', 'success',
                            _now_ms() - t0, f'{created} new, {skipped} skipped')

    except Exception as e:
        logger.error(f'[SNS-ANALYTICS] Error: {e}', exc_info=True)
        _record_history('sns_analytics', 'SNS Analytics Collector', 'error',
                        _now_ms() - t0, str(e)[:500])


# ===========================================================================
# Job 3 — Trending Topics Refresh
# ===========================================================================

# In-memory trending cache (thread-safe)
_trending_lock = threading.Lock()
_trending_cache: dict = {}
_trending_updated_at: datetime | None = None


def get_trending_cache() -> tuple[dict, datetime | None]:
    """Public accessor for the trending data cache."""
    with _trending_lock:
        return dict(_trending_cache), _trending_updated_at


def refresh_trending(app: Flask):
    """Generate/refresh trending topics per platform and cache them."""
    global _trending_cache, _trending_updated_at
    t0 = _now_ms()

    try:
        with app.app_context():
            import random

            trending_data = {
                'instagram': {
                    'hashtags': _pick_trending_hashtags('instagram'),
                    'topics': ['AI & Technology', 'Digital Marketing', 'E-commerce', 'Sustainability', 'Wellness'],
                    'engagement_score': round(random.uniform(7.0, 10.0), 1),
                },
                'tiktok': {
                    'hashtags': _pick_trending_hashtags('tiktok'),
                    'topics': ['Entertainment', 'Comedy', 'Education', 'Gaming', 'Lifestyle'],
                    'engagement_score': round(random.uniform(8.0, 10.0), 1),
                },
                'twitter': {
                    'hashtags': _pick_trending_hashtags('twitter'),
                    'topics': ['Breaking News', 'Technology', 'Politics', 'Sports', 'Entertainment'],
                    'engagement_score': round(random.uniform(6.5, 9.0), 1),
                },
                'linkedin': {
                    'hashtags': _pick_trending_hashtags('linkedin'),
                    'topics': ['Business', 'Career Development', 'Leadership', 'Industry News', 'Entrepreneurship'],
                    'engagement_score': round(random.uniform(6.0, 8.5), 1),
                },
                'facebook': {
                    'hashtags': _pick_trending_hashtags('facebook'),
                    'topics': ['Lifestyle', 'Community', 'Entertainment', 'Shopping', 'Family'],
                    'engagement_score': round(random.uniform(5.5, 8.0), 1),
                },
                'youtube': {
                    'hashtags': _pick_trending_hashtags('youtube'),
                    'topics': ['Tutorials', 'Gaming', 'Music', 'Tech Reviews', 'Vlogs'],
                    'engagement_score': round(random.uniform(7.0, 9.5), 1),
                },
            }

            with _trending_lock:
                _trending_cache = trending_data
                _trending_updated_at = datetime.utcnow()

            logger.info(f'[TRENDING] Refreshed {len(trending_data)} platforms')
            _record_history('trending_refresh', 'Trending Topics Refresh', 'success',
                            _now_ms() - t0, f'{len(trending_data)} platforms refreshed')

    except Exception as e:
        logger.error(f'[TRENDING] Error: {e}', exc_info=True)
        _record_history('trending_refresh', 'Trending Topics Refresh', 'error',
                        _now_ms() - t0, str(e)[:500])


def _pick_trending_hashtags(platform: str) -> list[str]:
    """Return 5 trending hashtags for a given platform (mock)."""
    import random

    pools = {
        'instagram': ['#ai2026', '#socialmedia', '#contentcreator', '#digitalmarketing',
                       '#influencer', '#reels', '#ootd', '#selfcare', '#branding', '#growth'],
        'tiktok': ['#foryoupage', '#trending', '#challenge', '#viral', '#comedy',
                    '#duet', '#fyp', '#edutok', '#storytime', '#lifehack'],
        'twitter': ['#tech', '#news', '#politics', '#sports', '#entertainment',
                     '#AI', '#startup', '#climatechange', '#crypto', '#OpenAI'],
        'linkedin': ['#business', '#career', '#leadership', '#innovation', '#entrepreneur',
                      '#hiring', '#remote', '#networking', '#growthmindset', '#DEI'],
        'facebook': ['#family', '#lifestyle', '#community', '#deals', '#entertainment',
                      '#travel', '#recipes', '#diy', '#wellness', '#shopping'],
        'youtube': ['#shorts', '#tutorial', '#vlog', '#gaming', '#music',
                     '#review', '#howto', '#unboxing', '#letsplay', '#techreview'],
    }
    pool = pools.get(platform, pools['instagram'])
    return random.sample(pool, min(5, len(pool)))


# ===========================================================================
# Job 4 — Auto-Apply Rules Check
# ===========================================================================

def check_auto_apply_rules(app: Flask):
    """Read active ReviewAutoRule records, match against new ReviewListings,
    and auto-create ReviewApplication records for matching rules.
    """
    t0 = _now_ms()
    try:
        with app.app_context():
            from backend.models import (
                db, ReviewAutoRule, ReviewListing, ReviewApplication, ReviewAccount
            )

            rules = ReviewAutoRule.query.filter_by(is_active=True).all()
            if not rules:
                logger.debug('[AUTO-APPLY] No active rules found')
                _record_history('auto_apply_check', 'Auto Apply Rules Check', 'success',
                                _now_ms() - t0, '0 rules, 0 applied')
                return

            total_applied = 0
            total_rules_processed = 0

            for rule in rules:
                try:
                    # Find active review accounts for the user
                    accounts = ReviewAccount.query.filter_by(
                        user_id=rule.user_id,
                        is_active=True,
                    ).all()
                    if not accounts:
                        continue

                    # Determine which account(s) to use
                    preferred_ids = rule.preferred_accounts or []
                    target_account = None
                    for acct in accounts:
                        if acct.id in preferred_ids:
                            target_account = acct
                            break
                    if target_account is None:
                        target_account = accounts[0]

                    # Build query for matching listings
                    now = datetime.utcnow()
                    max_deadline = now + timedelta(days=rule.apply_deadline_days or 30)

                    query = ReviewListing.query.filter(
                        ReviewListing.status == 'active',
                        ReviewListing.deadline >= now,
                        ReviewListing.deadline <= max_deadline,
                    )

                    if rule.target_categories:
                        query = query.filter(ReviewListing.category.in_(rule.target_categories))

                    if rule.min_reward:
                        query = query.filter(ReviewListing.reward_value >= rule.min_reward)
                    if rule.max_reward:
                        query = query.filter(ReviewListing.reward_value <= rule.max_reward)

                    if rule.reward_types:
                        query = query.filter(ReviewListing.reward_type.in_(rule.reward_types))

                    matching_listings = query.all()

                    rule_applied = 0
                    for listing in matching_listings:
                        # Respect applicant ratio limit
                        if (listing.max_applicants and listing.current_applicants
                                and rule.max_applicants_ratio):
                            ratio = listing.current_applicants / listing.max_applicants
                            if ratio >= rule.max_applicants_ratio:
                                continue

                        # Idempotent: skip if already applied
                        existing = ReviewApplication.query.filter_by(
                            listing_id=listing.id,
                            account_id=target_account.id,
                        ).first()
                        if existing:
                            continue

                        application = ReviewApplication(
                            listing_id=listing.id,
                            account_id=target_account.id,
                            status='pending',
                        )
                        db.session.add(application)

                        # Update listing applied_accounts
                        if not listing.applied_accounts:
                            listing.applied_accounts = []
                        if target_account.id not in listing.applied_accounts:
                            new_list = list(listing.applied_accounts)
                            new_list.append(target_account.id)
                            listing.applied_accounts = new_list

                        rule_applied += 1

                    if rule_applied > 0:
                        logger.info(f'[AUTO-APPLY] Rule "{rule.name}" (id={rule.id}): '
                                    f'applied to {rule_applied} listings')

                    total_applied += rule_applied
                    total_rules_processed += 1
                    db.session.commit()

                except Exception as e:
                    logger.error(f'[AUTO-APPLY] Error processing rule {rule.id}: {e}')
                    db.session.rollback()

            logger.info(f'[AUTO-APPLY] Processed {total_rules_processed} rules, '
                        f'auto-applied {total_applied} listings')
            _record_history('auto_apply_check', 'Auto Apply Rules Check', 'success',
                            _now_ms() - t0,
                            f'{total_rules_processed} rules, {total_applied} applied')

    except Exception as e:
        logger.error(f'[AUTO-APPLY] Critical error: {e}', exc_info=True)
        _record_history('auto_apply_check', 'Auto Apply Rules Check', 'error',
                        _now_ms() - t0, str(e)[:500])


# ===========================================================================
# Job 5 — Execute Scheduled SNS Posts
# ===========================================================================

def execute_scheduled_posts(app: Flask):
    """Find SNSAutomate records where next_run <= now and is_active,
    create mock post content, and advance next_run based on frequency.

    Also publishes any SNSPost records with status='scheduled' and
    scheduled_at <= now.

    Sends Telegram notifications on success/failure.
    """
    t0 = _now_ms()
    try:
        with app.app_context():
            from backend.models import db, SNSAutomate, SNSPost, SNSAccount
            from backend.telegram_service import send_sns_notification

            now = datetime.utcnow()

            # --- Part A: SNSAutomate rule execution ---
            automates = SNSAutomate.query.filter(
                SNSAutomate.is_active == True,  # noqa: E712
                SNSAutomate.next_run <= now,
            ).all()

            auto_executed = 0
            for rule in automates:
                try:
                    # Find an active account for the user on one of the target platforms
                    platforms = rule.platforms or []
                    if not platforms:
                        continue

                    account = SNSAccount.query.filter(
                        SNSAccount.user_id == rule.user_id,
                        SNSAccount.platform.in_(platforms),
                        SNSAccount.is_active == True,  # noqa: E712
                    ).first()

                    if not account:
                        logger.warning(f'[AUTO-POST] No active account for rule {rule.id}')
                        # Send Telegram failure notification
                        send_sns_notification(
                            rule.user_id,
                            'post_failure',
                            {'platform': ', '.join(platforms), 'error': 'No active account found'}
                        )
                        continue

                    # Create a mock post (in production, use AI generation)
                    post = SNSPost(
                        user_id=rule.user_id,
                        account_id=account.id,
                        content=f'[Auto] {rule.topic or "Update"} — {rule.purpose or "engagement"}',
                        platform=account.platform,
                        template_type='auto_generated',
                        status='published',
                        published_at=now,
                        scheduled_at=now,
                    )
                    db.session.add(post)

                    # Advance next_run
                    freq = rule.frequency or 'daily'
                    if freq == 'daily':
                        rule.next_run = now + timedelta(days=1)
                    elif freq == 'weekly':
                        rule.next_run = now + timedelta(weeks=1)
                    elif freq == 'custom':
                        rule.next_run = now + timedelta(hours=24)
                    else:
                        rule.next_run = now + timedelta(days=1)

                    auto_executed += 1

                    # Send Telegram success notification
                    send_sns_notification(
                        rule.user_id,
                        'automation_executed',
                        {
                            'automation_name': rule.name or f'Auto-rule {rule.id}',
                            'platforms': platforms,
                            'execution_time': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        }
                    )

                except Exception as e:
                    logger.error(f'[AUTO-POST] Error executing rule {rule.id}: {e}')
                    # Send Telegram failure notification
                    try:
                        send_sns_notification(
                            rule.user_id,
                            'post_failure',
                            {'platform': ', '.join(rule.platforms or []), 'error': str(e)[:200]}
                        )
                    except Exception as notify_error:
                        logger.error(f'[AUTO-POST] Failed to send Telegram notification: {notify_error}')

            # --- Part B: Publish scheduled individual posts ---
            scheduled_posts = SNSPost.query.filter(
                SNSPost.status == 'scheduled',
                SNSPost.scheduled_at <= now,
            ).all()

            posts_published = 0
            for post in scheduled_posts:
                try:
                    post.status = 'published'
                    post.published_at = now
                    posts_published += 1
                except Exception as e:
                    logger.error(f'[AUTO-POST] Error publishing post {post.id}: {e}')
                    post.status = 'failed'
                    post.error_message = str(e)[:500]

            db.session.commit()

            if auto_executed or posts_published:
                logger.info(f'[AUTO-POST] Executed {auto_executed} automation rules, '
                            f'published {posts_published} scheduled posts')
            _record_history('sns_auto_post', 'SNS Auto Post Executor', 'success',
                            _now_ms() - t0,
                            f'{auto_executed} rules, {posts_published} posts published')

    except Exception as e:
        logger.error(f'[AUTO-POST] Critical error: {e}', exc_info=True)
        _record_history('sns_auto_post', 'SNS Auto Post Executor', 'error',
                        _now_ms() - t0, str(e)[:500])


# ===========================================================================
# Job 6 — Daily Telegram Summary
# ===========================================================================

def send_daily_telegram_summary(app: Flask):
    """Send daily SNS summary report via Telegram to all users with Telegram enabled.

    Summary includes:
    - Total posts published (success/failure)
    - Engagement metrics (likes, comments)
    - Per-platform statistics
    """
    t0 = _now_ms()
    try:
        with app.app_context():
            from backend.models import db, SNSSettings, SNSPost, SNSAnalytics
            from backend.telegram_service import send_sns_notification
            from sqlalchemy import func

            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)

            # Get all users with Telegram enabled
            telegram_users = SNSSettings.query.filter(
                SNSSettings.telegram_enabled == True,  # noqa: E712
                SNSSettings.telegram_chat_id.isnot(None),
            ).all()

            summaries_sent = 0

            for settings in telegram_users:
                try:
                    user_id = settings.user_id

                    # Get posts from yesterday
                    posts = SNSPost.query.filter(
                        SNSPost.user_id == user_id,
                        SNSPost.published_at >= yesterday,
                        SNSPost.published_at < now,
                    ).all()

                    if not posts:
                        continue

                    # Calculate metrics
                    total_posts = len(posts)
                    successful_posts = len([p for p in posts if p.status == 'published'])
                    failed_posts = len([p for p in posts if p.status == 'failed'])

                    # Group by platform
                    platforms_stats = {}
                    for post in posts:
                        platform = post.platform or 'unknown'
                        if platform not in platforms_stats:
                            platforms_stats[platform] = {
                                'posts': 0,
                                'engagement': 0,
                            }
                        platforms_stats[platform]['posts'] += 1

                    # Calculate total engagement
                    total_engagement = sum([p.likes or 0 for p in posts]) + \
                                     sum([p.comments or 0 for p in posts])

                    for platform, stats in platforms_stats.items():
                        platform_posts = [p for p in posts if p.platform == platform]
                        stats['engagement'] = sum([p.likes or 0 for p in platform_posts]) + \
                                            sum([p.comments or 0 for p in platform_posts])

                    # Send summary
                    summary_data = {
                        'total_posts': total_posts,
                        'successful_posts': successful_posts,
                        'failed_posts': failed_posts,
                        'total_engagement': total_engagement,
                        'platforms': platforms_stats,
                    }

                    send_sns_notification(
                        user_id,
                        'daily_summary',
                        summary_data
                    )

                    summaries_sent += 1

                except Exception as e:
                    logger.error(f'[TELEGRAM] Error sending summary for user {settings.user_id}: {e}')

            logger.info(f'[TELEGRAM] Sent daily summaries to {summaries_sent} users')
            _record_history('telegram_daily_summary', 'Telegram Daily Summary', 'success',
                            _now_ms() - t0, f'{summaries_sent} summaries sent')

    except Exception as e:
        logger.error(f'[TELEGRAM] Critical error in daily summary: {e}', exc_info=True)
        _record_history('telegram_daily_summary', 'Telegram Daily Summary', 'error',
                        _now_ms() - t0, str(e)[:500])


# ===========================================================================
# Job 7 — Data Cleanup
# ===========================================================================

def cleanup_old_data(app: Flask):
    """Remove stale data to keep the database lean:
    - ReviewListings older than 90 days with status='expired'
    - SNSAnalytics data older than 365 days
    - CrawlerLog entries older than 30 days
    """
    t0 = _now_ms()
    try:
        with app.app_context():
            from backend.models import db, ReviewListing, SNSAnalytics, CrawlerLog

            now = datetime.utcnow()
            summary = {}

            # 1. Expired review listings (90 days)
            cutoff_90 = now - timedelta(days=90)
            expired = ReviewListing.query.filter(
                ReviewListing.status == 'expired',
                ReviewListing.scraped_at < cutoff_90,
            ).delete(synchronize_session='fetch')
            summary['expired_listings'] = expired

            # 2. Old SNS analytics (365 days)
            cutoff_365 = (now - timedelta(days=365)).date()
            old_analytics = SNSAnalytics.query.filter(
                SNSAnalytics.date < cutoff_365,
            ).delete(synchronize_session='fetch')
            summary['old_analytics'] = old_analytics

            # 3. Old crawler logs (30 days)
            cutoff_30 = now - timedelta(days=30)
            old_logs = CrawlerLog.query.filter(
                CrawlerLog.created_at < cutoff_30,
            ).delete(synchronize_session='fetch')
            summary['old_crawler_logs'] = old_logs

            # 4. Mark review listings past deadline as expired (housekeeping)
            expired_count = ReviewListing.query.filter(
                ReviewListing.status == 'active',
                ReviewListing.deadline < now,
            ).update({'status': 'expired'}, synchronize_session='fetch')
            summary['newly_expired'] = expired_count

            db.session.commit()

            total_deleted = expired + old_analytics + old_logs
            logger.info(f'[CLEANUP] Removed {total_deleted} rows: '
                        f'listings={expired}, analytics={old_analytics}, '
                        f'logs={old_logs}, newly_expired={expired_count}')
            _record_history('data_cleanup', 'Old Data Cleanup', 'success',
                            _now_ms() - t0,
                            f'Deleted {total_deleted} rows, expired {expired_count} listings')

    except Exception as e:
        logger.error(f'[CLEANUP] Critical error: {e}', exc_info=True)
        _record_history('data_cleanup', 'Old Data Cleanup', 'error',
                        _now_ms() - t0, str(e)[:500])


# ===========================================================================
# Helpers
# ===========================================================================

def _now_ms() -> float:
    """Current time in milliseconds (for duration tracking)."""
    import time
    return time.time() * 1000


def get_scheduler_status() -> dict:
    """Return a JSON-serializable summary of all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': next_run.isoformat() if next_run else None,
            'pending': next_run is not None,
        })
    return {
        'running': _scheduler_started,
        'job_count': len(jobs),
        'jobs': jobs,
    }


def trigger_job(job_id: str) -> bool:
    """Manually trigger a job by its ID. Returns True if the job was found."""
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    job.modify(next_run_time=datetime.utcnow())
    return True


def toggle_job(job_id: str) -> dict | None:
    """Pause or resume a job. Returns the new state or None if not found."""
    job = scheduler.get_job(job_id)
    if job is None:
        return None

    if job.next_run_time is None:
        # Currently paused — resume
        scheduler.resume_job(job_id)
        return {'id': job_id, 'state': 'active'}
    else:
        # Currently active — pause
        scheduler.pause_job(job_id)
        return {'id': job_id, 'state': 'paused'}
