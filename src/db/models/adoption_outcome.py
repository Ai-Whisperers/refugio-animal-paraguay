"""SQLAlchemy ORM model for adoption outcome tracking."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class AdoptionOutcomeType(StrEnum):
    """Final outcome classification for an adoption."""

    SUCCESSFUL = "successful"
    RETURNED = "returned"
    REHOMED = "rehomed"
    DECEASED = "deceased"
    UNKNOWN = "unknown"


class AdoptionOutcome(Base):
    """Aggregated outcome record for a completed adoption.

    One record per adoption request (created once the adoption enters a
    terminal state). Captures the final outcome type, aggregated welfare
    and satisfaction scores from follow-ups, and return/rehome metadata
    when applicable.
    """

    __tablename__ = "adoption_outcomes"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adoption_request_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adoption_requests.id", name="fk_adoption_outcomes_adoption_request_id"),
        nullable=False,
        unique=True,
        index=True,
    )
    outcome_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="unknown",
        index=True,
    )
    outcome_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Date the outcome was recorded or became effective",
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Aggregated scores (updated by background sync from follow-ups)
    avg_welfare_score: Mapped[float | None] = mapped_column(
        sa.Float,
        nullable=True,
        comment="Average welfare score (1-5) across all completed follow-ups",
    )
    avg_satisfaction_score: Mapped[float | None] = mapped_column(
        sa.Float,
        nullable=True,
        comment="Average adopter satisfaction score (1-5) across completed follow-ups",
    )
    total_follow_ups: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
        comment="Total number of scheduled follow-ups for this adoption",
    )
    completed_follow_ups: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
        comment="Number of follow-ups completed by the adopter",
    )

    # Return/rehome metadata (populated only when outcome_type in RETURNED/REHOMED)
    return_reason_code: Mapped[str | None] = mapped_column(
        sa.String(30),
        nullable=True,
        comment="Standardised return reason code (mirrors FollowUp.return_reason_code)",
    )
    return_date: Mapped[datetime | None] = mapped_column(
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

    # Relationships
    adoption_request: Mapped["AdoptionRequest"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AdoptionRequest",
        foreign_keys=[adoption_request_id],
        lazy="select",
    )
