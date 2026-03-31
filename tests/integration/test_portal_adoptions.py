"""Integration tests for GET /portal/adoptions endpoint."""

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

# Test user IDs — use distinct UUIDs to avoid collisions with other test modules
_ADOPTER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000401")
_EMPTY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000402")
_ADOPTER_EMAIL = "adoptions-test-adopter@refugio-shelter.org"
_EMPTY_EMAIL = "adoptions-test-empty@refugio-shelter.org"

# Test data IDs
_ADOPTER_PROFILE_ID = uuid.UUID("00000000-0000-0000-0000-000000000411")
_ANIMAL_ID_1 = uuid.UUID("00000000-0000-0000-0000-000000000421")
_ANIMAL_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000422")
_REQUEST_ID_1 = uuid.UUID("00000000-0000-0000-0000-000000000431")
_REQUEST_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000432")


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
async def adoptions_setup() -> AsyncGenerator[Settings, None]:
    """Set up test users, adopter profile, animals, and adoption requests."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create test users
        for uid, email, role, name in [
            (_ADOPTER_USER_ID, _ADOPTER_EMAIL, "adopter", "Sofia Gimenez"),
            (_EMPTY_USER_ID, _EMPTY_EMAIL, "adopter", "Empty Adopter"),
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
        for aid, aname, aspecies in [
            (_ANIMAL_ID_1, "Bolt", "dog"),
            (_ANIMAL_ID_2, "Nala", "cat"),
        ]:
            await session.execute(
                text("""
                    INSERT INTO animals (id, name, species, breed, age_months, sex, status)
                    VALUES (:id, :name, :species, :breed, :age, :sex, :status)
                    ON CONFLICT (id) DO UPDATE SET name = :name
                """),
                {
                    "id": str(aid),
                    "name": aname,
                    "species": aspecies,
                    "breed": "Mixed",
                    "age": 18,
                    "sex": "male",
                    "status": "available",
                },
            )

        # Create adopter profile matched by email
        await session.execute(
            text("""
                INSERT INTO adopters (id, full_name, email, created_at)
                VALUES (:id, :name, :email, :created_at)
                ON CONFLICT (id) DO UPDATE SET full_name = :name
            """),
            {
                "id": str(_ADOPTER_PROFILE_ID),
                "name": "Sofia Gimenez",
                "email": _ADOPTER_EMAIL,
                "created_at": datetime.now(UTC),
            },
        )

        # Create two adoption requests — one pending, one approved with notes
        now = datetime.now(UTC)
        await session.execute(
            text("""
                INSERT INTO adoption_requests
                    (id, animal_id, adopter_id, status, submitted_at, decided_at, notes)
                VALUES
                    (:id1, :a1, :adp, 'pending', :sub1, NULL, NULL),
                    (:id2, :a2, :adp, 'approved', :sub2, :dec2, :notes2)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id1": str(_REQUEST_ID_1),
                "a1": str(_ANIMAL_ID_1),
                "adp": str(_ADOPTER_PROFILE_ID),
                "sub1": now - timedelta(days=5),
                "id2": str(_REQUEST_ID_2),
                "a2": str(_ANIMAL_ID_2),
                "sub2": now - timedelta(days=10),
                "dec2": now - timedelta(days=2),
                "notes2": "Candidata ideal con hogar amplio",
            },
        )

        await session.commit()

    yield settings

    # Cleanup — order matters due to FK constraints
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM adoption_requests WHERE id IN (:r1, :r2)"),
            {"r1": str(_REQUEST_ID_1), "r2": str(_REQUEST_ID_2)},
        )
        await session.execute(
            text("DELETE FROM adopters WHERE id = :id"),
            {"id": str(_ADOPTER_PROFILE_ID)},
        )
        await session.execute(
            text("DELETE FROM animals WHERE id IN (:a1, :a2)"),
            {"a1": str(_ANIMAL_ID_1), "a2": str(_ANIMAL_ID_2)},
        )
        for uid in [_ADOPTER_USER_ID, _EMPTY_USER_ID]:
            await session.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": str(uid)},
            )
        await session.commit()


class TestPortalAdoptions:
    """Tests for GET /portal/adoptions."""

    async def test_returns_200_with_applications(self, adoptions_setup):
        """Authenticated adopter should receive their adoption applications."""
        async with _make_client(adoptions_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/adoptions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["applications"]) == 2

    async def test_applications_contain_expected_fields(self, adoptions_setup):
        """Each application should include id, animal info, status, dates, and notes."""
        async with _make_client(adoptions_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/adoptions")

        assert response.status_code == 200
        apps = response.json()["applications"]
        required_fields = {
            "id",
            "animal_id",
            "animal_name",
            "animal_species",
            "submitted_at",
            "decided_at",
            "status",
            "notes",
        }
        for application in apps:
            assert required_fields.issubset(application.keys())

    async def test_approved_application_includes_notes(self, adoptions_setup):
        """Approved application should include decision notes and decided_at."""
        async with _make_client(adoptions_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/adoptions")

        apps = response.json()["applications"]
        approved = next(a for a in apps if a["status"] == "approved")
        assert approved["notes"] == "Candidata ideal con hogar amplio"
        assert approved["decided_at"] is not None
        assert approved["animal_name"] == "Nala"

    async def test_pending_application_has_no_notes_or_decided_at(self, adoptions_setup):
        """Pending application should have null notes and decided_at."""
        async with _make_client(adoptions_setup, _ADOPTER_USER_ID) as client:
            response = await client.get("/portal/adoptions")

        apps = response.json()["applications"]
        pending = next(a for a in apps if a["status"] == "pending")
        assert pending["notes"] is None
        assert pending["decided_at"] is None
        assert pending["animal_name"] == "Bolt"

    async def test_returns_empty_when_no_applications(self, adoptions_setup):
        """Adopter with no applications should receive empty list."""
        async with _make_client(adoptions_setup, _EMPTY_USER_ID) as client:
            response = await client.get("/portal/adoptions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["applications"] == []

    async def test_returns_401_without_auth(self, adoptions_setup):
        """Unauthenticated request should return 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/portal/adoptions")

        assert response.status_code == 401
