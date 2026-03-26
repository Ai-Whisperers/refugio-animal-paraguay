"""Add SEPA Direct Debit support.

Creates sepa_mandates table and extends donations payment_method CHECK.

Revision ID: 010
Revises: 009
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Create sepa_mandates table ---
    op.create_table(
        "sepa_mandates",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("donor_id", sa.UUID(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=False),
        sa.Column("stripe_setup_intent_id", sa.String(255), nullable=True),
        sa.Column("stripe_payment_method_id", sa.String(255), nullable=True),
        sa.Column("stripe_mandate_id", sa.String(255), nullable=True),
        sa.Column("iban_last4", sa.String(4), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("interval", sa.String(20), server_default="month", nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('pending', 'active', 'revoked', 'failed')", name="chk_sepa_mandates_status"),
        sa.CheckConstraint("interval IN ('month', 'year')", name="chk_sepa_mandates_interval"),
        sa.CheckConstraint("amount_cents > 0", name="chk_sepa_mandates_amount_positive"),
    )
    op.create_index("ix_sepa_mandates_donor_id", "sepa_mandates", ["donor_id"])
    op.create_index("ix_sepa_mandates_stripe_setup_intent_id", "sepa_mandates", ["stripe_setup_intent_id"])

    # --- Extend donations payment_method CHECK to include sepa_debit ---
    op.drop_constraint("chk_donations_payment_method", "donations", type_="check")
    op.create_check_constraint(
        "chk_donations_payment_method",
        "donations",
        "payment_method IN ('stripe', 'cash', 'transfer', 'sepa_debit')",
    )


def downgrade() -> None:
    # Revert payment_method CHECK
    op.drop_constraint("chk_donations_payment_method", "donations", type_="check")
    op.create_check_constraint(
        "chk_donations_payment_method",
        "donations",
        "payment_method IN ('stripe', 'cash', 'transfer')",
    )

    # Drop sepa_mandates
    op.drop_index("ix_sepa_mandates_stripe_setup_intent_id", "sepa_mandates")
    op.drop_index("ix_sepa_mandates_donor_id", "sepa_mandates")
    op.drop_table("sepa_mandates")
