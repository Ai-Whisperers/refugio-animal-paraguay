"""Unit tests for the sub-processor registry endpoint (RAP-234)."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestSubProcessorRegistry:
    """GET /legal/sub-processors — sub-processor registry."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/legal/sub-processors")
        assert response.status_code == 200

    def test_response_is_json(self, client: TestClient) -> None:
        response = client.get("/legal/sub-processors")
        assert response.headers["content-type"].startswith("application/json")

    def test_has_required_top_level_keys(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        required = {
            "document",
            "controller",
            "last_updated",
            "contact",
            "gdpr_basis",
            "total_sub_processors",
            "sub_processors",
        }
        assert required.issubset(data.keys())

    def test_document_name(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        assert data["document"] == "Sub-Processor Registry"

    def test_sub_processors_list_non_empty(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        assert len(data["sub_processors"]) >= 4  # stripe, twilio, sentry, hostinger at minimum

    def test_total_count_matches_list(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        assert data["total_sub_processors"] == len(data["sub_processors"])

    def test_each_processor_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        required = {"name", "role", "data_processed", "purpose", "data_location"}
        for processor in data["sub_processors"]:
            assert required.issubset(processor.keys()), f"Missing fields in: {processor['name']}"

    def test_stripe_is_listed(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        names = [p["name"] for p in data["sub_processors"]]
        assert any("Stripe" in name for name in names)

    def test_twilio_is_listed(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        names = [p["name"] for p in data["sub_processors"]]
        assert any("Twilio" in name for name in names)

    def test_data_processed_is_list_of_strings(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        for processor in data["sub_processors"]:
            assert isinstance(processor["data_processed"], list)
            for item in processor["data_processed"]:
                assert isinstance(item, str)

    def test_contact_email_present(self, client: TestClient) -> None:
        data = client.get("/legal/sub-processors").json()
        assert "@" in data["contact"]
