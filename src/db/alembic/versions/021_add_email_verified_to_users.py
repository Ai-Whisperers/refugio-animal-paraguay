"""Add email_verified column to users table.

Revision ID: 021
Revises: 020
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Existing users created before this migration are treated as verified
    # so they are not locked out of the system.
    op.execute("UPDATE users SET email_verified = true")


def downgrade() -> None:
    op.drop_column("users", "email_verified")
