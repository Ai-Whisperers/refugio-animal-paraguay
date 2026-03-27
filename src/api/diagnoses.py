"""Diagnoses and Treatments CRUD router.

Endpoints — Diagnoses:
  GET    /vet-visits/{visit_id}/diagnoses              -- list diagnoses for a visit
  POST   /vet-visits/{visit_id}/diagnoses              -- create diagnosis, returns 201
  PATCH  /diagnoses/{diagnosis_id}                     -- update diagnosis
  DELETE /diagnoses/{diagnosis_id}                     -- delete diagnosis (cascade)

Endpoints — Treatments:
  GET    /diagnoses/{diagnosis_id}/treatments          -- list treatments for a diagnosis
  POST   /diagnoses/{diagnosis_id}/treatments          -- create treatment, returns 201
  PATCH  /treatments/{treatment_id}                    -- update treatment
  DELETE /treatments/{treatment_id}                    -- delete treatment (cascade)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.medical import Diagnosis, Treatment, VetVisit
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.medical import (
    DiagnosisCreate,
    DiagnosisResponse,
    DiagnosisUpdate,
    TreatmentCreate,
    TreatmentResponse,
    TreatmentUpdate,
)

# Two separate routers: one for diagnosis endpoints, one for treatment endpoints
diagnosis_router = APIRouter(tags=["diagnoses"], responses=RESOURCE_RESPONSES)
treatment_router = APIRouter(tags=["treatments"], responses=RESOURCE_RESPONSES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_visit_or_404(visit_id: UUID, db: AsyncSession) -> VetVisit:
    """Fetch a vet visit by ID or raise 404."""
    visit = await db.get(VetVisit, visit_id)
    if visit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vet visit not found",
        )
    return visit


async def _get_diagnosis_or_404(diagnosis_id: UUID, db: AsyncSession) -> Diagnosis:
    """Fetch a diagnosis by ID or raise 404."""
    diagnosis = await db.get(Diagnosis, diagnosis_id)
    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found",
        )
    return diagnosis


async def _get_treatment_or_404(treatment_id: UUID, db: AsyncSession) -> Treatment:
    """Fetch a treatment by ID or raise 404."""
    treatment = await db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found",
        )
    return treatment


# ---------------------------------------------------------------------------
# Diagnosis endpoints
# ---------------------------------------------------------------------------


@diagnosis_router.get(
    "/vet-visits/{visit_id}/diagnoses",
    response_model=list[DiagnosisResponse],
)
async def list_diagnoses(
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Diagnosis]:
    """List all diagnoses for a vet visit."""
    await _get_visit_or_404(visit_id, db)
    stmt = (
        select(Diagnosis)
        .where(Diagnosis.vet_visit_id == visit_id)
        .order_by(Diagnosis.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@diagnosis_router.post(
    "/vet-visits/{visit_id}/diagnoses",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_diagnosis(
    visit_id: UUID,
    payload: DiagnosisCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Diagnosis:
    """Create a diagnosis linked to a vet visit."""
    await _get_visit_or_404(visit_id, db)
    diagnosis_data = payload.model_dump(exclude_unset=True)
    diagnosis = Diagnosis(vet_visit_id=visit_id, **diagnosis_data)
    db.add(diagnosis)
    await db.flush()
    await db.refresh(diagnosis)
    return diagnosis


@diagnosis_router.patch(
    "/diagnoses/{diagnosis_id}",
    response_model=DiagnosisResponse,
)
async def update_diagnosis(
    diagnosis_id: UUID,
    payload: DiagnosisUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Diagnosis:
    """Partially update a diagnosis."""
    diagnosis = await _get_diagnosis_or_404(diagnosis_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(diagnosis, field, value)
    await db.flush()
    await db.refresh(diagnosis)
    return diagnosis


@diagnosis_router.delete(
    "/diagnoses/{diagnosis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_diagnosis(
    diagnosis_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete a diagnosis and all its treatments/medications (cascade)."""
    diagnosis = await _get_diagnosis_or_404(diagnosis_id, db)
    await db.delete(diagnosis)
    await db.flush()


# ---------------------------------------------------------------------------
# Treatment endpoints
# ---------------------------------------------------------------------------


@treatment_router.get(
    "/diagnoses/{diagnosis_id}/treatments",
    response_model=list[TreatmentResponse],
)
async def list_treatments(
    diagnosis_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Treatment]:
    """List all treatments for a diagnosis."""
    await _get_diagnosis_or_404(diagnosis_id, db)
    stmt = (
        select(Treatment)
        .where(Treatment.diagnosis_id == diagnosis_id)
        .order_by(Treatment.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@treatment_router.post(
    "/diagnoses/{diagnosis_id}/treatments",
    response_model=TreatmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_treatment(
    diagnosis_id: UUID,
    payload: TreatmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Treatment:
    """Create a treatment linked to a diagnosis."""
    await _get_diagnosis_or_404(diagnosis_id, db)
    treatment_data = payload.model_dump(exclude_unset=True)
    treatment = Treatment(diagnosis_id=diagnosis_id, **treatment_data)
    db.add(treatment)
    await db.flush()
    await db.refresh(treatment)
    return treatment


@treatment_router.patch(
    "/treatments/{treatment_id}",
    response_model=TreatmentResponse,
)
async def update_treatment(
    treatment_id: UUID,
    payload: TreatmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Treatment:
    """Partially update a treatment."""
    treatment = await _get_treatment_or_404(treatment_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(treatment, field, value)
    await db.flush()
    await db.refresh(treatment)
    return treatment


@treatment_router.delete(
    "/treatments/{treatment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_treatment(
    treatment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete a treatment and all its medications (cascade)."""
    treatment = await _get_treatment_or_404(treatment_id, db)
    await db.delete(treatment)
    await db.flush()
