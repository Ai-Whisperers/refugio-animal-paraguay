"""Public animal browsing router.

Unauthenticated endpoints for browsing available animals. All queries
automatically filter to only return animals with status 'available'.

Endpoints:
  GET /public/animals              -- paginated list with filtering and search
  GET /public/animals/{animal_id}  -- single animal detail with photos
"""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import (
    Animal,
    AnimalGender,
    AnimalSize,
    AnimalSpecies,
    AnimalStatus,
)
from src.db.session import get_db
from src.schemas.public_animal import (
    PaginatedResponse,
    PublicAnimalDetail,
    PublicAnimalSummary,
)

router = APIRouter(prefix="/public/animals", tags=["public-animals"])

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100
_AVAILABLE_STATUS = AnimalStatus.AVAILABLE.value


@router.get(
    "",
    response_model=PaginatedResponse[PublicAnimalSummary],
    summary="Browse available animals",
    description="List available animals with optional filtering by species, gender, "
    "size, and name search. Returns paginated results. Only animals with "
    "status 'available' are included.",
)
async def list_public_animals(
    species: AnimalSpecies | None = Query(
        default=None, description="Filter by species"
    ),
    gender: AnimalGender | None = Query(
        default=None, description="Filter by gender"
    ),
    size: AnimalSize | None = Query(default=None, description="Filter by size"),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search by name (case-insensitive partial match)",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=_DEFAULT_PAGE_SIZE,
        ge=1,
        le=_MAX_PAGE_SIZE,
        description="Items per page (max 100)",
    ),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PublicAnimalSummary]:
    # Base query: only available animals
    base = select(Animal).where(Animal.status == _AVAILABLE_STATUS)

    # Apply filters at database level
    if species is not None:
        base = base.where(Animal.species == species.value)
    if gender is not None:
        base = base.where(Animal.gender == gender.value)
    if size is not None:
        base = base.where(Animal.size == size.value)
    if search is not None:
        base = base.where(Animal.name.ilike(f"%{search}%"))

    # Count total matching records
    count_stmt = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Calculate pagination
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    # Fetch page of results
    items_stmt = (
        base.order_by(Animal.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await db.execute(items_stmt)
    animals = list(result.scalars().all())

    return PaginatedResponse[PublicAnimalSummary](
        items=[PublicAnimalSummary.model_validate(a) for a in animals],
        total=total,
        page=page,
        size=page_size,
        pages=total_pages,
    )


@router.get(
    "/{animal_id}",
    response_model=PublicAnimalDetail,
    summary="Get animal detail",
    description="Returns complete information for a single available animal "
    "including all photos. Returns 404 if the animal does not exist "
    "or is not available for adoption.",
)
async def get_public_animal(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicAnimalDetail:
    animal = await db.get(Animal, animal_id)

    if animal is None or animal.status != _AVAILABLE_STATUS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found or not available for adoption",
        )

    return PublicAnimalDetail.model_validate(animal)
