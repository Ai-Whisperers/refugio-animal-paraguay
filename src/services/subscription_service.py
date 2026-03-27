"""Service layer for recurring donation subscription management.

Handles Stripe subscription lifecycle operations: create, cancel, update,
pause, resume. All Stripe API calls are isolated here to keep the router thin.
"""

import logging
import os
from datetime import UTC, datetime

import stripe
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donation, Donor, PaymentMethod
from src.db.models.subscription import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

# Maximum number of failed payments before auto-cancellation
MAX_FAILED_PAYMENT_ATTEMPTS = 3


def _get_stripe_key() -> str:
    """Retrieve Stripe secret key from environment."""
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise ValueError("STRIPE_SECRET_KEY not configured")
    return key


async def get_or_create_stripe_customer(donor: Donor) -> str:
    """Get existing Stripe customer or create one for the donor.

    Returns the Stripe customer ID.
    """
    customers = stripe.Customer.list(email=donor.email, limit=1)
    if customers.data:
        return customers.data[0].id

    customer = stripe.Customer.create(
        email=donor.email,
        name=donor.full_name,
        metadata={"donor_id": str(donor.id)},
    )
    return customer.id


async def create_subscription(
    db: AsyncSession,
    donor: Donor,
    amount_cents: int,
    currency: str,
    interval: str,
    payment_method_id: str,
    notes: str | None = None,
) -> Subscription:
    """Create a Stripe subscription and local record.

    Steps:
    1. Get or create Stripe customer
    2. Attach payment method to customer
    3. Create Stripe price (inline, per-amount)
    4. Create Stripe subscription
    5. Create local Subscription record
    6. Create initial Donation record linked to subscription
    """
    stripe.api_key = _get_stripe_key()

    # Step 1: Get or create customer
    customer_id = await get_or_create_stripe_customer(donor)

    # Step 2: Attach payment method
    stripe.PaymentMethod.attach(
        payment_method_id,
        customer=customer_id,
    )
    stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )

    # Step 3: Create price
    interval_label = "monthly" if interval == "month" else "yearly"
    price = stripe.Price.create(
        unit_amount=amount_cents,
        currency=currency.lower(),
        recurring={"interval": interval},
        product_data={
            "name": f"Refugio Animal Paraguay - {interval_label} donation",
        },
    )

    # Step 4: Create Stripe subscription
    stripe_sub = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price.id}],
        metadata={
            "donor_id": str(donor.id),
        },
        payment_settings={
            "payment_method_types": ["card", "sepa_debit"],
            "save_default_payment_method": "on_subscription",
        },
    )

    # Step 5: Create local subscription record
    subscription = Subscription(
        donor_id=donor.id,
        stripe_subscription_id=stripe_sub.id,
        stripe_customer_id=customer_id,
        stripe_price_id=price.id,
        stripe_payment_method_id=payment_method_id,
        amount_cents=amount_cents,
        currency=currency,
        interval=interval,
        status=stripe_sub.status,
        current_period_start=_timestamp_to_datetime(stripe_sub.current_period_start),
        current_period_end=_timestamp_to_datetime(stripe_sub.current_period_end),
        notes=notes,
    )
    db.add(subscription)
    await db.flush()
    await db.refresh(subscription)

    # Step 6: Create initial donation record
    is_sepa = payment_method_id.startswith("pm_sepa")
    donation = Donation(
        donor_id=donor.id,
        amount_cents=amount_cents,
        currency=currency,
        payment_method=PaymentMethod.SEPA_DEBIT.value if is_sepa else PaymentMethod.STRIPE.value,
        stripe_subscription_id=stripe_sub.id,
        stripe_customer_id=customer_id,
        is_recurring=True,
        recurring_interval=interval,
        notes=notes,
    )
    db.add(donation)
    await db.flush()

    logger.info(
        "Created subscription %s for donor %s (%d %s/%s)",
        stripe_sub.id,
        donor.id,
        amount_cents,
        currency,
        interval,
    )

    return subscription


