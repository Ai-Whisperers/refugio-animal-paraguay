"""Pydantic schemas for the Animal resource."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.animal import AnimalGender, AnimalSize, AnimalSpecies, AnimalStatus


class PhotoCreate(BaseModel):
    """Fields for adding a photo to an animal gallery."""

    url: str = Field(..., min_length=1)
    caption: str | None = None
    display_order: int = Field(default=0, ge=0)


class PhotoResponse(BaseModel):
    """Shape returned for each animal photo."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    url: str
    caption: str | None
    display_order: int
    created_at: datetime


class AnimalCreate(BaseModel):
    """Fields required (or optional) when creating a new animal."""

    name: str = Field(..., min_length=1, max_length=255)
    species: AnimalSpecies = AnimalSpecies.DOG
    status: AnimalStatus = AnimalStatus.INTAKE
    breed: str | None = Field(default=None, max_length=100)
    size: AnimalSize | None = None
    gender: AnimalGender | None = None
    birth_date: date | None = None
    description: str | None = None
    primary_photo_url: str | None = None


class AnimalUpdate(BaseModel):
    """All fields optional — only provided fields are written on PATCH."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    species: AnimalSpecies | None = None
    status: AnimalStatus | None = None
    breed: str | None = Field(default=None, max_length=100)
    size: AnimalSize | None = None
    gender: AnimalGender | None = None
    birth_date: date | None = None
    description: str | None = None
    primary_photo_url: str | None = None


class AnimalResponse(BaseModel):
    """Shape returned by every Animal endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    status: AnimalStatus
    breed: str | None
    size: AnimalSize | None
    gender: AnimalGender | None
    birth_date: date | None
    description: str | None
    primary_photo_url: str | None
    photos: list[PhotoResponse]
    created_at: datetime
    updated_at: datetime
