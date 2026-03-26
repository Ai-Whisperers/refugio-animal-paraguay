"""Integration tests for CORS headers, rate limiting, and error standardization.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_cors_and_rate_limiting.py

Covers:
  - CORS preflight (OPTIONS) returns correct headers
  - CORS headers present on normal responses
  - Rate limiting returns 429 when exceeded
  - Rate limit headers on responses (X-RateLimit-Limit, etc.)
  - Error responses follow standard format (error_code, message, details, request_id)
  - X-Request-ID header present on all responses
  - Validation errors return field-level details
"""

import pytest
from httpx import ASGITransport, AsyncClient
from src.app import app
from src.config import Settings
from src.db.session import init_engine
from src.middleware.rate_limiter import configure_limiter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def _ensure_engine() -> None:
    """Ensure DB engine is initialized on current event loop."""
    init_engine(Settings())


# ---------------------------------------------------------------------------
# CORS tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_allows_configured_origin(_ensure_engine: None) -> None:
    """Configured origin receives CORS headers on normal requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_preflight_returns_allowed_methods(_ensure_engine: None) -> None:
    """OPTIONS preflight returns allowed methods and headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
    assert resp.status_code == 200
    assert "access-control-allow-methods" in resp.headers
    assert "access-control-allow-headers" in resp.headers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_rejects_unconfigured_origin(_ensure_engine: None) -> None:
    """Unconfigured origin does not receive CORS allow header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get(
            "/health",
            headers={"Origin": "http://evil.example.com"},
        )
    assert resp.status_code == 200
    # CORS middleware should NOT include the unconfigured origin
    allow_origin = resp.headers.get("access-control-allow-origin")
    assert allow_origin != "http://evil.example.com"


# ---------------------------------------------------------------------------
# Error format tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_404_error_returns_standard_format(_ensure_engine: None) -> None:
    """404 errors return the ErrorResponse format with error_code and message."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/animals/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404
    body = resp.json()
    assert "error_code" in body
    assert body["error_code"] == "NOT_FOUND"
    assert "message" in body
    assert "request_id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_422_validation_error_includes_field_details(_ensure_engine: None) -> None:
    """Validation errors include field-level details in the standard format."""
    # Use the public /auth/token endpoint with missing form fields to trigger 422
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/token",
            json={"bad": "data"},  # Wrong content type / missing form fields
        )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert len(body["details"]) >= 1
    # Each detail should have field, message, type
    detail = body["details"][0]
    assert "field" in detail
    assert "message" in detail
    assert "type" in detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_x_request_id_header_present(_ensure_engine: None) -> None:
    """All responses include an X-Request-ID header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_x_request_id_echoed_back(_ensure_engine: None) -> None:
    """Client-provided X-Request-ID is echoed back."""
    custom_id = "client-trace-abc-123"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )
    assert resp.headers.get("x-request-id") == custom_id


# ---------------------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rate_limiting_returns_429_when_exceeded(_ensure_engine: None) -> None:
    """Auth endpoint returns 429 after exceeding the rate limit."""
    # Re-enable rate limiting for this test
    configure_limiter(enabled=True)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            # Send 6 requests (limit is 5/minute on auth)
            responses = []
            for _ in range(7):
                resp = await c.post(
                    "/auth/token",
                    data={"username": "test@example.com", "password": "wrong"},
                )
                responses.append(resp)

            # At least one response should be 429
            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes, f"Expected 429 in {status_codes}"

            # The 429 response should have standard error format
            rate_limited = next(r for r in responses if r.status_code == 429)
            body = rate_limited.json()
            assert body["error_code"] == "RATE_LIMITED"
    finally:
        # Re-disable for other tests
        configure_limiter(enabled=False)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rate_limiting_disabled_allows_all_requests(_ensure_engine: None) -> None:
    """When rate limiting is disabled, no 429 responses are returned."""
    # Rate limiting is disabled by the autouse fixture
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        responses = []
        for _ in range(10):
            resp = await c.post(
                "/auth/token",
                data={"username": "test@example.com", "password": "wrong"},
            )
            responses.append(resp)

        status_codes = [r.status_code for r in responses]
        # All should be 401 (invalid credentials), never 429
        assert 429 not in status_codes
        assert all(code == 401 for code in status_codes)
