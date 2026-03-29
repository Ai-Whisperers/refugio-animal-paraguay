"""Add TOTP 2FA columns to users table.

Adds totp_secret (nullable string) and totp_enabled (bool default false).

Revision ID: 088
Revises: 087
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "088"
down_revision = "087"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("totp_secret", sa.String(64), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "totp_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
