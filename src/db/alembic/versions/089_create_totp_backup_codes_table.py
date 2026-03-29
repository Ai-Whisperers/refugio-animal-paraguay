"""Create totp_backup_codes table for 2FA recovery codes.

Each user may have up to 10 single-use backup codes stored as bcrypt hashes.
A code is marked used_at when consumed during login recovery.

Revision ID: 089
Revises: 088
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "089"
down_revision = "088"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "totp_backup_codes",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_totp_backup_codes_user_id",
        "totp_backup_codes",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_totp_backup_codes_user_id", table_name="totp_backup_codes")
    op.drop_table("totp_backup_codes")
