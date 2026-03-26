"""Add contract PDF columns to adoption_requests.

Revision ID: 011
Revises: 010
Create Date: 2026-03-26
"""

import sqlalchemy as sa
from alembic import op

revision = "012b"
down_revision = "012a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "adoption_requests",
        sa.Column("contract_pdf_path", sa.Text(), nullable=True),
    )
    op.add_column(
        "adoption_requests",
        sa.Column(
            "contract_generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("adoption_requests", "contract_generated_at")
    op.drop_column("adoption_requests", "contract_pdf_path")
