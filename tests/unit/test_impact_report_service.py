"""Unit tests for impact report service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services import impact_report_service

# --- Helpers ---
START = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 3, 31, tzinfo=UTC)


def _mock_db_rows(*row_dicts: dict) -> AsyncMock:
    """Create a mock db session that returns the given row dicts."""
    db = AsyncMock()
    mock_result = MagicMock()
    rows = []
    for rd in row_dicts:
        row = MagicMock()
        for k, v in rd.items():
            setattr(row, k, v)
        rows.append(row)
    mock_result.all.return_value = rows
    db.execute.return_value = mock_result
    return db


class TestCountAnimalsServed:
    """Tests for count_animals_served."""

    @pytest.mark.asyncio
    async def test_counts_by_species(self) -> None:
        db = _mock_db_rows(
            {"species": "dog", "count": 15},
            {"species": "cat", "count": 8},
        )

        result = await impact_report_service.count_animals_served(db, START, END)

        assert result["total"] == 23
        assert result["by_species"] == {"dog": 15, "cat": 8}

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty(self) -> None:
        db = _mock_db_rows()

        result = await impact_report_service.count_animals_served(db, START, END)

        assert result["total"] == 0
        assert result["by_species"] == {}


class TestCountAdoptions:
    """Tests for count_adoptions."""

    @pytest.mark.asyncio
    async def test_counts_approved_adoptions(self) -> None:
        db = _mock_db_rows(
            {"species": "dog", "count": 10},
            {"species": "cat", "count": 5},
        )

        result = await impact_report_service.count_adoptions(db, START, END)

        assert result["total"] == 15
        assert result["by_species"]["dog"] == 10
        assert result["by_species"]["cat"] == 5


class TestSumDonations:
    """Tests for sum_donations."""

    @pytest.mark.asyncio
    async def test_sums_by_currency_and_method(self) -> None:
        db = AsyncMock()

        # Currency query result
        currency_row1 = MagicMock()
        currency_row1.currency = "EUR"
        currency_row1.total_cents = 5000000
        currency_row1.count = 25

        currency_row2 = MagicMock()
        currency_row2.currency = "PYG"
        currency_row2.total_cents = 15000000
        currency_row2.count = 40

        currency_result = MagicMock()
        currency_result.all.return_value = [currency_row1, currency_row2]

        # Method query result
        method_row1 = MagicMock()
        method_row1.payment_method = "stripe"
        method_row1.count = 25

        method_row2 = MagicMock()
        method_row2.payment_method = "cash"
        method_row2.count = 40

        method_result = MagicMock()
        method_result.all.return_value = [method_row1, method_row2]

        db.execute.side_effect = [currency_result, method_result]

        result = await impact_report_service.sum_donations(db, START, END)

        assert result["total_count"] == 65
        assert result["by_currency"]["EUR"]["total_cents"] == 5000000
        assert result["by_currency"]["PYG"]["count"] == 40
        assert result["by_payment_method"]["stripe"] == 25
        assert result["by_payment_method"]["cash"] == 40


class TestSumInKindDonations:
    """Tests for sum_in_kind_donations."""

    @pytest.mark.asyncio
    async def test_sums_by_type(self) -> None:
        db = _mock_db_rows(
            {"item_type": "food", "count": 12},
            {"item_type": "medicine", "count": 5},
        )

        result = await impact_report_service.sum_in_kind_donations(db, START, END)

        assert result["total"] == 17
        assert result["by_type"]["food"] == 12


class TestGetFundAllocationBreakdown:
    """Tests for get_fund_allocation_breakdown."""

    @pytest.mark.asyncio
    async def test_calculates_percentages(self) -> None:
        db = _mock_db_rows(
            {"category": "medical", "total_cents": 600000, "count": 10},
            {"category": "food", "total_cents": 400000, "count": 8},
        )

        result = await impact_report_service.get_fund_allocation_breakdown(db, START, END)

        assert result["total_cents"] == 1000000
        assert len(result["breakdown"]) == 2
        assert result["breakdown"][0]["category"] == "medical"
        assert result["breakdown"][0]["percentage"] == 60.0
        assert result["breakdown"][1]["percentage"] == 40.0

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty(self) -> None:
        db = _mock_db_rows()

        result = await impact_report_service.get_fund_allocation_breakdown(db, START, END)

        assert result["total_cents"] == 0
        assert result["breakdown"] == []


class TestCalculateAvgTimeToAdoption:
    """Tests for calculate_avg_time_to_adoption."""

    @pytest.mark.asyncio
    async def test_returns_average_days(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 14.567
        db.execute.return_value = mock_result

        result = await impact_report_service.calculate_avg_time_to_adoption(db, START, END)

        assert result == 14.6  # Rounded to 1 decimal

    @pytest.mark.asyncio
    async def test_returns_none_when_no_adoptions(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        db.execute.return_value = mock_result

        result = await impact_report_service.calculate_avg_time_to_adoption(db, START, END)

        assert result is None


class TestGenerateImpactReport:
    """Tests for generate_impact_report (integration of all sub-queries)."""

    @pytest.mark.asyncio
    async def test_generates_full_report(self) -> None:
        db = AsyncMock()
        user_id = uuid4()

        # Set up side_effect to return different results for each query
        # count_animals: 1 query
        animals_result = MagicMock()
        row_dog = MagicMock()
        row_dog.species = "dog"
        row_dog.count = 20
        animals_result.all.return_value = [row_dog]

        # count_adoptions: 1 query
        adoptions_result = MagicMock()
        adopt_row = MagicMock()
        adopt_row.species = "dog"
        adopt_row.count = 10
        adoptions_result.all.return_value = [adopt_row]

        # sum_donations: 2 queries (currency + method)
        don_currency_result = MagicMock()
        don_currency_row = MagicMock()
        don_currency_row.currency = "EUR"
        don_currency_row.total_cents = 5000000
        don_currency_row.count = 25
        don_currency_result.all.return_value = [don_currency_row]

        don_method_result = MagicMock()
        don_method_row = MagicMock()
        don_method_row.payment_method = "stripe"
        don_method_row.count = 25
        don_method_result.all.return_value = [don_method_row]

        # sum_in_kind: 1 query
        inkind_result = MagicMock()
        inkind_row = MagicMock()
        inkind_row.item_type = "food"
        inkind_row.count = 5
        inkind_result.all.return_value = [inkind_row]

        # fund_allocation: 1 query
        fund_result = MagicMock()
        fund_row = MagicMock()
        fund_row.category = "medical"
        fund_row.total_cents = 500000
        fund_row.count = 8
        fund_result.all.return_value = [fund_row]

        # avg_time_to_adoption: 1 query (returns scalar)
        avg_time_result = MagicMock()
        avg_time_result.scalar.return_value = 12.5

        # count_volunteer_hours: 2 queries (category breakdown + unique totals)
        vol_cat_result = MagicMock()
        vol_cat_row = MagicMock()
        vol_cat_row.category = "animal_care"
        vol_cat_row.total_hours = 60.0
        vol_cat_result.all.return_value = [vol_cat_row]

        vol_unique_row = MagicMock()
        vol_unique_row.unique_volunteers = 5
        vol_unique_row.total_hours = 60.0
        vol_unique_result = MagicMock()
        vol_unique_result.one.return_value = vol_unique_row

        # count_active_foster_placements: 2 queries (active + new)
        foster_active_result = MagicMock()
        foster_active_result.scalar.return_value = 7

        foster_new_result = MagicMock()
        foster_new_result.scalar.return_value = 3

        db.execute.side_effect = [
            animals_result,  # count_animals_served
            adoptions_result,  # count_adoptions
            don_currency_result,  # sum_donations (currency)
            don_method_result,  # sum_donations (method)
            inkind_result,  # sum_in_kind_donations
            fund_result,  # get_fund_allocation_breakdown
            avg_time_result,  # calculate_avg_time_to_adoption
            vol_cat_result,  # count_volunteer_hours (categories)
            vol_unique_result,  # count_volunteer_hours (totals)
            foster_active_result,  # count_active_foster_placements (active)
            foster_new_result,  # count_active_foster_placements (new)
        ]

        result = await impact_report_service.generate_impact_report(
            db, START, END, generated_by_user_id=user_id
        )

        assert result["animals_served"]["total"] == 20
        assert result["adoptions"]["total"] == 10
        assert result["donations"]["total_count"] == 25
        assert result["in_kind_donations"]["total"] == 5
        assert result["fund_allocation"]["total_cents"] == 500000
        assert result["performance_metrics"]["avg_time_to_adoption_days"] == 12.5
        # cost_per_adoption = 500000 / 10 = 50000
        assert result["performance_metrics"]["cost_per_adoption_cents"] == 50000
        assert result["report_metadata"]["generated_by_user_id"] == str(user_id)
        assert result["volunteers"]["unique_volunteers"] == 5
        assert result["volunteers"]["total_hours"] == 60.0
        assert result["foster_placements"]["active_during_period"] == 7
        assert result["foster_placements"]["new_placements"] == 3


class TestCountVolunteerHours:
    """Tests for count_volunteer_hours."""

    @pytest.mark.asyncio
    async def test_returns_totals_and_by_category(self) -> None:
        db = AsyncMock()

        # Category breakdown query result
        cat_row1 = MagicMock()
        cat_row1.category = "animal_care"
        cat_row1.total_hours = 40.0

        cat_row2 = MagicMock()
        cat_row2.category = "transport"
        cat_row2.total_hours = 10.5

        cat_result = MagicMock()
        cat_result.all.return_value = [cat_row1, cat_row2]

        # Global unique + total query result
        unique_row = MagicMock()
        unique_row.unique_volunteers = 8
        unique_row.total_hours = 50.5

        unique_result = MagicMock()
        unique_result.one.return_value = unique_row

        db.execute.side_effect = [cat_result, unique_result]

        result = await impact_report_service.count_volunteer_hours(db, START, END)

        assert result["unique_volunteers"] == 8
        assert result["total_hours"] == 50.5
        assert result["by_category"]["animal_care"] == 40.0
        assert result["by_category"]["transport"] == 10.5

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_activity(self) -> None:
        db = AsyncMock()

        cat_result = MagicMock()
        cat_result.all.return_value = []

        unique_row = MagicMock()
        unique_row.unique_volunteers = None
        unique_row.total_hours = None

        unique_result = MagicMock()
        unique_result.one.return_value = unique_row

        db.execute.side_effect = [cat_result, unique_result]

        result = await impact_report_service.count_volunteer_hours(db, START, END)

        assert result["unique_volunteers"] == 0
        assert result["total_hours"] == 0.0
        assert result["by_category"] == {}


class TestCountActiveFosterPlacements:
    """Tests for count_active_foster_placements."""

    @pytest.mark.asyncio
    async def test_returns_active_and_new_counts(self) -> None:
        db = AsyncMock()

        active_result = MagicMock()
        active_result.scalar.return_value = 12

        new_result = MagicMock()
        new_result.scalar.return_value = 4

        db.execute.side_effect = [active_result, new_result]

        result = await impact_report_service.count_active_foster_placements(db, START, END)

        assert result["active_during_period"] == 12
        assert result["new_placements"] == 4

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_placements(self) -> None:
        db = AsyncMock()

        active_result = MagicMock()
        active_result.scalar.return_value = None

        new_result = MagicMock()
        new_result.scalar.return_value = None

        db.execute.side_effect = [active_result, new_result]

        result = await impact_report_service.count_active_foster_placements(db, START, END)

        assert result["active_during_period"] == 0
        assert result["new_placements"] == 0
