"""Donations router.

Endpoints:
  POST /donations                    — create donation record (public; anonymous if no donor_id)
  POST /donations/cash               — record cash donation (staff only, immediate completion)
  POST /donations/{id}/stripe-intent — create Stripe PaymentIntent, return client_secret (public)
  GET  /donations                    — paginated list with filters (staff only)
  GET  /donations/{id}               — single donation (staff only)
"""

import os
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.donation import (
    CashDonationCreate,
    DonationCreate,
    DonationResponse,
    StripeIntentResponse,
)

router = APIRouter(prefix="/donations", tags=["donations"])

_STRIPE_CURRENCY_MAP = {
    "EUR": "eur",
    "USD": "usd",
    # PYG is not supported by Stripe — only cash/transfer for local PYG donations
}


def _get_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )
    return key


@router.post("", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    payload: DonationCreate,
    db: AsyncSession = Depends(get_db),
) -> Donation:
    # Verify donor exists if a donor_id was supplied
    if payload.donor_id is not None:
        donor = await db.get(Donor, payload.donor_id)
        if donor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method=payload.payment_method.value,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)
    return donation


@router.post("/cash", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def record_cash_donation(
    payload: CashDonationCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Donation:
    """Record a cash donation received at the shelter. Staff only.

    Cash donations are created with status=completed immediately
    since the money has already been received.
    """
    if payload.donor_id is not None:
        donor = await db.get(Donor, payload.donor_id)
        if donor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method="cash",
        status="completed",
        receipt_number=payload.receipt_number,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)
    return donation


@router.post(
    "/{donation_id}/stripe-intent",
    response_model=StripeIntentResponse,
)
async def create_stripe_intent(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StripeIntentResponse:
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    if donation.status != DonationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create payment intent for donation with status '{donation.status}'",
        )

    if donation.currency not in _STRIPE_CURRENCY_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"Currency '{donation.currency}' is not supported by Stripe. Use cash or transfer for PYG.",
        )

    stripe.api_key = _get_stripe_key()
    intent = stripe.PaymentIntent.create(
        amount=donation.amount_cents,
        currency=_STRIPE_CURRENCY_MAP[donation.currency],
        metadata={"donation_id": str(donation_id)},
    )

    if intent.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a client secret",
        )

    donation.stripe_payment_intent_id = intent.id
    await db.flush()

    return StripeIntentResponse(
        donation_id=donation_id,
        stripe_payment_intent_id=intent.id,
        client_secret=intent.client_secret,
        amount_cents=donation.amount_cents,
        currency=donation.currency,  # type: ignore[arg-type]
    )


@router.get("", response_model=list[DonationResponse])
async def list_donations(
    currency: str | None = Query(default=None),
    donation_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Donation]:
    stmt = select(Donation)
    if currency is not None:
        stmt = stmt.where(Donation.currency == currency.upper())
    if donation_status is not None:
        stmt = stmt.where(Donation.status == donation_status.lower())
    stmt = stmt.order_by(Donation.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Donation:
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )
    return donation
