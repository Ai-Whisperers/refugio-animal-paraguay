"""Integration tests for donation dashboard endpoints.

Covers:
  GET /donations/stats              — summary statistics (staff only)
  GET /donations/export             — CSV export (staff only)
  GET /donations                    — enhanced filters (date range, donor, fund_category, payment_method)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_donation_dashboard.py
"""

import csv
import io
from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_donation(
    client: AsyncClient,
    *,
    amount_cents: int = 1000,
    currency: str = "EUR",
    payment_method: str = "stripe",
    donor_id: str | None = None,
) -> dict:
    payload: dict = {
        "amount_cents": amount_cents,
        "currency": currency,
        "payment_method": payment_method,
    }
    if donor_id:
        payload["donor_id"] = donor_id
    response = await client.post("/donations", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def _create_cash_donation(
    client: AsyncClient,
    *,
    amount_cents: int = 500000,
    currency: str = "PYG",
) -> dict:
    response = await client.post(
        "/donations/cash",
        json={"amount_cents": amount_cents, "currency": currency},
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# GET /donations/stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_returns_200_for_staff(client: AsyncClient) -> None:
    response = await client.get("/donations/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total_donations" in body
    assert "by_currency" in body
    assert "by_status" in body
    assert "by_payment_method" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_counts_new_donation(client: AsyncClient) -> None:
    # Baseline
    baseline = await client.get("/donations/stats")
    baseline_total = baseline.json()["total_donations"]

    await _create_donation(client, amount_cents=2500, currency="EUR")

    response = await client.get("/donations/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_donations"] >= baseline_total + 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_currency_breakdown_includes_eur(client: AsyncClient) -> None:
    await _create_donation(client, amount_cents=3000, currency="EUR")

    response = await client.get("/donations/stats")
    body = response.json()
    currencies = {item["currency"] for item in body["by_currency"]}
    assert "EUR" in currencies


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_currency_breakdown_includes_pyg(client: AsyncClient) -> None:
    await _create_cash_donation(client, amount_cents=100000, currency="PYG")

    response = await client.get("/donations/stats")
    body = response.json()
    currencies = {item["currency"] for item in body["by_currency"]}
    assert "PYG" in currencies


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_payment_method_breakdown_present(client: AsyncClient) -> None:
    await _create_donation(client, amount_cents=1500, payment_method="stripe")
    await _create_cash_donation(client, amount_cents=200000, currency="PYG")

    response = await client.get("/donations/stats")
    body = response.json()
    methods = {item["payment_method"] for item in body["by_payment_method"]}
    assert "stripe" in methods
    assert "cash" in methods


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_date_filter_excludes_future(client: AsyncClient) -> None:
    """Requesting stats for a future date range should return zero donations."""
    response = await client.get(
        "/donations/stats",
        params={"date_from": "2099-01-01T00:00:00Z", "date_to": "2099-12-31T23:59:59Z"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_donations"] == 0
    assert body["by_currency"] == []
    assert body["by_status"] == []
    assert body["by_payment_method"] == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_reflects_date_in_response(client: AsyncClient) -> None:
    date_from = "2026-01-01T00:00:00Z"
    date_to = "2026-12-31T23:59:59Z"
    response = await client.get(
        "/donations/stats",
        params={"date_from": date_from, "date_to": date_to},
    )
    body = response.json()
    assert body["date_from"] is not None
    assert body["date_to"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/donations/stats",
        headers={"Authorization": ""},
    )
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /donations/export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_returns_csv_content_type(client: AsyncClient) -> None:
    response = await client.get("/donations/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_csv_has_header_row(client: AsyncClient) -> None:
    response = await client.get("/donations/export")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    headers = next(reader)
    assert "id" in headers
    assert "amount_cents" in headers
    assert "currency" in headers
    assert "status" in headers
    assert "created_at" in headers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_includes_created_donation(client: AsyncClient) -> None:
    donation = await _create_donation(client, amount_cents=9999, currency="EUR")
    donation_id = donation["id"]

    response = await client.get("/donations/export")
    assert response.status_code == 200
    assert donation_id in response.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_content_disposition_attachment(client: AsyncClient) -> None:
    response = await client.get("/donations/export")
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "donations.csv" in cd


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_filter_by_currency(client: AsyncClient) -> None:
    await _create_donation(client, amount_cents=1000, currency="EUR")
    await _create_cash_donation(client, amount_cents=500000, currency="PYG")

    response = await client.get("/donations/export", params={"currency": "EUR"})
    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert all(r["currency"] == "EUR" for r in rows)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_requires_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/donations/export",
        headers={"Authorization": ""},
    )
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /donations — enhanced filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_date_from(client: AsyncClient) -> None:
    """Donations before date_from must not appear in results."""
    response = await client.get(
        "/donations",
        params={"date_from": "2099-01-01T00:00:00Z"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_date_to(client: AsyncClient) -> None:
    """Donations after date_to must not appear in results."""
    response = await client.get(
        "/donations",
        params={"date_to": "2000-01-01T00:00:00Z"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_payment_method(client: AsyncClient) -> None:
    await _create_donation(client, amount_cents=2000, payment_method="stripe")
    await _create_cash_donation(client, amount_cents=100000)

    response = await client.get("/donations", params={"payment_method": "cash"})
    assert response.status_code == 200
    results = response.json()
    assert all(r["payment_method"] == "cash" for r in results)
    assert len(results) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_by_donor_id(client: AsyncClient) -> None:
    # Create a donor first
    donor_email = f"donor-{uuid4().hex[:8]}@example.com"
    donor_resp = await client.post(
        "/donors",
        json={"full_name": "Test Donor", "email": donor_email},
    )
    assert donor_resp.status_code == 201
    donor_id = donor_resp.json()["id"]

    await _create_donation(client, amount_cents=3000, donor_id=donor_id)
    await _create_donation(client, amount_cents=1000)  # anonymous

    response = await client.get("/donations", params={"donor_id": donor_id})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(r["donor_id"] == donor_id for r in results)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donations_filter_combination(client: AsyncClient) -> None:
    """Combining currency + payment_method filters narrows results correctly."""
    await _create_donation(client, amount_cents=5000, currency="EUR", payment_method="stripe")

    response = await client.get(
        "/donations",
        params={"currency": "EUR", "payment_method": "stripe"},
    )
    assert response.status_code == 200
    results = response.json()
    assert all(r["currency"] == "EUR" for r in results)
    assert all(r["payment_method"] == "stripe" for r in results)
