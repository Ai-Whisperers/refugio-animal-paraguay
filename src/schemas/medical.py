"""Pydantic schemas for veterinary medical records."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.medical import (
    DiagnosisSeverity,
    DocumentType,
    MedicationFrequency,
    MedicationStatus,
    TreatmentStatus,
    VisitStatus,
    VisitType,
)


# --- Medication schemas ---


class MedicationCreate(BaseModel):
    """Fields for creating a medication record."""

    name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: MedicationFrequency = MedicationFrequency.DAILY
    route: str | None = Field(default=None, max_length=50)
    start_date: date
    end_date: date | None = None
    medication_status: MedicationStatus = MedicationStatus.ACTIVE
    notes: str | None = None


class MedicationUpdate(BaseModel):
    """Fields for updating a medication record."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    dosage: str | None = Field(default=None, min_length=1, max_length=100)
    frequency: MedicationFrequency | None = None
    route: str | None = Field(default=None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    medication_status: MedicationStatus | None = None
    notes: str | None = None


class MedicationResponse(BaseModel):
    """Shape returned for a medication record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    treatment_id: UUID
    name: str
    dosage: str
    frequency: MedicationFrequency
    route: str | None
    start_date: date
    end_date: date | None
    medication_status: MedicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


# --- Treatment schemas ---


class TreatmentCreate(BaseModel):
    """Fields for creating a treatment record."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    treatment_status: TreatmentStatus = TreatmentStatus.PLANNED
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class TreatmentUpdate(BaseModel):
    """Fields for updating a treatment record."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    treatment_status: TreatmentStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class TreatmentResponse(BaseModel):
    """Shape returned for a treatment record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    diagnosis_id: UUID
    name: str
    description: str | None
    treatment_status: TreatmentStatus
    start_date: date | None
    end_date: date | None
    notes: str | None
    medications: list[MedicationResponse]
    created_at: datetime
    updated_at: datetime


# --- Diagnosis schemas ---


class DiagnosisCreate(BaseModel):
    """Fields for creating a diagnosis record."""

    condition: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    severity: DiagnosisSeverity = DiagnosisSeverity.MODERATE
    is_chronic: bool = False


class DiagnosisUpdate(BaseModel):
    """Fields for updating a diagnosis record."""

    condition: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: DiagnosisSeverity | None = None
    is_chronic: bool | None = None


class DiagnosisResponse(BaseModel):
    """Shape returned for a diagnosis record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vet_visit_id: UUID
    condition: str
    description: str | None
    severity: DiagnosisSeverity
    is_chronic: bool
    treatments: list[TreatmentResponse]
    created_at: datetime


# --- Medical Document schemas ---


class MedicalDocumentCreate(BaseModel):
    """Fields for creating a medical document record."""

    document_type: DocumentType = DocumentType.OTHER
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    file_url: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=100)


class MedicalDocumentResponse(BaseModel):
    """Shape returned for a medical document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vet_visit_id: UUID
    document_type: DocumentType
    title: str
    description: str | None
    file_url: str
    file_name: str
    file_size_bytes: int | None
    mime_type: str | None
    created_at: datetime


# --- Vet Visit schemas ---


class VetVisitCreate(BaseModel):
    """Fields for creating a vet visit record."""

    veterinarian_name: str = Field(..., min_length=1, max_length=255)
    visit_type: VisitType = VisitType.CHECKUP
    visit_status: VisitStatus = VisitStatus.SCHEDULED
    visit_date: datetime | None = None
    reason: str | None = None
    notes: str | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=9999.99)
    temperature_celsius: float | None = Field(default=None, ge=30.0, le=45.0)
    next_visit_date: date | None = None


class VetVisitUpdate(BaseModel):
    """Fields for updating a vet visit record."""

    veterinarian_name: str | None = Field(default=None, min_length=1, max_length=255)
    visit_type: VisitType | None = None
    visit_status: VisitStatus | None = None
    visit_date: datetime | None = None
    reason: str | None = None
    notes: str | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=9999.99)
    temperature_celsius: float | None = Field(default=None, ge=30.0, le=45.0)
    next_visit_date: date | None = None


class VetVisitResponse(BaseModel):
    """Shape returned for a vet visit record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    veterinarian_name: str
    visit_type: VisitType
    visit_status: VisitStatus
    visit_date: datetime
    reason: str | None
    notes: str | None
    weight_kg: float | None
    temperature_celsius: float | None
    next_visit_date: date | None
    diagnoses: list[DiagnosisResponse]
    medical_documents: list[MedicalDocumentResponse]
    created_at: datetime
    updated_at: datetime


class VetVisitListResponse(BaseModel):
    """Paginated vet visit list."""

    model_config = ConfigDict(from_attributes=True)

    items: list[VetVisitResponse]
    total: int
    page: int
    page_size: int
