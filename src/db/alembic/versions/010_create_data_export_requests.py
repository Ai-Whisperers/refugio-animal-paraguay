"""Create data_export_requests table for GDPR Article 15/20 compliance.

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
        "data_export_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "requested_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_type", sa.String(20), nullable=False),
        sa.Column("subject_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_email", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("export_data", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "requested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("downloaded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "subject_type IN ('donor', 'adopter', 'staff')",
            name="chk_data_export_subject_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'expired')",
            name="chk_data_export_status",
        ),
    )
    op.create_index(
        "ix_data_export_subject",
        "data_export_requests",
        ["subject_type", "subject_id"],
    )
    op.create_index(
        "ix_data_export_requested_by",
        "data_export_requests",
        ["requested_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_data_export_requested_by", table_name="data_export_requests")
    op.drop_index("ix_data_export_subject", table_name="data_export_requests")
    op.drop_table("data_export_requests")
