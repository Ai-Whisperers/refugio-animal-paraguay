"""Integration tests for legal document endpoints (RAP-246).

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_legal_documents.py
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_returns_200(client: AsyncClient) -> None:
    response = await client.get("/legal/adoption-contract")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_default_language_spanish(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract")).json()
    assert data["language"] == "es"
    assert "Contrato" in data["document"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_english_via_param(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract?lang=en")).json()
    assert data["language"] == "en"
    assert "Adoption Contract" in data["document"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_invalid_lang_falls_back_to_spanish(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract?lang=de")).json()
    assert data["language"] == "es"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_contains_legal_basis(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract")).json()
    combined = " ".join(data["legal_basis"])
    assert "4840" in combined
    assert "3140" in combined


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_has_all_required_sections(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract")).json()
    section_ids = {s["id"] for s in data["sections"]}
    # Must include all 10 required sections
    for expected_id in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        assert expected_id in section_ids, f"Missing section {expected_id}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adoption_contract_signature_fields_are_empty(client: AsyncClient) -> None:
    data = (await client.get("/legal/adoption-contract")).json()
    for field in data["signature_fields"]:
        assert field["name"] is None
        assert field["signature"] is None
        assert field["date"] is None
