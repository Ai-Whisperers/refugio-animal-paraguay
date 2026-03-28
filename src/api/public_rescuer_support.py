"""Public rescuer support endpoint.

Allows unauthenticated donors to support a rescuer with a one-time
or recurring donation. Creates a Donor record (or finds existing),
creates a Donation record linked to the rescuer, and optionally
creates a Stripe Checkout session.
"""

import os
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import (
    CurrencyCode,
    Donation,
    DonationStatus,
    DonationTargetType,
    Donor,
    PaymentMethod,
)
from src.db.models.rescuer_profile import RescuerProfile
from src.db.models.user import User
from src.db.session import get_db

router = APIRouter(prefix="/public/rescuer-support", tags=["public-rescuer-support"])

MINIMUM_AMOUNT_CENTS = 500  # EUR 5


class RescuerSupportRequest(BaseModel):
    """Payload for a public (no-auth) rescuer support donation."""

    rescuer_user_id: UUID
    amount_cents: int = Field(..., ge=MINIMUM_AMOUNT_CENTS)
    currency: str = "EUR"
    is_recurring: bool = False
    donor_name: str = Field(..., min_length=1, max_length=255)
    donor_email: EmailStr
    is_anonymous: bool = False

    @field_validator("currency")
    @classmethod
    def currency_must_be_eur(cls, v: str) -> str:
        if v.upper() != "EUR":
            raise ValueError("Only EUR is supported for rescuer support")
        return v.upper()


class RescuerSupportResponse(BaseModel):
    """Response after creating a rescuer support donation."""

    donation_id: str
    rescuer_name: str
    donor_email: str
    amount_cents: int
    currency: str
    is_recurring: bool
    stripe_checkout_url: str | None = None
    message: str


@router.post(
    "",
    response_model=RescuerSupportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rescuer_support(
    payload: RescuerSupportRequest,
    db: AsyncSession = Depends(get_db),
) -> RescuerSupportResponse:
    """Create a donation directed at a rescuer (no auth required).

    1. Validate the rescuer user exists
    2. Find or create a Donor record
    3. Create a Donation with target_type=rescuer
    4. Update rescuer supporter_count
    5. Optionally create Stripe Checkout session
    """
    # 1 — Validate rescuer user
    rescuer_user = await db.get(User, payload.rescuer_user_id)
    if rescuer_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rescuer user {payload.rescuer_user_id} not found",
        )

    # Look up the rescuer profile for the display name
    profile_result = await db.execute(
        select(RescuerProfile).where(RescuerProfile.user_id == payload.rescuer_user_id)
    )
    profile = profile_result.scalar_one_or_none()
    rescuer_name = profile.display_name if profile else "Rescatista"

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

    # 3 — Create donation
    donation = Donation(
        donor_id=donor.id,
        amount_cents=payload.amount_cents,
        currency=CurrencyCode.EUR,
        payment_method=PaymentMethod.STRIPE,
        status=DonationStatus.PENDING,
        target_type=DonationTargetType.RESCUER,
        target_id=payload.rescuer_user_id,
        notes="anonymous=true" if payload.is_anonymous else None,
    )
    db.add(donation)

    # 4 — Increment supporter count on profile
    if profile is not None:
        profile.supporter_count = profile.supporter_count + 1

    await db.commit()
    await db.refresh(donation)

    # 5 — Optionally create Stripe Checkout session
    stripe_checkout_url: str | None = None
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if stripe_key:
        try:
            stripe.api_key = stripe_key
            mode = "subscription" if payload.is_recurring else "payment"
            line_items = [
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": payload.amount_cents,
                        "product_data": {
                            "name": f"Apoyo a {rescuer_name}",
                        },
                        **({"recurring": {"interval": "month"}} if payload.is_recurring else {}),
                    },
                    "quantity": 1,
                }
            ]
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            session = stripe.checkout.Session.create(
                mode=mode,
                line_items=line_items,
                customer_email=payload.donor_email,
                metadata={
                    "donation_id": str(donation.id),
                    "rescuer_user_id": str(payload.rescuer_user_id),
                    "donor_id": str(donor.id),
                },
                success_url=f"{frontend_url}/rescuers/{profile.slug if profile else 'unknown'}/support?success=1",
                cancel_url=f"{frontend_url}/rescuers/{profile.slug if profile else 'unknown'}/support",
            )
            stripe_checkout_url = session.url
        except stripe.StripeError:
            # Non-fatal: donation is recorded, Stripe can be retried
            pass

    return RescuerSupportResponse(
        donation_id=str(donation.id),
        rescuer_name=rescuer_name,
        donor_email=payload.donor_email,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        is_recurring=payload.is_recurring,
        stripe_checkout_url=stripe_checkout_url,
        message=f"Support for {rescuer_name} recorded successfully",
    )
