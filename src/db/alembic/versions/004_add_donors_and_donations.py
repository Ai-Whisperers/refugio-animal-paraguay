"""Alembic migration: Add donors and donations tables.

- Creates donors table with GDPR consent tracking
- Creates donations table with amount-in-cents, currency, Stripe integration
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create donors and donations tables."""

    # ------------------------------------------------------------------
    # TABLE: donors
    # Donor profiles — separate from adopters.
    # EU donors require GDPR consent tracking.
    # ------------------------------------------------------------------
    op.create_table(
        "donors",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column(
            "currency_preference",
            sa.String(3),
            nullable=False,
            server_default="EUR",
        ),
        sa.Column("gdpr_consent_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_donors_email"),
    )
    op.create_index("ix_donors_email", "donors", ["email"])

    # ------------------------------------------------------------------
    # TABLE: donations
    # Amount stored as integer cents to avoid float precision loss.
    # donor_id nullable to support anonymous donations.
    # ------------------------------------------------------------------
    op.create_table(
        "donations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "donor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column(
            "payment_method",
            sa.String(20),
            nullable=False,
            server_default="stripe",
        ),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text, nullable=True),
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
        sa.CheckConstraint(
            "amount_cents > 0", name="chk_donations_amount_cents_positive"
        ),
        sa.CheckConstraint(
            "currency IN ('EUR', 'PYG', 'USD')", name="chk_donations_currency"
        ),
        sa.CheckConstraint(
            "payment_method IN ('stripe', 'cash', 'transfer')",
            name="chk_donations_payment_method",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'refunded')",
            name="chk_donations_status",
        ),
    )
    op.create_index("ix_donations_donor_id", "donations", ["donor_id"])
    op.create_index(
        "ix_donations_stripe_payment_intent_id",
        "donations",
        ["stripe_payment_intent_id"],
    )


def downgrade() -> None:
    """Drop donations and donors tables."""
    op.drop_index("ix_donations_stripe_payment_intent_id", table_name="donations")
    op.drop_index("ix_donations_donor_id", table_name="donations")
    op.drop_table("donations")
    op.drop_index("ix_donors_email", table_name="donors")
    op.drop_table("donors")
