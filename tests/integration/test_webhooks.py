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
import stripe as stripe_lib
from httpx import AsyncClient, Response

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEBHOOK_URL = "/webhooks/stripe"
WEBHOOK_SECRET = "whsec_test_secret_for_integration_tests"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stripe_event(event_type: str, data_object: dict) -> dict:
    """Build a Stripe-like event dict for testing."""
    return {
        "id": f"evt_{uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
        "api_version": "2023-10-16",
    }


async def _create_donation_with_intent(
    client: AsyncClient, amount_cents: int, intent_id: str
) -> str:
    """Create a donation and assign a stripe payment intent ID. Returns donation_id."""
    resp = await client.post(
        "/donations",
        json={"amount_cents": amount_cents, "currency": "EUR", "payment_method": "stripe"},
    )
    assert resp.status_code == 201
    donation_id = resp.json()["id"]

    with patch("src.api.donations.stripe") as mock_stripe:
        mock_intent = MagicMock()
        mock_intent.id = intent_id
        mock_intent.client_secret = f"{intent_id}_secret"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
            intent_resp = await client.post(f"/donations/{donation_id}/stripe-intent")
            assert intent_resp.status_code == 200

    return donation_id


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
# POST /webhooks/stripe — signature verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_returns_400_for_invalid_signature(client: AsyncClient) -> None:
    """Invalid Stripe signature should return 400."""
    with (
        patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET}),
        patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe_lib.SignatureVerificationError("bad sig", "sig_header"),
        ),
    ):
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
    # Default Settings has stripe_webhook_secret="" so this returns 503
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
    intent_id = f"pi_succ_{uuid4().hex[:8]}"
    donation_id = await _create_donation_with_intent(client, 5000, intent_id)

    event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": intent_id, "amount": 5000, "currency": "eur"},
    )
    response = await _send_webhook(client, event)

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
    intent_id = f"pi_fail_{uuid4().hex[:8]}"
    donation_id = await _create_donation_with_intent(client, 3000, intent_id)

    event = _make_stripe_event(
        "payment_intent.payment_failed",
        {"id": intent_id, "amount": 3000, "currency": "eur"},
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "failed"

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
    intent_id = f"pi_ref_{uuid4().hex[:8]}"
    donation_id = await _create_donation_with_intent(client, 7500, intent_id)

    # First complete the donation
    succeeded_event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": intent_id, "amount": 7500, "currency": "eur"},
    )
    await _send_webhook(client, succeeded_event)

    # Then refund
    refund_event = _make_stripe_event(
        "charge.refunded",
        {"id": f"ch_{uuid4().hex[:8]}", "payment_intent": intent_id, "amount_refunded": 7500},
    )
    response = await _send_webhook(client, refund_event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "refunded"

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
    response = await _send_webhook(client, event)

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
    """Sending the same succeeded event twice returns 'already_completed' on second call."""
    intent_id = f"pi_idem_{uuid4().hex[:8]}"
    await _create_donation_with_intent(client, 2000, intent_id)

    event = _make_stripe_event(
        "payment_intent.succeeded",
        {"id": intent_id, "amount": 2000, "currency": "eur"},
    )

    resp1 = await _send_webhook(client, event)
    assert resp1.json()["result"] == "completed"

    resp2 = await _send_webhook(client, event)
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
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    assert response.json()["result"] == "donation_not_found"


# ---------------------------------------------------------------------------
# SEPA-specific webhook events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_payment_intent_processing(client: AsyncClient) -> None:
    """payment_intent.processing keeps donation in pending state (SEPA async)."""
    intent_id = f"pi_sepa_proc_{uuid4().hex[:8]}"
    await _create_donation_with_intent(client, 5000, intent_id)

    event = _make_stripe_event(
        "payment_intent.processing",
        {"id": intent_id, "amount": 5000, "currency": "eur"},
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "processing"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_payment_intent_processing_unknown_donation(
    client: AsyncClient,
) -> None:
    """payment_intent.processing with unknown intent returns donation_not_found."""
    event = _make_stripe_event(
        "payment_intent.processing",
        {"id": "pi_unknown_sepa", "amount": 1000, "currency": "eur"},
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    assert response.json()["result"] == "donation_not_found"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_setup_intent_succeeded(client: AsyncClient) -> None:
    """setup_intent.succeeded returns 200 with 'mandate_saved'."""
    event = _make_stripe_event(
        "setup_intent.succeeded",
        {
            "id": "seti_test_ok",
            "customer": "cus_test_nl",
            "payment_method": "pm_sepa_test",
            "metadata": {"donor_id": str(uuid4())},
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "mandate_saved"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_setup_intent_failed(client: AsyncClient) -> None:
    """setup_intent.setup_failed returns 200 with 'mandate_failed'."""
    event = _make_stripe_event(
        "setup_intent.setup_failed",
        {
            "id": "seti_test_fail",
            "customer": "cus_test_nl",
            "last_setup_error": {"code": "invalid_account_number"},
            "metadata": {"donor_id": str(uuid4())},
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "mandate_failed"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_mandate_updated_active(client: AsyncClient) -> None:
    """mandate.updated with active status returns 200 with 'mandate_active'."""
    event = _make_stripe_event(
        "mandate.updated",
        {
            "id": "mandate_test_active",
            "status": "active",
            "payment_method": "pm_sepa_test",
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "mandate_active"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_mandate_updated_inactive(client: AsyncClient) -> None:
    """mandate.updated with inactive status returns 200 with 'mandate_inactive'."""
    event = _make_stripe_event(
        "mandate.updated",
        {
            "id": "mandate_test_inactive",
            "status": "inactive",
            "payment_method": "pm_sepa_test",
        },
    )
    response = await _send_webhook(client, event)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["result"] == "mandate_inactive"
