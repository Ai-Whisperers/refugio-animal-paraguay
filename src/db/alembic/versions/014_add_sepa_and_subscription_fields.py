"""Alembic migration: Add SEPA Direct Debit and subscription fields to donations.

- Adds stripe_subscription_id, stripe_customer_id columns for subscription tracking
- Adds is_recurring flag and recurring_interval for recurring donations
- Updates payment_method CHECK constraint to include 'sepa_debit'
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add SEPA and subscription columns to donations table."""

    # Add new columns for subscription tracking
    op.add_column(
        "donations",
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column(
            "is_recurring",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "donations",
        sa.Column("recurring_interval", sa.String(20), nullable=True),
    )

    # Create indexes for subscription lookups
    op.create_index(
        "ix_donations_stripe_subscription_id",
        "donations",
        ["stripe_subscription_id"],
    )
    op.create_index(
        "ix_donations_stripe_customer_id",
        "donations",
        ["stripe_customer_id"],
    )

    # Update payment_method CHECK constraint to include 'sepa_debit'
    op.drop_constraint("chk_donations_payment_method", "donations", type_="check")
    op.create_check_constraint(
        "chk_donations_payment_method",
        "donations",
        "payment_method IN ('stripe', 'cash', 'transfer', 'sepa_debit')",
    )

    # Add CHECK constraint for recurring_interval values
    op.create_check_constraint(
        "chk_donations_recurring_interval",
        "donations",
        "recurring_interval IS NULL OR recurring_interval IN ('month', 'year')",
    )


def downgrade() -> None:
    """Remove SEPA and subscription columns from donations table."""
    op.drop_constraint("chk_donations_recurring_interval", "donations", type_="check")

    # Restore original payment_method constraint
    op.drop_constraint("chk_donations_payment_method", "donations", type_="check")
    op.create_check_constraint(
        "chk_donations_payment_method",
        "donations",
        "payment_method IN ('stripe', 'cash', 'transfer')",
    )

    op.drop_index("ix_donations_stripe_customer_id", table_name="donations")
    op.drop_index("ix_donations_stripe_subscription_id", table_name="donations")
    op.drop_column("donations", "recurring_interval")
    op.drop_column("donations", "is_recurring")
    op.drop_column("donations", "stripe_customer_id")
    op.drop_column("donations", "stripe_subscription_id")
