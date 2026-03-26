"""Unit tests for fund allocation service logic.

Tests allocation creation and category breakdown aggregation with mocked DB.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.fund_allocation import FundCategory
from src.services.fund_allocation_service import (
    create_allocation,
    get_allocation_breakdown,
)


class TestCreateAllocation:
    """Tests for create_allocation function."""

    @pytest.mark.asyncio
    async def test_creates_allocation_with_all_fields(self) -> None:
        db = AsyncMock()

        async def mock_refresh(obj: MagicMock) -> None:
            obj.id = uuid4()

        db.refresh = mock_refresh

        user_id = uuid4()
        txn_date = datetime(2026, 3, 1, tzinfo=UTC)

        result = await create_allocation(
            db=db,
            category=FundCategory.MEDICAL.value,
            amount_cents=50000,
            currency="PYG",
            description="Veterinary supplies March 2026",
            transaction_date=txn_date,
            recorded_by_user_id=user_id,
            receipt_reference="REC-001",
            notes="Monthly vet supply order",
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_creates_allocation_without_optional_fields(self) -> None:
        db = AsyncMock()

        async def mock_refresh(obj: MagicMock) -> None:
            obj.id = uuid4()

        db.refresh = mock_refresh

        txn_date = datetime(2026, 3, 15, tzinfo=UTC)

        result = await create_allocation(
            db=db,
            category=FundCategory.FOOD.value,
            amount_cents=25000,
            currency="PYG",
            description="Dog food purchase",
            transaction_date=txn_date,
        )

        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert added_obj.recorded_by_user_id is None
        assert added_obj.receipt_reference is None
        assert added_obj.notes is None
        assert result is not None

    @pytest.mark.asyncio
    async def test_amount_stored_as_cents(self) -> None:
        db = AsyncMock()

        async def mock_refresh(obj: MagicMock) -> None:
            obj.id = uuid4()

        db.refresh = mock_refresh

        txn_date = datetime(2026, 2, 1, tzinfo=UTC)

        await create_allocation(
            db=db,
            category=FundCategory.OPERATIONS.value,
            amount_cents=100000,
            currency="PYG",
            description="Utility bills",
            transaction_date=txn_date,
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.amount_cents == 100000
        assert added_obj.currency == "PYG"


class TestGetAllocationBreakdown:
    """Tests for get_allocation_breakdown function."""

    @pytest.mark.asyncio
    async def test_returns_empty_breakdown_when_no_data(self) -> None:
        db = AsyncMock()

        # Mock expense query — no rows
        expense_result = MagicMock()
        expense_result.__iter__ = MagicMock(return_value=iter([]))

        # Mock donation query — 0 total
        donation_result = MagicMock()
        donation_result.scalar_one.return_value = 0

        db.execute = AsyncMock(side_effect=[expense_result, donation_result])

        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 3, 31, tzinfo=UTC)

        result = await get_allocation_breakdown(db, start, end, currency="PYG")

        assert result["total_expenses_cents"] == 0
        assert result["total_donations_cents"] == 0
        assert result["breakdown"] == []
        assert result["currency"] == "PYG"

    @pytest.mark.asyncio
    async def test_calculates_category_percentages(self) -> None:
        db = AsyncMock()

        # Mock expense rows: medical 60k, food 40k
        row_medical = MagicMock()
        row_medical.category = "medical"
        row_medical.total_cents = 60000
        row_medical.transaction_count = 3

        row_food = MagicMock()
        row_food.category = "food"
        row_food.total_cents = 40000
        row_food.transaction_count = 2

        expense_result = MagicMock()
        expense_result.__iter__ = MagicMock(return_value=iter([row_medical, row_food]))

        donation_result = MagicMock()
        donation_result.scalar_one.return_value = 200000

        db.execute = AsyncMock(side_effect=[expense_result, donation_result])

        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 3, 31, tzinfo=UTC)

        result = await get_allocation_breakdown(db, start, end)

        assert result["total_expenses_cents"] == 100000
        assert result["total_donations_cents"] == 200000
        assert len(result["breakdown"]) == 2

        medical = result["breakdown"][0]
        assert medical["category"] == "medical"
        assert medical["total_cents"] == 60000
        assert medical["percentage"] == 60.0
        assert medical["transaction_count"] == 3

        food = result["breakdown"][1]
        assert food["category"] == "food"
        assert food["percentage"] == 40.0

    @pytest.mark.asyncio
    async def test_single_category_is_100_percent(self) -> None:
        db = AsyncMock()

        row = MagicMock()
        row.category = "operations"
        row.total_cents = 75000
        row.transaction_count = 5

        expense_result = MagicMock()
        expense_result.__iter__ = MagicMock(return_value=iter([row]))

        donation_result = MagicMock()
        donation_result.scalar_one.return_value = 100000

        db.execute = AsyncMock(side_effect=[expense_result, donation_result])

        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 3, 31, tzinfo=UTC)

        result = await get_allocation_breakdown(db, start, end)

        assert len(result["breakdown"]) == 1
        assert result["breakdown"][0]["percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_uses_date_range_from_arguments(self) -> None:
        db = AsyncMock()

        expense_result = MagicMock()
        expense_result.__iter__ = MagicMock(return_value=iter([]))

        donation_result = MagicMock()
        donation_result.scalar_one.return_value = 0

        db.execute = AsyncMock(side_effect=[expense_result, donation_result])

        start = datetime(2026, 2, 1, tzinfo=UTC)
        end = datetime(2026, 2, 28, tzinfo=UTC)

        result = await get_allocation_breakdown(db, start, end, currency="EUR")

        assert result["start_date"] == start
        assert result["end_date"] == end
        assert result["currency"] == "EUR"


class TestFundCategoryEnum:
    """Tests for FundCategory enum values."""

    def test_all_categories_present(self) -> None:
        expected = {"medical", "food", "operations", "admin", "fundraising", "other"}
        actual = {c.value for c in FundCategory}
        assert actual == expected

    def test_category_is_str_enum(self) -> None:
        assert isinstance(FundCategory.MEDICAL, str)
        assert FundCategory.MEDICAL == "medical"
