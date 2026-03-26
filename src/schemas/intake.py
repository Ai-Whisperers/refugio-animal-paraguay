"""Pydantic schemas for the Animal Intake Workflow."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.animal import AnimalSpecies
from src.db.models.intake import IntakeSource


class IntakeCreate(BaseModel):
    """Fields required when processing a new animal intake.

    Creates both an Animal record and an IntakeRecord in a single request.
    """

    # Animal fields
    name: str = Field(..., min_length=1, max_length=255, description="Animal name")
    species: AnimalSpecies = Field(
        default=AnimalSpecies.DOG, description="Animal species"
    )
    birth_date: str | None = Field(
        default=None, description="Animal birth date (YYYY-MM-DD)"
    )
    description: str | None = Field(
        default=None, description="Animal description"
    )

    # Intake fields
    source: IntakeSource = Field(..., description="How the animal arrived")
    finder_name: str | None = Field(
        default=None, max_length=255, description="Name of the person who found/brought the animal"
    )
    finder_email: EmailStr | None = Field(
        default=None, description="Finder's email address"
    )
    finder_phone: str | None = Field(
        default=None, max_length=50, description="Finder's phone number"
    )
    location_found: str | None = Field(
        default=None, description="Location where the animal was found"
    )
    condition_on_arrival: str | None = Field(
        default=None, description="Free-form description of animal's condition"
    )
    requires_quarantine: bool = Field(
        default=False, description="Whether the animal requires quarantine"
    )
    notes: str | None = Field(
        default=None, description="Additional intake notes"
    )
    photo_urls: list[str] = Field(
        default_factory=list,
        description="URLs of intake photos to link to the animal",
    )


class IntakeAnimalResponse(BaseModel):
    """Minimal animal info embedded in intake responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: str
    status: str
    created_at: datetime


class IntakeStaffResponse(BaseModel):
    """Minimal staff info embedded in intake responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class IntakeResponse(BaseModel):
    """Shape returned for an intake record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    source: IntakeSource
    finder_name: str | None
    finder_email: str | None
    finder_phone: str | None
    location_found: str | None
    condition_on_arrival: str | None
    requires_quarantine: bool
    intake_date: datetime
    staff_id: UUID
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Nested relations
    animal: IntakeAnimalResponse
    staff: IntakeStaffResponse
