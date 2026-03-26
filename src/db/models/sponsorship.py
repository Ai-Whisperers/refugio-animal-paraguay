"""SQLAlchemy ORM model for animal sponsorships.

Tracks recurring sponsorship subscriptions linking donors to specific animals
at configurable tier levels (Bronze, Silver, Gold) via Stripe Subscriptions.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .animal import Animal
    from .donation import Donor


class SponsorshipTier(enum.StrEnum):
    """Sponsorship pricing tiers — must match chk_sponsorships_tier CHECK constraint."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


# Tier pricing in cents (configurable defaults)
TIER_AMOUNT_CENTS: dict[str, int] = {
    SponsorshipTier.BRONZE: 1000,   # $10/month
    SponsorshipTier.SILVER: 2500,   # $25/month
    SponsorshipTier.GOLD: 5000,     # $50/month
}


class SponsorshipStatus(enum.StrEnum):
    """Sponsorship lifecycle status — must match chk_sponsorships_status CHECK constraint."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class Sponsorship(Base):
    """Recurring animal sponsorship — links a donor to an animal via Stripe Subscription.

    Amount stored as integer cents to avoid float precision loss.
    """

    __tablename__ = "sponsorships"

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
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="USD",
    )
    interval: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="month",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="active",
    )
    # Stripe references
    stripe_customer_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    # Lifecycle timestamps
    started_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
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

    # Relationships
    donor: Mapped["Donor"] = relationship("Donor", lazy="select")
    animal: Mapped["Animal"] = relationship("Animal", lazy="select")

    __table_args__ = (
        sa.CheckConstraint(
            "tier IN ('bronze', 'silver', 'gold')",
            name="chk_sponsorships_tier",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'cancelled', 'past_due')",
            name="chk_sponsorships_status",
        ),
        sa.CheckConstraint(
            "interval IN ('month', 'year')",
            name="chk_sponsorships_interval",
        ),
        sa.CheckConstraint(
            "amount_cents > 0",
            name="chk_sponsorships_amount_positive",
        ),
        # Partial unique index enforced in migration (only active/paused)
    )
