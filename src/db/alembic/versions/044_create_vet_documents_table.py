"""Create vet_documents table for medical document uploads.

Revision ID: 044
Revises: 036
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "044"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vet_documents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "vet_visit_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("document_type", sa.String(30), nullable=False, server_default="other"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "uploaded_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "is_virus_scanned",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("vet_documents")
