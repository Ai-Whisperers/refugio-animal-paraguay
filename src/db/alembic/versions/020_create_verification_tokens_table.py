"""Create verification_tokens table for password reset and email verification.

Revision ID: 020
Revises: 019
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verification_tokens",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "token_type",
            sa.String(50),
            nullable=False,
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_verification_tokens_token", "verification_tokens", ["token"], unique=True)
    op.create_index("ix_verification_tokens_user_id", "verification_tokens", ["user_id"])

    # Add check constraint for token_type
    op.create_check_constraint(
        "chk_verification_tokens_type",
        "verification_tokens",
        "token_type IN ('password_reset', 'email_verification')",
    )


def downgrade() -> None:
    op.drop_table("verification_tokens")
