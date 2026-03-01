"""SoftFactory Database Models (v2.0 — Optimized with Indexes & Relationships)"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, func
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ============ PLATFORM ============

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        # Single-column indexes (lookup, OAuth)
        Index('idx_email', 'email'),
        Index('idx_oauth_id', 'oauth_id'),
        # Composite index (user creation timeline queries)
        Index('idx_created_at', 'created_at'),
        # Status-based queries
        Index('idx_is_active', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Security fields (added 2026-02-25)
    is_locked = db.Column(db.Boolean, default=False)  # Account locked due to failed login attempts
    locked_until = db.Column(db.DateTime, nullable=True)  # When lockout expires
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)  # Track password age
    # OAuth fields (added 2026-02-26)
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'facebook', 'kakao', etc.
    oauth_id = db.Column(db.String(255), nullable=True, unique=True)  # Platform-specific user ID
    avatar_url = db.Column(db.String(500), nullable=True)  # Profile picture URL
    # Email verification fields (added 2026-02-26)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    # Password reset fields (added 2026-02-26)
    reset_token = db.Column(db.String(128), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    # 2FA/TOTP fields (added 2026-02-26)
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded TOTP secret
    totp_enabled = db.Column(db.Boolean, default=False)  # 2FA enabled
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of encrypted backup codes
    backup_codes_used = db.Column(db.Text, default='[]')  # JSON array of used backup code indexes

    # Relationships with optimized lazy loading
    subscriptions = db.relationship('Subscription', backref='user', lazy='select', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy='select', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_accounts = db.relationship('SNSAccount', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_posts = db.relationship('SNSPost', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_campaigns = db.relationship('SNSCampaign', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_templates = db.relationship('SNSTemplate', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_analytics = db.relationship('SNSAnalytics', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_inbox = db.relationship('SNSInboxMessage', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_settings = db.relationship('SNSSettings', backref='user', lazy='select', cascade='all, delete-orphan', uselist=False)
    sns_link_in_bios = db.relationship('SNSLinkInBio', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_automates = db.relationship('SNSAutomate', backref='user', lazy='select', cascade='all, delete-orphan')
    sns_competitors = db.relationship('SNSCompetitor', backref='user', lazy='select', cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='creator', lazy='select', cascade='all, delete-orphan', foreign_keys='Campaign.creator_id')
    campaign_applications = db.relationship('CampaignApplication', backref='user', lazy='select', cascade='all, delete-orphan')
    review_accounts = db.relationship('ReviewAccount', backref='user', lazy='select', cascade='all, delete-orphan')
    review_auto_rules = db.relationship('ReviewAutoRule', backref='user', lazy='select', cascade='all, delete-orphan')
    ai_employees = db.relationship('AIEmployee', backref='user', lazy='select', cascade='all, delete-orphan')
    bootcamp_enrollments = db.relationship('BootcampEnrollment', backref='user', lazy='select', cascade='all, delete-orphan')
    webapps = db.relationship('WebApp', backref='user', lazy='select', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'oauth_provider': self.oauth_provider,
            'email_verified': self.email_verified if self.email_verified is not None else False,
            'totp_enabled': getattr(self, 'totp_enabled', False),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # emoji or icon name
    monthly_price = db.Column(db.Float, nullable=False)
    annual_price = db.Column(db.Float)
    stripe_price_id_monthly = db.Column(db.String(255))
    stripe_price_id_annual = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    subscriptions = db.relationship('Subscription', backref='product', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'monthly_price': self.monthly_price,
            'annual_price': self.annual_price,
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255))
    plan_type = db.Column(db.String(20), default='monthly')  # 'monthly' or 'annual'
    status = db.Column(db.String(20), default='active')  # 'active', 'canceled', 'expired'
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'plan_type': self.plan_type,
            'status': self.status,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ COOCOOK ============

class Chef(db.Model):
    __tablename__ = 'chefs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text)
    cuisine_type = db.Column(db.String(50))  # Korean, Italian, Japanese, French, Mexican
    location = db.Column(db.String(200))
    price_per_session = db.Column(db.Float, nullable=False)  # USD
    rating = db.Column(db.Float, default=5.0)
    rating_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='chef', lazy=True, cascade='all, delete-orphan')


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chef_id = db.Column(db.Integer, db.ForeignKey('chefs.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Integer, default=2)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'completed', 'canceled'
    total_price = db.Column(db.Float, nullable=False)
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class BookingPayment(db.Model):
    __tablename__ = "booking_payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="KRW")
    status = db.Column(db.String(20), default="completed")
    transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BookingReview(db.Model):
    __tablename__ = "booking_reviews"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    chef_id = db.Column(db.Integer, db.ForeignKey("chefs.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "chef_id": self.chef_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ShoppingList(db.Model):
    __tablename__ = 'shopping_lists'
    __table_args__ = (
        Index('idx_shopping_list_user', 'user_id'),
        Index('idx_shopping_list_created', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    items = db.Column(db.JSON, default=list)  # [{name, quantity, unit, checked, category}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'items': self.items or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============ SNS AUTO (v2.0) ============

class SNSAccount(db.Model):
    """SNS Account with expanded OAuth & analytics fields"""
    __tablename__ = 'sns_accounts'
    __table_args__ = (
        # User-platform lookup
        Index('idx_sns_account_user_platform', 'user_id', 'platform'),
        # Platform status queries (active accounts per platform)
        Index('idx_sns_account_platform_active', 'platform', 'is_active'),
        # User active accounts
        Index('idx_sns_account_user_active', 'user_id', 'is_active'),
        # OAuth lookup
        Index('idx_platform_user_id', 'platform', 'platform_user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # instagram, facebook, twitter, linkedin, tiktok, youtube, pinterest, threads, youtube_shorts
    account_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # OAuth fields (v2.0 new)
    access_token = db.Column(db.Text)  # Encrypted in production
    refresh_token = db.Column(db.Text)  # Encrypted in production
    token_expires_at = db.Column(db.DateTime)
    platform_user_id = db.Column(db.String(255))  # Platform-specific user ID
    profile_picture_url = db.Column(db.String(500))
    account_type = db.Column(db.String(50), default='personal')  # 'personal' or 'business'

    # Analytics fields (v2.0 new)
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    permissions_json = db.Column(db.JSON, default={})  # {read, write, analytics, messaging, ...}

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('SNSPost', backref='account', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('SNSAnalytics', backref='account', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'account_name': self.account_name,
            'is_active': self.is_active,
            'platform_user_id': self.platform_user_id,
            'profile_picture_url': self.profile_picture_url,
            'account_type': self.account_type,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'created_at': self.created_at.isoformat(),
        }


class SNSPost(db.Model):
    """SNS Post with analytics and campaign tracking"""
    __tablename__ = 'sns_posts'
    __table_args__ = (
        # User post timeline (most common query)
        Index('idx_sns_post_user_created', 'user_id', 'created_at'),
        # Platform status queries (filter by status & platform)
        Index('idx_sns_post_platform_status', 'platform', 'status'),
        # Scheduled posts (APScheduler job queue)
        Index('idx_sns_post_scheduled_at', 'scheduled_at'),
        # User-platform posts
        Index('idx_sns_post_user_platform', 'user_id', 'platform'),
        # Campaign posts
        Index('idx_sns_post_campaign_id', 'campaign_id'),
        # Account posts (N+1 prevention)
        Index('idx_sns_post_account_created', 'account_id', 'created_at'),
        # Published posts (analytics queries)
        Index('idx_sns_post_user_published', 'user_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('sns_accounts.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('sns_campaigns.id'), nullable=True)

    content = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='draft')  # 'draft', 'scheduled', 'published', 'failed'
    scheduled_at = db.Column(db.DateTime)
    published_at = db.Column(db.DateTime)
    template_type = db.Column(db.String(50))  # 'card_news', 'blog_post', 'reel', 'shorts', 'carousel'

    # Media & metadata (v2.0 new)
    media_urls = db.Column(db.JSON, default=[])  # List of image/video URLs
    hashtags = db.Column(db.JSON, default=[])  # List of hashtags
    link_url = db.Column(db.String(500))  # External URL in post

    # Platform fields (v2.0 new)
    external_post_id = db.Column(db.String(255))  # Platform-specific post ID
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    reach = db.Column(db.Integer, default=0)

    # Error handling (v2.0 new)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'campaign_id': self.campaign_id,
            'platform': self.platform,
            'content': self.content[:100] + ('...' if len(self.content) > 100 else ''),
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'likes': self.likes_count,
            'comments': self.comments_count,
            'views': self.views_count,
            'reach': self.reach,
            'created_at': self.created_at.isoformat(),
        }


class SNSCampaign(db.Model):
    """SNS Campaign — multi-post coordinated promotion"""
    __tablename__ = 'sns_campaigns'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    target_platforms = db.Column(db.JSON, default=[])  # ['instagram', 'tiktok', ...]
    status = db.Column(db.String(20), default='active', index=True)  # 'active', 'paused', 'completed'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('SNSPost', backref='campaign', lazy=True, cascade='all, delete-orphan', foreign_keys='SNSPost.campaign_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_platforms': self.target_platforms,
            'status': self.status,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'post_count': len(self.posts),
            'created_at': self.created_at.isoformat(),
        }


class SNSTemplate(db.Model):
    """Reusable SNS content templates"""
    __tablename__ = 'sns_templates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = system template
    name = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # specific platform or 'all'
    content_template = db.Column(db.Text, nullable=False)  # Content with {placeholders}
    hashtag_template = db.Column(db.Text)  # Hashtag with {placeholders}
    category = db.Column(db.String(50))  # 'promotional', 'educational', 'engagement', 'announcement'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'category': self.category,
            'content_template': self.content_template[:100],
        }


class SNSAnalytics(db.Model):
    """Daily SNS Analytics snapshot"""
    __tablename__ = 'sns_analytics'
    __table_args__ = (
        # Time-series analytics (date range queries)
        Index('idx_sns_analytics_account_date', 'account_id', 'date'),
        # User analytics timeline
        Index('idx_sns_analytics_user_date', 'user_id', 'date'),
        # Daily update queries
        Index('idx_sns_analytics_date', 'date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('sns_accounts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    followers = db.Column(db.Integer, default=0)
    total_engagement = db.Column(db.Integer, default=0)  # likes + comments + shares
    total_reach = db.Column(db.Integer, default=0)
    total_impressions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'followers': self.followers,
            'engagement': self.total_engagement,
            'reach': self.total_reach,
            'impressions': self.total_impressions,
        }


class SNSInboxMessage(db.Model):
    """Unified SNS Inbox (DMs, comments, mentions)"""
    __tablename__ = 'sns_inbox_messages'
    __table_args__ = (
        # User inbox (unread first, then by date)
        Index('idx_sns_inbox_user_status', 'user_id', 'status'),
        # Unread messages timeline
        Index('idx_sns_inbox_user_unread_created', 'user_id', 'status', 'created_at'),
        # Account messages
        Index('idx_sns_inbox_account_created', 'account_id', 'created_at'),
        # External ID lookup (platform message sync)
        Index('idx_sns_inbox_external_id', 'external_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('sns_accounts.id'), nullable=False)
    sender_name = db.Column(db.String(200), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50))  # 'dm', 'comment', 'mention'
    status = db.Column(db.String(20), default='unread')  # 'unread', 'read', 'replied'
    external_id = db.Column(db.String(255))  # Platform-specific message ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender_name,
            'text': self.message_text,
            'type': self.message_type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }


class SNSOAuthState(db.Model):
    """OAuth state token tracking (CSRF prevention)"""
    __tablename__ = 'sns_oauth_states'
    __table_args__ = (
        # State token lookup (CSRF verification)
        Index('idx_state_token', 'state_token'),
        # Expired state cleanup
        Index('idx_expires_at', 'expires_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    state_token = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SNSSettings(db.Model):
    """User SNS Settings"""
    __tablename__ = 'sns_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    auto_optimal_time = db.Column(db.Boolean, default=True)  # Auto-post at optimal time
    engagement_notifications = db.Column(db.Boolean, default=True)  # Notify on new engagement
    auto_reply_enabled = db.Column(db.Boolean, default=False)  # Auto-reply to comments
    banned_keywords = db.Column(db.JSON, default=[])  # Keywords to avoid in posts
    telegram_chat_id = db.Column(db.String(100), nullable=True)  # Telegram chat ID for SNS notifications (added 2026-02-26)
    telegram_enabled = db.Column(db.Boolean, default=False)  # Enable Telegram notifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'auto_optimal_time': self.auto_optimal_time,
            'engagement_notifications': self.engagement_notifications,
            'auto_reply_enabled': self.auto_reply_enabled,
            'banned_keywords': self.banned_keywords,
            'telegram_chat_id': self.telegram_chat_id,
            'telegram_enabled': self.telegram_enabled,
        }


class SNSLinkInBio(db.Model):
    """SNS Link In Bio — Single landing page with multiple links"""
    __tablename__ = 'sns_link_in_bios'
    __table_args__ = (
        # User link lookup
        Index('idx_sns_link_in_bio_user', 'user_id'),
        # Slug lookup (public access)
        Index('idx_sns_link_in_bio_slug', 'slug'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255))
    links = db.Column(db.JSON, default=[])  # [{url, label, icon}, ...]
    theme = db.Column(db.String(50), default='light')  # 'light', 'dark', custom theme name
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'links': self.links,
            'theme': self.theme,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SNSAutomate(db.Model):
    """SNS Automation Rule — Auto-posting to multiple platforms"""
    __tablename__ = 'sns_automates'
    __table_args__ = (
        # User automation lookup
        Index('idx_sns_automate_user_active', 'user_id', 'is_active'),
        # Scheduler queries (find next jobs to run)
        Index('idx_sns_automate_next_run', 'next_run'),
        # Active automation rules
        Index('idx_sns_automate_active', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(500))  # e.g., "AI news", "Product tips"
    purpose = db.Column(db.String(500))  # '홍보' (promotion), '판매' (sales), '커뮤니티' (community)
    platforms = db.Column(db.JSON, default=[])  # ['instagram', 'twitter', 'tiktok', ...]
    frequency = db.Column(db.String(50), default='daily')  # 'daily', 'weekly', 'custom'
    next_run = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'topic': self.topic,
            'purpose': self.purpose,
            'platforms': self.platforms,
            'frequency': self.frequency,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SNSCompetitor(db.Model):
    """SNS Competitor tracking — Track competitor accounts & analytics"""
    __tablename__ = 'sns_competitors'
    __table_args__ = (
        # User competitor lookup
        Index('idx_competitor_user_platform', 'user_id', 'platform'),
        # Platform competitor search
        Index('idx_competitor_platform_username', 'platform', 'username'),
        # Last analysis time (for scheduling updates)
        Index('idx_competitor_last_analyzed', 'last_analyzed'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # instagram, facebook, twitter, etc.
    username = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True)  # Display name for the competitor
    followers_count = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)  # percentage
    avg_likes = db.Column(db.Integer, default=0)
    avg_comments = db.Column(db.Integer, default=0)
    posting_frequency = db.Column(db.String(50))  # 'daily', 'weekly', 'random'
    data = db.Column(db.JSON, default={})  # Additional competitor data (hashtags, content themes, etc.)
    last_analyzed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'username': self.username,
            'name': self.name or self.username,
            'followers_count': self.followers_count,
            'engagement_rate': self.engagement_rate,
            'avg_likes': self.avg_likes,
            'avg_comments': self.avg_comments,
            'posting_frequency': self.posting_frequency,
            'data': self.data,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ReviewListing(db.Model):
    """Review Listing — Brand review opportunities from various platforms"""
    __tablename__ = 'review_listings'
    __table_args__ = (
        # Platform scraping (fetch new listings)
        Index('idx_source_platform_scraped', 'source_platform', 'scraped_at'),
        # Active listings (filtering & pagination)
        Index('idx_category_deadline', 'category', 'deadline'),
        # Reward range queries
        Index('idx_reward_value', 'reward_value'),
        # Status filtering (active, closed, ended)
        Index('idx_status_created', 'status', 'scraped_at'),
        # Duplicate prevention (external_id lookup)
        Index('idx_external_id_platform', 'external_id', 'source_platform'),
        # Deadline queries (expired listings cleanup)
        Index('idx_deadline', 'deadline'),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_platform = db.Column(db.String(50), nullable=False)  # 'revu', 'reviewplace', 'wible', ...
    external_id = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    brand = db.Column(db.String(255))
    category = db.Column(db.String(100))
    reward_type = db.Column(db.String(50))  # '상품' (product), '금전' (cash), '경험' (experience)
    reward_value = db.Column(db.Integer)  # KRW amount
    requirements = db.Column(db.JSON, default={})  # {follower_min, tags, demographics, etc.}
    deadline = db.Column(db.DateTime)
    max_applicants = db.Column(db.Integer)
    current_applicants = db.Column(db.Integer, default=0)
    url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    applied_accounts = db.Column(db.JSON, default=[])  # [account_ids]
    status = db.Column(db.String(50), default='active')  # 'active', 'closed', 'ended'
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('ReviewApplication', backref='listing', lazy='select', cascade='all, delete-orphan')
    bookmarks = db.relationship('ReviewBookmark', backref='listing', lazy='select', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'source_platform': self.source_platform,
            'external_id': self.external_id,
            'title': self.title,
            'brand': self.brand,
            'category': self.category,
            'reward_type': self.reward_type,
            'reward_value': self.reward_value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'max_applicants': self.max_applicants,
            'current_applicants': self.current_applicants,
            'url': self.url,
            'image_url': self.image_url,
            'status': self.status,
            'created_at': self.scraped_at.isoformat() if self.scraped_at else None,
        }


class ReviewBookmark(db.Model):
    """Review Bookmark — User bookmarked review listing"""
    __tablename__ = 'review_bookmarks'
    __table_args__ = (
        # User bookmarks
        Index('idx_user_listing', 'user_id', 'listing_id'),
        # Listing bookmarks count
        Index('idx_listing_id', 'listing_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('review_listings.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'created_at': self.created_at.isoformat(),
        }


class ReviewAccount(db.Model):
    """Review Account — User's account for review applications"""
    __tablename__ = 'review_accounts'
    __table_args__ = (
        # User's accounts lookup
        Index('idx_review_account_user', 'user_id'),
        # User+platform duplicate check
        Index('idx_review_account_user_platform', 'user_id', 'platform'),
        # Active accounts filtering
        Index('idx_review_account_user_active', 'user_id', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # 'naver', 'instagram', 'blog', 'youtube', 'tiktok'
    account_name = db.Column(db.String(255), nullable=False)
    credentials_enc = db.Column(db.String(1000))  # Encrypted credentials (base64)
    follower_count = db.Column(db.Integer, default=0)
    category_tags = db.Column(db.JSON, default=[])  # ['패션' (fashion), '뷰티' (beauty), ...]
    success_rate = db.Column(db.Float, default=0.0)  # 0.0-1.0 (percentage of successful applications)
    last_reviewed = db.Column(db.DateTime, nullable=True)  # Last review date (added 2026-02-26)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship('ReviewApplication', backref='account', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'account_name': self.account_name,
            'follower_count': self.follower_count,
            'category_tags': self.category_tags,
            'success_rate': self.success_rate,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ReviewApplication(db.Model):
    """Review Application — User applying for a review listing"""
    __tablename__ = 'review_applications'
    __table_args__ = (
        # User application history
        Index('idx_review_app_account_created', 'account_id', 'applied_at'),
        # Listing applications (check if user already applied)
        Index('idx_listing_account', 'listing_id', 'account_id'),
        # User progress (active applications)
        Index('idx_user_status', 'account_id', 'status'),
        # Status timeline
        Index('idx_review_app_status_created', 'status', 'applied_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('review_listings.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('review_accounts.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'selected', 'rejected', 'completed'
    result = db.Column(db.String(500))  # Summary of application result
    review_url = db.Column(db.String(500))  # URL to posted review
    review_posted_at = db.Column(db.DateTime)  # Review posting date
    review_content = db.Column(db.Text)  # Review content summary (added 2026-02-26)

    def to_dict(self):
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'account_id': self.account_id,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'status': self.status,
            'result': self.result,
            'review_url': self.review_url,
            'review_posted_at': self.review_posted_at.isoformat() if self.review_posted_at else None,
            'review_content': self.review_content,
        }


class ReviewAutoRule(db.Model):
    """Review Automation Rule — Auto-apply to matching review listings"""
    __tablename__ = 'review_auto_rules'
    __table_args__ = (
        # User rules lookup
        Index('idx_review_rule_user_active', 'user_id', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    target_categories = db.Column(db.JSON, default=[])  # ['패션', '뷰티', ...]
    min_reward = db.Column(db.Integer, default=0)  # Minimum reward value in KRW
    max_reward = db.Column(db.Integer)  # Maximum reward value in KRW (optional)
    apply_deadline_days = db.Column(db.Integer, default=30)  # Only apply to listings ending within this many days
    max_applicants_ratio = db.Column(db.Float, default=0.5)  # Max applicant ratio threshold (0.0-1.0)
    preferred_accounts = db.Column(db.JSON, default=[])  # [account_ids] to prefer for applications
    reward_types = db.Column(db.JSON, default=[])  # ['상품', '금전', '경험'] - which reward types to match
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_categories': self.target_categories,
            'min_reward': self.min_reward,
            'max_reward': self.max_reward,
            'apply_deadline_days': self.apply_deadline_days,
            'max_applicants_ratio': self.max_applicants_ratio,
            'preferred_accounts': self.preferred_accounts,
            'reward_types': self.reward_types,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ============ REVIEW CAMPAIGNS ============

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    __table_args__ = (
        # Status filtering (active campaigns list)
        Index('idx_campaign_status', 'status'),
        # Creator's campaigns lookup
        Index('idx_campaign_creator', 'creator_id'),
        # Active campaigns by category (filtered browsing)
        Index('idx_campaign_status_category', 'status', 'category'),
        # Deadline queries (expiry checks)
        Index('idx_campaign_deadline', 'deadline'),
    )

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'beauty', 'food', 'tech', 'fashion'
    reward_type = db.Column(db.String(50))  # 'product', 'cash', 'both'
    reward_value = db.Column(db.String(200))  # e.g., "$50" or "Free product"
    max_reviewers = db.Column(db.Integer, default=10)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('CampaignApplication', backref='campaign', lazy='select', cascade='all, delete-orphan')


class CampaignApplication(db.Model):
    __tablename__ = 'campaign_applications'
    __table_args__ = (
        # Campaign applications list
        Index('idx_campaign_app_campaign', 'campaign_id'),
        # User's applications
        Index('idx_campaign_app_user', 'user_id'),
        # Duplicate check (one application per user per campaign)
        Index('idx_campaign_app_campaign_user', 'campaign_id', 'user_id'),
        # Status filtering
        Index('idx_campaign_app_status', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)  # Why they want to review
    sns_link = db.Column(db.String(500))
    follower_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ AI AUTOMATION ============

class AIEmployee(db.Model):
    """AI Employee (Automation Instance)"""
    __tablename__ = 'ai_employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    scenario_type = db.Column(db.String(50), nullable=False)  # email, social, customer_service, data_entry, scheduling
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, training, active, paused
    monthly_savings_hours = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'description': self.description,
            'status': self.status,
            'monthly_savings_hours': self.monthly_savings_hours,
            'created_at': self.created_at.isoformat(),
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None
        }


class Scenario(db.Model):
    """Pre-built Automation Scenario Template"""
    __tablename__ = 'scenarios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # email, social, customer_service, data_entry, scheduling
    description = db.Column(db.Text)
    estimated_savings = db.Column(db.Integer)  # hours/month
    complexity = db.Column(db.String(20))  # easy, medium, advanced
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'estimated_savings': self.estimated_savings,
            'complexity': self.complexity,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat()
        }


# ============ WEBAPP BUILDER ============

class BootcampEnrollment(db.Model):
    """User enrolled in bootcamp course"""
    __tablename__ = 'bootcamp_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # 'weekday' or 'weekend'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='enrolled')  # enrolled, in_progress, completed, dropped
    progress = db.Column(db.Integer, default=0)  # 0-100%
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan_type,
            'status': self.status,
            'progress': self.progress,
            'start': self.start_date.isoformat(),
            'end': self.end_date.isoformat(),
            'days_remaining': (self.end_date - datetime.utcnow()).days
        }


class WebApp(db.Model):
    """User's built webapp"""
    __tablename__ = 'webapps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500))  # Live URL
    status = db.Column(db.String(20), default='draft')  # draft, building, deployed, live
    code_repo = db.Column(db.String(500))  # GitHub URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'url': self.url,
            'repo': self.code_repo,
            'created': self.created_at.isoformat(),
            'deployed': self.deployed_at.isoformat() if self.deployed_at else None
        }


# ============ EXPERIENCE ============

class ExperienceListing(db.Model):
    __tablename__ = 'experience_listings'

    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(50), nullable=False)  # 'coupang_eats', 'danggeun', 'soomgo', etc.
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    deadline = db.Column(db.DateTime)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    reward = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'site': self.site,
            'title': self.title,
            'url': self.url,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'image_url': self.image_url,
            'category': self.category,
            'description': self.description,
            'reward': self.reward,
            'created_at': self.created_at.isoformat()
        }


class CrawlerLog(db.Model):
    __tablename__ = 'crawler_logs'

    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(50), nullable=False)
    listing_count = db.Column(db.Integer, default=0)
    last_crawl_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')  # 'success', 'error'
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'site': self.site,
            'listing_count': self.listing_count,
            'last_crawl_time': self.last_crawl_time.isoformat(),
            'status': self.status
        }


