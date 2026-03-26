"""Integration tests for donors and donations endpoints.

Covers:
  POST /donors                        — create donor profile
  GET  /donors/{id}                   — get donor (staff only)
  POST /donations                     — create donation record
  POST /donations/{id}/stripe-intent  — create Stripe PaymentIntent (mocked)
  GET  /donations                     — list donations (staff only)
  GET  /donations/{id}                — get donation (staff only)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_donations.py
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# POST /donors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donor_returns_201(client: AsyncClient) -> None:
    email = f"donor-{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/donors",
        json={"full_name": "Maria García", "email": email},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Maria García"
    assert body["email"] == email
    assert body["currency_preference"] == "EUR"
    assert body["country"] is None
    assert body["gdpr_consent_at"] is None
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donor_with_all_fields(client: AsyncClient) -> None:
    email = f"donor-{uuid4().hex[:8]}@example.nl"
    response = await client.post(
        "/donors",
        json={
            "full_name": "Pieter van der Berg",
            "email": email,
            "country": "NL",
            "currency_preference": "EUR",
            "gdpr_consent_at": "2026-01-15T10:00:00Z",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["country"] == "NL"
    assert body["currency_preference"] == "EUR"
    assert body["gdpr_consent_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donor_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = f"donor-{uuid4().hex[:8]}@example.com"
    await client.post("/donors", json={"full_name": "First", "email": email})
    response = await client.post("/donors", json={"full_name": "Second", "email": email})
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donor_invalid_email_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/donors",
        json={"full_name": "Bad Email", "email": "not-an-email"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donor_empty_name_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/donors",
        json={"full_name": "", "email": f"donor-{uuid4().hex[:8]}@example.com"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /donors/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donor_returns_donor(client: AsyncClient) -> None:
    email = f"donor-{uuid4().hex[:8]}@example.com"
    create_resp = await client.post("/donors", json={"full_name": "Test Donor", "email": email})
    donor_id = create_resp.json()["id"]

    response = await client.get(f"/donors/{donor_id}")
    assert response.status_code == 200
    assert response.json()["id"] == donor_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donor_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/donors/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donor_requires_auth(client: AsyncClient) -> None:
    from httpx import ASGITransport
    from httpx import AsyncClient as PlainClient
    from src.app import app

    email = f"donor-{uuid4().hex[:8]}@example.com"
    create_resp = await client.post("/donors", json={"full_name": "Auth Test", "email": email})
    donor_id = create_resp.json()["id"]

    async with PlainClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        response = await anon.get(f"/donors/{donor_id}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /donations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_returns_201(client: AsyncClient) -> None:
    response = await client.post(
        "/donations",
        json={"amount_cents": 1000, "currency": "EUR"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["amount_cents"] == 1000
    assert body["currency"] == "EUR"
    assert body["status"] == "pending"
    assert body["donor_id"] is None
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_with_donor(client: AsyncClient) -> None:
    email = f"donor-{uuid4().hex[:8]}@example.com"
    donor_resp = await client.post("/donors", json={"full_name": "Linked Donor", "email": email})
    donor_id = donor_resp.json()["id"]

    response = await client.post(
        "/donations",
        json={"amount_cents": 5000, "currency": "EUR", "donor_id": donor_id},
    )
    assert response.status_code == 201
    assert response.json()["donor_id"] == donor_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/donations",
        json={"amount_cents": 1000, "currency": "EUR", "donor_id": str(uuid4())},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_zero_amount_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/donations",
        json={"amount_cents": 0, "currency": "EUR"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_negative_amount_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/donations",
        json={"amount_cents": -100, "currency": "EUR"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_donation_pyg_cash(client: AsyncClient) -> None:
    response = await client.post(
        "/donations",
        json={"amount_cents": 500000, "currency": "PYG", "payment_method": "cash"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "PYG"
    assert body["payment_method"] == "cash"


# ---------------------------------------------------------------------------
# POST /donations/{id}/stripe-intent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_stripe_intent_returns_intent(client: AsyncClient) -> None:
    donation_resp = await client.post("/donations", json={"amount_cents": 2000, "currency": "EUR"})
    donation_id = donation_resp.json()["id"]

    mock_intent = MagicMock()
    mock_intent.id = "pi_test_mock_intent"
    mock_intent.client_secret = "pi_test_mock_intent_secret_key"

    with (
        patch("src.api.donations.stripe.PaymentIntent.create", return_value=mock_intent),
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake_key"}),
    ):
        response = await client.post(f"/donations/{donation_id}/stripe-intent")

    assert response.status_code == 200
    body = response.json()
    assert body["donation_id"] == donation_id
    assert body["stripe_payment_intent_id"] == "pi_test_mock_intent"
    assert body["client_secret"] == "pi_test_mock_intent_secret_key"
    assert body["amount_cents"] == 2000
    assert body["currency"] == "EUR"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_stripe_intent_nonexistent_donation_returns_404(
    client: AsyncClient,
) -> None:
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake_key"}):
        response = await client.post(f"/donations/{uuid4()}/stripe-intent")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_stripe_intent_pyg_returns_422(client: AsyncClient) -> None:
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 100000, "currency": "PYG", "payment_method": "cash"},
    )
    donation_id = donation_resp.json()["id"]

    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake_key"}):
        response = await client.post(f"/donations/{donation_id}/stripe-intent")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_stripe_intent_no_key_returns_503(client: AsyncClient) -> None:
    donation_resp = await client.post("/donations", json={"amount_cents": 1000, "currency": "EUR"})
    donation_id = donation_resp.json()["id"]

    # Ensure STRIPE_SECRET_KEY is absent
    import os

    env_backup = os.environ.pop("STRIPE_SECRET_KEY", None)
    try:
        response = await client.post(f"/donations/{donation_id}/stripe-intent")
        assert response.status_code == 503
    finally:
        if env_backup is not None:
            os.environ["STRIPE_SECRET_KEY"] = env_backup


# ---------------------------------------------------------------------------
# GET /donations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_returns_list(client: AsyncClient) -> None:
    await client.post("/donations", json={"amount_cents": 500, "currency": "EUR"})
    response = await client.get("/donations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_currency(client: AsyncClient) -> None:
    await client.post("/donations", json={"amount_cents": 300, "currency": "USD"})
    response = await client.get("/donations?currency=USD")
    assert response.status_code == 200
    for item in response.json():
        assert item["currency"] == "USD"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_status(client: AsyncClient) -> None:
    response = await client.get("/donations?status=pending")
    assert response.status_code == 200
    for item in response.json():
        assert item["status"] == "pending"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_pagination(client: AsyncClient) -> None:
    for _ in range(3):
        await client.post("/donations", json={"amount_cents": 100, "currency": "EUR"})
    response = await client.get("/donations?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()) <= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_requires_auth(client: AsyncClient) -> None:
    from httpx import ASGITransport
    from httpx import AsyncClient as PlainClient
    from src.app import app

    async with PlainClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        response = await anon.get("/donations")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /donations/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donation_returns_donation(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/donations",
        json={"amount_cents": 750, "currency": "EUR", "notes": "Birthday gift"},
    )
    donation_id = create_resp.json()["id"]

    response = await client.get(f"/donations/{donation_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == donation_id
    assert body["amount_cents"] == 750
    assert body["notes"] == "Birthday gift"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donation_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/donations/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_donation_requires_auth(client: AsyncClient) -> None:
    from httpx import ASGITransport
    from httpx import AsyncClient as PlainClient
    from src.app import app

    create_resp = await client.post("/donations", json={"amount_cents": 1000, "currency": "EUR"})
    donation_id = create_resp.json()["id"]

    async with PlainClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        response = await anon.get(f"/donations/{donation_id}")
    assert response.status_code == 401
