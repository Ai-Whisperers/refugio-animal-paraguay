"""Integration tests for the password reset flow.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_password_reset.py

Covers:
  - POST /auth/password-reset-request (request reset)
  - POST /auth/password-reset/{token} (complete reset)
  - Token expiry, reuse, same-password rejection
  - No account enumeration (identical responses)
  - Login with new password after reset
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.password_reset import generate_reset_token, hash_token
from src.auth.utils import hash_password
from src.config import Settings
from src.db.session import init_engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_PASSWORD = "OldPassword123!"
_NEW_PASSWORD = "NewSecurePass99!"


def _unique_email() -> str:
    return f"reset-{uuid4().hex[:8]}@example.com"


async def _setup_user(email: str, password: str = _TEST_PASSWORD) -> str:
    """Create a test user and return their ID. Uses a fresh session."""
    settings = Settings()
    engine = init_engine(settings)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    user_id = str(uuid4())
    async with factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (email) DO UPDATE SET
                    hashed_password = :pwd,
                    is_active = true
                RETURNING id
                """),
            {
                "id": user_id,
                "email": email,
                "pwd": hash_password(password),
            },
        )
        result = await session.execute(
            text("SELECT id::text FROM users WHERE email = :email"),
            {"email": email},
        )
        user_id = result.scalar_one()
        await session.commit()
    return user_id


async def _insert_token(
    user_id: str,
    plaintext: str,
    expires_minutes: int = 60,
) -> None:
    """Insert a reset token directly into the DB."""
    settings = Settings()
    engine = init_engine(settings)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    th = hash_token(plaintext)
    exp = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) "
                "VALUES (:uid, :th, :exp)"
            ),
            {"uid": user_id, "th": th, "exp": exp},
        )
        await session.commit()


async def _cleanup_tokens(user_id: str) -> None:
    """Remove all reset tokens for a user."""
    settings = Settings()
    engine = init_engine(settings)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text("DELETE FROM password_reset_tokens WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await session.commit()


async def _count_tokens(user_id: str) -> int:
    """Count reset tokens for a user."""
    settings = Settings()
    engine = init_engine(settings)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(
            text("SELECT count(*) FROM password_reset_tokens WHERE user_id = :uid"),
            {"uid": user_id},
        )
        return result.scalar_one()


# ---------------------------------------------------------------------------
# POST /auth/password-reset-request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reset_request_returns_200_for_valid_email() -> None:
    """Known email returns 200 with generic message."""
    email = _unique_email()
    await _setup_user(email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset-request",
            json={"email": email},
        )
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reset_request_returns_200_for_unknown_email() -> None:
    """Unknown email returns identical 200 -- no enumeration."""
    init_engine(Settings())  # Ensure engine on current event loop
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset-request",
            json={"email": "nonexistent@example.com"},
        )
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reset_request_creates_token_in_db() -> None:
    """Requesting reset for a valid user creates a hashed token row."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post(
            "/auth/password-reset-request",
            json={"email": email},
        )

    count = await _count_tokens(user_id)
    assert count >= 1
    await _cleanup_tokens(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reset_request_invalid_email_format_returns_422() -> None:
    """Malformed email rejected by Pydantic."""
    init_engine(Settings())  # Ensure engine on current event loop
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset-request",
            json={"email": "not-an-email"},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/password-reset/{token} -- happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_with_valid_token() -> None:
    """Valid token + valid new password resets the password."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    plaintext = generate_reset_token()
    await _insert_token(user_id, plaintext)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            f"/auth/password-reset/{plaintext}",
            json={"new_password": _NEW_PASSWORD},
        )
    assert resp.status_code == 200
    assert "successfully" in resp.json()["message"].lower()

    # Verify login with new password works
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        login_resp = await c.post(
            "/auth/token",
            data={"username": email, "password": _NEW_PASSWORD},
        )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_deletes_all_user_tokens() -> None:
    """After reset, all tokens for the user are deleted."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    # Insert two tokens
    tokens = []
    for _ in range(2):
        pt = generate_reset_token()
        tokens.append(pt)
        await _insert_token(user_id, pt)

    # Use the first token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            f"/auth/password-reset/{tokens[0]}",
            json={"new_password": "BrandNewPass1!"},
        )
    assert resp.status_code == 200

    # Second token should now be invalid
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp2 = await c.post(
            f"/auth/password-reset/{tokens[1]}",
            json={"new_password": "AnotherPass2!"},
        )
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# POST /auth/password-reset/{token} -- error cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_invalid_token_returns_404() -> None:
    """Completely unknown token returns 404."""
    init_engine(Settings())  # Ensure engine on current event loop
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset/bogus-token-value",
            json={"new_password": _NEW_PASSWORD},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_expired_token_returns_404() -> None:
    """Expired token returns 404 (same as invalid -- no info leak)."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    # Insert an already-expired token
    plaintext = generate_reset_token()
    await _insert_token(user_id, plaintext, expires_minutes=-10)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            f"/auth/password-reset/{plaintext}",
            json={"new_password": _NEW_PASSWORD},
        )
    assert resp.status_code == 404
    await _cleanup_tokens(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_same_password_returns_400() -> None:
    """Cannot reset to the same password."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    plaintext = generate_reset_token()
    await _insert_token(user_id, plaintext)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            f"/auth/password-reset/{plaintext}",
            json={"new_password": _TEST_PASSWORD},
        )
    assert resp.status_code == 400
    assert "different" in resp.json()["detail"].lower()
    await _cleanup_tokens(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_short_password_returns_422() -> None:
    """Password below minimum length rejected by schema validation."""
    init_engine(Settings())  # Ensure engine on current event loop
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset/any-token",
            json={"new_password": "short"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_reset_token_cannot_be_reused() -> None:
    """Token is consumed on first successful use."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    plaintext = generate_reset_token()
    await _insert_token(user_id, plaintext)

    # First use -- succeeds
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp1 = await c.post(
            f"/auth/password-reset/{plaintext}",
            json={"new_password": "FirstNewPass1!"},
        )
    assert resp1.status_code == 200

    # Second use -- fails
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp2 = await c.post(
            f"/auth/password-reset/{plaintext}",
            json={"new_password": "SecondNewPass2!"},
        )
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Full flow: request -> complete -> login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_reset_flow_request_then_complete_then_login() -> None:
    """End-to-end: request reset, insert known token, complete, login."""
    email = _unique_email()
    user_id = await _setup_user(email)
    await _cleanup_tokens(user_id)

    # Step 1: Request reset (creates token in DB)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/auth/password-reset-request",
            json={"email": email},
        )
    assert resp.status_code == 200

    # Step 2: Since we can't extract the plaintext from the API response,
    # insert a known token directly for the completion step
    await _cleanup_tokens(user_id)
    known_plaintext = generate_reset_token()
    await _insert_token(user_id, known_plaintext)

    final_password = "FinalResetPass3!"

    # Step 3: Complete reset
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp2 = await c.post(
            f"/auth/password-reset/{known_plaintext}",
            json={"new_password": final_password},
        )
    assert resp2.status_code == 200

    # Step 4: Login with new password
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        login_resp = await c.post(
            "/auth/token",
            data={"username": email, "password": final_password},
        )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Step 5: Old password should fail
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        old_login = await c.post(
            "/auth/token",
            data={"username": email, "password": _TEST_PASSWORD},
        )
    assert old_login.status_code == 401
