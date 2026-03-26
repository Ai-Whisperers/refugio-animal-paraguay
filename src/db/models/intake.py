"""SQLAlchemy ORM model for animal intake records."""

import enum
import logging
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

logger = logging.getLogger(__name__)


class IntakeSource(str, enum.Enum):
    """How the animal arrived at the shelter."""

    STRAY = "stray"
    SURRENDER = "surrender"
    RESCUE = "rescue"
    TRANSFER = "transfer"


class IntakeRecord(Base):
    """Record of an animal's intake into the shelter.

    Captures source, finder information, location, condition on arrival,
    and quarantine status. Links to the Animal record created during intake.
    """

    __tablename__ = "intake_records"

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
        unique=True,
    )
    source: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    finder_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    finder_email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    finder_phone: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    location_found: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    condition_on_arrival: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    requires_quarantine: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    intake_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        index=True,
    )
    staff_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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
    animal: Mapped["Animal"] = relationship("Animal", lazy="selectin")  # type: ignore[name-defined]  # noqa: F821
    staff: Mapped["User"] = relationship("User", lazy="selectin")  # type: ignore[name-defined]  # noqa: F821

    # Indexes defined via __table_args__
    __table_args__ = (
        sa.Index("ix_intake_records_source", "source"),
        sa.Index("ix_intake_records_requires_quarantine", "requires_quarantine"),
    )


def handle_quarantine_trigger(intake_record: IntakeRecord) -> None:
    """Stub for EPIC-4 medical record creation on quarantine.

    When requires_quarantine is True, this function will eventually create
    a medical record flagged for veterinary review. For now, it only logs.

    TODO(EPIC-4): Replace with actual medical record creation.
    """
    if intake_record.requires_quarantine:
        logger.info(
            "Quarantine flagged for animal %s (intake %s) — "
            "medical record creation pending EPIC-4 implementation",
            intake_record.animal_id,
            intake_record.id,
        )
