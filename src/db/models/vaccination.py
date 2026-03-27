"""SQLAlchemy ORM models for vaccination management.

Tables:
  vaccine_types         — Catalog of available vaccines (e.g., Rabies, DHPP)
  vaccination_schedules — Species-specific schedule templates
  vaccinations          — Individual vaccination records for animals
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class VaccinationStatus(StrEnum):
    """Status of a vaccination record."""

    SCHEDULED = "scheduled"
    ADMINISTERED = "administered"
    MISSED = "missed"
    CANCELLED = "cancelled"


class VaccineType(Base):
    """Catalog of available vaccine types."""

    __tablename__ = "vaccine_types"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    target_species: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="dog",
    )  # dog, cat, other, all
    is_required: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Relationships
    schedules: Mapped[list["VaccinationSchedule"]] = relationship(
        "VaccinationSchedule",
        back_populates="vaccine_type",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    vaccinations: Mapped[list["Vaccination"]] = relationship(
        "Vaccination",
        back_populates="vaccine_type",
        lazy="select",
    )


class VaccinationSchedule(Base):
    """Species-specific vaccination schedule template.

    Defines when a vaccine should be given (e.g., first dose at 8 weeks,
    booster at 12 weeks, then annually).
    """

    __tablename__ = "vaccination_schedules"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vaccine_type_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vaccine_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    species: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    dose_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="1")
    age_weeks_min: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    age_weeks_max: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    interval_days: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )  # days after previous dose
    is_booster: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Relationships
    vaccine_type: Mapped["VaccineType"] = relationship("VaccineType", back_populates="schedules")


class Vaccination(Base):
    """An individual vaccination record for an animal."""

    __tablename__ = "vaccinations"

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
    vaccine_type_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vaccine_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vaccination_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="scheduled",
    )
    scheduled_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    administered_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    administered_by: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    dose_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="1")
    next_due_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
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
    animal: Mapped["Animal"] = relationship("Animal", back_populates="vaccinations")  # type: ignore[name-defined]  # noqa: F821
    vaccine_type: Mapped["VaccineType"] = relationship("VaccineType", back_populates="vaccinations")
