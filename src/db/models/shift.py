"""SQLAlchemy ORM models for volunteer shift scheduling."""

from datetime import date, datetime, time
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ShiftStatus(StrEnum):
    """Lifecycle status of a scheduled shift."""

    OPEN = "open"
    FULL = "full"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ShiftRole(StrEnum):
    """Type of work performed during a shift."""

    ANIMAL_CARE = "animal_care"
    VETERINARY_ASSISTANCE = "veterinary_assistance"
    CLEANING = "cleaning"
    TRANSPORT_DRIVING = "transport_driving"
    ADMIN_OFFICE = "admin_office"
    EDUCATION_OUTREACH = "education_outreach"
    EVENT_COORDINATION = "event_coordination"
    GENERAL = "general"


VALID_SHIFT_STATUSES = {s.value for s in ShiftStatus}
VALID_SHIFT_ROLES = {r.value for r in ShiftRole}

SHIFT_CAPACITY_MIN = 1
SHIFT_CAPACITY_MAX = 50


class Shift(Base):
    """A scheduled volunteer shift with time slot and capacity."""

    __tablename__ = "shifts"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    created_by: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    shift_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(sa.Time(timezone=False), nullable=False)
    end_time: Mapped[time] = mapped_column(sa.Time(timezone=False), nullable=False)
    role: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'general'"),
    )
    capacity: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=1)
    slots_filled: Mapped[int] = mapped_column(
        sa.SmallInteger, nullable=False, server_default=sa.text("0")
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'open'"),
        index=True,
    )
    title: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    location: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
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
            "status IN ('open', 'full', 'cancelled', 'completed')",
            name="chk_shift_status_valid",
        ),
        sa.CheckConstraint(
            f"capacity >= {SHIFT_CAPACITY_MIN} AND capacity <= {SHIFT_CAPACITY_MAX}",
            name="chk_shift_capacity_range",
        ),
        sa.CheckConstraint(
            "slots_filled >= 0 AND slots_filled <= capacity",
            name="chk_shift_slots_filled_range",
        ),
        sa.CheckConstraint(
            "end_time > start_time",
            name="chk_shift_end_after_start",
        ),
        sa.CheckConstraint(
            "role IN ('animal_care', 'veterinary_assistance', 'cleaning', "
            "'transport_driving', 'admin_office', 'education_outreach', "
            "'event_coordination', 'general')",
            name="chk_shift_role_valid",
        ),
    )


class ShiftSignup(Base):
    """Junction table — a volunteer signed up for a specific shift."""

    __tablename__ = "shift_signups"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    shift_id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    volunteer_id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    attended: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    signed_up_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    notes: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("shift_id", "volunteer_id", name="uq_shift_signup_volunteer"),
    )
