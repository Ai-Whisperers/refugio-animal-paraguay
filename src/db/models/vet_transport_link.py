"""SQLAlchemy ORM model for linking transport requests to vet visits."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class LinkStatus(StrEnum):
    """Status of a vet-transport link."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


VALID_LINK_STATUSES = {s.value for s in LinkStatus}


class VetTransportLink(Base):
    """Links a transport request to a vet visit for coordinated logistics."""

    __tablename__ = "vet_transport_links"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    transport_request_id: Mapped[UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("transport_requests.id"), nullable=False
    )
    vet_visit_id: Mapped[UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("vet_visits.id"), nullable=False
    )
    animal_id: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("animals.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=LinkStatus.SCHEDULED.value
    )
    pickup_time: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    dropoff_time: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    created_by: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    __table_args__ = (
        sa.UniqueConstraint("transport_request_id", "vet_visit_id", name="uq_transport_vet_visit"),
        sa.Index("ix_vet_transport_links_transport_id", "transport_request_id"),
        sa.Index("ix_vet_transport_links_vet_visit_id", "vet_visit_id"),
        sa.Index("ix_vet_transport_links_animal_id", "animal_id"),
    )
