"""Alembic migration: Create users table for staff/admin authentication.

Adds the users table with hashed passwords and role-based access control.
Roles: staff (shelter employees) and admin (full access).
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.String(50),
            nullable=False,
            server_default="staff",
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('staff', 'admin')",
            name="chk_users_role",
        ),
        sa.CheckConstraint(
            "email ~* '^[^@]+@[^@]+\\.[^@]+$'",
            name="chk_users_email_format",
        ),
    )

    op.create_index("idx_users_email", "users", ["email"])


def downgrade() -> None:
    """Drop users table."""
    op.drop_table("users")
