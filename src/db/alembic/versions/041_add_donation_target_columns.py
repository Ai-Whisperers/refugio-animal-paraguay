"""Add target_type and target_id columns to donations table.

Revision ID: 041
Revises: 036
Create Date: 2026-03-27

Adds flexible donation targeting: donors can direct support to a specific
animal, rescuer, clinic, campaign, or need. Existing donations default
to 'general' target type.
"""

import sqlalchemy as sa
from alembic import op

revision = "041"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donations",
        sa.Column(
            "target_type",
            sa.String(20),
            nullable=False,
            server_default="general",
        ),
    )
    op.add_column(
        "donations",
        sa.Column(
            "target_id",
            sa.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    # Composite index for efficient filtering by target
    op.create_index(
        "ix_donations_target_type_target_id",
        "donations",
        ["target_type", "target_id"],
    )
    # Check constraint: target_id must be NULL when target_type is 'general'
    # and NOT NULL when target_type is not 'general'
    op.execute("""
        ALTER TABLE donations ADD CONSTRAINT chk_donations_target_consistency
        CHECK (
            (target_type = 'general' AND target_id IS NULL)
            OR (target_type != 'general' AND target_id IS NOT NULL)
        )
        """)
    # Check constraint: target_type must be one of the allowed values
    op.execute("""
        ALTER TABLE donations ADD CONSTRAINT chk_donations_target_type
        CHECK (target_type IN ('general', 'animal', 'rescuer', 'clinic', 'campaign', 'need'))
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_target_type")
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_target_consistency")
    op.drop_index("ix_donations_target_type_target_id", table_name="donations")
    op.drop_column("donations", "target_id")
    op.drop_column("donations", "target_type")
