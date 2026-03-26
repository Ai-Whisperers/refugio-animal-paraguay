---
name: payment-patterns
description: Payment gateway integration, Stripe, SEPA, IBAN, EUR/PYG currency handling, idempotency, and donation receipt patterns for Refugio Animal Paraguay.
load-when: Implementing donation flows, payment processing, SEPA/EUR transfers, Stripe integration, IBAN handling, recurring donations, donation receipts
not-when: EU-specific GDPR/compliance rules (use eu-donation-patterns), REST API design (use rest-api-patterns), database schema (use postgresql-patterns)
---

# Skill: Payment & Donation Patterns

---

## Context: Refugio Animal Paraguay Payment Requirements

This project has dual payment contexts:
1. **Local (PYG)**: Paraguayan donors paying in Guaraní via local bank transfers or cash
2. **International/EU (EUR)**: Dutch/European donors via Stripe, SEPA Direct Debit, or IBAN transfers

Both must be handled with:
- GDPR compliance for EU donor data
- Proper currency handling (no floating point for money)
- Idempotent payment operations (no double charges)
- Audit trail for all transactions

---

## Money Handling — Never Use Float

```python
# ❌ NEVER — floating point arithmetic is imprecise for money
total = 10.50 + 0.10  # May be 10.600000000000001

# ✅ ALWAYS — use Decimal with fixed precision
from decimal import Decimal, ROUND_HALF_UP

def to_decimal(amount: float | str | int) -> Decimal:
    """Convert any amount to Decimal with 2dp precision."""
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# For Stripe: amounts are in cents (integer)
def to_stripe_amount(amount: Decimal, currency: str = "eur") -> int:
    """Convert Decimal EUR amount to Stripe cents integer."""
    # EUR, USD, GBP: multiply by 100 (2 decimal places)
    # PYG is a zero-decimal currency — do NOT multiply
    zero_decimal_currencies = {"pyg", "jpy", "krw"}
    if currency.lower() in zero_decimal_currencies:
        return int(amount)
    return int(amount * 100)

def from_stripe_amount(stripe_amount: int, currency: str = "eur") -> Decimal:
    """Convert Stripe cents back to Decimal."""
    zero_decimal_currencies = {"pyg", "jpy", "krw"}
    if currency.lower() in zero_decimal_currencies:
        return Decimal(stripe_amount)
    return Decimal(stripe_amount) / 100
```

---

## Stripe Integration

### Setup

```python
# src/core/stripe_client.py
import stripe
from src.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = "2024-06-20"  # Pin to a specific version
```

### Payment Intent (one-time donation)

```python
# src/services/donation.py
import stripe
from decimal import Decimal
from uuid import UUID

from src.schemas.donation import DonationCreate
from src.models.donation import Donation, DonationStatus


class DonationService:
    async def create_payment_intent(
        self,
        donor_id: UUID,
        amount: Decimal,
        currency: str,
        metadata: dict | None = None,
    ) -> stripe.PaymentIntent:
        """Create a Stripe PaymentIntent for a one-time donation."""
        return stripe.PaymentIntent.create(
            amount=to_stripe_amount(amount, currency),
            currency=currency.lower(),
            automatic_payment_methods={"enabled": True},
            metadata={
                "donor_id": str(donor_id),
                "source": "refugio_animal_paraguay",
                **(metadata or {}),
            },
            idempotency_key=f"donation-{donor_id}-{amount}-{currency}",
        )

    async def confirm_webhook(self, payload: bytes, sig_header: str) -> stripe.Event:
        """Verify webhook signature — never trust unverified events."""
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
```

### Webhook Handler

```python
# src/api/v1/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Header
import stripe

from src.services.donation import DonationService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
) -> dict:
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    match event["type"]:
        case "payment_intent.succeeded":
            await handle_payment_succeeded(event["data"]["object"])
        case "payment_intent.payment_failed":
            await handle_payment_failed(event["data"]["object"])
        case "customer.subscription.created":
            await handle_subscription_created(event["data"]["object"])
        case _:
            pass  # Ignore unhandled event types

    return {"received": True}
```

