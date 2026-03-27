"""Vet Referrals router: CRUD for external veterinary referrals.

Endpoints:
  GET    /vet-referrals              - paginated list (filter by animal, status, urgency)
  GET    /vet-referrals/{id}         - single referral or 404
  POST   /vet-referrals              - create referral, returns 201
  PATCH  /vet-referrals/{id}         - update referral
  DELETE /vet-referrals/{id}         - soft-delete (cancel) referral
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_medical_staff
from src.db.models.animal import Animal
from src.db.models.user import User
from src.db.models.vet_referral import ReferralStatus, ReferralUrgency, VetReferral
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.vet_referral import (
    VetReferralCreate,
    VetReferralListResponse,
    VetReferralResponse,
    VetReferralUpdate,
)

referral_router = APIRouter(
    prefix="/vet-referrals",
    tags=["vet-referrals"],
    responses=RESOURCE_RESPONSES,
)

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


async def _get_animal_or_404(animal_id: UUID, db: AsyncSession) -> Animal:
    """Fetch animal by ID or raise 404."""
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found",
        )
    return animal


async def _get_referral_or_404(referral_id: UUID, db: AsyncSession) -> VetReferral:
    """Fetch referral by ID or raise 404."""
    referral = await db.get(VetReferral, referral_id)
    if referral is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral {referral_id} not found",
        )
    return referral


@referral_router.get("", response_model=VetReferralListResponse)
async def list_referrals(
    animal_id: UUID | None = Query(default=None),
    status_filter: ReferralStatus | None = Query(default=None, alias="status"),
    urgency: ReferralUrgency | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_medical_staff),
) -> dict:
    """List vet referrals with optional filters."""
    base = select(VetReferral)
    count_q = select(func.count(VetReferral.id))

    if animal_id is not None:
        base = base.where(VetReferral.animal_id == animal_id)
        count_q = count_q.where(VetReferral.animal_id == animal_id)
    if status_filter is not None:
        base = base.where(VetReferral.status == status_filter.value)
        count_q = count_q.where(VetReferral.status == status_filter.value)
    if urgency is not None:
        base = base.where(VetReferral.urgency == urgency.value)
        count_q = count_q.where(VetReferral.urgency == urgency.value)

    total = (await db.execute(count_q)).scalar() or 0
    stmt = base.order_by(VetReferral.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return {"items": list(rows), "total": total, "offset": offset, "limit": limit}


@referral_router.get("/{referral_id}", response_model=VetReferralResponse)
async def get_referral(
    referral_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_medical_staff),
) -> VetReferral:
    """Get a single vet referral by ID."""
    return await _get_referral_or_404(referral_id, db)


@referral_router.post("", response_model=VetReferralResponse, status_code=status.HTTP_201_CREATED)
async def create_referral(
    body: VetReferralCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_medical_staff),
) -> VetReferral:
    """Create a new external vet referral."""
    await _get_animal_or_404(body.animal_id, db)

    referral = VetReferral(
        animal_id=body.animal_id,
        referred_by_id=user.id,
        external_vet_name=body.external_vet_name,
        external_vet_clinic=body.external_vet_clinic,
        external_vet_phone=body.external_vet_phone,
        external_vet_email=body.external_vet_email,
        reason=body.reason,
        specialty=body.specialty,
        urgency=body.urgency.value,
        appointment_date=body.appointment_date,
        estimated_cost=body.estimated_cost,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral


@referral_router.patch("/{referral_id}", response_model=VetReferralResponse)
async def update_referral(
    referral_id: UUID,
    body: VetReferralUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_medical_staff),
) -> VetReferral:
    """Update an existing vet referral."""
    referral = await _get_referral_or_404(referral_id, db)

    updates = body.model_dump(exclude_unset=True)
    # Convert enum values to strings for DB storage
    if "urgency" in updates and updates["urgency"] is not None:
        updates["urgency"] = updates["urgency"].value
    if "status" in updates and updates["status"] is not None:
        updates["status"] = updates["status"].value

    for field, value in updates.items():
        setattr(referral, field, value)

    await db.commit()
    await db.refresh(referral)
    return referral


@referral_router.delete("/{referral_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_referral(
    referral_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_medical_staff),
) -> None:
    """Cancel (soft-delete) a vet referral by setting status to cancelled."""
    referral = await _get_referral_or_404(referral_id, db)
    referral.status = ReferralStatus.CANCELLED.value
    await db.commit()
