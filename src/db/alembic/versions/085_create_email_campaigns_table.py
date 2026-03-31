"""Create email_campaigns table.

Revision ID: 085
Revises: 084
Create Date: 2026-03-29

Adds email campaign scheduling for EPIC-44 (Email Campaign System).
Campaigns link an email list to an email template and track the
lifecycle from draft through scheduled → sending → sent.
"""

import sqlalchemy as sa
from alembic import op

revision = "085"
down_revision = "084"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_campaigns",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "email_list_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("email_lists.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "email_template_id",
            sa.UUID(as_uuid=True),
            nullable=False,
            comment="References email_templates.id",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_by_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_email_campaigns_status", "email_campaigns", ["status"])
    op.create_index("ix_email_campaigns_email_list_id", "email_campaigns", ["email_list_id"])
    op.create_index(
        "ix_email_campaigns_email_template_id",
        "email_campaigns",
        ["email_template_id"],
    )
    op.create_index("ix_email_campaigns_created_by_id", "email_campaigns", ["created_by_id"])
    op.create_index("ix_email_campaigns_scheduled_at", "email_campaigns", ["scheduled_at"])


def downgrade() -> None:
    op.drop_table("email_campaigns")
