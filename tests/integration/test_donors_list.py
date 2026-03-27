"""Integration tests for GET /donors and GET /donors/export endpoints.

Covers:
  GET  /donors         - paginated list with search/filter/sort (staff only)
  GET  /donors/export  - CSV export with filters (staff only)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_donors_list.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_donor(client: AsyncClient, **overrides: object) -> dict:
    """Create a donor via POST /donors and return the response body."""
    defaults = {
        "full_name": f"Test Donor {uuid4().hex[:6]}",
        "email": f"donor-{uuid4().hex[:8]}@example.com",
    }
    defaults.update(overrides)
    resp = await client.post("/donors", json=defaults)
    assert resp.status_code == 201, f"Failed to create donor: {resp.text}"
    return resp.json()


async def _create_donation(client: AsyncClient, donor_id: str, **overrides: object) -> dict:
    """Create a completed donation for a donor."""
    defaults = {
        "donor_id": donor_id,
        "amount_cents": 5000,
        "currency": "EUR",
        "payment_method": "cash",
    }
    defaults.update(overrides)
    resp = await client.post("/donations", json=defaults)
    assert resp.status_code == 201, f"Failed to create donation: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# GET /donors — list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_returns_200(client: AsyncClient) -> None:
    response = await client.get("/donors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_includes_created_donor(client: AsyncClient) -> None:
    donor = await _create_donor(client, full_name="Pieter van der Berg")
    response = await client.get("/donors")
    assert response.status_code == 200
    ids = [d["id"] for d in response.json()]
    assert donor["id"] in ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_search_by_name(client: AsyncClient) -> None:
    unique_name = f"UniqueSearchName-{uuid4().hex[:6]}"
    await _create_donor(client, full_name=unique_name)
    response = await client.get("/donors", params={"search": unique_name[:10]})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(unique_name in d["full_name"] for d in results)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_search_by_email(client: AsyncClient) -> None:
    unique_email = f"unique-search-{uuid4().hex[:8]}@example.com"
    await _create_donor(client, email=unique_email)
    response = await client.get("/donors", params={"search": unique_email[:20]})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(unique_email == d["email"] for d in results)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_filter_by_country(client: AsyncClient) -> None:
    await _create_donor(client, country="DE")
    response = await client.get("/donors", params={"country": "DE"})
    assert response.status_code == 200
    for d in response.json():
        assert d["country"] == "DE"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_pagination(client: AsyncClient) -> None:
    # Create enough donors to paginate
    for _ in range(3):
        await _create_donor(client)

    page1 = await client.get("/donors", params={"limit": 2, "offset": 0})
    page2 = await client.get("/donors", params={"limit": 2, "offset": 2})
    assert page1.status_code == 200
    assert page2.status_code == 200
    assert len(page1.json()) <= 2
    # Pages should not overlap
    ids_p1 = {d["id"] for d in page1.json()}
    ids_p2 = {d["id"] for d in page2.json()}
    assert ids_p1.isdisjoint(ids_p2)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_sort_by_full_name_asc(client: AsyncClient) -> None:
    response = await client.get("/donors", params={"sort_by": "full_name", "sort_order": "asc"})
    assert response.status_code == 200
    names = [d["full_name"] for d in response.json()]
    assert names == sorted(names, key=str.lower)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_invalid_sort_field_returns_422(client: AsyncClient) -> None:
    response = await client.get("/donors", params={"sort_by": "invalid_field"})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_includes_donation_stats(client: AsyncClient) -> None:
    donor = await _create_donor(client)
    await _create_donation(client, donor["id"])
    response = await client.get("/donors")
    assert response.status_code == 200
    results = response.json()
    matching = [d for d in results if d["id"] == donor["id"]]
    assert len(matching) == 1
    assert "total_donations" in matching[0]
    assert "total_donated_cents" in matching[0]
    assert matching[0]["total_donations"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donors_gdpr_consent_filter(client: AsyncClient) -> None:
    await _create_donor(client, gdpr_consent_at="2026-01-15T10:00:00Z")
    response = await client.get("/donors", params={"has_gdpr_consent": "true"})
    assert response.status_code == 200
    for d in response.json():
        assert d["gdpr_consent_at"] is not None


# ---------------------------------------------------------------------------
# GET /donors/export — CSV
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_donors_csv_returns_200(client: AsyncClient) -> None:
    await _create_donor(client)
    response = await client.get("/donors/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "donors-export.csv" in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_donors_csv_contains_headers(client: AsyncClient) -> None:
    await _create_donor(client)
    response = await client.get("/donors/export")
    assert response.status_code == 200
    lines = response.text.strip().split("\n")
    assert len(lines) >= 2  # header + at least 1 data row
    header = lines[0]
    assert "full_name" in header
    assert "email" in header
    assert "total_donations" in header


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_donors_csv_with_search_filter(client: AsyncClient) -> None:
    unique_name = f"ExportTest-{uuid4().hex[:6]}"
    await _create_donor(client, full_name=unique_name)
    response = await client.get("/donors/export", params={"search": unique_name[:10]})
    assert response.status_code == 200
    assert unique_name in response.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_donors_csv_invalid_sort_returns_422(client: AsyncClient) -> None:
    response = await client.get("/donors/export", params={"sort_by": "bad_field"})
    assert response.status_code == 422
