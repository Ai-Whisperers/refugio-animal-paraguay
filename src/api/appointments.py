"""Appointments router — cross-animal view of scheduled vet visits.

Endpoints:
  GET  /appointments  — paginated list of upcoming scheduled vet visits
  POST /appointments  — create a new scheduled vet visit (appointment)
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_medical_staff
from src.db.models.animal import Animal
from src.db.models.medical import VetVisit, VisitStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.appointments import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentRow,
)
from src.schemas.error import RESOURCE_RESPONSES

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
    responses=RESOURCE_RESPONSES,
)

_DEFAULT_PAGE_SIZE = 25
_MAX_PAGE_SIZE = 100


def _base_query(
    *,
    animal_id: UUID | None,
    include_past: bool,
):
    """Return a base SELECT joining vet_visits to animals for appointment rows."""
    now = datetime.now(UTC)

    q = (
        select(
            VetVisit.id,
            VetVisit.animal_id,
            VetVisit.veterinarian_name,
            VetVisit.visit_type,
            VetVisit.visit_status,
            VetVisit.visit_date,
            VetVisit.reason,
            VetVisit.notes,
            VetVisit.created_at,
            VetVisit.updated_at,
            Animal.name.label("animal_name"),
            Animal.species.label("animal_species"),
        )
        .join(Animal, VetVisit.animal_id == Animal.id)
        .where(VetVisit.visit_status == VisitStatus.SCHEDULED.value)
    )

    if not include_past:
        q = q.where(VetVisit.visit_date >= now)

    if animal_id is not None:
        q = q.where(Animal.id == animal_id)

    return q


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    animal_id: UUID | None = Query(default=None, description="Filter by animal"),
    include_past: bool = Query(default=False, description="Include past scheduled visits"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_medical_staff),
) -> dict:
    """List scheduled vet appointments across all animals."""
    base = _base_query(animal_id=animal_id, include_past=include_past)

    count_q = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * page_size
    rows = (
        await db.execute(base.order_by(VetVisit.visit_date.asc()).offset(offset).limit(page_size))
    ).all()

    items = [AppointmentRow.model_validate(dict(r._mapping)) for r in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=AppointmentRow, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_medical_staff),
) -> AppointmentRow:
    """Schedule a new vet appointment for an animal."""
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {payload.animal_id} not found",
        )

    visit = VetVisit(
        animal_id=payload.animal_id,
        veterinarian_name=payload.veterinarian_name,
        visit_type=payload.visit_type.value,
        visit_status=VisitStatus.SCHEDULED.value,
        visit_date=payload.visit_date,
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)

    return AppointmentRow(
        id=visit.id,
        animal_id=animal.id,
        animal_name=animal.name,
        animal_species=animal.species,
        veterinarian_name=visit.veterinarian_name,
        visit_type=visit.visit_type,
        visit_status=visit.visit_status,
        visit_date=visit.visit_date,
        reason=visit.reason,
        notes=visit.notes,
        created_at=visit.created_at,
        updated_at=visit.updated_at,
    )
