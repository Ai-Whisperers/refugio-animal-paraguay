---
story: RAP-414
epic: EPIC-73
title: "Harden payment error handling (Stripe + Tigo)"
status: ready
priority: 1
points: 4
created: 2026-03-27
---

# RAP-414: Harden Payment Error Handling (Stripe + Tigo)

## Story

As a **backend developer**, I want **specific error handling for payment gateway failures** so that **donation and payment issues are reported clearly to users without exposing payment processing details**.

## Description

Payment endpoints (`src/api/donations.py`, `src/api/stripe_webhooks.py`) have minimal error handling for Stripe and Tigo Money API failures. These third-party errors must be caught, mapped to internal error codes, and returned with appropriate HTTP status codes.

## Acceptance Criteria

### Stripe Error Handling

**Given** Stripe API returns authentication error (invalid API key)
**When** payment endpoint attempts API call
**Then**
- [ ] `stripe.error.AuthenticationError` is caught (not bare Exception)
- [ ] Response is 503 Service Unavailable (not 500)
- [ ] Error message: `{"detail": "Payment service unavailable", "error_code": "PAYMENT_SERVICE_UNAVAILABLE"}`
- [ ] No API key exposed in error message
- [ ] Error is logged with severity=HIGH (ops needs to know)

**Pattern**:
```python
import stripe

try:
    charge = stripe.Charge.create(
        amount=amount_cents,
        currency="usd",
        source=token,
    )
except stripe.error.AuthenticationError as e:
    logger.error(
        "stripe_auth_error",
        error_code="PAYMENT_AUTH_FAILED",
        severity="HIGH",
    )
    raise APIException(
        detail="Payment service is temporarily unavailable",
        error_code="PAYMENT_SERVICE_UNAVAILABLE",
        status_code=503,
    )
```

**Given** Stripe returns card error (insufficient funds, declined card)
**When** payment endpoint attempts charge
**Then**
- [ ] `stripe.error.CardError` is caught
- [ ] Response is 402 Payment Required (not 500)
- [ ] Error message is user-friendly: `{"detail": "Card was declined. Please try another card.", "error_code": "CARD_DECLINED"}`
- [ ] Decline code is logged for debugging: "insufficient_funds", "lost_card", "stolen_card", etc.
- [ ] Declined cards are NOT retried automatically

**Pattern**:
```python
try:
    charge = stripe.Charge.create(...)
except stripe.error.CardError as e:
    # e.code is decline reason: "insufficient_funds", "lost_card", etc.
    decline_code = e.code
    user_message = {
        "insufficient_funds": "Insufficient funds. Please use a different card.",
        "lost_card": "Card reported as lost. Please use a different card.",
        "stolen_card": "Card reported as stolen. Please use a different card.",
        "expired_card": "Card has expired.",
        "processing_error": "Card processing error. Please try again.",
    }.get(decline_code, "Card was declined. Please try another card.")

    logger.warning(
        "stripe_card_declined",
        error_code="CARD_DECLINED",
        decline_code=decline_code,
        donor_id=donor_id,
    )

    raise APIException(
        detail=user_message,
        error_code="CARD_DECLINED",
        status_code=402,
    )
```

**Given** Stripe returns rate limit error (too many requests)
**When** donation endpoint is called during high traffic
**Then**
- [ ] `stripe.error.RateLimitError` is caught
- [ ] Response is 503 Service Unavailable with Retry-After header
- [ ] Error message: `{"detail": "Service temporarily overwhelmed. Please try again in 60 seconds.", "error_code": "RATE_LIMITED"}`
- [ ] Response header includes: `Retry-After: 60`

**Pattern**:
```python
try:
    charge = stripe.Charge.create(...)
except stripe.error.RateLimitError as e:
    logger.warning("stripe_rate_limit", backoff_seconds=60)
    raise APIException(
        detail="Service temporarily overwhelmed. Please try again in a few moments.",
        error_code="RATE_LIMITED",
        status_code=503,
        # Note: Response header is set by middleware or response handler
    )
```

