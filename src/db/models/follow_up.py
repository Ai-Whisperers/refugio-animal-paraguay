"""SQLAlchemy ORM models for post-adoption follow-up tracking."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class FollowUpStatus(enum.StrEnum):
    """Status of a scheduled follow-up check."""

    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ReturnReasonCode(enum.StrEnum):
    """Standardised reason codes for adoption returns/rehomes."""

    MOVED_AWAY = "moved_away"
    BEHAVIOR_ISSUES = "behavior_issues"
    FAMILY_CIRCUMSTANCES = "family_circumstances"
    ALLERGIES = "allergies"
    HOUSING_SITUATION = "housing_situation"
    FINANCIAL = "financial"
    TIME_CONSTRAINTS = "time_constraints"
    OTHER = "other"


FOLLOW_UP_SCHEDULE_DAYS = (7, 30, 90, 365)
"""Standard follow-up intervals in days after adoption completion."""


class FollowUp(Base):
    """A scheduled post-adoption follow-up check.

    Automatically created when an adoption is completed.  One row per
    scheduled check-in (7d, 30d, 90d, 365d).
    """

    __tablename__ = "follow_ups"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adoption_request_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adoption_requests.id", name="fk_follow_ups_adoption_request_id"),
        nullable=False,
    )
    scheduled_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    day_offset: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        comment="Days after adoption (7, 30, 90, 365)",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
        index=True,
    )
    survey_sent_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    survey_completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Survey response (nullable until adopter completes it)
    welfare_score: Mapped[int | None] = mapped_column(
        sa.SmallInteger,
        nullable=True,
        comment="1-5 welfare assessment",
    )
    satisfaction_score: Mapped[int | None] = mapped_column(
        sa.SmallInteger,
        nullable=True,
        comment="1-5 adopter satisfaction",
    )
    comments: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    issues_noted: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Return/rehome tracking
    return_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    return_reason_code: Mapped[str | None] = mapped_column(
        sa.String(30),
        nullable=True,
    )
    return_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

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

    # Relationships
    adoption_request: Mapped["AdoptionRequest"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AdoptionRequest",
        foreign_keys=[adoption_request_id],
        lazy="select",
    )
