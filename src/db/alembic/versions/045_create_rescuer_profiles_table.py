"""Create rescuer_profiles table for rescuer self-registration.

Revision ID: 045
Revises: 036
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "045"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rescuer_profiles",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True, index=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("location_city", sa.String(100), nullable=True),
        sa.Column("location_coords", sa.JSON, nullable=True),
        sa.Column("social_links", sa.JSON, nullable=True),
        sa.Column("phone_whatsapp", sa.String(20), nullable=True),
        sa.Column(
            "is_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("verification_method", sa.String(20), nullable=True),
        sa.Column(
            "animal_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "supporter_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "joined_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
        sa.CheckConstraint(
            "length(display_name) >= 2",
            name="chk_rescuer_display_name_min_len",
        ),
        sa.CheckConstraint(
            "length(display_name) <= 100",
            name="chk_rescuer_display_name_max_len",
        ),
        sa.CheckConstraint(
            "bio IS NULL OR length(bio) <= 1000",
            name="chk_rescuer_bio_max_len",
        ),
        sa.CheckConstraint(
            "animal_count >= 0",
            name="chk_rescuer_animal_count_positive",
        ),
        sa.CheckConstraint(
            "supporter_count >= 0",
            name="chk_rescuer_supporter_count_positive",
        ),
    )


def downgrade() -> None:
    op.drop_table("rescuer_profiles")
