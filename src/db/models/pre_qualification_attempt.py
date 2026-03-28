"""SQLAlchemy ORM model for pre-qualification attempt tracking."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class QualificationOutcome(enum.StrEnum):
    """Outcome of a pre-qualification attempt."""

    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


class PreQualificationAttempt(Base):
    """Records each pre-qualification attempt for analytics.

    Captures the outcome, score, animal targeted, and which requirements
    were failed — enabling aggregate reporting on pass/fail rates,
    common blockers, and popular animals.
    """

    __tablename__ = "pre_qualification_attempts"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Staff user who ran the pre-qualification (nullable for anonymous)
    user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    outcome: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    # JSON list of failed requirement types for drill-down analytics
    failed_requirement_types: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    # Count of failed mandatory requirements
    mandatory_failures: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
    )
    # Count of failed preferred requirements
    preferred_failures: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        index=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "outcome IN ('qualified', 'disqualified')",
            name="chk_pqa_outcome",
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100",
            name="chk_pqa_score_range",
        ),
    )
