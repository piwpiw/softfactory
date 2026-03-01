"""Alembic environment configuration — SoftFactory
Supports both SQLite (development) and PostgreSQL (production).
All models from backend.models are imported here so Alembic can detect
schema changes automatically via `flask db migrate`.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Add project root to sys.path so `backend` package is importable
# ---------------------------------------------------------------------------
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# Import ALL models so their metadata is visible to Alembic's autogenerate.
# Adding a new model to backend/models.py makes it auto-detected on
# `flask db migrate` without any changes to this file.
# ---------------------------------------------------------------------------
from backend.models import (  # noqa: E402, F401
    db,
    User,
    Product,
    Subscription,
    Payment,
    Chef,
    Booking,
    BookingPayment,
    BookingReview,
    ShoppingList,
    SNSAccount,
    SNSPost,
    SNSCampaign,
    SNSTemplate,
    SNSAnalytics,
    SNSInboxMessage,
    SNSOAuthState,
    SNSSettings,
    SNSLinkInBio,
    SNSAutomate,
    SNSCompetitor,
    ReviewListing,
    ReviewBookmark,
    ReviewAccount,
    ReviewApplication,
    ReviewAutoRule,
    Campaign,
    CampaignApplication,
    AIEmployee,
    Scenario,
    BootcampEnrollment,
    WebApp,
    ExperienceListing,
    CrawlerLog,
    LoginAttempt,
    ErrorLog,
    ErrorPattern,
)

# ---------------------------------------------------------------------------
# Alembic Config object (provides access to .ini file values)
# ---------------------------------------------------------------------------
config = context.config

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLAlchemy metadata from our models for autogenerate support
target_metadata = db.metadata


# ---------------------------------------------------------------------------
# Helper: resolve database URL
# Environment variable DATABASE_URL takes precedence over alembic.ini value.
# ---------------------------------------------------------------------------
def get_url() -> str:
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")
    # Normalize Heroku/Railway legacy postgres:// → postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


# ---------------------------------------------------------------------------
# Offline mode — generate SQL script without a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode we configure the context with just a URL (no Engine),
    which is useful for generating SQL scripts for review / DBA approval.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare server defaults so Alembic detects column default changes
        compare_server_default=True,
        # Include schema-level objects (sequences, etc.)
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — run migrations against a live database connection
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an active connection."""
    url = get_url()

    # Override the sqlalchemy.url in the alembic config so engine_from_config
    # picks up the runtime URL (env var or ini value).
    config.set_main_option("sqlalchemy.url", url)

    # Choose the right connection pool:
    # - SQLite: NullPool avoids "cannot reuse across threads" issues in tests
    # - PostgreSQL: default QueuePool for connection reuse / performance
    if url.startswith("sqlite"):
        poolclass = pool.NullPool
        connect_args = {"check_same_thread": False}
    else:
        poolclass = pool.NullPool  # NullPool is safe for migration scripts
        connect_args = {}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=poolclass,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_server_default=True,
            include_schemas=True,
            # Render item types for better diff output
            render_as_batch=url.startswith("sqlite"),  # Required for SQLite ALTER TABLE
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
