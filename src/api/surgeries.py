"""Surgery and post-op monitoring API endpoints.

Provides CRUD for surgical procedure records and post-operative check-ins.

Routes:
    /surgeries                         -- All surgeries (schedule view)
    /animals/{animal_id}/surgeries     -- Surgery records for an animal
    /surgeries/{id}                    -- Direct surgery record access
    /surgeries/{id}/post-op-checks     -- Post-op monitoring checks
    /post-op-checks/{id}               -- Direct post-op check access
"""

from datetime import date
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal
from src.db.models.surgery import PostOpCheck, Surgery
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.surgery import (
    PostOpCheckCreate,
    PostOpCheckListResponse,
    PostOpCheckResponse,
    PostOpCheckUpdate,
    SurgeryCreate,
    SurgeryListResponse,
    SurgeryResponse,
    SurgeryScheduleListResponse,
    SurgeryUpdate,
    SurgeryWithAnimalResponse,
)

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100

surgery_router = APIRouter(
    tags=["surgeries"],
    dependencies=[],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_animal_or_404(animal_id: UUID, db: AsyncSession) -> Animal:
    result = await db.execute(sa.select(Animal).where(Animal.id == animal_id))
    animal = result.scalar_one_or_none()
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal


async def _get_surgery_or_404(surgery_id: UUID, db: AsyncSession) -> Surgery:
    result = await db.execute(sa.select(Surgery).where(Surgery.id == surgery_id))
    surgery = result.scalar_one_or_none()
    if surgery is None:
        raise HTTPException(status_code=404, detail="Surgery not found")
    return surgery


async def _get_post_op_check_or_404(check_id: UUID, db: AsyncSession) -> PostOpCheck:
    result = await db.execute(sa.select(PostOpCheck).where(PostOpCheck.id == check_id))
    check = result.scalar_one_or_none()
    if check is None:
        raise HTTPException(status_code=404, detail="Post-op check not found")
    return check


# ---------------------------------------------------------------------------
# Surgery schedule (all animals)
# ---------------------------------------------------------------------------


@surgery_router.get(
    "/surgeries",
    response_model=SurgeryScheduleListResponse,
    summary="List all surgeries across all animals (schedule view)",
)
async def list_all_surgeries(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    surgery_status: str | None = Query(None, description="Filter by status"),
    surgery_type: str | None = Query(None, description="Filter by type"),
    date_from: date | None = Query(None, description="Filter: scheduled_date >= date_from"),
    date_to: date | None = Query(None, description="Filter: scheduled_date <= date_to"),
) -> dict[str, Any]:
    """Return all surgeries with animal name for the scheduling calendar view."""
    base_where = []
    if surgery_status:
        base_where.append(Surgery.surgery_status == surgery_status)
    if surgery_type:
        base_where.append(Surgery.surgery_type == surgery_type)
    if date_from:
        base_where.append(Surgery.scheduled_date >= date_from)
    if date_to:
        base_where.append(Surgery.scheduled_date <= date_to)

    count_query = sa.select(sa.func.count()).select_from(Surgery)
    if base_where:
        count_query = count_query.where(*base_where)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        sa.select(Surgery, Animal.name.label("animal_name"))
        .join(Animal, Surgery.animal_id == Animal.id)
        .order_by(Surgery.scheduled_date.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    if base_where:
        query = query.where(*base_where)

    result = await db.execute(query)
    rows = result.all()

    items = [
        SurgeryWithAnimalResponse(
            **{c.key: getattr(row.Surgery, c.key) for c in Surgery.__table__.columns},
            animal_name=row.animal_name,
        )
        for row in rows
    ]
    return {"items": items, "total": total, "page": page, "size": size}


# ---------------------------------------------------------------------------
# Surgery CRUD
# ---------------------------------------------------------------------------


@surgery_router.get(
    "/animals/{animal_id}/surgeries",
    response_model=SurgeryListResponse,
    responses=RESOURCE_RESPONSES,
    summary="List surgeries for an animal",
)
async def list_surgeries(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    surgery_status: str | None = Query(None, description="Filter by status"),
    surgery_type: str | None = Query(None, description="Filter by type"),
) -> dict[str, Any]:
    await _get_animal_or_404(animal_id, db)

    query = sa.select(Surgery).where(Surgery.animal_id == animal_id)
    count_query = (
        sa.select(sa.func.count()).select_from(Surgery).where(Surgery.animal_id == animal_id)
    )

    if surgery_status:
        query = query.where(Surgery.surgery_status == surgery_status)
        count_query = count_query.where(Surgery.surgery_status == surgery_status)
    if surgery_type:
        query = query.where(Surgery.surgery_type == surgery_type)
        count_query = count_query.where(Surgery.surgery_type == surgery_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Surgery.scheduled_date.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "size": size}


@surgery_router.post(
    "/animals/{animal_id}/surgeries",
    response_model=SurgeryResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_RESPONSES,
    summary="Record a surgery for an animal",
)
async def create_surgery(
    animal_id: UUID,
    body: SurgeryCreate,
    db: AsyncSession = Depends(get_db),
) -> Surgery:
    await _get_animal_or_404(animal_id, db)

    surgery = Surgery(animal_id=animal_id, **body.model_dump())
    db.add(surgery)
    await db.commit()
    await db.refresh(surgery)
    return surgery


@surgery_router.get(
    "/surgeries/{surgery_id}",
    response_model=SurgeryResponse,
    responses=RESOURCE_RESPONSES,
    summary="Get a surgery record by ID",
)
async def get_surgery(
    surgery_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Surgery:
    return await _get_surgery_or_404(surgery_id, db)


@surgery_router.patch(
    "/surgeries/{surgery_id}",
    response_model=SurgeryResponse,
    responses=RESOURCE_RESPONSES,
    summary="Update a surgery record",
)
async def update_surgery(
    surgery_id: UUID,
    body: SurgeryUpdate,
    db: AsyncSession = Depends(get_db),
) -> Surgery:
    surgery = await _get_surgery_or_404(surgery_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(surgery, field, value)
    await db.commit()
    await db.refresh(surgery)
    return surgery


@surgery_router.delete(
    "/surgeries/{surgery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RESOURCE_RESPONSES,
    summary="Delete a surgery record",
)
async def delete_surgery(
    surgery_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    surgery = await _get_surgery_or_404(surgery_id, db)
    await db.delete(surgery)
    await db.commit()


# ---------------------------------------------------------------------------
# Post-op check CRUD
# ---------------------------------------------------------------------------


@surgery_router.get(
    "/surgeries/{surgery_id}/post-op-checks",
    response_model=PostOpCheckListResponse,
    responses=RESOURCE_RESPONSES,
    summary="List post-op checks for a surgery",
)
async def list_post_op_checks(
    surgery_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await _get_surgery_or_404(surgery_id, db)

    query = (
        sa.select(PostOpCheck)
        .where(PostOpCheck.surgery_id == surgery_id)
        .order_by(PostOpCheck.scheduled_time.asc())
    )
    result = await db.execute(query)
    items = list(result.scalars().all())
    return {"items": items, "total": len(items)}


@surgery_router.post(
    "/surgeries/{surgery_id}/post-op-checks",
    response_model=PostOpCheckResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_RESPONSES,
    summary="Add a post-op check for a surgery",
)
async def create_post_op_check(
    surgery_id: UUID,
    body: PostOpCheckCreate,
    db: AsyncSession = Depends(get_db),
) -> PostOpCheck:
    await _get_surgery_or_404(surgery_id, db)

    check = PostOpCheck(surgery_id=surgery_id, **body.model_dump())
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


@surgery_router.get(
    "/post-op-checks/{check_id}",
    response_model=PostOpCheckResponse,
    responses=RESOURCE_RESPONSES,
    summary="Get a post-op check by ID",
)
async def get_post_op_check(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PostOpCheck:
    return await _get_post_op_check_or_404(check_id, db)


@surgery_router.patch(
    "/post-op-checks/{check_id}",
    response_model=PostOpCheckResponse,
    responses=RESOURCE_RESPONSES,
    summary="Update a post-op check",
)
async def update_post_op_check(
    check_id: UUID,
    body: PostOpCheckUpdate,
    db: AsyncSession = Depends(get_db),
) -> PostOpCheck:
    check = await _get_post_op_check_or_404(check_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(check, field, value)
    await db.commit()
    await db.refresh(check)
    return check


@surgery_router.delete(
    "/post-op-checks/{check_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RESOURCE_RESPONSES,
    summary="Delete a post-op check",
)
async def delete_post_op_check(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    check = await _get_post_op_check_or_404(check_id, db)
    await db.delete(check)
    await db.commit()


# ---------------------------------------------------------------------------
# Post-op checklist generation
# ---------------------------------------------------------------------------


@surgery_router.post(
    "/surgeries/{surgery_id}/generate-checklist",
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_RESPONSES,
    summary="Generate post-op monitoring checklist for a surgery",
)
async def generate_checklist(
    surgery_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from src.services.post_op_checklist_service import generate_post_op_checklist

    await _get_surgery_or_404(surgery_id, db)
    result = await generate_post_op_checklist(surgery_id, db)
    return {
        "surgery_id": str(result.surgery_id),
        "checks_created": result.checks_created,
        "check_ids": [str(cid) for cid in result.check_ids],
    }
