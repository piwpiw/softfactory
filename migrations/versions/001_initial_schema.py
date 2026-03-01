"""initial schema — all tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-26 00:00:00.000000

Manually authored migration covering every SQLAlchemy model defined in
backend/models.py (v2.0).  Table list:

    Platform    : users, products, subscriptions, payments
    CooCook     : chefs, bookings, booking_payments, booking_reviews,
                  shopping_lists
    SNS Auto    : sns_accounts, sns_posts, sns_campaigns, sns_templates,
                  sns_analytics, sns_inbox_messages, sns_oauth_states,
                  sns_settings, sns_link_in_bios, sns_automates,
                  sns_competitors
    Review      : review_listings, review_bookmarks, review_accounts,
                  review_applications, review_auto_rules
    Campaigns   : campaigns, campaign_applications
    AI Auto     : ai_employees, scenarios
    Webapp      : bootcamp_enrollments, webapps
    Experience  : experience_listings, crawler_logs
    Security    : login_attempts, error_logs, error_patterns
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # PLATFORM
    # ------------------------------------------------------------------

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('role', sa.String(20), nullable=True, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        # Security fields
        sa.Column('is_locked', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        # OAuth fields
        sa.Column('oauth_provider', sa.String(20), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('oauth_id'),
    )
    op.create_index('idx_email', 'users', ['email'])
    op.create_index('idx_oauth_id', 'users', ['oauth_id'])
    op.create_index('idx_created_at', 'users', ['created_at'])
    op.create_index('idx_is_active', 'users', ['is_active'])

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('monthly_price', sa.Float(), nullable=False),
        sa.Column('annual_price', sa.Float(), nullable=True),
        sa.Column('stripe_price_id_monthly', sa.String(255), nullable=True),
        sa.Column('stripe_price_id_annual', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('plan_type', sa.String(20), nullable=True, server_default='monthly'),
        sa.Column('status', sa.String(20), nullable=True, server_default='active'),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('stripe_payment_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True, server_default='USD'),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # COOCOOK
    # ------------------------------------------------------------------

    op.create_table(
        'chefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('cuisine_type', sa.String(50), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('price_per_session', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True, server_default='5.0'),
        sa.Column('rating_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chef_id', sa.Integer(), nullable=False),
        sa.Column('booking_date', sa.Date(), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chef_id'], ['chefs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'booking_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True, server_default='KRW'),
        sa.Column('status', sa.String(20), nullable=True, server_default='completed'),
        sa.Column('transaction_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'booking_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chef_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chef_id'], ['chefs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'shopping_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_shopping_list_user', 'shopping_lists', ['user_id'])
    op.create_index('idx_shopping_list_created', 'shopping_lists', ['created_at'])

    # ------------------------------------------------------------------
    # SNS AUTO
    # ------------------------------------------------------------------

    op.create_table(
        'sns_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_platforms', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='active'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sns_campaigns_status', 'sns_campaigns', ['status'])

    op.create_table(
        'sns_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('platform_user_id', sa.String(255), nullable=True),
        sa.Column('profile_picture_url', sa.String(500), nullable=True),
        sa.Column('account_type', sa.String(50), nullable=True, server_default='personal'),
        sa.Column('followers_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('following_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('permissions_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sns_account_user_platform', 'sns_accounts', ['user_id', 'platform'])
    op.create_index('idx_sns_account_platform_active', 'sns_accounts', ['platform', 'is_active'])
    op.create_index('idx_sns_account_user_active', 'sns_accounts', ['user_id', 'is_active'])
    op.create_index('idx_platform_user_id', 'sns_accounts', ['platform', 'platform_user_id'])

    op.create_table(
        'sns_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='draft'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('template_type', sa.String(50), nullable=True),
        sa.Column('media_urls', sa.JSON(), nullable=True),
        sa.Column('hashtags', sa.JSON(), nullable=True),
        sa.Column('link_url', sa.String(500), nullable=True),
        sa.Column('external_post_id', sa.String(255), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comments_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('views_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reach', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['sns_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['campaign_id'], ['sns_campaigns.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sns_post_user_created', 'sns_posts', ['user_id', 'created_at'])
    op.create_index('idx_sns_post_platform_status', 'sns_posts', ['platform', 'status'])
    op.create_index('idx_sns_post_scheduled_at', 'sns_posts', ['scheduled_at'])
    op.create_index('idx_sns_post_user_platform', 'sns_posts', ['user_id', 'platform'])
    op.create_index('idx_sns_post_campaign_id', 'sns_posts', ['campaign_id'])
    op.create_index('idx_sns_post_account_created', 'sns_posts', ['account_id', 'created_at'])
    op.create_index('idx_sns_post_user_published', 'sns_posts', ['user_id', 'status'])

    op.create_table(
        'sns_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('content_template', sa.Text(), nullable=False),
        sa.Column('hashtag_template', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'sns_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('followers', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_engagement', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_reach', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_impressions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['sns_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sns_analytics_account_date', 'sns_analytics', ['account_id', 'date'])
    op.create_index('idx_sns_analytics_user_date', 'sns_analytics', ['user_id', 'date'])
    op.create_index('idx_sns_analytics_date', 'sns_analytics', ['date'])

    op.create_table(
        'sns_inbox_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('sender_name', sa.String(200), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='unread'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['sns_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sns_inbox_user_status', 'sns_inbox_messages', ['user_id', 'status'])
    op.create_index('idx_sns_inbox_user_unread_created', 'sns_inbox_messages', ['user_id', 'status', 'created_at'])
    op.create_index('idx_sns_inbox_account_created', 'sns_inbox_messages', ['account_id', 'created_at'])
    op.create_index('idx_sns_inbox_external_id', 'sns_inbox_messages', ['external_id'])

    op.create_table(
        'sns_oauth_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('state_token', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state_token'),
    )
    op.create_index('idx_state_token', 'sns_oauth_states', ['state_token'])
    op.create_index('idx_expires_at', 'sns_oauth_states', ['expires_at'])

    op.create_table(
        'sns_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('auto_optimal_time', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('engagement_notifications', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('auto_reply_enabled', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('banned_keywords', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    op.create_table(
        'sns_link_in_bios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('links', sa.JSON(), nullable=True),
        sa.Column('theme', sa.String(50), nullable=True, server_default='light'),
        sa.Column('click_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('idx_sns_link_in_bio_user', 'sns_link_in_bios', ['user_id'])
    op.create_index('idx_sns_link_in_bio_slug', 'sns_link_in_bios', ['slug'])

    op.create_table(
        'sns_automates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('topic', sa.String(500), nullable=True),
        sa.Column('purpose', sa.String(500), nullable=True),
        sa.Column('platforms', sa.JSON(), nullable=True),
        sa.Column('frequency', sa.String(50), nullable=True, server_default='daily'),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sns_automate_user_active', 'sns_automates', ['user_id', 'is_active'])
    op.create_index('idx_sns_automate_next_run', 'sns_automates', ['next_run'])
    op.create_index('idx_sns_automate_active', 'sns_automates', ['is_active'])

    op.create_table(
        'sns_competitors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('followers_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('engagement_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('avg_likes', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_comments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('posting_frequency', sa.String(50), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('last_analyzed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_competitor_user_platform', 'sns_competitors', ['user_id', 'platform'])
    op.create_index('idx_competitor_platform_username', 'sns_competitors', ['platform', 'username'])
    op.create_index('idx_competitor_last_analyzed', 'sns_competitors', ['last_analyzed'])

    # ------------------------------------------------------------------
    # REVIEW
    # ------------------------------------------------------------------

    op.create_table(
        'review_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_platform', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('brand', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('reward_type', sa.String(50), nullable=True),
        sa.Column('reward_value', sa.Integer(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('max_applicants', sa.Integer(), nullable=True),
        sa.Column('current_applicants', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('applied_accounts', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='active'),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
    )
    op.create_index('idx_source_platform_scraped', 'review_listings', ['source_platform', 'scraped_at'])
    op.create_index('idx_category_deadline', 'review_listings', ['category', 'deadline'])
    op.create_index('idx_reward_value', 'review_listings', ['reward_value'])
    op.create_index('idx_status_created', 'review_listings', ['status', 'scraped_at'])
    op.create_index('idx_external_id_platform', 'review_listings', ['external_id', 'source_platform'])
    op.create_index('idx_deadline', 'review_listings', ['deadline'])

    op.create_table(
        'review_bookmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['review_listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_user_listing', 'review_bookmarks', ['user_id', 'listing_id'])
    op.create_index('idx_listing_id', 'review_bookmarks', ['listing_id'])

    op.create_table(
        'review_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('credentials_enc', sa.String(1000), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('category_tags', sa.JSON(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('last_reviewed', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_review_account_user', 'review_accounts', ['user_id'])
    op.create_index('idx_review_account_user_platform', 'review_accounts', ['user_id', 'platform'])
    op.create_index('idx_review_account_user_active', 'review_accounts', ['user_id', 'is_active'])

    op.create_table(
        'review_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('result', sa.String(500), nullable=True),
        sa.Column('review_url', sa.String(500), nullable=True),
        sa.Column('review_posted_at', sa.DateTime(), nullable=True),
        sa.Column('review_content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['listing_id'], ['review_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['review_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_review_app_account_created', 'review_applications', ['account_id', 'applied_at'])
    op.create_index('idx_listing_account', 'review_applications', ['listing_id', 'account_id'])
    op.create_index('idx_user_status', 'review_applications', ['account_id', 'status'])
    op.create_index('idx_review_app_status_created', 'review_applications', ['status', 'applied_at'])

    op.create_table(
        'review_auto_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_categories', sa.JSON(), nullable=True),
        sa.Column('min_reward', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_reward', sa.Integer(), nullable=True),
        sa.Column('apply_deadline_days', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('max_applicants_ratio', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('preferred_accounts', sa.JSON(), nullable=True),
        sa.Column('reward_types', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_review_rule_user_active', 'review_auto_rules', ['user_id', 'is_active'])

    # ------------------------------------------------------------------
    # CAMPAIGNS
    # ------------------------------------------------------------------

    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('reward_type', sa.String(50), nullable=True),
        sa.Column('reward_value', sa.String(200), nullable=True),
        sa.Column('max_reviewers', sa.Integer(), nullable=True, server_default='10'),
        sa.Column('deadline', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_campaign_status', 'campaigns', ['status'])
    op.create_index('idx_campaign_creator', 'campaigns', ['creator_id'])
    op.create_index('idx_campaign_status_category', 'campaigns', ['status', 'category'])
    op.create_index('idx_campaign_deadline', 'campaigns', ['deadline'])

    op.create_table(
        'campaign_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sns_link', sa.String(500), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_campaign_app_campaign', 'campaign_applications', ['campaign_id'])
    op.create_index('idx_campaign_app_user', 'campaign_applications', ['user_id'])
    op.create_index('idx_campaign_app_campaign_user', 'campaign_applications', ['campaign_id', 'user_id'])
    op.create_index('idx_campaign_app_status', 'campaign_applications', ['status'])

    # ------------------------------------------------------------------
    # AI AUTOMATION
    # ------------------------------------------------------------------

    op.create_table(
        'ai_employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('scenario_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='draft'),
        sa.Column('monthly_savings_hours', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_savings', sa.Integer(), nullable=True),
        sa.Column('complexity', sa.String(20), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # WEBAPP BUILDER
    # ------------------------------------------------------------------

    op.create_table(
        'bootcamp_enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_type', sa.String(50), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='enrolled'),
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'webapps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='draft'),
        sa.Column('code_repo', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------------

    op.create_table(
        'experience_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reward', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'crawler_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site', sa.String(50), nullable=False),
        sa.Column('listing_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_crawl_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------------------

    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_login_attempts_email', 'login_attempts', ['email'])
    op.create_index('ix_login_attempts_timestamp', 'login_attempts', ['timestamp'])

    op.create_table(
        'error_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('error_type', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True, server_default='medium'),
        sa.Column('resolved', sa.Boolean(), nullable=True, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_error_logs_error_type', 'error_logs', ['error_type'])
    op.create_index('ix_error_logs_timestamp', 'error_logs', ['timestamp'])
    op.create_index('ix_error_logs_project_id', 'error_logs', ['project_id'])

    op.create_table(
        'error_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('error_type', sa.String(255), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=True, server_default='medium'),
        sa.Column('root_cause', sa.String(500), nullable=True),
        sa.Column('resolution', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('error_type'),
    )
    op.create_index('ix_error_patterns_error_type', 'error_patterns', ['error_type'])
    op.create_index('ix_error_patterns_first_seen', 'error_patterns', ['first_seen'])


def downgrade():
    # Drop tables in reverse dependency order (children before parents)

    # Security
    op.drop_table('error_patterns')
    op.drop_table('error_logs')
    op.drop_table('login_attempts')

    # Experience
    op.drop_table('crawler_logs')
    op.drop_table('experience_listings')

    # Webapp Builder
    op.drop_table('webapps')
    op.drop_table('bootcamp_enrollments')

    # AI Automation
    op.drop_table('scenarios')
    op.drop_table('ai_employees')

    # Campaigns
    op.drop_table('campaign_applications')
    op.drop_table('campaigns')

    # Review
    op.drop_table('review_auto_rules')
    op.drop_table('review_applications')
    op.drop_table('review_accounts')
    op.drop_table('review_bookmarks')
    op.drop_table('review_listings')

    # SNS Auto
    op.drop_table('sns_competitors')
    op.drop_table('sns_automates')
    op.drop_table('sns_link_in_bios')
    op.drop_table('sns_settings')
    op.drop_table('sns_oauth_states')
    op.drop_table('sns_inbox_messages')
    op.drop_table('sns_analytics')
    op.drop_table('sns_templates')
    op.drop_table('sns_posts')
    op.drop_table('sns_accounts')
    op.drop_table('sns_campaigns')

    # CooCook
    op.drop_table('shopping_lists')
    op.drop_table('booking_reviews')
    op.drop_table('booking_payments')
    op.drop_table('bookings')
    op.drop_table('chefs')

    # Platform
    op.drop_table('payments')
    op.drop_table('subscriptions')
    op.drop_table('products')
    op.drop_table('users')
