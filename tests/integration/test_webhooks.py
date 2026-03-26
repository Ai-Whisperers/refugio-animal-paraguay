"""Integration tests for Stripe webhook endpoint.

Tests the POST /webhooks/stripe endpoint with a live database.
Stripe signature verification is mocked since we cannot generate real signatures.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_webhooks.py
"""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEBHOOK_URL = "/webhooks/stripe"
WEBHOOK_SECRET = "whsec_test_secret_for_integration_tests"


def _make_stripe_event(event_type: str, data_object: dict) -> dict:
    """Build a Stripe-like event dict for testing."""
    return {
        "id": f"evt_{uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
        "api_version": "2023-10-16",
    }


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — signature verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_returns_400_for_invalid_signature(client: AsyncClient) -> None:
    """Invalid Stripe signature should return 400."""
    with patch("src.api.webhooks.get_settings") as mock_settings:
        settings = MagicMock()
        settings.stripe_webhook_secret = WEBHOOK_SECRET
        mock_settings.return_value = settings

        response = await client.post(
            WEBHOOK_URL,
            content=b'{"type": "payment_intent.succeeded"}',
            headers={"stripe-signature": "t=123,v1=bad_signature"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_returns_503_when_secret_not_configured(client: AsyncClient) -> None:
    """Missing webhook secret should return 503."""
    with patch("src.api.webhooks.get_settings") as mock_settings:
        settings = MagicMock()
        settings.stripe_webhook_secret = ""
        mock_settings.return_value = settings

        response = await client.post(
            WEBHOOK_URL,
            content=b'{"type": "payment_intent.succeeded"}',
            headers={"stripe-signature": "t=123,v1=sig"},
        )
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — payment_intent.succeeded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_payment_succeeded_updates_donation(client: AsyncClient) -> None:
    """Successful payment webhook marks donation as completed."""
    # Create a donation first
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 5000, "currency": "EUR", "payment_method": "stripe"},
    )
    assert donation_resp.status_code == 201
    donation = donation_resp.json()
    donation_id = donation["id"]

    # Simulate Stripe PaymentIntent creation (set the intent ID on the donation)
    with patch("src.api.donations.stripe") as mock_stripe:
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_succeeded"
        mock_intent.client_secret = "pi_test_succeeded_secret_123"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
            intent_resp = await client.post(f"/donations/{donation_id}/stripe-intent")
            assert intent_resp.status_code == 200

    # Now send the webhook event (mock signature verification)
    event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": "pi_test_succeeded", "amount": 5000, "currency": "eur"},
    )

    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            response = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "completed"

    # Verify donation status was updated
    get_resp = await client.get(f"/donations/{donation_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — payment_intent.payment_failed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_payment_failed_updates_donation(client: AsyncClient) -> None:
    """Failed payment webhook marks donation as failed."""
    # Create a donation
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 3000, "currency": "EUR", "payment_method": "stripe"},
    )
    assert donation_resp.status_code == 201
    donation = donation_resp.json()
    donation_id = donation["id"]

    # Set stripe intent ID
    with patch("src.api.donations.stripe") as mock_stripe:
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_failed"
        mock_intent.client_secret = "pi_test_failed_secret_123"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
            intent_resp = await client.post(f"/donations/{donation_id}/stripe-intent")
            assert intent_resp.status_code == 200

    # Send failed webhook
    event = _make_stripe_event(
        "payment_intent.payment_failed",
        {"id": "pi_test_failed", "amount": 3000, "currency": "eur"},
    )

    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            response = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "failed"

    # Verify donation status
    get_resp = await client.get(f"/donations/{donation_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — charge.refunded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_charge_refunded_updates_donation(client: AsyncClient) -> None:
    """Refund webhook marks donation as refunded."""
    # Create and complete a donation first
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 7500, "currency": "EUR", "payment_method": "stripe"},
    )
    assert donation_resp.status_code == 201
    donation = donation_resp.json()
    donation_id = donation["id"]

    # Set stripe intent ID
    with patch("src.api.donations.stripe") as mock_stripe:
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_refund"
        mock_intent.client_secret = "pi_test_refund_secret_123"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
            intent_resp = await client.post(f"/donations/{donation_id}/stripe-intent")
            assert intent_resp.status_code == 200

    # First complete the donation via succeeded webhook
    succeeded_event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": "pi_test_refund", "amount": 7500, "currency": "eur"},
    )
    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = succeeded_event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings
            await client.post(
                WEBHOOK_URL,
                content=json.dumps(succeeded_event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    # Now send refund webhook
    refund_event = _make_stripe_event(
        "charge.refunded",
        {
            "id": "ch_test_refund",
            "payment_intent": "pi_test_refund",
            "amount_refunded": 7500,
        },
    )

    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = refund_event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            response = await client.post(
                WEBHOOK_URL,
                content=json.dumps(refund_event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "refunded"

    # Verify donation status
    get_resp = await client.get(f"/donations/{donation_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "refunded"


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — unhandled event types
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_unhandled_event_returns_skipped(client: AsyncClient) -> None:
    """Unhandled event types return 200 with 'skipped' status."""
    event = _make_stripe_event("customer.created", {"id": "cus_123"})

    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            response = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["event_type"] == "customer.created"


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_idempotent_duplicate_succeeded(client: AsyncClient) -> None:
    """Sending the same succeeded event twice returns 'already_completed'."""
    # Create a donation
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 2000, "currency": "EUR", "payment_method": "stripe"},
    )
    assert donation_resp.status_code == 201
    donation_id = donation_resp.json()["id"]

    # Set stripe intent ID
    with patch("src.api.donations.stripe") as mock_stripe:
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_idempotent"
        mock_intent.client_secret = "pi_test_idempotent_secret"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
            await client.post(f"/donations/{donation_id}/stripe-intent")

    event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": "pi_test_idempotent", "amount": 2000, "currency": "eur"},
    )

    # First call
    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            resp1 = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )
            assert resp1.json()["result"] == "completed"

    # Second call (duplicate)
    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            resp2 = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )
            assert resp2.json()["result"] == "already_completed"


# ---------------------------------------------------------------------------
# POST /webhooks/stripe — donation not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_donation_not_found_returns_processed(client: AsyncClient) -> None:
    """Webhook for unknown payment intent returns 200 with 'donation_not_found'."""
    event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": "pi_does_not_exist", "amount": 1000, "currency": "eur"},
    )

    with patch("src.api.webhooks.stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = event
        with patch("src.api.webhooks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.stripe_webhook_secret = WEBHOOK_SECRET
            mock_settings.return_value = settings

            response = await client.post(
                WEBHOOK_URL,
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=123,v1=valid"},
            )

    assert response.status_code == 200
    assert response.json()["result"] == "donation_not_found"
