"""Extend verification token types for password change and account deletion.

Revision ID: 032
Revises: 031
Create Date: 2026-03-27
"""

from alembic import op

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "chk_verification_token_type",
        "verification_tokens",
        type_="check",
    )
    op.create_check_constraint(
        "chk_verification_token_type",
        "verification_tokens",
        "token_type IN ('password_reset', 'email_verification', 'password_change', 'account_deletion')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_verification_token_type",
        "verification_tokens",
        type_="check",
    )
    op.create_check_constraint(
        "chk_verification_token_type",
        "verification_tokens",
        "token_type IN ('password_reset', 'email_verification')",
    )
