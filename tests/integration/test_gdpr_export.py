"""Integration tests for GDPR data export endpoint.

Tests POST /gdpr/data-export with a live database.
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

_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-a00000000059")
_ADMIN_EMAIL = f"export-admin-{uuid.uuid4().hex[:8]}@refugio.test"

_TARGET_USER_ID = uuid.UUID("00000000-0000-0000-0000-b00000000059")
_TARGET_USER_EMAIL = f"export-target-{uuid.uuid4().hex[:8]}@refugio.test"

_TARGET_DONOR_ID = uuid.UUID("00000000-0000-0000-0000-c00000000059")
_TARGET_ADOPTER_ID = uuid.UUID("00000000-0000-0000-0000-d00000000059")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_test_data(settings: Settings) -> None:
    """Create admin user, target user, donor, and adopter for export tests."""
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

        # Target user
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
                "name": "Export Test Donor",
                "email": f"export-donor-{uuid.uuid4().hex[:8]}@refugio.test",
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
                "name": "Export Test Adopter",
                "email": f"export-adopter-{uuid.uuid4().hex[:8]}@refugio.test",
                "phone": "+595981234567",
                "addr": "123 Export St, Asuncion",
            },
        )

        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with admin role for GDPR export endpoint."""
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
# POST /gdpr/data-export — admin auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_returns_403_for_staff(client: AsyncClient) -> None:
    """Staff users cannot trigger GDPR export — admin-only endpoint."""
    resp = await client.post(
        "/gdpr/data-export",
        json={"user_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_user_only(admin_client: AsyncClient) -> None:
    """Export user data without donor/adopter linked records."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={"user_id": str(_TARGET_USER_ID)},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["export_metadata"]["user_id"] == str(_TARGET_USER_ID)
    assert body["export_metadata"]["format_version"] == "1.0"
    assert body["user_profile"] is not None
    assert body["user_profile"]["email"] == _TARGET_USER_EMAIL
    assert body["donor_data"] is None
    assert body["adopter_data"] is None
    assert isinstance(body["consents"], list)
    assert isinstance(body["notifications"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_with_donor(admin_client: AsyncClient) -> None:
    """Export user data with linked donor record."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={
            "user_id": str(_TARGET_USER_ID),
            "donor_id": str(_TARGET_DONOR_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["donor_data"] is not None
    assert body["donor_data"]["profile"]["full_name"] == "Export Test Donor"
    assert body["donor_data"]["profile"]["country"] == "NL"
    assert isinstance(body["donor_data"]["donations"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_with_adopter(admin_client: AsyncClient) -> None:
    """Export user data with linked adopter record."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={
            "user_id": str(_TARGET_USER_ID),
            "adopter_id": str(_TARGET_ADOPTER_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["adopter_data"] is not None
    assert body["adopter_data"]["profile"]["full_name"] == "Export Test Adopter"
    assert isinstance(body["adopter_data"]["adoption_requests"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_full(admin_client: AsyncClient) -> None:
    """Full export request with user, donor, and adopter."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={
            "user_id": str(_TARGET_USER_ID),
            "donor_id": str(_TARGET_DONOR_ID),
            "adopter_id": str(_TARGET_ADOPTER_ID),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["export_metadata"]["user_id"] == str(_TARGET_USER_ID)
    assert "Article 15" in body["export_metadata"]["gdpr_articles"][0]
    assert "Article 20" in body["export_metadata"]["gdpr_articles"][1]
    assert body["user_profile"] is not None
    assert body["donor_data"] is not None
    assert body["adopter_data"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_nonexistent_user(admin_client: AsyncClient) -> None:
    """Export for non-existent user returns 200 with null profile."""
    fake_id = str(uuid.uuid4())
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={"user_id": fake_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_profile"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_validates_uuid(admin_client: AsyncClient) -> None:
    """Invalid UUID in request body returns 422."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={"user_id": "not-a-uuid"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_missing_user_id(admin_client: AsyncClient) -> None:
    """Missing required user_id field returns 422."""
    resp = await admin_client.post(
        "/gdpr/data-export",
        json={},
    )
    assert resp.status_code == 422
