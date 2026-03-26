"""Alembic migration: Add receipt_number column to donations table.

Supports cash donation recording with paper receipt cross-referencing.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donations",
        sa.Column("receipt_number", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("donations", "receipt_number")
