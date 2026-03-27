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
from src.schemas.error import PAYMENT_RESPONSES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"], responses=PAYMENT_RESPONSES)

# Stripe event types we handle
EVENT_PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
EVENT_PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
EVENT_CHARGE_REFUNDED = "charge.refunded"
EVENT_INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
EVENT_INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
EVENT_SUBSCRIPTION_DELETED = "customer.subscription.deleted"

HANDLED_EVENT_TYPES = frozenset(
    {
        EVENT_PAYMENT_INTENT_SUCCEEDED,
        EVENT_PAYMENT_INTENT_FAILED,
        EVENT_CHARGE_REFUNDED,
        EVENT_INVOICE_PAYMENT_SUCCEEDED,
        EVENT_INVOICE_PAYMENT_FAILED,
        EVENT_SUBSCRIPTION_DELETED,
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


async def _handle_invoice_payment_succeeded(
    db: AsyncSession,
    data_object: Any,
    event_bus: EventBus | None,
) -> str:
    """Handle invoice.payment_succeeded: record recurring donation payment.

    When a subscription invoice is paid, create or update the donation record
    for the recurring subscription.
    """
    subscription_id = data_object.get("subscription")
    if not subscription_id:
        logger.debug("Invoice payment_succeeded without subscription, skipping")
        return "not_subscription"

    # Find the most recent donation record for this subscription
    stmt = (
        select(Donation)
        .where(Donation.stripe_subscription_id == subscription_id)
        .order_by(Donation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    donation = result.scalar_one_or_none()

    if donation is None:
        logger.warning(
            "Invoice payment_succeeded: no donation found for subscription %s",
            subscription_id,
        )
        return "donation_not_found"

    # For the initial invoice, mark the donation as completed
    if donation.status == DonationStatus.PENDING.value:
        donation.status = DonationStatus.COMPLETED.value
        await db.flush()

        if event_bus is not None and event_bus.is_running:
            event = create_donation_received(
                aggregate_id=donation.id,
                amount=str(donation.amount_cents),
                currency=donation.currency,
                donor_id=donation.donor_id,
            )
            await event_bus.publish(event)

        logger.info(
            "Subscription donation %s marked completed (subscription: %s)",
            donation.id,
            subscription_id,
        )
        return "completed"

    # For renewal invoices, the donation is already completed — idempotent
    logger.info(
        "Subscription donation %s already completed, renewal acknowledged (subscription: %s)",
        donation.id,
        subscription_id,
    )
    return "already_completed"


async def _handle_invoice_payment_failed(
    db: AsyncSession,
    data_object: Any,
) -> str:
    """Handle invoice.payment_failed: mark subscription donation as failed."""
    subscription_id = data_object.get("subscription")
    if not subscription_id:
        return "not_subscription"

    stmt = (
        select(Donation)
        .where(Donation.stripe_subscription_id == subscription_id)
        .order_by(Donation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    donation = result.scalar_one_or_none()

    if donation is None:
        logger.warning(
            "Invoice payment_failed: no donation found for subscription %s",
            subscription_id,
        )
        return "donation_not_found"

    if donation.status == DonationStatus.FAILED.value:
        return "already_failed"

    donation.status = DonationStatus.FAILED.value
    await db.flush()

    logger.info(
        "Subscription donation %s marked failed (subscription: %s)",
        donation.id,
        subscription_id,
    )
    return "failed"


async def _handle_subscription_deleted(
    db: AsyncSession,
    data_object: Any,
) -> str:
    """Handle customer.subscription.deleted: mark subscription as cancelled."""
    subscription_id = data_object.get("id")
    if not subscription_id:
        return "no_subscription_id"

    stmt = (
        select(Donation)
        .where(Donation.stripe_subscription_id == subscription_id)
        .order_by(Donation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    donation = result.scalar_one_or_none()

    if donation is None:
        logger.warning(
            "Subscription deleted: no donation found for subscription %s",
            subscription_id,
        )
        return "donation_not_found"

    # Mark as no longer recurring
    donation.is_recurring = False
    await db.flush()

    logger.info(
        "Subscription %s cancelled, donation %s updated",
        subscription_id,
        donation.id,
    )
    return "cancelled"


def _extract_payment_intent_id_from_object(data_object: Any, event_type: str) -> str | None:
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
    except ValueError as exc:
        logger.warning("Stripe webhook: invalid payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        ) from exc
    except stripe.SignatureVerificationError as exc:
        logger.warning("Stripe webhook: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        ) from exc

    event_type: str = event["type"]

    # Skip unhandled event types with 200 (don't trigger Stripe retries)
    if event_type not in HANDLED_EVENT_TYPES:
        logger.debug("Stripe webhook: unhandled event type %s, skipping", event_type)
        return {"status": "skipped", "event_type": event_type}

    # Extract the data object from the event using dict-style access
    # Stripe StripeObject supports [] but not .get() in v15
    data_obj: Any = event["data"]["object"]

    # Get event bus from app state for domain event publishing
    event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)

    # Route to handler — subscription/invoice events use data_obj directly
    if event_type == EVENT_INVOICE_PAYMENT_SUCCEEDED:
        result = await _handle_invoice_payment_succeeded(db, data_obj, event_bus)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_INVOICE_PAYMENT_FAILED:
        result = await _handle_invoice_payment_failed(db, data_obj)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_SUBSCRIPTION_DELETED:
        result = await _handle_subscription_deleted(db, data_obj)
        return {"status": "processed", "event_type": event_type, "result": result}

    # Payment intent events require extraction of payment_intent_id
    payment_intent_id = _extract_payment_intent_id_from_object(data_obj, event_type)
    if not payment_intent_id:
        logger.warning(
            "Stripe webhook: could not extract payment_intent_id from %s event",
            event_type,
        )
        return {"status": "skipped", "reason": "no_payment_intent_id"}

    if event_type == EVENT_PAYMENT_INTENT_SUCCEEDED:
        result = await _handle_payment_succeeded(db, payment_intent_id, event_bus)
    elif event_type == EVENT_PAYMENT_INTENT_FAILED:
        result = await _handle_payment_failed(db, payment_intent_id)
    elif event_type == EVENT_CHARGE_REFUNDED:
        result = await _handle_charge_refunded(db, payment_intent_id)
    else:
        result = "unhandled"

    return {"status": "processed", "event_type": event_type, "result": result}
