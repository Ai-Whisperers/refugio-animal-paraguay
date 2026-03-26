"""Integration tests for password reset and email verification endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.token_service import (
    create_verification_token,
    hash_token,
)
from src.auth.utils import hash_password, verify_password
from src.config import Settings
from src.db.models.verification_token import TokenType
from src.db.session import init_engine

# Deterministic test user for password reset tests
_RESET_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
_RESET_USER_EMAIL = "reset-test@refugio-example.com"
_RESET_USER_PASSWORD = "OldPassword123!"

# Unverified user for verification tests
_UNVERIFIED_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000011")
_UNVERIFIED_USER_EMAIL = "unverified@refugio-example.com"
_UNVERIFIED_USER_PASSWORD = "Unverified123!"


@pytest_asyncio.fixture
async def anon_client() -> AsyncClient:
    """Unauthenticated AsyncClient for public endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a raw DB session for test setup/assertions."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def seed_test_users(db_session: AsyncSession) -> None:
    """Seed a verified user and an unverified user for tests."""
    # Verified user (for password reset tests)
    await db_session.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, role, is_active, is_verified)
            VALUES (:id, :email, :pwd, 'staff', true, true)
            ON CONFLICT (id) DO UPDATE SET
                email = :email,
                hashed_password = :pwd,
                is_verified = true,
                is_active = true
        """),
        {
            "id": str(_RESET_USER_ID),
            "email": _RESET_USER_EMAIL,
            "pwd": hash_password(_RESET_USER_PASSWORD),
        },
    )

    # Unverified user (for email verification tests)
    await db_session.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, role, is_active, is_verified)
            VALUES (:id, :email, :pwd, 'staff', true, false)
            ON CONFLICT (id) DO UPDATE SET
                email = :email,
                hashed_password = :pwd,
                is_verified = false,
                is_active = true
        """),
        {
            "id": str(_UNVERIFIED_USER_ID),
            "email": _UNVERIFIED_USER_EMAIL,
            "pwd": hash_password(_UNVERIFIED_USER_PASSWORD),
        },
    )

    # Clean up any leftover tokens
    await db_session.execute(
        text("DELETE FROM verification_tokens WHERE user_id IN (:id1, :id2)"),
        {"id1": str(_RESET_USER_ID), "id2": str(_UNVERIFIED_USER_ID)},
    )
    await db_session.commit()


# --- Login: unverified user rejection ---


