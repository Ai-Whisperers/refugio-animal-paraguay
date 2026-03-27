"""Adopters CRUD router.

Endpoints:
  GET    /adopters          — paginated list (soft-deleted excluded)
  GET    /adopters/{id}     — single adopter or 404
  POST   /adopters          — create, returns 201; 409 on duplicate email
  PATCH  /adopters/{id}     — partial update (name, phone, address, gdpr consent)
  DELETE /adopters/{id}     — soft delete (sets deleted_at), returns 204
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adopter import Adopter
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.adopter import AdopterCreate, AdopterResponse, AdopterUpdate

router = APIRouter(prefix="/adopters", tags=["adopters"])

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@router.get("", response_model=list[AdopterResponse])
async def list_adopters(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
) -> list[Adopter]:
    stmt = (
        select(Adopter)
        .where(Adopter.deleted_at.is_(None))
        .offset(offset)
        .limit(limit)
        .order_by(Adopter.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{adopter_id}", response_model=AdopterResponse)
async def get_adopter(
    adopter_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Adopter:
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None or adopter.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adopter not found")
    return adopter


@router.post("", response_model=AdopterResponse, status_code=status.HTTP_201_CREATED)
async def create_adopter(
    payload: AdopterCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Adopter:
    adopter = Adopter(
        full_name=payload.full_name,
        email=str(payload.email),
        phone=payload.phone,
        address=payload.address,
        gdpr_consent_at=payload.gdpr_consent_at,
    )
    db.add(adopter)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An adopter with this email already exists",
        ) from exc
    await db.refresh(adopter)
    return adopter


@router.patch("/{adopter_id}", response_model=AdopterResponse)
async def update_adopter(
    adopter_id: UUID,
    payload: AdopterUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Adopter:
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None or adopter.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adopter not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(adopter, field, value)

    adopter.updated_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(adopter)
    return adopter


@router.delete("/{adopter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_adopter(
    adopter_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Response:
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None or adopter.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adopter not found")

    # Soft delete — preserves GDPR audit trail and FK references
    adopter.deleted_at = datetime.now(UTC)
    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
