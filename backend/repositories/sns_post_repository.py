"""SNS Post Repository — Optimized SNS post queries"""

from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from backend.models import db, SNSPost, SNSAccount, SNSAnalytics, SNSCampaign


class SNSPostRepository:
    """Repository for SNSPost entity — optimized for analytics & scheduling"""

    @staticmethod
    def get_user_posts(user_id, limit=50, offset=0, include_account=True):
        """
        Fetch user's SNS posts with pagination.

        Uses composite index: idx_user_created(user_id, created_at)
        Eager loads account to prevent N+1 queries

        Args:
            user_id: User ID
            limit: Pagination limit
            offset: Pagination offset
            include_account: Eager load SNSAccount

        Returns:
            List of SNSPost objects
        """
        query = SNSPost.query.filter_by(user_id=user_id)

        if include_account:
            query = query.options(
                joinedload(SNSPost.account)
            )

        return query.order_by(
            SNSPost.created_at.desc()
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_user_posts_by_platform(user_id, platform, limit=50):
        """
        Fetch user's posts for specific platform.

        Uses composite index: idx_user_platform(user_id, platform)
        """
        return SNSPost.query.filter(
            SNSPost.user_id == user_id,
            SNSPost.platform == platform
        ).order_by(
            SNSPost.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_user_posts_by_status(user_id, status, limit=100):
        """
        Fetch user's posts by status.

        Uses composite index: idx_user_published(user_id, status)
        """
        return SNSPost.query.filter(
            SNSPost.user_id == user_id,
            SNSPost.status == status
        ).order_by(
            SNSPost.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_scheduled_posts(scheduled_after=None, limit=1000):
        """
        Fetch all scheduled posts ready for publishing.

        Uses index: idx_scheduled_at
        Called by APScheduler every 60 seconds

        Args:
            scheduled_after: Only posts scheduled after this datetime
            limit: Max posts to fetch (batch size)

        Returns:
            List of scheduled SNSPost objects
        """
        from datetime import datetime
        if scheduled_after is None:
            scheduled_after = datetime.utcnow()

        return SNSPost.query.filter(
            SNSPost.status == 'scheduled',
            SNSPost.scheduled_at <= scheduled_after
        ).order_by(
            SNSPost.scheduled_at.asc()
        ).limit(limit).all()

    @staticmethod
    def get_platform_posts_by_status(platform, status, limit=100):
        """
        Fetch posts across all users for a platform in specific status.

        Uses composite index: idx_platform_status(platform, status)
        Useful for debugging or platform-wide operations

        Args:
            platform: SNS platform name
            status: Post status
            limit: Result limit

        Returns:
            List of SNSPost objects
        """
        return SNSPost.query.filter(
            SNSPost.platform == platform,
            SNSPost.status == status
        ).order_by(
            SNSPost.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_campaign_posts(campaign_id, include_account=True):
        """
        Fetch all posts in a campaign.

        Uses index: idx_campaign_id
        """
        query = SNSPost.query.filter_by(campaign_id=campaign_id)

        if include_account:
            query = query.options(
                joinedload(SNSPost.account)
            )

        return query.order_by(
            SNSPost.created_at.desc()
        ).all()

    @staticmethod
    def get_user_post_stats(user_id):
        """
        Aggregate user post statistics (dashboard).

        Single aggregation query using window functions

        Returns:
            Dict with total_posts, avg_engagement, max_reach, published_count
        """
        stats = db.session.query(
            func.count(SNSPost.id).label('total_posts'),
            func.count(
                case=[(SNSPost.status == 'published', 1)]
            ).label('published_count'),
            func.avg(SNSPost.likes_count).label('avg_likes'),
            func.avg(SNSPost.reach).label('avg_reach'),
            func.max(SNSPost.reach).label('max_reach'),
        ).filter(
            SNSPost.user_id == user_id
        ).first()

        return {
            'total_posts': stats.total_posts or 0,
            'published_count': stats.published_count or 0,
            'avg_likes': round(stats.avg_likes or 0, 2),
            'avg_reach': round(stats.avg_reach or 0, 2),
            'max_reach': stats.max_reach or 0,
        }

    @staticmethod
    def get_platform_performance(user_id):
        """
        Aggregate performance metrics by platform.

        Single query with GROUP BY

        Returns:
            List of dicts with platform stats
        """
        results = db.session.query(
            SNSPost.platform,
            func.count(SNSPost.id).label('post_count'),
            func.avg(SNSPost.likes_count).label('avg_likes'),
            func.avg(SNSPost.reach).label('avg_reach'),
        ).filter(
            SNSPost.user_id == user_id,
            SNSPost.status == 'published'
        ).group_by(
            SNSPost.platform
        ).all()

        return [
            {
                'platform': r.platform,
                'post_count': r.post_count,
                'avg_likes': round(r.avg_likes or 0, 2),
                'avg_reach': round(r.avg_reach or 0, 2),
            }
            for r in results
        ]

    @staticmethod
    def update_post_status(post_id, status, error_message=None):
        """Update post status after publishing"""
        post = SNSPost.query.get(post_id)
        if post:
            post.status = status
            if error_message:
                post.error_message = error_message
            db.session.commit()
        return post

    @staticmethod
    def delete_user_posts(user_id, status='draft'):
        """Delete user's draft posts (cleanup)"""
        deleted_count = SNSPost.query.filter(
            SNSPost.user_id == user_id,
            SNSPost.status == status
        ).delete()
        db.session.commit()
        return deleted_count


# Import after class definition to avoid circular imports
try:
    from sqlalchemy import case
except ImportError:
    from sqlalchemy.sql import case
