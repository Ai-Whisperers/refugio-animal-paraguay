"""Create vet_vouchers table for veterinary service voucher system.

Vouchers are purchased by donors and redeemed at partner clinics.
Lifecycle: purchased -> assigned -> redeemed (or expired/cancelled).

Revision ID: 038
Revises: 037
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vet_vouchers",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "code",
            sa.String(20),
            nullable=False,
            unique=True,
            comment="Human-readable voucher code (e.g. VV-A1B2C3D4)",
        ),
        sa.Column(
            "amount_pyg",
            sa.Integer,
            nullable=False,
            comment="Voucher value in Paraguayan Guarani",
        ),
        sa.Column(
            "amount_eur",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Original EUR amount paid by donor (for reporting)",
        ),
        sa.Column(
            "donor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "beneficiary_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "clinic_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
            nullable=True,
            comment="Restrict to specific clinic (NULL = any active clinic)",
        ),
        sa.Column(
            "redeemed_clinic_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "service_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clinic_services.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_category", sa.String(50), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'purchased'"),
        ),
        sa.Column(
            "purchased_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Voucher expiry date",
        ),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
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
        # Constraints
        sa.CheckConstraint(
            "status IN ('purchased', 'assigned', 'redeemed', 'expired', 'cancelled')",
            name="chk_vet_vouchers_status",
        ),
        sa.CheckConstraint("amount_pyg > 0", name="chk_vet_vouchers_amount_pyg"),
        sa.CheckConstraint(
            "amount_eur IS NULL OR amount_eur > 0",
            name="chk_vet_vouchers_amount_eur",
        ),
    )

    # Indexes
    op.create_index("ix_vet_vouchers_code", "vet_vouchers", ["code"])
    op.create_index("ix_vet_vouchers_status", "vet_vouchers", ["status"])
    op.create_index("ix_vet_vouchers_donor_id", "vet_vouchers", ["donor_id"])
    op.create_index("ix_vet_vouchers_beneficiary_id", "vet_vouchers", ["beneficiary_id"])
    op.create_index("ix_vet_vouchers_expires_at", "vet_vouchers", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_vet_vouchers_expires_at", table_name="vet_vouchers")
    op.drop_index("ix_vet_vouchers_beneficiary_id", table_name="vet_vouchers")
    op.drop_index("ix_vet_vouchers_donor_id", table_name="vet_vouchers")
    op.drop_index("ix_vet_vouchers_status", table_name="vet_vouchers")
    op.drop_index("ix_vet_vouchers_code", table_name="vet_vouchers")
    op.drop_table("vet_vouchers")
