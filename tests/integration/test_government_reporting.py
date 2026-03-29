"""Integration tests for Paraguayan government reporting endpoints (RAP-248).

Tests use a live PostgreSQL database and verify:
  GET /admin/reports/government/annual-census         — admin-only JSON report
  GET /admin/reports/government/annual-census/export  — admin-only CSV export
"""

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.integration
class TestAnnualCensusJsonEndpoint:
    """GET /admin/reports/government/annual-census integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_for_admin(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_json(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census")
        assert response.headers["content-type"].startswith("application/json")

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/reports/government/annual-census")).json()
        required = {
            "reporting_year",
            "generated_at",
            "shelter_name",
            "shelter_location",
            "reporting_authority",
            "legal_basis",
            "summary",
            "species_breakdown",
            "status_breakdown",
        }
        assert required.issubset(data.keys())

    @pytest.mark.asyncio
    async def test_summary_counts_are_non_negative(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/reports/government/annual-census")).json()
        for key, value in data["summary"].items():
            assert isinstance(value, int) and value >= 0, f"{key} must be non-negative int"

    @pytest.mark.asyncio
    async def test_legal_basis_cites_ley_4840(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/reports/government/annual-census")).json()
        assert any("4840" in b for b in data["legal_basis"])

    @pytest.mark.asyncio
    async def test_year_param_defaults_to_current_year(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/reports/government/annual-census")).json()
        assert data["reporting_year"] == datetime.now().year

    @pytest.mark.asyncio
    async def test_year_param_accepted(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census?year=2024")
        assert response.status_code == 200
        assert response.json()["reporting_year"] == 2024

    @pytest.mark.asyncio
    async def test_year_param_too_low_returns_422(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census?year=1999")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient) -> None:
        from src.app import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
            response = await anon.get("/admin/reports/government/annual-census")
        assert response.status_code == 401


@pytest.mark.integration
class TestAnnualCensusCsvEndpoint:
    """GET /admin/reports/government/annual-census/export integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_for_admin(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census/export")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_content_type_is_csv(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census/export")
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_content_disposition_is_attachment(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census/export")
        assert "attachment" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_csv_contains_senacsa_header(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census/export")
        assert "SENACSA" in response.text

    @pytest.mark.asyncio
    async def test_csv_contains_reporting_year(self, client: AsyncClient) -> None:
        response = await client.get("/admin/reports/government/annual-census/export")
        assert str(datetime.now().year) in response.text

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient) -> None:
        from src.app import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
            response = await anon.get("/admin/reports/government/annual-census/export")
        assert response.status_code == 401
