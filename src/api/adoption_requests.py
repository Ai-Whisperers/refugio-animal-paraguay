"""Adoption Requests workflow router.

Endpoints:
  GET    /adoption-requests              — paginated list (filter by status / animal / adopter)
  GET    /adoption-requests/{id}         — single request or 404
  POST   /adoption-requests              — create, returns 201
  PATCH  /adoption-requests/{id}/status  — transition status; approved sets animal → adopted
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.adoption_request import (
    AdoptionRequestCreate,
    AdoptionRequestResponse,
    AdoptionRequestStatusUpdate,
)

router = APIRouter(prefix="/adoption-requests", tags=["adoption-requests"])

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100

# ---------------------------------------------------------------------------
# Valid status transitions
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[AdoptionRequestStatus, set[AdoptionRequestStatus]] = {
    AdoptionRequestStatus.PENDING: {
        AdoptionRequestStatus.APPROVED,
        AdoptionRequestStatus.REJECTED,
        AdoptionRequestStatus.CANCELLED,
    },
    AdoptionRequestStatus.APPROVED: {AdoptionRequestStatus.CANCELLED},
    AdoptionRequestStatus.REJECTED: {AdoptionRequestStatus.CANCELLED},
    AdoptionRequestStatus.CANCELLED: set(),
}


@router.get("", response_model=list[AdoptionRequestResponse])
async def list_adoption_requests(
    status_filter: AdoptionRequestStatus | None = Query(default=None, alias="status"),
    animal_id: UUID | None = Query(default=None),
    adopter_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
) -> list[AdoptionRequest]:
    stmt = (
        select(AdoptionRequest)
        .offset(offset)
        .limit(limit)
        .order_by(AdoptionRequest.submitted_at.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(AdoptionRequest.status == status_filter.value)
    if animal_id is not None:
        stmt = stmt.where(AdoptionRequest.animal_id == animal_id)
    if adopter_id is not None:
        stmt = stmt.where(AdoptionRequest.adopter_id == adopter_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{request_id}", response_model=AdoptionRequestResponse)
async def get_adoption_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AdoptionRequest:
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )
    return req


@router.post(
    "", response_model=AdoptionRequestResponse, status_code=status.HTTP_201_CREATED
)
async def create_adoption_request(
    payload: AdoptionRequestCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> AdoptionRequest:
    # Validate animal exists
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )

    # Validate adopter exists and is not soft-deleted
    adopter = await db.get(Adopter, payload.adopter_id)
    if adopter is None or adopter.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adopter not found",
        )

    req = AdoptionRequest(
        animal_id=payload.animal_id,
        adopter_id=payload.adopter_id,
        status=AdoptionRequestStatus.PENDING.value,
        submitted_at=datetime.now(UTC),
        notes=payload.notes,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return req


@router.patch("/{request_id}/status", response_model=AdoptionRequestResponse)
async def update_adoption_request_status(
    request_id: UUID,
    payload: AdoptionRequestStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> AdoptionRequest:
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )

    current = AdoptionRequestStatus(req.status)
    new_status = payload.status

    if new_status not in _ALLOWED_TRANSITIONS[current]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Cannot transition adoption request from '{current.value}'"
                f" to '{new_status.value}'"
            ),
        )

    req.status = new_status.value
    req.decided_at = datetime.now(UTC)
    req.updated_at = datetime.now(UTC)

    # Side-effect: approved request marks animal as adopted
    if new_status == AdoptionRequestStatus.APPROVED:
        animal = await db.get(Animal, req.animal_id)
        if animal is not None:
            animal.status = "adopted"
            animal.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(req)
    return req
