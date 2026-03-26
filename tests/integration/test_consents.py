"""Integration tests for GDPR consent tracking endpoints.

Tests the consent API endpoints with a live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_consents.py
"""

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.auth.utils import hash_password
from src.config import Settings
from src.db.session import init_engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_CONSENT_USER_ID = uuid4()
_TEST_CONSENT_USER_EMAIL = f"consent-user-{uuid4().hex[:8]}@refugio.test"


async def _ensure_user_consents_table(settings: Settings) -> None:
    """Create user_consents table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_consents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    consent_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    opt_in_date TIMESTAMPTZ NOT NULL DEFAULT now(),
                    opt_out_date TIMESTAMPTZ,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(500),
                    method VARCHAR(30) NOT NULL DEFAULT 'user_self_service',
                    granted_by_staff_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    notes TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_user_consent_type UNIQUE (user_id, consent_type)
                )
            """))
        await session.commit()


async def _create_test_user(settings: Settings, user_id: UUID, email: str) -> None:
    """Create a test user for consent operations."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (email) DO NOTHING
            """),
            {"id": str(user_id), "email": email, "pwd": hash_password("TestPass123!")},
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_consent_table() -> None:
    """Ensure user_consents table and test user exist before tests."""
    settings = Settings()
    await _ensure_user_consents_table(settings)
    await _create_test_user(settings, _TEST_CONSENT_USER_ID, _TEST_CONSENT_USER_EMAIL)


# ---------------------------------------------------------------------------
# PUT /users/{user_id}/consents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_grant_consent_returns_200(client: AsyncClient) -> None:
    """Granting consent creates a record and returns it."""
    user_id = _TEST_CONSENT_USER_ID
    response = await client.put(
        f"/users/{user_id}/consents",
        json={
            "consents": [
                {"consent_type": "newsletter", "granted": True},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["consent_type"] == "newsletter"
    assert body[0]["status"] == "active"
    assert body[0]["user_id"] == str(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_grant_multiple_consents(client: AsyncClient) -> None:
    """Granting multiple consents at once."""
    user_id = _TEST_CONSENT_USER_ID
    response = await client.put(
        f"/users/{user_id}/consents",
        json={
            "consents": [
                {"consent_type": "marketing_email", "granted": True},
                {"consent_type": "donation_receipts", "granted": True},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    types = {c["consent_type"] for c in body}
    assert "marketing_email" in types
    assert "donation_receipts" in types


@pytest.mark.asyncio
@pytest.mark.integration
async def test_revoke_consent(client: AsyncClient) -> None:
    """Revoking consent updates status to revoked."""
    user_id = _TEST_CONSENT_USER_ID

    # First grant
    await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "sms_updates", "granted": True}]},
    )

    # Then revoke
    response = await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "sms_updates", "granted": False}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "revoked"
    assert body[0]["opt_out_date"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_grant_consent_is_idempotent(client: AsyncClient) -> None:
    """Re-granting active consent is a no-op."""
    user_id = _TEST_CONSENT_USER_ID

    # Grant twice
    await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "event_invitations", "granted": True}]},
    )
    response = await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "event_invitations", "granted": True}]},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "active"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consent_for_nonexistent_user_returns_404(client: AsyncClient) -> None:
    """Updating consents for non-existent user returns 404."""
    fake_id = uuid4()
    response = await client.put(
        f"/users/{fake_id}/consents",
        json={"consents": [{"consent_type": "newsletter", "granted": True}]},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /users/{user_id}/consents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_consent_summary(client: AsyncClient) -> None:
    """Get consent summary returns all types with active/inactive status."""
    user_id = _TEST_CONSENT_USER_ID

    # Grant newsletter consent
    await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "newsletter", "granted": True}]},
    )

    response = await client.get(f"/users/{user_id}/consents")
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert isinstance(body["consents"], dict)
    # Newsletter should be active
    assert body["consents"]["newsletter"] is True


# ---------------------------------------------------------------------------
# GET /users/{user_id}/consents/details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_consent_details(client: AsyncClient) -> None:
    """Get consent details returns full records."""
    user_id = _TEST_CONSENT_USER_ID

    # Grant a consent first
    await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "newsletter", "granted": True}]},
    )

    response = await client.get(f"/users/{user_id}/consents/details")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    # Should have at least the newsletter consent
    newsletter_records = [c for c in body if c["consent_type"] == "newsletter"]
    assert len(newsletter_records) >= 1


# ---------------------------------------------------------------------------
# Invalid consent type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_consent_type_returns_422(client: AsyncClient) -> None:
    """Invalid consent type returns 422 validation error."""
    user_id = _TEST_CONSENT_USER_ID
    response = await client.put(
        f"/users/{user_id}/consents",
        json={"consents": [{"consent_type": "invalid_type", "granted": True}]},
    )
    assert response.status_code == 422
