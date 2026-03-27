"""Integration tests for SEPA notification hook-up in webhook handlers.

Verifies that the SepaNotificationService methods are called (or gracefully
skipped) when SEPA-specific Stripe webhook events are received.

Stripe signature verification is mocked. The SepaNotificationService is
mocked to avoid sending real emails and to assert call behaviour.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_sepa_notifications.py
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from src.app import app as _app

WEBHOOK_URL = "/webhooks/stripe"
WEBHOOK_SECRET = "whsec_test_secret_for_sepa_notifications"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stripe_event(event_type: str, data_object: dict) -> dict:
    """Build a minimal Stripe-like event dict."""
    return {
        "id": f"evt_{uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
        "api_version": "2023-10-16",
    }


async def _send_webhook(client: AsyncClient, event: dict) -> dict:
    """Post a webhook event with mocked signature verification. Returns JSON body."""
    with (
        patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET}),
        patch("stripe.Webhook.construct_event", return_value=event),
    ):
        response = await client.post(
            WEBHOOK_URL,
            content=json.dumps(event).encode(),
            headers={"stripe-signature": "t=123,v1=valid"},
        )
    assert response.status_code == 200, f"Unexpected status {response.status_code}: {response.text}"
    return response.json()


def _mock_sepa_notifier() -> MagicMock:
    """Return a MagicMock SepaNotificationService with async methods."""
    notifier = MagicMock()
    notifier.notify_mandate_saved = AsyncMock()
    notifier.notify_payment_processing = AsyncMock()
    notifier.notify_payment_failed = AsyncMock()
    return notifier


async def _create_donation_with_intent(
    client: AsyncClient, amount_cents: int, intent_id: str
) -> str:
    """Create a donation and assign a Stripe PaymentIntent ID. Returns donation_id."""
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
            await client.post(f"/donations/{donation_id}/stripe-intent")

    return donation_id


# ---------------------------------------------------------------------------
# setup_intent.succeeded — mandate saved notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setup_intent_succeeded_calls_notify_mandate_saved(
    client: AsyncClient,
) -> None:
    """setup_intent.succeeded triggers notify_mandate_saved with donor_id from metadata."""
    donor_id = str(uuid4())
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "setup_intent.succeeded",
        {
            "id": "seti_notify_test",
            "customer": "cus_test_eu",
            "payment_method": "pm_sepa_test",
            "metadata": {"donor_id": donor_id},
        },
    )

    # Inject mock notifier onto app state
    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "mandate_saved"
    notifier.notify_mandate_saved.assert_awaited_once_with(donor_id)
    notifier.notify_payment_processing.assert_not_awaited()
    notifier.notify_payment_failed.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setup_intent_succeeded_no_donor_id_skips_notification(
    client: AsyncClient,
) -> None:
    """setup_intent.succeeded without metadata.donor_id skips notification gracefully."""
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "setup_intent.succeeded",
        {
            "id": "seti_no_meta",
            "customer": "cus_no_meta",
            "payment_method": "pm_sepa_no_meta",
            "metadata": {},
        },
    )

    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "mandate_saved"
    notifier.notify_mandate_saved.assert_not_awaited()


# ---------------------------------------------------------------------------
# setup_intent.setup_failed — failure notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setup_intent_failed_calls_notify_payment_failed(
    client: AsyncClient,
) -> None:
    """setup_intent.setup_failed triggers notify_payment_failed with donor_id."""
    donor_id = str(uuid4())
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "setup_intent.setup_failed",
        {
            "id": "seti_fail_notify",
            "customer": "cus_fail",
            "last_setup_error": {"code": "account_closed"},
            "metadata": {"donor_id": donor_id},
        },
    )

    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "mandate_failed"
    notifier.notify_payment_failed.assert_awaited_once_with(donor_id=donor_id)
    notifier.notify_mandate_saved.assert_not_awaited()
    notifier.notify_payment_processing.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setup_intent_failed_no_donor_id_skips_notification(
    client: AsyncClient,
) -> None:
    """setup_intent.setup_failed without donor_id in metadata skips notification."""
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "setup_intent.setup_failed",
        {
            "id": "seti_fail_no_meta",
            "customer": "cus_fail_no_meta",
            "last_setup_error": {},
            "metadata": {},
        },
    )

    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "mandate_failed"
    notifier.notify_payment_failed.assert_not_awaited()


# ---------------------------------------------------------------------------
# payment_intent.processing — processing notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_payment_intent_processing_calls_notify_payment_processing(
    client: AsyncClient,
) -> None:
    """payment_intent.processing triggers notify_payment_processing with donation_id."""
    intent_id = f"pi_proc_notify_{uuid4().hex[:8]}"
    donation_id = await _create_donation_with_intent(client, 7500, intent_id)
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "payment_intent.processing",
        {"id": intent_id, "amount": 7500, "currency": "eur"},
    )

    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "processing"
    notifier.notify_payment_processing.assert_awaited_once()
    call_args = notifier.notify_payment_processing.call_args[0]
    # donation_id is a UUID; compare as strings for safety
    assert str(call_args[0]) == donation_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_payment_intent_processing_no_donation_skips_notification(
    client: AsyncClient,
) -> None:
    """payment_intent.processing with unknown intent skips notification gracefully."""
    notifier = _mock_sepa_notifier()

    event = _make_stripe_event(
        "payment_intent.processing",
        {"id": "pi_unknown_notify", "amount": 1000, "currency": "eur"},
    )

    _app.state.sepa_notifier = notifier

    body = await _send_webhook(client, event)

    assert body["result"] == "donation_not_found"
    notifier.notify_payment_processing.assert_not_awaited()


# ---------------------------------------------------------------------------
# Notifier absent from app state — graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setup_intent_succeeded_without_notifier_in_state(
    client: AsyncClient,
) -> None:
    """Webhook succeeds even when sepa_notifier is not set on app.state."""
    # Remove notifier from state if present
    if hasattr(_app.state, "sepa_notifier"):
        del _app.state.sepa_notifier

    event = _make_stripe_event(
        "setup_intent.succeeded",
        {
            "id": "seti_no_notifier",
            "customer": "cus_no_notifier",
            "payment_method": "pm_sepa",
            "metadata": {"donor_id": str(uuid4())},
        },
    )

    body = await _send_webhook(client, event)
    assert body["result"] == "mandate_saved"
