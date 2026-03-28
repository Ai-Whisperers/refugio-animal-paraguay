"""Create volunteer_profiles table.

RAP-640: Volunteer registration and profile model.

Revision ID: 071
Revises: 070
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "071"
down_revision = "070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "volunteer_profiles",
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
            unique=True,
        ),
        sa.Column("motivation", sa.Text, nullable=False),
        sa.Column("skills", sa.JSON, nullable=True),
        sa.Column("availability", sa.JSON, nullable=True),
        sa.Column("hours_per_week", sa.Integer, nullable=True),
        sa.Column("emergency_contact_name", sa.String(100), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(20), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column(
            "reviewed_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "total_hours_logged",
            sa.Numeric(8, 2),
            nullable=False,
            server_default="0",
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
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'inactive')",
            name="chk_volunteer_status_valid",
        ),
        sa.CheckConstraint(
            "length(motivation) >= 20",
            name="chk_volunteer_motivation_min_len",
        ),
        sa.CheckConstraint(
            "hours_per_week IS NULL OR (hours_per_week >= 1 AND hours_per_week <= 40)",
            name="chk_volunteer_hours_per_week_range",
        ),
    )
    op.create_index(
        "ix_volunteer_profiles_user_id",
        "volunteer_profiles",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_volunteer_profiles_status",
        "volunteer_profiles",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_volunteer_profiles_status", table_name="volunteer_profiles")
    op.drop_index("ix_volunteer_profiles_user_id", table_name="volunteer_profiles")
    op.drop_table("volunteer_profiles")
