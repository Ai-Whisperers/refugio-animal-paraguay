"""Integration tests for in-kind donations endpoints.

Covers:
  POST   /in-kind-donations              -- record in-kind donation (staff only)
  GET    /in-kind-donations              -- list with filters (staff only)
  GET    /in-kind-donations/{id}         -- get single (staff only)
  PUT    /in-kind-donations/{id}         -- update (staff only)
  DELETE /in-kind-donations/{id}         -- delete (staff only)
  GET    /donors/{id}/giving-summary     -- combined cash + in-kind totals (staff only)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_in_kind_donations.py
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from src.app import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_donor(client: AsyncClient) -> str:
    """Create a test donor and return its ID."""
    email = f"inkind-donor-{uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/donors",
        json={"full_name": "In-Kind Test Donor", "email": email},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_in_kind(
    client: AsyncClient,
    donor_id: str | None = None,
    item_type: str = "food",
    estimated_value_cents: int = 2500,
    quantity: int = 1,
    currency: str = "EUR",
) -> dict:
    """Create an in-kind donation and return the response body."""
    payload: dict = {
        "item_type": item_type,
        "estimated_value_cents": estimated_value_cents,
        "quantity": quantity,
        "currency": currency,
    }
    if donor_id is not None:
        payload["donor_id"] = donor_id
    resp = await client.post("/in-kind-donations", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /in-kind-donations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_returns_201(client: AsyncClient) -> None:
    body = await _create_in_kind(client, item_type="food", estimated_value_cents=2500)
    assert body["item_type"] == "food"
    assert body["estimated_value_cents"] == 2500
    assert body["quantity"] == 1
    assert body["currency"] == "EUR"
    assert body["received_by_staff_id"] is not None
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_with_donor(client: AsyncClient) -> None:
    donor_id = await _create_donor(client)
    body = await _create_in_kind(client, donor_id=donor_id, item_type="medication")
    assert body["donor_id"] == donor_id
    assert body["item_type"] == "medication"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_all_item_types(client: AsyncClient) -> None:
    item_types = [
        "food",
        "medication",
        "equipment",
        "toys",
        "bedding",
        "supplies",
        "veterinary_services",
        "transportation",
        "other",
    ]
    for it in item_types:
        body = await _create_in_kind(client, item_type=it)
        assert body["item_type"] == it


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_with_description(client: AsyncClient) -> None:
    resp = await client.post(
        "/in-kind-donations",
        json={
            "item_type": "food",
            "estimated_value_cents": 5000,
            "description": "20kg bag of premium dog food",
            "notes": "Donated by local pet store",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == "20kg bag of premium dog food"
    assert body["notes"] == "Donated by local pet store"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/in-kind-donations",
        json={
            "item_type": "food",
            "estimated_value_cents": 1000,
            "donor_id": str(uuid4()),
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_negative_value_returns_422(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/in-kind-donations",
        json={"item_type": "food", "estimated_value_cents": -100},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_zero_quantity_returns_422(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/in-kind-donations",
        json={"item_type": "food", "estimated_value_cents": 1000, "quantity": 0},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_in_kind_donation_requires_auth(client: AsyncClient) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        resp = await anon.post(
            "/in-kind-donations",
            json={"item_type": "food", "estimated_value_cents": 1000},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /in-kind-donations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_in_kind_donations_returns_paginated(client: AsyncClient) -> None:
    await _create_in_kind(client)
    resp = await client.get("/in-kind-donations")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_in_kind_donations_filter_by_item_type(client: AsyncClient) -> None:
    await _create_in_kind(client, item_type="bedding")
    resp = await client.get("/in-kind-donations?item_type=bedding")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["item_type"] == "bedding"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_in_kind_donations_filter_by_donor(client: AsyncClient) -> None:
    donor_id = await _create_donor(client)
    await _create_in_kind(client, donor_id=donor_id)
    resp = await client.get(f"/in-kind-donations?donor_id={donor_id}")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["donor_id"] == donor_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_in_kind_donations_pagination(client: AsyncClient) -> None:
    for _ in range(3):
        await _create_in_kind(client)
    resp = await client.get("/in-kind-donations?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 2


# ---------------------------------------------------------------------------
# GET /in-kind-donations/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_in_kind_donation_returns_donation(client: AsyncClient) -> None:
    created = await _create_in_kind(client, item_type="toys", estimated_value_cents=800)
    donation_id = created["id"]
    resp = await client.get(f"/in-kind-donations/{donation_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == donation_id
    assert resp.json()["item_type"] == "toys"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_in_kind_donation_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/in-kind-donations/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /in-kind-donations/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_in_kind_donation(client: AsyncClient) -> None:
    created = await _create_in_kind(client, item_type="food", estimated_value_cents=2500)
    donation_id = created["id"]

    resp = await client.put(
        f"/in-kind-donations/{donation_id}",
        json={"quantity": 5, "notes": "Updated to 5 bags"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity"] == 5
    assert body["notes"] == "Updated to 5 bags"
    # Unchanged fields preserved
    assert body["item_type"] == "food"
    assert body["estimated_value_cents"] == 2500


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_in_kind_donation_item_type(client: AsyncClient) -> None:
    created = await _create_in_kind(client, item_type="other")
    donation_id = created["id"]

    resp = await client.put(
        f"/in-kind-donations/{donation_id}",
        json={"item_type": "equipment"},
    )
    assert resp.status_code == 200
    assert resp.json()["item_type"] == "equipment"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_in_kind_donation_not_found(client: AsyncClient) -> None:
    resp = await client.put(
        f"/in-kind-donations/{uuid4()}",
        json={"quantity": 3},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /in-kind-donations/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_in_kind_donation(client: AsyncClient) -> None:
    created = await _create_in_kind(client)
    donation_id = created["id"]

    resp = await client.delete(f"/in-kind-donations/{donation_id}")
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/in-kind-donations/{donation_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_in_kind_donation_not_found(client: AsyncClient) -> None:
    resp = await client.delete(f"/in-kind-donations/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /donors/{id}/giving-summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_donor_giving_summary_combined_totals(client: AsyncClient) -> None:
    donor_id = await _create_donor(client)

    # Create a completed cash donation
    donation_resp = await client.post(
        "/donations",
        json={"amount_cents": 5000, "currency": "EUR", "donor_id": donor_id},
    )
    assert donation_resp.status_code == 201

    # Create in-kind donations
    await _create_in_kind(client, donor_id=donor_id, estimated_value_cents=3000)
    await _create_in_kind(client, donor_id=donor_id, estimated_value_cents=2000)

    resp = await client.get(f"/donors/{donor_id}/giving-summary?currency=EUR")
    assert resp.status_code == 200
    body = resp.json()
    assert body["donor_id"] == donor_id
    assert body["in_kind_total_cents"] == 5000
    assert body["in_kind_donation_count"] == 2
    assert body["currency"] == "EUR"
    # Cash donations are pending (not completed), so cash_total_cents = 0
    assert body["cash_total_cents"] == 0
    assert body["combined_total_cents"] == 5000


@pytest.mark.asyncio
@pytest.mark.integration
async def test_donor_giving_summary_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/donors/{uuid4()}/giving-summary")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_donor_giving_summary_empty(client: AsyncClient) -> None:
    donor_id = await _create_donor(client)
    resp = await client.get(f"/donors/{donor_id}/giving-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cash_total_cents"] == 0
    assert body["in_kind_total_cents"] == 0
    assert body["combined_total_cents"] == 0
    assert body["cash_donation_count"] == 0
    assert body["in_kind_donation_count"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_donor_giving_summary_requires_auth(client: AsyncClient) -> None:
    donor_id = await _create_donor(client)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        resp = await anon.get(f"/donors/{donor_id}/giving-summary")
    assert resp.status_code == 401
