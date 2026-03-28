"""Create voucher_notifications table for donor transparency.

Revision ID: 039
Revises: 038
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "voucher_notifications",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column(
            "voucher_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_vouchers.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("channel", sa.String(20), nullable=False, server_default=sa.text("'email'")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("body_preview", sa.String(500), nullable=True),
        sa.Column("context_data", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('voucher_claimed', 'voucher_redeemed', 'monthly_summary')",
            name="chk_voucher_notifications_event_type",
        ),
        sa.CheckConstraint(
            "channel IN ('email', 'whatsapp')",
            name="chk_voucher_notifications_channel",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'skipped')",
            name="chk_voucher_notifications_status",
        ),
        sa.CheckConstraint(
            "retry_count >= 0",
            name="chk_voucher_notifications_retry_count",
        ),
    )
    op.create_index(
        "ix_voucher_notifications_user_status",
        "voucher_notifications",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_voucher_notifications_created_at",
        "voucher_notifications",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_voucher_notifications_created_at")
    op.drop_index("ix_voucher_notifications_user_status")
    op.drop_table("voucher_notifications")
