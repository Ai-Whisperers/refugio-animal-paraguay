"""Create volunteer_hours_log table (RAP-195).

Revision ID: 079
Revises: 078
Create Date: 2026-03-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "079"
down_revision: str | None = "078"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "volunteer_hours_log",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("volunteer_id", sa.Uuid(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("duration_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("shift_id", sa.Uuid(), nullable=True),
        sa.Column("approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column(
            "approved_at", sa.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["volunteer_id"],
            ["volunteer_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["shift_id"],
            ["shifts.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_volunteer_hours_log_volunteer_id", "volunteer_hours_log", ["volunteer_id"])
    op.create_index("ix_volunteer_hours_log_activity_date", "volunteer_hours_log", ["activity_date"])
    op.create_index("ix_volunteer_hours_log_category", "volunteer_hours_log", ["category"])
    op.create_index("ix_volunteer_hours_log_shift_id", "volunteer_hours_log", ["shift_id"])


def downgrade() -> None:
    op.drop_index("ix_volunteer_hours_log_shift_id", table_name="volunteer_hours_log")
    op.drop_index("ix_volunteer_hours_log_category", table_name="volunteer_hours_log")
    op.drop_index("ix_volunteer_hours_log_activity_date", table_name="volunteer_hours_log")
    op.drop_index("ix_volunteer_hours_log_volunteer_id", table_name="volunteer_hours_log")
    op.drop_table("volunteer_hours_log")
