"""Integration tests for multilingual legal document endpoints (RAP-249).

Tests use a live PostgreSQL database and verify:
  GET /legal/supported-languages         — language discovery (public)
  GET /legal/dpa?lang=es|en              — bilingual DPA
  GET /legal/record-retention-policy?lang=es|en  — bilingual retention policy
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSupportedLanguagesEndpoint:
    """GET /legal/supported-languages integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/legal/supported-languages")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_has_required_keys(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/supported-languages")).json()
        assert "default_language" in data
        assert "supported_languages" in data
        assert "documents" in data

    @pytest.mark.asyncio
    async def test_default_language_is_es(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/supported-languages")).json()
        assert data["default_language"] == "es"

    @pytest.mark.asyncio
    async def test_public_no_auth_required(self, client: AsyncClient) -> None:
        response = await client.get("/legal/supported-languages")
        assert response.status_code != 401


@pytest.mark.integration
class TestDpaLanguageSupport:
    """GET /legal/dpa with ?lang integration tests."""

    @pytest.mark.asyncio
    async def test_default_returns_spanish(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/dpa")).json()
        assert data["language"] == "es"
        assert "Acuerdo" in data["document"]

    @pytest.mark.asyncio
    async def test_lang_en_returns_english(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/dpa?lang=en")).json()
        assert data["language"] == "en"
        assert "Data Processing Agreement" in data["document"]

    @pytest.mark.asyncio
    async def test_lang_es_sections_are_spanish(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/dpa?lang=es")).json()
        titles = [s["title"] for s in data["sections"]]
        assert any("Objeto" in t or "Finalidad" in t or "Obligaciones" in t for t in titles)

    @pytest.mark.asyncio
    async def test_lang_en_sections_are_english(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/dpa?lang=en")).json()
        titles = [s["title"] for s in data["sections"]]
        assert "Subject matter and duration" in titles

    @pytest.mark.asyncio
    async def test_unsupported_lang_falls_back_to_es(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/dpa?lang=fr")).json()
        assert data["language"] == "es"

    @pytest.mark.asyncio
    async def test_both_languages_have_nine_sections(self, client: AsyncClient) -> None:
        es = (await client.get("/legal/dpa?lang=es")).json()
        en = (await client.get("/legal/dpa?lang=en")).json()
        assert len(es["sections"]) == 9
        assert len(en["sections"]) == 9


@pytest.mark.integration
class TestRetentionPolicyLanguageSupport:
    """GET /legal/record-retention-policy with ?lang integration tests."""

    @pytest.mark.asyncio
    async def test_default_returns_spanish(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy")).json()
        assert data["language"] == "es"

    @pytest.mark.asyncio
    async def test_lang_en_returns_english_document_title(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy?lang=en")).json()
        assert data["language"] == "en"
        assert data["document"] == "Paraguayan Record Retention Policy"

    @pytest.mark.asyncio
    async def test_policies_count_same_in_both_languages(self, client: AsyncClient) -> None:
        es = (await client.get("/legal/record-retention-policy?lang=es")).json()
        en = (await client.get("/legal/record-retention-policy?lang=en")).json()
        assert len(es["policies"]) == len(en["policies"]) == 6

    @pytest.mark.asyncio
    async def test_unsupported_lang_falls_back_to_es(self, client: AsyncClient) -> None:
        data = (await client.get("/legal/record-retention-policy?lang=zh")).json()
        assert data["language"] == "es"
