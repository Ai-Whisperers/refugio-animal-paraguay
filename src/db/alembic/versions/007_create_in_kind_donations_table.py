"""Alembic migration: Create in_kind_donations table.

Tracks non-cash donations (food, supplies, vet services) with
estimated monetary values for impact reporting.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

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
        sa.Column("item_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("estimated_value_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PYG"),
        sa.Column(
            "date_received",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "received_by_user_id",
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
    )

    # Check constraint for valid item types
    op.create_check_constraint(
        "chk_in_kind_donations_item_type",
        "in_kind_donations",
        sa.column("item_type").in_(ITEM_TYPES),
    )

    # Composite indexes for common query patterns
    op.create_index(
        "ix_in_kind_donations_donor_date",
        "in_kind_donations",
        ["donor_id", "date_received"],
    )
    op.create_index(
        "ix_in_kind_donations_item_type",
        "in_kind_donations",
        ["item_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_in_kind_donations_item_type", table_name="in_kind_donations")
    op.drop_index("ix_in_kind_donations_donor_date", table_name="in_kind_donations")
    op.drop_constraint(
        "chk_in_kind_donations_item_type", "in_kind_donations", type_="check"
    )
    op.drop_table("in_kind_donations")
