"""SQLAlchemy ORM model for adoption trial periods."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TrialStatus(StrEnum):
    """Trial period lifecycle status."""

    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"
    EXTENDED = "extended"


DEFAULT_TRIAL_DAYS = 14
DEFAULT_CHECK_IN_DAYS = [3, 7, 14]


class TrialPeriod(Base):
    """Adoption trial period with check-in schedule."""

    __tablename__ = "trial_periods"

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
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    check_in_schedule: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="active",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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
            "status IN ('active', 'passed', 'failed', 'extended')",
            name="chk_trial_status_valid",
        ),
    )


class TrialCheckIn(Base):
    """Adopter check-in response during trial period."""

    __tablename__ = "trial_check_ins"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    trial_period_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("trial_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    how_is_animal: Mapped[str] = mapped_column(sa.Text, nullable=False)
    photos: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )
    issues: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    happiness_rating: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    has_issues: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "happiness_rating >= 1 AND happiness_rating <= 5",
            name="chk_checkin_rating_range",
        ),
        sa.CheckConstraint(
            "day_number > 0",
            name="chk_checkin_day_positive",
        ),
    )
