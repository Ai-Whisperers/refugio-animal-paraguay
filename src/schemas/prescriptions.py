"""Pydantic schemas for the prescriptions cross-animal view."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.db.models.medical import MedicationFrequency, MedicationStatus


class PrescriptionRow(BaseModel):
    """Single medication row enriched with animal context."""

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

    # Animal context (joined)
    animal_id: UUID
    animal_name: str
    animal_species: str


class PrescriptionListResponse(BaseModel):
    """Paginated list of prescriptions."""

    items: list[PrescriptionRow]
    total: int
    page: int
    page_size: int
