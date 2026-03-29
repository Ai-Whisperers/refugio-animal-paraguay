"""SQLAlchemy ORM model for foster supply requests (RAP-194).

Foster families can request supplies (food, medication, bedding, toys, etc.)
from the shelter.  Staff review the request and either fulfil it or reject it.

Lifecycle:
    pending → (staff approves) → approved → (staff marks delivered) → fulfilled
    pending → (staff declines) → rejected
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SupplyType(StrEnum):
    """Category of supply being requested."""

    FOOD = "food"
    MEDICATION = "medication"
    BEDDING = "bedding"
    TOYS = "toys"
    TRANSPORT = "transport"
    GROOMING = "grooming"
    OTHER = "other"


class SupplyRequestStatus(StrEnum):
    """Lifecycle status of a supply request."""

    PENDING = "pending"
    APPROVED = "approved"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"


SUPPLY_TYPE_VALUES = frozenset(s.value for s in SupplyType)
SUPPLY_REQUEST_STATUS_VALUES = frozenset(s.value for s in SupplyRequestStatus)

SUPPLY_DESCRIPTION_MIN_LENGTH = 10
SUPPLY_DESCRIPTION_MAX_LENGTH = 1000
SUPPLY_STAFF_NOTES_MAX_LENGTH = 500
SUPPLY_MAX_QUANTITY = 999


class FosterSupplyRequest(Base):
    """A supply request submitted by a foster family."""

    __tablename__ = "foster_supply_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    foster_profile_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("foster_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optionally scoped to a specific active placement
    placement_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("foster_placements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supply_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    quantity: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        index=True,
    )
    # Resolution tracking
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    staff_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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
            f"supply_type IN ({', '.join(repr(v) for v in sorted(SUPPLY_TYPE_VALUES))})",
            name="chk_foster_supply_type_valid",
        ),
        sa.CheckConstraint(
            f"status IN ({', '.join(repr(v) for v in sorted(SUPPLY_REQUEST_STATUS_VALUES))})",
            name="chk_foster_supply_status_valid",
        ),
        sa.CheckConstraint(
            f"length(description) >= {SUPPLY_DESCRIPTION_MIN_LENGTH}",
            name="chk_foster_supply_description_min_len",
        ),
        sa.CheckConstraint(
            f"quantity IS NULL OR (quantity >= 1 AND quantity <= {SUPPLY_MAX_QUANTITY})",
            name="chk_foster_supply_quantity_range",
        ),
    )
