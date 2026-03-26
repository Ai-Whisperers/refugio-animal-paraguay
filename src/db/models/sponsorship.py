"""SQLAlchemy ORM models for animal sponsorship tiers and sponsorships."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

# ---------------------------------------------------------------------------
# Tier pricing constants (USD cents per month) — configurable source of truth
# ---------------------------------------------------------------------------
BRONZE_AMOUNT_CENTS = 1000  # $10.00/month
SILVER_AMOUNT_CENTS = 2500  # $25.00/month
GOLD_AMOUNT_CENTS = 5000  # $50.00/month


class SponsorshipTierLevel(enum.StrEnum):
    """Sponsorship tier names — must match chk_sponsorship_tiers_level CHECK constraint."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class SponsorshipFrequency(enum.StrEnum):
    """Billing frequency for sponsorships."""

    MONTHLY = "monthly"
    ANNUAL = "annual"


class SponsorshipStatus(enum.StrEnum):
    """Sponsorship lifecycle status.

    Transitions:
      active → paused (donor request)
      active → cancelled (donor request or payment failure after retries)
      active → completed (animal adopted / deceased — natural end)
      paused → active (donor resumes)
      paused → cancelled (donor cancels while paused)
    """

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SponsorshipTier(Base):
    """Reference table for the three sponsorship tiers.

    Seeded at migration time with Bronze/Silver/Gold. Staff can update
    benefit descriptions without code changes.
    """

    __tablename__ = "sponsorship_tiers"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # bronze | silver | gold — unique per tier level
    level: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    # Amount in smallest currency unit (cents) — USD
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="USD",
    )
    # Stripe Price ID for monthly recurring subscription — configured in Stripe dashboard
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    # Stripe Price ID for annual recurring subscription (optional)
    stripe_price_id_annual: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    # JSONB blob describing what this tier includes
    # e.g. {"includes_updates": true, "includes_certificate": true, "includes_visit": false}
    benefits: Mapped[dict | None] = mapped_column(
        sa.JSON,
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    display_order: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
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

    sponsorships: Mapped[list["Sponsorship"]] = relationship(
        "Sponsorship",
        back_populates="tier",
        lazy="select",
    )


class Sponsorship(Base):
    """An active or historical sponsorship linking a donor to an animal.

    Each sponsorship maps to a Stripe Subscription for recurring billing.
    Stripe manages the payment schedule; we store the subscription ID for
    management operations (pause, resume, cancel, upgrade).
    """

    __tablename__ = "sponsorships"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donor_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tier_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("sponsorship_tiers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    frequency: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
        server_default="monthly",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="active",
        index=True,
    )
    # Stripe Subscription ID — set after Stripe subscription is created
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
        unique=True,
    )
    # Running total contributed since sponsorship start (updated by webhooks)
    total_contributed_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
    )
    started_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    # Set when sponsorship ends (cancelled, completed)
    ended_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # Staff notes on why this sponsorship ended or was modified
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

    tier: Mapped["SponsorshipTier"] = relationship(
        "SponsorshipTier",
        back_populates="sponsorships",
        lazy="select",
    )
