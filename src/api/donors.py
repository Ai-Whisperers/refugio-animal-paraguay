"""Donors router.

Endpoints:
  POST /donors       — create donor profile (public)
  GET  /donors/{id}  — get donor profile (staff only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.donation import DonorCreate, DonorResponse

router = APIRouter(prefix="/donors", tags=["donors"])


@router.post("", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    payload: DonorCreate,
    db: AsyncSession = Depends(get_db),
) -> Donor:
    donor = Donor(
        full_name=payload.full_name,
        email=str(payload.email),
        country=payload.country,
        currency_preference=payload.currency_preference.value,
        gdpr_consent_at=payload.gdpr_consent_at,
    )
    db.add(donor)
    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A donor with this email already exists",
        ) from exc
    await db.refresh(donor)
    return donor


@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Donor:
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")
    return donor
