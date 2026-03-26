"""SEPA Direct Debit service.

Manages SEPA mandate lifecycle: create SetupIntent, confirm mandate,
handle activation/failure via webhooks, and revoke mandates.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donor
from src.db.models.sepa_mandate import MandateStatus, SepaMandate
from src.utils.iban import mask_iban, normalize_iban

logger = logging.getLogger(__name__)


async def create_sepa_setup(
    db: AsyncSession,
    donor_id: UUID,
    iban: str,
    amount_cents: int,
    interval: str,
    stripe_api_key: str,
) -> tuple[SepaMandate, str]:
    """Create a SEPA Direct Debit SetupIntent and mandate record.

    Returns (mandate, client_secret) for frontend to confirm the mandate.
    """
    # Verify donor exists
    donor = await db.get(Donor, donor_id)
    if donor is None:
        msg = f"Donor {donor_id} not found"
        raise ValueError(msg)

    normalized_iban = normalize_iban(iban)
    iban_last4 = normalized_iban[-4:]

    stripe.api_key = stripe_api_key

    # Create or retrieve Stripe Customer for this donor
    customer = stripe.Customer.create(
        email=donor.email,
        name=donor.full_name,
        metadata={
            "donor_id": str(donor_id),
            "source": "refugio_animal_paraguay",
        },
    )

    # Create SEPA payment method from IBAN
    payment_method = stripe.PaymentMethod.create(
        type="sepa_debit",
        sepa_debit={"iban": normalized_iban},
        billing_details={
            "email": donor.email,
            "name": donor.full_name,
        },
    )

    # Attach payment method to customer
    stripe.PaymentMethod.attach(payment_method.id, customer=customer.id)

    # Create SetupIntent to confirm the mandate
    setup_intent = stripe.SetupIntent.create(
        customer=customer.id,
        payment_method=payment_method.id,
        payment_method_types=["sepa_debit"],
        confirm=True,
        mandate_data={
            "customer_acceptance": {
                "type": "online",
                "online": {
                    "ip_address": "0.0.0.0",  # noqa: S104  # nosec B104 — Stripe placeholder, not a bind address
                    "user_agent": "refugio-api",
                },
            },
        },
        metadata={
            "donor_id": str(donor_id),
            "amount_cents": str(amount_cents),
            "interval": interval,
        },
    )

    # Create mandate record
    mandate = SepaMandate(
        donor_id=donor_id,
        stripe_customer_id=customer.id,
        stripe_setup_intent_id=setup_intent.id,
        stripe_payment_method_id=payment_method.id,
        iban_last4=iban_last4,
        status=MandateStatus.PENDING.value,
        amount_cents=amount_cents,
        interval=interval,
    )
    db.add(mandate)
    await db.flush()
    await db.refresh(mandate)

    logger.info(
        "SEPA mandate created: donor=%s iban=%s amount=%d interval=%s",
        donor_id,
        mask_iban(normalized_iban),
        amount_cents,
        interval,
    )

    client_secret = setup_intent.client_secret or ""
    return mandate, client_secret


async def activate_mandate(
    db: AsyncSession,
    stripe_setup_intent_id: str,
    stripe_mandate_id: str | None = None,
) -> SepaMandate | None:
    """Activate a mandate after SetupIntent succeeds (called from webhook).

    Returns the updated mandate, or None if not found.
    """
    stmt = select(SepaMandate).where(
        SepaMandate.stripe_setup_intent_id == stripe_setup_intent_id,
    )
    result = await db.execute(stmt)
    mandate = result.scalar_one_or_none()

    if mandate is None:
        logger.warning(
            "Mandate not found for setup_intent: %s",
            stripe_setup_intent_id,
        )
        return None

    if mandate.status == MandateStatus.ACTIVE.value:
        # Already active — idempotent
        return mandate

    mandate.status = MandateStatus.ACTIVE.value
    mandate.stripe_mandate_id = stripe_mandate_id
    mandate.activated_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(mandate)

    logger.info(
        "SEPA mandate activated: id=%s donor=%s",
        mandate.id,
        mandate.donor_id,
    )
    return mandate


async def fail_mandate(
    db: AsyncSession,
    stripe_setup_intent_id: str,
    failure_reason: str | None = None,
) -> SepaMandate | None:
    """Mark a mandate as failed (called from webhook on setup failure).

    Returns the updated mandate, or None if not found.
    """
    stmt = select(SepaMandate).where(
        SepaMandate.stripe_setup_intent_id == stripe_setup_intent_id,
    )
    result = await db.execute(stmt)
    mandate = result.scalar_one_or_none()

    if mandate is None:
        logger.warning(
            "Mandate not found for failed setup_intent: %s",
            stripe_setup_intent_id,
        )
        return None

    if mandate.status == MandateStatus.FAILED.value:
        # Already failed — idempotent
        return mandate

    mandate.status = MandateStatus.FAILED.value
    mandate.failure_reason = failure_reason
    await db.flush()
    await db.refresh(mandate)

    logger.info(
        "SEPA mandate failed: id=%s reason=%s",
        mandate.id,
        failure_reason,
    )
    return mandate


async def revoke_mandate(
    db: AsyncSession,
    mandate_id: UUID,
    stripe_api_key: str | None = None,
) -> SepaMandate | None:
    """Revoke a SEPA mandate. Cancels Stripe subscription if active.

    Returns the updated mandate, or None if not found.
    """
    mandate = await db.get(SepaMandate, mandate_id)
    if mandate is None:
        return None

    if mandate.status == MandateStatus.REVOKED.value:
        # Already revoked — idempotent
        return mandate

    # Cancel Stripe subscription if one exists
    if mandate.stripe_subscription_id and stripe_api_key:
        stripe.api_key = stripe_api_key
        try:
            stripe.Subscription.cancel(mandate.stripe_subscription_id)
        except stripe.StripeError as exc:
            logger.warning(
                "Failed to cancel Stripe subscription %s: %s",
                mandate.stripe_subscription_id,
                str(exc),
            )

    mandate.status = MandateStatus.REVOKED.value
    mandate.revoked_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(mandate)

    logger.info(
        "SEPA mandate revoked: id=%s donor=%s",
        mandate.id,
        mandate.donor_id,
    )
    return mandate


async def get_donor_mandates(
    db: AsyncSession,
    donor_id: UUID,
) -> list[SepaMandate]:
    """Get all SEPA mandates for a donor."""
    stmt = (
        select(SepaMandate)
        .where(SepaMandate.donor_id == donor_id)
        .order_by(SepaMandate.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
