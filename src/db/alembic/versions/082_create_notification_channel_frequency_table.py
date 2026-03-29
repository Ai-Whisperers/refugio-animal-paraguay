"""Create notification_channel_frequency table.

Revision ID: 082
Revises: 081
Create Date: 2026-03-29

Adds per-user, per-channel frequency control for notification delivery.
Frequency values: immediate (default), daily_digest, weekly.
"""

from alembic import op
import sqlalchemy as sa

revision = "082"
down_revision = "081"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_channel_frequency",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "frequency",
            sa.String(20),
            nullable=False,
            server_default="immediate",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id",
            "channel",
            name="uq_notification_channel_frequency_user_channel",
        ),
        sa.CheckConstraint(
            "channel IN ('in_app', 'email')",
            name="chk_notification_channel_frequency_channel",
        ),
        sa.CheckConstraint(
            "frequency IN ('immediate', 'daily_digest', 'weekly')",
            name="chk_notification_channel_frequency_value",
        ),
    )
    op.create_index(
        "ix_notification_channel_frequency_user",
        "notification_channel_frequency",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_channel_frequency_user",
        table_name="notification_channel_frequency",
    )
    op.drop_table("notification_channel_frequency")
