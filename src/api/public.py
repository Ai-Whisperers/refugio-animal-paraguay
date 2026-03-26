"""Public (unauthenticated) animal browsing endpoints.

Endpoints:
  GET /public/animals             — paginated list with filters and search
  GET /public/animals/{animal_id} — full detail for a single available animal

All endpoints:
  - Require NO authentication
  - Only return animals with status='available'
  - Have NO rate limiting (high-traffic discovery use case)
  - Return consistent JSON with explicit nulls (never omitted fields)
"""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import (
    Animal,
    AnimalGender,
    AnimalSize,
    AnimalSpecies,
    AnimalStatus,
)
from src.db.session import get_db
from src.schemas.public import (
    PaginatedAnimalResponse,
    PaginationMeta,
    PublicAnimalDetail,
    PublicAnimalListItem,
)

router = APIRouter(prefix="/public/animals", tags=["public"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Only animals with this status are shown publicly
_PUBLIC_STATUS = AnimalStatus.AVAILABLE.value


@router.get("", response_model=PaginatedAnimalResponse)
async def list_available_animals(
    species: AnimalSpecies | None = Query(default=None, description="Filter by species"),
    breed: str | None = Query(default=None, max_length=100, description="Filter by breed (case-insensitive)"),
    size: AnimalSize | None = Query(default=None, description="Filter by size category"),
    gender: AnimalGender | None = Query(default=None, description="Filter by gender"),
    min_age_months: int | None = Query(default=None, ge=0, description="Minimum age in months"),
    max_age_months: int | None = Query(default=None, ge=0, description="Maximum age in months"),
    search: str | None = Query(default=None, max_length=255, description="Search by animal name (partial, case-insensitive)"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedAnimalResponse:
    """List available animals with filtering, search, and pagination.

    Only animals with status='available' are returned. Filtering operates
    at the database query level for efficiency. All filters can be combined.
    """
    # Base query: only available animals
    base_query = select(Animal).where(Animal.status == _PUBLIC_STATUS)

    # Apply filters at DB level
    if species is not None:
        base_query = base_query.where(Animal.species == species.value)
    if breed is not None:
        base_query = base_query.where(func.lower(Animal.breed) == func.lower(breed))
    if size is not None:
        base_query = base_query.where(Animal.size == size.value)
    if gender is not None:
        base_query = base_query.where(Animal.gender == gender.value)
    if min_age_months is not None:
        # Animal must be at least min_age_months old (born before cutoff date)
        base_query = base_query.where(
            Animal.birth_date <= func.current_date() - text("make_interval(months => :months)").bindparams(months=min_age_months)
        )
    if max_age_months is not None:
        # Animal must be at most max_age_months old (born after cutoff date)
        base_query = base_query.where(
            Animal.birth_date >= func.current_date() - text("make_interval(months => :months)").bindparams(months=max_age_months)
        )
    if search is not None and search.strip():
        base_query = base_query.where(Animal.name.ilike(f"%{search.strip()}%"))

    # Count total matching records
    count_query = select(func.count()).select_from(base_query.subquery())
    total_items_result = await db.execute(count_query)
    total_items = total_items_result.scalar_one()

    # Calculate pagination
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    offset = (page - 1) * page_size

    # Fetch paginated results
    data_query = base_query.order_by(Animal.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(data_query)
    animals = list(result.scalars().all())

    return PaginatedAnimalResponse(
        items=[PublicAnimalListItem.model_validate(a) for a in animals],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get("/{animal_id}", response_model=PublicAnimalDetail)
async def get_available_animal(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicAnimalDetail:
    """Get full detail for a single available animal.

    Returns 404 if the animal does not exist or is not in 'available' status.
    This prevents public access to animals in quarantine, under treatment, etc.
    """
    animal = await db.get(Animal, animal_id)

    if animal is None or animal.status != _PUBLIC_STATUS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )

    return PublicAnimalDetail.model_validate(animal)
