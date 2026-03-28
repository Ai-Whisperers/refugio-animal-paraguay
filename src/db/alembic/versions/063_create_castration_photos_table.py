"""Create castration_photos table.

Revision ID: 063
Revises: 062
Create Date: 2026-03-28

Stores before/after/recovery photos for castration campaign voucher
redemptions. Only photos with public_consent=True appear in the
public gallery.
"""

import sqlalchemy as sa
from alembic import op

revision = "063"
down_revision = "062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "castration_photos",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "vet_voucher_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_vouchers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "campaign_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("castration_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column(
            "photo_type",
            sa.String(20),
            nullable=False,
            comment="before | after | recovery",
        ),
        sa.Column("animal_name", sa.String(200), nullable=False),
        sa.Column("animal_species", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "public_consent",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "is_featured",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "uploaded_by_clinic_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "uploaded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "photo_type IN ('before', 'after', 'recovery')",
            name="chk_castration_photo_type",
        ),
    )
    op.create_index(
        "ix_castration_photos_campaign_consent",
        "castration_photos",
        ["campaign_id", "public_consent"],
    )


def downgrade() -> None:
    op.drop_index("ix_castration_photos_campaign_consent", table_name="castration_photos")
    op.drop_table("castration_photos")
