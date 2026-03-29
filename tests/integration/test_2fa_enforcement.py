"""Integration tests for 2FA enforcement at login (RAP-238).

Scenarios covered:
  - Normal login without 2FA → succeeds as before
  - Login with 2FA enabled but no totp_code → 401 with "totp_required"
  - Login with 2FA enabled and valid TOTP code → succeeds
  - Login with 2FA enabled and invalid TOTP code → 401
  - Login with 2FA enabled and valid backup code → succeeds
  - Login with 2FA enabled and used/invalid backup code → 401
"""

import pyotp
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine

pytestmark = pytest.mark.asyncio

_TEST_STAFF_ID = "00000000-0000-0000-0000-000000000001"
_TEST_STAFF_EMAIL = "test-staff@refugio.test"
_TEST_STAFF_PASSWORD = "TestPass123!"

_LOGIN_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest_asyncio.fixture(autouse=True)
async def _reset_2fa_and_backup_codes() -> None:
    """Reset 2FA state and backup codes before each test."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("UPDATE users SET totp_secret = NULL, totp_enabled = FALSE WHERE id = :id"),
            {"id": _TEST_STAFF_ID},
        )
        await session.execute(
            text("DELETE FROM totp_backup_codes WHERE user_id = :id"),
            {"id": _TEST_STAFF_ID},
        )
        await session.commit()
    await engine.dispose()


async def _enable_2fa_and_get_secret(client: AsyncClient) -> str:
    """Enable 2FA for the test user and return the TOTP secret."""
    setup_resp = await client.post("/auth/2fa/setup")
    secret = setup_resp.json()["secret"]
    totp = pyotp.TOTP(secret)
    await client.post("/auth/2fa/verify", json={"code": totp.now()})
    return secret


async def test_login_without_2fa_succeeds(client: AsyncClient) -> None:
    """Standard form login works when 2FA is not enabled."""
    response = await client.post(
        "/auth/token",
        data={"username": _TEST_STAFF_EMAIL, "password": _TEST_STAFF_PASSWORD},
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_with_2fa_enabled_no_code_returns_401_totp_required(
    client: AsyncClient,
) -> None:
    """When 2FA is enabled and no totp_code is supplied, login returns 401 with 'totp_required'."""
    await _enable_2fa_and_get_secret(client)

    response = await client.post(
        "/auth/token",
        data={"username": _TEST_STAFF_EMAIL, "password": _TEST_STAFF_PASSWORD},
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 401
    assert response.json()["message"] == "totp_required"


async def test_login_with_2fa_enabled_and_valid_totp_code_succeeds(
    client: AsyncClient,
) -> None:
    """Login with correct TOTP code returns an access token."""
    secret = await _enable_2fa_and_get_secret(client)
    totp = pyotp.TOTP(secret)

    response = await client.post(
        "/auth/token",
        data={
            "username": _TEST_STAFF_EMAIL,
            "password": _TEST_STAFF_PASSWORD,
            "totp_code": totp.now(),
        },
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_with_2fa_enabled_and_invalid_totp_code_returns_401(
    client: AsyncClient,
) -> None:
    """Login with wrong TOTP code is rejected."""
    await _enable_2fa_and_get_secret(client)

    response = await client.post(
        "/auth/token",
        data={
            "username": _TEST_STAFF_EMAIL,
            "password": _TEST_STAFF_PASSWORD,
            "totp_code": "000000",
        },
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 401
    assert response.json()["message"] != "totp_required"


async def test_login_with_2fa_enabled_and_valid_backup_code_succeeds(
    client: AsyncClient,
) -> None:
    """Login with a valid backup code succeeds as an alternative to TOTP."""
    await _enable_2fa_and_get_secret(client)

    # Generate backup codes
    backup_resp = await client.post("/auth/2fa/backup-codes")
    codes = backup_resp.json()["codes"]

    response = await client.post(
        "/auth/token",
        data={
            "username": _TEST_STAFF_EMAIL,
            "password": _TEST_STAFF_PASSWORD,
            "totp_code": codes[0],
        },
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_backup_code_consumed_after_login(client: AsyncClient) -> None:
    """After using a backup code to log in, that code cannot be reused."""
    from src.db.models.totp_backup_code import BACKUP_CODE_COUNT

    await _enable_2fa_and_get_secret(client)
    backup_resp = await client.post("/auth/2fa/backup-codes")
    codes = backup_resp.json()["codes"]

    # Use first code to log in
    await client.post(
        "/auth/token",
        data={
            "username": _TEST_STAFF_EMAIL,
            "password": _TEST_STAFF_PASSWORD,
            "totp_code": codes[0],
        },
        headers=_LOGIN_HEADERS,
    )

    # Count should have decreased by 1
    count_resp = await client.get("/auth/2fa/backup-codes/count")
    assert count_resp.json()["remaining"] == BACKUP_CODE_COUNT - 1


async def test_login_with_invalid_backup_code_returns_401(client: AsyncClient) -> None:
    """Login with a non-existent backup code is rejected."""
    await _enable_2fa_and_get_secret(client)
    # Generate backup codes but don't use them; submit a fake code
    await client.post("/auth/2fa/backup-codes")

    response = await client.post(
        "/auth/token",
        data={
            "username": _TEST_STAFF_EMAIL,
            "password": _TEST_STAFF_PASSWORD,
            "totp_code": "XXXXXXXX",
        },
        headers=_LOGIN_HEADERS,
    )
    assert response.status_code == 401