async def cancel_subscription(
    db: AsyncSession,
    subscription: Subscription,
    cancel_immediately: bool = False,
    reason: str | None = None,
) -> Subscription:
    """Cancel a Stripe subscription.

    Args:
        cancel_immediately: If True, cancel now. If False, cancel at period end.
        reason: Optional cancellation reason for records.
    """
    stripe.api_key = _get_stripe_key()

    if cancel_immediately:
        stripe.Subscription.cancel(subscription.stripe_subscription_id)
        subscription.status = SubscriptionStatus.CANCELED.value
        subscription.canceled_at = datetime.now(UTC)
    else:
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        subscription.cancel_at_period_end = True

    if reason:
        existing_notes = subscription.notes or ""
        cancellation_note = f"\n[Cancellation reason]: {reason}"
        subscription.notes = existing_notes + cancellation_note

    await db.flush()
    await db.refresh(subscription)

    logger.info(
        "Cancelled subscription %s (immediate=%s, reason=%s)",
        subscription.stripe_subscription_id,
        cancel_immediately,
        reason,
    )

    return subscription


async def update_subscription_amount(
    db: AsyncSession,
    subscription: Subscription,
    new_amount_cents: int,
) -> Subscription:
    """Update subscription amount by creating a new Stripe price and swapping it.

    Stripe does not allow modifying a price amount directly — instead we create
    a new price and update the subscription item to use it.
    """
    stripe.api_key = _get_stripe_key()

    interval_label = "monthly" if subscription.interval == "month" else "yearly"
    new_price = stripe.Price.create(
        unit_amount=new_amount_cents,
        currency=subscription.currency.lower(),
        recurring={"interval": subscription.interval},
        product_data={
            "name": f"Refugio Animal Paraguay - {interval_label} donation",
        },
    )

    # Get subscription items to find the current one
    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    if stripe_sub.get("items") and stripe_sub["items"].get("data"):
        item_id = stripe_sub["items"]["data"][0]["id"]
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{"id": item_id, "price": new_price.id}],
            proration_behavior="none",
        )

    subscription.amount_cents = new_amount_cents
    subscription.stripe_price_id = new_price.id
    await db.flush()
    await db.refresh(subscription)

    logger.info(
        "Updated subscription %s amount to %d cents",
        subscription.stripe_subscription_id,
        new_amount_cents,
    )

    return subscription


async def pause_subscription(
    db: AsyncSession,
    subscription: Subscription,
) -> Subscription:
    """Pause a subscription by setting pause_collection on Stripe."""
    stripe.api_key = _get_stripe_key()

    stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        pause_collection={"behavior": "void"},
    )

    subscription.status = SubscriptionStatus.PAUSED.value
    await db.flush()
    await db.refresh(subscription)

    logger.info("Paused subscription %s", subscription.stripe_subscription_id)

    return subscription


async def resume_subscription(
    db: AsyncSession,
    subscription: Subscription,
) -> Subscription:
    """Resume a paused subscription."""
    stripe.api_key = _get_stripe_key()

    stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        pause_collection="",
    )

    subscription.status = SubscriptionStatus.ACTIVE.value
    await db.flush()
    await db.refresh(subscription)

    logger.info("Resumed subscription %s", subscription.stripe_subscription_id)

    return subscription


async def handle_subscription_updated(
    db: AsyncSession,
    stripe_subscription_id: str,
    new_status: str,
    current_period_start: int | None = None,
    current_period_end: int | None = None,
    cancel_at_period_end: bool | None = None,
) -> str:
    """Handle subscription status updates from Stripe webhooks.

    Returns a result string for webhook response.
    """
    stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if subscription is None:
        logger.warning(
            "Webhook: no local subscription found for %s",
            stripe_subscription_id,
        )
        return "subscription_not_found"

    subscription.status = new_status
    if current_period_start is not None:
        subscription.current_period_start = _timestamp_to_datetime(current_period_start)
    if current_period_end is not None:
        subscription.current_period_end = _timestamp_to_datetime(current_period_end)
    if cancel_at_period_end is not None:
        subscription.cancel_at_period_end = cancel_at_period_end

    if new_status == SubscriptionStatus.CANCELED.value and subscription.canceled_at is None:
        subscription.canceled_at = datetime.now(UTC)

    await db.flush()

    logger.info(
        "Updated subscription %s status to %s",
        stripe_subscription_id,
        new_status,
    )

    return f"updated_{new_status}"


