"""Pydantic v2 schemas for surgery and post-op monitoring.

Covers: Surgery, PostOpCheck.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Surgery schemas
# ---------------------------------------------------------------------------


class SurgeryCreate(BaseModel):
    """Create a new surgery record."""

    surgery_type: str = Field("other", max_length=50)
    surgery_status: str = Field("scheduled", max_length=50)
    veterinarian_name: str = Field(..., min_length=1, max_length=255)
    scheduled_date: date
    performed_date: date | None = None
    anesthesia_type: str | None = Field(None, max_length=50)
    anesthesia_notes: str | None = None
    procedure_description: str | None = None
    outcome: str | None = Field(None, max_length=50)
    outcome_notes: str | None = None
    complications: str | None = None
    weight_kg: float | None = Field(None, ge=0, le=9999.99)
    recovery_notes: str | None = None
    follow_up_date: date | None = None


class SurgeryUpdate(BaseModel):
    """Partial update for a surgery record."""

    surgery_type: str | None = Field(None, max_length=50)
    surgery_status: str | None = Field(None, max_length=50)
    veterinarian_name: str | None = Field(None, min_length=1, max_length=255)
    scheduled_date: date | None = None
    performed_date: date | None = None
    anesthesia_type: str | None = Field(None, max_length=50)
    anesthesia_notes: str | None = None
    procedure_description: str | None = None
    outcome: str | None = Field(None, max_length=50)
    outcome_notes: str | None = None
    complications: str | None = None
    weight_kg: float | None = Field(None, ge=0, le=9999.99)
    recovery_notes: str | None = None
    follow_up_date: date | None = None


class SurgeryResponse(BaseModel):
    """Surgery record read response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    surgery_type: str
    surgery_status: str
    veterinarian_name: str
    scheduled_date: date
    performed_date: date | None = None
    anesthesia_type: str | None = None
    anesthesia_notes: str | None = None
    procedure_description: str | None = None
    outcome: str | None = None
    outcome_notes: str | None = None
    complications: str | None = None
    weight_kg: float | None = None
    recovery_notes: str | None = None
    follow_up_date: date | None = None
    created_at: datetime
    updated_at: datetime


class SurgeryListResponse(BaseModel):
    """Paginated list of surgery records."""

    items: list[SurgeryResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# PostOpCheck schemas
# ---------------------------------------------------------------------------


class PostOpCheckCreate(BaseModel):
    """Create a post-op monitoring check record."""

    scheduled_time: datetime
    check_status: str = Field("pending", max_length=50)
    completed_time: datetime | None = None
    checked_by: str | None = Field(None, max_length=255)
    temperature_celsius: float | None = Field(None, ge=30.0, le=45.0)
    pain_level: int | None = Field(None, ge=0, le=10)
    appetite: str | None = Field(None, max_length=50)
    mobility: str | None = Field(None, max_length=50)
    wound_condition: str | None = Field(None, max_length=100)
    notes: str | None = None
    concerns: str | None = None


class PostOpCheckUpdate(BaseModel):
    """Partial update for a post-op check."""

    check_status: str | None = Field(None, max_length=50)
    completed_time: datetime | None = None
    checked_by: str | None = Field(None, max_length=255)
    temperature_celsius: float | None = Field(None, ge=30.0, le=45.0)
    pain_level: int | None = Field(None, ge=0, le=10)
    appetite: str | None = Field(None, max_length=50)
    mobility: str | None = Field(None, max_length=50)
    wound_condition: str | None = Field(None, max_length=100)
    notes: str | None = None
    concerns: str | None = None


class PostOpCheckResponse(BaseModel):
    """Post-op check read response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    surgery_id: UUID
    check_status: str
    scheduled_time: datetime
    completed_time: datetime | None = None
    checked_by: str | None = None
    temperature_celsius: float | None = None
    pain_level: int | None = None
    appetite: str | None = None
    mobility: str | None = None
    wound_condition: str | None = None
    notes: str | None = None
    concerns: str | None = None
    created_at: datetime


class PostOpCheckListResponse(BaseModel):
    """List of post-op check records."""

    items: list[PostOpCheckResponse]
    total: int
