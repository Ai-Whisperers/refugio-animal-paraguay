"""Integration tests for GET /portal/dashboard endpoint."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]

# Test user IDs
_ADOPTER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000301")
_DONOR_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000302")
_EMPTY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000303")
_ADOPTER_EMAIL = "dashboard-adopter@refugio-shelter.org"
_DONOR_EMAIL = "dashboard-donor@refugio-shelter.org"
_EMPTY_EMAIL = "dashboard-empty@refugio-shelter.org"

# Test data IDs
_ADOPTER_PROFILE_ID = uuid.UUID("00000000-0000-0000-0000-000000000311")
_DONOR_PROFILE_ID = uuid.UUID("00000000-0000-0000-0000-000000000312")
_ANIMAL_ID_1 = uuid.UUID("00000000-0000-0000-0000-000000000321")
_ANIMAL_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000322")


def _make_client(settings: Settings, user_id: uuid.UUID) -> AsyncClient:
    """Create an authenticated test client for a given user."""
    token = create_access_token(
        data={"sub": str(user_id)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest_asyncio.fixture
async def dashboard_setup() -> AsyncGenerator[Settings, None]:
    """Set up test users, adopter profile, donor profile, animals, and related data."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create test users
        for uid, email, role, name in [
            (_ADOPTER_USER_ID, _ADOPTER_EMAIL, "adopter", "Maria Garcia"),
            (_DONOR_USER_ID, _DONOR_EMAIL, "donor", "Jan van Dijk"),
            (_EMPTY_USER_ID, _EMPTY_EMAIL, "volunteer", "Empty User"),
        ]:
            await session.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, role, is_active, email_verified, full_name)
                    VALUES (:id, :email, :pwd, :role, true, true, :name)
                    ON CONFLICT (id) DO UPDATE SET
                        email = :email, role = :role, is_active = true,
                        email_verified = true, full_name = :name
                """),
                {
                    "id": str(uid),
                    "email": email,
                    "pwd": hash_password("TestPass123!"),
                    "role": role,
                    "name": name,
                },
            )

        # Create test animals
        for aid, name, species in [
            (_ANIMAL_ID_1, "Luna", "dog"),
            (_ANIMAL_ID_2, "Michi", "cat"),
        ]:
            await session.execute(
                text("""
                    INSERT INTO animals (id, name, species, status, gender, birth_date)
                    VALUES (:id, :name, :species, 'available', 'female', '2023-01-01')
                    ON CONFLICT (id) DO UPDATE SET name = :name, species = :species
                """),
                {"id": str(aid), "name": name, "species": species},
            )

        # Create adopter profile linked by email
        await session.execute(
            text("""
                INSERT INTO adopters (id, full_name, email, phone)
                VALUES (:id, 'Maria Garcia', :email, '+595981000301')
                ON CONFLICT (id) DO UPDATE SET email = :email
            """),
            {"id": str(_ADOPTER_PROFILE_ID), "email": _ADOPTER_EMAIL},
        )

        # Create adoption requests
        now = datetime.now(UTC)
        for i, (animal_id, status) in enumerate(
            [(_ANIMAL_ID_1, "pending"), (_ANIMAL_ID_2, "approved")]
        ):
            await session.execute(
                text("""
                    INSERT INTO adoption_requests
                        (id, animal_id, adopter_id, status, submitted_at)
                    VALUES (:id, :animal_id, :adopter_id, :status, :submitted)
                    ON CONFLICT (id) DO UPDATE SET status = :status
                """),
                {
                    "id": str(uuid.UUID(f"00000000-0000-0000-0000-00000000033{i}")),
                    "animal_id": str(animal_id),
                    "adopter_id": str(_ADOPTER_PROFILE_ID),
                    "status": status,
                    "submitted": now - timedelta(days=i),
                },
            )

        # Create donor profile linked by email
        await session.execute(
            text("""
                INSERT INTO donors (id, full_name, email, currency_preference)
                VALUES (:id, 'Jan van Dijk', :email, 'EUR')
                ON CONFLICT (id) DO UPDATE SET email = :email
            """),
            {"id": str(_DONOR_PROFILE_ID), "email": _DONOR_EMAIL},
        )

        # Create completed donations
        for i in range(3):
            await session.execute(
                text("""
                    INSERT INTO donations
                        (id, donor_id, amount_cents, currency, status, payment_method)
                    VALUES (:id, :donor_id, :amount, 'EUR', 'completed', 'stripe')
                    ON CONFLICT (id) DO UPDATE SET amount_cents = :amount
                """),
                {
                    "id": str(uuid.UUID(f"00000000-0000-0000-0000-00000000034{i}")),
                    "donor_id": str(_DONOR_PROFILE_ID),
                    "amount": (i + 1) * 2500,
                },
            )

        await session.commit()

    yield settings

    # Cleanup — order matters due to FK constraints
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM adoption_requests WHERE adopter_id = :id"),
            {"id": str(_ADOPTER_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM donations WHERE donor_id = :id"),
            {"id": str(_DONOR_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM sponsorships WHERE donor_id = :id"),
            {"id": str(_DONOR_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM adopters WHERE id = :id"),
            {"id": str(_ADOPTER_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM donors WHERE id = :id"),
            {"id": str(_DONOR_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM animals WHERE id IN (:a1, :a2)"),
            {"a1": str(_ANIMAL_ID_1), "a2": str(_ANIMAL_ID_2)},
        )
        for uid in [_ADOPTER_USER_ID, _DONOR_USER_ID, _EMPTY_USER_ID]:
            await session.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": str(uid)},
            )
        await session.commit()


class TestPortalDashboard:
    """Tests for GET /portal/dashboard."""

    async def test_returns_200_with_applications_for_adopter(self, dashboard_setup):
        """Adopter should see their adoption applications."""
        async with _make_client(dashboard_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Maria Garcia"
        assert data["role"] == "adopter"
        assert len(data["applications"]) == 2
        statuses = {app["status"] for app in data["applications"]}
        assert "pending" in statuses
        assert "approved" in statuses

    async def test_returns_200_with_donations_for_donor(self, dashboard_setup):
        """Donor should see aggregated donation stats."""
        async with _make_client(dashboard_setup, _DONOR_USER_ID) as client:
            response = await client.get("/portal/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Jan van Dijk"
        assert data["role"] == "donor"
        ds = data["donation_summary"]
        assert ds["total_count"] == 3
        # 2500 + 5000 + 7500 = 15000 cents
        assert ds["total_amount_cents"] == 15000
        assert ds["currency"] == "EUR"

    async def test_returns_200_with_empty_state(self, dashboard_setup):
        """User with no data should get empty sections."""
        async with _make_client(dashboard_setup, _EMPTY_USER_ID) as client:
            response = await client.get("/portal/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Empty User"
        assert data["applications"] == []
        assert data["sponsored_animals"] == []
        assert data["donation_summary"]["total_count"] == 0

    async def test_returns_401_without_auth(self, dashboard_setup):
        """Unauthenticated request should get 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/portal/dashboard")

        assert response.status_code == 401

    async def test_response_includes_counts(self, dashboard_setup):
        """Response should include total_applications and total_sponsored_animals counts."""
        async with _make_client(dashboard_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["total_applications"] == 2
        assert data["total_sponsored_animals"] == 0
