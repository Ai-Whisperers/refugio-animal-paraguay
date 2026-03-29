"""Integration tests for admin 2FA reset endpoint (RAP-239).

Scenarios covered:
  - Admin can reset 2FA for a 2FA-enabled user → 204, user's 2FA is disabled
  - Admin reset clears backup codes too
  - Non-admin (staff) cannot call the admin reset endpoint → 403
  - Reset for a non-existent user_id → 404
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

pytestmark = pytest.mark.asyncio

_TEST_STAFF_ID = "00000000-0000-0000-0000-000000000001"
_TEST_STAFF_EMAIL = "test-staff@refugio.test"
_TEST_STAFF_PASSWORD = "TestPass123!"

_ADMIN_ID = "00000000-0000-0000-0000-000000000099"
_ADMIN_EMAIL = "test-admin-2fa@refugio.test"


async def _upsert_admin(settings: Settings) -> None:
    """Ensure the admin test user exists."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, email_verified)
                VALUES (:id, :email, :pwd, 'admin', true, true)
                ON CONFLICT (email) DO UPDATE SET role = 'admin', is_active = true
            """),
            {"id": _ADMIN_ID, "email": _ADMIN_EMAIL, "pwd": hash_password("AdminPass123!")},
        )
        await session.commit()
    await engine.dispose()


@pytest_asyncio.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with admin role."""
    settings = Settings()
    await _upsert_admin(settings)
    token = create_access_token(
        data={"sub": _ADMIN_ID},
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


@pytest_asyncio.fixture(autouse=True)
async def _reset_2fa_state() -> None:
    """Reset 2FA state for the test staff user before each test."""
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


async def _enable_2fa(client: AsyncClient) -> str:
    """Enable 2FA for the test staff user; return the secret."""
    import pyotp

    setup_resp = await client.post("/auth/2fa/setup")
    secret = setup_resp.json()["secret"]
    totp = pyotp.TOTP(secret)
    await client.post("/auth/2fa/verify", json={"code": totp.now()})
    return secret


async def test_admin_can_reset_2fa_for_user(
    client: AsyncClient,
    admin_client: AsyncClient,
) -> None:
    """Admin DELETE /auth/2fa/admin/users/{id} disables 2FA and returns 204."""
    await _enable_2fa(client)

    # Confirm 2FA is enabled
    status_resp = await client.get("/auth/2fa/status")
    assert status_resp.json()["enabled"] is True

    # Admin resets it
    reset_resp = await admin_client.delete(f"/auth/2fa/admin/users/{_TEST_STAFF_ID}")
    assert reset_resp.status_code == 204

    # Confirm 2FA is now disabled
    status_resp = await client.get("/auth/2fa/status")
    assert status_resp.json()["enabled"] is False


async def test_admin_reset_also_clears_backup_codes(
    client: AsyncClient,
    admin_client: AsyncClient,
) -> None:
    """After admin reset, the user's backup codes count should be 0."""
    from src.db.models.totp_backup_code import BACKUP_CODE_COUNT

    await _enable_2fa(client)
    await client.post("/auth/2fa/backup-codes")  # generate backup codes

    count_resp = await client.get("/auth/2fa/backup-codes/count")
    assert count_resp.json()["remaining"] == BACKUP_CODE_COUNT

    # Admin resets 2FA
    await admin_client.delete(f"/auth/2fa/admin/users/{_TEST_STAFF_ID}")

    # Backup codes should be gone
    count_resp = await client.get("/auth/2fa/backup-codes/count")
    assert count_resp.json()["remaining"] == 0


async def test_staff_cannot_call_admin_reset(client: AsyncClient) -> None:
    """Staff user calling the admin endpoint should receive 403."""
    resp = await client.delete(f"/auth/2fa/admin/users/{_TEST_STAFF_ID}")
    assert resp.status_code == 403


async def test_admin_reset_nonexistent_user_returns_404(
    admin_client: AsyncClient,
) -> None:
    """Requesting reset for an unknown user_id should return 404."""
    nonexistent_id = str(uuid.uuid4())
    resp = await admin_client.delete(f"/auth/2fa/admin/users/{nonexistent_id}")
    assert resp.status_code == 404


async def test_admin_reset_works_even_when_2fa_not_enabled(
    client: AsyncClient,
    admin_client: AsyncClient,
) -> None:
    """Admin can call reset for a user who has no 2FA active — idempotent 204."""
    # 2FA is already disabled (autouse fixture ensures this)
    status_resp = await client.get("/auth/2fa/status")
    assert status_resp.json()["enabled"] is False

    # Should still succeed
    reset_resp = await admin_client.delete(f"/auth/2fa/admin/users/{_TEST_STAFF_ID}")
    assert reset_resp.status_code == 204