async def record_payment_failure(
    db: AsyncSession,
    stripe_subscription_id: str,
    error_message: str | None = None,
) -> dict:
    """Record a payment failure for a subscription.

    Increments the failed_payment_count and stores the error message.
    If the count reaches MAX_FAILED_PAYMENT_ATTEMPTS, cancels the
    subscription on Stripe and locally.

    Returns a dict with:
      - action: "payment_failure_recorded", "subscription_cancelled", or
                "subscription_not_found"
      - subscription_id: local UUID (if found)
      - failed_count: updated count (if found)
      - donor_id: UUID of the donor (if found)
    """
    stmt = select(Subscription).where(
        Subscription.stripe_subscription_id == stripe_subscription_id
    )
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if subscription is None:
        return {"action": "subscription_not_found"}

    subscription.failed_payment_count += 1
    subscription.last_payment_error = error_message
    subscription.status = SubscriptionStatus.PAST_DUE.value

    action = "payment_failure_recorded"

    # Auto-cancel after max failures
    if subscription.failed_payment_count >= MAX_FAILED_PAYMENT_ATTEMPTS:
        try:
            stripe.api_key = _get_stripe_key()
            stripe.Subscription.cancel(stripe_subscription_id)
        except Exception as cancel_exc:
            logger.error(
                "Failed to cancel Stripe subscription %s after %d failures: %s",
                stripe_subscription_id,
                subscription.failed_payment_count,
                cancel_exc,
            )
        subscription.status = SubscriptionStatus.CANCELED.value
        subscription.canceled_at = datetime.now(UTC)
        existing_notes = subscription.notes or ""
        subscription.notes = (
            existing_notes
            + f"\n[Auto-cancelled]: Exceeded {MAX_FAILED_PAYMENT_ATTEMPTS} "
            f"failed payment attempts"
        )
        action = "subscription_cancelled"

    await db.flush()

    logger.warning(
        "Subscription %s payment failed (attempt %d/%d): %s — action: %s",
        stripe_subscription_id,
        subscription.failed_payment_count,
        MAX_FAILED_PAYMENT_ATTEMPTS,
        error_message,
        action,
    )

    return {
        "action": action,
        "subscription_id": str(subscription.id),
        "failed_count": subscription.failed_payment_count,
        "donor_id": str(subscription.donor_id),
    }


async def get_subscription_stats(
    db: AsyncSession,
) -> dict:
    """Get aggregated subscription statistics."""
    # Count by status
    status_counts = await db.execute(
        select(
            Subscription.status,
            func.count(Subscription.id).label("count"),
        ).group_by(Subscription.status)
    )
    counts_by_status: dict[str, int] = {}
    for row in status_counts:
        counts_by_status[row.status] = row.count

    # Monthly recurring revenue (active monthly subs)
    monthly_result = await db.execute(
        select(func.coalesce(func.sum(Subscription.amount_cents), 0)).where(
            Subscription.status == SubscriptionStatus.ACTIVE.value,
            Subscription.interval == "month",
        )
    )
    monthly_recurring = monthly_result.scalar() or 0

    # Yearly recurring (active yearly subs)
    yearly_result = await db.execute(
        select(func.coalesce(func.sum(Subscription.amount_cents), 0)).where(
            Subscription.status == SubscriptionStatus.ACTIVE.value,
            Subscription.interval == "year",
        )
    )
    yearly_recurring = yearly_result.scalar() or 0

    return {
        "total_active": counts_by_status.get(SubscriptionStatus.ACTIVE.value, 0),
        "total_paused": counts_by_status.get(SubscriptionStatus.PAUSED.value, 0),
        "total_canceled": counts_by_status.get(SubscriptionStatus.CANCELED.value, 0),
        "total_past_due": counts_by_status.get(SubscriptionStatus.PAST_DUE.value, 0),
        "monthly_recurring_cents": monthly_recurring,
        "yearly_recurring_cents": yearly_recurring,
    }


def _timestamp_to_datetime(ts: int | None) -> datetime | None:
    """Convert a Unix timestamp to a timezone-aware datetime."""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC)
