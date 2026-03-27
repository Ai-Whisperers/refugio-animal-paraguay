"""Medications CRUD router.

Endpoints:
  GET    /treatments/{treatment_id}/medications              -- list medications for a treatment
  GET    /medications/{medication_id}                         -- single medication
  POST   /treatments/{treatment_id}/medications              -- create, returns 201
  PATCH  /medications/{medication_id}                         -- partial update
  DELETE /medications/{medication_id}                         -- delete

  GET    /animals/{animal_id}/medications                    -- all active medications for an animal
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.animal import Animal
from src.db.models.medical import (
    Diagnosis,
    Medication,
    Treatment,
    VetVisit,
)
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.medical import (
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
)

router = APIRouter(tags=["medications"], responses=RESOURCE_RESPONSES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_treatment_or_404(treatment_id: UUID, db: AsyncSession) -> Treatment:
    """Fetch a treatment by ID or raise 404."""
    treatment = await db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found",
        )
    return treatment


async def _get_medication_or_404(medication_id: UUID, db: AsyncSession) -> Medication:
    """Fetch a medication by ID or raise 404."""
    medication = await db.get(Medication, medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )
    return medication


# ---------------------------------------------------------------------------
# Treatment-scoped endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/treatments/{treatment_id}/medications",
    response_model=list[MedicationResponse],
)
async def list_medications_for_treatment(
    treatment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Medication]:
    """List all medications for a treatment."""
    await _get_treatment_or_404(treatment_id, db)
    stmt = (
        select(Medication)
        .where(Medication.treatment_id == treatment_id)
        .order_by(Medication.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/treatments/{treatment_id}/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medication(
    treatment_id: UUID,
    payload: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Medication:
    """Create a medication linked to a treatment."""
    await _get_treatment_or_404(treatment_id, db)
    med_data = payload.model_dump(exclude_unset=True)
    medication = Medication(treatment_id=treatment_id, **med_data)
    db.add(medication)
    await db.flush()
    await db.refresh(medication)
    return medication


# ---------------------------------------------------------------------------
# Direct medication endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/medications/{medication_id}",
    response_model=MedicationResponse,
)
async def get_medication(
    medication_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Medication:
    """Get a single medication by ID."""
    return await _get_medication_or_404(medication_id, db)


@router.patch(
    "/medications/{medication_id}",
    response_model=MedicationResponse,
)
async def update_medication(
    medication_id: UUID,
    payload: MedicationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Medication:
    """Partially update a medication."""
    medication = await _get_medication_or_404(medication_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medication, field, value)
    await db.flush()
    await db.refresh(medication)
    return medication


@router.delete(
    "/medications/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_medication(
    medication_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete a medication."""
    medication = await _get_medication_or_404(medication_id, db)
    await db.delete(medication)
    await db.flush()


# ---------------------------------------------------------------------------
# Animal-level medication view
# ---------------------------------------------------------------------------


@router.get(
    "/animals/{animal_id}/medications",
    response_model=list[MedicationResponse],
)
async def list_active_medications_for_animal(
    animal_id: UUID,
    include_all: bool = Query(
        default=False,
        description="If true, return all medications. If false (default), only active ones.",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Medication]:
    """List medications for an animal, traversing vet_visits > diagnoses > treatments.

    By default returns only active medications. Set include_all=true for all statuses.
    """
    # Verify animal exists
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )

    stmt = (
        select(Medication)
        .join(Treatment, Medication.treatment_id == Treatment.id)
        .join(Diagnosis, Treatment.diagnosis_id == Diagnosis.id)
        .join(VetVisit, Diagnosis.vet_visit_id == VetVisit.id)
        .where(VetVisit.animal_id == animal_id)
    )

    if not include_all:
        stmt = stmt.where(Medication.medication_status == "active")

    stmt = stmt.order_by(Medication.start_date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
