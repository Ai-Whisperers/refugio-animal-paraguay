"""Create adopter_documents table for EPIC-56 adopter portal document upload.

Adds an adopter_documents table that stores documents uploaded by adopters
to support their adoption applications (ID, proof of residence, etc.).

Revision ID: 092
Revises: 091
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "092"
down_revision = "091"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adopter_documents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "adopter_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("adopters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column(
            "document_type",
            sa.String(30),
            nullable=False,
            server_default="other",
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "uploaded_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_adopter_documents_adopter_id",
        "adopter_documents",
        ["adopter_id"],
    )
    op.create_index(
        "ix_adopter_documents_uploaded_by_user_id",
        "adopter_documents",
        ["uploaded_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_adopter_documents_uploaded_by_user_id", "adopter_documents")
    op.drop_index("ix_adopter_documents_adopter_id", "adopter_documents")
    op.drop_table("adopter_documents")
