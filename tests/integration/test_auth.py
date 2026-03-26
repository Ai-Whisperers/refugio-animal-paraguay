"""Integration tests for JWT authentication endpoints.

Endpoints:
  POST /auth/token    — login, returns access token
  POST /auth/users    — create user (admin only)
  GET  /auth/me       — return current user

Also verifies 401 enforcement on protected mutation endpoints.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app

# ---------------------------------------------------------------------------
# POST /auth/token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_with_valid_credentials_returns_token(client: AsyncClient) -> None:
    """The conftest staff user can obtain a token via form login."""
    response = await client.post(
        "/auth/token",
        data={"username": "test-staff@refugio.test", "password": "TestPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": "test-staff@refugio.test", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": "nobody@example.com", "password": "anything"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_me_returns_current_user(client: AsyncClient) -> None:
    """The pre-authenticated client fixture carries a staff token."""
    response = await client.get("/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "test-staff@refugio.test"
    assert body["role"] == "staff"
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_me_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.get("/auth/me")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 401 enforcement on mutation endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_animal_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.post(
            "/animals", json={"name": "Unauthorized", "species": "dog"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.patch(
            f"/animals/{uuid4()}", json={"name": "x"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_animal_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.delete(f"/animals/{uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_adopter_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.post(
            "/adopters",
            json={"full_name": "Unauth", "email": "unauth@example.com"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_adoption_request_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.post(
            "/adoption-requests",
            json={"animal_id": str(uuid4()), "adopter_id": str(uuid4())},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adoption_request_status_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauthenticated:
        response = await unauthenticated.patch(
            f"/adoption-requests/{uuid4()}/status", json={"status": "approved"}
        )
    assert response.status_code == 401
