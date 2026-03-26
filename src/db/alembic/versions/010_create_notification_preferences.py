"""Create notification_preferences table.

Revision ID: 010
Revises: 009
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "notification_type",
            "channel",
            name="uq_notification_pref_user_type_channel",
        ),
        sa.CheckConstraint(
            "channel IN ('in_app', 'email')",
            name="chk_notification_pref_channel",
        ),
        sa.CheckConstraint(
            "notification_type IN ("
            "'adoption_request_created', 'adoption_status_changed', "
            "'donation_received', 'donation_refunded', "
            "'animal_intake_completed', 'animal_status_changed', "
            "'system_alert', 'gdpr_request')",
            name="chk_notification_pref_type",
        ),
    )

    op.create_index(
        "ix_notification_pref_user",
        "notification_preferences",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_pref_user", table_name="notification_preferences")
    op.drop_table("notification_preferences")
