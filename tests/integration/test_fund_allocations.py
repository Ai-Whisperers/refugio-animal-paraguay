"""Integration tests for fund allocation endpoints.

Exercises POST/GET endpoints against a live PostgreSQL database
with an authenticated staff client.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture
async def _clean_allocations() -> None:
    """Remove all fund_allocations rows before each test."""
    settings = Settings()
    engine = init_engine(settings)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await session.execute(text("DELETE FROM fund_allocations"))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
class TestCreateFundAllocation:
    """POST /fund-allocations — record a new expense."""

    async def test_creates_allocation_successfully(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        payload = {
            "category": "medical",
            "amount_cents": 50000,
            "currency": "PYG",
            "description": "Veterinary supplies",
            "transaction_date": "2026-03-01T00:00:00Z",
        }
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 201

        data = resp.json()
        assert data["category"] == "medical"
        assert data["amount_cents"] == 50000
        assert data["currency"] == "PYG"
        assert data["description"] == "Veterinary supplies"
        assert data["id"] is not None
        assert data["recorded_by_user_id"] is not None

    async def test_creates_allocation_with_optional_fields(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        payload = {
            "category": "food",
            "amount_cents": 25000,
            "currency": "PYG",
            "description": "Dog food bulk purchase",
            "transaction_date": "2026-03-15T10:00:00Z",
            "receipt_reference": "REC-2026-042",
            "notes": "Monthly bulk order from supplier",
        }
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 201

        data = resp.json()
        assert data["receipt_reference"] == "REC-2026-042"
        assert data["notes"] == "Monthly bulk order from supplier"

    async def test_rejects_invalid_category(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        payload = {
            "category": "entertainment",
            "amount_cents": 10000,
            "currency": "PYG",
            "description": "Invalid category test",
            "transaction_date": "2026-03-01T00:00:00Z",
        }
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 422

    async def test_rejects_zero_amount(self, client: AsyncClient, _clean_allocations: None) -> None:
        payload = {
            "category": "operations",
            "amount_cents": 0,
            "currency": "PYG",
            "description": "Zero amount test",
            "transaction_date": "2026-03-01T00:00:00Z",
        }
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 422

    async def test_rejects_negative_amount(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        payload = {
            "category": "admin",
            "amount_cents": -5000,
            "currency": "PYG",
            "description": "Negative amount test",
            "transaction_date": "2026-03-01T00:00:00Z",
        }
        resp = await client.post("/fund-allocations", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
class TestListFundAllocations:
    """GET /fund-allocations — list allocations with filters."""

    async def test_returns_empty_list_when_no_allocations(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        resp = await client.get("/fund-allocations")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_lists_created_allocations(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        # Create two allocations
        for cat in ("medical", "food"):
            await client.post(
                "/fund-allocations",
                json={
                    "category": cat,
                    "amount_cents": 10000,
                    "currency": "PYG",
                    "description": f"{cat} expense",
                    "transaction_date": "2026-03-01T00:00:00Z",
                },
            )

        resp = await client.get("/fund-allocations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_filters_by_category(self, client: AsyncClient, _clean_allocations: None) -> None:
        for cat in ("medical", "food", "medical"):
            await client.post(
                "/fund-allocations",
                json={
                    "category": cat,
                    "amount_cents": 10000,
                    "currency": "PYG",
                    "description": f"{cat} expense",
                    "transaction_date": "2026-03-01T00:00:00Z",
                },
            )

        resp = await client.get("/fund-allocations", params={"category": "medical"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(item["category"] == "medical" for item in data)

    async def test_pagination(self, client: AsyncClient, _clean_allocations: None) -> None:
        for i in range(5):
            await client.post(
                "/fund-allocations",
                json={
                    "category": "operations",
                    "amount_cents": 10000 * (i + 1),
                    "currency": "PYG",
                    "description": f"Expense {i}",
                    "transaction_date": f"2026-03-{i + 1:02d}T00:00:00Z",
                },
            )

        resp = await client.get("/fund-allocations", params={"limit": 2, "offset": 0})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        resp2 = await client.get("/fund-allocations", params={"limit": 2, "offset": 2})
        assert resp2.status_code == 200
        assert len(resp2.json()) == 2


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetFundAllocation:
    """GET /fund-allocations/{id} — single allocation detail."""

    async def test_returns_allocation_by_id(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        create_resp = await client.post(
            "/fund-allocations",
            json={
                "category": "fundraising",
                "amount_cents": 30000,
                "currency": "EUR",
                "description": "EU fundraising event expenses",
                "transaction_date": "2026-03-10T00:00:00Z",
            },
        )
        allocation_id = create_resp.json()["id"]

        resp = await client.get(f"/fund-allocations/{allocation_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == allocation_id
        assert resp.json()["category"] == "fundraising"

    async def test_returns_404_for_nonexistent_id(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000099"
        resp = await client.get(f"/fund-allocations/{fake_id}")
        assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
class TestAllocationSummary:
    """GET /fund-allocations/summary — category breakdown."""

    async def test_returns_summary_with_breakdown(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        # Create allocations in different categories
        for cat, amount in [("medical", 60000), ("food", 40000)]:
            await client.post(
                "/fund-allocations",
                json={
                    "category": cat,
                    "amount_cents": amount,
                    "currency": "PYG",
                    "description": f"{cat} expense",
                    "transaction_date": "2026-03-15T00:00:00Z",
                },
            )

        resp = await client.get(
            "/fund-allocations/summary",
            params={"currency": "PYG"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_expenses_cents"] == 100000
        assert data["currency"] == "PYG"
        assert len(data["breakdown"]) == 2

        # Categories ordered by amount desc
        assert data["breakdown"][0]["category"] == "medical"
        assert data["breakdown"][0]["percentage"] == 60.0
        assert data["breakdown"][1]["category"] == "food"
        assert data["breakdown"][1]["percentage"] == 40.0

    async def test_returns_empty_summary_when_no_data(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        resp = await client.get("/fund-allocations/summary")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_expenses_cents"] == 0
        assert data["breakdown"] == []

    async def test_summary_respects_date_range(
        self, client: AsyncClient, _clean_allocations: None
    ) -> None:
        # Create one in Jan, one in Mar
        await client.post(
            "/fund-allocations",
            json={
                "category": "medical",
                "amount_cents": 10000,
                "currency": "PYG",
                "description": "Jan expense",
                "transaction_date": "2026-01-15T00:00:00Z",
            },
        )
        await client.post(
            "/fund-allocations",
            json={
                "category": "food",
                "amount_cents": 20000,
                "currency": "PYG",
                "description": "Mar expense",
                "transaction_date": "2026-03-15T00:00:00Z",
            },
        )

        # Query only March
        resp = await client.get(
            "/fund-allocations/summary",
            params={
                "start_date": "2026-03-01T00:00:00Z",
                "end_date": "2026-03-31T23:59:59Z",
                "currency": "PYG",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expenses_cents"] == 20000
        assert len(data["breakdown"]) == 1
        assert data["breakdown"][0]["category"] == "food"
