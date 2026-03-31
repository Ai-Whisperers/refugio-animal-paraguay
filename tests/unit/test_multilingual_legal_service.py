"""Unit tests for the multilingual legal service and updated legal document endpoints (RAP-249).

Tests cover:
- normalise_language: supported codes, fallback, case-insensitive
- SUPPORTED_LANGUAGES and DEFAULT_LANGUAGE constants
- MULTILINGUAL_DOCUMENTS structure
- DPA_SECTIONS_ES Spanish translation completeness
- GET /legal/supported-languages endpoint
- GET /legal/dpa with ?lang param
- GET /legal/record-retention-policy with ?lang param
"""

import pytest
from fastapi.testclient import TestClient
from src.services.multilingual_legal_service import (
    DEFAULT_LANGUAGE,
    DPA_SECTIONS_ES,
    MULTILINGUAL_DOCUMENTS,
    SUPPORTED_LANGUAGES,
    normalise_language,
)

# ---------------------------------------------------------------------------
# normalise_language
# ---------------------------------------------------------------------------


class TestNormaliseLanguage:
    """Tests for normalise_language helper."""

    def test_es_code_returned_as_is(self) -> None:
        assert normalise_language("es") == "es"

    def test_en_code_returned_as_is(self) -> None:
        assert normalise_language("en") == "en"

    def test_uppercase_es_normalised(self) -> None:
        assert normalise_language("ES") == "es"

    def test_uppercase_en_normalised(self) -> None:
        assert normalise_language("EN") == "en"

    def test_mixed_case_normalised(self) -> None:
        assert normalise_language("Es") == "es"

    def test_unsupported_code_falls_back_to_default(self) -> None:
        assert normalise_language("fr") == DEFAULT_LANGUAGE

    def test_empty_string_falls_back_to_default(self) -> None:
        assert normalise_language("") == DEFAULT_LANGUAGE

    def test_random_string_falls_back_to_default(self) -> None:
        assert normalise_language("gu") == DEFAULT_LANGUAGE

    def test_strips_whitespace(self) -> None:
        assert normalise_language(" en ") == "en"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for service-level constants."""

    def test_default_language_is_es(self) -> None:
        assert DEFAULT_LANGUAGE == "es"

    def test_supported_languages_contains_es(self) -> None:
        assert "es" in SUPPORTED_LANGUAGES

    def test_supported_languages_contains_en(self) -> None:
        assert "en" in SUPPORTED_LANGUAGES

    def test_supported_languages_is_immutable(self) -> None:
        assert isinstance(SUPPORTED_LANGUAGES, frozenset)


# ---------------------------------------------------------------------------
# MULTILINGUAL_DOCUMENTS
# ---------------------------------------------------------------------------


class TestMultilingualDocuments:
    """Tests for MULTILINGUAL_DOCUMENTS list."""

    def test_is_non_empty_list(self) -> None:
        assert isinstance(MULTILINGUAL_DOCUMENTS, list)
        assert len(MULTILINGUAL_DOCUMENTS) > 0

    def test_each_entry_has_required_keys(self) -> None:
        required = {"document_key", "endpoint", "title_en", "title_es", "supported_languages"}
        for doc in MULTILINGUAL_DOCUMENTS:
            assert required.issubset(doc.keys()), f"Missing keys in {doc['document_key']}"

    def test_dpa_entry_present(self) -> None:
        keys = {d["document_key"] for d in MULTILINGUAL_DOCUMENTS}
        assert "dpa" in keys

    def test_retention_policy_entry_present(self) -> None:
        keys = {d["document_key"] for d in MULTILINGUAL_DOCUMENTS}
        assert "record-retention-policy" in keys

    def test_all_entries_support_es_and_en(self) -> None:
        for doc in MULTILINGUAL_DOCUMENTS:
            assert "es" in doc["supported_languages"]
            assert "en" in doc["supported_languages"]


# ---------------------------------------------------------------------------
# DPA_SECTIONS_ES
# ---------------------------------------------------------------------------


class TestDpaSectionsEs:
    """Tests for Spanish DPA sections."""

    def test_nine_sections(self) -> None:
        assert len(DPA_SECTIONS_ES) == 9

    def test_each_section_has_id_title_body(self) -> None:
        for section in DPA_SECTIONS_ES:
            assert "id" in section
            assert "title" in section
            assert "body" in section
            assert len(section["body"]) > 20

    def test_sections_are_in_spanish(self) -> None:
        all_titles = " ".join(s["title"] for s in DPA_SECTIONS_ES)
        # Should contain Spanish words
        spanish_markers = {"Objeto", "Finalidad", "Obligaciones", "Seguridad", "Legislación", "Sub"}
        assert any(marker in all_titles for marker in spanish_markers)


# ---------------------------------------------------------------------------
# GET /legal/supported-languages
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    from src.app import app

    return TestClient(app)


class TestSupportedLanguagesEndpoint:
    """GET /legal/supported-languages."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/legal/supported-languages")
        assert response.status_code == 200

    def test_has_required_keys(self, client: TestClient) -> None:
        data = client.get("/legal/supported-languages").json()
        assert "default_language" in data
        assert "supported_languages" in data
        assert "documents" in data

    def test_default_language_is_es(self, client: TestClient) -> None:
        data = client.get("/legal/supported-languages").json()
        assert data["default_language"] == "es"

    def test_supported_languages_has_es_and_en(self, client: TestClient) -> None:
        data = client.get("/legal/supported-languages").json()
        codes = {lang["code"] for lang in data["supported_languages"]}
        assert "es" in codes
        assert "en" in codes

    def test_documents_list_non_empty(self, client: TestClient) -> None:
        data = client.get("/legal/supported-languages").json()
        assert len(data["documents"]) > 0

    def test_no_authentication_required(self, client: TestClient) -> None:
        response = client.get("/legal/supported-languages")
        assert response.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# GET /legal/dpa with lang param
# ---------------------------------------------------------------------------


class TestDpaEndpointLanguage:
    """Language support for GET /legal/dpa."""

    def test_default_lang_is_es(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        assert data["language"] == "es"
        assert data["document"] == "Acuerdo de Procesamiento de Datos"

    def test_lang_es_explicit(self, client: TestClient) -> None:
        data = client.get("/legal/dpa?lang=es").json()
        assert data["language"] == "es"

    def test_lang_en(self, client: TestClient) -> None:
        data = client.get("/legal/dpa?lang=en").json()
        assert data["language"] == "en"
        assert data["document"] == "Data Processing Agreement"

    def test_lang_en_sections_are_english(self, client: TestClient) -> None:
        data = client.get("/legal/dpa?lang=en").json()
        titles = [s["title"] for s in data["sections"]]
        assert "Subject matter and duration" in titles

    def test_lang_es_sections_are_spanish(self, client: TestClient) -> None:
        data = client.get("/legal/dpa?lang=es").json()
        titles = [s["title"] for s in data["sections"]]
        assert any("Objeto" in t or "Finalidad" in t for t in titles)

    def test_unsupported_lang_falls_back_to_es(self, client: TestClient) -> None:
        data = client.get("/legal/dpa?lang=fr").json()
        assert data["language"] == "es"

    def test_lang_field_present_in_response(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        assert "language" in data

    def test_nine_sections_in_both_languages(self, client: TestClient) -> None:
        es_data = client.get("/legal/dpa?lang=es").json()
        en_data = client.get("/legal/dpa?lang=en").json()
        assert len(es_data["sections"]) == 9
        assert len(en_data["sections"]) == 9


# ---------------------------------------------------------------------------
# GET /legal/record-retention-policy with lang param
# ---------------------------------------------------------------------------


class TestRetentionPolicyEndpointLanguage:
    """Language support for GET /legal/record-retention-policy."""

    def test_default_lang_is_es(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert data["language"] == "es"

    def test_lang_en(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy?lang=en").json()
        assert data["language"] == "en"
        assert data["document"] == "Paraguayan Record Retention Policy"

    def test_lang_es_note_is_spanish(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy?lang=es").json()
        # Spanish note should contain Spanish words
        assert (
            "retención" in data["note"].lower()
            or "período" in data["note"].lower()
            or "refugio" in data["note"].lower()
        )

    def test_lang_en_note_is_english(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy?lang=en").json()
        assert "minimum" in data["note"].lower()

    def test_unsupported_lang_falls_back_to_es(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy?lang=de").json()
        assert data["language"] == "es"

    def test_lang_field_present_in_response(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert "language" in data

    def test_policies_list_unchanged_by_language(self, client: TestClient) -> None:
        es_data = client.get("/legal/record-retention-policy?lang=es").json()
        en_data = client.get("/legal/record-retention-policy?lang=en").json()
        assert len(es_data["policies"]) == len(en_data["policies"]) == 6