---

## SEPA Direct Debit (EU recurring donors)

```python
async def create_sepa_subscription(
    donor_email: str,
    iban: str,
    amount_eur: Decimal,
    interval: str = "month",  # "month" | "year"
) -> stripe.Subscription:
    """Set up recurring SEPA Direct Debit donation."""

    # 1. Create or retrieve Stripe Customer
    customer = stripe.Customer.create(
        email=donor_email,
        metadata={"source": "refugio_sepa_donation"},
    )

    # 2. Set up SEPA payment method
    payment_method = stripe.PaymentMethod.create(
        type="sepa_debit",
        sepa_debit={"iban": iban},
        billing_details={"email": donor_email},
    )
    stripe.PaymentMethod.attach(payment_method.id, customer=customer.id)

    # 3. Create Price (amount in cents, EUR)
    price = stripe.Price.create(
        unit_amount=to_stripe_amount(amount_eur, "eur"),
        currency="eur",
        recurring={"interval": interval},
        product_data={"name": "Refugio Animal Paraguay Monthly Donation"},
    )

    # 4. Create Subscription with SEPA mandate
    return stripe.Subscription.create(
        customer=customer.id,
        items=[{"price": price.id}],
        default_payment_method=payment_method.id,
        payment_settings={
            "payment_method_types": ["sepa_debit"],
            "save_default_payment_method": "on_subscription",
        },
        metadata={"donor_email": donor_email},
    )
```

---

## IBAN Validation

```python
import re


IBAN_PATTERNS = {
    "DE": re.compile(r"^DE\d{2}[0-9A-Z]{18}$"),    # Germany — 22 chars
    "NL": re.compile(r"^NL\d{2}[A-Z]{4}\d{10}$"),  # Netherlands — 18 chars
    "ES": re.compile(r"^ES\d{2}\d{20}$"),            # Spain — 24 chars
    # Add more EU countries as needed
}


def validate_iban(iban: str) -> bool:
    """
    Validate IBAN format.

    This checks format only — for production, use a dedicated library
    like `python-stdnum` which also validates the checksum.
    """
    iban = iban.replace(" ", "").upper()
    country_code = iban[:2]
    pattern = IBAN_PATTERNS.get(country_code)
    if pattern is None:
        # Unknown country — accept if overall format looks valid (18-34 chars)
        return bool(re.match(r"^[A-Z]{2}\d{2}[0-9A-Z]{14,30}$", iban))
    return bool(pattern.match(iban))


def mask_iban(iban: str) -> str:
    """Mask IBAN for logging/display — never log full IBAN."""
    iban = iban.replace(" ", "").upper()
    if len(iban) < 8:
        return "****"
    return f"{iban[:4]}****{iban[-4:]}"
```

---

## Database Schema for Donations

```sql
-- Donations table — supports both EUR and PYG, one-time and recurring
CREATE TABLE donations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id        UUID NOT NULL REFERENCES donors(id),
    amount          NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency        VARCHAR(3) NOT NULL CHECK (currency IN ('EUR', 'PYG', 'USD')),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'refunded')),
    payment_method  VARCHAR(30),            -- 'stripe_card', 'sepa_debit', 'bank_transfer', 'cash'
    stripe_pi_id    VARCHAR(100) UNIQUE,    -- Stripe PaymentIntent ID (nullable for cash)
    stripe_sub_id   VARCHAR(100),           -- Stripe Subscription ID (for recurring)
    is_recurring    BOOLEAN NOT NULL DEFAULT FALSE,
    recurring_interval VARCHAR(10),         -- 'month', 'year'
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Idempotency: prevent duplicate Stripe events from creating duplicate records
CREATE UNIQUE INDEX idx_donations_stripe_pi ON donations(stripe_pi_id)
    WHERE stripe_pi_id IS NOT NULL;

-- Query pattern: donor donation history
CREATE INDEX idx_donations_donor_created ON donations(donor_id, created_at DESC);
```

