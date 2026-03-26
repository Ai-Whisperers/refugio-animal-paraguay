"""Sponsorships router.

Endpoints:
  POST   /sponsorships                         -- create sponsorship (staff or authenticated donor)
  GET    /sponsorships                         -- list all sponsorships, paginated (staff only)
  GET    /sponsorships/{id}                    -- single sponsorship (staff only)
  PATCH  /sponsorships/{id}/cancel             -- cancel sponsorship (staff only)
  PATCH  /sponsorships/{id}/pause              -- pause sponsorship (staff only)
  PATCH  /sponsorships/{id}/resume             -- resume sponsorship (staff only)
  GET    /sponsorships/tiers                   -- list available tiers (public)
  PATCH  /sponsorships/tiers/{id}              -- update tier metadata (admin only)
  GET    /animals/{animal_id}/sponsorships     -- sponsorships for an animal (staff only)
  GET    /donors/{donor_id}/sponsorships       -- sponsorships for a donor (staff only)
"""

import os
from datetime import UTC, datetime
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import require_admin, require_staff
from src.db.models.animal import Animal
from src.db.models.donation import Donor
from src.db.models.sponsorship import (
    Sponsorship,
    SponsorshipFrequency,
    SponsorshipStatus,
    SponsorshipTier,
)
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.sponsorship import (
    SponsorshipCancelRequest,
    SponsorshipCreate,
    SponsorshipListResponse,
    SponsorshipPauseRequest,
    SponsorshipResponse,
    SponsorshipTierResponse,
    SponsorshipTierUpdate,
)

router = APIRouter(tags=["sponsorships"])

# ---------------------------------------------------------------------------
# Stripe helper
# ---------------------------------------------------------------------------


def _get_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )
    return key


# ---------------------------------------------------------------------------
# Public: tier listing
# ---------------------------------------------------------------------------


@router.get("/sponsorships/tiers", response_model=list[SponsorshipTierResponse])
async def list_sponsorship_tiers(
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipTier]:
    """Return all active sponsorship tiers, ordered by display_order."""
    result = await db.execute(
        select(SponsorshipTier)
        .where(SponsorshipTier.active == True)  # noqa: E712
        .order_by(SponsorshipTier.display_order)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Admin: tier update
# ---------------------------------------------------------------------------


@router.patch(
    "/sponsorships/tiers/{tier_id}",
    response_model=SponsorshipTierResponse,
)
async def update_sponsorship_tier(
    tier_id: UUID,
    payload: SponsorshipTierUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> SponsorshipTier:
    """Update tier metadata (Stripe price IDs, benefits). Admin only."""
    tier = await db.get(SponsorshipTier, tier_id)
    if tier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship tier {tier_id} not found",
        )
    if payload.stripe_price_id_monthly is not None:
        tier.stripe_price_id_monthly = payload.stripe_price_id_monthly
    if payload.stripe_price_id_annual is not None:
        tier.stripe_price_id_annual = payload.stripe_price_id_annual
    if payload.benefits is not None:
        tier.benefits = payload.benefits
    if payload.active is not None:
        tier.active = payload.active
    await db.commit()
    await db.refresh(tier)
    return tier


# ---------------------------------------------------------------------------
# Staff: create sponsorship
# ---------------------------------------------------------------------------


@router.post(
    "/sponsorships",
    response_model=SponsorshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsorship(
    payload: SponsorshipCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Sponsorship:
    """Create a new sponsorship and initiate Stripe subscription if price ID configured."""
    # Verify donor exists
    donor = await db.get(Donor, payload.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor {payload.donor_id} not found",
        )

    # Verify animal exists
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {payload.animal_id} not found",
        )

    # Fetch the tier by level
    tier_result = await db.execute(
        select(SponsorshipTier).where(
            SponsorshipTier.level == payload.tier_level.value,
            SponsorshipTier.active == True,  # noqa: E712
        )
    )
    tier = tier_result.scalar_one_or_none()
    if tier is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sponsorship tier '{payload.tier_level}' not found or inactive",
        )

    # Check that the donor does not already have an active sponsorship for this animal
    existing_result = await db.execute(
        select(Sponsorship).where(
            Sponsorship.donor_id == payload.donor_id,
            Sponsorship.animal_id == payload.animal_id,
            Sponsorship.status == SponsorshipStatus.ACTIVE,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donor already has an active sponsorship for this animal",
        )

    # Create Stripe subscription if a price ID is configured for this tier/frequency
    stripe_subscription_id: str | None = None
    price_id = (
        tier.stripe_price_id_monthly
        if payload.frequency == SponsorshipFrequency.MONTHLY
        else tier.stripe_price_id_annual
    )

    if price_id:
        try:
            stripe.api_key = _get_stripe_key()
            # Create a Stripe Customer first (using email for idempotency search),
            # then attach the subscription. In production, persist customer.id on the Donor.
            existing_customers = stripe.Customer.list(email=donor.email, limit=1)
            if existing_customers.data:
                stripe_customer_id = existing_customers.data[0].id
            else:
                customer = stripe.Customer.create(
                    email=donor.email,
                    name=donor.full_name,
                    metadata={"donor_id": str(payload.donor_id)},
                )
                stripe_customer_id = customer.id

            subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{"price": price_id}],
                metadata={
                    "donor_id": str(payload.donor_id),
                    "animal_id": str(payload.animal_id),
                    "tier_level": payload.tier_level.value,
                },
            )
            stripe_subscription_id = subscription.id
        except stripe.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe subscription creation failed: {exc.user_message}",
            ) from exc

    sponsorship = Sponsorship(
        donor_id=payload.donor_id,
        animal_id=payload.animal_id,
        tier_id=tier.id,
        frequency=payload.frequency.value,
        status=SponsorshipStatus.ACTIVE.value,
        stripe_subscription_id=stripe_subscription_id,
        notes=payload.notes,
    )
    db.add(sponsorship)
    await db.commit()
    await db.refresh(sponsorship)

    # Load tier relationship for response
    await db.refresh(sponsorship, ["tier"])
    return sponsorship


