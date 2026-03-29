"""SQLAlchemy ORM model for volunteer hours logging (RAP-195)."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class HoursCategory(StrEnum):
    """Category of volunteer activity for hours logging."""

    ANIMAL_CARE = "animal_care"
    VETERINARY_ASSISTANCE = "veterinary_assistance"
    CLEANING = "cleaning"
    TRANSPORT = "transport"
    ADMIN = "admin"
    EDUCATION_OUTREACH = "education_outreach"
    EVENT = "event"
    FOSTER_CARE = "foster_care"
    FUNDRAISING = "fundraising"
    OTHER = "other"


VALID_HOUR_CATEGORIES = {c.value for c in HoursCategory}

HOURS_MIN_DURATION = 0.25  # 15 minutes minimum
HOURS_MAX_DURATION = 24.0  # 24 hours maximum per log entry


class VolunteerHoursLog(Base):
    """Records hours volunteered outside of structured shifts."""

    __tablename__ = "volunteer_hours_log"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    volunteer_id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("volunteer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    duration_hours: Mapped[float] = mapped_column(
        sa.Numeric(5, 2),
        nullable=False,
        comment="Duration in hours (0.25 min, 24.0 max)",
    )
    category: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Optional link to a shift signup (for shift-based hours)
    shift_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("shifts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Staff approval workflow
    approved: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
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
