"""sns automate delivery contract

Revision ID: 003_sns_automate_delivery_contract
Revises: 002_growth_automation_mvp
Create Date: 2026-03-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_sns_automate_delivery_contract"
down_revision = "002_growth_automation_mvp"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sns_automates", sa.Column("engine", sa.String(length=50), nullable=True))
    op.add_column("sns_automates", sa.Column("webhook_url", sa.String(length=1000), nullable=True))
    op.add_column("sns_automates", sa.Column("delivery_mode", sa.String(length=50), nullable=True))
    op.add_column("sns_automates", sa.Column("payload_version", sa.String(length=50), nullable=True))
    op.add_column("sns_automates", sa.Column("requested_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE sns_automates SET engine = 'direct' WHERE engine IS NULL")
    op.execute("UPDATE sns_automates SET delivery_mode = 'direct' WHERE delivery_mode IS NULL")
    op.execute("UPDATE sns_automates SET payload_version = '2026-03-10' WHERE payload_version IS NULL")
    op.execute("UPDATE sns_automates SET requested_at = created_at WHERE requested_at IS NULL")


def downgrade():
    op.drop_column("sns_automates", "requested_at")
    op.drop_column("sns_automates", "payload_version")
    op.drop_column("sns_automates", "delivery_mode")
    op.drop_column("sns_automates", "webhook_url")
    op.drop_column("sns_automates", "engine")