**Given** Stripe returns invalid request error (bad parameters)
**When** donation endpoint is called with invalid data
**Then**
- [ ] `stripe.error.InvalidRequestError` is caught
- [ ] Response is 400 Bad Request
- [ ] Error message: `{"detail": "Invalid payment parameters", "error_code": "INVALID_PAYMENT_PARAMS"}`
- [ ] Stripe error details logged (not returned to client)

**Pattern**:
```python
try:
    charge = stripe.Charge.create(...)
except stripe.error.InvalidRequestError as e:
    logger.error(
        "stripe_invalid_request",
        error_code="INVALID_PAYMENT_PARAMS",
        stripe_error_message=str(e),
    )
    raise APIException(
        detail="Invalid payment parameters",
        error_code="INVALID_PAYMENT_PARAMS",
        status_code=400,
    )
```

**Given** Stripe API connection fails (network error, timeout)
**When** payment endpoint attempts API call
**Then**
- [ ] `stripe.error.APIConnectionError` is caught
- [ ] Response is 503 Service Unavailable
- [ ] Error message: `{"detail": "Payment service unavailable. Please try again.", "error_code": "PAYMENT_SERVICE_UNAVAILABLE"}`
- [ ] Error is retryable (client can retry safely)

**Pattern**:
```python
try:
    charge = stripe.Charge.create(...)
except stripe.error.APIConnectionError as e:
    logger.error(
        "stripe_connection_error",
        error_code="PAYMENT_SERVICE_UNAVAILABLE",
        retry=True,
    )
    raise APIException(
        detail="Payment service unavailable. Please try again.",
        error_code="PAYMENT_SERVICE_UNAVAILABLE",
        status_code=503,
    )
```

### Tigo Money Error Handling

**Given** Tigo Money API returns authentication error
**When** payment endpoint attempts transaction
**Then**
- [ ] Error is caught (TigoException or requests.RequestException)
- [ ] Response is 503 Service Unavailable
- [ ] Error message: `{"detail": "Payment provider unavailable", "error_code": "PAYMENT_SERVICE_UNAVAILABLE"}`
- [ ] No credentials exposed in error

**Pattern**:
```python
from requests.exceptions import RequestException

try:
    response = tigo_client.create_payment(
        phone=phone_number,
        amount=amount_pgn,
    )
except RequestException as e:
    if e.response.status_code == 401:
        logger.error(
            "tigo_auth_failed",
            error_code="PAYMENT_AUTH_FAILED",
            severity="HIGH",
        )
    raise APIException(
        detail="Payment provider temporarily unavailable",
        error_code="PAYMENT_SERVICE_UNAVAILABLE",
        status_code=503,
    )
```

**Given** Tigo Money returns insufficient balance error
**When** donor account doesn't have enough funds
**Then**
- [ ] Error is caught with specific error code
- [ ] Response is 402 Payment Required
- [ ] Error message: `{"detail": "Insufficient balance. Please try with a different amount.", "error_code": "INSUFFICIENT_BALANCE"}`

**Pattern**:
```python
try:
    response = tigo_client.create_payment(...)
    if response.get("error_code") == "INSUFFICIENT_BALANCE":
        raise APIException(
            detail="Insufficient balance. Please try a smaller amount.",
            error_code="INSUFFICIENT_BALANCE",
            status_code=402,
        )
except RequestException as e:
    # Handle connection errors
```

### Idempotency & Retry Safety

**Given** payment fails and donor retries
**When** second request is received with same donation data
**Then**
- [ ] Duplicate charge is prevented using idempotency key
- [ ] Both requests return same response
- [ ] No double-charging occurs

**Implementation**:
```python
from uuid import uuid4

@router.post("/donations")
async def create_donation(donation: CreateDonationSchema, db: Session):
    # Generate or use provided idempotency key
    idempotency_key = request.headers.get("X-Idempotency-Key", str(uuid4()))

    # Check if donation already processed with this key
    existing = await db.query(Donation).filter_by(
        idempotency_key=idempotency_key
    ).first()
    if existing:
        return existing  # Return cached result

    try:
        # Process payment
        charge = stripe.Charge.create(
            amount=donation.amount_cents,
            currency=donation.currency,
            idempotency_key=idempotency_key,  # Pass to Stripe
        )
        # Save donation with idempotency_key
        db_donation = Donation(
            **donation.model_dump(),
            idempotency_key=idempotency_key,
            stripe_charge_id=charge.id,
        )
        db.add(db_donation)
        await db.commit()
        return db_donation
    except StripeException as e:
        # Return error — client can retry with same key
        raise APIException(...)
```

