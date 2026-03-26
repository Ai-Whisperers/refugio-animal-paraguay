"""Business logic for animal sponsorship management.

Handles sponsorship creation, lifecycle management, and Stripe Subscription
integration for recurring donor payments.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donor
from src.db.models.sponsorship import (
    TIER_AMOUNT_CENTS,
    Sponsorship,
    SponsorshipStatus,
)

logger = logging.getLogger(__name__)


async def create_sponsorship(
    db: AsyncSession,
    donor_id: UUID,
    animal_id: UUID,
    tier: str,
    currency: str = "USD",
    interval: str = "month",
    stripe_api_key: str | None = None,
) -> Sponsorship:
    """Create a new sponsorship with a Stripe Subscription.

    Args:
        db: Database session.
        donor_id: UUID of the sponsoring donor.
        animal_id: UUID of the animal being sponsored.
        tier: Sponsorship tier (bronze, silver, gold).
        currency: Payment currency (USD or EUR).
        interval: Billing interval (month or year).
        stripe_api_key: Stripe secret key.

    Returns:
        The created Sponsorship record.

    Raises:
        ValueError: If donor not found or already has active sponsorship for this animal.
    """
    # Verify donor exists
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise ValueError(f"Donor {donor_id} not found")

    # Check for existing active/paused sponsorship for this animal
    stmt = select(Sponsorship).where(
        Sponsorship.donor_id == donor_id,
        Sponsorship.animal_id == animal_id,
        Sponsorship.status.in_(
            [
                SponsorshipStatus.ACTIVE.value,
                SponsorshipStatus.PAUSED.value,
            ]
        ),
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise ValueError(
            f"Donor {donor_id} already has an active sponsorship for animal {animal_id}"
        )

    amount_cents = TIER_AMOUNT_CENTS[tier]

    # Create Stripe Customer + Subscription if key provided
    stripe_customer_id = None
    stripe_subscription_id = None
    stripe_price_id = None
    current_period_end = None

    if stripe_api_key:
        stripe.api_key = stripe_api_key

        # Create or retrieve Stripe customer
        customer = stripe.Customer.create(
            metadata={"donor_id": str(donor_id)},
        )
        stripe_customer_id = customer.id

        # Create a price for this tier
        price = stripe.Price.create(
            unit_amount=amount_cents,
            currency=currency.lower(),
            recurring=cast(Any, {"interval": interval}),
            product_data={
                "name": f"Animal Sponsorship - {tier.capitalize()}",
                "metadata": {"animal_id": str(animal_id), "tier": tier},
            },
        )
        stripe_price_id = price.id

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price.id}],
            metadata={
                "donor_id": str(donor_id),
                "animal_id": str(animal_id),
                "tier": tier,
            },
        )
        stripe_subscription_id = subscription.id
        current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=UTC)

    sponsorship = Sponsorship(
        donor_id=donor_id,
        animal_id=animal_id,
        tier=tier,
        amount_cents=amount_cents,
        currency=currency,
        interval=interval,
        status=SponsorshipStatus.ACTIVE.value,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_price_id=stripe_price_id,
        current_period_end=current_period_end,
    )
    db.add(sponsorship)
    await db.flush()

    logger.info(
        "Created %s sponsorship for donor %s -> animal %s",
        tier,
        donor_id,
        animal_id,
    )
    return sponsorship


async def update_sponsorship(
    db: AsyncSession,
    sponsorship_id: UUID,
    tier: str | None = None,
    action: str | None = None,
    stripe_api_key: str | None = None,
) -> Sponsorship | None:
    """Update a sponsorship: change tier, pause, or resume.

    Args:
        db: Database session.
        sponsorship_id: UUID of the sponsorship.
        tier: New tier (bronze, silver, gold) or None.
        action: Lifecycle action (pause, resume) or None.
        stripe_api_key: Stripe secret key.

    Returns:
        Updated Sponsorship or None if not found.
    """
    sponsorship = await db.get(Sponsorship, sponsorship_id)
    if sponsorship is None:
        return None

    if action == "pause" and sponsorship.status == SponsorshipStatus.ACTIVE.value:
        sponsorship.status = SponsorshipStatus.PAUSED.value
        sponsorship.paused_at = datetime.now(UTC)

        if stripe_api_key and sponsorship.stripe_subscription_id:
            stripe.api_key = stripe_api_key
            stripe.Subscription.modify(
                sponsorship.stripe_subscription_id,
                pause_collection={"behavior": "void"},
            )

        logger.info("Paused sponsorship %s", sponsorship_id)

    elif action == "resume" and sponsorship.status == SponsorshipStatus.PAUSED.value:
        sponsorship.status = SponsorshipStatus.ACTIVE.value
        sponsorship.paused_at = None

        if stripe_api_key and sponsorship.stripe_subscription_id:
            stripe.api_key = stripe_api_key
            stripe.Subscription.modify(
                sponsorship.stripe_subscription_id,
                pause_collection="",
            )

        logger.info("Resumed sponsorship %s", sponsorship_id)

    if tier and tier != sponsorship.tier:
        new_amount = TIER_AMOUNT_CENTS[tier]
        sponsorship.tier = tier
        sponsorship.amount_cents = new_amount

        if stripe_api_key and sponsorship.stripe_subscription_id:
            stripe.api_key = stripe_api_key
            # Create new price for the new tier
            price = stripe.Price.create(
                unit_amount=new_amount,
                currency=sponsorship.currency.lower(),
                recurring=cast(Any, {"interval": sponsorship.interval}),
                product_data={
                    "name": f"Animal Sponsorship - {tier.capitalize()}",
                    "metadata": {"animal_id": str(sponsorship.animal_id), "tier": tier},
                },
            )
            # Update subscription item
            sub = stripe.Subscription.retrieve(sponsorship.stripe_subscription_id)
            stripe.Subscription.modify(
                sponsorship.stripe_subscription_id,
                items=[{"id": sub["items"]["data"][0]["id"], "price": price.id}],
            )
            sponsorship.stripe_price_id = price.id

        logger.info("Changed sponsorship %s tier to %s", sponsorship_id, tier)

    await db.flush()
    return sponsorship


async def cancel_sponsorship(
    db: AsyncSession,
    sponsorship_id: UUID,
    stripe_api_key: str | None = None,
) -> Sponsorship | None:
    """Cancel a sponsorship.

    Args:
        db: Database session.
        sponsorship_id: UUID of the sponsorship.
        stripe_api_key: Stripe secret key.

    Returns:
        Cancelled Sponsorship or None if not found.
    """
    sponsorship = await db.get(Sponsorship, sponsorship_id)
    if sponsorship is None:
        return None

    # Idempotent: already cancelled
    if sponsorship.status == SponsorshipStatus.CANCELLED.value:
        return sponsorship

    sponsorship.status = SponsorshipStatus.CANCELLED.value
    sponsorship.cancelled_at = datetime.now(UTC)

    if stripe_api_key and sponsorship.stripe_subscription_id:
        stripe.api_key = stripe_api_key
        stripe.Subscription.cancel(sponsorship.stripe_subscription_id)

    await db.flush()

    logger.info("Cancelled sponsorship %s", sponsorship_id)
    return sponsorship


async def get_donor_sponsorships(
    db: AsyncSession,
    donor_id: UUID,
) -> list[Sponsorship]:
    """Get all sponsorships for a donor."""
    stmt = (
        select(Sponsorship)
        .where(Sponsorship.donor_id == donor_id)
        .order_by(Sponsorship.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_animal_sponsors(
    db: AsyncSession,
    animal_id: UUID,
) -> list[Sponsorship]:
    """Get all active sponsorships for an animal."""
    stmt = (
        select(Sponsorship)
        .where(
            Sponsorship.animal_id == animal_id,
            Sponsorship.status.in_(
                [
                    SponsorshipStatus.ACTIVE.value,
                    SponsorshipStatus.PAUSED.value,
                ]
            ),
        )
        .order_by(Sponsorship.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def handle_subscription_updated(
    db: AsyncSession,
    stripe_subscription_id: str,
    new_status: str,
    current_period_end: int | None = None,
) -> Sponsorship | None:
    """Handle Stripe subscription webhook updates.

    Maps Stripe subscription statuses to our sponsorship statuses.

    Args:
        db: Database session.
        stripe_subscription_id: Stripe subscription ID.
        new_status: Stripe subscription status string.
        current_period_end: Unix timestamp of current period end.

    Returns:
        Updated Sponsorship or None if not found.
    """
    stmt = select(Sponsorship).where(Sponsorship.stripe_subscription_id == stripe_subscription_id)
    result = await db.execute(stmt)
    sponsorship = result.scalar_one_or_none()
    if sponsorship is None:
        logger.warning(
            "Webhook: no sponsorship found for subscription %s",
            stripe_subscription_id,
        )
        return None

    # Map Stripe statuses to our statuses
    status_map: dict[str, str] = {
        "active": SponsorshipStatus.ACTIVE.value,
        "paused": SponsorshipStatus.PAUSED.value,
        "canceled": SponsorshipStatus.CANCELLED.value,
        "past_due": SponsorshipStatus.PAST_DUE.value,
    }

    mapped_status = status_map.get(new_status)
    if mapped_status and mapped_status != sponsorship.status:
        sponsorship.status = mapped_status

        if mapped_status == SponsorshipStatus.CANCELLED.value:
            sponsorship.cancelled_at = datetime.now(UTC)
        elif mapped_status == SponsorshipStatus.PAUSED.value:
            sponsorship.paused_at = datetime.now(UTC)

        logger.info(
            "Webhook: updated sponsorship %s status to %s",
            sponsorship.id,
            mapped_status,
        )

    if current_period_end is not None:
        sponsorship.current_period_end = datetime.fromtimestamp(current_period_end, tz=UTC)

    await db.flush()
    return sponsorship
