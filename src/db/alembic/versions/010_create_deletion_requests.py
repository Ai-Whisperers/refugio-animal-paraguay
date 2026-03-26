"""Create deletion_requests table for GDPR Article 17 compliance.

Revision ID: 010
Revises: 009
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deletion_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("subject_type", sa.String(20), nullable=False),
        sa.Column("subject_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_email", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "requested_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("denial_reason", sa.Text, nullable=True),
        sa.Column(
            "requested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "subject_type IN ('donor', 'adopter', 'staff')",
            name="chk_deletion_request_subject_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'executed', 'cancelled', 'denied')",
            name="chk_deletion_request_status",
        ),
    )
    op.create_index(
        "ix_deletion_request_subject",
        "deletion_requests",
        ["subject_type", "subject_id"],
    )
    op.create_index(
        "ix_deletion_request_status",
        "deletion_requests",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_deletion_request_status", table_name="deletion_requests")
    op.drop_index("ix_deletion_request_subject", table_name="deletion_requests")
    op.drop_table("deletion_requests")
