"""Prescriptions router — cross-animal view of active medications.

Endpoints:
  GET /prescriptions  — paginated list of all medications with animal context
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_medical_staff
from src.db.models.animal import Animal
from src.db.models.medical import (
    Diagnosis,
    Medication,
    MedicationStatus,
    Treatment,
    VetVisit,
)
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.prescriptions import PrescriptionListResponse, PrescriptionRow

router = APIRouter(
    prefix="/prescriptions",
    tags=["prescriptions"],
    responses=RESOURCE_RESPONSES,
)

_DEFAULT_PAGE_SIZE = 25
_MAX_PAGE_SIZE = 100


def _base_query(
    *,
    animal_id: UUID | None,
    medication_status: MedicationStatus | None,
):
    """Return a base SELECT joining medications through to animals."""
    q = (
        select(
            Medication.id,
            Medication.name,
            Medication.dosage,
            Medication.frequency,
            Medication.route,
            Medication.start_date,
            Medication.end_date,
            Medication.medication_status,
            Medication.notes,
            Medication.created_at,
            Medication.updated_at,
            Medication.treatment_id,
            Animal.id.label("animal_id"),
            Animal.name.label("animal_name"),
            Animal.species.label("animal_species"),
        )
        .join(Treatment, Medication.treatment_id == Treatment.id)
        .join(Diagnosis, Treatment.diagnosis_id == Diagnosis.id)
        .join(VetVisit, Diagnosis.vet_visit_id == VetVisit.id)
        .join(Animal, VetVisit.animal_id == Animal.id)
    )
    if animal_id is not None:
        q = q.where(Animal.id == animal_id)
    if medication_status is not None:
        q = q.where(Medication.medication_status == medication_status.value)
    return q


@router.get("", response_model=PrescriptionListResponse)
async def list_prescriptions(
    animal_id: UUID | None = Query(default=None, description="Filter by animal"),
    medication_status: MedicationStatus | None = Query(
        default=None, alias="status", description="Filter by medication status"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_medical_staff),
) -> dict:
    """List all medications (prescriptions) across all animals with context."""
    base = _base_query(animal_id=animal_id, medication_status=medication_status)

    count_q = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * page_size
    rows = (
        await db.execute(base.order_by(Medication.created_at.desc()).offset(offset).limit(page_size))
    ).all()

    items = [PrescriptionRow.model_validate(dict(r._mapping)) for r in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