---

## Donation Receipt (GDPR + Tax)

EU donors typically need receipts for tax purposes. Always generate and store:

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from uuid import UUID


@dataclass
class DonationReceipt:
    receipt_id: str               # RAP-YYYY-NNNNNN
    donor_name: str
    donor_address: str            # Required for EU tax receipts
    amount: Decimal
    currency: str
    donation_date: date
    organization_name: str = "Refugio Animal Paraguay"
    organization_tax_id: str = ""  # Fill when registered


def generate_receipt_number(donation_id: UUID, year: int) -> str:
    """Generate human-readable receipt number."""
    short_id = str(donation_id).replace("-", "")[:6].upper()
    return f"RAP-{year}-{short_id}"
```

---

## Idempotency — Prevent Double Charges

```python
from functools import wraps
import hashlib


def idempotent_payment(func):
    """
    Decorator: hash the payment parameters to create an idempotency key.
    Stripe will return the same PaymentIntent if called twice with the same key.
    """
    @wraps(func)
    async def wrapper(self, donor_id, amount, currency, *args, **kwargs):
        key_data = f"{donor_id}-{amount}-{currency}"
        idempotency_key = hashlib.sha256(key_data.encode()).hexdigest()[:32]
        return await func(self, donor_id, amount, currency,
                          *args, idempotency_key=idempotency_key, **kwargs)
    return wrapper
```

---

## Currency Conversion Display

For the UI — always show both currencies when relevant:

```python
from decimal import Decimal


EUR_TO_PYG_RATE = Decimal("7800")  # Example rate — fetch from ECB or BCRA API


def format_amount_bilingual(amount: Decimal, source_currency: str) -> str:
    """Format amount with equivalent in other currency."""
    if source_currency == "EUR":
        pyg_equivalent = (amount * EUR_TO_PYG_RATE).quantize(Decimal("1"))
        return f"€{amount:,.2f} EUR (~₲{pyg_equivalent:,} PYG)"
    elif source_currency == "PYG":
        eur_equivalent = (amount / EUR_TO_PYG_RATE).quantize(Decimal("0.01"))
        return f"₲{amount:,.0f} PYG (~€{eur_equivalent:,.2f} EUR)"
    return f"{amount} {source_currency}"
```

---

## Error Handling for Payment Failures

```python
import stripe
import logging

logger = logging.getLogger(__name__)


async def safe_charge(payment_intent_id: str) -> bool:
    """Confirm a payment intent with proper Stripe error handling."""
    try:
        stripe.PaymentIntent.confirm(payment_intent_id)
        return True
    except stripe.error.CardError as e:
        # Card was declined — not a system error, inform the user
        logger.info("Card declined for payment %s: %s", payment_intent_id, e.user_message)
        raise DonationDeclinedError(reason=e.user_message)
    except stripe.error.RateLimitError:
        logger.warning("Stripe rate limit hit — retry with backoff")
        raise
    except stripe.error.InvalidRequestError as e:
        # Programming error — log as error, don't expose to user
        logger.error("Invalid Stripe request for %s: %s", payment_intent_id, str(e))
        raise
    except stripe.error.StripeError as e:
        logger.error("Stripe error for %s: %s", payment_intent_id, str(e))
        raise
```

---

## Security Checklist for Payments

- [ ] `STRIPE_SECRET_KEY` in env var, never hardcoded
- [ ] `STRIPE_WEBHOOK_SECRET` used to verify all webhook events
- [ ] IBAN numbers masked in all logs (`mask_iban()`)
- [ ] Donor PII (email, address) not logged at INFO level
- [ ] All amounts stored as `NUMERIC(12,2)` — never `FLOAT`
- [ ] Idempotency keys on all charge operations
- [ ] Webhook endpoint only accepts POST from Stripe IP ranges
- [ ] Payment failure reasons never exposed raw to end users
