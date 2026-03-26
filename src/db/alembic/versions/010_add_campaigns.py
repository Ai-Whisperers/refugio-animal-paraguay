"""Add campaigns table and campaign_id to donations.

Revision ID: 010
Revises: 009
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal_amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("category", sa.String(20), server_default="other", nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "category IN ('medical', 'food', 'operations', 'rescue', 'facility', 'other')",
            name="chk_campaigns_category",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'completed', 'archived')",
            name="chk_campaigns_status",
        ),
        sa.CheckConstraint("goal_amount_cents > 0", name="chk_campaigns_goal_positive"),
    )

    # Add campaign_id to donations
    op.add_column(
        "donations",
        sa.Column("campaign_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_donations_campaign_id",
        "donations",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_donations_campaign_id", "donations", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_donations_campaign_id", table_name="donations")
    op.drop_constraint("fk_donations_campaign_id", "donations", type_="foreignkey")
    op.drop_column("donations", "campaign_id")
    op.drop_table("campaigns")
