"""Integration tests for email verification API endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app
from src.auth.utils import hash_password
from src.config import Settings
from src.db.session import init_engine

_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000201")
_TEST_USER_EMAIL = "verify-test@refugio-shelter.org"
_TEST_USER_PASSWORD = "TestPassword123!"

_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000202")
_ADMIN_EMAIL = "admin-verify@refugio-shelter.org"
_ADMIN_PASSWORD = "AdminPassword123!"


@pytest_asyncio.fixture
async def verify_client():
    """Client with test users for email verification tests."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        # Create an unverified test user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified)
                VALUES (:id, :email, :pwd, 'staff', true, false)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd,
                    is_active = true,
                    email_verified = false
            """),
            {
                "id": str(_TEST_USER_ID),
                "email": _TEST_USER_EMAIL,
                "pwd": hash_password(_TEST_USER_PASSWORD),
            },
        )
        # Create a verified admin user for user creation tests
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified)
                VALUES (:id, :email, :pwd, 'admin', true, true)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd,
                    is_active = true,
                    email_verified = true
            """),
            {
                "id": str(_ADMIN_USER_ID),
                "email": _ADMIN_EMAIL,
                "pwd": hash_password(_ADMIN_PASSWORD),
            },
        )
        await session.execute(
            text("DELETE FROM verification_tokens WHERE user_id IN (:uid1, :uid2)"),
            {"uid1": str(_TEST_USER_ID), "uid2": str(_ADMIN_USER_ID)},
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
            text("DELETE FROM verification_tokens WHERE user_id IN (:uid1, :uid2)"),
            {"uid1": str(_TEST_USER_ID), "uid2": str(_ADMIN_USER_ID)},
        )
        await session.commit()


async def _get_admin_token(client: AsyncClient) -> str:
    """Log in as admin and return access token."""
    response = await client.post(
        "/auth/token",
        data={"username": _ADMIN_EMAIL, "password": _ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _create_verification_token(user_id: str) -> str:
    """Create a verification token directly in the DB."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        from src.services.email_verification_service import (
            create_email_verification_token,
        )

        token = await create_email_verification_token(session, user_id)
        await session.commit()
        return token


@pytest.mark.integration()
class TestEmailVerification:
    """Tests for POST /auth/email/verify."""

    @pytest.mark.asyncio()
    async def test_verify_valid_token(self, verify_client):
        """Should verify email and return success."""
        token = await _create_verification_token(str(_TEST_USER_ID))
        assert token is not None

        response = await verify_client.post(
            "/auth/email/verify",
            json={"token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True

    @pytest.mark.asyncio()
    async def test_verify_invalid_token(self, verify_client):
        """Should return 400 for invalid token."""
        response = await verify_client.post(
            "/auth/email/verify",
            json={"token": "completely-bogus-token"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_login_blocked_before_verification(self, verify_client):
        """Should block login for unverified users with 403."""
        response = await verify_client.post(
            "/auth/token",
            data={
                "username": _TEST_USER_EMAIL,
                "password": _TEST_USER_PASSWORD,
            },
        )
        assert response.status_code == 403
        body = response.json()
        message = body.get("message", body.get("detail", ""))
        assert "not verified" in message.lower()

    @pytest.mark.asyncio()
    async def test_login_allowed_after_verification(self, verify_client):
        """Should allow login after email verification."""
        # Verify the email first
        token = await _create_verification_token(str(_TEST_USER_ID))
        verify_response = await verify_client.post(
            "/auth/email/verify",
            json={"token": token},
        )
        assert verify_response.status_code == 200

        # Now login should work
        login_response = await verify_client.post(
            "/auth/token",
            data={
                "username": _TEST_USER_EMAIL,
                "password": _TEST_USER_PASSWORD,
            },
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


@pytest.mark.integration()
class TestResendVerificationEmail:
    """Tests for POST /auth/email/resend."""

    @pytest.mark.asyncio()
    async def test_resend_for_unverified_user(self, verify_client):
        """Should return success for unverified user email."""
        response = await verify_client.post(
            "/auth/email/resend",
            json={"email": _TEST_USER_EMAIL},
        )
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio()
    async def test_resend_for_nonexistent_email(self, verify_client):
        """Should return same success to not leak email existence."""
        response = await verify_client.post(
            "/auth/email/resend",
            json={"email": "nobody@refugio-shelter.org"},
        )
        assert response.status_code == 200
        assert "message" in response.json()
