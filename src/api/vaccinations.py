"""Vaccination management API endpoints.

Provides CRUD for vaccine types, vaccination schedules, and individual
vaccination records. Vaccine administration is recorded via POST/PATCH
on the vaccinations endpoints.

Routes:
    /vaccine-types                             — Vaccine type catalog CRUD
    /vaccine-types/{id}/schedules              — Schedule templates per vaccine type
    /animals/{animal_id}/vaccinations          — Animal vaccination records CRUD
    /vaccinations/{id}                         — Direct vaccination record access
"""

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import require_staff
from src.db.models.animal import Animal
from src.db.models.vaccination import (
    Vaccination,
    VaccinationSchedule,
    VaccineType,
)
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.vaccination import (
    BulkVaccinationCreate,
    BulkVaccinationResponse,
    VaccinationCreate,
    VaccinationListResponse,
    VaccinationResponse,
    VaccinationScheduleCreate,
    VaccinationScheduleListResponse,
    VaccinationScheduleResponse,
    VaccinationScheduleUpdate,
    VaccinationUpdate,
    VaccineTypeCreate,
    VaccineTypeListResponse,
    VaccineTypeResponse,
    VaccineTypeUpdate,
)
from src.services.vaccination_alert_service import VaccinationAlertSummary, get_vaccination_alerts
from src.services.vaccination_certificate_service import (
    CertificateData,
    VaccinationRecord,
    generate_vaccination_certificate,
)

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

vaccine_type_router = APIRouter(
    prefix="/vaccine-types",
    tags=["vaccine-types"],
    dependencies=[Depends(require_staff)],
)

vaccination_router = APIRouter(
    tags=["vaccinations"],
    dependencies=[Depends(require_staff)],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_animal_or_404(animal_id: UUID, db: AsyncSession) -> Animal:
    result = await db.execute(sa.select(Animal).where(Animal.id == animal_id))
    animal = result.scalar_one_or_none()
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found",
        )
    return animal


async def _get_vaccine_type_or_404(vaccine_type_id: UUID, db: AsyncSession) -> VaccineType:
    result = await db.execute(sa.select(VaccineType).where(VaccineType.id == vaccine_type_id))
    vt = result.scalar_one_or_none()
    if vt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vaccine type {vaccine_type_id} not found",
        )
    return vt


async def _get_vaccination_or_404(vaccination_id: UUID, db: AsyncSession) -> Vaccination:
    result = await db.execute(
        sa.select(Vaccination)
        .options(selectinload(Vaccination.vaccine_type))
        .where(Vaccination.id == vaccination_id)
    )
    vacc = result.scalar_one_or_none()
    if vacc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vaccination record {vaccination_id} not found",
        )
    return vacc


async def _get_schedule_or_404(schedule_id: UUID, db: AsyncSession) -> VaccinationSchedule:
    result = await db.execute(
        sa.select(VaccinationSchedule).where(VaccinationSchedule.id == schedule_id)
    )
    sched = result.scalar_one_or_none()
    if sched is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vaccination schedule {schedule_id} not found",
        )
    return sched


# ---------------------------------------------------------------------------
# Vaccine Type endpoints
# ---------------------------------------------------------------------------


