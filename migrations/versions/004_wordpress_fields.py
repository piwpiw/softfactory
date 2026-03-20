"""Add WordPress/blog fields to sns_accounts

Revision ID: 004_wordpress_fields
Revises: 003_sns_automate_delivery_contract
Create Date: 2026-03-16

Adds:
  sns_accounts.site_url     — WordPress site URL (e.g. https://myblog.com)
  sns_accounts.wp_username  — WordPress username for Application Password auth
"""
from alembic import op
import sqlalchemy as sa

revision = '004_wordpress_fields'
down_revision = '003_sns_automate_delivery_contract'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sns_accounts') as batch_op:
        batch_op.add_column(sa.Column('site_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('wp_username', sa.String(120), nullable=True))


def downgrade():
    with op.batch_alter_table('sns_accounts') as batch_op:
        batch_op.drop_column('wp_username')
        batch_op.drop_column('site_url')
