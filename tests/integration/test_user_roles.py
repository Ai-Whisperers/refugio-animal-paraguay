"""Integration tests for user role self-assignment (GET/POST /api/users/roles).

Tests cover: listing roles, adding roles, removing roles, preventing last-role
removal, duplicate detection, and privilege escalation prevention.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

_TEST_ROLE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
_TEST_ROLE_EMAIL = "role-test@refugio.test"


@pytest_asyncio.fixture
async def role_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client with a fresh adopter user for role tests.

    Creates a user with role='adopter' and seeds a matching row in the
    user_roles junction table. Cleans up after test.
    """
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        # Clean up any leftover rows from previous runs
        await session.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid"),
            {"uid": str(_TEST_ROLE_USER_ID)},
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": str(_TEST_ROLE_USER_ID)},
        )
        await session.commit()

        # Create test user with 'adopter' role
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'adopter', true)
            """),
            {
                "id": str(_TEST_ROLE_USER_ID),
                "email": _TEST_ROLE_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        # Seed junction table with the primary role
        await session.execute(
            text("""
                INSERT INTO user_roles (id, user_id, role)
                VALUES (:id, :uid, 'adopter')
            """),
            {
                "id": str(uuid.uuid4()),
                "uid": str(_TEST_ROLE_USER_ID),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_TEST_ROLE_USER_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac

    # Cleanup
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid"),
            {"uid": str(_TEST_ROLE_USER_ID)},
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": str(_TEST_ROLE_USER_ID)},
        )
        await session.commit()


# ---------------------------------------------------------------------------
# GET /api/users/roles — List roles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_roles_returns_current_and_available(
    role_client: AsyncClient,
) -> None:
    """GET /api/users/roles returns user's roles and all available roles."""
    response = await role_client.get("/api/users/roles")
    assert response.status_code == 200
    body = response.json()
    assert "adopter" in body["roles"]
    assert len(body["available_roles"]) == 4  # adopter, donor, volunteer, foster
    # Check structure of available_roles entries
    for role_info in body["available_roles"]:
        assert "role" in role_info
        assert "label" in role_info
        assert "description" in role_info
        assert "assigned" in role_info


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_roles_shows_assigned_status(role_client: AsyncClient) -> None:
    """Assigned roles are marked as assigned=True in available_roles."""
    response = await role_client.get("/api/users/roles")
    body = response.json()
    adopter_info = next(r for r in body["available_roles"] if r["role"] == "adopter")
    donor_info = next(r for r in body["available_roles"] if r["role"] == "donor")
    assert adopter_info["assigned"] is True
    assert donor_info["assigned"] is False


# ---------------------------------------------------------------------------
# POST /api/users/roles — Add role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_role_succeeds(role_client: AsyncClient) -> None:
    """Adding a valid self-assignable role returns updated roles list."""
    response = await role_client.post(
        "/api/users/roles", json={"role": "volunteer", "action": "add"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "volunteer" in body["roles"]
    assert "adopter" in body["roles"]
    assert "message" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_duplicate_role_returns_409(role_client: AsyncClient) -> None:
    """Adding a role the user already has returns 409 Conflict."""
    response = await role_client.post(
        "/api/users/roles", json={"role": "adopter", "action": "add"}
    )
    assert response.status_code == 409
    assert "already" in response.json()["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_privileged_role_returns_422(role_client: AsyncClient) -> None:
    """Attempting to add admin/staff/vet returns 422 (Pydantic validation)."""
    response = await role_client.post(
        "/api/users/roles", json={"role": "admin", "action": "add"}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/users/roles — Remove role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_remove_role_succeeds(role_client: AsyncClient) -> None:
    """Removing a role when user has multiple roles succeeds."""
    # First add a second role
    await role_client.post(
        "/api/users/roles", json={"role": "donor", "action": "add"}
    )

    # Now remove the original role
    response = await role_client.post(
        "/api/users/roles", json={"role": "adopter", "action": "remove"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "adopter" not in body["roles"]
    assert "donor" in body["roles"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_remove_last_role_returns_400(role_client: AsyncClient) -> None:
    """Removing the only role returns 400 — users must keep at least one."""
    response = await role_client.post(
        "/api/users/roles", json={"role": "adopter", "action": "remove"}
    )
    assert response.status_code == 400
    assert "at least one" in response.json()["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_remove_unassigned_role_returns_400(role_client: AsyncClient) -> None:
    """Removing a role the user doesn't have returns 400."""
    # Add a second role so the "last role" guard doesn't trigger first
    await role_client.post(
        "/api/users/roles", json={"role": "donor", "action": "add"}
    )
    response = await role_client.post(
        "/api/users/roles", json={"role": "volunteer", "action": "remove"}
    )
    assert response.status_code == 400
    assert "don't have" in response.json()["message"].lower()


# ---------------------------------------------------------------------------
# Full workflow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_then_verify_in_listing(role_client: AsyncClient) -> None:
    """After adding a role, GET /roles reflects the change."""
    # Add volunteer
    await role_client.post(
        "/api/users/roles", json={"role": "volunteer", "action": "add"}
    )

    # Verify in listing
    response = await role_client.get("/api/users/roles")
    body = response.json()
    assert "volunteer" in body["roles"]
    volunteer_info = next(r for r in body["available_roles"] if r["role"] == "volunteer")
    assert volunteer_info["assigned"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_request_returns_401() -> None:
    """Requests without auth token return 401."""
    settings = Settings()
    init_engine(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/users/roles")
        assert response.status_code == 401
