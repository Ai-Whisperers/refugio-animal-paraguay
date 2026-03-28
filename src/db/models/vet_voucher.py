"""SQLAlchemy ORM model for veterinary vouchers.

Vouchers are purchased by donors and redeemed at partner clinics for
veterinary services. They follow a lifecycle: purchased -> assigned ->
redeemed (or expired/cancelled).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VoucherStatus(StrEnum):
    """Voucher lifecycle status."""

    PURCHASED = "purchased"
    ASSIGNED = "assigned"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Valid status transitions
VALID_VOUCHER_TRANSITIONS: dict[str, set[str]] = {
    VoucherStatus.PURCHASED: {
        VoucherStatus.ASSIGNED,
        VoucherStatus.CANCELLED,
        VoucherStatus.EXPIRED,
    },
    VoucherStatus.ASSIGNED: {
        VoucherStatus.REDEEMED,
        VoucherStatus.CANCELLED,
        VoucherStatus.EXPIRED,
    },
    VoucherStatus.REDEEMED: set(),
    VoucherStatus.EXPIRED: set(),
    VoucherStatus.CANCELLED: set(),
}


class VetVoucher(Base):
    """A veterinary service voucher purchased by a donor.

    Vouchers have a monetary value in PYG and can be redeemed at any
    active partner clinic. They can optionally be restricted to a
    specific clinic or service category.
    """

    __tablename__ = "vet_vouchers"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # -- Voucher code (human-readable, unique) --
    code: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Human-readable voucher code (e.g. VV-A1B2C3D4)",
    )

    # -- Monetary value --
    amount_pyg: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        comment="Voucher value in Paraguayan Guarani",
    )
    amount_eur: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 2),
        nullable=True,
        comment="Original EUR amount paid by donor (for reporting)",
    )

    # -- Relationships --
    donor_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Donor who purchased the voucher",
    )
    beneficiary_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Rescuer/user the voucher is assigned to",
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
        nullable=True,
        comment="Restrict to specific clinic (NULL = any active clinic)",
    )
    redeemed_clinic_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
        nullable=True,
        comment="Clinic where the voucher was actually redeemed",
    )
    service_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("clinic_services.id", ondelete="SET NULL"),
        nullable=True,
        comment="Service the voucher was redeemed for",
    )

    # -- Service category restriction --
    service_category: Mapped[str | None] = mapped_column(
        sa.String(50),
        nullable=True,
        comment="Restrict to category (NULL = any service)",
    )

    # -- Status --
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'purchased'"),
    )

    # -- Dates --
    purchased_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        comment="Voucher expiry date",
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )

    # -- Proof of service (populated at redemption) --
    proof_photo_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
        comment="URL of proof photo",
    )
    proof_description: Mapped[str | None] = mapped_column(
        sa.String(1000),
        nullable=True,
        comment="Description of service performed",
    )
    invoice_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
        comment="URL of clinic invoice",
    )
    invoice_filename: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        comment="Original invoice filename",
    )
    redeemed_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Clinic staff user who processed the redemption",
    )

    # -- Notes --
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    # -- Timestamps --
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('purchased', 'assigned', 'redeemed', 'expired', 'cancelled')",
            name="chk_vet_vouchers_status",
        ),
        sa.CheckConstraint("amount_pyg > 0", name="chk_vet_vouchers_amount_pyg"),
        sa.CheckConstraint(
            "amount_eur IS NULL OR amount_eur > 0",
            name="chk_vet_vouchers_amount_eur",
        ),
        sa.Index("ix_vet_vouchers_status", "status"),
        sa.Index("ix_vet_vouchers_donor_id", "donor_id"),
        sa.Index("ix_vet_vouchers_beneficiary_id", "beneficiary_id"),
        sa.Index("ix_vet_vouchers_expires_at", "expires_at"),
    )
