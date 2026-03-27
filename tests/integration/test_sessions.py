"""Integration tests for session management API endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app
from src.auth.utils import hash_password
from src.config import Settings
from src.db.session import init_engine

_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000301")
_ADMIN_EMAIL = "session-admin@refugio-shelter.org"
_ADMIN_PASSWORD = "AdminPass123!"

_STAFF_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000302")
_STAFF_EMAIL = "session-staff@refugio-shelter.org"
_STAFF_PASSWORD = "StaffPass123!"


@pytest_asyncio.fixture
async def session_client():
    """Client with admin and staff users for session tests."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified)
                VALUES (:id, :email, :pwd, 'admin', true, true)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd, is_active = true, email_verified = true
            """),
            {
                "id": str(_ADMIN_USER_ID),
                "email": _ADMIN_EMAIL,
                "pwd": hash_password(_ADMIN_PASSWORD),
            },
        )
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified)
                VALUES (:id, :email, :pwd, 'staff', true, true)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd, is_active = true, email_verified = true
            """),
            {
                "id": str(_STAFF_USER_ID),
                "email": _STAFF_EMAIL,
                "pwd": hash_password(_STAFF_PASSWORD),
            },
        )
        # Cleanup old sessions
        await session.execute(
            text("DELETE FROM active_sessions WHERE user_id IN (:uid1, :uid2)"),
            {"uid1": str(_ADMIN_USER_ID), "uid2": str(_STAFF_USER_ID)},
        )
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Cleanup
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM active_sessions WHERE user_id IN (:uid1, :uid2)"),
            {"uid1": str(_ADMIN_USER_ID), "uid2": str(_STAFF_USER_ID)},
        )
        await session.commit()


async def _login(client: AsyncClient, email: str, password: str) -> str:
    """Log in and return the access token."""
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.integration()
class TestSessionCreation:
    """Tests for session creation on login."""

    @pytest.mark.asyncio()
    async def test_login_creates_session(self, session_client):
        """Should create an active session record on login."""
        admin_token = await _login(session_client, _ADMIN_EMAIL, _ADMIN_PASSWORD)

        # List sessions — should see at least the admin's session
        response = await session_client.get(
            "/auth/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            s["user_id"] == str(_ADMIN_USER_ID) for s in data["sessions"]
        )


@pytest.mark.integration()
class TestForceLogout:
    """Tests for admin force-logout endpoints."""

    @pytest.mark.asyncio()
    async def test_admin_can_force_logout_staff_session(self, session_client):
        """Admin should be able to force-logout a staff session."""
        admin_token = await _login(session_client, _ADMIN_EMAIL, _ADMIN_PASSWORD)
        staff_token = await _login(session_client, _STAFF_EMAIL, _STAFF_PASSWORD)

        # Get staff session ID
        response = await session_client.get(
            f"/auth/sessions?user_id={_STAFF_USER_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        assert len(sessions) >= 1
        staff_session_id = sessions[0]["id"]

        # Force logout
        response = await session_client.delete(
            f"/auth/sessions/{staff_session_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["revoked"] is True

        # Staff token should now be rejected
        response = await session_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio()
    async def test_admin_can_force_logout_all_user_sessions(self, session_client):
        """Admin should be able to force-logout all sessions for a user."""
        admin_token = await _login(session_client, _ADMIN_EMAIL, _ADMIN_PASSWORD)
        # Create two staff sessions
        await _login(session_client, _STAFF_EMAIL, _STAFF_PASSWORD)
        staff_token_2 = await _login(session_client, _STAFF_EMAIL, _STAFF_PASSWORD)

        # Force logout all
        response = await session_client.delete(
            f"/auth/sessions/user/{_STAFF_USER_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # Staff should be locked out
        response = await session_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {staff_token_2}"},
        )
        assert response.status_code == 401


@pytest.mark.integration()
class TestSessionTimeout:
    """Tests for session inactivity timeout."""

    @pytest.mark.asyncio()
    async def test_session_times_out_after_inactivity(self, session_client):
        """Should reject token when session has been inactive too long."""
        staff_token = await _login(session_client, _STAFF_EMAIL, _STAFF_PASSWORD)

        # Manually set last_activity to 31 minutes ago
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            await session.execute(
                text("""
                    UPDATE active_sessions
                    SET last_activity = :old_time
                    WHERE user_id = :uid AND revoked_at IS NULL
                """),
                {
                    "uid": str(_STAFF_USER_ID),
                    "old_time": datetime.now(UTC) - timedelta(minutes=31),
                },
            )
            await session.commit()

        # Token should now be rejected
        response = await session_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 401
