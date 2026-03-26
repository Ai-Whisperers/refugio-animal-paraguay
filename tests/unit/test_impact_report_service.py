"""Unit tests for impact report service logic.

Tests each stats aggregation function with mocked database sessions.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.schemas.impact_report import (
    AdoptionStats,
    AnimalStats,
    DonationStats,
    InKindStats,
)
from src.services.impact_report_service import (
    _get_adoption_stats,
    _get_animal_stats,
    _get_donation_stats,
    _get_in_kind_stats,
    generate_impact_report,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 3, 31, tzinfo=UTC)


class TestGetAnimalStats:
    """Tests for _get_animal_stats aggregation."""

    @pytest.mark.asyncio
    async def test_returns_zero_counts_when_empty(self) -> None:
        db = AsyncMock()

        total_result = MagicMock()
        total_result.scalar_one.return_value = 0
        intakes_result = MagicMock()
        intakes_result.scalar_one.return_value = 0
        species_result = MagicMock()
        species_result.__iter__ = MagicMock(return_value=iter([]))
        status_result = MagicMock()
        status_result.__iter__ = MagicMock(return_value=iter([]))

        db.execute = AsyncMock(
            side_effect=[total_result, intakes_result, species_result, status_result]
        )

        result = await _get_animal_stats(db, START, END)

        assert isinstance(result, AnimalStats)
        assert result.total_animals == 0
        assert result.new_intakes == 0
        assert result.by_species == []
        assert result.by_status == []

    @pytest.mark.asyncio
    async def test_aggregates_species_and_status_counts(self) -> None:
        db = AsyncMock()

        total_result = MagicMock()
        total_result.scalar_one.return_value = 15
        intakes_result = MagicMock()
        intakes_result.scalar_one.return_value = 5

        dog_row = MagicMock(species="dog", cnt=10)
        cat_row = MagicMock(species="cat", cnt=5)
        species_result = MagicMock()
        species_result.__iter__ = MagicMock(return_value=iter([dog_row, cat_row]))

        available_row = MagicMock(status="available", cnt=8)
        intake_row = MagicMock(status="intake", cnt=7)
        status_result = MagicMock()
        status_result.__iter__ = MagicMock(
            return_value=iter([available_row, intake_row])
        )

        db.execute = AsyncMock(
            side_effect=[total_result, intakes_result, species_result, status_result]
        )

        result = await _get_animal_stats(db, START, END)

        assert result.total_animals == 15
        assert result.new_intakes == 5
        assert len(result.by_species) == 2
        assert result.by_species[0].species == "dog"
        assert result.by_species[0].count == 10
        assert len(result.by_status) == 2


class TestGetAdoptionStats:
    """Tests for _get_adoption_stats aggregation."""

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_requests(self) -> None:
        db = AsyncMock()
        results = [MagicMock() for _ in range(4)]
        for r in results:
            r.scalar_one.return_value = 0
        db.execute = AsyncMock(side_effect=results)

        result = await _get_adoption_stats(db, START, END)

        assert isinstance(result, AdoptionStats)
        assert result.total_requests == 0
        assert result.approval_rate_pct == 0.0

    @pytest.mark.asyncio
    async def test_calculates_approval_rate(self) -> None:
        db = AsyncMock()
        total = MagicMock()
        total.scalar_one.return_value = 10
        approved = MagicMock()
        approved.scalar_one.return_value = 7
        rejected = MagicMock()
        rejected.scalar_one.return_value = 2
        pending = MagicMock()
        pending.scalar_one.return_value = 1
        db.execute = AsyncMock(side_effect=[total, approved, rejected, pending])

        result = await _get_adoption_stats(db, START, END)

        assert result.total_requests == 10
        assert result.approved == 7
        assert result.rejected == 2
        assert result.pending == 1
        assert result.approval_rate_pct == 70.0


class TestGetDonationStats:
    """Tests for _get_donation_stats aggregation."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_donations(self) -> None:
        db = AsyncMock()
        total = MagicMock()
        total.scalar_one.return_value = 0
        currency = MagicMock()
        currency.__iter__ = MagicMock(return_value=iter([]))
        donors = MagicMock()
        donors.scalar_one.return_value = 0
        db.execute = AsyncMock(side_effect=[total, currency, donors])

        result = await _get_donation_stats(db, START, END)

        assert isinstance(result, DonationStats)
        assert result.total_completed == 0
        assert result.total_by_currency == []
        assert result.unique_donors == 0

    @pytest.mark.asyncio
    async def test_aggregates_by_currency(self) -> None:
        db = AsyncMock()
        total = MagicMock()
        total.scalar_one.return_value = 5
        eur_row = MagicMock(currency="EUR", total_cents=100000, donation_count=3)
        pyg_row = MagicMock(currency="PYG", total_cents=500000, donation_count=2)
        currency = MagicMock()
        currency.__iter__ = MagicMock(return_value=iter([eur_row, pyg_row]))
        donors = MagicMock()
        donors.scalar_one.return_value = 4
        db.execute = AsyncMock(side_effect=[total, currency, donors])

        result = await _get_donation_stats(db, START, END)

        assert result.total_completed == 5
        assert len(result.total_by_currency) == 2
        assert result.total_by_currency[0].currency == "EUR"
        assert result.unique_donors == 4


class TestGetInKindStats:
    """Tests for _get_in_kind_stats aggregation."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_in_kind(self) -> None:
        db = AsyncMock()
        total = MagicMock()
        total.scalar_one.return_value = 0
        categories = MagicMock()
        categories.__iter__ = MagicMock(return_value=iter([]))
        db.execute = AsyncMock(side_effect=[total, categories])

        result = await _get_in_kind_stats(db, START, END)

        assert isinstance(result, InKindStats)
        assert result.total_donations == 0
        assert result.by_category == []

    @pytest.mark.asyncio
    async def test_aggregates_by_category(self) -> None:
        db = AsyncMock()
        total = MagicMock()
        total.scalar_one.return_value = 8
        food_row = MagicMock(item_type="food", cnt=5, value_cents=200000)
        medical_row = MagicMock(
            item_type="medical_supplies", cnt=3, value_cents=150000
        )
        categories = MagicMock()
        categories.__iter__ = MagicMock(return_value=iter([food_row, medical_row]))
        db.execute = AsyncMock(side_effect=[total, categories])

        result = await _get_in_kind_stats(db, START, END)

        assert result.total_donations == 8
        assert len(result.by_category) == 2
        assert result.by_category[0].category == "food"
        assert result.by_category[0].count == 5


class TestGenerateImpactReport:
    """Tests for the top-level generate_impact_report function."""

    @pytest.mark.asyncio
    async def test_produces_complete_report_structure(self) -> None:
        db = AsyncMock()
        # 4 queries for animals, 4 for adoptions, 3 for donations, 2 for in-kind = 13
        mocks = []
        for _ in range(13):
            m = MagicMock()
            m.scalar_one.return_value = 0
            m.__iter__ = MagicMock(return_value=iter([]))
            mocks.append(m)
        db.execute = AsyncMock(side_effect=mocks)

        result = await generate_impact_report(db, START, END)

        assert result.report_title == "Refugio Animal Paraguay — Impact Report"
        assert result.start_date == START
        assert result.end_date == END
        assert result.generated_at is not None
        assert isinstance(result.animals, AnimalStats)
        assert isinstance(result.adoptions, AdoptionStats)
        assert isinstance(result.donations, DonationStats)
        assert isinstance(result.in_kind, InKindStats)
