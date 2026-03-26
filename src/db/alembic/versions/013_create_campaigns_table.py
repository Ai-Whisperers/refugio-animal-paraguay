"""Alembic migration: Create campaigns and campaign_donations tables.

- Creates campaigns table for fundraising campaign management
- Creates campaign_donations junction table linking donations to campaigns
- Adds indexes for efficient campaign progress queries
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "013"
down_revision = "012c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create campaigns and campaign_donations tables."""

    # ------------------------------------------------------------------
    # TABLE: campaigns
    # Fundraising campaigns with target amounts and deadlines.
    # ------------------------------------------------------------------
    op.create_table(
        "campaigns",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("impact_story", sa.Text, nullable=True),
        sa.Column("target_amount_cents", sa.Integer, nullable=False),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="EUR",
        ),
        sa.Column(
            "fund_category",
            sa.String(20),
            nullable=False,
            server_default="general",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("deadline", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("min_donation_cents", sa.Integer, nullable=True),
        sa.Column("max_donation_cents", sa.Integer, nullable=True),
        sa.Column(
            "allow_overfunding",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_by_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # CHECK constraints for valid enum values
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'cancelled')",
            name="chk_campaigns_status",
        ),
        sa.CheckConstraint(
            "fund_category IN ('medical', 'food', 'operations', 'rescue', 'infrastructure', 'general')",
            name="chk_campaigns_fund_category",
        ),
        sa.CheckConstraint(
            "currency IN ('EUR', 'PYG', 'USD')",
            name="chk_campaigns_currency",
        ),
        sa.CheckConstraint(
            "target_amount_cents > 0",
            name="chk_campaigns_target_positive",
        ),
    )

    # Index for listing active campaigns efficiently
    op.create_index(
        "ix_campaigns_status_deadline",
        "campaigns",
        ["status", "deadline"],
    )

    # ------------------------------------------------------------------
    # TABLE: campaign_donations
    # Links donations to campaigns for progress tracking.
    # ------------------------------------------------------------------
    op.create_table(
        "campaign_donations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "campaign_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "donation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Indexes for efficient campaign progress queries
    op.create_index(
        "ix_campaign_donations_campaign_id",
        "campaign_donations",
        ["campaign_id"],
    )
    op.create_index(
        "ix_campaign_donations_donation_id",
        "campaign_donations",
        ["donation_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop campaign_donations and campaigns tables."""
    op.drop_table("campaign_donations")
    op.drop_table("campaigns")
