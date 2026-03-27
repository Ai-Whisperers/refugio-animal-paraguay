"""Integration tests for SEPA Direct Debit and subscription endpoints.

Tests POST /donations/sepa, POST /donations/{id}/sepa-intent,
POST /donations/subscribe, DELETE /donations/subscriptions/{id},
and subscription-related webhook events.

Requires a live PostgreSQL instance (refugio_dev).
"""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, Response

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEBHOOK_URL = "/webhooks/stripe"
WEBHOOK_SECRET = "whsec_test_secret_for_integration_tests"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_donor(client: AsyncClient, email: str | None = None) -> dict:
    """Create a donor and return the response JSON."""
    donor_email = email or f"donor-{uuid4().hex[:8]}@example.nl"
    resp = await client.post(
        "/donors",
        json={
            "full_name": "Test Donor",
            "email": donor_email,
            "country": "NL",
            "currency_preference": "EUR",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _make_stripe_event(event_type: str, data_object: dict) -> dict:
    """Build a Stripe-like event dict for testing."""
    return {
        "id": f"evt_{uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
        "api_version": "2023-10-16",
    }


async def _send_webhook(client: AsyncClient, event: dict) -> Response:
    """Send a webhook event with mocked Stripe signature verification."""
    with (
        patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET}),
        patch("stripe.Webhook.construct_event", return_value=event),
    ):
        return await client.post(
            WEBHOOK_URL,
            content=json.dumps(event).encode(),
            headers={"stripe-signature": "t=123,v1=valid"},
        )


