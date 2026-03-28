"""Create user_roles junction table for multi-role support.

Users can have multiple roles simultaneously (adopter + volunteer + donor).
The primary role stays on users.role; this table holds additional roles.

Revision ID: 035
Revises: 031
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "035"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_roles",
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
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    # Add CHECK constraint for valid roles
    op.execute(
        "ALTER TABLE user_roles ADD CONSTRAINT chk_user_roles_role "
        "CHECK (role IN ('staff', 'admin', 'vet', 'adopter', 'donor', 'volunteer', 'foster'))"
    )

    # Seed: insert each existing user's primary role into user_roles
    op.execute(
        "INSERT INTO user_roles (user_id, role) "
        "SELECT id, role FROM users ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("user_roles")
