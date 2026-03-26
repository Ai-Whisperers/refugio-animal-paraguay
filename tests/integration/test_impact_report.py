"""Integration tests for the impact report endpoint.

Exercises GET /reports/impact against a live PostgreSQL database
with an authenticated staff client.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
class TestImpactReportEndpoint:
    """GET /reports/impact — generate shelter impact report."""

    async def test_returns_report_with_default_date_range(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200

        data = resp.json()
        assert "report_title" in data
        assert "animals" in data
        assert "adoptions" in data
        assert "donations" in data
        assert "in_kind" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "generated_at" in data

    async def test_returns_report_with_custom_date_range(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/reports/impact",
            params={
                "start_date": "2026-01-01T00:00:00Z",
                "end_date": "2026-03-31T23:59:59Z",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["animals"]["total_animals"] >= 0
        assert data["adoptions"]["total_requests"] >= 0
        assert data["donations"]["total_completed"] >= 0
        assert data["in_kind"]["total_donations"] >= 0

    async def test_animal_stats_structure(self, client: AsyncClient) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200

        animals = resp.json()["animals"]
        assert "total_animals" in animals
        assert "new_intakes" in animals
        assert "by_species" in animals
        assert "by_status" in animals
        assert isinstance(animals["by_species"], list)
        assert isinstance(animals["by_status"], list)

    async def test_adoption_stats_structure(self, client: AsyncClient) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200

        adoptions = resp.json()["adoptions"]
        assert "total_requests" in adoptions
        assert "approved" in adoptions
        assert "rejected" in adoptions
        assert "pending" in adoptions
        assert "approval_rate_pct" in adoptions
        assert isinstance(adoptions["approval_rate_pct"], (int, float))

    async def test_donation_stats_structure(self, client: AsyncClient) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200

        donations = resp.json()["donations"]
        assert "total_completed" in donations
        assert "total_by_currency" in donations
        assert "unique_donors" in donations
        assert isinstance(donations["total_by_currency"], list)

    async def test_in_kind_stats_structure(self, client: AsyncClient) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200

        in_kind = resp.json()["in_kind"]
        assert "total_donations" in in_kind
        assert "by_category" in in_kind
        assert isinstance(in_kind["by_category"], list)

    async def test_report_title_present(self, client: AsyncClient) -> None:
        resp = await client.get("/reports/impact")
        assert resp.status_code == 200
        assert (
            resp.json()["report_title"]
            == "Refugio Animal Paraguay \u2014 Impact Report"
        )
