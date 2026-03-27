"""Integration tests for profile management API endpoints."""

import uuid
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

_PROFILE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000401")
_PROFILE_USER_EMAIL = "profile-test@refugio.org"
_PROFILE_USER_PASSWORD = "TestPass123!"

_DONOR_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000402")
_DONOR_USER_EMAIL = "donor-profile@refugio.org"
_DONOR_USER_PASSWORD = "DonorPass1!"


@pytest_asyncio.fixture
async def profile_client():
    """Authenticated client for profile tests with a test user."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        # Create profile test user (staff role - guaranteed to exist in check constraint)
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified, full_name, phone)
                VALUES (:id, :email, :pwd, 'staff', true, true, 'Test Profile', '+595981000001')
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd,
                    role = 'staff',
                    is_active = true,
                    email_verified = true,
                    full_name = 'Test Profile',
                    phone = '+595981000001'
            """),
            {
                "id": str(_PROFILE_USER_ID),
                "email": _PROFILE_USER_EMAIL,
                "pwd": hash_password(_PROFILE_USER_PASSWORD),
            },
        )
        # Create donor test user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified, full_name)
                VALUES (:id, :email, :pwd, 'staff', true, true, 'Donor User')
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd,
                    role = 'staff',
                    is_active = true,
                    email_verified = true,
                    full_name = 'Donor User'
            """),
            {
                "id": str(_DONOR_USER_ID),
                "email": _DONOR_USER_EMAIL,
                "pwd": hash_password(_DONOR_USER_PASSWORD),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_PROFILE_USER_ID)},
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


def _donor_token() -> str:
    """Create a JWT token for the donor test user."""
    settings = Settings()
    return create_access_token(
        data={"sub": str(_DONOR_USER_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )


@pytest.mark.integration()
class TestGetProfile:
    """Tests for GET /portal/profile."""

    @pytest.mark.asyncio()
    async def test_returns_current_user_profile(self, profile_client) -> None:
        response = await profile_client.get("/portal/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == _PROFILE_USER_EMAIL
        assert data["full_name"] == "Test Profile"
        assert data["role"] == "staff"

    @pytest.mark.asyncio()
    async def test_requires_authentication(self, profile_client) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauthed:
            response = await unauthed.get("/portal/profile")
        assert response.status_code == 401


@pytest.mark.integration()
class TestUpdateProfile:
    """Tests for PUT /portal/profile."""

    @pytest.mark.asyncio()
    async def test_updates_full_name(self, profile_client) -> None:
        response = await profile_client.put(
            "/portal/profile",
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

        # Restore original name for other tests
        await profile_client.put(
            "/portal/profile",
            json={"full_name": "Test Profile"},
        )

    @pytest.mark.asyncio()
    async def test_updates_phone(self, profile_client) -> None:
        response = await profile_client.put(
            "/portal/profile",
            json={"phone": "+595981999999"},
        )
        assert response.status_code == 200
        assert response.json()["phone"] == "+595981999999"

    @pytest.mark.asyncio()
    async def test_rejects_invalid_phone_format(self, profile_client) -> None:
        response = await profile_client.put(
            "/portal/profile",
            json={"phone": "12345"},
        )
        assert response.status_code == 422


@pytest.mark.integration()
class TestChangePassword:
    """Tests for POST /portal/change-password."""

    @pytest.mark.asyncio()
    async def test_changes_password_successfully(self, profile_client) -> None:
        response = await profile_client.post(
            "/portal/change-password",
            json={
                "current_password": _PROFILE_USER_PASSWORD,
                "new_password": "NewSecure1!",
            },
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

        # Restore original password
        settings = Settings()
        engine = init_engine(settings)
        sf = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with sf() as session:
            await session.execute(
                text("UPDATE users SET hashed_password = :pwd WHERE id = :id"),
                {
                    "pwd": hash_password(_PROFILE_USER_PASSWORD),
                    "id": str(_PROFILE_USER_ID),
                },
            )
            await session.commit()

    @pytest.mark.asyncio()
    async def test_rejects_wrong_current_password(self, profile_client) -> None:
        response = await profile_client.post(
            "/portal/change-password",
            json={
                "current_password": "WrongPassword1!",
                "new_password": "NewSecure1!",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_rejects_weak_password(self, profile_client) -> None:
        response = await profile_client.post(
            "/portal/change-password",
            json={
                "current_password": _PROFILE_USER_PASSWORD,
                "new_password": "weak",
            },
        )
        assert response.status_code == 422


@pytest.mark.integration()
class TestPreferences:
    """Tests for GET/PUT /portal/preferences."""

    @pytest.mark.asyncio()
    async def test_get_default_preferences(self, profile_client) -> None:
        response = await profile_client.get("/portal/preferences")
        assert response.status_code == 200
        data = response.json()
        assert "email_adoption" in data
        assert "inapp_enabled" in data

    @pytest.mark.asyncio()
    async def test_update_preferences(self, profile_client) -> None:
        response = await profile_client.put(
            "/portal/preferences",
            json={
                "email_adoption": False,
                "email_donations": True,
                "email_volunteer": False,
                "whatsapp_enabled": False,
                "inapp_enabled": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email_adoption"] is False
        assert data["email_volunteer"] is False


@pytest.mark.integration()
class TestGDPRExport:
    """Tests for GET /portal/gdpr/export."""

    @pytest.mark.asyncio()
    async def test_exports_user_data_as_json(self, profile_client) -> None:
        response = await profile_client.get("/portal/gdpr/export")
        assert response.status_code == 200
        data = response.json()
        assert data["user_profile"]["email"] == _PROFILE_USER_EMAIL
        assert "export_date" in data
        assert "adoption_requests" in data
        assert "donations" in data

    @pytest.mark.asyncio()
    async def test_export_has_download_header(self, profile_client) -> None:
        response = await profile_client.get("/portal/gdpr/export")
        assert response.status_code == 200
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp
        assert "refugio_data_" in content_disp


@pytest.mark.integration()
class TestAccountDeletion:
    """Tests for POST /portal/gdpr/delete and /portal/gdpr/delete/confirm."""

    @pytest.mark.asyncio()
    async def test_delete_request_with_correct_password(self, profile_client) -> None:
        donor_token = _donor_token()
        response = await profile_client.post(
            "/portal/gdpr/delete",
            json={"password": _DONOR_USER_PASSWORD},
            headers={"Authorization": f"Bearer {donor_token}"},
        )
        assert response.status_code == 200
        assert response.json()["confirmation_required"] is True

    @pytest.mark.asyncio()
    async def test_delete_request_with_wrong_password(self, profile_client) -> None:
        response = await profile_client.post(
            "/portal/gdpr/delete",
            json={"password": "WrongPassword1!"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_delete_confirm_with_invalid_token(self, profile_client) -> None:
        response = await profile_client.post(
            "/portal/gdpr/delete/confirm",
            json={"token": "bogus-token-value"},
        )
        assert response.status_code == 400
