"""Integration tests for public user registration (POST /auth/register).

Tests cover: successful registration, duplicate email/phone detection,
validation errors, and role restrictions.
"""

import random
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from src.app import app
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture
async def public_client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated AsyncClient for public endpoint tests.

    Does not include Bearer token — avoids audit middleware errors
    when audit_logs table is absent in test environments.
    """
    settings = Settings()
    init_engine(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


def _register_data(**overrides: object) -> dict:
    """Return a valid registration payload with unique email/phone."""
    unique = uuid.uuid4().hex[:8]
    # Generate 6 random digits for the phone number (hex chars include a-f)
    phone_digits = "".join(str(random.randint(0, 9)) for _ in range(6))
    defaults: dict = {
        "full_name": "Test User",
        "email": f"test-{unique}@example.com",
        "phone": f"+595981{phone_digits}",
        "password": "SecureP@ss1",
        "role": "adopter",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Successful registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_adopter_returns_201(public_client: AsyncClient) -> None:
    """Successful registration returns 201 with user_id and next_step."""
    data = _register_data(role="adopter")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 201
    body = response.json()
    assert "user_id" in body
    assert body["next_step"] == "verify_email"
    assert "Registration successful" in body["message"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_donor_returns_201(public_client: AsyncClient) -> None:
    data = _register_data(role="donor")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_volunteer_returns_201(public_client: AsyncClient) -> None:
    data = _register_data(role="volunteer")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_foster_returns_201(public_client: AsyncClient) -> None:
    data = _register_data(role="foster")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_registered_user_has_unverified_status(public_client: AsyncClient) -> None:
    """Newly registered users cannot login (email not verified)."""
    data = _register_data()
    reg_response = await public_client.post("/auth/register", json=data)
    assert reg_response.status_code == 201

    # Attempt login should fail with 403 (email not verified)
    login_response = await public_client.post(
        "/auth/token",
        data={"username": data["email"], "password": data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 403
    body = login_response.json()
    error_text = (body.get("detail") or body.get("message") or "").lower()
    assert "not verified" in error_text


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_email_returns_400(public_client: AsyncClient) -> None:
    data = _register_data()
    first_response = await public_client.post("/auth/register", json=data)
    assert first_response.status_code == 201

    # Same email, different phone
    duplicate = _register_data(email=data["email"])
    second_response = await public_client.post("/auth/register", json=duplicate)
    assert second_response.status_code == 400
    body = second_response.json()
    error_text = (body.get("detail") or body.get("message") or "").lower()
    assert "email" in error_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_phone_returns_400(public_client: AsyncClient) -> None:
    data = _register_data()
    first_response = await public_client.post("/auth/register", json=data)
    assert first_response.status_code == 201

    # Same phone, different email
    duplicate = _register_data(phone=data["phone"])
    second_response = await public_client.post("/auth/register", json=duplicate)
    assert second_response.status_code == 400
    body = second_response.json()
    error_text = (body.get("detail") or body.get("message") or "").lower()
    assert "phone" in error_text


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_email_returns_422(public_client: AsyncClient) -> None:
    data = _register_data(email="not-an-email")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_weak_password_returns_422(public_client: AsyncClient) -> None:
    data = _register_data(password="weak")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_phone_format_returns_422(public_client: AsyncClient) -> None:
    data = _register_data(phone="+1234567890")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_name_too_short_returns_422(public_client: AsyncClient) -> None:
    data = _register_data(full_name="A")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Role restrictions — staff/admin/vet not allowed via public registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_role_rejected(public_client: AsyncClient) -> None:
    data = _register_data(role="staff")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_role_rejected(public_client: AsyncClient) -> None:
    data = _register_data(role="admin")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_name_whitespace_trimmed(public_client: AsyncClient) -> None:
    """Leading/trailing whitespace in name should be trimmed."""
    data = _register_data(full_name="  Maria Garcia  ")
    response = await public_client.post("/auth/register", json=data)
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_missing_required_fields_returns_422(public_client: AsyncClient) -> None:
    """Missing required fields should return 422."""
    response = await public_client.post("/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_double_submission_prevention(public_client: AsyncClient) -> None:
    """Submitting the same data twice should fail on second attempt."""
    data = _register_data()
    first = await public_client.post("/auth/register", json=data)
    assert first.status_code == 201

    second = await public_client.post("/auth/register", json=data)
    assert second.status_code == 400
