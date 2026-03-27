"""Pydantic v2 schemas for vaccination management.

Covers: VaccineType, VaccinationSchedule, Vaccination.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# VaccineType schemas
# ---------------------------------------------------------------------------

class VaccineTypeCreate(BaseModel):
    """Create a new vaccine type in the catalog."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    manufacturer: str | None = Field(None, max_length=255)
    target_species: str = Field("dog", max_length=50)
    is_required: bool = False


class VaccineTypeUpdate(BaseModel):
    """Partial update for a vaccine type."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    manufacturer: str | None = Field(None, max_length=255)
    target_species: str | None = Field(None, max_length=50)
    is_required: bool | None = None


class VaccineTypeResponse(BaseModel):
    """Vaccine type read response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    manufacturer: str | None = None
    target_species: str
    is_required: bool
    created_at: datetime


class VaccineTypeListResponse(BaseModel):
    """Paginated list of vaccine types."""

    items: list[VaccineTypeResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# VaccinationSchedule schemas
# ---------------------------------------------------------------------------

class VaccinationScheduleCreate(BaseModel):
    """Create a vaccination schedule template."""

    vaccine_type_id: UUID
    species: str = Field(..., min_length=1, max_length=50)
    dose_number: int = Field(1, ge=1)
    age_weeks_min: int | None = Field(None, ge=0)
    age_weeks_max: int | None = Field(None, ge=0)
    interval_days: int | None = Field(None, ge=0)
    is_booster: bool = False
    notes: str | None = None


class VaccinationScheduleUpdate(BaseModel):
    """Partial update for a vaccination schedule."""

    species: str | None = Field(None, min_length=1, max_length=50)
    dose_number: int | None = Field(None, ge=1)
    age_weeks_min: int | None = Field(None, ge=0)
    age_weeks_max: int | None = Field(None, ge=0)
    interval_days: int | None = Field(None, ge=0)
    is_booster: bool | None = None
    notes: str | None = None


class VaccinationScheduleResponse(BaseModel):
    """Vaccination schedule read response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vaccine_type_id: UUID
    species: str
    dose_number: int
    age_weeks_min: int | None = None
    age_weeks_max: int | None = None
    interval_days: int | None = None
    is_booster: bool
    notes: str | None = None
    created_at: datetime


class VaccinationScheduleListResponse(BaseModel):
    """Paginated list of vaccination schedules."""

    items: list[VaccinationScheduleResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Vaccination schemas
# ---------------------------------------------------------------------------

class VaccinationCreate(BaseModel):
    """Create a vaccination record for an animal."""

    vaccine_type_id: UUID
    scheduled_date: date
    administered_date: date | None = None
    administered_by: str | None = Field(None, max_length=255)
    batch_number: str | None = Field(None, max_length=100)
    dose_number: int = Field(1, ge=1)
    next_due_date: date | None = None
    vaccination_status: str = Field("scheduled", max_length=50)
    notes: str | None = None


class VaccinationUpdate(BaseModel):
    """Partial update for a vaccination record."""

    vaccination_status: str | None = Field(None, max_length=50)
    scheduled_date: date | None = None
    administered_date: date | None = None
    administered_by: str | None = Field(None, max_length=255)
    batch_number: str | None = Field(None, max_length=100)
    dose_number: int | None = Field(None, ge=1)
    next_due_date: date | None = None
    notes: str | None = None


class VaccinationResponse(BaseModel):
    """Vaccination record read response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    vaccine_type_id: UUID
    vaccination_status: str
    scheduled_date: date
    administered_date: date | None = None
    administered_by: str | None = None
    batch_number: str | None = None
    dose_number: int
    next_due_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    vaccine_type: VaccineTypeResponse | None = None


class VaccinationListResponse(BaseModel):
    """Paginated list of vaccination records."""

    items: list[VaccinationResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Bulk vaccination schemas
# ---------------------------------------------------------------------------


class BulkVaccinationCreate(BaseModel):
    """Create the same vaccination record for multiple animals at once.

    Used during intake processing when a batch of animals all receive
    the same vaccine on the same day.
    """

    animal_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    vaccine_type_id: UUID
    scheduled_date: date
    administered_date: date | None = None
    administered_by: str | None = Field(None, max_length=255)
    batch_number: str | None = Field(None, max_length=100)
    vaccination_status: str = Field("scheduled", max_length=50)
    dose_number: int = Field(1, ge=1)
    next_due_date: date | None = None
    notes: str | None = None


class BulkVaccinationResultItem(BaseModel):
    """Result for a single animal in a bulk vaccination operation."""

    animal_id: UUID
    vaccination_id: UUID | None = None
    success: bool
    error: str | None = None


class BulkVaccinationResponse(BaseModel):
    """Summary of a bulk vaccination operation."""

    total_requested: int
    total_created: int
    total_failed: int
    results: list[BulkVaccinationResultItem]
