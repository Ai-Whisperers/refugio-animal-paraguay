"""Add sponsorships table for animal sponsorship tiers.

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
    op.create_table(
        "sponsorships",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("donor_id", sa.UUID(), nullable=False),
        sa.Column("animal_id", sa.UUID(), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("interval", sa.String(20), server_default="month", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("paused_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["animal_id"], ["animals.id"], ondelete="CASCADE"),
        sa.CheckConstraint("tier IN ('bronze', 'silver', 'gold')", name="chk_sponsorships_tier"),
        sa.CheckConstraint("status IN ('active', 'paused', 'cancelled', 'past_due')", name="chk_sponsorships_status"),
        sa.CheckConstraint("interval IN ('month', 'year')", name="chk_sponsorships_interval"),
        sa.CheckConstraint("amount_cents > 0", name="chk_sponsorships_amount_positive"),
    )

    # Indexes
    op.create_index("ix_sponsorships_donor_id", "sponsorships", ["donor_id"])
    op.create_index("ix_sponsorships_animal_id", "sponsorships", ["animal_id"])
    op.create_index("ix_sponsorships_stripe_subscription_id", "sponsorships", ["stripe_subscription_id"], unique=True)

    # Partial unique index: one active/paused sponsorship per donor-animal pair
    op.execute(
        "CREATE UNIQUE INDEX uq_sponsorships_donor_animal_active "
        "ON sponsorships (donor_id, animal_id) "
        "WHERE status IN ('active', 'paused')"
    )


def downgrade() -> None:
    op.drop_index("uq_sponsorships_donor_animal_active", table_name="sponsorships")
    op.drop_index("ix_sponsorships_stripe_subscription_id", table_name="sponsorships")
    op.drop_index("ix_sponsorships_animal_id", table_name="sponsorships")
    op.drop_index("ix_sponsorships_donor_id", table_name="sponsorships")
    op.drop_table("sponsorships")
