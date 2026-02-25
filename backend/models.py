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
# ============ SNS AUTO (v2.0) ============

class SNSAccount(db.Model):
    """SNS Account with expanded OAuth & analytics fields"""
    __tablename__ = 'sns_accounts'
    __table_args__ = (
        # User-platform lookup
        Index('idx_user_platform', 'user_id', 'platform'),
        # Platform status queries (active accounts per platform)
        Index('idx_platform_status', 'platform', 'is_active'),
        # User active accounts
        Index('idx_user_active', 'user_id', 'is_active'),
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
        Index('idx_user_created', 'user_id', 'created_at'),
        # Platform status queries (filter by status & platform)
        Index('idx_platform_status', 'platform', 'status'),
        # Scheduled posts (APScheduler job queue)
        Index('idx_scheduled_at', 'scheduled_at'),
        # User-platform posts
        Index('idx_user_platform', 'user_id', 'platform'),
        # Campaign posts
        Index('idx_campaign_id', 'campaign_id'),
        # Account posts (N+1 prevention)
        Index('idx_account_created', 'account_id', 'created_at'),
        # Published posts (analytics queries)
        Index('idx_user_published', 'user_id', 'status'),
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
        Index('idx_account_date', 'account_id', 'date'),
        # User analytics timeline
        Index('idx_user_date', 'user_id', 'date'),
        # Daily update queries
        Index('idx_date', 'date'),
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
        Index('idx_user_status', 'user_id', 'status'),
        # Unread messages timeline
        Index('idx_user_unread_created', 'user_id', 'status', 'created_at'),
        # Account messages
        Index('idx_account_created', 'account_id', 'created_at'),
        # External ID lookup (platform message sync)
        Index('idx_external_id', 'external_id'),
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'auto_optimal_time': self.auto_optimal_time,
            'engagement_notifications': self.engagement_notifications,
            'auto_reply_enabled': self.auto_reply_enabled,
            'banned_keywords': self.banned_keywords,
        }


class SNSLinkInBio(db.Model):
    """SNS Link In Bio — Single landing page with multiple links"""
    __tablename__ = 'sns_link_in_bios'

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

    applications = db.relationship('ReviewApplication', backref='listing', lazy=True, cascade='all, delete-orphan')

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

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # 'naver', 'instagram', 'blog', 'youtube', 'tiktok'
    account_name = db.Column(db.String(255), nullable=False)
    credentials_enc = db.Column(db.String(1000))  # Encrypted credentials (base64)
    follower_count = db.Column(db.Integer, default=0)
    category_tags = db.Column(db.JSON, default=[])  # ['패션' (fashion), '뷰티' (beauty), ...]
    success_rate = db.Column(db.Float, default=0.0)  # 0.0-1.0 (percentage of successful applications)
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
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ReviewApplication(db.Model):
    """Review Application — User applying for a review listing"""
    __tablename__ = 'review_applications'
    __table_args__ = (
        # User application history
        Index('idx_account_created', 'account_id', 'applied_at'),
        # Listing applications (check if user already applied)
        Index('idx_listing_account', 'listing_id', 'account_id'),
        # User progress (active applications)
        Index('idx_user_status', 'account_id', 'status'),
        # Status timeline
        Index('idx_status_created', 'status', 'applied_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('review_listings.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('review_accounts.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'selected', 'rejected', 'completed'
    result = db.Column(db.String(500))  # Summary of application result
    review_url = db.Column(db.String(500))  # URL to posted review
    review_posted_at = db.Column(db.DateTime)

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
        }


class ReviewAutoRule(db.Model):
    """Review Automation Rule — Auto-apply to matching review listings"""
    __tablename__ = 'review_auto_rules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    categories = db.Column(db.JSON, default=[])  # ['패션', '뷰티', ...]
    min_reward = db.Column(db.Integer, default=0)  # Minimum reward value in KRW
    max_applicants_ratio = db.Column(db.Float, default=0.5)  # Max applicant ratio threshold (0.0-1.0)
    preferred_accounts = db.Column(db.JSON, default=[])  # [account_ids] to prefer for applications
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'categories': self.categories,
            'min_reward': self.min_reward,
            'max_applicants_ratio': self.max_applicants_ratio,
            'preferred_accounts': self.preferred_accounts,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ============ REVIEW CAMPAIGNS ============

class Campaign(db.Model):
    __tablename__ = 'campaigns'

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

    applications = db.relationship('CampaignApplication', backref='campaign', lazy=True, cascade='all, delete-orphan')


class CampaignApplication(db.Model):
    __tablename__ = 'campaign_applications'

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
