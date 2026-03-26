"""Pydantic schemas for the Animal resource."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.animal import AnimalSpecies, AnimalStatus


class AnimalCreate(BaseModel):
    """Fields required (or optional) when creating a new animal."""

    name: str = Field(..., min_length=1, max_length=255)
    species: AnimalSpecies = AnimalSpecies.DOG
    status: AnimalStatus = AnimalStatus.INTAKE
    birth_date: date | None = None
    description: str | None = None


class AnimalUpdate(BaseModel):
    """All fields optional — only provided fields are written on PATCH."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    species: AnimalSpecies | None = None
    status: AnimalStatus | None = None
    birth_date: date | None = None
    description: str | None = None


class AnimalResponse(BaseModel):
    """Shape returned by every Animal endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    status: AnimalStatus
    birth_date: date | None
    description: str | None
    created_at: datetime
    updated_at: datetime
