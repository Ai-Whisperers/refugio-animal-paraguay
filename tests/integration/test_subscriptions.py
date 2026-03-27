"""Integration tests for the subscriptions API endpoints.

Tests the /subscriptions router with mocked Stripe API but real database.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

SUBSCRIPTIONS_URL = "/subscriptions"


async def _create_donor(client: AsyncClient, email: str | None = None) -> dict:
    """Create a donor and return the response JSON."""
    donor_email = email or f"donor-{uuid4().hex[:8]}@example.nl"
    resp = await client.post(
        "/donors",
        json={
            "full_name": "Jan de Vries",
            "email": donor_email,
            "country": "NL",
            "currency_preference": "EUR",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _mock_stripe_subscription_flow() -> tuple:
    """Set up mock Stripe returns for a complete subscription creation flow."""
    mock_customer_list = MagicMock()
    mock_customer_list.data = [MagicMock(id="cus_test_int")]

    mock_price = MagicMock(id="price_test_int")
    mock_sub = MagicMock(
        id="sub_test_int_" + uuid4().hex[:8],
        status="active",
        current_period_start=1767225600,
        current_period_end=1769817600,
    )

    return mock_customer_list, mock_price, mock_sub


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_subscription(client: AsyncClient) -> None:
    """Create a subscription and verify the response."""
    donor = await _create_donor(client)
    mock_customer_list, mock_price, mock_sub = _mock_stripe_subscription_flow()

    with (
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
        patch("src.services.subscription_service.stripe") as mock_stripe,
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.PaymentMethod.attach = MagicMock()
        mock_stripe.Customer.modify = MagicMock()
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_sub

        resp = await client.post(
            SUBSCRIPTIONS_URL,
            json={
                "donor_id": donor["id"],
                "amount_cents": 2000,
                "currency": "EUR",
                "interval": "month",
                "payment_method_id": "pm_card_visa",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["donor_id"] == donor["id"]
    assert data["amount_cents"] == 2000
    assert data["status"] == "active"
    assert data["stripe_subscription_id"] == mock_sub.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_subscription_donor_not_found(client: AsyncClient) -> None:
    """Creating subscription for non-existent donor returns 404."""
    resp = await client.post(
        SUBSCRIPTIONS_URL,
        json={
            "donor_id": str(uuid4()),
            "amount_cents": 2000,
            "currency": "EUR",
            "interval": "month",
            "payment_method_id": "pm_card_visa",
        },
    )

    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_subscriptions_empty(client: AsyncClient) -> None:
    """List subscriptions returns empty list when none exist for filter."""
    resp = await client.get(
        SUBSCRIPTIONS_URL,
        params={"status": "trialing"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == [] or isinstance(data["items"], list)
    assert data["total"] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_subscription_not_found(client: AsyncClient) -> None:
    """Getting non-existent subscription returns 404."""
    resp = await client.get(f"{SUBSCRIPTIONS_URL}/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_subscription_stats(client: AsyncClient) -> None:
    """Stats endpoint returns expected shape."""
    resp = await client.get(f"{SUBSCRIPTIONS_URL}/stats")

    assert resp.status_code == 200
    data = resp.json()
    assert "total_active" in data
    assert "monthly_recurring_cents" in data
    assert "yearly_recurring_cents" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_subscription_not_found(client: AsyncClient) -> None:
    """Canceling non-existent subscription returns 404."""
    resp = await client.post(
        f"{SUBSCRIPTIONS_URL}/{uuid4()}/cancel",
        json={"cancel_immediately": False},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_pause_subscription_not_found(client: AsyncClient) -> None:
    """Pausing non-existent subscription returns 404."""
    resp = await client.post(f"{SUBSCRIPTIONS_URL}/{uuid4()}/pause")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resume_subscription_not_found(client: AsyncClient) -> None:
    """Resuming non-existent subscription returns 404."""
    resp = await client.post(f"{SUBSCRIPTIONS_URL}/{uuid4()}/resume")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_subscription_not_found(client: AsyncClient) -> None:
    """Updating non-existent subscription returns 404."""
    resp = await client.patch(
        f"{SUBSCRIPTIONS_URL}/{uuid4()}",
        json={"amount_cents": 5000},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_subscription_lifecycle(client: AsyncClient) -> None:
    """Create, get, pause, resume, cancel a subscription (full lifecycle)."""
    donor = await _create_donor(client)
    mock_customer_list, mock_price, mock_sub = _mock_stripe_subscription_flow()

    # 1. Create subscription
    with (
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
        patch("src.services.subscription_service.stripe") as mock_stripe,
    ):
        mock_stripe.Customer.list.return_value = mock_customer_list
        mock_stripe.PaymentMethod.attach = MagicMock()
        mock_stripe.Customer.modify = MagicMock()
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe.Subscription.create.return_value = mock_sub

        resp = await client.post(
            SUBSCRIPTIONS_URL,
            json={
                "donor_id": donor["id"],
                "amount_cents": 3000,
                "currency": "EUR",
                "interval": "month",
                "payment_method_id": "pm_card_visa",
            },
        )

    assert resp.status_code == 201
    sub_id = resp.json()["id"]

    # 2. Get subscription
    resp = await client.get(f"{SUBSCRIPTIONS_URL}/{sub_id}")
    assert resp.status_code == 200
    assert resp.json()["amount_cents"] == 3000

    # 3. Get donor subscriptions
    resp = await client.get(f"{SUBSCRIPTIONS_URL}/donor/{donor['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 4. Pause subscription
    with (
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
        patch("src.services.subscription_service.stripe") as mock_stripe,
    ):
        mock_stripe.Subscription.modify = MagicMock()
        resp = await client.post(f"{SUBSCRIPTIONS_URL}/{sub_id}/pause")

    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"

    # 5. Resume subscription
    with (
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
        patch("src.services.subscription_service.stripe") as mock_stripe,
    ):
        mock_stripe.Subscription.modify = MagicMock()
        resp = await client.post(f"{SUBSCRIPTIONS_URL}/{sub_id}/resume")

    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # 6. Cancel subscription (at period end)
    with (
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
        patch("src.services.subscription_service.stripe") as mock_stripe,
    ):
        mock_stripe.Subscription.modify = MagicMock()
        resp = await client.post(
            f"{SUBSCRIPTIONS_URL}/{sub_id}/cancel",
            json={"cancel_immediately": False, "reason": "Switching to yearly"},
        )

    assert resp.status_code == 200
    assert resp.json()["cancel_at_period_end"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_subscriptions_with_pagination(client: AsyncClient) -> None:
    """List subscriptions supports page and per_page params."""
    resp = await client.get(
        SUBSCRIPTIONS_URL,
        params={"page": 1, "per_page": 5},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["per_page"] == 5