@pytest.mark.asyncio
async def test_login_rejects_unverified_user(anon_client: AsyncClient) -> None:
    """Unverified users get 403 with a clear message."""
    resp = await anon_client.post(
        "/auth/token",
        data={"username": _UNVERIFIED_USER_EMAIL, "password": _UNVERIFIED_USER_PASSWORD},
    )
    assert resp.status_code == 403
    assert "not verified" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_accepts_verified_user(anon_client: AsyncClient) -> None:
    """Verified users can log in normally."""
    resp = await anon_client.post(
        "/auth/token",
        data={"username": _RESET_USER_EMAIL, "password": _RESET_USER_PASSWORD},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# --- Email Verification ---


@pytest.mark.asyncio
async def test_verify_email_with_valid_token(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A valid verification token marks the user as verified."""
    token = await create_verification_token(db_session, _UNVERIFIED_USER_ID, TokenType.EMAIL_VERIFY)
    await db_session.commit()

    resp = await anon_client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200
    assert "verified" in resp.json()["message"].lower()

    # User should now be verified in DB
    result = await db_session.execute(
        text("SELECT is_verified FROM users WHERE id = :id"),
        {"id": str(_UNVERIFIED_USER_ID)},
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] is True


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token(anon_client: AsyncClient) -> None:
    """An invalid token returns 400."""
    resp = await anon_client.post("/auth/verify-email", json={"token": "totally-invalid-token"})
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_token_is_single_use(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A verification token cannot be reused."""
    token = await create_verification_token(db_session, _UNVERIFIED_USER_ID, TokenType.EMAIL_VERIFY)
    await db_session.commit()

    # First use succeeds
    resp1 = await anon_client.post("/auth/verify-email", json={"token": token})
    assert resp1.status_code == 200

    # Second use fails
    resp2 = await anon_client.post("/auth/verify-email", json={"token": token})
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_expired_token(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """An expired verification token is rejected."""
    from datetime import UTC, datetime

    token = await create_verification_token(db_session, _UNVERIFIED_USER_ID, TokenType.EMAIL_VERIFY)
    # Manually expire the token
    await db_session.execute(
        text("""
            UPDATE verification_tokens SET expires_at = :expired
            WHERE token_hash = :hash
        """),
        {
            "expired": datetime(2020, 1, 1, tzinfo=UTC),
            "hash": hash_token(token),
        },
    )
    await db_session.commit()

    resp = await anon_client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 400


# --- Resend Verification ---


@pytest.mark.asyncio
async def test_resend_verification_returns_generic_message(
    anon_client: AsyncClient,
) -> None:
    """Resend endpoint returns success regardless of whether email exists."""
    resp = await anon_client.post(
        "/auth/resend-verification",
        json={"email": _UNVERIFIED_USER_EMAIL},
    )
    assert resp.status_code == 200
    assert "check your inbox" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_resend_verification_nonexistent_email_same_response(
    anon_client: AsyncClient,
) -> None:
    """Non-existent email gets the same generic response (no enumeration)."""
    resp = await anon_client.post(
        "/auth/resend-verification",
        json={"email": "does-not-exist@example.com"},
    )
    assert resp.status_code == 200
    assert "check your inbox" in resp.json()["message"].lower()


# --- Password Reset Initiation ---


@pytest.mark.asyncio
async def test_password_reset_initiation_returns_generic_message(
    anon_client: AsyncClient,
) -> None:
    """Reset initiation returns success regardless of email existence."""
    resp = await anon_client.post(
        "/auth/password-reset",
        json={"email": _RESET_USER_EMAIL},
    )
    assert resp.status_code == 200
    assert "check your inbox" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_password_reset_initiation_nonexistent_email_same_response(
    anon_client: AsyncClient,
) -> None:
    """Non-existent email returns same generic response."""
    resp = await anon_client.post(
        "/auth/password-reset",
        json={"email": "nobody@nowhere.com"},
    )
    assert resp.status_code == 200
    assert "check your inbox" in resp.json()["message"].lower()


# --- Password Reset Confirmation ---


@pytest.mark.asyncio
async def test_password_reset_confirm_with_valid_token(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A valid reset token allows setting a new password."""
    token = await create_verification_token(db_session, _RESET_USER_ID, TokenType.PASSWORD_RESET)
    await db_session.commit()

    new_password = "BrandNewPass456!"
    resp = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": new_password},
    )
    assert resp.status_code == 200
    assert "reset successfully" in resp.json()["message"].lower()

    # Verify the password was actually changed
    result = await db_session.execute(
        text("SELECT hashed_password FROM users WHERE id = :id"),
        {"id": str(_RESET_USER_ID)},
    )
    row = result.fetchone()
    assert row is not None
    assert verify_password(new_password, row[0])


@pytest.mark.asyncio
async def test_password_reset_confirm_invalid_token(
    anon_client: AsyncClient,
) -> None:
    """An invalid reset token returns 400."""
    resp = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": "bogus-token", "new_password": "NewPass123!"},
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_password_reset_token_is_single_use(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A reset token cannot be reused."""
    token = await create_verification_token(db_session, _RESET_USER_ID, TokenType.PASSWORD_RESET)
    await db_session.commit()

    # First use succeeds
    resp1 = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "FirstReset123!"},
    )
    assert resp1.status_code == 200

    # Second use fails
    resp2 = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "SecondReset123!"},
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_short_password_rejected(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Password shorter than 8 chars is rejected by schema validation."""
    token = await create_verification_token(db_session, _RESET_USER_ID, TokenType.PASSWORD_RESET)
    await db_session.commit()

    resp = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "short"},
    )
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_password_reset_expired_token_rejected(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """An expired reset token is rejected."""
    from datetime import UTC, datetime

    token = await create_verification_token(db_session, _RESET_USER_ID, TokenType.PASSWORD_RESET)
    await db_session.execute(
        text("""
            UPDATE verification_tokens SET expires_at = :expired
            WHERE token_hash = :hash
        """),
        {
            "expired": datetime(2020, 1, 1, tzinfo=UTC),
            "hash": hash_token(token),
        },
    )
    await db_session.commit()

    resp = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewPass123!"},
    )
    assert resp.status_code == 400


# --- Cross-type token validation ---


@pytest.mark.asyncio
async def test_verify_email_token_cannot_reset_password(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """An email verification token cannot be used for password reset."""
    token = await create_verification_token(db_session, _RESET_USER_ID, TokenType.EMAIL_VERIFY)
    await db_session.commit()

    resp = await anon_client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "CrossType123!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_token_cannot_verify_email(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A password reset token cannot be used for email verification."""
    token = await create_verification_token(
        db_session, _UNVERIFIED_USER_ID, TokenType.PASSWORD_RESET
    )
    await db_session.commit()

    resp = await anon_client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 400
