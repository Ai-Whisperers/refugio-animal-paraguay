"""Add OAuth provider columns to users table for social login.

Adds oauth_provider, oauth_id, and profile_picture_url columns.
Makes hashed_password nullable (OAuth users may not have a password).

Revision ID: 038
Revises: 037
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("oauth_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("profile_picture_url", sa.String(500), nullable=True),
    )

    # OAuth users authenticate via provider, so password is not required
    op.alter_column("users", "hashed_password", nullable=True)

    # Unique constraint: one OAuth ID per provider
    op.create_unique_constraint(
        "uq_users_oauth_provider_id",
        "users",
        ["oauth_provider", "oauth_id"],
    )

    # Index for fast OAuth lookups
    op.create_index(
        "ix_users_oauth_provider_oauth_id",
        "users",
        ["oauth_provider", "oauth_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_oauth_provider_oauth_id", table_name="users")
    op.drop_constraint("uq_users_oauth_provider_id", "users", type_="unique")
    op.alter_column("users", "hashed_password", nullable=False)
    op.drop_column("users", "profile_picture_url")
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
