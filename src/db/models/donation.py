"""SQLAlchemy ORM models for donors and donations."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class DonationTargetType(enum.StrEnum):
    """Donation target types — determines where a donation is directed."""

    GENERAL = "general"
    ANIMAL = "animal"
    RESCUER = "rescuer"
    CLINIC = "clinic"
    CAMPAIGN = "campaign"
    NEED = "need"
    EMERGENCY = "emergency"


class CurrencyCode(enum.StrEnum):
    """Supported currencies — must match chk_donations_currency CHECK constraint exactly."""

    EUR = "EUR"
    PYG = "PYG"
    USD = "USD"


class PaymentMethod(enum.StrEnum):
    """Payment methods — must match chk_donations_payment_method CHECK constraint exactly."""

    STRIPE = "stripe"
    CASH = "cash"
    TRANSFER = "transfer"
    SEPA_DEBIT = "sepa_debit"
    TIGO_MONEY = "tigo_money"


class RecurringInterval(enum.StrEnum):
    """Recurring donation intervals — must match chk_donations_recurring_interval."""

    MONTH = "month"
    YEAR = "year"


class DonationStatus(enum.StrEnum):
    """Donation lifecycle status — must match chk_donations_status CHECK constraint exactly."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


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
    # Whether this donor opts in to public listing on campaign social proof pages.
    # Defaults to True (visible); donors can opt out via preference settings.
    show_in_public: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
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
    # Stripe subscription ID for recurring donations
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    # Stripe customer ID — required for subscriptions and SEPA mandates
    stripe_customer_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    # Tigo Money transaction ID — populated when payment_method = tigo_money
    tigo_transaction_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    # Whether this donation is part of a recurring subscription
    is_recurring: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    # Recurring interval: 'month' or 'year' (null for one-time donations)
    recurring_interval: Mapped[str | None] = mapped_column(
        sa.String(20),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
    )
    # Paper receipt reference for cash donations — cross-references physical receipt book
    receipt_number: Mapped[str | None] = mapped_column(
        sa.String(50),
        nullable=True,
    )
    # Fund category for transparency reporting (medical, food, operations, etc.)
    fund_category: Mapped[str | None] = mapped_column(
        sa.String(20),
        nullable=True,
        index=True,
    )
    # Flexible donation target: where the donation is directed
    target_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="general",
        index=True,
    )
    # UUID of the target entity (animal, rescuer, clinic, campaign, need)
    # NULL when target_type is 'general'
    target_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
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
        back_populates="donations",
        lazy="select",
    )
