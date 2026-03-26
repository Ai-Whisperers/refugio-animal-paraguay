"""SQLAlchemy ORM model for donation campaigns."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class CampaignStatus(enum.StrEnum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FundCategory(enum.StrEnum):
    """Pre-defined fund categories for campaigns."""

    MEDICAL = "medical"
    FOOD = "food"
    OPERATIONS = "operations"
    RESCUE = "rescue"
    INFRASTRUCTURE = "infrastructure"
    GENERAL = "general"


class Campaign(Base):
    """Donation campaign — a fundraising initiative with a target amount and deadline."""

    __tablename__ = "campaigns"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # Optional longer narrative about the campaign's impact
    impact_story: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Target amount in smallest currency unit (cents for EUR/USD)
    target_amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    # Currency for the campaign target
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="EUR",
    )
    fund_category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="general",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="draft",
    )
    # Optional campaign image URL
    image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    # Optional deadline; campaigns without deadline run indefinitely
    deadline: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # Minimum and maximum donation amounts in cents (optional)
    min_donation_cents: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_donation_cents: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    # Whether to allow donations after target is reached
    allow_overfunding: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    # Staff member who created the campaign
    created_by_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
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

    donations: Mapped[list["CampaignDonation"]] = relationship(
        "CampaignDonation",
        back_populates="campaign",
        lazy="select",
    )


class CampaignDonation(Base):
    """Junction linking a donation to a campaign for tracking campaign progress."""

    __tablename__ = "campaign_donations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    campaign_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    donation_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="donations",
        lazy="select",
    )
