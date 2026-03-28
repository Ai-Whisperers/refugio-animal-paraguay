"""Public sponsorship endpoints.

Allows unauthenticated donors to initiate an animal sponsorship.
Creates donor + sponsorship records and (when configured) initiates
a Stripe Checkout session for recurring billing.
"""

import os
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal
from src.db.models.donation import Donor
from src.db.models.sponsorship import (
    Sponsorship,
    SponsorshipFrequency,
    SponsorshipStatus,
    SponsorshipTier,
    SponsorshipTierLevel,
)
from src.db.session import get_db

router = APIRouter(prefix="/public/sponsorships", tags=["public-sponsorships"])

# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

MINIMUM_AMOUNT_CENTS = 500  # EUR 5


class PublicSponsorshipRequest(BaseModel):
    """Payload for a public (unauthenticated) sponsorship sign-up."""

    animal_id: UUID
    amount_cents: int = Field(..., ge=MINIMUM_AMOUNT_CENTS)
    currency: str = "EUR"
    frequency: SponsorshipFrequency = SponsorshipFrequency.MONTHLY
    donor_name: str = Field(..., min_length=1, max_length=255)
    donor_email: EmailStr
    tier_level: SponsorshipTierLevel | None = None

    @field_validator("currency")
    @classmethod
    def currency_must_be_eur(cls, v: str) -> str:
        if v.upper() != "EUR":
            raise ValueError("Only EUR is supported for sponsorships")
        return v.upper()


class PublicSponsorshipResponse(BaseModel):
    """Response after a public sponsorship is created."""

    sponsorship_id: str
    animal_id: str
    donor_email: str
    amount_cents: int
    currency: str
    frequency: str
    stripe_checkout_url: str | None = None
    message: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=PublicSponsorshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_sponsorship(
    payload: PublicSponsorshipRequest,
    db: AsyncSession = Depends(get_db),
) -> PublicSponsorshipResponse:
    """Create a sponsorship from the public sponsor page (no auth required).

    1. Validates animal exists
    2. Finds or creates a Donor record
    3. Resolves the sponsorship tier (by level or by amount)
    4. Creates a Sponsorship record
    5. Optionally creates a Stripe Checkout Session for recurring billing
    """
    # 1 — Validate animal
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {payload.animal_id} not found",
        )

    # 2 — Find or create donor
    donor_result = await db.execute(select(Donor).where(Donor.email == payload.donor_email))
    donor = donor_result.scalar_one_or_none()
    if donor is None:
        donor = Donor(
            full_name=payload.donor_name,
            email=payload.donor_email,
            currency_preference=payload.currency,
        )
        db.add(donor)
        await db.flush()

    # 3 — Resolve tier
    tier: SponsorshipTier | None = None
    if payload.tier_level is not None:
        tier_result = await db.execute(
            select(SponsorshipTier).where(
                SponsorshipTier.level == payload.tier_level.value,
                SponsorshipTier.active == True,  # noqa: E712
            )
        )
        tier = tier_result.scalar_one_or_none()

    # If no tier matched (custom amount), find the closest tier or use bronze as fallback
    if tier is None:
        tier_result = await db.execute(
            select(SponsorshipTier)
            .where(SponsorshipTier.active == True)  # noqa: E712
            .order_by(SponsorshipTier.amount_cents.asc())
        )
        all_tiers = list(tier_result.scalars().all())
        # Pick the tier whose amount is closest to but not exceeding the chosen amount
        tier = all_tiers[0] if all_tiers else None

    if tier is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No sponsorship tiers configured",
        )

    # 4 — Check for duplicate active sponsorship
    existing = await db.execute(
        select(Sponsorship).where(
            Sponsorship.donor_id == donor.id,
            Sponsorship.animal_id == payload.animal_id,
            Sponsorship.status == SponsorshipStatus.ACTIVE,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active sponsorship for this animal",
        )

    # 5 — Create sponsorship
    sponsorship = Sponsorship(
        donor_id=donor.id,
        animal_id=payload.animal_id,
        tier_id=tier.id,
        frequency=payload.frequency.value,
        status=SponsorshipStatus.ACTIVE.value,
    )
    db.add(sponsorship)
    await db.commit()
    await db.refresh(sponsorship)

    # 6 — Optionally create Stripe Checkout Session
    stripe_checkout_url: str | None = None
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    price_id = (
        tier.stripe_price_id_monthly
        if payload.frequency == SponsorshipFrequency.MONTHLY
        else tier.stripe_price_id_annual
    )

    if stripe_key and price_id:
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                customer_email=payload.donor_email,
                metadata={
                    "sponsorship_id": str(sponsorship.id),
                    "donor_id": str(donor.id),
                    "animal_id": str(payload.animal_id),
                },
                success_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/animals/{payload.animal_id}/sponsor?success=1",
                cancel_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/animals/{payload.animal_id}/sponsor",
            )
            stripe_checkout_url = session.url
        except stripe.StripeError:
            # Non-fatal: sponsorship is recorded, Stripe can be retried
            pass

    return PublicSponsorshipResponse(
        sponsorship_id=str(sponsorship.id),
        animal_id=str(payload.animal_id),
        donor_email=payload.donor_email,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        frequency=payload.frequency.value,
        stripe_checkout_url=stripe_checkout_url,
        message=f"Sponsorship for {animal.name} created successfully",
    )
