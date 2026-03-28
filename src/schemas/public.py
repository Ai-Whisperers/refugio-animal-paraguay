"""Pydantic schemas for public (unauthenticated) browsing endpoints.

These schemas are designed for the public portal where visitors browse
available animals. They include pagination metadata and simplified
response shapes optimized for the browsing experience.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.animal import AnimalGender, AnimalSize, AnimalSpecies


class PublicPhotoResponse(BaseModel):
    """Photo data exposed on public animal profiles."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    caption: str | None
    display_order: int


class PublicAnimalListItem(BaseModel):
    """Compact animal representation for listing/browsing results.

    Includes primary photo and key attributes for card-style display.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    breed: str | None
    size: AnimalSize | None
    gender: AnimalGender | None
    birth_date: date | None
    description: str | None
    primary_photo_url: str | None
    is_featured: bool
    created_at: datetime


class PublicAnimalDetail(BaseModel):
    """Full animal profile for the detail page.

    Includes all public-safe fields plus photo gallery.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: AnimalSpecies
    breed: str | None
    size: AnimalSize | None
    gender: AnimalGender | None
    birth_date: date | None
    description: str | None
    primary_photo_url: str | None
    is_featured: bool
    photos: list[PublicPhotoResponse]
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseModel):
    """Pagination metadata returned alongside list results."""

    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_items: int = Field(..., ge=0, description="Total matching records")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class PaginatedAnimalResponse(BaseModel):
    """Paginated response wrapper for the animal listing endpoint."""

    items: list[PublicAnimalListItem]
    pagination: PaginationMeta
