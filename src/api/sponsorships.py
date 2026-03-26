"""Sponsorship API endpoints.

Manages animal sponsorship tiers for recurring donor payments.

Endpoints:
  POST   /sponsorships              -- create a new sponsorship
  GET    /donors/{donor_id}/sponsorships  -- list donor's sponsorships
  GET    /animals/{animal_id}/sponsors    -- list animal's sponsors
  PATCH  /sponsorships/{id}         -- update tier, pause, or resume
  DELETE /sponsorships/{id}         -- cancel sponsorship
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.auth.models import User
from src.config import Settings, get_settings
from src.db.models.animal import Animal
from src.db.models.donation import Donor
from src.db.session import get_db
from src.schemas.sponsorship import (
    SponsorshipCreateRequest,
    SponsorshipListResponse,
    SponsorshipResponse,
    SponsorshipUpdateRequest,
)
from src.services.sponsorship_service import (
    cancel_sponsorship,
    create_sponsorship,
    get_animal_sponsors,
    get_donor_sponsorships,
    update_sponsorship,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sponsorships"])


@router.post(
    "/sponsorships",
    response_model=SponsorshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsorship_endpoint(
    payload: SponsorshipCreateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _current_user: User = Depends(require_staff),
) -> SponsorshipResponse:
    """Create a new animal sponsorship with recurring billing."""
    # Verify animal exists
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {payload.animal_id} not found",
        )

    try:
        sponsorship = await create_sponsorship(
            db=db,
            donor_id=payload.donor_id,
            animal_id=payload.animal_id,
            tier=payload.tier,
            currency=payload.currency,
            interval=payload.interval,
            stripe_api_key=settings.stripe_secret_key or None,
        )
    except ValueError as exc:
        # Donor not found or duplicate sponsorship
        detail = str(exc)
        if "not found" in detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        ) from exc

    return SponsorshipResponse.model_validate(sponsorship)


@router.get(
    "/donors/{donor_id}/sponsorships",
    response_model=SponsorshipListResponse,
)
async def list_donor_sponsorships(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SponsorshipListResponse:
    """List all sponsorships for a donor."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor {donor_id} not found",
        )

    sponsorships = await get_donor_sponsorships(db, donor_id)
    return SponsorshipListResponse(
        items=[SponsorshipResponse.model_validate(s) for s in sponsorships],
        count=len(sponsorships),
    )


@router.get(
    "/animals/{animal_id}/sponsors",
    response_model=SponsorshipListResponse,
)
async def list_animal_sponsors(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SponsorshipListResponse:
    """List active sponsors for an animal."""
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found",
        )

    sponsorships = await get_animal_sponsors(db, animal_id)
    return SponsorshipListResponse(
        items=[SponsorshipResponse.model_validate(s) for s in sponsorships],
        count=len(sponsorships),
    )


@router.patch(
    "/sponsorships/{sponsorship_id}",
    response_model=SponsorshipResponse,
)
async def update_sponsorship_endpoint(
    sponsorship_id: UUID,
    payload: SponsorshipUpdateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _current_user: User = Depends(require_staff),
) -> SponsorshipResponse:
    """Update a sponsorship: change tier, pause, or resume."""
    sponsorship = await update_sponsorship(
        db=db,
        sponsorship_id=sponsorship_id,
        tier=payload.tier,
        action=payload.action,
        stripe_api_key=settings.stripe_secret_key or None,
    )
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )

    return SponsorshipResponse.model_validate(sponsorship)


@router.delete(
    "/sponsorships/{sponsorship_id}",
    response_model=SponsorshipResponse,
)
async def cancel_sponsorship_endpoint(
    sponsorship_id: UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _current_user: User = Depends(require_staff),
) -> SponsorshipResponse:
    """Cancel a sponsorship."""
    sponsorship = await cancel_sponsorship(
        db=db,
        sponsorship_id=sponsorship_id,
        stripe_api_key=settings.stripe_secret_key or None,
    )
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )

    return SponsorshipResponse.model_validate(sponsorship)
