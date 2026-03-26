"""Create in_kind_donations table.

Revision ID: 005
Revises: 004
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Valid item_type values — must match ItemType enum in donation.py
ITEM_TYPES = [
    "food",
    "medication",
    "equipment",
    "toys",
    "bedding",
    "supplies",
    "veterinary_services",
    "transportation",
    "other",
]

# Valid currency values — reuse from donations table
CURRENCIES = ["EUR", "PYG", "USD"]


def upgrade() -> None:
    op.create_table(
        "in_kind_donations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "donor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donors.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("estimated_value_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column(
            "date_received",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "received_by_staff_id",
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
        # Constraints
        sa.CheckConstraint(
            f"item_type IN ({', '.join(repr(v) for v in ITEM_TYPES)})",
            name="chk_inkind_item_type",
        ),
        sa.CheckConstraint(
            f"currency IN ({', '.join(repr(v) for v in CURRENCIES)})",
            name="chk_inkind_currency",
        ),
        sa.CheckConstraint("quantity > 0", name="chk_inkind_quantity_positive"),
        sa.CheckConstraint("estimated_value_cents >= 0", name="chk_inkind_value_non_negative"),
    )

    # Indexes for common query patterns
    op.create_index(
        "ix_in_kind_donations_item_type",
        "in_kind_donations",
        ["item_type"],
    )
    op.create_index(
        "ix_in_kind_donations_date_received",
        "in_kind_donations",
        ["date_received"],
    )


def downgrade() -> None:
    op.drop_index("ix_in_kind_donations_date_received", table_name="in_kind_donations")
    op.drop_index("ix_in_kind_donations_item_type", table_name="in_kind_donations")
    op.drop_table("in_kind_donations")
