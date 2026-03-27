"""Integration tests for password reset API endpoints.

Tests cover:
- Request reset (existing user, nonexistent email, invalid format)
- Confirm reset (valid token, invalid token, short password, full flow with login)
- Validate token (valid, invalid)
- Token reuse prevention (used token cannot reset again)
- Old password invalidation (after reset, old password no longer works)
- Expired token handling (expired token returns invalid)
"""

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

_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000199")
_TEST_USER_EMAIL = "reset-test@refugio-shelter.org"
_TEST_USER_PASSWORD = "OldPassword123!"


@pytest_asyncio.fixture
async def reset_client():
    """Unauthenticated client for password reset endpoints."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd,
                    is_active = true
            """),
            {
                "id": str(_TEST_USER_ID),
                "email": _TEST_USER_EMAIL,
                "pwd": hash_password(_TEST_USER_PASSWORD),
            },
        )
        await session.execute(
            text("DELETE FROM verification_tokens WHERE user_id = :uid"),
            {"uid": str(_TEST_USER_ID)},
        )
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Cleanup tokens
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM verification_tokens WHERE user_id = :uid"),
            {"uid": str(_TEST_USER_ID)},
        )
        await session.commit()


@pytest.mark.integration()
class TestPasswordResetRequest:
    """Tests for POST /auth/password-reset/request."""

    @pytest.mark.asyncio()
    async def test_request_reset_for_existing_user(self, reset_client):
        """Should return success message for existing email."""
        response = await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio()
    async def test_request_reset_for_nonexistent_email(self, reset_client):
        """Should return same success message to not leak email existence."""
        response = await reset_client.post(
            "/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio()
    async def test_request_reset_invalid_email_format(self, reset_client):
        """Should reject invalid email format."""
        response = await reset_client.post(
            "/auth/password-reset/request",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


@pytest.mark.integration()
class TestPasswordResetConfirm:
    """Tests for POST /auth/password-reset/confirm."""

    @pytest.mark.asyncio()
    async def test_confirm_reset_with_valid_token(self, reset_client):
        """Should reset password when token is valid."""
        # Step 1: Request a reset
        response = await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )
        assert response.status_code == 200

        # Step 2: Get the token from DB
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None, "No reset token found in DB"
            token_value = row[0]

        # Step 3: Confirm reset
        new_password = "NewSecurePass456!"
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": new_password},
        )
        assert response.status_code == 200

        # Step 4: Verify login with new password
        login_response = await reset_client.post(
            "/auth/token",
            data={"username": _TEST_USER_EMAIL, "password": new_password},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    @pytest.mark.asyncio()
    async def test_confirm_reset_with_invalid_token(self, reset_client):
        """Should reject invalid token."""
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": "completely-invalid-token", "new_password": "NewPass123!"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_confirm_reset_with_short_password(self, reset_client):
        """Should reject password shorter than 8 characters."""
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": "some-token", "new_password": "short"},
        )
        assert response.status_code == 422


@pytest.mark.integration()
class TestPasswordResetValidate:
    """Tests for GET /auth/password-reset/validate."""

    @pytest.mark.asyncio()
    async def test_validate_valid_token(self, reset_client):
        """Should return valid=true for a valid token."""
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

        response = await reset_client.get(f"/auth/password-reset/validate?token={token_value}")
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio()
    async def test_validate_invalid_token(self, reset_client):
        """Should return valid=false for an invalid token."""
        response = await reset_client.get("/auth/password-reset/validate?token=nonexistent-token")
        assert response.status_code == 200
        assert response.json()["valid"] is False


@pytest.mark.integration()
class TestPasswordResetTokenReuse:
    """Tests for token reuse prevention."""

    @pytest.mark.asyncio()
    async def test_used_token_cannot_reset_again(self, reset_client):
        """After a successful reset, the same token should be rejected."""
        # Step 1: Request reset
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Step 2: Get token from DB
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

        # Step 3: Use token to reset password
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": "FirstReset123!"},
        )
        assert response.status_code == 200

        # Step 4: Try to reuse the same token
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": "SecondReset456!"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_used_token_validates_as_invalid(self, reset_client):
        """After a successful reset, the token should validate as invalid."""
        # Request reset
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Get token
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

        # Use token
        await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": "NewPass123!"},
        )

        # Validate should return false
        response = await reset_client.get(f"/auth/password-reset/validate?token={token_value}")
        assert response.status_code == 200
        assert response.json()["valid"] is False


@pytest.mark.integration()
class TestPasswordResetOldPasswordInvalidation:
    """Tests for old password invalidation after reset."""

    @pytest.mark.asyncio()
    async def test_old_password_fails_after_reset(self, reset_client):
        """After password reset, the old password should no longer work for login."""
        # Step 1: Request reset
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Step 2: Get token
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

        # Step 3: Reset password
        new_password = "BrandNewPassword789!"
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": new_password},
        )
        assert response.status_code == 200

        # Step 4: Old password should fail
        login_response = await reset_client.post(
            "/auth/token",
            data={"username": _TEST_USER_EMAIL, "password": _TEST_USER_PASSWORD},
        )
        assert login_response.status_code == 401

        # Step 5: New password should work
        login_response = await reset_client.post(
            "/auth/token",
            data={"username": _TEST_USER_EMAIL, "password": new_password},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


@pytest.mark.integration()
class TestPasswordResetExpiredToken:
    """Tests for expired token handling."""

    @pytest.mark.asyncio()
    async def test_expired_token_returns_error(self, reset_client):
        """An expired token should be rejected during confirm."""
        # Request reset to create a token
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Manually expire the token in DB
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

            # Set expires_at to the past
            await session.execute(
                text("""
                    UPDATE verification_tokens
                    SET expires_at = :expired_at
                    WHERE token = :token
                """),
                {
                    "expired_at": datetime.now(UTC) - timedelta(hours=2),
                    "token": token_value,
                },
            )
            await session.commit()

        # Try to use expired token
        response = await reset_client.post(
            "/auth/password-reset/confirm",
            json={"token": token_value, "new_password": "ExpiredPass123!"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_expired_token_validates_as_invalid(self, reset_client):
        """An expired token should validate as invalid."""
        # Request reset
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Expire the token
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            token_value = row[0]

            await session.execute(
                text("""
                    UPDATE verification_tokens
                    SET expires_at = :expired_at
                    WHERE token = :token
                """),
                {
                    "expired_at": datetime.now(UTC) - timedelta(hours=2),
                    "token": token_value,
                },
            )
            await session.commit()

        # Validate should return false
        response = await reset_client.get(f"/auth/password-reset/validate?token={token_value}")
        assert response.status_code == 200
        assert response.json()["valid"] is False


@pytest.mark.integration()
class TestPasswordResetNewTokenInvalidatesOld:
    """Tests that requesting a new token invalidates old ones."""

    @pytest.mark.asyncio()
    async def test_old_token_invalidated_by_new_request(self, reset_client):
        """Requesting a new reset should invalidate previous unused tokens."""
        # First request
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # Get first token
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT token FROM verification_tokens
                    WHERE user_id = :uid AND token_type = 'password_reset' AND used_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"uid": str(_TEST_USER_ID)},
            )
            row = result.fetchone()
            assert row is not None
            first_token = row[0]

        # Second request (should invalidate first token)
        await reset_client.post(
            "/auth/password-reset/request",
            json={"email": _TEST_USER_EMAIL},
        )

        # First token should now be invalid
        response = await reset_client.get(f"/auth/password-reset/validate?token={first_token}")
        assert response.status_code == 200
        assert response.json()["valid"] is False
