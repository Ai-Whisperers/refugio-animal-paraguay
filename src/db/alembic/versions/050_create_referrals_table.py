"""Create referrals table for referral tracking.

Revision ID: 050
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "050"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referrals",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "referrer_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "referred_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("conversion_type", sa.String(30), nullable=True, index=True),
        sa.Column("conversion_entity_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("landing_path", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("converted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        sa.CheckConstraint(
            "conversion_type IN ('donation', 'adoption_application', 'registration') "
            "OR conversion_type IS NULL",
            name="chk_referral_conversion_type_valid",
        ),
        sa.Index("ix_referrals_referrer_created", "referrer_user_id", "created_at"),
    )


def downgrade() -> None:
    op.drop_table("referrals")
