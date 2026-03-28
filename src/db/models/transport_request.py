"""SQLAlchemy ORM model for animal transport requests."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TransportUrgency(StrEnum):
    """Urgency levels for transport requests."""

    NORMAL = "normal"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class TransportStatus(StrEnum):
    """Status lifecycle for transport requests."""

    OPEN = "open"
    CLAIMED = "claimed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


VALID_URGENCIES = {u.value for u in TransportUrgency}
VALID_STATUSES = {s.value for s in TransportStatus}


class TransportRequest(Base):
    """A request to transport an animal between locations."""

    __tablename__ = "transport_requests"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    requester_id: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animals.id"), nullable=True
    )
    pickup_location: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    destination: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    urgency: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=TransportUrgency.NORMAL.value
    )
    preferred_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=TransportStatus.OPEN.value
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    claimed_by: Mapped[UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    __table_args__ = (
        sa.Index("ix_transport_requests_status", "status"),
        sa.Index("ix_transport_requests_urgency", "urgency"),
        sa.Index("ix_transport_requests_requester_id", "requester_id"),
    )
