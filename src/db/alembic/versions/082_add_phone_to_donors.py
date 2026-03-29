"""Add phone column to donors table (RAP-203).

Allows WhatsApp receipt delivery to donors who have provided a WhatsApp-capable
phone number. Column is nullable because existing donors may not have a phone
number, and phone is not required for donation processing.

Revision ID: 082
Revises: 081
Create Date: 2026-03-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "082"
down_revision: str | None = "081"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "donors",
        sa.Column(
            "phone",
            sa.String(50),
            nullable=True,
            comment="E.164 phone number for WhatsApp receipt delivery (e.g. +595981234567)",
        ),
    )
    op.create_index("ix_donors_phone", "donors", ["phone"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_donors_phone", table_name="donors")
    op.drop_column("donors", "phone")
