"""SEPA Direct Debit and recurring subscription endpoints.

Endpoints:
  POST /donations/{id}/sepa-intent                  -- create SEPA PaymentIntent for a pending donation
  POST /donations/sepa                              -- create donation + SEPA PaymentIntent in one step
  POST /donations/sepa/setup-intent                 -- create SEPA SetupIntent (save mandate for future charges)
  GET  /donations/sepa/payment-methods/{customer_id} -- list saved SEPA payment methods
  POST /donations/subscribe                         -- create recurring donation subscription
  DELETE /donations/subscriptions/{sub_id}          -- cancel a recurring subscription
"""

import logging
import os
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import (
    Donation,
    DonationStatus,
    Donor,
    PaymentMethod,
)
from src.db.session import get_db
from src.schemas.donation import (
    SepaIntentCreate,
    SepaIntentResponse,
    SepaPaymentMethodItem,
    SepaPaymentMethodsResponse,
    SepaSetupIntentCreate,
    SepaSetupIntentResponse,
    SubscriptionCancelResponse,
    SubscriptionCreate,
    SubscriptionResponse,
)
from src.schemas.error import PAYMENT_RESPONSES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/donations", tags=["donations", "sepa"], responses=PAYMENT_RESPONSES)


def _get_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )
    return key


async def _get_or_create_stripe_customer(
    donor: Donor,
) -> str:
    """Get existing Stripe customer or create one for the donor.

    Returns the Stripe customer ID.
    """
    # Search for existing customer by email
    customers = stripe.Customer.list(email=donor.email, limit=1)
    if customers.data:
        return customers.data[0].id

    # Create new customer
    customer = stripe.Customer.create(
        email=donor.email,
        name=donor.full_name,
        metadata={"donor_id": str(donor.id)},
    )
    return customer.id


@router.post("/sepa", response_model=SepaIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_sepa_donation(
    payload: SepaIntentCreate,
    db: AsyncSession = Depends(get_db),
) -> SepaIntentResponse:
    """Create a donation with SEPA Direct Debit payment method and return a PaymentIntent.

    SEPA Direct Debit is only available for EUR donations from EU bank accounts.
    The client_secret is used on the frontend to confirm the payment with Stripe Elements.
    """
    # Verify donor exists
    donor = await db.get(Donor, payload.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    stripe.api_key = _get_stripe_key()

    # Get or create Stripe customer for mandate tracking
    customer_id = await _get_or_create_stripe_customer(donor)

    # Create donation record
    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency="EUR",
        payment_method=PaymentMethod.SEPA_DEBIT.value,
        stripe_customer_id=customer_id,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)

    # Create PaymentIntent with SEPA Direct Debit payment method type
    intent = stripe.PaymentIntent.create(
        amount=payload.amount_cents,
        currency="eur",
        customer=customer_id,
        payment_method_types=["sepa_debit"],
        metadata={
            "donation_id": str(donation.id),
            "donor_id": str(payload.donor_id),
        },
    )

    if intent.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a client secret",
        )

    donation.stripe_payment_intent_id = intent.id
    await db.flush()

    return SepaIntentResponse(
        donation_id=donation.id,
        stripe_payment_intent_id=intent.id,
        client_secret=intent.client_secret,
        amount_cents=payload.amount_cents,
    )