### Webhook Error Handling

**Given** Stripe webhook received with invalid signature
**When** webhook handler verifies signature
**Then**
- [ ] `stripe.error.SignatureVerificationError` is caught
- [ ] Webhook is rejected (not processed)
- [ ] Response is 400 Bad Request
- [ ] Incident is logged (possible security issue)

**Pattern** (in webhook handler):
```python
from stripe.error import SignatureVerificationError

@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET,
        )
    except SignatureVerificationError as e:
        logger.error(
            "stripe_webhook_invalid_signature",
            error_code="WEBHOOK_VERIFICATION_FAILED",
            severity="HIGH",
        )
        raise APIException(
            detail="Invalid webhook signature",
            error_code="WEBHOOK_VERIFICATION_FAILED",
            status_code=400,
        )

    # Process webhook event
    if event.type == "charge.succeeded":
        ...
    elif event.type == "charge.failed":
        ...
```

**Given** webhook processing fails (e.g., database error)
**When** webhook handler encounters error
**Then**
- [ ] Webhook is re-queued by Stripe (not acked)
- [ ] Webhook handler returns 500 or 5xx (not 2xx)
- [ ] Stripe retries according to backoff policy
- [ ] Error is logged for debugging

**Pattern**:
```python
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    try:
        event = stripe.Webhook.construct_event(...)
        # Process event
        await process_webhook_event(event, db)
        return {"status": "success"}  # Return 200 OK
    except Exception as e:
        logger.error("webhook_processing_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        )  # Stripe will retry
```

### Payment Error Code Mapping

Create reference: `docs/PAYMENT_ERROR_CODES.md`

| Stripe Error | Status | Error Code | User Message |
|------|--------|-----------|--------------|
| CardError | 402 | CARD_DECLINED | Card was declined. Try another card. |
| AuthenticationError | 503 | PAYMENT_SERVICE_UNAVAILABLE | Service unavailable. |
| RateLimitError | 503 | RATE_LIMITED | Service busy. Try in 60s. |
| InvalidRequestError | 400 | INVALID_PAYMENT_PARAMS | Invalid payment parameters. |
| APIConnectionError | 503 | PAYMENT_SERVICE_UNAVAILABLE | Service unavailable. |

## Definition of Done

- [ ] All Stripe error types handled (CardError, AuthenticationError, RateLimitError, InvalidRequestError, APIConnectionError, SignatureVerificationError)
- [ ] All Tigo Money error types handled
- [ ] All payment endpoints (donations, payments) have try/except blocks
- [ ] Webhook handlers verify signature and handle failures
- [ ] Idempotency keys used to prevent double-charging
- [ ] No Stripe/Tigo error details exposed to clients
- [ ] All errors mapped to appropriate HTTP status codes
- [ ] All errors logged with structured context
- [ ] Error code mapping document created and maintained
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Modify
- `src/api/donations.py` — Donation creation with Stripe payment
- `src/api/stripe_webhooks.py` — Webhook handling
- `src/services/payment_service.py` — Payment processing logic (if exists)
- `src/api/error_handlers.py` — Global payment error handlers

### Stripe Libraries
```python
import stripe
from stripe.error import (
    CardError,
    RateLimitError,
    InvalidRequestError,
    AuthenticationError,
    APIConnectionError,
    SignatureVerificationError,
)
```

### Testing Payment Errors

Unit tests will verify error handling (see EPIC-72). Example:

```python
@patch("stripe.Charge.create")
def test_card_declined_returns_402(mock_create):
    mock_create.side_effect = stripe.error.CardError(
        message="Your card was declined",
        param="card",
        code="card_declined",
    )

    with pytest.raises(APIException) as exc_info:
        create_donation(donation_schema, db)

    assert exc_info.value.status_code == 402
    assert exc_info.value.error_code == "CARD_DECLINED"
```

---

*Last updated: 2026-03-27*
