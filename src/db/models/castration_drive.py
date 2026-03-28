"""SQLAlchemy ORM model for castration drive scheduling.

A castration drive is a scheduled event within a castration campaign where
animals are brought to a specific clinic/location for spay/neuter procedures.
"""

from datetime import date, datetime, time
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

# Drive status values
DRIVE_STATUS_SCHEDULED = "scheduled"
DRIVE_STATUS_IN_PROGRESS = "in_progress"
DRIVE_STATUS_COMPLETED = "completed"
DRIVE_STATUS_CANCELLED = "cancelled"

VALID_DRIVE_STATUSES = frozenset(
    {
        DRIVE_STATUS_SCHEDULED,
        DRIVE_STATUS_IN_PROGRESS,
        DRIVE_STATUS_COMPLETED,
        DRIVE_STATUS_CANCELLED,
    }
)


class CastrationDrive(Base):
    """A scheduled castration event within a campaign.

    Represents a single day/session where castrations take place at a
    specific location. Tracks capacity, registrations, and completion.
    """

    __tablename__ = "castration_drives"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    campaign_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("castration_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    location_name: Mapped[str] = mapped_column(sa.String(300), nullable=False)
    location_address: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    drive_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    start_time: Mapped[time | None] = mapped_column(sa.Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(sa.Time, nullable=True)
    max_capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    registered_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    completed_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text(f"'{DRIVE_STATUS_SCHEDULED}'"),
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(sa.String(30), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
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
        sa.CheckConstraint("max_capacity > 0", name="chk_drive_capacity_positive"),
        sa.CheckConstraint(
            "registered_count >= 0",
            name="chk_drive_registered_non_negative",
        ),
        sa.CheckConstraint(
            "completed_count >= 0",
            name="chk_drive_completed_non_negative",
        ),
        sa.CheckConstraint(
            f"status IN ('{DRIVE_STATUS_SCHEDULED}', '{DRIVE_STATUS_IN_PROGRESS}', "
            f"'{DRIVE_STATUS_COMPLETED}', '{DRIVE_STATUS_CANCELLED}')",
            name="chk_drive_status_valid",
        ),
    )

    @property
    def spots_available(self) -> int:
        """Number of remaining registration spots."""
        return max(0, self.max_capacity - self.registered_count)

    @property
    def is_full(self) -> bool:
        """Whether the drive has reached capacity."""
        return self.registered_count >= self.max_capacity
