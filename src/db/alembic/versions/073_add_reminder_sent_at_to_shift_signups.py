"""Add reminder_sent_at to shift_signups.

Revision ID: 073
Revises: 072
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "073"
down_revision = "072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shift_signups",
        sa.Column(
            "reminder_sent_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("shift_signups", "reminder_sent_at")
