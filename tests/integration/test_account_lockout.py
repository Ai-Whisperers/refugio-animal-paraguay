"""Integration tests for account lockout after failed login attempts."""

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
from src.services.account_lockout_service import MAX_FAILED_ATTEMPTS

_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000401")
_USER_EMAIL = "lockout-test@refugio-shelter.org"
_USER_PASSWORD = "TestPass123!"


@pytest_asyncio.fixture
async def lockout_client():
    """Client with a test user for lockout tests."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active,
                                   email_verified, failed_login_attempts, locked_until)
                VALUES (:id, :email, :pwd, 'staff', true, true, 0, NULL)
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = :pwd, is_active = true, email_verified = true,
                    failed_login_attempts = 0, locked_until = NULL
            """),
            {
                "id": str(_USER_ID),
                "email": _USER_EMAIL,
                "pwd": hash_password(_USER_PASSWORD),
            },
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    # Cleanup
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM active_sessions WHERE user_id = :uid"),
            {"uid": str(_USER_ID)},
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": str(_USER_ID)},
        )
        await session.commit()


async def _login(client: AsyncClient, email: str, password: str):
    """Helper to POST /auth/token."""
    return await client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_locks_after_max_failed_attempts(lockout_client):
    """After MAX_FAILED_ATTEMPTS wrong passwords, the account should be locked."""
    client, _ = lockout_client

    # Exhaust all attempts with wrong password
    for i in range(MAX_FAILED_ATTEMPTS):
        resp = await _login(client, _USER_EMAIL, "WrongPassword!")
        if i < MAX_FAILED_ATTEMPTS - 1:
            assert resp.status_code == 401, f"Attempt {i+1} should return 401"
        else:
            # The 5th attempt triggers lockout
            assert resp.status_code == 423, f"Attempt {i+1} should trigger lockout (423)"

    # Next attempt should also be 423 even with correct password
    resp = await _login(client, _USER_EMAIL, _USER_PASSWORD)
    assert resp.status_code == 423
    body = resp.json()
    msg = body.get("message", body.get("detail", ""))
    assert "locked" in msg.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lockout_expires_after_duration(lockout_client):
    """After the lockout period, the user should be able to log in again."""
    client, session_factory = lockout_client

    # Lock the account by setting locked_until in the past and failed attempts at max
    past_lockout = datetime.now(UTC) - timedelta(seconds=10)
    async with session_factory() as session:
        await session.execute(
            text("""
                UPDATE users SET failed_login_attempts = :attempts, locked_until = :until
                WHERE id = :uid
            """),
            {
                "attempts": MAX_FAILED_ATTEMPTS,
                "until": past_lockout,
                "uid": str(_USER_ID),
            },
        )
        await session.commit()

    # Should succeed because lockout has expired
    resp = await _login(client, _USER_EMAIL, _USER_PASSWORD)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_successful_login_resets_failed_attempts(lockout_client):
    """A correct login resets the failed attempt counter."""
    client, session_factory = lockout_client

    # Fail a few times (below threshold)
    for _ in range(3):
        await _login(client, _USER_EMAIL, "WrongPassword!")

    # Now succeed
    resp = await _login(client, _USER_EMAIL, _USER_PASSWORD)
    assert resp.status_code == 200

    # Verify counter was reset in the DB
    async with session_factory() as session:
        result = await session.execute(
            text("SELECT failed_login_attempts FROM users WHERE id = :uid"),
            {"uid": str(_USER_ID)},
        )
        count = result.scalar_one()
        assert count == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_locked_account_rejects_even_correct_password(lockout_client):
    """While locked, even the correct password is rejected."""
    client, session_factory = lockout_client

    # Set active lockout
    future_lockout = datetime.now(UTC) + timedelta(minutes=10)
    async with session_factory() as session:
        await session.execute(
            text("""
                UPDATE users SET failed_login_attempts = :attempts, locked_until = :until
                WHERE id = :uid
            """),
            {
                "attempts": MAX_FAILED_ATTEMPTS,
                "until": future_lockout,
                "uid": str(_USER_ID),
            },
        )
        await session.commit()

    resp = await _login(client, _USER_EMAIL, _USER_PASSWORD)
    assert resp.status_code == 423
    body = resp.json()
    msg = body.get("message", body.get("detail", ""))
    assert "locked" in msg.lower()
