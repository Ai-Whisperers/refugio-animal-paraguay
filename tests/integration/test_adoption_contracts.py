"""Integration tests for adoption contract PDF generation endpoint.

Tests the POST /adoption-requests/{id}/contract endpoint with a live
PostgreSQL instance (refugio_dev).

Run: pytest -m integration tests/integration/test_adoption_contracts.py
"""

import os
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_approved_request(client: AsyncClient) -> tuple[str, str, str]:
    """Create an animal, adopter, adoption request, and approve it."""
    # Create animal
    resp = await client.post("/animals", json={"name": "ContractAnimal", "species": "dog"})
    assert resp.status_code == 201
    animal_id = resp.json()["id"]

    # Create adopter
    email = f"contract-adopter-{uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/adopters",
        json={"full_name": "Contract Adopter", "email": email, "phone": "+595981111111"},
    )
    assert resp.status_code == 201
    adopter_id = resp.json()["id"]

    # Create request
    resp = await client.post(
        "/adoption-requests",
        json={"animal_id": animal_id, "adopter_id": adopter_id},
    )
    assert resp.status_code == 201
    request_id = resp.json()["id"]

    # Approve it
    resp = await client.patch(
        f"/adoption-requests/{request_id}/status",
        json={"status": "approved"},
    )
    assert resp.status_code == 200

    return request_id, animal_id, adopter_id


class TestGenerateAdoptionContract:
    """Tests for POST /adoption-requests/{id}/contract."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_contract_returns_201(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp = await client.post(f"/adoption-requests/{request_id}/contract")
        assert resp.status_code == 201
        data = resp.json()
        assert data["request_id"] == request_id
        assert "contract.pdf" in data["contract_pdf_path"]
        assert data["contract_generated_at"] is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_contract_creates_pdf_file(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp = await client.post(f"/adoption-requests/{request_id}/contract")
        assert resp.status_code == 201
        pdf_path = resp.json()["contract_pdf_path"]
        assert os.path.exists(pdf_path)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_contract_for_pending_request_returns_422(self, client: AsyncClient) -> None:
        # Create but don't approve
        resp = await client.post("/animals", json={"name": "PendingAnimal", "species": "cat"})
        animal_id = resp.json()["id"]

        email = f"pending-{uuid4().hex[:8]}@example.com"
        resp = await client.post("/adopters", json={"full_name": "Pending Adopter", "email": email})
        adopter_id = resp.json()["id"]

        resp = await client.post(
            "/adoption-requests",
            json={"animal_id": animal_id, "adopter_id": adopter_id},
        )
        request_id = resp.json()["id"]

        # Try to generate contract for pending request
        resp = await client.post(f"/adoption-requests/{request_id}/contract")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_contract_for_nonexistent_request_returns_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid4())
        resp = await client.post(f"/adoption-requests/{fake_id}/contract")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_regenerate_contract_overwrites(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        # Generate twice
        resp1 = await client.post(f"/adoption-requests/{request_id}/contract")
        resp2 = await client.post(f"/adoption-requests/{request_id}/contract")

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        # Path should be the same (overwrite)
        assert resp1.json()["contract_pdf_path"] == resp2.json()["contract_pdf_path"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_contract_path_stored_on_request(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        await client.post(f"/adoption-requests/{request_id}/contract")

        # Fetch the request and check contract fields
        resp = await client.get(f"/adoption-requests/{request_id}")
        data = resp.json()
        assert data["contract_pdf_path"] is not None
        assert data["contract_generated_at"] is not None
