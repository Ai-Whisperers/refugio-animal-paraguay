"""Alembic migration: Add email verification and password reset support.

- Adds is_verified column to users table (default false)
- Creates verification_tokens table for email verification and password reset tokens
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "006"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_verified to users and create verification_tokens table."""
    # Add is_verified column to users — existing users default to false
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Create verification_tokens table
    op.create_table(
        "verification_tokens",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("token_type", sa.String(20), nullable=False),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Indexes for efficient lookups
    op.create_index(
        "ix_verification_tokens_user_id",
        "verification_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_verification_tokens_token_hash",
        "verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_verification_tokens_expires_at",
        "verification_tokens",
        ["expires_at"],
    )

    # CHECK constraint for token_type
    op.execute(
        "ALTER TABLE verification_tokens ADD CONSTRAINT "
        "chk_verification_tokens_token_type "
        "CHECK (token_type IN ('email_verify', 'password_reset'))"
    )


def downgrade() -> None:
    """Remove verification_tokens table and is_verified column."""
    op.drop_table("verification_tokens")
    op.drop_column("users", "is_verified")
