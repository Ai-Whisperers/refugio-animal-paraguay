"""Add tigo_money to donations: payment_method constraint + tigo_transaction_id column.

Revision ID: 017
Revises: 016
Create Date: 2026-03-26
"""

from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tigo_transaction_id column for Tigo Money transaction references
    op.execute(
        "ALTER TABLE donations ADD COLUMN IF NOT EXISTS "
        "tigo_transaction_id VARCHAR(255) DEFAULT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_donations_tigo_transaction_id "
        "ON donations (tigo_transaction_id)"
    )

    # Expand the CHECK constraint to include tigo_money.
    # PostgreSQL does not support in-place ALTER CHECK; drop and re-add.
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_payment_method")
    op.execute(
        "ALTER TABLE donations ADD CONSTRAINT chk_donations_payment_method "
        "CHECK (payment_method IN ('stripe', 'cash', 'transfer', 'sepa_debit', 'tigo_money'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_payment_method")
    op.execute(
        "ALTER TABLE donations ADD CONSTRAINT chk_donations_payment_method "
        "CHECK (payment_method IN ('stripe', 'cash', 'transfer', 'sepa_debit'))"
    )
    op.execute("DROP INDEX IF EXISTS ix_donations_tigo_transaction_id")
    op.execute("ALTER TABLE donations DROP COLUMN IF EXISTS tigo_transaction_id")
