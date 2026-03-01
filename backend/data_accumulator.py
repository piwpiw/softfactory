"""Data Accumulator — Stores, queries, and manages accumulated crawled data.

Provides a clean interface for storing crawl results, retrieving historical
data, computing aggregate statistics, and measuring data freshness per
platform.

All functions require an active Flask application context.
"""

import logging
from datetime import datetime, timedelta, date
from collections import defaultdict
from typing import Optional

from .models import db, ReviewListing, CrawlerLog, SNSAnalytics

logger = logging.getLogger('data_accumulator')


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def store_crawl_result(
    platform: str,
    listings: list[dict],
    metadata: Optional[dict] = None,
) -> dict:
    """Persist crawled listings for a given platform and record a CrawlerLog entry.

    Each listing dict should contain at minimum:
        external_id, title, brand, category, reward_type, reward_value,
        deadline (ISO string or datetime), url

    Returns a summary dict with counts of inserted / skipped / errors.

    This function is idempotent: existing external_ids are skipped.
    """
    inserted = 0
    skipped = 0
    errors = 0

    for item in listings:
        try:
            ext_id = item.get('external_id')
            if not ext_id:
                errors += 1
                continue

            # Idempotent: skip duplicates
            existing = ReviewListing.query.filter_by(external_id=ext_id).first()
            if existing:
                skipped += 1
                continue

            # Parse deadline
            deadline = item.get('deadline')
            if isinstance(deadline, str):
                try:
                    deadline = datetime.fromisoformat(deadline)
                except (ValueError, TypeError):
                    deadline = datetime.utcnow() + timedelta(days=30)
            elif not isinstance(deadline, datetime):
                deadline = datetime.utcnow() + timedelta(days=30)

            listing = ReviewListing(
                source_platform=platform,
                external_id=ext_id,
                title=item.get('title', 'Untitled')[:500],
                brand=item.get('brand', '')[:255],
                category=item.get('category', '')[:100],
                reward_type=item.get('reward_type', 'product')[:50],
                reward_value=item.get('reward_value', 0),
                requirements=item.get('requirements', {}),
                deadline=deadline,
                max_applicants=item.get('max_applicants'),
                current_applicants=item.get('current_applicants', 0),
                url=item.get('url', '')[:500],
                image_url=item.get('image_url', '')[:500] if item.get('image_url') else None,
                status='active',
                scraped_at=datetime.utcnow(),
            )
            db.session.add(listing)
            inserted += 1

        except Exception as e:
            logger.error(f'[ACCUMULATOR] Error storing listing {item.get("external_id")}: {e}')
            errors += 1

    # Record CrawlerLog entry
    log_entry = CrawlerLog(
        site=platform,
        listing_count=inserted,
        last_crawl_time=datetime.utcnow(),
        status='success' if errors == 0 else 'partial',
        error_message=f'{errors} errors during ingestion' if errors else None,
    )
    db.session.add(log_entry)

    db.session.commit()

    summary = {
        'platform': platform,
        'inserted': inserted,
        'skipped': skipped,
        'errors': errors,
        'total_input': len(listings),
        'metadata': metadata or {},
        'timestamp': datetime.utcnow().isoformat(),
    }
    logger.info(f'[ACCUMULATOR] {platform}: +{inserted} new, {skipped} skipped, {errors} errors')
    return summary


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def get_crawl_history(
    platform: Optional[str] = None,
    days: int = 30,
) -> list[dict]:
    """Return CrawlerLog entries for the last *days* days, optionally filtered by platform.

    Results are ordered newest-first.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = CrawlerLog.query.filter(CrawlerLog.created_at >= cutoff)

    if platform:
        query = query.filter_by(site=platform)

    query = query.order_by(CrawlerLog.created_at.desc())
    logs = query.limit(500).all()

    return [log.to_dict() for log in logs]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_accumulated_stats() -> dict:
    """Compute aggregate statistics over all accumulated review listings.

    Returns:
        {
            total_listings: int,
            active_listings: int,
            expired_listings: int,
            by_platform: { platform: count, ... },
            by_category: { category: count, ... },
            by_date: [ { date: "YYYY-MM-DD", count: int }, ... ]  (last 30 days)
        }
    """
    from sqlalchemy import func, case

    # Total & active counts
    totals = db.session.query(
        func.count(ReviewListing.id).label('total'),
        func.sum(case((ReviewListing.status == 'active', 1), else_=0)).label('active'),
    ).first()
    total = totals[0] or 0
    active = totals[1] or 0

    # By platform
    platform_rows = db.session.query(
        ReviewListing.source_platform,
        func.count(ReviewListing.id),
    ).group_by(ReviewListing.source_platform).all()
    by_platform = {row[0]: row[1] for row in platform_rows}

    # By category
    category_rows = db.session.query(
        ReviewListing.category,
        func.count(ReviewListing.id),
    ).filter(ReviewListing.category.isnot(None)).group_by(ReviewListing.category).all()
    by_category = {row[0]: row[1] for row in category_rows}

    # By date (last 30 days of ingestion)
    cutoff_30 = datetime.utcnow() - timedelta(days=30)
    date_rows = db.session.query(
        func.date(ReviewListing.scraped_at).label('day'),
        func.count(ReviewListing.id).label('cnt'),
    ).filter(
        ReviewListing.scraped_at >= cutoff_30,
    ).group_by(
        func.date(ReviewListing.scraped_at),
    ).order_by(
        func.date(ReviewListing.scraped_at),
    ).all()
    by_date = [{'date': str(row[0]), 'count': row[1]} for row in date_rows]

    return {
        'total_listings': total,
        'active_listings': active,
        'expired_listings': total - active,
        'by_platform': by_platform,
        'by_category': by_category,
        'by_date': by_date,
    }


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------

def get_data_freshness() -> dict:
    """Report how old the most recent data is per platform.

    Returns:
        {
            platforms: {
                "revu": { last_crawl: "ISO", age_minutes: 145, stale: false },
                ...
            },
            oldest_platform: "wible",
            newest_platform: "revu",
            overall_age_minutes: 72,
        }
    """
    from sqlalchemy import func

    now = datetime.utcnow()
    stale_threshold_hours = 6  # consider data stale after 6 hours

    rows = db.session.query(
        ReviewListing.source_platform,
        func.max(ReviewListing.scraped_at).label('last_scraped'),
        func.count(ReviewListing.id).label('total'),
    ).group_by(ReviewListing.source_platform).all()

    platforms = {}
    oldest_age = -1
    newest_age = float('inf')
    oldest_platform = None
    newest_platform = None

    for row in rows:
        platform = row[0]
        last = row[1]
        total = row[2]

        if last:
            age = (now - last).total_seconds() / 60  # minutes
        else:
            age = float('inf')

        is_stale = age > (stale_threshold_hours * 60)

        platforms[platform] = {
            'last_crawl': last.isoformat() if last else None,
            'age_minutes': round(age, 1) if age != float('inf') else None,
            'stale': is_stale,
            'listing_count': total,
        }

        if age > oldest_age:
            oldest_age = age
            oldest_platform = platform
        if age < newest_age:
            newest_age = age
            newest_platform = platform

    # Overall age = average age across platforms
    finite_ages = [p['age_minutes'] for p in platforms.values() if p['age_minutes'] is not None]
    overall = round(sum(finite_ages) / len(finite_ages), 1) if finite_ages else None

    return {
        'platforms': platforms,
        'oldest_platform': oldest_platform,
        'newest_platform': newest_platform,
        'overall_age_minutes': overall,
        'stale_threshold_hours': stale_threshold_hours,
        'checked_at': now.isoformat(),
    }
