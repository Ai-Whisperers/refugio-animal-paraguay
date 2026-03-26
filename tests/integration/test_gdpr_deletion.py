"""Integration tests for GDPR data deletion endpoint.

Tests POST /gdpr/deletion-request with a live database.
Requires a live PostgreSQL instance (refugio_dev).
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

# ---------------------------------------------------------------------------
# Deterministic IDs for test data
# ---------------------------------------------------------------------------

_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-a00000000058")
_ADMIN_EMAIL = f"gdpr-admin-{uuid.uuid4().hex[:8]}@refugio.test"

_TARGET_USER_ID = uuid.UUID("00000000-0000-0000-0000-b00000000058")
_TARGET_USER_EMAIL = f"gdpr-target-{uuid.uuid4().hex[:8]}@refugio.test"

_TARGET_DONOR_ID = uuid.UUID("00000000-0000-0000-0000-c00000000058")
_TARGET_ADOPTER_ID = uuid.UUID("00000000-0000-0000-0000-d00000000058")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_test_data(settings: Settings) -> None:
    """Create admin user, target user, donor, and adopter for deletion tests."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        pwd = hash_password("TestPass123!")

        # Admin user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'admin', true)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    is_active = true
            """),
            {"id": str(_ADMIN_USER_ID), "email": _ADMIN_EMAIL, "pwd": pwd},
        )

        # Target user (to be deleted)
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    is_active = true
            """),
            {"id": str(_TARGET_USER_ID), "email": _TARGET_USER_EMAIL, "pwd": pwd},
        )

        # Donor record
        await session.execute(
            text("""
                INSERT INTO donors (id, full_name, email, country)
                VALUES (:id, :name, :email, :country)
                ON CONFLICT (id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    country = EXCLUDED.country
            """),
            {
                "id": str(_TARGET_DONOR_ID),
                "name": "Test Donor",
                "email": f"donor-{uuid.uuid4().hex[:8]}@refugio.test",
                "country": "NL",
            },
        )

        # Adopter record
        await session.execute(
            text("""
                INSERT INTO adopters (id, full_name, email, phone, address)
                VALUES (:id, :name, :email, :phone, :addr)
                ON CONFLICT (id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    address = EXCLUDED.address
            """),
            {
                "id": str(_TARGET_ADOPTER_ID),
                "name": "Test Adopter",
                "email": f"adopter-{uuid.uuid4().hex[:8]}@refugio.test",
                "phone": "+595981234567",
                "addr": "123 Test St, Asuncion",
            },
        )

        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with admin role for GDPR endpoints."""
    settings = Settings()
    await _setup_test_data(settings)

    token = create_access_token(
        data={"sub": str(_ADMIN_USER_ID)},
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


# ---------------------------------------------------------------------------
# POST /gdpr/deletion-request — admin auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_returns_403_for_staff(client: AsyncClient) -> None:
    """Staff users cannot trigger GDPR deletion — admin-only endpoint."""
    resp = await client.post(
        "/gdpr/deletion-request",
        json={"user_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_returns_401_without_auth(client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    # Send request without Authorization header
    resp = await client.post(
        "/gdpr/deletion-request",
        json={"user_id": str(uuid.uuid4())},
        headers={"Authorization": ""},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_user_only(admin_client: AsyncClient) -> None:
    """Delete user data without donor/adopter linked records."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={"user_id": str(_TARGET_USER_ID)},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(_TARGET_USER_ID)
    assert body["user_deactivated"] is True
    assert body["consents_deleted"] >= 0
    assert body["notifications_deleted"] >= 0
    assert body["donor_anonymized"] is False
    assert body["adopter_anonymized"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_with_donor(admin_client: AsyncClient) -> None:
    """Delete user data with linked donor record."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={
            "user_id": str(_TARGET_USER_ID),
            "donor_id": str(_TARGET_DONOR_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["donor_anonymized"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_with_adopter(admin_client: AsyncClient) -> None:
    """Delete user data with linked adopter record."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={
            "user_id": str(_TARGET_USER_ID),
            "adopter_id": str(_TARGET_ADOPTER_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["adopter_anonymized"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_full(admin_client: AsyncClient) -> None:
    """Full deletion request with user, donor, and adopter."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={
            "user_id": str(_TARGET_USER_ID),
            "donor_id": str(_TARGET_DONOR_ID),
            "adopter_id": str(_TARGET_ADOPTER_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(_TARGET_USER_ID)
    assert isinstance(body["user_deactivated"], bool)
    assert isinstance(body["consents_deleted"], int)
    assert isinstance(body["notifications_deleted"], int)
    assert isinstance(body["donor_anonymized"], bool)
    assert isinstance(body["adopter_anonymized"], bool)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_nonexistent_user(admin_client: AsyncClient) -> None:
    """Deletion request for non-existent user still returns 200."""
    fake_id = str(uuid.uuid4())
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={"user_id": fake_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_deactivated"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_validates_uuid(admin_client: AsyncClient) -> None:
    """Invalid UUID in request body returns 422."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={"user_id": "not-a-uuid"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deletion_request_missing_user_id(admin_client: AsyncClient) -> None:
    """Missing required user_id field returns 422."""
    resp = await admin_client.post(
        "/gdpr/deletion-request",
        json={},
    )
    assert resp.status_code == 422
