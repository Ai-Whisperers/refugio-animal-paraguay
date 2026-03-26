"""Stripe webhook endpoint.

Receives and processes Stripe webhook events for payment lifecycle management.
Verifies webhook signatures to prevent spoofed events, then dispatches to
the appropriate handler based on event type.

Endpoints:
  POST /webhooks/stripe  -- receive Stripe webhook events
"""

import logging
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.models.donation import Donation, DonationStatus
from src.db.session import get_db
from src.events.bus import EventBus
from src.events.domain_events import create_donation_received

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Stripe event types we handle
EVENT_PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
EVENT_PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
EVENT_CHARGE_REFUNDED = "charge.refunded"

HANDLED_EVENT_TYPES = frozenset(
    {
        EVENT_PAYMENT_INTENT_SUCCEEDED,
        EVENT_PAYMENT_INTENT_FAILED,
        EVENT_CHARGE_REFUNDED,
    }
)


async def _find_donation_by_payment_intent(
    db: AsyncSession, payment_intent_id: str
) -> Donation | None:
    """Look up a donation by its Stripe payment intent ID."""
    stmt = select(Donation).where(Donation.stripe_payment_intent_id == payment_intent_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _handle_payment_succeeded(
    db: AsyncSession,
    payment_intent_id: str,
    event_bus: EventBus | None,
) -> str:
    """Handle payment_intent.succeeded: mark donation completed, publish event."""
    donation = await _find_donation_by_payment_intent(db, payment_intent_id)
    if donation is None:
        logger.warning(
            "Webhook payment_intent.succeeded: no donation found for intent %s",
            payment_intent_id,
        )
        return "donation_not_found"

    # Idempotent: already completed
    if donation.status == DonationStatus.COMPLETED.value:
        logger.info(
            "Donation %s already completed, skipping duplicate webhook",
            donation.id,
        )
        return "already_completed"

    donation.status = DonationStatus.COMPLETED.value
    await db.flush()

    # Publish domain event for downstream processing (notifications, audit, etc.)
    if event_bus is not None and event_bus.is_running:
        event = create_donation_received(
            aggregate_id=donation.id,
            amount=str(donation.amount_cents),
            currency=donation.currency,
            donor_id=donation.donor_id,
        )
        await event_bus.publish(event)

    logger.info(
        "Donation %s marked completed via webhook (intent: %s)",
        donation.id,
        payment_intent_id,
    )
    return "completed"


async def _handle_payment_failed(
    db: AsyncSession,
    payment_intent_id: str,
) -> str:
    """Handle payment_intent.payment_failed: mark donation failed."""
    donation = await _find_donation_by_payment_intent(db, payment_intent_id)
    if donation is None:
        logger.warning(
            "Webhook payment_intent.payment_failed: no donation found for intent %s",
            payment_intent_id,
        )
        return "donation_not_found"

    # Idempotent: already failed
    if donation.status == DonationStatus.FAILED.value:
        logger.info(
            "Donation %s already failed, skipping duplicate webhook",
            donation.id,
        )
        return "already_failed"

    donation.status = DonationStatus.FAILED.value
    await db.flush()

    logger.info(
        "Donation %s marked failed via webhook (intent: %s)",
        donation.id,
        payment_intent_id,
    )
    return "failed"


async def _handle_charge_refunded(
    db: AsyncSession,
    payment_intent_id: str,
) -> str:
    """Handle charge.refunded: mark donation refunded."""
    donation = await _find_donation_by_payment_intent(db, payment_intent_id)
    if donation is None:
        logger.warning(
            "Webhook charge.refunded: no donation found for intent %s",
            payment_intent_id,
        )
        return "donation_not_found"

    # Idempotent: already refunded
    if donation.status == DonationStatus.REFUNDED.value:
        logger.info(
            "Donation %s already refunded, skipping duplicate webhook",
            donation.id,
        )
        return "already_refunded"

    donation.status = DonationStatus.REFUNDED.value
    await db.flush()

    logger.info(
        "Donation %s marked refunded via webhook (intent: %s)",
        donation.id,
        payment_intent_id,
    )
    return "refunded"


def _extract_payment_intent_id_from_object(
    data_object: Any, event_type: str
) -> str | None:
    """Extract the payment intent ID from a Stripe event's data.object.

    For payment_intent events, the object IS the payment intent (id field).
    For charge events, the payment_intent is a field on the charge object.
    data_object is a Stripe StripeObject which supports both [] and .get() access.
    """
    if event_type in (EVENT_PAYMENT_INTENT_SUCCEEDED, EVENT_PAYMENT_INTENT_FAILED):
        return data_object.get("id")
    if event_type == EVENT_CHARGE_REFUNDED:
        return data_object.get("payment_intent")
    return None


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Receive and process Stripe webhook events.

    Stripe sends POST requests to this endpoint when payment events occur.
    The endpoint verifies the webhook signature, then routes to the appropriate
    handler based on event type.

    Returns 200 for all valid requests (even unhandled event types) to prevent
    Stripe from retrying. Returns 400 only for invalid signatures.
    """
    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # Verify webhook signature
    webhook_secret = settings.stripe_webhook_secret
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook signing secret not configured",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except ValueError:
        logger.warning("Stripe webhook: invalid payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    event_type: str = event["type"]

    # Skip unhandled event types with 200 (don't trigger Stripe retries)
    if event_type not in HANDLED_EVENT_TYPES:
        logger.debug("Stripe webhook: unhandled event type %s, skipping", event_type)
        return {"status": "skipped", "event_type": event_type}

    # Extract the data object from the event using dict-style access
    # Stripe StripeObject supports [] but not .get() in v15
    data_obj: Any = event["data"]["object"]
    payment_intent_id = _extract_payment_intent_id_from_object(data_obj, event_type)
    if not payment_intent_id:
        logger.warning(
            "Stripe webhook: could not extract payment_intent_id from %s event",
            event_type,
        )
        return {"status": "skipped", "reason": "no_payment_intent_id"}

    # Get event bus from app state for domain event publishing
    event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)

    # Route to handler
    if event_type == EVENT_PAYMENT_INTENT_SUCCEEDED:
        result = await _handle_payment_succeeded(db, payment_intent_id, event_bus)
    elif event_type == EVENT_PAYMENT_INTENT_FAILED:
        result = await _handle_payment_failed(db, payment_intent_id)
    elif event_type == EVENT_CHARGE_REFUNDED:
        result = await _handle_charge_refunded(db, payment_intent_id)
    else:
        result = "unhandled"

    return {"status": "processed", "event_type": event_type, "result": result}
