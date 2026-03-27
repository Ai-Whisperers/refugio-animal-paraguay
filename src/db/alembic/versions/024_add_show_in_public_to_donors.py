"""Add missing ORM columns to donors and donations tables.

Fixes schema drift: the Donor and Donation ORM models define columns that
were not present in the original migrations. Adds:
  - donors.show_in_public (boolean, default True)
  - donations.tigo_transaction_id (varchar 255, nullable)
"""

import sqlalchemy as sa
from alembic import op

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donors",
        sa.Column(
            "show_in_public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "donations",
        sa.Column(
            "tigo_transaction_id",
            sa.String(255),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_donations_tigo_transaction_id",
        "donations",
        ["tigo_transaction_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_donations_tigo_transaction_id", table_name="donations")
    op.drop_column("donations", "tigo_transaction_id")
    op.drop_column("donors", "show_in_public")
