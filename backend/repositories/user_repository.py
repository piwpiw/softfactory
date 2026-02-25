"""User Repository — Optimized user queries"""

from sqlalchemy.orm import joinedload, selectinload
from backend.models import db, User, SNSAccount, SNSPost, ReviewAccount


class UserRepository:
    """Repository for User entity — encapsulates all user queries"""

    @staticmethod
    def get_user_by_id(user_id, include_sns=False, include_reviews=False):
        """
        Fetch user with optional eager loading.

        Args:
            user_id: User ID
            include_sns: Load SNS accounts & posts
            include_reviews: Load review accounts & applications

        Returns:
            User object or None

        Example:
            user = UserRepository.get_user_by_id(1, include_sns=True)
            # Accesses user.sns_accounts without extra queries
        """
        query = User.query

        if include_sns:
            query = query.options(
                joinedload(User.sns_accounts),
                joinedload(User.sns_posts)
            )

        if include_reviews:
            query = query.options(
                joinedload(User.review_accounts)
            )

        return query.filter_by(id=user_id).first()

    @staticmethod
    def get_user_by_email(email, include_subscriptions=False):
        """Fetch user by email (login query)"""
        query = User.query

        if include_subscriptions:
            query = query.options(
                selectinload(User.subscriptions)
            )

        return query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_oauth_id(oauth_id, oauth_provider=None):
        """Fetch user by OAuth ID (OAuth login)"""
        query = User.query.filter_by(oauth_id=oauth_id)

        if oauth_provider:
            query = query.filter_by(oauth_provider=oauth_provider)

        return query.first()

    @staticmethod
    def get_active_users(limit=100, offset=0):
        """Fetch active users (pagination)"""
        return User.query.filter_by(
            is_active=True
        ).order_by(
            User.created_at.desc()
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_users_created_between(start_date, end_date, limit=100):
        """Fetch users created in date range (analytics)"""
        return User.query.filter(
            User.created_at.between(start_date, end_date)
        ).order_by(
            User.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def count_active_users():
        """Count active users (dashboard metric)"""
        return User.query.filter_by(is_active=True).count()

    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user fields"""
        user = User.query.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()
        return user
