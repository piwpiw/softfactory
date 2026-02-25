"""Review Listing Repository — Optimized review opportunity queries"""

from datetime import datetime
from sqlalchemy import func, and_, or_
from backend.models import db, ReviewListing, ReviewApplication, ReviewAccount


class ReviewListingRepository:
    """Repository for ReviewListing entity — optimized for scraping & browsing"""

    @staticmethod
    def get_active_listings(limit=50, offset=0, category=None):
        """
        Fetch active review listings (main browse view).

        Uses composite index: idx_category_deadline(category, deadline)
        Filters by status and deadline

        Args:
            limit: Pagination limit
            offset: Pagination offset
            category: Optional category filter

        Returns:
            List of active ReviewListing objects
        """
        query = ReviewListing.query.filter(
            ReviewListing.status == 'active',
            ReviewListing.deadline > datetime.utcnow()
        )

        if category:
            query = query.filter_by(category=category)

        return query.order_by(
            ReviewListing.deadline.asc()
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_listings_by_category(category, status='active', limit=100):
        """
        Fetch listings for specific category.

        Uses composite index: idx_category_deadline(category, deadline)
        """
        return ReviewListing.query.filter(
            ReviewListing.category == category,
            ReviewListing.status == status,
            ReviewListing.deadline > datetime.utcnow()
        ).order_by(
            ReviewListing.deadline.asc()
        ).limit(limit).all()

    @staticmethod
    def get_listings_by_reward_range(min_reward, max_reward, limit=100):
        """
        Fetch listings by reward value range.

        Uses index: idx_reward_value
        """
        return ReviewListing.query.filter(
            ReviewListing.reward_value.between(min_reward, max_reward),
            ReviewListing.status == 'active',
            ReviewListing.deadline > datetime.utcnow()
        ).order_by(
            ReviewListing.reward_value.desc()
        ).limit(limit).all()

    @staticmethod
    def get_listings_to_scrape(platform, last_scraped_before=None, limit=100):
        """
        Fetch listings from platform that need scraping.

        Uses composite index: idx_source_platform_scraped(source_platform, scraped_at)
        Called by scraper jobs

        Args:
            platform: Source platform name
            last_scraped_before: Only listings not scraped recently
            limit: Max listings to scrape in batch

        Returns:
            List of ReviewListing objects
        """
        if last_scraped_before is None:
            from datetime import timedelta
            last_scraped_before = datetime.utcnow() - timedelta(hours=1)

        return ReviewListing.query.filter(
            ReviewListing.source_platform == platform,
            ReviewListing.scraped_at < last_scraped_before
        ).order_by(
            ReviewListing.scraped_at.asc()
        ).limit(limit).all()

    @staticmethod
    def get_expired_listings(limit=1000):
        """
        Fetch listings that have expired.

        Uses index: idx_deadline
        For status cleanup job

        Returns:
            List of expired ReviewListing objects
        """
        return ReviewListing.query.filter(
            ReviewListing.deadline < datetime.utcnow(),
            ReviewListing.status.in_(['active', 'closed'])
        ).limit(limit).all()

    @staticmethod
    def get_listing_by_external_id(external_id, platform):
        """
        Fetch listing by platform-specific ID (duplicate prevention).

        Uses composite index: idx_external_id_platform(external_id, source_platform)

        Args:
            external_id: Platform's internal listing ID
            platform: Source platform name

        Returns:
            ReviewListing object or None
        """
        return ReviewListing.query.filter(
            ReviewListing.external_id == external_id,
            ReviewListing.source_platform == platform
        ).first()

    @staticmethod
    def get_listing_with_applications(listing_id):
        """
        Fetch listing with all applications (detail view).

        Uses eager loading to prevent N+1 queries
        """
        from sqlalchemy.orm import joinedload
        return ReviewListing.query.options(
            joinedload(ReviewListing.applications)
        ).filter_by(id=listing_id).first()

    @staticmethod
    def get_user_applied_listings(user_id, limit=50):
        """
        Fetch listings user has already applied to.

        Joins through ReviewApplication
        """
        return db.session.query(ReviewListing).join(
            ReviewApplication,
            ReviewListing.id == ReviewApplication.listing_id
        ).join(
            ReviewAccount,
            ReviewApplication.account_id == ReviewAccount.id
        ).filter(
            ReviewAccount.user_id == user_id
        ).order_by(
            ReviewApplication.applied_at.desc()
        ).limit(limit).all()

    @staticmethod
    def update_listing_status(listing_id, status):
        """Update listing status after deadline check"""
        listing = ReviewListing.query.get(listing_id)
        if listing:
            listing.status = status
            db.session.commit()
        return listing

    @staticmethod
    def update_listing_applicant_count(listing_id, increment=1):
        """Increment applicant count when user applies"""
        listing = ReviewListing.query.get(listing_id)
        if listing:
            listing.current_applicants += increment
            db.session.commit()
        return listing

    @staticmethod
    def bulk_update_scraped_at(platform, listing_ids):
        """Bulk update scraped_at timestamp for listings"""
        db.session.query(ReviewListing).filter(
            ReviewListing.source_platform == platform,
            ReviewListing.id.in_(listing_ids)
        ).update({'scraped_at': datetime.utcnow()})
        db.session.commit()

    @staticmethod
    def get_platform_stats(platform):
        """
        Get statistics for a scraping platform.

        Single aggregation query
        """
        stats = db.session.query(
            func.count(ReviewListing.id).label('total_listings'),
            func.count(
                case=[(ReviewListing.status == 'active', 1)]
            ).label('active_listings'),
            func.avg(ReviewListing.reward_value).label('avg_reward'),
            func.max(ReviewListing.reward_value).label('max_reward'),
        ).filter(
            ReviewListing.source_platform == platform,
            ReviewListing.deadline > datetime.utcnow()
        ).first()

        return {
            'total_listings': stats.total_listings or 0,
            'active_listings': stats.active_listings or 0,
            'avg_reward': round(stats.avg_reward or 0, 0),
            'max_reward': stats.max_reward or 0,
        }

    @staticmethod
    def delete_expired_listings(days_old=30):
        """Delete listings older than N days (archiving)"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        deleted_count = ReviewListing.query.filter(
            ReviewListing.deadline < cutoff_date,
            ReviewListing.status == 'ended'
        ).delete()
        db.session.commit()
        return deleted_count


# Import after class definition
try:
    from sqlalchemy import case
except ImportError:
    from sqlalchemy.sql import case
