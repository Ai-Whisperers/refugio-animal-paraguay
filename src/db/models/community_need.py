"""SQLAlchemy ORM model for community needs (donation targets)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class NeedStatus(StrEnum):
    """Community need lifecycle status."""

    OPEN = "open"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class NeedCategory(StrEnum):
    """Category of community need."""

    MEDICAL = "medical"
    FOOD = "food"
    SHELTER = "shelter"
    TRANSPORT = "transport"
    SUPPLIES = "supplies"
    OTHER = "other"


class CommunityNeed(Base):
    """Community need — a specific request that donors can fund."""

    __tablename__ = "community_needs"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=NeedCategory.OTHER,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=NeedStatus.OPEN,
        index=True,
    )
    estimated_cost_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    current_raised_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="USD",
    )
    donor_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    creator_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
