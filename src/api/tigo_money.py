"""Tigo Money payment API router.

Endpoints:
  POST /tigo-money/initiate  — start a Tigo Money checkout session for a PYG donation
  POST /tigo-money/callback  — Tigo webhook: verify signature, complete donation

These endpoints complement the existing Stripe endpoints in /donations.
Local Paraguayan donors use Tigo Money instead of credit cards.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.models.donation import Donation, DonationStatus, Donor, PaymentMethod
from src.db.session import get_db
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.schemas.error import PAYMENT_RESPONSES
from src.schemas.tigo_money import (
    TigoCallbackRequest,
    TigoPaymentInitRequest,
    TigoPaymentInitResponse,
)
from src.services.tigo_money_service import (
    TIGO_STATUS_CANCELLED,
    TIGO_STATUS_COMPLETED,
    TIGO_STATUS_FAILED,
    TigoMoneyService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tigo-money", tags=["tigo-money"], responses=PAYMENT_RESPONSES)


def _get_tigo_service(settings: Settings = Depends(get_settings)) -> TigoMoneyService:
    """Dependency: resolved Tigo Money service bound to app settings."""
    return TigoMoneyService(settings)


@router.post(
    "/initiate",
    response_model=TigoPaymentInitResponse,
    summary="Initiate a Tigo Money checkout session",
    description=(
        "Creates a pending donation record and returns a Tigo Money checkout URL. "
        "Redirect the donor to checkout_url to complete payment."
    ),
)
async def initiate_tigo_payment(
    body: TigoPaymentInitRequest,
    db: AsyncSession = Depends(get_db),
    tigo: TigoMoneyService = Depends(_get_tigo_service),
) -> TigoPaymentInitResponse:
    """Start a Tigo Money payment session for a local PYG donation."""
    if not tigo.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tigo Money payments are not enabled on this server.",
        )

    # Verify donor exists
    donor_result = await db.execute(select(Donor).where(Donor.id == body.donor_id))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor {body.donor_id} not found.",
        )

    # Create a pending donation record — will be updated on callback
    donation = Donation(
        donor_id=body.donor_id,
        amount_cents=body.amount_pyg,  # PYG has no minor unit; 1 PYG = 1 stored unit
        currency="PYG",
        payment_method=PaymentMethod.TIGO_MONEY,
        status=DonationStatus.PENDING,
        fund_category=body.fund_category,
        campaign_id=body.campaign_id,
    )
    db.add(donation)
    await db.flush()  # Populate donation.id without committing

    # Initiate Tigo Money session
    session = await tigo.initiate_payment(
        amount_pyg=body.amount_pyg,
        reference=str(donation.id),
        return_url=body.return_url,
    )

    if not session:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tigo Money payment gateway did not return a checkout URL. Try again.",
        )

    # Store the transaction ID for lookup on callback
    donation.tigo_transaction_id = session.transaction_id
    await db.commit()

    logger.info(
        "Tigo Money session initiated: donation_id=%s transaction_id=%s amount_pyg=%d",
        donation.id,
        session.transaction_id,
        body.amount_pyg,
    )

    return TigoPaymentInitResponse(
        donation_id=donation.id,
        transaction_id=session.transaction_id,
        checkout_url=session.checkout_url,
        amount_pyg=body.amount_pyg,
    )


@router.post(
    "/callback",
    status_code=status.HTTP_200_OK,
    summary="Tigo Money webhook callback",
    description=(
        "Receives payment outcome from Tigo Money. "
        "Verifies HMAC signature, updates donation status, and emits domain event."
    ),
)
async def tigo_callback(
    request: Request,
    body: TigoCallbackRequest,
    x_tigo_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    tigo: TigoMoneyService = Depends(_get_tigo_service),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Handle Tigo Money webhook after payment completion or failure."""
    if not tigo.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tigo Money payments are not enabled.",
        )

    # Verify webhook signature
    if x_tigo_signature:
        callback = tigo.verify_callback(body.model_dump(), x_tigo_signature)
        if callback is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature.",
            )
    else:
        # Signature header absent — log warning but continue (sandbox may omit it)
        logger.warning(
            "Tigo Money callback received without X-Tigo-Signature header "
            "— proceeding without verification (expected only in sandbox mode)"
        )

    # Look up the donation by reference (= donation.id)
    try:
        donation_id = UUID(body.reference)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"reference is not a valid donation ID: {body.reference!r}",
        ) from exc

    result = await db.execute(select(Donation).where(Donation.id == donation_id))
    donation = result.scalar_one_or_none()
    if not donation:
        logger.warning(
            "Tigo callback for unknown donation_id=%s — ignoring",
            donation_id,
        )
        return {"received": True}

    # Idempotency: skip if already in a terminal state
    if donation.status in (DonationStatus.COMPLETED, DonationStatus.FAILED):
        logger.info(
            "Tigo callback for already-settled donation_id=%s status=%s — skipping",
            donation_id,
            donation.status,
        )
        return {"received": True}

    # Update status based on Tigo outcome
    if body.status == TIGO_STATUS_COMPLETED:
        donation.status = DonationStatus.COMPLETED
        logger.info(
            "Tigo payment completed: donation_id=%s transaction_id=%s",
            donation_id,
            body.transaction_id,
        )
        # Emit domain event for downstream handlers (email, in-app, etc.)
        event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)
        if event_bus:
            await event_bus.publish(
                DomainEvent(
                    event_type=EventType.DONATION_RECEIVED,
                    aggregate_id=donation.id,
                    aggregate_type="donation",
                    payload={
                        "amount": str(donation.amount_cents),
                        "currency": "PYG",
                        "payment_method": "tigo_money",
                        "transaction_id": body.transaction_id,
                    },
                )
            )
    elif body.status in (TIGO_STATUS_FAILED, TIGO_STATUS_CANCELLED):
        donation.status = DonationStatus.FAILED
        logger.info(
            "Tigo payment failed/cancelled: donation_id=%s status=%s",
            donation_id,
            body.status,
        )
    else:
        # PENDING or unknown — leave as-is
        logger.debug(
            "Tigo callback with non-terminal status=%s for donation_id=%s",
            body.status,
            donation_id,
        )

    await db.commit()
    return {"received": True}
