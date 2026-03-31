"""SQLAlchemy ORM model for adopter-initiated visit requests."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VisitRequestStatus(StrEnum):
    """Status of an adopter visit request."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class VisitRequest(Base):
    """Adopter-initiated visit scheduling request.

    An adopter proposes one or more preferred time slots for a home visit.
    Staff confirm the most suitable slot, which creates a HomeVisit record.
    """

    __tablename__ = "visit_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adoption_request_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adoption_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    adopter_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adopters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Comma-separated or JSON array of proposed ISO-8601 datetime strings
    proposed_slots: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        comment="List of proposed datetime strings (ISO 8601) for the visit",
    )
    address: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=VisitRequestStatus.PENDING.value,
        index=True,
    )
    # Set when staff confirms a slot and links to a HomeVisit
    confirmed_home_visit_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("home_visits.id", ondelete="SET NULL"),
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

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled', 'expired')",
            name="chk_visit_request_status_valid",
        ),
    )
