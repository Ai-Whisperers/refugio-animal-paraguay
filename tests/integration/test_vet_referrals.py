"""Integration tests for vet referral CRUD endpoints."""

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

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]

_TEST_VET_ID = uuid.UUID("00000000-0000-0000-0000-000000000088")
_TEST_VET_EMAIL = "test-referral-vet@refugio.example.com"


@pytest_asyncio.fixture
async def vet_medical_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with vet role for medical staff endpoints."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'vet', true)
                ON CONFLICT (id) DO UPDATE SET role = 'vet', is_active = true
            """),
            {
                "id": str(_TEST_VET_ID),
                "email": _TEST_VET_EMAIL,
                "pwd": hash_password("VetPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_TEST_VET_ID)},
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


@pytest_asyncio.fixture
async def sample_animal_id(client: AsyncClient) -> uuid.UUID:
    """Create a test animal and return its ID."""
    resp = await client.post(
        "/animals",
        json={
            "name": "Referral Test Dog",
            "species": "dog",
            "breed": "mixed",
            "status": "intake",
        },
    )
    assert resp.status_code == 201
    return uuid.UUID(resp.json()["id"])


class TestCreateReferral:
    """Tests for POST /vet-referrals."""

    async def test_create_referral_success(
        self, client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """Staff can create a referral."""
        resp = await client.post(
            "/vet-referrals",
            json={
                "animal_id": str(sample_animal_id),
                "external_vet_name": "Dr. Rodriguez",
                "external_vet_clinic": "Clinica Asuncion",
                "reason": "Orthopedic specialist consultation",
                "specialty": "Orthopedics",
                "urgency": "high",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["external_vet_name"] == "Dr. Rodriguez"
        assert body["urgency"] == "high"
        assert body["status"] == "pending"
        assert body["animal_id"] == str(sample_animal_id)

    async def test_create_referral_as_vet(
        self, vet_medical_client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """Vet (medical staff) can create a referral."""
        resp = await vet_medical_client.post(
            "/vet-referrals",
            json={
                "animal_id": str(sample_animal_id),
                "external_vet_name": "Dr. Specialist",
                "reason": "Cardiac evaluation",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["referred_by_id"] == str(_TEST_VET_ID)

    async def test_create_referral_nonexistent_animal(self, client: AsyncClient) -> None:
        """Creating a referral for a non-existent animal returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            "/vet-referrals",
            json={
                "animal_id": fake_id,
                "external_vet_name": "Dr. Test",
                "reason": "Checkup",
            },
        )
        assert resp.status_code == 404


class TestListReferrals:
    """Tests for GET /vet-referrals."""

    async def test_list_referrals_empty(self, client: AsyncClient) -> None:
        """List returns empty when no referrals for filter."""
        fake_animal = str(uuid.uuid4())
        resp = await client.get(f"/vet-referrals?animal_id={fake_animal}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_referrals_with_data(
        self, client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """List returns created referrals."""
        # Create two referrals
        for name in ["Dr. A", "Dr. B"]:
            await client.post(
                "/vet-referrals",
                json={
                    "animal_id": str(sample_animal_id),
                    "external_vet_name": name,
                    "reason": "Evaluation",
                },
            )

        resp = await client.get(f"/vet-referrals?animal_id={sample_animal_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2

    async def test_list_filter_by_status(
        self, client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """Filtering by status works."""
        resp = await client.get("/vet-referrals?status=completed")
        assert resp.status_code == 200


class TestGetReferral:
    """Tests for GET /vet-referrals/{id}."""

    async def test_get_referral_success(
        self, client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """Retrieve a single referral by ID."""
        create_resp = await client.post(
            "/vet-referrals",
            json={
                "animal_id": str(sample_animal_id),
                "external_vet_name": "Dr. Garcia",
                "reason": "Eye examination",
                "specialty": "Ophthalmology",
            },
        )
        referral_id = create_resp.json()["id"]

        resp = await client.get(f"/vet-referrals/{referral_id}")
        assert resp.status_code == 200
        assert resp.json()["specialty"] == "Ophthalmology"

    async def test_get_referral_not_found(self, client: AsyncClient) -> None:
        """Non-existent referral returns 404."""
        resp = await client.get(f"/vet-referrals/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateReferral:
    """Tests for PATCH /vet-referrals/{id}."""

    async def test_update_referral_status(
        self, client: AsyncClient, sample_animal_id: uuid.UUID
    ) -> None:
        """Update referral status and add diagnosis."""
        create_resp = await client.post(
            "/vet-referrals",
            json={
                "animal_id": str(sample_animal_id),
                "external_vet_name": "Dr. Lopez",
                "reason": "Dental procedure",
            },
        )
        referral_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/vet-referrals/{referral_id}",
            json={
                "status": "completed",
                "diagnosis": "Dental calculus removed",
                "actual_cost": 75000.00,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["diagnosis"] == "Dental calculus removed"
        assert float(body["actual_cost"]) == 75000.00


class TestCancelReferral:
    """Tests for DELETE /vet-referrals/{id}."""

    async def test_cancel_referral(self, client: AsyncClient, sample_animal_id: uuid.UUID) -> None:
        """Cancelling sets status to cancelled."""
        create_resp = await client.post(
            "/vet-referrals",
            json={
                "animal_id": str(sample_animal_id),
                "external_vet_name": "Dr. Cancel",
                "reason": "No longer needed",
            },
        )
        referral_id = create_resp.json()["id"]

        resp = await client.delete(f"/vet-referrals/{referral_id}")
        assert resp.status_code == 204

        # Verify it's cancelled
        get_resp = await client.get(f"/vet-referrals/{referral_id}")
        assert get_resp.json()["status"] == "cancelled"

    async def test_cancel_nonexistent_referral(self, client: AsyncClient) -> None:
        """Cancelling a non-existent referral returns 404."""
        resp = await client.delete(f"/vet-referrals/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestReferralAuth:
    """Tests for auth/permission on referral endpoints."""

    async def test_unauthenticated_access_denied(self) -> None:
        """Unauthenticated users cannot access referrals."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            resp = await ac.get("/vet-referrals")
            # HTTPBearer returns 401 when no credentials provided
            assert resp.status_code in (401, 403)