# ---------------------------------------------------------------------------
# Staff: list sponsorships
# ---------------------------------------------------------------------------


@router.get("/sponsorships", response_model=SponsorshipListResponse)
async def list_sponsorships(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: SponsorshipStatus | None = Query(None, alias="status"),
    donor_id: UUID | None = None,
    animal_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SponsorshipListResponse:
    """List all sponsorships with optional filters. Staff only."""
    base_query = select(Sponsorship).options(selectinload(Sponsorship.tier))

    if status_filter is not None:
        base_query = base_query.where(Sponsorship.status == status_filter.value)
    if donor_id is not None:
        base_query = base_query.where(Sponsorship.donor_id == donor_id)
    if animal_id is not None:
        base_query = base_query.where(Sponsorship.animal_id == animal_id)

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base_query.order_by(Sponsorship.created_at.desc()).offset(offset).limit(page_size)
    )
    items = list(items_result.scalars().all())

    return SponsorshipListResponse(
        items=[SponsorshipResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Staff: single sponsorship
# ---------------------------------------------------------------------------


@router.get("/sponsorships/{sponsorship_id}", response_model=SponsorshipResponse)
async def get_sponsorship(
    sponsorship_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Sponsorship:
    """Fetch a single sponsorship by ID. Staff only."""
    result = await db.execute(
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.id == sponsorship_id)
    )
    sponsorship = result.scalar_one_or_none()
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )
    return sponsorship


# ---------------------------------------------------------------------------
# Staff: cancel sponsorship
# ---------------------------------------------------------------------------


@router.patch("/sponsorships/{sponsorship_id}/cancel", response_model=SponsorshipResponse)
async def cancel_sponsorship(
    sponsorship_id: UUID,
    payload: SponsorshipCancelRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Sponsorship:
    """Cancel an active or paused sponsorship. Staff only."""
    result = await db.execute(
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.id == sponsorship_id)
    )
    sponsorship = result.scalar_one_or_none()
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )
    if sponsorship.status == SponsorshipStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sponsorship is already cancelled",
        )
    if sponsorship.status == SponsorshipStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot cancel a completed sponsorship",
        )

    # Cancel Stripe subscription if present
    if sponsorship.stripe_subscription_id:
        try:
            stripe.api_key = _get_stripe_key()
            stripe.Subscription.cancel(sponsorship.stripe_subscription_id)
        except stripe.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe cancellation failed: {exc.user_message}",
            ) from exc

    sponsorship.status = SponsorshipStatus.CANCELLED.value
    sponsorship.ended_at = datetime.now(UTC)
    if payload and payload.notes:
        sponsorship.notes = payload.notes

    await db.commit()
    await db.refresh(sponsorship, ["tier"])
    return sponsorship


