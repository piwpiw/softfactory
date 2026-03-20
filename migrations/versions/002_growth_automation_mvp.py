"""growth automation mvp schema

Revision ID: 002_growth_automation_mvp
Revises: 001_initial_schema
Create Date: 2026-03-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_growth_automation_mvp"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "marketing_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_uid", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("lifecycle_stage", sa.String(length=30), nullable=False, server_default="lead"),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="ko-KR"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Seoul"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_uid"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("idx_marketing_contact_status", "marketing_contacts", ["status"])
    op.create_index("idx_marketing_contact_lifecycle", "marketing_contacts", ["lifecycle_stage"])
    op.create_index("idx_marketing_contact_created", "marketing_contacts", ["created_at"])

    op.create_table(
        "marketing_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("opt_in", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("policy_version", sa.String(length=50), nullable=False, server_default="v1"),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["marketing_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_marketing_consent_contact_channel", "marketing_consents", ["contact_id", "channel"])

    op.create_table(
        "marketing_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("event_name", sa.String(length=120), nullable=False),
        sa.Column("event_ts", sa.DateTime(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("anonymous_id", sa.String(length=120), nullable=True),
        sa.Column("context_json", sa.JSON(), nullable=True),
        sa.Column("props_json", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("processing_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("processing_updated_at", sa.DateTime(), nullable=False),
        sa.Column("workflow_run_id", sa.String(length=120), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["marketing_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("idx_marketing_event_name_ts", "marketing_events", ["event_name", "event_ts"])
    op.create_index("idx_marketing_event_status", "marketing_events", ["processing_status"])
    op.create_index("idx_marketing_event_contact_ts", "marketing_events", ["contact_id", "event_ts"])
    op.create_index("idx_marketing_event_anonymous", "marketing_events", ["anonymous_id"])

    op.create_table(
        "marketing_journey_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=60), nullable=False),
        sa.Column("entered_at", sa.DateTime(), nullable=False),
        sa.Column("last_action_at", sa.DateTime(), nullable=True),
        sa.Column("cooldown_until", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["contact_id"], ["marketing_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_id", "journey_id", name="uq_marketing_journey_contact_journey"),
    )
    op.create_index("idx_marketing_journey_state", "marketing_journey_states", ["journey_id", "state"])
    op.create_index("idx_marketing_journey_contact", "marketing_journey_states", ["contact_id"])

    op.create_table(
        "marketing_message_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_uid", sa.String(length=64), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("template_id", sa.String(length=120), nullable=True),
        sa.Column("campaign_id", sa.String(length=120), nullable=True),
        sa.Column("variant_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provider_msg_id", sa.String(length=160), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["marketing_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_uid"),
    )
    op.create_index("idx_marketing_message_status", "marketing_message_logs", ["status"])
    op.create_index("idx_marketing_message_campaign", "marketing_message_logs", ["campaign_id"])
    op.create_index("idx_marketing_message_contact_sent", "marketing_message_logs", ["contact_id", "sent_at"])

    op.create_table(
        "marketing_dlq",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_name", sa.String(length=120), nullable=False),
        sa.Column("step_name", sa.String(length=120), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_reason", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_marketing_dlq_status", "marketing_dlq", ["status"])
    op.create_index("idx_marketing_dlq_event_id", "marketing_dlq", ["event_id"])
    op.create_index("idx_marketing_dlq_workflow_created", "marketing_dlq", ["workflow_name", "created_at"])


def downgrade():
    op.drop_index("idx_marketing_dlq_workflow_created", table_name="marketing_dlq")
    op.drop_index("idx_marketing_dlq_event_id", table_name="marketing_dlq")
    op.drop_index("idx_marketing_dlq_status", table_name="marketing_dlq")
    op.drop_table("marketing_dlq")

    op.drop_index("idx_marketing_message_contact_sent", table_name="marketing_message_logs")
    op.drop_index("idx_marketing_message_campaign", table_name="marketing_message_logs")
    op.drop_index("idx_marketing_message_status", table_name="marketing_message_logs")
    op.drop_table("marketing_message_logs")

    op.drop_index("idx_marketing_journey_contact", table_name="marketing_journey_states")
    op.drop_index("idx_marketing_journey_state", table_name="marketing_journey_states")
    op.drop_table("marketing_journey_states")

    op.drop_index("idx_marketing_event_anonymous", table_name="marketing_events")
    op.drop_index("idx_marketing_event_contact_ts", table_name="marketing_events")
    op.drop_index("idx_marketing_event_status", table_name="marketing_events")
    op.drop_index("idx_marketing_event_name_ts", table_name="marketing_events")
    op.drop_table("marketing_events")

    op.drop_index("idx_marketing_consent_contact_channel", table_name="marketing_consents")
    op.drop_table("marketing_consents")

    op.drop_index("idx_marketing_contact_created", table_name="marketing_contacts")
    op.drop_index("idx_marketing_contact_lifecycle", table_name="marketing_contacts")
    op.drop_index("idx_marketing_contact_status", table_name="marketing_contacts")
    op.drop_table("marketing_contacts")
