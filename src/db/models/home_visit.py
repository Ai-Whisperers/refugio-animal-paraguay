"""SQLAlchemy ORM model for home visits during adoption process."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class HomeVisitStatus(StrEnum):
    """Possible statuses for a home visit."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HomeVisit(Base):
    """Home visit scheduled as part of the adoption process."""

    __tablename__ = "home_visits"

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
    scheduled_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    staff_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'scheduled'"),
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    photos: Mapped[list | None] = mapped_column(
        sa.JSON,
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
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
            "status IN ('scheduled', 'completed', 'cancelled')",
            name="chk_home_visit_status_valid",
        ),
        sa.Index("ix_home_visits_scheduled_at", "scheduled_at"),
        sa.Index("ix_home_visits_adoption_status", "adoption_request_id", "status"),
    )
