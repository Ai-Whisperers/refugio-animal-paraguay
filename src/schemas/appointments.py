"""Pydantic schemas for the appointments cross-animal view."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.medical import VisitStatus, VisitType


class AppointmentCreate(BaseModel):
    """Fields for scheduling a new vet appointment."""

    animal_id: UUID
    veterinarian_name: str = Field(..., min_length=1, max_length=255)
    visit_type: VisitType = VisitType.CHECKUP
    visit_date: datetime
    reason: str | None = None
    notes: str | None = None


class AppointmentRow(BaseModel):
    """Single scheduled vet visit enriched with animal context."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    animal_name: str
    animal_species: str
    veterinarian_name: str
    visit_type: VisitType
    visit_status: VisitStatus
    visit_date: datetime
    reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AppointmentListResponse(BaseModel):
    """Paginated list of appointments."""

    items: list[AppointmentRow]
    total: int
    page: int
    page_size: int
