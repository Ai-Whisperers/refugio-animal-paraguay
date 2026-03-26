"""Pydantic schemas for public animal browsing endpoints.

These schemas are used by the unauthenticated public browsing API.
They return only available animals with safe-to-expose fields.
"""

from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.animal import AnimalGender, AnimalSize, AnimalSpecies

T = TypeVar("T")


class PublicPhotoResponse(BaseModel):
    """Photo data returned in public animal listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    caption: str | None
    display_order: int


class PublicAnimalSummary(BaseModel):
    """Compact animal data for listing pages."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    gender: AnimalGender | None
    size: AnimalSize | None
    birth_date: date | None
    description: str | None
    primary_photo_url: str | None
    created_at: datetime


class PublicAnimalDetail(BaseModel):
    """Full animal data for detail pages, including photos."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    gender: AnimalGender | None
    size: AnimalSize | None
    birth_date: date | None
    description: str | None
    primary_photo_url: str | None
    photos: list[PublicPhotoResponse]
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper with metadata."""

    items: list[T]
    total: int = Field(description="Total number of matching records")
    page: int = Field(description="Current page number (1-based)")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")
