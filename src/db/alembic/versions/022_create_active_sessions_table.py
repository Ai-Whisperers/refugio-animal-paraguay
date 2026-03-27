"""Create active_sessions table for session tracking and forced logout.

Revision ID: 022
Revises: 021
"""

import sqlalchemy as sa
from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "active_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_activity", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
    )
    op.create_index("ix_active_sessions_user_id", "active_sessions", ["user_id"])
    op.create_index("ix_active_sessions_jti", "active_sessions", ["jti"])


def downgrade() -> None:
    op.drop_index("ix_active_sessions_jti")
    op.drop_index("ix_active_sessions_user_id")
    op.drop_table("active_sessions")
