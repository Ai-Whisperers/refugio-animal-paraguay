"""Unit tests for SecurityHeadersMiddleware.

Verifies that HTTP security headers are injected correctly for both
production and non-production environments.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.middleware.security_headers import (
    CSP_DEVELOPMENT,
    CSP_PRODUCTION,
    HSTS_VALUE,
    PERMISSIONS_POLICY,
    REFERRER_POLICY,
    X_CONTENT_TYPE_OPTIONS,
    X_FRAME_OPTIONS,
    SecurityHeadersMiddleware,
)


def _build_app(environment: str) -> FastAPI:
    """Create a minimal FastAPI app with SecurityHeadersMiddleware for testing."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    return app


@pytest.fixture
def production_client() -> TestClient:
    return TestClient(_build_app("production"))


@pytest.fixture
def development_client() -> TestClient:
    return TestClient(_build_app("development"))


@pytest.fixture
def test_env_client() -> TestClient:
    return TestClient(_build_app("test"))


# --- Production environment ---


class TestProductionHeaders:
    def test_csp_header_is_strict_in_production(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["content-security-policy"] == CSP_PRODUCTION

    def test_csp_does_not_allow_unsafe_inline_in_production(
        self, production_client: TestClient
    ) -> None:
        response = production_client.get("/ping")
        csp = response.headers["content-security-policy"]
        assert "unsafe-inline" not in csp
        assert "unsafe-eval" not in csp

    def test_hsts_header_present_in_production(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["strict-transport-security"] == HSTS_VALUE

    def test_hsts_includes_one_year_max_age(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert "max-age=31536000" in response.headers["strict-transport-security"]

    def test_hsts_includes_subdomains(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert "includeSubDomains" in response.headers["strict-transport-security"]

    def test_x_frame_options_deny(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["x-frame-options"] == X_FRAME_OPTIONS

    def test_x_content_type_options_nosniff(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["x-content-type-options"] == X_CONTENT_TYPE_OPTIONS

    def test_referrer_policy(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["referrer-policy"] == REFERRER_POLICY

    def test_permissions_policy(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert response.headers["permissions-policy"] == PERMISSIONS_POLICY

    def test_permissions_policy_denies_camera(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert "camera=()" in response.headers["permissions-policy"]

    def test_permissions_policy_denies_geolocation(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert "geolocation=()" in response.headers["permissions-policy"]

    def test_permissions_policy_denies_microphone(self, production_client: TestClient) -> None:
        response = production_client.get("/ping")
        assert "microphone=()" in response.headers["permissions-policy"]


# --- Development environment ---


class TestDevelopmentHeaders:
    def test_csp_header_is_relaxed_in_development(self, development_client: TestClient) -> None:
        response = development_client.get("/ping")
        assert response.headers["content-security-policy"] == CSP_DEVELOPMENT

    def test_csp_allows_unsafe_inline_in_development(self, development_client: TestClient) -> None:
        response = development_client.get("/ping")
        csp = response.headers["content-security-policy"]
        assert "unsafe-inline" in csp

    def test_no_hsts_in_development(self, development_client: TestClient) -> None:
        # HSTS must not be sent in non-production to avoid locking out HTTP dev servers.
        response = development_client.get("/ping")
        assert "strict-transport-security" not in response.headers

    def test_x_frame_options_still_set_in_development(self, development_client: TestClient) -> None:
        response = development_client.get("/ping")
        assert response.headers["x-frame-options"] == X_FRAME_OPTIONS

    def test_x_content_type_options_still_set_in_development(
        self, development_client: TestClient
    ) -> None:
        response = development_client.get("/ping")
        assert response.headers["x-content-type-options"] == X_CONTENT_TYPE_OPTIONS

    def test_referrer_policy_still_set_in_development(self, development_client: TestClient) -> None:
        response = development_client.get("/ping")
        assert response.headers["referrer-policy"] == REFERRER_POLICY

    def test_permissions_policy_still_set_in_development(
        self, development_client: TestClient
    ) -> None:
        response = development_client.get("/ping")
        assert response.headers["permissions-policy"] == PERMISSIONS_POLICY


# --- Test environment (same as non-production) ---


class TestTestEnvironmentHeaders:
    def test_no_hsts_in_test_environment(self, test_env_client: TestClient) -> None:
        response = test_env_client.get("/ping")
        assert "strict-transport-security" not in response.headers

    def test_csp_is_development_policy_in_test(self, test_env_client: TestClient) -> None:
        response = test_env_client.get("/ping")
        assert response.headers["content-security-policy"] == CSP_DEVELOPMENT

    def test_all_base_headers_present_in_test(self, test_env_client: TestClient) -> None:
        response = test_env_client.get("/ping")
        assert "content-security-policy" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "referrer-policy" in response.headers
        assert "permissions-policy" in response.headers


# --- Header constant validation ---


class TestHeaderConstants:
    def test_production_csp_denies_scripts(self) -> None:
        assert "script-src 'none'" in CSP_PRODUCTION

    def test_production_csp_denies_forms(self) -> None:
        assert "form-action 'none'" in CSP_PRODUCTION

    def test_production_csp_denies_framing(self) -> None:
        assert "frame-ancestors 'none'" in CSP_PRODUCTION

    def test_development_csp_allows_websockets(self) -> None:
        # WebSockets needed for Next.js hot module replacement in development.
        assert "ws:" in CSP_DEVELOPMENT

    def test_x_frame_options_is_deny(self) -> None:
        assert X_FRAME_OPTIONS == "DENY"

    def test_x_content_type_options_is_nosniff(self) -> None:
        assert X_CONTENT_TYPE_OPTIONS == "nosniff"
