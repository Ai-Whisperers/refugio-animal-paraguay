"""SQLAlchemy ORM model for fundraising campaigns.

Tracks campaign lifecycle, goals, deadlines, and donation associations
for targeted fundraising efforts.
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .donation import Donation


class CampaignCategory(enum.StrEnum):
    """Campaign fund allocation categories."""

    MEDICAL = "medical"
    FOOD = "food"
    OPERATIONS = "operations"
    RESCUE = "rescue"
    FACILITY = "facility"
    OTHER = "other"


class CampaignStatus(enum.StrEnum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Campaign(Base):
    """Fundraising campaign with goal tracking and donation association."""

    __tablename__ = "campaigns"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    goal_amount_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="USD",
    )
    category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="other",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="draft",
    )
    featured: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    deadline: Mapped[date | None] = mapped_column(
        sa.Date,
        nullable=True,
    )
    # Staff member who created the campaign
    created_by_user_id: Mapped[UUID | None] = mapped_column(
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

    # Donations linked to this campaign
    donations: Mapped[list[Donation]] = relationship(
        "Donation",
        primaryjoin="Campaign.id == foreign(Donation.campaign_id)",
        lazy="select",
        viewonly=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "category IN ('medical', 'food', 'operations', 'rescue', 'facility', 'other')",
            name="chk_campaigns_category",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'completed', 'archived')",
            name="chk_campaigns_status",
        ),
        sa.CheckConstraint(
            "goal_amount_cents > 0",
            name="chk_campaigns_goal_positive",
        ),
    )
