"""Unit tests for legal document endpoints (RAP-233, RAP-234)."""

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
        required = {"document", "version", "last_updated", "controller", "sections", "signature_fields"}
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
        assert len(sections) >= 5  # at minimum data collection, purpose, security, breach, transfers

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
