"""SQLAlchemy ORM model for foster check-in schedules (RAP-192).

Staff schedule periodic welfare check-ins with foster families.  Each check-in
tracks whether it was completed on time, staff notes from the call/visit, and
when a reminder was last dispatched.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHECK_IN_NOTES_MAX_LENGTH = 2000
CHECK_IN_CANCELLATION_REASON_MAX_LENGTH = 500

DEFAULT_INTERVAL_DAYS = 7
MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 90


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class CheckInStatus(StrEnum):
    """Lifecycle status of a scheduled foster check-in."""

    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


CHECK_IN_STATUS_VALUES = frozenset(s.value for s in CheckInStatus)


class CheckInType(StrEnum):
    """How the check-in was initiated."""

    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"


CHECK_IN_TYPE_VALUES = frozenset(t.value for t in CheckInType)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class FosterCheckIn(Base):
    """Scheduled or ad-hoc welfare check-in for an active foster placement."""

    __tablename__ = "foster_check_ins"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    foster_placement_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("foster_placements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_in_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'scheduled'"),
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    # How many days until the next auto-scheduled check-in (0 = no auto-schedule)
    interval_days: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text(str(DEFAULT_INTERVAL_DAYS)),
    )
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
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

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'missed', 'cancelled')",
            name="chk_foster_check_in_status_valid",
        ),
        sa.CheckConstraint(
            "check_in_type IN ('scheduled', 'unscheduled')",
            name="chk_foster_check_in_type_valid",
        ),
        sa.CheckConstraint(
            f"interval_days >= {MIN_INTERVAL_DAYS} AND interval_days <= {MAX_INTERVAL_DAYS}",
            name="chk_foster_check_in_interval_days_range",
        ),
    )
