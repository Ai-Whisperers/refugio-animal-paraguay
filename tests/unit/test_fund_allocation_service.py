"""Unit tests for fund allocation service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.db.models.fund_allocation import FundAllocation, FundCategory
from src.services import fund_allocation_service


class TestCreateAllocation:
    """Tests for create_allocation."""

    @pytest.mark.asyncio
    async def test_creates_allocation_with_all_fields(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        result = await fund_allocation_service.create_allocation(
            db=db,
            category=FundCategory.MEDICAL,
            amount_cents=150000,
            currency="PYG",
            description="Veterinary supplies",
            transaction_date=now,
            recorded_by_user_id=user_id,
            receipt_reference="INV-2026-001",
            notes="Monthly supply order",
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

        added = db.add.call_args[0][0]
        assert isinstance(added, FundAllocation)
        assert added.category == FundCategory.MEDICAL
        assert added.amount_cents == 150000
        assert added.currency == "PYG"
        assert added.description == "Veterinary supplies"
        assert added.recorded_by_user_id == user_id
        assert added.receipt_reference == "INV-2026-001"
        assert added.notes == "Monthly supply order"

    @pytest.mark.asyncio
    async def test_creates_allocation_with_minimal_fields(self) -> None:
        db = AsyncMock()
        now = datetime.now(tz=timezone.utc)

        await fund_allocation_service.create_allocation(
            db=db,
            category=FundCategory.FOOD,
            amount_cents=50000,
            currency="PYG",
            description="Dog food purchase",
            transaction_date=now,
        )

        added = db.add.call_args[0][0]
        assert added.category == FundCategory.FOOD
        assert added.recorded_by_user_id is None
        assert added.receipt_reference is None
        assert added.notes is None


class TestGetAllocation:
    """Tests for get_allocation."""

    @pytest.mark.asyncio
    async def test_returns_allocation_when_found(self) -> None:
        allocation = MagicMock(spec=FundAllocation)
        allocation.id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = allocation
        db.execute.return_value = mock_result

        result = await fund_allocation_service.get_allocation(db, allocation.id)
        assert result == allocation

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await fund_allocation_service.get_allocation(db, uuid4())
        assert result is None


class TestUpdateAllocation:
    """Tests for update_allocation."""

    @pytest.mark.asyncio
    async def test_updates_specified_fields(self) -> None:
        allocation = MagicMock(spec=FundAllocation)
        db = AsyncMock()

        updates = {"category": FundCategory.OPERATIONS, "amount_cents": 200000}
        result = await fund_allocation_service.update_allocation(
            db, allocation, updates
        )

        assert allocation.category == FundCategory.OPERATIONS
        assert allocation.amount_cents == 200000
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_none_values(self) -> None:
        allocation = MagicMock(spec=FundAllocation)
        allocation.category = FundCategory.MEDICAL
        db = AsyncMock()

        updates = {"category": None, "notes": "Updated note"}
        await fund_allocation_service.update_allocation(db, allocation, updates)

        # category should not change since value is None
        assert allocation.notes == "Updated note"


class TestDeleteAllocation:
    """Tests for delete_allocation."""

    @pytest.mark.asyncio
    async def test_deletes_allocation(self) -> None:
        allocation = MagicMock(spec=FundAllocation)
        db = AsyncMock()

        await fund_allocation_service.delete_allocation(db, allocation)

        db.delete.assert_awaited_once_with(allocation)
        db.flush.assert_awaited_once()


class TestListAllocations:
    """Tests for list_allocations."""

    @pytest.mark.asyncio
    async def test_returns_items_and_count(self) -> None:
        allocations = [MagicMock(spec=FundAllocation) for _ in range(3)]

        db = AsyncMock()
        # Mock for items query
        items_result = MagicMock()
        items_scalars = MagicMock()
        items_scalars.all.return_value = allocations
        items_result.scalars.return_value = items_scalars

        # Mock for count query
        count_result = MagicMock()
        count_result.scalar.return_value = 3

        db.execute.side_effect = [items_result, count_result]

        items, total = await fund_allocation_service.list_allocations(db)

        assert len(items) == 3
        assert total == 3


class TestGetCategoryBreakdown:
    """Tests for get_category_breakdown."""

    @pytest.mark.asyncio
    async def test_returns_breakdown_with_percentages(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()

        # Simulate two categories
        row1 = MagicMock()
        row1.category = "medical"
        row1.total_cents = 750000
        row1.transaction_count = 5

        row2 = MagicMock()
        row2.category = "food"
        row2.total_cents = 250000
        row2.transaction_count = 3

        mock_result.all.return_value = [row1, row2]
        db.execute.return_value = mock_result

        now = datetime.now(tz=timezone.utc)
        result = await fund_allocation_service.get_category_breakdown(
            db,
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=now,
            currency="PYG",
        )

        assert len(result) == 2
        assert result[0]["category"] == "medical"
        assert result[0]["total_cents"] == 750000
        assert result[0]["percentage"] == 75.0
        assert result[1]["category"] == "food"
        assert result[1]["total_cents"] == 250000
        assert result[1]["percentage"] == 25.0

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_data(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await fund_allocation_service.get_category_breakdown(
            db,
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 3, 31, tzinfo=timezone.utc),
        )

        assert result == []


class TestGetPeriodTrends:
    """Tests for get_period_trends."""

    @pytest.mark.asyncio
    async def test_returns_trends_with_change(self) -> None:
        db = AsyncMock()

        current_row = MagicMock()
        current_row.category = "medical"
        current_row.total_cents = 300000

        previous_row = MagicMock()
        previous_row.category = "medical"
        previous_row.total_cents = 200000

        current_result = MagicMock()
        current_result.all.return_value = [current_row]
        previous_result = MagicMock()
        previous_result.all.return_value = [previous_row]

        db.execute.side_effect = [current_result, previous_result]

        result = await fund_allocation_service.get_period_trends(
            db,
            current_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            current_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
            previous_start=datetime(2025, 10, 1, tzinfo=timezone.utc),
            previous_end=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )

        assert len(result) == 1
        assert result[0]["category"] == "medical"
        assert result[0]["current_period_cents"] == 300000
        assert result[0]["previous_period_cents"] == 200000
        assert result[0]["change_cents"] == 100000
        assert result[0]["change_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_returns_none_percentage_when_previous_zero(self) -> None:
        db = AsyncMock()

        current_row = MagicMock()
        current_row.category = "food"
        current_row.total_cents = 100000

        current_result = MagicMock()
        current_result.all.return_value = [current_row]
        previous_result = MagicMock()
        previous_result.all.return_value = []

        db.execute.side_effect = [current_result, previous_result]

        result = await fund_allocation_service.get_period_trends(
            db,
            current_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            current_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
            previous_start=datetime(2025, 10, 1, tzinfo=timezone.utc),
            previous_end=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )

        assert len(result) == 1
        assert result[0]["change_percentage"] is None

    @pytest.mark.asyncio
    async def test_merges_categories_from_both_periods(self) -> None:
        db = AsyncMock()

        # Current period has medical only
        current_row = MagicMock()
        current_row.category = "medical"
        current_row.total_cents = 100000

        # Previous period has food only
        previous_row = MagicMock()
        previous_row.category = "food"
        previous_row.total_cents = 50000

        current_result = MagicMock()
        current_result.all.return_value = [current_row]
        previous_result = MagicMock()
        previous_result.all.return_value = [previous_row]

        db.execute.side_effect = [current_result, previous_result]

        result = await fund_allocation_service.get_period_trends(
            db,
            current_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            current_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
            previous_start=datetime(2025, 10, 1, tzinfo=timezone.utc),
            previous_end=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )

        assert len(result) == 2
        categories = [t["category"] for t in result]
        assert "food" in categories
        assert "medical" in categories

        food_trend = next(t for t in result if t["category"] == "food")
        assert food_trend["current_period_cents"] == 0
        assert food_trend["previous_period_cents"] == 50000