# ---------------------------------------------------------------------------
# Staff: pause sponsorship
# ---------------------------------------------------------------------------


@router.patch("/sponsorships/{sponsorship_id}/pause", response_model=SponsorshipResponse)
async def pause_sponsorship(
    sponsorship_id: UUID,
    payload: SponsorshipPauseRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Sponsorship:
    """Pause an active sponsorship (suspends Stripe invoices). Staff only."""
    result = await db.execute(
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.id == sponsorship_id)
    )
    sponsorship = result.scalar_one_or_none()
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )
    if sponsorship.status != SponsorshipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only active sponsorships can be paused (current status: {sponsorship.status})",
        )

    # Pause Stripe subscription billing
    if sponsorship.stripe_subscription_id:
        try:
            stripe.api_key = _get_stripe_key()
            stripe.Subscription.modify(
                sponsorship.stripe_subscription_id,
                pause_collection={"behavior": "void"},
            )
        except stripe.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe pause failed: {exc.user_message}",
            ) from exc

    sponsorship.status = SponsorshipStatus.PAUSED.value
    if payload and payload.notes:
        sponsorship.notes = payload.notes

    await db.commit()
    await db.refresh(sponsorship, ["tier"])
    return sponsorship


# ---------------------------------------------------------------------------
# Staff: resume sponsorship
# ---------------------------------------------------------------------------


@router.patch("/sponsorships/{sponsorship_id}/resume", response_model=SponsorshipResponse)
async def resume_sponsorship(
    sponsorship_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Sponsorship:
    """Resume a paused sponsorship. Staff only."""
    result = await db.execute(
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.id == sponsorship_id)
    )
    sponsorship = result.scalar_one_or_none()
    if sponsorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found",
        )
    if sponsorship.status != SponsorshipStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Only paused sponsorships can be resumed "
                f"(current status: {sponsorship.status})"
            ),
        )

    # Resume Stripe subscription billing
    if sponsorship.stripe_subscription_id:
        try:
            stripe.api_key = _get_stripe_key()
            stripe.Subscription.modify(
                sponsorship.stripe_subscription_id,
                pause_collection="",
            )
        except stripe.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe resume failed: {exc.user_message}",
            ) from exc

    sponsorship.status = SponsorshipStatus.ACTIVE.value
    await db.commit()
    await db.refresh(sponsorship, ["tier"])
    return sponsorship


# ---------------------------------------------------------------------------
# Staff: sponsorships by animal
# ---------------------------------------------------------------------------


@router.get("/animals/{animal_id}/sponsorships", response_model=SponsorshipListResponse)
async def list_animal_sponsorships(
    animal_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SponsorshipListResponse:
    """List all sponsorships for a specific animal. Staff only."""
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found",
        )

    base_query = (
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.animal_id == animal_id)
    )
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base_query.order_by(Sponsorship.created_at.desc()).offset(offset).limit(page_size)
    )

    return SponsorshipListResponse(
        items=[SponsorshipResponse.model_validate(s) for s in items_result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Staff: sponsorships by donor
# ---------------------------------------------------------------------------


@router.get("/donors/{donor_id}/sponsorships", response_model=SponsorshipListResponse)
async def list_donor_sponsorships(
    donor_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SponsorshipListResponse:
    """List all sponsorships for a specific donor. Staff only."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor {donor_id} not found",
        )

    base_query = (
        select(Sponsorship)
        .options(selectinload(Sponsorship.tier))
        .where(Sponsorship.donor_id == donor_id)
    )
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base_query.order_by(Sponsorship.created_at.desc()).offset(offset).limit(page_size)
    )

    return SponsorshipListResponse(
        items=[SponsorshipResponse.model_validate(s) for s in items_result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )
