"""Unit tests for legal document endpoints (RAP-233, RAP-234, RAP-246)."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestDPAEndpoint:
    """GET /legal/dpa — Data Processing Agreement template."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/legal/dpa")
        assert response.status_code == 200

    def test_response_is_json(self, client: TestClient) -> None:
        response = client.get("/legal/dpa")
        assert response.headers["content-type"].startswith("application/json")

    def test_has_required_top_level_keys(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        required = {
            "document",
            "version",
            "last_updated",
            "controller",
            "sections",
            "signature_fields",
        }
        assert required.issubset(data.keys())

    def test_document_name(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        assert data["document"] == "Data Processing Agreement"

    def test_controller_fields(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        controller = data["controller"]
        assert "name" in controller
        assert "contact" in controller
        assert "refugioanimal" in controller["contact"]

    def test_sections_non_empty(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        sections = data["sections"]
        assert (
            len(sections) >= 5
        )  # at minimum data collection, purpose, security, breach, transfers

    def test_each_section_has_title_and_body(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        for section in data["sections"]:
            assert "title" in section, f"Section missing 'title': {section}"
            assert "body" in section, f"Section missing 'body': {section}"
            assert len(section["title"]) > 0
            assert len(section["body"]) > 0

    def test_signature_fields_present(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        sig_fields = data["signature_fields"]
        assert len(sig_fields) == 2
        parties = {f["party"] for f in sig_fields}
        assert "Controller" in parties
        assert "Processor" in parties

    def test_contact_email_present(self, client: TestClient) -> None:
        data = client.get("/legal/dpa").json()
        assert "contact_for_execution" in data
        assert "@" in data["contact_for_execution"]


class TestAdoptionContractEndpoint:
    """GET /legal/adoption-contract — Paraguayan adoption contract template."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/legal/adoption-contract")
        assert response.status_code == 200

    def test_default_language_is_spanish(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        assert data["language"] == "es"

    def test_english_language_via_param(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract?lang=en").json()
        assert data["language"] == "en"
        assert "Animal Adoption Contract" in data["document"]

    def test_spanish_language_via_param(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract?lang=es").json()
        assert data["language"] == "es"
        assert "Contrato de Adopcion" in data["document"]

    def test_invalid_language_falls_back_to_spanish(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract?lang=fr").json()
        assert data["language"] == "es"

    def test_has_required_top_level_keys(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        required = {
            "document",
            "version",
            "last_updated",
            "language",
            "shelter",
            "sections",
            "signature_fields",
            "legal_basis",
        }
        assert required.issubset(data.keys())

    def test_legal_basis_references_paraguayan_laws(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        legal_basis = " ".join(data["legal_basis"])
        assert "4840" in legal_basis  # Ley 4840/2013 — Animal Welfare
        assert "3140" in legal_basis  # Ley 3140/2006 — Disease Control

    def test_sections_count_at_least_9(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        assert len(data["sections"]) >= 9

    def test_each_section_has_id_title_body(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        for section in data["sections"]:
            assert "id" in section, f"Section missing 'id': {section}"
            assert "title" in section, f"Section missing 'title': {section}"
            assert "body" in section, f"Section missing 'body': {section}"
            assert len(section["body"]) > 0

    def test_signature_fields_present(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        sig_fields = data["signature_fields"]
        assert len(sig_fields) == 2
        parties = {f["party"] for f in sig_fields}
        assert "adoptante" in parties or "adopter" in parties
        assert "shelter" in parties

    def test_shelter_info_included(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        shelter = data["shelter"]
        assert "Refugio Animal Paraguay" in shelter["name"]
        assert "@" in shelter["contact"]

    def test_vaccination_section_references_ley_3140(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        # Section 3 is vaccination
        vaccination_section = next(s for s in data["sections"] if s["id"] == "3")
        assert (
            "3140" in vaccination_section.get("legal_ref", "")
            or "3140" in vaccination_section["body"]
        )

    def test_welfare_section_references_ley_4840(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        # Section 8 is animal welfare obligations
        welfare_section = next(s for s in data["sections"] if s["id"] == "8")
        assert "4840" in welfare_section.get("legal_ref", "") or "4840" in welfare_section["body"]

    def test_english_sections_have_english_titles(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract?lang=en").json()
        # Section 1 should have English title in EN version
        first_section = data["sections"][0]
        assert "Animal Description" in first_section["title"]

    def test_spanish_sections_have_spanish_titles(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract?lang=es").json()
        first_section = data["sections"][0]
        assert "Animal" in first_section["title"]  # "Descripcion del Animal"

    def test_version_field_present(self, client: TestClient) -> None:
        data = client.get("/legal/adoption-contract").json()
        assert data["version"] == "1.0"
