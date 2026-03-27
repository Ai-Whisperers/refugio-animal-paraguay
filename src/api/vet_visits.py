"""Vet visits CRUD router.

Endpoints:
  GET    /animals/{animal_id}/vet-visits              -- paginated list for an animal
  GET    /animals/{animal_id}/vet-visits/{visit_id}   -- single visit or 404
  POST   /animals/{animal_id}/vet-visits              -- create, returns 201
  PATCH  /animals/{animal_id}/vet-visits/{visit_id}   -- partial update, returns 200
  DELETE /animals/{animal_id}/vet-visits/{visit_id}   -- hard delete, returns 204
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.animal import Animal
from src.db.models.medical import VetVisit
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.medical import (
    VetVisitCreate,
    VetVisitListResponse,
    VetVisitResponse,
    VetVisitUpdate,
)

router = APIRouter(
    prefix="/animals/{animal_id}/vet-visits",
    tags=["vet-visits"],
    responses=RESOURCE_RESPONSES,
)

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100


async def _get_animal_or_404(animal_id: UUID, db: AsyncSession) -> Animal:
    """Fetch an animal by ID or raise 404."""
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )
    return animal


async def _get_visit_or_404(
    visit_id: UUID, animal_id: UUID, db: AsyncSession
) -> VetVisit:
    """Fetch a vet visit by ID and animal, or raise 404."""
    visit = await db.get(VetVisit, visit_id)
    if visit is None or visit.animal_id != animal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vet visit not found",
        )
    return visit


@router.get("", response_model=VetVisitListResponse)
async def list_vet_visits(
    animal_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> dict:
    """List vet visits for an animal with pagination."""
    await _get_animal_or_404(animal_id, db)

    base_query = select(VetVisit).where(VetVisit.animal_id == animal_id)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    visits_query = (
        base_query.order_by(VetVisit.visit_date.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(visits_query)
    visits = list(result.scalars().all())

    return {
        "items": visits,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{visit_id}", response_model=VetVisitResponse)
async def get_vet_visit(
    animal_id: UUID,
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> VetVisit:
    """Get a single vet visit by ID."""
    await _get_animal_or_404(animal_id, db)
    return await _get_visit_or_404(visit_id, animal_id, db)


@router.post("", response_model=VetVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_visit(
    animal_id: UUID,
    payload: VetVisitCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> VetVisit:
    """Create a new vet visit for an animal."""
    await _get_animal_or_404(animal_id, db)

    visit_data = payload.model_dump(exclude_unset=True)
    visit = VetVisit(animal_id=animal_id, **visit_data)
    db.add(visit)
    await db.flush()
    await db.refresh(visit)
    return visit


@router.patch("/{visit_id}", response_model=VetVisitResponse)
async def update_vet_visit(
    animal_id: UUID,
    visit_id: UUID,
    payload: VetVisitUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> VetVisit:
    """Partially update a vet visit."""
    await _get_animal_or_404(animal_id, db)
    visit = await _get_visit_or_404(visit_id, animal_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(visit, field, value)

    await db.flush()
    await db.refresh(visit)
    return visit


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vet_visit(
    animal_id: UUID,
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete a vet visit and all associated records (cascade)."""
    await _get_animal_or_404(animal_id, db)
    visit = await _get_visit_or_404(visit_id, animal_id, db)
    await db.delete(visit)
    await db.flush()