# ============ SECURITY ============

class LoginAttempt(db.Model):
    """Track login attempts for rate limiting and security auditing"""
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # Supports IPv4 and IPv6
    success = db.Column(db.Boolean, default=False)  # True if login succeeded, False if failed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_agent = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'ip_address': self.ip_address,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
        }


class ErrorLog(db.Model):
    """Error logging for all projects (M-001, M-002, etc.)"""
    __tablename__ = 'error_logs'

    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(255), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    context = db.Column(db.JSON)  # {user_id, endpoint, method, status_code, ...}
    project_id = db.Column(db.String(50), index=True)  # M-001, M-002, etc.
    severity = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    resolved = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'error_type': self.error_type,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'context': self.context,
            'project_id': self.project_id,
            'severity': self.severity,
            'resolved': self.resolved
        }


class ErrorPattern(db.Model):
    """Detected error patterns for root cause analysis"""
    __tablename__ = 'error_patterns'

    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(255), nullable=False, unique=True, index=True)
    frequency = db.Column(db.Integer, default=0)  # Total occurrences
    first_seen = db.Column(db.DateTime, nullable=False, index=True)
    last_seen = db.Column(db.DateTime, nullable=False)
    severity = db.Column(db.String(20), default='medium')
    root_cause = db.Column(db.String(500))
    resolution = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'error_type': self.error_type,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'severity': self.severity,
            'root_cause': self.root_cause,
            'resolution': self.resolution,
            'is_active': self.is_active
        }


