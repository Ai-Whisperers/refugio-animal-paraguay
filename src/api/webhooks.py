"""Stripe webhook endpoint.

Receives and processes Stripe webhook events for payment lifecycle management.
Verifies webhook signatures to prevent spoofed events, then dispatches to
the appropriate handler based on event type.

Endpoints:
  POST /webhooks/stripe  -- receive Stripe webhook events

SEPA-specific events handled:
  payment_intent.processing          -- SEPA payment accepted by bank (async processing)
  setup_intent.succeeded             -- SEPA mandate saved successfully
  setup_intent.setup_failed          -- SEPA mandate setup failed
  mandate.updated                    -- SEPA mandate status changed
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
from src.services import subscription_service
from src.services.dunning_service import DunningService
from src.services.sepa_notification_service import SepaNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"], responses=PAYMENT_RESPONSES)

# Stripe event types we handle
EVENT_PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
EVENT_PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
EVENT_PAYMENT_INTENT_PROCESSING = "payment_intent.processing"
EVENT_CHARGE_REFUNDED = "charge.refunded"
EVENT_INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
EVENT_INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
EVENT_SUBSCRIPTION_DELETED = "customer.subscription.deleted"
EVENT_SUBSCRIPTION_UPDATED = "customer.subscription.updated"

# SEPA-specific events
EVENT_SETUP_INTENT_SUCCEEDED = "setup_intent.succeeded"
EVENT_SETUP_INTENT_FAILED = "setup_intent.setup_failed"
EVENT_MANDATE_UPDATED = "mandate.updated"

HANDLED_EVENT_TYPES = frozenset(
    {
        EVENT_PAYMENT_INTENT_SUCCEEDED,
        EVENT_PAYMENT_INTENT_FAILED,
        EVENT_PAYMENT_INTENT_PROCESSING,
        EVENT_CHARGE_REFUNDED,
        EVENT_INVOICE_PAYMENT_SUCCEEDED,
        EVENT_INVOICE_PAYMENT_FAILED,
        EVENT_SUBSCRIPTION_DELETED,
        EVENT_SUBSCRIPTION_UPDATED,
        EVENT_SETUP_INTENT_SUCCEEDED,
        EVENT_SETUP_INTENT_FAILED,
        EVENT_MANDATE_UPDATED,
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
    dunning: "DunningService | None" = None,
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

    # Record failure on the Subscription record for dunning tracking
    error_message = data_object.get("last_finalization_error", {})
    error_msg_str = (
        str(error_message.get("message", "Payment failed")) if error_message else "Payment failed"
    )
    failure_result = await subscription_service.record_payment_failure(
        db, subscription_id, error_msg_str
    )

    # Send dunning email based on failure count
    if failure_result.get("subscription_id"):
        try:
            if dunning:
                await dunning.send_dunning_email(
                    subscription_id=failure_result["subscription_id"],
                    failed_count=failure_result["failed_count"],
                    error_message=error_msg_str,
                )
            else:
                logger.warning(
                    "Dunning service not configured — skipping dunning email "
                    "for subscription %s",
                    subscription_id,
                )
        except Exception as dunning_exc:
            # Dunning is fire-and-forget — never block webhook processing
            logger.exception(
                "Failed to send dunning email for subscription %s: %s",
                subscription_id,
                dunning_exc,
            )

    logger.info(
        "Subscription donation %s marked failed (subscription: %s, action: %s)",
        donation.id,
        subscription_id,
        failure_result.get("action", "unknown"),
    )
    return "failed"


async def _handle_subscription_updated(
    db: AsyncSession,
    data_object: Any,
) -> str:
    """Handle customer.subscription.updated: sync subscription status changes."""
    subscription_id = data_object.get("id")
    if not subscription_id:
        return "no_subscription_id"

    new_status = data_object.get("status", "")
    current_period_start = data_object.get("current_period_start")
    current_period_end = data_object.get("current_period_end")
    cancel_at_period_end = data_object.get("cancel_at_period_end")

    result = await subscription_service.handle_subscription_updated(
        db=db,
        stripe_subscription_id=subscription_id,
        new_status=new_status,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
    )

    return result


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

    # Mark donation as no longer recurring
    donation.is_recurring = False
    await db.flush()

    # Update the Subscription record
    await subscription_service.handle_subscription_updated(
        db=db,
        stripe_subscription_id=subscription_id,
        new_status="canceled",
    )

    logger.info(
        "Subscription %s cancelled, donation %s updated",
        subscription_id,
        donation.id,
    )
    return "cancelled"


async def _handle_payment_intent_processing(
    db: AsyncSession,
    payment_intent_id: str,
    sepa_notifier: "SepaNotificationService | None" = None,
) -> str:
    """Handle payment_intent.processing: SEPA payment accepted by bank, awaiting settlement.

    SEPA Direct Debit payments are asynchronous — the bank accepts the debit instruction
    but settlement takes 1-3 business days. This event fires when Stripe has submitted
    the debit to the banking network. The donation stays in 'pending' status until
    payment_intent.succeeded confirms the funds have settled.
    """
    donation = await _find_donation_by_payment_intent(db, payment_intent_id)
    if donation is None:
        logger.warning(
            "Webhook payment_intent.processing: no donation found for intent %s",
            payment_intent_id,
        )
        return "donation_not_found"

    # Donation remains pending — SEPA settlement is async (1-3 business days)
    logger.info(
        "SEPA payment %s processing for donation %s (awaiting bank settlement)",
        payment_intent_id,
        donation.id,
    )

    if sepa_notifier is not None:
        await sepa_notifier.notify_payment_processing(donation.id)

    return "processing"


async def _handle_setup_intent_succeeded(
    data_object: Any,
    sepa_notifier: "SepaNotificationService | None" = None,
) -> str:
    """Handle setup_intent.succeeded: SEPA mandate saved successfully.

    The donor's IBAN has been verified and a SEPA mandate has been created.
    The payment method can now be used for future off-session charges.
    We log the event for audit trail; no donation record is created here
    (mandates are stored in Stripe, charges happen via separate PaymentIntents).
    """
    setup_intent_id = data_object.get("id")
    customer_id = data_object.get("customer")
    payment_method_id = data_object.get("payment_method")
    donor_id = data_object.get("metadata", {}).get("donor_id")

    logger.info(
        "SEPA mandate saved: setup_intent=%s customer=%s payment_method=%s donor_id=%s",
        setup_intent_id,
        customer_id,
        payment_method_id,
        donor_id,
    )

    if sepa_notifier is not None and donor_id:
        await sepa_notifier.notify_mandate_saved(donor_id)

    return "mandate_saved"


async def _handle_setup_intent_failed(
    data_object: Any,
    sepa_notifier: "SepaNotificationService | None" = None,
) -> str:
    """Handle setup_intent.setup_failed: SEPA mandate setup failed.

    The bank rejected the IBAN or the setup could not be completed.
    Logged for audit trail; the donor must retry with a valid account.
    """
    setup_intent_id = data_object.get("id")
    customer_id = data_object.get("customer")
    last_error = data_object.get("last_setup_error", {})
    error_code = last_error.get("code") if last_error else None
    donor_id = data_object.get("metadata", {}).get("donor_id")

    logger.warning(
        "SEPA mandate setup failed: setup_intent=%s customer=%s error=%s donor_id=%s",
        setup_intent_id,
        customer_id,
        error_code,
        donor_id,
    )

    if sepa_notifier is not None and donor_id:
        await sepa_notifier.notify_payment_failed(donor_id=donor_id)

    return "mandate_failed"


async def _handle_mandate_updated(
    data_object: Any,
) -> str:
    """Handle mandate.updated: SEPA mandate status changed.

    Mandates can become inactive if the bank cancels them (e.g. account closed,
    donor revoked authorization). We log the new status for monitoring.
    SEPA mandate_id is stored in Stripe; this event signals when we should
    stop attempting charges against this payment method.
    """
    mandate_id = data_object.get("id")
    mandate_status = data_object.get("status")
    payment_method_id = data_object.get("payment_method")

    logger.info(
        "SEPA mandate updated: mandate=%s status=%s payment_method=%s",
        mandate_id,
        mandate_status,
        payment_method_id,
    )

    # Active → inactive transition: log at warning for ops visibility
    if mandate_status == "inactive":
        logger.warning(
            "SEPA mandate %s became inactive (payment_method: %s) — "
            "recurring charges will fail until mandate is re-authorized",
            mandate_id,
            payment_method_id,
        )
        return "mandate_inactive"

    return f"mandate_{mandate_status}"


def _extract_payment_intent_id_from_object(data_object: Any, event_type: str) -> str | None:
    """Extract the payment intent ID from a Stripe event's data.object.

    For payment_intent events, the object IS the payment intent (id field).
    For charge events, the payment_intent is a field on the charge object.
    data_object is a Stripe StripeObject which supports both [] and .get() access.
    """
    if event_type in (
        EVENT_PAYMENT_INTENT_SUCCEEDED,
        EVENT_PAYMENT_INTENT_FAILED,
        EVENT_PAYMENT_INTENT_PROCESSING,
    ):
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

    # Get event bus and SEPA notifier from app state
    event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)
    sepa_notifier: SepaNotificationService | None = getattr(
        request.app.state, "sepa_notifier", None
    )

    # Route to handler — subscription/invoice events use data_obj directly
    if event_type == EVENT_INVOICE_PAYMENT_SUCCEEDED:
        result = await _handle_invoice_payment_succeeded(db, data_obj, event_bus)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_INVOICE_PAYMENT_FAILED:
        dunning_svc: DunningService | None = getattr(request.app.state, "dunning_service", None)
        result = await _handle_invoice_payment_failed(db, data_obj, dunning=dunning_svc)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_SUBSCRIPTION_DELETED:
        result = await _handle_subscription_deleted(db, data_obj)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_SUBSCRIPTION_UPDATED:
        result = await _handle_subscription_updated(db, data_obj)
        return {"status": "processed", "event_type": event_type, "result": result}

    # SEPA-specific events that don't need a payment intent ID
    if event_type == EVENT_SETUP_INTENT_SUCCEEDED:
        result = await _handle_setup_intent_succeeded(data_obj, sepa_notifier)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_SETUP_INTENT_FAILED:
        result = await _handle_setup_intent_failed(data_obj, sepa_notifier)
        return {"status": "processed", "event_type": event_type, "result": result}
    if event_type == EVENT_MANDATE_UPDATED:
        result = await _handle_mandate_updated(data_obj)
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
    elif event_type == EVENT_PAYMENT_INTENT_PROCESSING:
        result = await _handle_payment_intent_processing(db, payment_intent_id, sepa_notifier)
    elif event_type == EVENT_CHARGE_REFUNDED:
        result = await _handle_charge_refunded(db, payment_intent_id)
    else:
        result = "unhandled"

    return {"status": "processed", "event_type": event_type, "result": result}
