"""SQLAlchemy ORM models for donors, donations, and in-kind donations."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class CurrencyCode(str, enum.Enum):
    """Supported currencies — must match chk_donations_currency CHECK constraint exactly."""

    EUR = "EUR"
    PYG = "PYG"
    USD = "USD"


class PaymentMethod(str, enum.Enum):
    """Payment methods — must match chk_donations_payment_method CHECK constraint exactly."""

    STRIPE = "stripe"
    CASH = "cash"
    TRANSFER = "transfer"


class DonationStatus(str, enum.Enum):
    """Donation lifecycle status — must match chk_donations_status CHECK constraint exactly."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ItemType(enum.StrEnum):
    """Categories for in-kind donations — must match chk_inkind_item_type CHECK constraint."""

    FOOD = "food"
    MEDICATION = "medication"
    EQUIPMENT = "equipment"
    TOYS = "toys"
    BEDDING = "bedding"
    SUPPLIES = "supplies"
    VETERINARY_SERVICES = "veterinary_services"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class Donor(Base):
    """Donor profile — separate from adopters; EU donors tracked for GDPR compliance."""

    __tablename__ = "donors"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    country: Mapped[str | None] = mapped_column(sa.String(2), nullable=True)
    # Preferred currency for display and default donation creation
    currency_preference: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="EUR",
    )
    # Nullable: consent recorded when given; None = not yet obtained
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
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

    donations: Mapped[list["Donation"]] = relationship(
        "Donation",
        back_populates="donor",
        lazy="select",
    )
    in_kind_donations: Mapped[list["InKindDonation"]] = relationship(
        "InKindDonation",
        back_populates="donor",
        lazy="select",
    )


class Donation(Base):
    """Individual donation record — amount stored as integer cents to avoid float precision loss."""

    __tablename__ = "donations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # Nullable: anonymous donations allowed
    donor_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Integer cents: 1000 EUR = €10.00; avoids float precision issues
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="EUR",
    )
    payment_method: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="stripe",
    )
    # Populated after Stripe PaymentIntent is created
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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

    donor: Mapped["Donor | None"] = relationship(
        "Donor",
        back_populates="donations",
        lazy="select",
    )


class InKindDonation(Base):
    """Non-cash donation record — estimated value stored as integer cents."""

    __tablename__ = "in_kind_donations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donor_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="1")
    # Estimated value in smallest currency unit (cents for EUR/USD, guaranies for PYG)
    estimated_value_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="EUR",
    )
    date_received: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    # Staff member who received/recorded the donation
    received_by_staff_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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

    donor: Mapped["Donor | None"] = relationship(
        "Donor",
        back_populates="in_kind_donations",
        lazy="select",
    )