def init_db(app):
    """Initialize database with tables and seed data"""
    with app.app_context():
        db.create_all()

        # Check if data already exists
        if User.query.count() > 0:
            return

        # Create admin user
        admin = User(email='admin@softfactory.com', name='Admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # Create 5 products
        products = [
            Product(slug='coocook', name='CooCook', description='Local food experiences & chef booking',
                   icon='🍳', monthly_price=29.0, annual_price=290.0),
            Product(slug='sns-auto', name='SNS Auto', description='Auto-post to Instagram, Blog, TikTok, Shorts',
                   icon='📱', monthly_price=49.0, annual_price=490.0),
            Product(slug='review', name='Review Campaign', description='Brand review & influencer campaigns',
                   icon='⭐', monthly_price=39.0, annual_price=390.0),
            Product(slug='ai-automation', name='AI Automation', description='24/7 AI employees for business automation',
                   icon='🤖', monthly_price=89.0, annual_price=890.0),
            Product(slug='webapp-builder', name='WebApp Builder', description='8-week bootcamp: Learn automation + build your own web app',
                   icon='💻', monthly_price=590000.0, annual_price=None),
        ]
        for product in products:
            db.session.add(product)

        # Create sample user
        user = User(email='demo@softfactory.com', name='Demo User', role='user')
        user.set_password('demo123')
        db.session.add(user)

        db.session.commit()

        # Create sample chefs (after commit to get user_id)
        chefs = [
            Chef(user_id=user.id, name='Chef Park', bio='Korean traditional cuisine',
                cuisine_type='Korean', location='Seoul', price_per_session=120.0),
            Chef(user_id=user.id, name='Chef Marco', bio='Italian pasta & risotto expert',
                cuisine_type='Italian', location='Seoul', price_per_session=130.0),
            Chef(user_id=user.id, name='Chef Tanaka', bio='Authentic Japanese sushi master',
                cuisine_type='Japanese', location='Seoul', price_per_session=150.0),
            Chef(user_id=user.id, name='Chef Dubois', bio='French culinary techniques',
                cuisine_type='French', location='Seoul', price_per_session=140.0),
            Chef(user_id=user.id, name='Chef Garcia', bio='Authentic Mexican street food',
                cuisine_type='Mexican', location='Seoul', price_per_session=110.0),
        ]
        for chef in chefs:
            db.session.add(chef)

        # Create sample campaigns
        campaigns = [
            Campaign(creator_id=admin.id, title='New Skincare Product Launch',
                    product_name='GlowSkin Pro', category='beauty',
                    reward_type='product', reward_value='Free $150 skincare kit',
                    max_reviewers=20, deadline=datetime.utcnow() + timedelta(days=30)),
            Campaign(creator_id=admin.id, title='Organic Coffee Brand Review',
                    product_name='BeanBliss Coffee', category='food',
                    reward_type='cash', reward_value='$50 gift card',
                    max_reviewers=15, deadline=datetime.utcnow() + timedelta(days=25)),
            Campaign(creator_id=admin.id, title='Latest Tech Gadget Review',
                    product_name='SmartHub X3', category='tech',
                    reward_type='both', reward_value='Product + $75 bonus',
                    max_reviewers=10, deadline=datetime.utcnow() + timedelta(days=20)),
        ]
        for campaign in campaigns:
            db.session.add(campaign)

        # Create sample automation scenarios
        scenarios = [
            Scenario(name='Email Response Automation', category='email', complexity='easy',
                    description='AI automatically responds to customer emails', estimated_savings=15, is_premium=False),
            Scenario(name='Social Media Posting', category='social', complexity='medium',
                    description='AI writes and posts content to social media', estimated_savings=20, is_premium=False),
            Scenario(name='Customer Support Bot', category='customer_service', complexity='advanced',
                    description='24/7 AI customer support with escalation to humans', estimated_savings=30, is_premium=True),
            Scenario(name='Data Entry Automation', category='data_entry', complexity='medium',
                    description='AI extracts and enters data from documents', estimated_savings=25, is_premium=False),
            Scenario(name='Meeting Scheduling', category='scheduling', complexity='easy',
                    description='AI manages calendar and schedules meetings', estimated_savings=10, is_premium=False),
        ]
        for scenario in scenarios:
            db.session.add(scenario)

        db.session.commit()


# ============ FILE STORAGE ============

class FileUpload(db.Model):
    """Cloud storage metadata for S3-uploaded files"""
    __tablename__ = 'file_uploads'
    __table_args__ = (
        Index('idx_user_id_files', 'user_id'),
        Index('idx_category', 'category'),
        Index('idx_uploaded_at', 'uploaded_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_key = db.Column(db.String(500), unique=True, nullable=False)  # S3 object key
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    content_type = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'image', 'video', 'document'
    s3_url = db.Column(db.String(500), nullable=False)
    cdn_url = db.Column(db.String(500), nullable=True)  # CloudFront URL if configured
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # For temporary uploads

    user = db.relationship('User', backref=db.backref('uploads', lazy='select'))

    def to_dict(self):
        return {
            'id': self.id,
            'file_key': self.file_key,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'category': self.category,
            's3_url': self.s3_url,
            'cdn_url': self.cdn_url,
            'uploaded_at': self.uploaded_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


# ============ ORDERS & INVOICING ============

class Order(db.Model):
    """Customer orders for SoftFactory products/services"""
    __tablename__ = 'orders'
    __table_args__ = (
        Index('idx_user_id_orders', 'user_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at_orders', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, canceled

    # Items & pricing (KRW - Korean Won)
    items_json = db.Column(db.Text, nullable=False)  # JSON array of {product_id, quantity, price_krw}
    subtotal_krw = db.Column(db.Integer, nullable=False)  # Sum of item prices
    tax_krw = db.Column(db.Integer, default=0)
    discount_krw = db.Column(db.Integer, default=0)
    total_amount_krw = db.Column(db.Integer, nullable=False)

    # Metadata
    currency = db.Column(db.String(3), default='KRW')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('orders', lazy='select'))
    # Invoice relationship - single direction via Invoice.order_id FK
    invoices = db.relationship('Invoice', backref='order', lazy='select', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'subtotal_krw': self.subtotal_krw,
            'tax_krw': self.tax_krw,
            'discount_krw': self.discount_krw,
            'total_amount_krw': self.total_amount_krw,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Invoice(db.Model):
    """PDF invoices for orders"""
    __tablename__ = 'invoices'
    __table_args__ = (
        Index('idx_order_id', 'order_id'),
        Index('idx_user_id_invoices', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)

    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    pdf_file_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id'), nullable=True)

    # Invoice details
    amount_krw = db.Column(db.Integer, nullable=False)
    tax_krw = db.Column(db.Integer, default=0)
    total_krw = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(50), default='draft')  # draft, issued, paid, canceled
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    paid_date = db.Column(db.DateTime, nullable=True)

    # Payment tracking
    stripe_invoice_id = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)  # 'stripe', 'bank_transfer', etc.

    user = db.relationship('User', backref=db.backref('invoices', lazy='select'))
    pdf = db.relationship('FileUpload', backref=db.backref('invoices', lazy='select'))

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'amount_krw': self.amount_krw,
            'tax_krw': self.tax_krw,
            'total_krw': self.total_krw,
            'status': self.status,
            'issued_date': self.issued_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'stripe_invoice_id': self.stripe_invoice_id,
            'payment_method': self.payment_method,
        }


class SubscriptionPlan(db.Model):
    """Flexible subscription plans"""
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Pricing (KRW)
    monthly_price_krw = db.Column(db.Integer, nullable=False)
    annual_price_krw = db.Column(db.Integer, nullable=False)

    # Stripe IDs
    stripe_price_id_monthly = db.Column(db.String(100), nullable=True)
    stripe_price_id_annual = db.Column(db.String(100), nullable=True)

    # Features
    features_json = db.Column(db.Text, nullable=True)  # JSON array of feature strings
    max_projects = db.Column(db.Integer, nullable=True)
    max_users = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'monthly_price_krw': self.monthly_price_krw,
            'annual_price_krw': self.annual_price_krw,
            'features': json.loads(self.features_json) if self.features_json else [],
            'max_projects': self.max_projects,
            'max_users': self.max_users,
            'is_active': self.is_active,
        }


# ============ SECURITY & ENCRYPTION ============

class APIKey(db.Model):
    """
    API Key management with encryption and rotation support.

    - Keys are encrypted at rest
    - Automatic expiration after 30 days (configurable)
    - Last used tracking for security audits
    - Soft delete support (is_active flag)
    """
    __tablename__ = 'api_keys'
    __table_args__ = (
        Index('idx_apikey_user_id', 'user_id'),
        Index('idx_apikey_is_active', 'is_active'),
        Index('idx_apikey_expires_at', 'expires_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Key metadata
    name = db.Column(db.String(100), nullable=False)  # User-friendly name
    prefix = db.Column(db.String(20), nullable=False, unique=True)  # pk_xxx prefix for partial display

    # The actual key is encrypted (stored as Fernet token)
    encrypted_key = db.Column(db.Text, nullable=False)

    # Lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)  # Default: created_at + 30 days
    is_active = db.Column(db.Boolean, default=True)  # Soft delete

    # Scopes/permissions (JSON array)
    scopes = db.Column(db.Text, nullable=True)  # e.g., '["read:projects", "write:sns"]'

    # Audit trail
    revoked_at = db.Column(db.DateTime, nullable=True)
    revocation_reason = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('api_keys', lazy='select'))

    def to_dict(self, include_key=False):
        """Return API key as dictionary (key included only on creation)"""
        data = {
            'id': self.id,
            'name': self.name,
            'prefix': self.prefix,
            'created_at': self.created_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
            'scopes': self.scopes.split(',') if self.scopes else [],
        }
        if include_key:
            data['key'] = self.encrypted_key  # Only on creation
        return data

    def is_expired(self):
        """Check if key has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if key is valid (active and not expired)"""
        return self.is_active and not self.is_expired()


class AuditLog(db.Model):
    """
    Security audit log for tracking sensitive operations.

    - Encryption/decryption access
    - API key operations (create, revoke, rotate)
    - Failed authentication attempts
    - Data access logging
    """
    __tablename__ = 'audit_logs'
    __table_args__ = (
        Index('idx_auditlog_user_id', 'user_id'),
        Index('idx_auditlog_action', 'action'),
        Index('idx_auditlog_timestamp', 'timestamp'),
        Index('idx_auditlog_resource_type', 'resource_type'),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Action classification
    action = db.Column(db.String(50), nullable=False)  # e.g., 'api_key_created', 'field_encrypted', 'field_decrypted'
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., 'api_key', 'user', 'project'
    resource_id = db.Column(db.Integer, nullable=True)

    # Request metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)

    # Action details
    status = db.Column(db.String(20), default='success')  # 'success', 'failure'
    details = db.Column(db.Text, nullable=True)  # JSON or free text

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='select'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
        }


class EncryptionKeyRotation(db.Model):
    """
    Track encryption key rotations for compliance and recovery.

    - Maintains history of all key versions
    - Timestamp of rotation
    - Identifies which records were rotated
    """
    __tablename__ = 'encryption_key_rotations'
    __table_args__ = (
        Index('idx_keyrotation_timestamp', 'timestamp'),
        Index('idx_keyrotation_rotation_status', 'rotation_status'),
    )

    id = db.Column(db.Integer, primary_key=True)

    # Key version identifier (not the actual key!)
    old_key_version = db.Column(db.String(50), nullable=False)
    new_key_version = db.Column(db.String(50), nullable=False)

    # Rotation metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    initiated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Progress tracking
    rotation_status = db.Column(db.String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'failed'
    total_records = db.Column(db.Integer, default=0)
    rotated_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)

    # Details
    notes = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)

    initiated_by = db.relationship('User', backref=db.backref('key_rotations', lazy='select'))

    def to_dict(self):
        return {
            'id': self.id,
            'old_key_version': self.old_key_version,
            'new_key_version': self.new_key_version,
            'timestamp': self.timestamp.isoformat(),
            'rotation_status': self.rotation_status,
            'total_records': self.total_records,
            'rotated_records': self.rotated_records,
            'failed_records': self.failed_records,
            'progress_percent': int((self.rotated_records / self.total_records * 100) if self.total_records > 0 else 0),
        }

    def is_complete(self):
        """Check if rotation is complete"""
        return self.rotation_status == 'completed'


# ============ COOCOOK ============

class Recipe(db.Model):
    """Recipe model for CooCook service"""
    __tablename__ = 'recipes'
    __table_args__ = (
        Index('idx_cuisine', 'cuisine'),
        Index('idx_difficulty', 'difficulty'),
        Index('idx_prep_time', 'prep_time'),
        Index('idx_chef_id', 'chef_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    cuisine = db.Column(db.String(50), nullable=False)  # e.g., 'Korean', 'Italian', 'Thai'
    difficulty = db.Column(db.String(20), nullable=False)  # 'easy', 'medium', 'hard'
    prep_time = db.Column(db.Integer, nullable=False)  # minutes
    servings = db.Column(db.Integer, nullable=False)  # number of servings
    ingredients_json = db.Column(db.JSON, nullable=False)  # [{'name': 'salt', 'amount': 1, 'unit': 'tsp'}, ...]
    nutrition_json = db.Column(db.JSON, nullable=True)  # {'calories': 250, 'protein': 15, 'carbs': 30, 'fat': 8}
    chef_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)  # optional premium recipe price
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Float, default=0.0)  # average rating (1-5)
    review_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)

    # Relationships
    chef = db.relationship('User', backref=db.backref('recipes', lazy='select'), foreign_keys=[chef_id])
    reviews = db.relationship('RecipeReview', backref='recipe', lazy='select', cascade='all, delete-orphan')
    likes = db.relationship('RecipeLike', backref='recipe', lazy='select', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cuisine': self.cuisine,
            'difficulty': self.difficulty,
            'prep_time': self.prep_time,
            'servings': self.servings,
            'ingredients': self.ingredients_json,
            'nutrition': self.nutrition_json,
            'chef_id': self.chef_id,
            'description': self.description,
            'price': self.price,
            'rating': self.rating,
            'review_count': self.review_count,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def update_rating(self):
        """Update recipe rating based on reviews"""
        from sqlalchemy import func
        avg_rating = db.session.query(func.avg(RecipeReview.rating)).filter(
            RecipeReview.recipe_id == self.id
        ).scalar()
        self.rating = round(avg_rating, 2) if avg_rating else 0.0
        self.review_count = db.session.query(func.count(RecipeReview.id)).filter(
            RecipeReview.recipe_id == self.id
        ).scalar() or 0
        db.session.commit()


class RecipeReview(db.Model):
    """Reviews and ratings for recipes"""
    __tablename__ = 'recipe_reviews'
    __table_args__ = (
        Index('idx_review_recipe_id', 'recipe_id'),
        Index('idx_review_user_id', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    text = db.Column(db.Text, nullable=True)  # review comment
    photos_json = db.Column(db.JSON, nullable=True)  # [{'url': '...', 'caption': '...'}, ...]
    photos = db.Column(db.JSON, nullable=True)  # Alternative field name
    helpful_count = db.Column(db.Integer, default=0)  # Number of helpful votes
    unhelpful_count = db.Column(db.Integer, default=0)  # Number of unhelpful votes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('recipe_reviews', lazy='select', overlaps='recipe_reviews_alt'),
        overlaps='recipe_reviews_alt'
    )
    reviewer = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('recipe_reviews_alt', lazy='select', overlaps='recipe_reviews'),
        overlaps='recipe_reviews,user'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'text': self.text,
            'photos': self.photos_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class RecipeLike(db.Model):
    """User likes on recipes"""
    __tablename__ = 'recipe_likes'
    __table_args__ = (
        Index('idx_like_recipe_id', 'recipe_id'),
        Index('idx_like_user_id', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('recipe_likes', lazy='select'), foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ShoppingListItem(db.Model):
    """Items in a shopping list"""
    __tablename__ = 'shopping_list_items'
    __table_args__ = (
        Index('idx_item_list_id', 'list_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=False)
    ingredient = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # 'cup', 'tbsp', 'tsp', 'g', 'kg', 'ml', 'l', 'pcs'
    estimated_price = db.Column(db.Float, nullable=True)  # price estimate
    is_checked = db.Column(db.Boolean, default=False)  # whether it's been crossed off

    def to_dict(self):
        return {
            'id': self.id,
            'list_id': self.list_id,
            'ingredient': self.ingredient,
            'quantity': self.quantity,
            'unit': self.unit,
            'estimated_price': self.estimated_price,
            'is_checked': self.is_checked,
        }


class UserFollow(db.Model):
    """User follow relationships"""
    __tablename__ = 'user_follows'
    __table_args__ = (
        Index('idx_follow_follower_id', 'follower_id'),
        Index('idx_follow_following_id', 'following_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    follower = db.relationship('User', backref=db.backref('following', lazy='select'), foreign_keys=[follower_id])
    followed = db.relationship('User', backref=db.backref('followers', lazy='select'), foreign_keys=[following_id])

    def to_dict(self):
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'following_id': self.following_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Feed(db.Model):
    """User activity feed"""
    __tablename__ = 'feeds'
    __table_args__ = (
        Index('idx_feed_user_id', 'user_id'),
        Index('idx_feed_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'recipe_published', 'recipe_liked', 'recipe_reviewed', 'user_followed', 'comment_added'
    content_json = db.Column(db.JSON, nullable=True)  # dynamic content based on activity type
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('feed_activities', lazy='select'), foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'content': self.content_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CookingSession(db.Model):
    """User cooking sessions"""
    __tablename__ = 'cooking_sessions'
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_recipe_id', 'recipe_id'),
        Index('idx_session_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'abandoned'
    notes = db.Column(db.Text, nullable=True)  # User's notes about the cooking session
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('cooking_sessions', lazy='select'), foreign_keys=[user_id])
    recipe = db.relationship('Recipe', backref=db.backref('cooking_sessions', lazy='select'), foreign_keys=[recipe_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipe_id': self.recipe_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ============ RBAC (Role-Based Access Control) ============

class Role(db.Model):
    """Role model for RBAC — Groups permissions for different user types."""
    __tablename__ = 'roles'
    __table_args__ = (
        Index('idx_role_name', 'name'),
        Index('idx_role_is_active', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 'admin', 'moderator', 'creator', 'user'
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = db.relationship(
        'Permission',
        secondary='role_permissions',
        backref=db.backref('roles', lazy='select'),
        lazy='select'
    )
    users = db.relationship(
        'User',
        secondary='user_roles',
        foreign_keys='[UserRole.role_id, UserRole.user_id]',
        backref=db.backref('roles', lazy='select'),
        lazy='select'
    )

    def to_dict(self, include_permissions=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_permissions:
            data['permissions'] = [p.to_dict() for p in self.permissions]
        return data


class Permission(db.Model):
    """Permission model — Granular access control actions."""
    __tablename__ = 'permissions'
    __table_args__ = (
        Index('idx_permission_name', 'name'),
        Index('idx_permission_resource', 'resource'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., 'write:sns_posts', 'delete:users'
    resource = db.Column(db.String(50), nullable=False)  # e.g., 'sns_posts', 'users', 'payments'
    action = db.Column(db.String(50), nullable=False)  # e.g., 'create', 'read', 'update', 'delete', 'moderate'
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'resource': self.resource,
            'action': self.action,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class RolePermission(db.Model):
    """Junction table for Role-Permission many-to-many relationship."""
    __tablename__ = 'role_permissions'
    __table_args__ = (
        Index('idx_role_perm_role_id', 'role_id'),
        Index('idx_role_perm_perm_id', 'permission_id'),
    )

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserRole(db.Model):
    """Junction table for User-Role many-to-many relationship."""
    __tablename__ = 'user_roles'
    __table_args__ = (
        Index('idx_user_role_user_id', 'user_id'),
        Index('idx_user_role_role_id', 'role_id'),
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who assigned this role
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional: temporary role assignment

    # Relationships
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id], backref='assigned_roles_by')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'role_id': self.role_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'assigned_by_id': self.assigned_by_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


class SearchHistory(db.Model):
    """Search query history for analytics and personalization"""
    __tablename__ = 'search_history'
    __table_args__ = (
        Index('idx_search_history_user', 'user_id'),
        Index('idx_search_history_index', 'index'),
        Index('idx_search_history_created', 'created_at'),
        Index('idx_search_history_user_created', 'user_id', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    index = db.Column(db.String(50), nullable=False)  # 'recipes', 'sns_posts', 'users'
    result_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='search_history')

    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'index': self.index,
            'result_count': self.result_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class RoleAuditLog(db.Model):
    """Audit log for RBAC changes — Track all role and permission modifications."""
    __tablename__ = 'role_audit_logs'
    __table_args__ = (
        Index('idx_rbac_audit_user_id', 'user_id'),
        Index('idx_rbac_audit_action', 'action'),
        Index('idx_rbac_audit_timestamp', 'timestamp'),
        Index('idx_rbac_audit_target_user', 'target_user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)

    # Who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # What happened
    action = db.Column(db.String(50), nullable=False)  # 'assign_role', 'remove_role', 'grant_permission', 'revoke_permission'
    target_type = db.Column(db.String(50), nullable=False)  # 'user', 'role'
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    target_permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=True)

    # Request metadata
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # Details
    status = db.Column(db.String(20), default='success')  # 'success', 'failure'
    details = db.Column(db.Text, nullable=True)  # JSON or details

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    actor = db.relationship('User', foreign_keys=[user_id], backref='rbac_audit_logs_made')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='rbac_audit_logs_received')
    target_role = db.relationship('Role', backref='audit_logs')
    target_permission = db.relationship('Permission', backref='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'target_type': self.target_type,
            'target_user_id': self.target_user_id,
            'target_role_id': self.target_role_id,
            'target_permission_id': self.target_permission_id,
            'ip_address': self.ip_address,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


# ============ WEBSOCKET / NOTIFICATIONS ============

class Notification(db.Model):
    """User notifications — supports multiple notification types."""
    __tablename__ = 'notifications'
    __table_args__ = (
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'sns_publish', 'comment', 'like', 'order', 'message', etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_url = db.Column(db.String(500), nullable=True)  # Link to take action on notification
    icon = db.Column(db.String(50), nullable=True)  # Material icon name
    extra_data = db.Column(db.JSON, nullable=True)  # Extra data (post_id, order_id, etc.)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationship
    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'action_url': self.action_url,
            'icon': self.icon,
            'extra_data': self.extra_data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }


class ChatMessage(db.Model):
    """Chat messages between users."""
    __tablename__ = 'chat_messages'
    __table_args__ = (
        Index('idx_chat_from_user_id', 'from_user_id'),
        Index('idx_chat_to_user_id', 'to_user_id'),
        Index('idx_chat_created_at', 'created_at'),
        Index('idx_chat_is_read', 'is_read'),
    )

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='sent_messages')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'from_user_name': self.from_user.name if self.from_user else None,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }


# ============ VIDEO PROCESSING ============

class Video(db.Model):
    """Video metadata and processing status"""
    __tablename__ = 'videos'
    __table_args__ = (
        Index('idx_video_user_id', 'user_id'),
        Index('idx_video_status', 'processing_status'),
        Index('idx_video_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # File information
    original_filename = db.Column(db.String(500), nullable=False)
    file_key = db.Column(db.String(1000), nullable=False)  # S3 key
    file_size = db.Column(db.Integer, nullable=False)  # Original file size in bytes
    mime_type = db.Column(db.String(100), default='video/mp4')

    # Metadata
    title = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    width = db.Column(db.Integer, nullable=True)  # Original width in pixels
    height = db.Column(db.Integer, nullable=True)  # Original height in pixels
    fps = db.Column(db.Float, nullable=True)  # Frames per second
    codec = db.Column(db.String(50), nullable=True)  # Video codec (h264, vp8, etc.)

    # Processing
    processing_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_error = db.Column(db.Text, nullable=True)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)

    # Visibility
    is_public = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('videos', lazy='select'), foreign_keys=[user_id])
    variants = db.relationship('VideoVariant', backref='video', lazy='select', cascade='all, delete-orphan')
    thumbnails = db.relationship('VideoThumbnail', backref='video', lazy='select', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'codec': self.codec,
            'processing_status': self.processing_status,
            'processing_error': self.processing_error,
            'is_public': self.is_public,
            'variants': [v.to_dict() for v in self.variants] if self.variants else [],
            'thumbnails': [t.to_dict() for t in self.thumbnails] if self.thumbnails else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class VideoVariant(db.Model):
    """Video variants at different quality levels"""
    __tablename__ = 'video_variants'
    __table_args__ = (
        Index('idx_variant_video_id', 'video_id'),
        Index('idx_variant_quality', 'quality'),
    )

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)

    # Quality and format
    quality = db.Column(db.String(50), nullable=False)  # '360p', '720p', '1080p', 'source'
    format = db.Column(db.String(20), nullable=False)  # 'mp4', 'webm', 'webp'
    bitrate = db.Column(db.String(50), nullable=True)  # e.g., '500k', '2500k'

    # Storage
    file_key = db.Column(db.String(1000), nullable=False)  # S3 key
    file_size = db.Column(db.Integer, nullable=False)  # File size in bytes

    # Metadata
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=True)

    # Status
    processing_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_error = db.Column(db.Text, nullable=True)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'quality': self.quality,
            'format': self.format,
            'bitrate': self.bitrate,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class VideoThumbnail(db.Model):
    """Video thumbnails and preview frames"""
    __tablename__ = 'video_thumbnails'
    __table_args__ = (
        Index('idx_thumbnail_video_id', 'video_id'),
        Index('idx_thumbnail_type', 'thumbnail_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)

    # Thumbnail type
    thumbnail_type = db.Column(db.String(50), nullable=False)  # 'main', 'preview', 'frame_N'

    # Storage
    file_key = db.Column(db.String(1000), nullable=False)  # S3 key
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), default='image/jpeg')

    # Metadata
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Float, nullable=True)  # Timestamp in video where thumbnail was taken

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'thumbnail_type': self.thumbnail_type,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'timestamp': self.timestamp,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class VideoProcessingJob(db.Model):
    """Queue of video processing jobs"""
    __tablename__ = 'video_processing_jobs'
    __table_args__ = (
        Index('idx_job_video_id', 'video_id'),
        Index('idx_job_status', 'status'),
        Index('idx_job_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)

    # Job type
    job_type = db.Column(db.String(100), nullable=False)  # 'transcoding_360p', 'transcoding_720p', 'thumbnail', etc.

    # Status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    # Timing
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Parameters (JSON)
    parameters = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'job_type': self.job_type,
            'status': self.status,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
