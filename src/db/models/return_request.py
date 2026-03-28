"""SQLAlchemy ORM model for adoption return requests.

Tracks cases where adopters return animals, including the reason,
animal condition on return, and whether it's an emergency.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AnimalCondition(enum.StrEnum):
    """Condition of the animal at the time of return."""

    HEALTHY = "healthy"
    INJURED = "injured"
    SICK = "sick"
    DECEASED = "deceased"


class ReturnRequestStatus(enum.StrEnum):
    """Status of a return request."""

    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReturnRequest(Base):
    """Record of an adoption return.

    Created when an adopter returns an animal. Tracks the reason,
    animal condition, and triggers appropriate follow-up actions.
    """

    __tablename__ = "return_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adoption_request_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "adoption_requests.id",
            name="fk_return_requests_adoption_request_id",
        ),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    animal_condition: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="healthy",
    )
    is_emergency: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
    )
    staff_notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    requested_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", name="fk_return_requests_requested_by"),
        nullable=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
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

    __table_args__ = (
        sa.Index(
            "ix_return_requests_adoption",
            "adoption_request_id",
        ),
        sa.Index(
            "ix_return_requests_status",
            "status",
        ),
    )