# ---------------------------------------------------------------------------
# POST /donations/sepa — create SEPA donation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_donation(client: AsyncClient) -> None:
    """Create a SEPA donation returns PaymentIntent with client_secret."""
    donor = await _create_donor(client)

    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_test_sepa"

    mock_intent = MagicMock()
    mock_intent.id = "pi_sepa_test123"
    mock_intent.client_secret = "pi_sepa_test123_secret"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        resp = await client.post(
            "/donations/sepa",
            json={
                "donor_id": donor["id"],
                "amount_cents": 5000,
                "notes": "SEPA test donation",
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["stripe_payment_intent_id"] == "pi_sepa_test123"
    assert body["client_secret"] == "pi_sepa_test123_secret"
    assert body["amount_cents"] == 5000
    assert body["currency"] == "EUR"

    # Verify PaymentIntent was created with sepa_debit method type
    call_kwargs = mock_stripe.PaymentIntent.create.call_args
    assert call_kwargs.kwargs["payment_method_types"] == ["sepa_debit"]
    assert call_kwargs.kwargs["customer"] == "cus_test_sepa"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_donation_donor_not_found(client: AsyncClient) -> None:
    """SEPA donation with nonexistent donor returns 404."""
    resp = await client.post(
        "/donations/sepa",
        json={
            "donor_id": str(uuid4()),
            "amount_cents": 5000,
        },
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /donations/{id}/sepa-intent — SEPA intent for existing donation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_intent_for_existing_donation(client: AsyncClient) -> None:
    """Create SEPA intent for an existing pending EUR donation."""
    donor = await _create_donor(client)

    # Create a pending donation first
    donation_resp = await client.post(
        "/donations",
        json={
            "donor_id": donor["id"],
            "amount_cents": 3000,
            "currency": "EUR",
            "payment_method": "stripe",
        },
    )
    assert donation_resp.status_code == 201
    donation_id = donation_resp.json()["id"]

    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_test_existing"

    mock_intent = MagicMock()
    mock_intent.id = "pi_sepa_existing"
    mock_intent.client_secret = "pi_sepa_existing_secret"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        resp = await client.post(f"/donations/{donation_id}/sepa-intent")

    assert resp.status_code == 200
    body = resp.json()
    assert body["stripe_payment_intent_id"] == "pi_sepa_existing"
    assert body["amount_cents"] == 3000


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sepa_intent_rejects_non_eur_donation(client: AsyncClient) -> None:
    """SEPA intent for PYG donation returns 422."""
    donor = await _create_donor(client)
    donation_resp = await client.post(
        "/donations",
        json={
            "donor_id": donor["id"],
            "amount_cents": 500000,
            "currency": "PYG",
            "payment_method": "cash",
        },
    )
    # Cash donations are created immediately, and PYG doesn't go through SEPA
    # Just test that the sepa-intent endpoint rejects non-EUR
    if donation_resp.status_code == 201:
        donation_id = donation_resp.json()["id"]
        resp = await client.post(f"/donations/{donation_id}/sepa-intent")
        assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sepa_intent_rejects_anonymous_donation(client: AsyncClient) -> None:
    """SEPA intent for anonymous donation (no donor_id) returns 422."""
    donation_resp = await client.post(
        "/donations",
        json={
            "amount_cents": 2000,
            "currency": "EUR",
            "payment_method": "stripe",
        },
    )
    assert donation_resp.status_code == 201
    donation_id = donation_resp.json()["id"]

    resp = await client.post(f"/donations/{donation_id}/sepa-intent")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /donations/subscribe — create subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_subscription(client: AsyncClient) -> None:
    """Create a recurring donation subscription."""
    donor = await _create_donor(client)

    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_test_sub"

    mock_price = MagicMock()
    mock_price.id = "price_test123"

    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    mock_subscription.status = "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.Customer.modify.return_value = None
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_subscription

        resp = await client.post(
            "/donations/subscribe",
            json={
                "donor_id": donor["id"],
                "amount_cents": 2000,
                "currency": "EUR",
                "interval": "month",
                "payment_method_id": "pm_test_sepa",
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["stripe_subscription_id"] == "sub_test123"
    assert body["stripe_customer_id"] == "cus_test_sub"
    assert body["amount_cents"] == 2000
    assert body["interval"] == "month"
    assert body["status"] == "active"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_subscription_donor_not_found(client: AsyncClient) -> None:
    """Subscription with nonexistent donor returns 404."""
    resp = await client.post(
        "/donations/subscribe",
        json={
            "donor_id": str(uuid4()),
            "amount_cents": 2000,
            "payment_method_id": "pm_test",
        },
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /donations/subscriptions/{sub_id} — cancel subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_subscription(client: AsyncClient) -> None:
    """Cancel an existing subscription."""
    donor = await _create_donor(client)

    # First create a subscription
    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_cancel_test"

    mock_price = MagicMock()
    mock_price.id = "price_cancel"

    mock_subscription = MagicMock()
    mock_subscription.id = "sub_cancel_test"
    mock_subscription.status = "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.Customer.modify.return_value = None
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_subscription

        await client.post(
            "/donations/subscribe",
            json={
                "donor_id": donor["id"],
                "amount_cents": 2000,
                "payment_method_id": "pm_test",
            },
        )

    # Now cancel it
    mock_cancelled = MagicMock()
    mock_cancelled.status = "active"  # cancel_at_period_end keeps status "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Subscription.modify.return_value = mock_cancelled

        resp = await client.delete("/donations/subscriptions/sub_cancel_test")

    assert resp.status_code == 200
    body = resp.json()
    assert body["stripe_subscription_id"] == "sub_cancel_test"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_nonexistent_subscription(client: AsyncClient) -> None:
    """Cancel a subscription that doesn't exist returns 404."""
    resp = await client.delete("/donations/subscriptions/sub_does_not_exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Webhook: invoice.payment_succeeded (subscription renewal)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_invoice_payment_succeeded_for_subscription(
    client: AsyncClient,
) -> None:
    """Invoice payment succeeded webhook marks subscription donation completed."""
    donor = await _create_donor(client)

    # Create subscription
    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_webhook_test"
    mock_price = MagicMock()
    mock_price.id = "price_wh"
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_wh_test"
    mock_subscription.status = "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.Customer.modify.return_value = None
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_subscription

        sub_resp = await client.post(
            "/donations/subscribe",
            json={
                "donor_id": donor["id"],
                "amount_cents": 2000,
                "payment_method_id": "pm_test",
            },
        )
        assert sub_resp.status_code == 201

    # Send invoice.payment_succeeded webhook
    event = _make_stripe_event(
        "invoice.payment_succeeded",
        {
            "id": f"in_{uuid4().hex[:8]}",
            "subscription": "sub_wh_test",
            "amount_paid": 2000,
            "currency": "eur",
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "completed"


# ---------------------------------------------------------------------------
# Webhook: invoice.payment_failed (subscription failure)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_invoice_payment_failed_for_subscription(
    client: AsyncClient,
) -> None:
    """Invoice payment failed webhook marks subscription donation as failed."""
    donor = await _create_donor(client)

    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_fail_test"
    mock_price = MagicMock()
    mock_price.id = "price_fail"
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_fail_test"
    mock_subscription.status = "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.Customer.modify.return_value = None
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_subscription

        await client.post(
            "/donations/subscribe",
            json={
                "donor_id": donor["id"],
                "amount_cents": 1500,
                "payment_method_id": "pm_test",
            },
        )

    event = _make_stripe_event(
        "invoice.payment_failed",
        {
            "id": f"in_{uuid4().hex[:8]}",
            "subscription": "sub_fail_test",
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "failed"


# ---------------------------------------------------------------------------
# Webhook: customer.subscription.deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_subscription_deleted(client: AsyncClient) -> None:
    """Subscription deleted webhook marks donation as non-recurring."""
    donor = await _create_donor(client)

    mock_customer_list = MagicMock()
    mock_customer_list.data = []
    mock_customer = MagicMock()
    mock_customer.id = "cus_del_test"
    mock_price = MagicMock()
    mock_price.id = "price_del"
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_del_test"
    mock_subscription.status = "active"

    with (
        patch("src.api.sepa.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.Customer.modify.return_value = None
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_subscription

        await client.post(
            "/donations/subscribe",
            json={
                "donor_id": donor["id"],
                "amount_cents": 3000,
                "payment_method_id": "pm_test",
            },
        )

    event = _make_stripe_event(
        "customer.subscription.deleted",
        {"id": "sub_del_test", "status": "canceled"},
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "cancelled"