@vaccine_type_router.get(
    "",
    response_model=VaccineTypeListResponse,
    summary="List vaccine types",
)
async def list_vaccine_types(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    species: str | None = Query(None, description="Filter by target species"),
) -> dict[str, Any]:
    query = sa.select(VaccineType)
    count_query = sa.select(sa.func.count()).select_from(VaccineType)

    if species:
        query = query.where(
            (VaccineType.target_species == species) | (VaccineType.target_species == "all")
        )
        count_query = count_query.where(
            (VaccineType.target_species == species) | (VaccineType.target_species == "all")
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(VaccineType.name.asc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "size": size}


@vaccine_type_router.get(
    "/{vaccine_type_id}",
    response_model=VaccineTypeResponse,
    responses=RESOURCE_RESPONSES,
    summary="Get vaccine type by ID",
)
async def get_vaccine_type(
    vaccine_type_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> VaccineType:
    return await _get_vaccine_type_or_404(vaccine_type_id, db)


@vaccine_type_router.post(
    "",
    response_model=VaccineTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a vaccine type",
)
async def create_vaccine_type(
    body: VaccineTypeCreate,
    db: AsyncSession = Depends(get_db),
) -> VaccineType:
    vt = VaccineType(**body.model_dump())
    db.add(vt)
    await db.commit()
    await db.refresh(vt)
    return vt


@vaccine_type_router.patch(
    "/{vaccine_type_id}",
    response_model=VaccineTypeResponse,
    responses=RESOURCE_RESPONSES,
    summary="Update a vaccine type",
)
async def update_vaccine_type(
    vaccine_type_id: UUID,
    body: VaccineTypeUpdate,
    db: AsyncSession = Depends(get_db),
) -> VaccineType:
    vt = await _get_vaccine_type_or_404(vaccine_type_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vt, field, value)
    await db.commit()
    await db.refresh(vt)
    return vt


@vaccine_type_router.delete(
    "/{vaccine_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RESOURCE_RESPONSES,
    summary="Delete a vaccine type",
)
async def delete_vaccine_type(
    vaccine_type_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    vt = await _get_vaccine_type_or_404(vaccine_type_id, db)
    await db.delete(vt)
    await db.commit()


# ---------------------------------------------------------------------------
# Vaccination Schedule endpoints
# ---------------------------------------------------------------------------


@vaccine_type_router.get(
    "/{vaccine_type_id}/schedules",
    response_model=VaccinationScheduleListResponse,
    responses=RESOURCE_RESPONSES,
    summary="List schedules for a vaccine type",
)
async def list_schedules(
    vaccine_type_id: UUID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    species: str | None = Query(None),
) -> dict[str, Any]:
    await _get_vaccine_type_or_404(vaccine_type_id, db)

    query = sa.select(VaccinationSchedule).where(
        VaccinationSchedule.vaccine_type_id == vaccine_type_id
    )
    count_query = (
        sa.select(sa.func.count())
        .select_from(VaccinationSchedule)
        .where(VaccinationSchedule.vaccine_type_id == vaccine_type_id)
    )

    if species:
        query = query.where(VaccinationSchedule.species == species)
        count_query = count_query.where(VaccinationSchedule.species == species)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        query.order_by(VaccinationSchedule.dose_number.asc()).offset((page - 1) * size).limit(size)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "size": size}


@vaccine_type_router.post(
    "/{vaccine_type_id}/schedules",
    response_model=VaccinationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_RESPONSES,
    summary="Create a vaccination schedule template",
)
async def create_schedule(
    vaccine_type_id: UUID,
    body: VaccinationScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> VaccinationSchedule:
    await _get_vaccine_type_or_404(vaccine_type_id, db)
    # Override vaccine_type_id from URL path
    data = body.model_dump()
    data["vaccine_type_id"] = vaccine_type_id
    schedule = VaccinationSchedule(**data)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@vaccination_router.get(
    "/vaccination-schedules/{schedule_id}",
    response_model=VaccinationScheduleResponse,
    responses=RESOURCE_RESPONSES,
    summary="Get a vaccination schedule by ID",
)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> VaccinationSchedule:
    return await _get_schedule_or_404(schedule_id, db)


@vaccination_router.patch(
    "/vaccination-schedules/{schedule_id}",
    response_model=VaccinationScheduleResponse,
    responses=RESOURCE_RESPONSES,
    summary="Update a vaccination schedule",
)
async def update_schedule(
    schedule_id: UUID,
    body: VaccinationScheduleUpdate,
    db: AsyncSession = Depends(get_db),
) -> VaccinationSchedule:
    schedule = await _get_schedule_or_404(schedule_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@vaccination_router.delete(
    "/vaccination-schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RESOURCE_RESPONSES,
    summary="Delete a vaccination schedule",
)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    schedule = await _get_schedule_or_404(schedule_id, db)
    await db.delete(schedule)
    await db.commit()


# ---------------------------------------------------------------------------
# Vaccination record endpoints (animal-scoped)
# ---------------------------------------------------------------------------


@vaccination_router.get(
    "/animals/{animal_id}/vaccinations",
    response_model=VaccinationListResponse,
    responses=RESOURCE_RESPONSES,
    summary="List vaccinations for an animal",
)
async def list_vaccinations(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    vaccination_status: str | None = Query(None, description="Filter by status"),
) -> dict[str, Any]:
    await _get_animal_or_404(animal_id, db)

    query = (
        sa.select(Vaccination)
        .options(selectinload(Vaccination.vaccine_type))
        .where(Vaccination.animal_id == animal_id)
    )
    count_query = (
        sa.select(sa.func.count())
        .select_from(Vaccination)
        .where(Vaccination.animal_id == animal_id)
    )

    if vaccination_status:
        query = query.where(Vaccination.vaccination_status == vaccination_status)
        count_query = count_query.where(Vaccination.vaccination_status == vaccination_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Vaccination.scheduled_date.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = list(result.scalars().unique().all())

    return {"items": items, "total": total, "page": page, "size": size}


@vaccination_router.post(
    "/animals/{animal_id}/vaccinations",
    response_model=VaccinationResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_RESPONSES,
    summary="Record a vaccination for an animal",
)
async def create_vaccination(
    animal_id: UUID,
    body: VaccinationCreate,
    db: AsyncSession = Depends(get_db),
) -> Vaccination:
    await _get_animal_or_404(animal_id, db)
    await _get_vaccine_type_or_404(body.vaccine_type_id, db)

    vacc = Vaccination(animal_id=animal_id, **body.model_dump())
    db.add(vacc)
    await db.commit()
    await db.refresh(vacc)
    # Reload with vaccine_type relationship
    return await _get_vaccination_or_404(vacc.id, db)


@vaccination_router.get(
    "/vaccinations/{vaccination_id}",
    response_model=VaccinationResponse,
    responses=RESOURCE_RESPONSES,
    summary="Get a vaccination record by ID",
)
async def get_vaccination(
    vaccination_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Vaccination:
    return await _get_vaccination_or_404(vaccination_id, db)


@vaccination_router.patch(
    "/vaccinations/{vaccination_id}",
    response_model=VaccinationResponse,
    responses=RESOURCE_RESPONSES,
    summary="Update a vaccination record (e.g. mark as administered)",
)
async def update_vaccination(
    vaccination_id: UUID,
    body: VaccinationUpdate,
    db: AsyncSession = Depends(get_db),
) -> Vaccination:
    vacc = await _get_vaccination_or_404(vaccination_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vacc, field, value)
    await db.commit()
    await db.refresh(vacc)
    return await _get_vaccination_or_404(vacc.id, db)


@vaccination_router.delete(
    "/vaccinations/{vaccination_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RESOURCE_RESPONSES,
    summary="Delete a vaccination record",
)
async def delete_vaccination(
    vaccination_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    vacc = await _get_vaccination_or_404(vaccination_id, db)
    await db.delete(vacc)
    await db.commit()


# ---------------------------------------------------------------------------
# Vaccination alert endpoints
# ---------------------------------------------------------------------------


@vaccination_router.get(
    "/vaccination-alerts",
    response_model=VaccinationAlertSummary,
    summary="Get vaccination due-date alerts",
)
async def list_vaccination_alerts(
    db: AsyncSession = Depends(get_db),
    window_days: int = Query(7, ge=1, le=90, description="Days ahead to check"),
) -> VaccinationAlertSummary:
    return await get_vaccination_alerts(db, window_days=window_days)


@vaccination_router.get(
    "/animals/{animal_id}/vaccination-alerts",
    response_model=VaccinationAlertSummary,
    responses=RESOURCE_RESPONSES,
    summary="Get vaccination alerts for a specific animal",
)
async def list_animal_vaccination_alerts(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    window_days: int = Query(7, ge=1, le=90),
) -> VaccinationAlertSummary:
    await _get_animal_or_404(animal_id, db)
    return await get_vaccination_alerts(db, window_days=window_days, animal_id=animal_id)


# ---------------------------------------------------------------------------
# Vaccination certificate endpoint
# ---------------------------------------------------------------------------


@vaccination_router.get(
    "/animals/{animal_id}/vaccination-certificate",
    responses={
        **RESOURCE_RESPONSES,
        200: {"content": {"application/pdf": {}}, "description": "PDF certificate"},
    },
    summary="Generate vaccination certificate PDF for an animal",
)
async def generate_certificate(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    from fastapi.responses import FileResponse

    animal = await _get_animal_or_404(animal_id, db)

    # Fetch administered vaccinations for this animal
    query = (
        sa.select(Vaccination)
        .options(selectinload(Vaccination.vaccine_type))
        .where(
            Vaccination.animal_id == animal_id,
            Vaccination.vaccination_status == "administered",
        )
        .order_by(Vaccination.administered_date.asc())
    )
    result = await db.execute(query)
    vaccinations = list(result.scalars().unique().all())

    records = [
        VaccinationRecord(
            vaccine_name=v.vaccine_type.name if v.vaccine_type else "Unknown",
            administered_date=v.administered_date or v.scheduled_date,
            batch_number=v.batch_number,
            administered_by=v.administered_by,
            dose_number=v.dose_number,
            next_due_date=v.next_due_date,
        )
        for v in vaccinations
    ]

    cert_data = CertificateData(
        animal_id=animal.id,
        animal_name=animal.name,
        animal_species=animal.species,
        animal_breed=animal.breed,
        animal_birth_date=animal.birth_date,
        vaccinations=records,
    )

    filepath = generate_vaccination_certificate(cert_data)
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=f"vaccination_certificate_{animal.name}.pdf",
    )


# ---------------------------------------------------------------------------
# Bulk vaccination endpoints
# ---------------------------------------------------------------------------


@vaccination_router.post(
    "/vaccinations/bulk",
    response_model=BulkVaccinationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record vaccinations for multiple animals at once (intake batch)",
)
async def create_bulk_vaccinations(
    body: BulkVaccinationCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Validate vaccine type exists
    await _get_vaccine_type_or_404(body.vaccine_type_id, db)

    results: list[dict[str, Any]] = []
    created_count = 0
    failed_count = 0

    for animal_id in body.animal_ids:
        try:
            # Validate animal exists
            animal_query = sa.select(Animal).where(Animal.id == animal_id)
            animal_result = await db.execute(animal_query)
            animal = animal_result.scalar_one_or_none()
            if animal is None:
                results.append(
                    {
                        "animal_id": animal_id,
                        "vaccination_id": None,
                        "success": False,
                        "error": f"Animal {animal_id} not found",
                    }
                )
                failed_count += 1
                continue

            vacc = Vaccination(
                animal_id=animal_id,
                vaccine_type_id=body.vaccine_type_id,
                scheduled_date=body.scheduled_date,
                administered_date=body.administered_date,
                administered_by=body.administered_by,
                batch_number=body.batch_number,
                vaccination_status=body.vaccination_status,
                dose_number=body.dose_number,
                next_due_date=body.next_due_date,
                notes=body.notes,
            )
            db.add(vacc)
            await db.flush()
            results.append(
                {
                    "animal_id": animal_id,
                    "vaccination_id": vacc.id,
                    "success": True,
                    "error": None,
                }
            )
            created_count += 1
        except Exception as exc:
            results.append(
                {
                    "animal_id": animal_id,
                    "vaccination_id": None,
                    "success": False,
                    "error": str(exc),
                }
            )
            failed_count += 1

    await db.commit()

    return {
        "total_requested": len(body.animal_ids),
        "total_created": created_count,
        "total_failed": failed_count,
        "results": results,
    }
