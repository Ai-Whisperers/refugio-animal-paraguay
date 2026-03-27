"""Add account lockout columns to users table.

Revision ID: 023
Revises: 022
Create Date: 2026-03-27

Adds failed_login_attempts (int, default 0) and locked_until (timestamp, nullable)
to support account lockout after consecutive failed login attempts.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
