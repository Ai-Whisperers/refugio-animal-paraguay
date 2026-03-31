"""Create foster_profiles table.

RAP-190: Foster family registration and approval model.

Revision ID: 075
Revises: 074
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "075"
down_revision = "074"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foster_profiles",
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
        sa.Column("experience_description", sa.Text, nullable=True),
        sa.Column(
            "home_type",
            sa.String(30),
            nullable=False,
            server_default="apartment",
        ),
        sa.Column(
            "has_outdoor_space",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_other_pets",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("other_pets_description", sa.String(500), nullable=True),
        sa.Column(
            "max_animals",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column("preferred_animal_types", sa.JSON, nullable=True),
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
            name="chk_foster_status_valid",
        ),
        sa.CheckConstraint(
            "length(motivation) >= 20",
            name="chk_foster_motivation_min_len",
        ),
        sa.CheckConstraint(
            "max_animals >= 1 AND max_animals <= 20",
            name="chk_foster_max_animals_range",
        ),
        sa.CheckConstraint(
            "home_type IN ('house_with_yard', 'house_without_yard', 'apartment', 'farm', 'other')",
            name="chk_foster_home_type_valid",
        ),
    )
    op.create_index(
        "ix_foster_profiles_user_id",
        "foster_profiles",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_foster_profiles_status",
        "foster_profiles",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_foster_profiles_status", table_name="foster_profiles")
    op.drop_index("ix_foster_profiles_user_id", table_name="foster_profiles")
    op.drop_table("foster_profiles")
