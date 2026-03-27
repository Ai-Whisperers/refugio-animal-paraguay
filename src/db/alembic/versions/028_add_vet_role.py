"""Add vet role to users table CHECK constraint.

Revision ID: 028
Revises: 027
Create Date: 2026-03-27
"""

from alembic import op

revision = "028"
down_revision = ("025", "026")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old CHECK constraint and add new one with vet role
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_role "
        "CHECK (role IN ('staff', 'admin', 'vet'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_role "
        "CHECK (role IN ('staff', 'admin'))"
    )
