"""SQLAlchemy ORM models for veterinary medical records.

Tables:
  vet_visits      — Individual vet visit records linked to an animal
  diagnoses       — Diagnoses recorded during a vet visit
  treatments      — Treatment plans linked to a diagnosis
  medications     — Medications prescribed with dosage and schedule
  medical_documents — Uploaded documents (lab results, X-rays) linked to a visit
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class VisitType(StrEnum):
    """Type of veterinary visit."""

    CHECKUP = "checkup"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    VACCINATION = "vaccination"
    FOLLOW_UP = "follow_up"
    DENTAL = "dental"
    OTHER = "other"


class VisitStatus(StrEnum):
    """Status of a vet visit."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosisSeverity(StrEnum):
    """Severity level for a diagnosis."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class TreatmentStatus(StrEnum):
    """Status of a treatment plan."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"


class MedicationFrequency(StrEnum):
    """How often a medication is administered."""

    ONCE = "once"
    DAILY = "daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"


class MedicationStatus(StrEnum):
    """Status of a medication prescription."""

    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"


class DocumentType(StrEnum):
    """Type of medical document."""

    LAB_RESULT = "lab_result"
    XRAY = "xray"
    ULTRASOUND = "ultrasound"
    PRESCRIPTION = "prescription"
    CERTIFICATE = "certificate"
    OTHER = "other"


class VetVisit(Base):
    """A veterinary visit record for an animal."""

    __tablename__ = "vet_visits"

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
    veterinarian_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    visit_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="checkup",
    )
    visit_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="scheduled",
    )
    visit_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(
        sa.Numeric(4, 1), nullable=True
    )
    next_visit_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
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
    animal: Mapped["Animal"] = relationship("Animal", back_populates="vet_visits")  # type: ignore[name-defined]  # noqa: F821
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        "Diagnosis",
        back_populates="vet_visit",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Diagnosis.created_at.desc()",
    )
    medical_documents: Mapped[list["MedicalDocument"]] = relationship(
        "MedicalDocument",
        back_populates="vet_visit",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="MedicalDocument.created_at.desc()",
    )


class Diagnosis(Base):
    """A diagnosis recorded during a vet visit."""

    __tablename__ = "diagnoses"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vet_visit_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="moderate",
    )
    is_chronic: Mapped[bool] = mapped_column(
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
    vet_visit: Mapped["VetVisit"] = relationship(
        "VetVisit", back_populates="diagnoses"
    )
    treatments: Mapped[list["Treatment"]] = relationship(
        "Treatment",
        back_populates="diagnosis",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Treatment.created_at.desc()",
    )


class Treatment(Base):
    """A treatment plan linked to a diagnosis."""

    __tablename__ = "treatments"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    diagnosis_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("diagnoses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    treatment_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="planned",
    )
    start_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
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
    diagnosis: Mapped["Diagnosis"] = relationship(
        "Diagnosis", back_populates="treatments"
    )
    medications: Mapped[list["Medication"]] = relationship(
        "Medication",
        back_populates="treatment",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Medication.created_at.desc()",
    )


class Medication(Base):
    """A medication prescribed as part of a treatment."""

    __tablename__ = "medications"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    treatment_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("treatments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="daily",
    )
    route: Mapped[str | None] = mapped_column(
        sa.String(50), nullable=True
    )  # oral, injection, topical, etc.
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    medication_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="active",
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
    treatment: Mapped["Treatment"] = relationship(
        "Treatment", back_populates="medications"
    )


class MedicalDocument(Base):
    """A medical document (lab result, X-ray, etc.) linked to a vet visit."""

    __tablename__ = "medical_documents"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vet_visit_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="other",
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    file_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    file_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Relationships
    vet_visit: Mapped["VetVisit"] = relationship(
        "VetVisit", back_populates="medical_documents"
    )