@router.post(
    "/{donation_id}/sepa-intent",
    response_model=SepaIntentResponse,
)
async def create_sepa_intent_for_existing(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SepaIntentResponse:
    """Create a SEPA Direct Debit PaymentIntent for an existing pending donation.

    The donation must be in 'pending' status and have EUR currency.
    Requires the donation to have a donor_id (SEPA needs customer for mandate).
    """
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    if donation.status != DonationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create SEPA intent for donation with status '{donation.status}'",
        )

    if donation.currency != "EUR":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="SEPA Direct Debit is only available for EUR donations",
        )

    if donation.donor_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="SEPA Direct Debit requires a donor (cannot be anonymous)",
        )

    donor = await db.get(Donor, donation.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    stripe.api_key = _get_stripe_key()

    customer_id = await _get_or_create_stripe_customer(donor)
    donation.stripe_customer_id = customer_id
    donation.payment_method = PaymentMethod.SEPA_DEBIT.value

    intent = stripe.PaymentIntent.create(
        amount=donation.amount_cents,
        currency="eur",
        customer=customer_id,
        payment_method_types=["sepa_debit"],
        metadata={
            "donation_id": str(donation_id),
            "donor_id": str(donation.donor_id),
        },
    )

    if intent.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a client secret",
        )

    donation.stripe_payment_intent_id = intent.id
    await db.flush()

    return SepaIntentResponse(
        donation_id=donation_id,
        stripe_payment_intent_id=intent.id,
        client_secret=intent.client_secret,
        amount_cents=donation.amount_cents,
    )


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Create a recurring donation subscription via Stripe.

    Sets up a Stripe subscription with the specified interval (monthly or yearly).
    The donor must exist and a valid Stripe payment method ID must be provided.
    Stripe handles recurring billing automatically after setup.
    """
    donor = await db.get(Donor, payload.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    stripe.api_key = _get_stripe_key()

    # Get or create Stripe customer
    customer_id = await _get_or_create_stripe_customer(donor)

    # Attach payment method to customer
    stripe.PaymentMethod.attach(
        payload.payment_method_id,
        customer=customer_id,
    )

    # Set as default payment method
    stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payload.payment_method_id},
    )

    # Create a Stripe price for this subscription amount
    price = stripe.Price.create(
        unit_amount=payload.amount_cents,
        currency=payload.currency.value.lower(),
        recurring={"interval": payload.interval.value},
        product_data={"name": f"Refugio Animal Paraguay - {payload.interval.value}ly donation"},
    )

    # Create subscription
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price.id}],
        metadata={
            "donor_id": str(payload.donor_id),
        },
    )

    # Create donation record for the initial subscription
    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method=(
            PaymentMethod.SEPA_DEBIT.value
            if payload.payment_method_id.startswith("pm_sepa")
            else PaymentMethod.STRIPE.value
        ),
        stripe_subscription_id=subscription.id,
        stripe_customer_id=customer_id,
        is_recurring=True,
        recurring_interval=payload.interval.value,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)

    logger.info(
        "Created subscription %s for donor %s (%s %s/%s)",
        subscription.id,
        payload.donor_id,
        payload.amount_cents,
        payload.currency.value,
        payload.interval.value,
    )

    return SubscriptionResponse(
        donation_id=donation.id,
        stripe_subscription_id=subscription.id,
        stripe_customer_id=customer_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        interval=payload.interval,
        status=subscription.status,
    )


@router.delete(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionCancelResponse,
)
async def cancel_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionCancelResponse:
    """Cancel a recurring donation subscription.

    Cancels the Stripe subscription and updates the local donation record.
    The subscription will stop at the end of the current billing period.
    """
    # Verify donation with this subscription exists (most recent if multiple)
    stmt = (
        select(Donation)
        .where(Donation.stripe_subscription_id == subscription_id)
        .order_by(Donation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    donation = result.scalar_one_or_none()

    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    stripe.api_key = _get_stripe_key()

    # Cancel at period end (graceful cancellation)
    cancelled_sub = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True,
    )

    logger.info(
        "Cancelled subscription %s for donation %s",
        subscription_id,
        donation.id,
    )

    return SubscriptionCancelResponse(
        stripe_subscription_id=subscription_id,
        status=cancelled_sub.status,
    )


@router.post(
    "/sepa/setup-intent",
    response_model=SepaSetupIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sepa_setup_intent(
    payload: SepaSetupIntentCreate,
    db: AsyncSession = Depends(get_db),
) -> SepaSetupIntentResponse:
    """Create a SEPA Direct Debit SetupIntent to save a donor's bank account as a mandate.

    Use this endpoint before charging when you want to save the IBAN for future use.
    The returned client_secret is used on the frontend to confirm the SetupIntent with
    Stripe Elements (IbanElement or PaymentElement). Stripe will create a mandate after
    the donor confirms their IBAN.
    """
    donor = await db.get(Donor, payload.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    stripe.api_key = _get_stripe_key()

    customer_id = await _get_or_create_stripe_customer(donor)

    # SetupIntent with usage=off_session so the mandate allows future charges
    # without the donor being present (automated recurring donations)
    setup_intent = stripe.SetupIntent.create(
        customer=customer_id,
        payment_method_types=["sepa_debit"],
        usage="off_session",
        metadata={
            "donor_id": str(payload.donor_id),
        },
    )

    if setup_intent.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a client secret",
        )

    logger.info(
        "Created SEPA SetupIntent %s for donor %s (customer %s)",
        setup_intent.id,
        payload.donor_id,
        customer_id,
    )

    return SepaSetupIntentResponse(
        stripe_setup_intent_id=setup_intent.id,
        client_secret=setup_intent.client_secret,
        stripe_customer_id=customer_id,
        donor_id=payload.donor_id,
    )


@router.get(
    "/sepa/payment-methods/{customer_id}",
    response_model=SepaPaymentMethodsResponse,
)
async def list_sepa_payment_methods(
    customer_id: str,
) -> SepaPaymentMethodsResponse:
    """List saved SEPA Direct Debit payment methods for a Stripe customer.

    Returns the stored bank accounts (SEPA mandates) associated with the customer.
    Each item includes the last 4 digits of the IBAN, bank name, and mandate status.
    """
    stripe.api_key = _get_stripe_key()

    try:
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="sepa_debit",
        )
    except stripe.InvalidRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stripe customer not found: {customer_id}",
        ) from exc

    items: list[SepaPaymentMethodItem] = []
    for pm in payment_methods.data:
        sepa_debit = getattr(pm, "sepa_debit", None)
        if sepa_debit is None:
            continue

        # Retrieve mandate details if available
        mandate_id: str | None = None
        mandate_status: str | None = None
        if pm.get("mandate"):
            mandate_id = pm["mandate"]
            try:
                mandate = stripe.Mandate.retrieve(mandate_id)
                mandate_status = mandate.status
            except stripe.StripeError:
                mandate_status = "unknown"

        items.append(
            SepaPaymentMethodItem(
                payment_method_id=pm.id,
                bank_name=sepa_debit.get("bank_name"),
                last4=sepa_debit.get("last4"),
                country=sepa_debit.get("country"),
                mandate_id=mandate_id,
                mandate_status=mandate_status,
            )
        )

    return SepaPaymentMethodsResponse(
        stripe_customer_id=customer_id,
        payment_methods=items,
    )
