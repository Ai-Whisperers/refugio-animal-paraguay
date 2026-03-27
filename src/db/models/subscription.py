"""SQLAlchemy ORM model for recurring donation subscriptions."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class SubscriptionStatus(enum.StrEnum):
    """Subscription lifecycle status — mirrors Stripe subscription statuses."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class SubscriptionInterval(enum.StrEnum):
    """Billing interval for subscriptions."""

    MONTH = "month"
    YEAR = "year"


class Subscription(Base):
    """Recurring donation subscription — tracks Stripe subscription lifecycle.

    Each subscription belongs to a donor and tracks the billing relationship
    with Stripe. Individual payments from invoices are recorded as Donation
    records linked back via stripe_subscription_id.
    """

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donor_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Stripe identifiers
    stripe_subscription_id: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
        index=True,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    stripe_payment_method_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    # Billing details
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="EUR",
    )
    interval: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
        server_default="month",
    )
    # Lifecycle
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="active",
        index=True,
    )
    # When the current billing period started and ends
    current_period_start: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # Cancellation tracking
    cancel_at_period_end: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # Payment failure tracking for dunning
    last_payment_error: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    failed_payment_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
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

    donor: Mapped["Donor"] = relationship(  # noqa: F821
        "Donor",
        lazy="select",
    )
