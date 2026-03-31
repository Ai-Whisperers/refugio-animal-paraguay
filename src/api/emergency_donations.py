"""Emergency donation endpoints -- simplified donation flow for emergencies.

Endpoints:
  POST /api/emergencies/{id}/donate -- create donation for an emergency (public)
  GET  /api/emergencies/{id}/donate/info -- get emergency info for donation page (public)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import (
    CurrencyCode,
    Donation,
    DonationTargetType,
    PaymentMethod,
)
from src.db.models.emergency_case import EmergencyCase
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

SUGGESTED_FIXED_AMOUNTS_CENTS = [5_000, 10_000, 25_000, 50_000]

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EmergencyDonateInfoResponse(BaseModel):
    """Emergency info needed to render the donation page."""

    id: UUID
    title: str
    description: str
    photos: list = Field(default_factory=list)
    amount_needed_cents: int
    amount_raised_cents: int
    remaining_cents: int
    currency: str
    progress_pct: int
    suggested_amounts_cents: list[int]
    status: str

    model_config = {"from_attributes": True}


class EmergencyDonationRequest(BaseModel):
    """Payload for creating an emergency donation."""

    amount_cents: int = Field(..., gt=0, description="Amount in smallest currency unit")
    currency: CurrencyCode = CurrencyCode.USD
    payment_method: PaymentMethod = PaymentMethod.STRIPE
    # Guest donor info (optional -- logged-in users skip these)
    donor_email: EmailStr | None = None
    donor_name: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)


class EmergencyDonationResponse(BaseModel):
    """Response after creating an emergency donation."""

    donation_id: UUID
    emergency_id: UUID
    amount_cents: int
    currency: str
    new_total_raised_cents: int
    new_progress_pct: int
    message: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/emergencies",
    tags=["emergency-donations"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_active_emergency(db: AsyncSession, emergency_id: UUID) -> EmergencyCase:
    """Fetch an active emergency or raise 404."""
    stmt = select(EmergencyCase).where(
        EmergencyCase.id == emergency_id,
        EmergencyCase.is_deleted.is_(False),
    )
    result = await db.execute(stmt)
    case_obj = result.scalar_one_or_none()

    if case_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Emergency not found"},
        )
    return case_obj


def _calc_progress(needed: int, raised: int) -> int:
    """Calculate funding progress percentage, capped at 100."""
    if needed <= 0:
        return 100
    return min(100, int((raised / needed) * 100))


def _suggested_amounts(remaining_cents: int) -> list[int]:
    """Return suggested donation amounts based on remaining need.

    Returns percentage-based amounts (10%, 25%, 50%, 100% of remaining)
    plus fixed fallback amounts, deduplicated and sorted.
    """
    if remaining_cents <= 0:
        return SUGGESTED_FIXED_AMOUNTS_CENTS

    pct_amounts = [max(100, int(remaining_cents * pct)) for pct in (0.10, 0.25, 0.50, 1.00)]
    # Merge with fixed amounts, deduplicate, sort
    all_amounts = sorted(set(pct_amounts + SUGGESTED_FIXED_AMOUNTS_CENTS))
    return all_amounts[:6]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{emergency_id}/donate/info",
    response_model=EmergencyDonateInfoResponse,
    summary="Get emergency info for donation page",
)
async def get_emergency_donate_info(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return emergency details and suggested donation amounts for the donate page."""
    case_obj = await _get_active_emergency(db, emergency_id)

    needed = case_obj.amount_needed_cents or 0
    raised = case_obj.amount_raised_cents or 0
    remaining = max(0, needed - raised)

    return {
        "id": case_obj.id,
        "title": case_obj.title,
        "description": case_obj.description,
        "photos": case_obj.photos or [],
        "amount_needed_cents": needed,
        "amount_raised_cents": raised,
        "remaining_cents": remaining,
        "currency": case_obj.currency,
        "progress_pct": _calc_progress(needed, raised),
        "suggested_amounts_cents": _suggested_amounts(remaining),
        "status": case_obj.status,
    }


@router.post(
    "/{emergency_id}/donate",
    response_model=EmergencyDonationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a donation for an emergency case",
)
async def create_emergency_donation(
    emergency_id: UUID,
    payload: EmergencyDonationRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a donation targeted at a specific emergency case.

    Updates the emergency's amount_raised_cents and creates a donation record
    with target_type='emergency'.
    """
    case_obj = await _get_active_emergency(db, emergency_id)

    if case_obj.status not in ("active", "funded"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Emergency is not accepting donations"},
        )

    # Create donation record
    donation = Donation(
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method=payload.payment_method.value,
        target_type=DonationTargetType.EMERGENCY.value,
        target_id=emergency_id,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()

    # Update emergency raised amount
    new_raised = (case_obj.amount_raised_cents or 0) + payload.amount_cents
    case_obj.amount_raised_cents = new_raised

    # Auto-mark as funded if goal reached
    if new_raised >= (case_obj.amount_needed_cents or 0):
        case_obj.status = "funded"
        logger.info(
            "Emergency %s fully funded (raised=%d, needed=%d)",
            emergency_id,
            new_raised,
            case_obj.amount_needed_cents,
        )

    await db.flush()
    await db.refresh(donation)

    progress = _calc_progress(case_obj.amount_needed_cents or 0, new_raised)

    return {
        "donation_id": donation.id,
        "emergency_id": emergency_id,
        "amount_cents": payload.amount_cents,
        "currency": payload.currency.value,
        "new_total_raised_cents": new_raised,
        "new_progress_pct": progress,
        "message": f"Gracias por tu donacion! Has ayudado a alcanzar el {progress}% de la meta.",
    }
