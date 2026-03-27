"""SQLAlchemy ORM models for surgical procedure tracking.

Tables:
  surgeries           -- Surgical procedure records linked to an animal
  post_op_checks      -- Post-operative monitoring check-in records
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class SurgeryType(StrEnum):
    """Type of surgical procedure."""

    SPAY = "spay"
    NEUTER = "neuter"
    MASS_REMOVAL = "mass_removal"
    ORTHOPEDIC = "orthopedic"
    DENTAL = "dental"
    EMERGENCY = "emergency"
    BIOPSY = "biopsy"
    EYE = "eye"
    OTHER = "other"


class SurgeryStatus(StrEnum):
    """Status of a surgical procedure."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    COMPLICATIONS = "complications"


class AnesthesiaType(StrEnum):
    """Type of anesthesia used."""

    GENERAL = "general"
    LOCAL = "local"
    SEDATION = "sedation"
    NONE = "none"


class SurgeryOutcome(StrEnum):
    """Outcome of the surgery."""

    SUCCESSFUL = "successful"
    COMPLICATIONS = "complications"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class PostOpStatus(StrEnum):
    """Status of a post-op monitoring check."""

    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    CONCERN = "concern"


class Surgery(Base):
    """A surgical procedure record for an animal."""

    __tablename__ = "surgeries"

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
    surgery_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="other",
    )
    surgery_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="scheduled",
    )
    veterinarian_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    performed_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    anesthesia_type: Mapped[str | None] = mapped_column(
        sa.String(50), nullable=True
    )
    anesthesia_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    procedure_description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    complications: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(
        sa.Numeric(6, 2), nullable=True
    )
    recovery_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
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

    animal: Mapped["Animal"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Animal", back_populates="surgeries"
    )
    post_op_checks: Mapped[list["PostOpCheck"]] = relationship(
        "PostOpCheck",
        back_populates="surgery",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="PostOpCheck.scheduled_time.asc()",
    )


class PostOpCheck(Base):
    """Post-operative monitoring check-in record."""

    __tablename__ = "post_op_checks"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    surgery_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("surgeries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="pending",
    )
    scheduled_time: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
    )
    completed_time: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    checked_by: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(
        sa.Numeric(4, 1), nullable=True
    )
    pain_level: Mapped[int | None] = mapped_column(
        sa.SmallInteger, nullable=True
    )
    appetite: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    mobility: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    wound_condition: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    surgery: Mapped["Surgery"] = relationship(
        "Surgery", back_populates="post_op_checks"
    )
