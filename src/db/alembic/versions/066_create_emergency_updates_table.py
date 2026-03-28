"""Create emergency_updates table.

Revision ID: 066
Revises: 065
Create Date: 2026-03-28

Stores progress updates on emergency cases -- text, photos, and optional
resolution outcome. Allows rescuers to keep donors informed about
the impact of their contributions.
"""

import sqlalchemy as sa
from alembic import op

revision = "066"
down_revision = "065"


def upgrade() -> None:
    op.create_table(
        "emergency_updates",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "emergency_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("emergency_cases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("text", sa.String(1000), nullable=False),
        sa.Column(
            "photos",
            sa.JSON,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "posted_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "is_resolution",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("outcome", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "length(text) >= 1",
            name="chk_emergency_update_text_not_empty",
        ),
        sa.CheckConstraint(
            "length(text) <= 1000",
            name="chk_emergency_update_text_max_len",
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('recovered', 'adopted', 'in_care', 'deceased', 'other')",
            name="chk_emergency_update_outcome_valid",
        ),
    )
    op.create_index(
        "ix_emergency_updates_created_at",
        "emergency_updates",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_emergency_updates_created_at", table_name="emergency_updates")
    op.drop_table("emergency_updates")
