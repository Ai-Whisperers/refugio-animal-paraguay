"""070: Add tax_id_encrypted and tax_id_type to donors table.

Stores encrypted donor tax identification numbers (BSN/TIN) for EU
compliance and ANBI giftenaftrek documentation.

Revision ID: 070
Revises: 069
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "070"
down_revision = "069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donors",
        sa.Column("tax_id_encrypted", sa.Text, nullable=True),
    )
    op.add_column(
        "donors",
        sa.Column(
            "tax_id_type",
            sa.String(10),
            nullable=True,
            comment="Tax ID type: BSN (Dutch), TIN, CPF, etc.",
        ),
    )


def downgrade() -> None:
    op.drop_column("donors", "tax_id_type")
    op.drop_column("donors", "tax_id_encrypted")
