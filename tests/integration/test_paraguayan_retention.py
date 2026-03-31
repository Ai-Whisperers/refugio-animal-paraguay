"""Integration tests for Paraguayan record retention endpoints (RAP-247).

Tests use a live PostgreSQL database and verify:
  GET /legal/record-retention-policy  — public, no auth required
  GET /admin/data-retention/paraguayan-status — admin-only, requires JWT
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRecordRetentionPolicyEndpoint:
    """GET /legal/record-retention-policy integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/legal/record-retention-policy")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_json(self, client: AsyncClient) -> None:
        response = await client.get("/legal/record-retention-policy")
        assert response.headers["content-type"].startswith("application/json")

    @pytest.mark.asyncio
    async def test_default_language_spanish(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy")).json()
        assert data["document"] == "Paraguayan Record Retention Policy"

    @pytest.mark.asyncio
    async def test_policies_list_present_and_non_empty(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy")).json()
        assert isinstance(data["policies"], list)
        assert len(data["policies"]) > 0

    @pytest.mark.asyncio
    async def test_contains_all_six_record_types(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy")).json()
        types = {p["record_type"] for p in data["policies"]}
        expected = {
            "adoption_contracts",
            "animal_health_records",
            "vaccination_records",
            "donation_records",
            "adopter_personal_data",
            "contact_submissions",
        }
        assert expected == types

    @pytest.mark.asyncio
    async def test_legal_bases_cite_paraguayan_law(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy")).json()
        all_bases = " ".join(p["legal_basis"] for p in data["policies"])
        # Must cite at least Ley 4840/2013 and the Codigo Civil
        assert "4840" in all_bases
        assert "Codigo Civil" in all_bases

    @pytest.mark.asyncio
    async def test_no_auth_required(self, client: AsyncClient) -> None:
        # Unauthenticated get — should still return 200 (public endpoint)
        from httpx import ASGITransport
        from httpx import AsyncClient as PlainClient
        from src.app import app

        async with PlainClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
            response = await anon.get("/legal/record-retention-policy")
        assert response.status_code == 200


@pytest.mark.integration
class TestParaguayanRetentionStatusEndpoint:
    """GET /admin/data-retention/paraguayan-status integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_for_admin(self, client: AsyncClient) -> None:
        response = await client.get("/admin/data-retention/paraguayan-status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/data-retention/paraguayan-status")).json()
        required = {
            "check_date",
            "active_animal_count",
            "pending_adoption_count",
            "recent_donation_count",
            "oldest_adoption_date",
            "oldest_donation_date",
            "policy",
        }
        assert required.issubset(data.keys())

    @pytest.mark.asyncio
    async def test_counts_are_non_negative_integers(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/data-retention/paraguayan-status")).json()
        assert isinstance(data["active_animal_count"], int)
        assert data["active_animal_count"] >= 0
        assert isinstance(data["pending_adoption_count"], int)
        assert data["pending_adoption_count"] >= 0
        assert isinstance(data["recent_donation_count"], int)
        assert data["recent_donation_count"] >= 0

    @pytest.mark.asyncio
    async def test_policy_list_non_empty(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/data-retention/paraguayan-status")).json()
        assert isinstance(data["policy"], list)
        assert len(data["policy"]) == 6

    @pytest.mark.asyncio
    async def test_check_date_is_iso_string(self, client: AsyncClient) -> None:
        data = (await client.get("/admin/data-retention/paraguayan-status")).json()
        # Should be parseable as ISO datetime
        from datetime import datetime

        dt = datetime.fromisoformat(data["check_date"])
        assert dt is not None

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient) -> None:
        from httpx import ASGITransport
        from httpx import AsyncClient as PlainClient
        from src.app import app

        async with PlainClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
            response = await anon.get("/admin/data-retention/paraguayan-status")
        assert response.status_code == 401
