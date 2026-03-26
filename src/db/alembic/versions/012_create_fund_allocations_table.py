"""Create fund_allocations table and add fund_category to donations.

Revision ID: 012
Revises: 010
"""

import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donations",
        sa.Column("fund_category", sa.String(20), nullable=True),
    )
    op.create_index("ix_donations_fund_category", "donations", ["fund_category"])

    op.create_table(
        "fund_allocations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column(
            "amount_cents",
            sa.Integer,
            nullable=False,
            comment="Expense amount in cents (same precision as donations)",
        ),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PYG"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("transaction_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "recorded_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", name="fk_fund_allocations_recorded_by"),
            nullable=True,
        ),
        sa.Column("receipt_reference", sa.String(100), nullable=True),
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
    )
    op.create_index("ix_fund_allocations_category", "fund_allocations", ["category"])
    op.create_index(
        "ix_fund_allocations_transaction_date",
        "fund_allocations",
        ["transaction_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_fund_allocations_transaction_date", table_name="fund_allocations")
    op.drop_index("ix_fund_allocations_category", table_name="fund_allocations")
    op.drop_table("fund_allocations")
    op.drop_index("ix_donations_fund_category", table_name="donations")
    op.drop_column("donations", "fund_category")
