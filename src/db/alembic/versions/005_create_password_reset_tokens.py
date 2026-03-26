"""Alembic migration: Create password_reset_tokens table.

Stores SHA-256 hashed reset tokens with expiration for secure
password recovery flow.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create password_reset_tokens table."""
    op.create_table(
        "password_reset_tokens",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(64),
            nullable=False,
            unique=True,
            comment="SHA-256 hex digest of the plaintext token",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Token invalid after this timestamp (1 hour after creation)",
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Drop password_reset_tokens table."""
    op.drop_index("ix_password_reset_tokens_token_hash")
    op.drop_index("ix_password_reset_tokens_user_id")
    op.drop_table("password_reset_tokens")
