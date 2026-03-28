"""SQLAlchemy ORM model for emergency animal rescue cases."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class EmergencyCaseStatus(StrEnum):
    """Emergency case lifecycle status."""

    ACTIVE = "active"
    FUNDED = "funded"
    CLOSED = "closed"
    EXPIRED = "expired"


class EmergencyUrgency(StrEnum):
    """Urgency level for emergency cases."""

    HIGH = "high"
    CRITICAL = "critical"


class EmergencyCurrency(StrEnum):
    """Supported currencies for emergency fundraising."""

    USD = "USD"
    PYG = "PYG"


class EmergencyCase(Base):
    """Emergency animal rescue case with linked fundraising campaign."""

    __tablename__ = "emergency_cases"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rescuer_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    photos: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )
    amount_needed_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    amount_raised_cents: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False, server_default="USD")
    deadline: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="active", index=True
    )
    urgency: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="high", index=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
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

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('active', 'funded', 'closed', 'expired')",
            name="chk_emergency_status_valid",
        ),
        sa.CheckConstraint(
            "urgency IN ('high', 'critical')",
            name="chk_emergency_urgency_valid",
        ),
        sa.CheckConstraint(
            "currency IN ('USD', 'PYG')",
            name="chk_emergency_currency_valid",
        ),
        sa.CheckConstraint(
            "amount_needed_cents > 0",
            name="chk_emergency_amount_positive",
        ),
        sa.Index("ix_emergency_cases_deadline", "deadline"),
    )
