"""Create expenses and donation_allocations tables.

Revision ID: 042
Revises: 041
Create Date: 2026-03-27

Adds expense tracking and donation allocation linking, enabling
donors to see how their contributions are used.
"""

import sqlalchemy as sa
from alembic import op

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PYG"),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column(
            "related_animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recorded_by_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.CheckConstraint("amount_cents > 0", name="chk_expenses_amount_positive"),
        sa.CheckConstraint(
            "category IN ('food', 'medical', 'transport', 'housing', 'other')",
            name="chk_expenses_category",
        ),
    )
    op.create_index("ix_expenses_category", "expenses", ["category"])
    op.create_index("ix_expenses_related_animal_id", "expenses", ["related_animal_id"])

    op.create_table(
        "donation_allocations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "donation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "expense_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("expenses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column(
            "allocated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "amount_cents > 0",
            name="chk_donation_allocations_amount_positive",
        ),
    )
    op.create_index(
        "ix_donation_allocations_donation_id",
        "donation_allocations",
        ["donation_id"],
    )
    op.create_index(
        "ix_donation_allocations_expense_id",
        "donation_allocations",
        ["expense_id"],
    )


def downgrade() -> None:
    op.drop_table("donation_allocations")
    op.drop_table("expenses")
