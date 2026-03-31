"""Create foster_check_ins table (RAP-192).

Revision ID: 077
Revises: 076
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "077"
down_revision = "076"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foster_check_ins",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "foster_placement_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("foster_placements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "check_in_type",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'scheduled'"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "scheduled_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        sa.Column(
            "interval_days",
            sa.Integer,
            nullable=False,
            server_default=sa.text("7"),
        ),
        sa.Column(
            "reminder_sent_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_foster_check_ins_foster_placement_id",
        "foster_check_ins",
        ["foster_placement_id"],
    )
    op.create_index(
        "ix_foster_check_ins_status",
        "foster_check_ins",
        ["status"],
    )
    op.create_index(
        "ix_foster_check_ins_scheduled_at",
        "foster_check_ins",
        ["scheduled_at"],
    )

    op.create_check_constraint(
        "chk_foster_check_in_status_valid",
        "foster_check_ins",
        "status IN ('pending', 'completed', 'missed', 'cancelled')",
    )
    op.create_check_constraint(
        "chk_foster_check_in_type_valid",
        "foster_check_ins",
        "check_in_type IN ('scheduled', 'unscheduled')",
    )
    op.create_check_constraint(
        "chk_foster_check_in_interval_days_range",
        "foster_check_ins",
        "interval_days >= 1 AND interval_days <= 90",
    )


def downgrade() -> None:
    op.drop_table("foster_check_ins")
