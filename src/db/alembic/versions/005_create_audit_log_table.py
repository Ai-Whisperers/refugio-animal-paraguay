"""Create audit_logs table for GDPR Article 30 compliance.

Revision ID: 005
Revises: 004
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("http_method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("old_values", JSONB, nullable=True),
        sa.Column("new_values", JSONB, nullable=True),
    )

    # Individual column indexes
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # Composite indexes for common query patterns
    op.create_index(
        "ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"]
    )
    op.create_index(
        "ix_audit_logs_resource_timestamp",
        "audit_logs",
        ["resource_type", "resource_id", "timestamp"],
    )

    # CHECK constraints for enum values
    op.execute(
        """
        ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_action
        CHECK (action IN (
            'create', 'read', 'update', 'delete',
            'approve', 'reject', 'assign', 'export',
            'login', 'logout'
        ))
        """
    )
    op.execute(
        """
        ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_resource_type
        CHECK (resource_type IN (
            'animal', 'adopter', 'adoption_request',
            'donor', 'donation', 'user', 'photo', 'system'
        ))
        """
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
