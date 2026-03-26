"""Integration tests for fund allocation endpoints.

Tests run against the live PostgreSQL test database with authenticated
staff and admin clients.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

# Deterministic admin user for delete tests
_TEST_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
_TEST_ADMIN_EMAIL = "test-admin-fund@refugio.test"


@pytest_asyncio.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with admin role for delete endpoint."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'admin', true)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    role = EXCLUDED.role,
                    is_active = EXCLUDED.is_active
            """),
            {
                "id": str(_TEST_ADMIN_ID),
                "email": _TEST_ADMIN_EMAIL,
                "pwd": hash_password("AdminPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_TEST_ADMIN_ID)},
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


def _allocation_payload(**overrides: object) -> dict:
    """Build a valid fund allocation payload with sensible defaults."""
    now = datetime.now(tz=timezone.utc).isoformat()
    defaults: dict = {
        "category": "medical",
        "amount_cents": 150000,
        "currency": "PYG",
        "description": "Veterinary supplies for March",
        "transaction_date": now,
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.integration
class TestCreateAllocation:
    """POST /fund-allocations."""

    @pytest.mark.asyncio
    async def test_creates_allocation_returns_201(self, client: AsyncClient) -> None:
        payload = _allocation_payload()
        resp = await client.post("/fund-allocations", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "medical"
        assert data["amount_cents"] == 150000
        assert data["currency"] == "PYG"
        assert data["description"] == "Veterinary supplies for March"
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_creates_allocation_with_optional_fields(
        self, client: AsyncClient
    ) -> None:
        payload = _allocation_payload(
            receipt_reference="INV-2026-042",
            notes="Bulk order discount applied",
        )
        resp = await client.post("/fund-allocations", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert data["receipt_reference"] == "INV-2026-042"
        assert data["notes"] == "Bulk order discount applied"

    @pytest.mark.asyncio
    async def test_rejects_invalid_category(self, client: AsyncClient) -> None:
        payload = _allocation_payload(category="invalid_category")
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_zero_amount(self, client: AsyncClient) -> None:
        payload = _allocation_payload(amount_cents=0)
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        payload = _allocation_payload()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauth_client:
            resp = await unauth_client.post("/fund-allocations", json=payload)
        assert resp.status_code == 401


@pytest.mark.integration
class TestListAllocations:
    """GET /fund-allocations."""

    @pytest.mark.asyncio
    async def test_lists_allocations(self, client: AsyncClient) -> None:
        # Create one to ensure list isn't empty
        await client.post("/fund-allocations", json=_allocation_payload())

        resp = await client.get("/fund-allocations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_filters_by_category(self, client: AsyncClient) -> None:
        await client.post(
            "/fund-allocations", json=_allocation_payload(category="food")
        )

        resp = await client.get("/fund-allocations", params={"category": "food"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["category"] == "food"


@pytest.mark.integration
class TestGetAllocation:
    """GET /fund-allocations/{id}."""

    @pytest.mark.asyncio
    async def test_returns_allocation_by_id(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/fund-allocations", json=_allocation_payload()
        )
        allocation_id = create_resp.json()["id"]

        resp = await client.get(f"/fund-allocations/{allocation_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == allocation_id

    @pytest.mark.asyncio
    async def test_returns_404_for_missing(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/fund-allocations/{fake_id}")
        assert resp.status_code == 404


@pytest.mark.integration
class TestUpdateAllocation:
    """PATCH /fund-allocations/{id}."""

    @pytest.mark.asyncio
    async def test_updates_allocation_fields(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/fund-allocations", json=_allocation_payload()
        )
        allocation_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/fund-allocations/{allocation_id}",
            json={"category": "operations", "notes": "Reclassified expense"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "operations"
        assert data["notes"] == "Reclassified expense"


@pytest.mark.integration
class TestDeleteAllocation:
    """DELETE /fund-allocations/{id}."""

    @pytest.mark.asyncio
    async def test_admin_can_delete(
        self, client: AsyncClient, admin_client: AsyncClient
    ) -> None:
        # Create with staff client
        create_resp = await client.post(
            "/fund-allocations", json=_allocation_payload()
        )
        allocation_id = create_resp.json()["id"]

        # Delete with admin client
        resp = await admin_client.delete(f"/fund-allocations/{allocation_id}")
        assert resp.status_code == 204

        # Verify deleted
        get_resp = await client.get(f"/fund-allocations/{allocation_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_staff_cannot_delete(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/fund-allocations", json=_allocation_payload()
        )
        allocation_id = create_resp.json()["id"]

        resp = await client.delete(f"/fund-allocations/{allocation_id}")
        assert resp.status_code == 403


@pytest.mark.integration
class TestAllocationSummary:
    """GET /fund-allocations/summary."""

    @pytest.mark.asyncio
    async def test_returns_category_breakdown(self, client: AsyncClient) -> None:
        now = datetime.now(tz=timezone.utc)
        start = (now - timedelta(days=30)).isoformat()
        end = now.isoformat()

        # Create allocations in different categories
        await client.post(
            "/fund-allocations",
            json=_allocation_payload(category="medical", amount_cents=300000),
        )
        await client.post(
            "/fund-allocations",
            json=_allocation_payload(category="food", amount_cents=100000),
        )

        resp = await client.get(
            "/fund-allocations/summary",
            params={"start_date": start, "end_date": end, "currency": "PYG"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_allocated_cents"] > 0
        assert isinstance(data["breakdown"], list)
        assert len(data["breakdown"]) >= 1

        # Check percentages sum to ~100
        total_pct = sum(b["percentage"] for b in data["breakdown"])
        assert 99.9 <= total_pct <= 100.1


@pytest.mark.integration
class TestPublicBreakdown:
    """GET /fund-allocations/public."""

    @pytest.mark.asyncio
    async def test_public_endpoint_no_auth(self, client: AsyncClient) -> None:
        now = datetime.now(tz=timezone.utc)
        start = (now - timedelta(days=30)).isoformat()
        end = now.isoformat()

        # Public endpoint should work without auth
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as public_client:
            resp = await public_client.get(
                "/fund-allocations/public",
                params={"start_date": start, "end_date": end, "currency": "PYG"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "breakdown" in data
        assert "total_allocated_cents" in data
