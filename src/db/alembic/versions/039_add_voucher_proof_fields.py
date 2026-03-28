"""Add proof and invoice fields to vet_vouchers for clinic redemption.

Revision ID: 039
Revises: 038
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vet_vouchers",
        sa.Column("proof_photo_url", sa.String(500), nullable=True, comment="URL of proof photo"),
    )
    op.add_column(
        "vet_vouchers",
        sa.Column(
            "proof_description", sa.String(1000), nullable=True, comment="Description of service"
        ),
    )
    op.add_column(
        "vet_vouchers",
        sa.Column("invoice_url", sa.String(500), nullable=True, comment="URL of clinic invoice"),
    )
    op.add_column(
        "vet_vouchers",
        sa.Column(
            "invoice_filename", sa.String(255), nullable=True, comment="Original invoice filename"
        ),
    )
    op.add_column(
        "vet_vouchers",
        sa.Column(
            "redeemed_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="Clinic staff user who processed the redemption",
        ),
    )


def downgrade() -> None:
    op.drop_column("vet_vouchers", "redeemed_by_user_id")
    op.drop_column("vet_vouchers", "invoice_filename")
    op.drop_column("vet_vouchers", "invoice_url")
    op.drop_column("vet_vouchers", "proof_description")
    op.drop_column("vet_vouchers", "proof_photo_url")
