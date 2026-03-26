"""Integration tests for impact report generation endpoint.

Tests run against the live PostgreSQL test database with an
authenticated staff client.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from src.app import app


def _report_payload(**overrides: object) -> dict:
    """Build a valid impact report request payload."""
    now = datetime.now(tz=timezone.utc)
    defaults: dict = {
        "start_date": (now - timedelta(days=90)).isoformat(),
        "end_date": now.isoformat(),
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.integration
class TestGenerateImpactReport:
    """POST /impact-reports/generate."""

    @pytest.mark.asyncio
    async def test_generates_report_with_all_sections(
        self, client: AsyncClient
    ) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        assert resp.status_code == 200
        data = resp.json()

        # Verify all top-level sections exist
        assert "report_metadata" in data
        assert "animals_served" in data
        assert "adoptions" in data
        assert "donations" in data
        assert "in_kind_donations" in data
        assert "fund_allocation" in data
        assert "performance_metrics" in data

    @pytest.mark.asyncio
    async def test_report_metadata_contains_dates(
        self, client: AsyncClient
    ) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        data = resp.json()
        metadata = data["report_metadata"]
        assert metadata["start_date"] is not None
        assert metadata["end_date"] is not None
        assert metadata["generated_by_user_id"] is not None

    @pytest.mark.asyncio
    async def test_animals_served_structure(self, client: AsyncClient) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        animals = resp.json()["animals_served"]
        assert "total" in animals
        assert "by_species" in animals
        assert isinstance(animals["total"], int)
        assert isinstance(animals["by_species"], dict)

    @pytest.mark.asyncio
    async def test_donations_structure(self, client: AsyncClient) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        donations = resp.json()["donations"]
        assert "total_count" in donations
        assert "by_currency" in donations
        assert "by_payment_method" in donations

    @pytest.mark.asyncio
    async def test_fund_allocation_structure(self, client: AsyncClient) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        fund = resp.json()["fund_allocation"]
        assert "total_cents" in fund
        assert "breakdown" in fund
        assert isinstance(fund["breakdown"], list)

    @pytest.mark.asyncio
    async def test_performance_metrics_structure(
        self, client: AsyncClient
    ) -> None:
        payload = _report_payload()
        resp = await client.post("/impact-reports/generate", json=payload)

        metrics = resp.json()["performance_metrics"]
        assert "avg_time_to_adoption_days" in metrics
        assert "cost_per_adoption_cents" in metrics

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        payload = _report_payload()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauth_client:
            resp = await unauth_client.post(
                "/impact-reports/generate", json=payload
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_missing_dates(self, client: AsyncClient) -> None:
        resp = await client.post("/impact-reports/generate", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_narrow_date_range_returns_empty(
        self, client: AsyncClient
    ) -> None:
        """A date range in the far past should return zero metrics."""
        payload = {
            "start_date": "2020-01-01T00:00:00Z",
            "end_date": "2020-01-02T00:00:00Z",
        }
        resp = await client.post("/impact-reports/generate", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["animals_served"]["total"] == 0
        assert data["adoptions"]["total"] == 0
        assert data["donations"]["total_count"] == 0
