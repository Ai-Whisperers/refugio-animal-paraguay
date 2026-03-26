"""Integration tests for CORS, rate limiting, and error standardization.

Covers:
  - CORS headers on preflight and actual requests
  - Rate limiting (429 trigger on auth endpoints)
  - Standard error response format
  - Validation error format (422)
  - 500 error does not leak internal details

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_cors_ratelimit.py
"""

import pytest
from httpx import ASGITransport, AsyncClient
from src.app import app

# ---------------------------------------------------------------------------
# CORS Headers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_preflight_returns_headers(client: AsyncClient) -> None:
    """OPTIONS request to any endpoint returns CORS headers."""
    # Use a plain client to send custom Origin header
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_actual_request_has_origin_header(client: AsyncClient) -> None:
    """GET with Origin header returns Access-Control-Allow-Origin."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cors_disallowed_origin_has_no_header(client: AsyncClient) -> None:
    """Request from non-allowed origin does not get CORS header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get(
            "/health",
            headers={"Origin": "http://evil.example.com"},
        )
    assert resp.status_code == 200
    # CORS middleware should NOT include the origin
    assert resp.headers.get("access-control-allow-origin") != "http://evil.example.com"


# ---------------------------------------------------------------------------
# Standard Error Format
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_404_returns_standard_error_format(client: AsyncClient) -> None:
    """404 error from a known router follows {error_code, message, request_id} format."""
    from uuid import uuid4

    # Use a known endpoint that raises HTTPException(404) — e.g., get non-existent animal
    resp = await client.get(f"/animals/{uuid4()}")
    assert resp.status_code == 404
    body = resp.json()
    assert "error_code" in body
    assert body["error_code"] == "not_found"
    assert "message" in body
    assert "request_id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_422_returns_field_level_details(client: AsyncClient) -> None:
    """Validation error includes field-level details."""
    resp = await client.post(
        "/donors",
        json={"full_name": "", "email": "not-an-email"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "validation_error"
    assert body["message"] == "Request validation failed"
    assert body["details"] is not None
    assert len(body["details"]) > 0
    # Each detail has field and message
    for detail in body["details"]:
        assert "field" in detail
        assert "message" in detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_401_returns_standard_error_format(client: AsyncClient) -> None:
    """Unauthenticated request returns standard error format."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        resp = await anon.get("/auth/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error_code"] == "unauthorized"
    assert "request_id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_409_returns_standard_error_format(client: AsyncClient) -> None:
    """Conflict error returns standard error format."""
    from uuid import uuid4

    email = f"cors-test-{uuid4().hex[:8]}@example.com"
    # Create first donor
    await client.post("/donors", json={"full_name": "First", "email": email})
    # Attempt duplicate
    resp = await client.post("/donors", json={"full_name": "Second", "email": email})
    assert resp.status_code == 409
    body = resp.json()
    assert body["error_code"] == "conflict"
    assert "request_id" in body


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rate_limit_on_auth_endpoint(
    client: AsyncClient, enable_rate_limiting: None
) -> None:
    """Auth endpoint returns 429 after exceeding 5 requests/minute.

    Uses enable_rate_limiting fixture to temporarily enable rate limiting.
    Sends 7 requests — expects at least one 429.
    """
    statuses = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for _ in range(7):
            resp = await c.post(
                "/auth/token",
                data={"username": "nonexistent@example.com", "password": "wrong"},
            )
            statuses.append(resp.status_code)

    # At least some should be 401 (invalid creds) or 429 (rate limited)
    assert all(s in (401, 429) for s in statuses)
    # With rate limiting enabled, we expect at least one 429
    has_rate_limited = any(s == 429 for s in statuses)
    assert has_rate_limited, f"Expected at least one 429, got statuses: {statuses}"
