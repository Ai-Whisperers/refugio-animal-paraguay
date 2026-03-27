"""Add public user registration fields and roles.

Adds full_name, phone columns to users table and extends the role
CHECK constraint to include public roles: adopter, donor, volunteer, foster.

Revision ID: 031
Revises: 030
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full_name column (nullable for backward compat with existing users)
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(100), nullable=True),
    )
    # Add phone column with unique constraint
    op.add_column(
        "users",
        sa.Column("phone", sa.String(20), nullable=True),
    )
    op.create_unique_constraint("uq_users_phone", "users", ["phone"])

    # Extend role CHECK constraint with public roles
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_role "
        "CHECK (role IN ('staff', 'admin', 'vet', 'adopter', 'donor', 'volunteer', 'foster'))"
    )


def downgrade() -> None:
    # Restore original role constraint
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_role "
        "CHECK (role IN ('staff', 'admin', 'vet'))"
    )
    op.drop_constraint("uq_users_phone", "users", type_="unique")
    op.drop_column("users", "phone")
    op.drop_column("users", "full_name")
