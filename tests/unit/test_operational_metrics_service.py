"""Unit tests for the operational metrics service (RAP-250)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.animal import AnimalStatus
from src.services.operational_metrics_service import (
    DEFAULT_SHELTER_CAPACITY,
    SHELTERED_STATUSES,
    OccupancyMetrics,
    OperationalMetrics,
    PopulationBreakdown,
    _get_avg_los_days,
    _get_period_counts,
    _get_population_breakdown,
    _get_species_breakdown,
    get_operational_metrics,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> AsyncMock:
    """Return a mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


def _scalar_result(value):
    """Return a mock that behaves like a scalar result."""
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _row_result(**kwargs):
    """Return a mock that behaves like a one-row result."""
    row = MagicMock()
    for key, value in kwargs.items():
        setattr(row, key, value)
    result = MagicMock()
    result.one.return_value = row
    return result


# ---------------------------------------------------------------------------
# PopulationBreakdown unit tests
# ---------------------------------------------------------------------------


class TestPopulationBreakdown:
    def test_total_sums_sheltered_statuses(self) -> None:
        pop = PopulationBreakdown(
            intake=10,
            quarantine=5,
            available=20,
            foster=3,
            under_treatment=2,
            adopted=50,
            deceased=1,
        )
        # Total only counts in-facility statuses (not foster which is offsite)
        # The service currently includes foster in total — verify consistent with impl
        assert (
            pop.total == 10 + 5 + 20 + 3 + 2
        )  # intake+quarantine+available+foster+under_treatment

    def test_total_excludes_adopted_and_deceased(self) -> None:
        pop = PopulationBreakdown(
            intake=0,
            quarantine=0,
            available=0,
            foster=0,
            under_treatment=0,
            adopted=100,
            deceased=50,
        )
        assert pop.total == 0

    def test_total_reflects_all_sheltered(self) -> None:
        pop = PopulationBreakdown(
            intake=1,
            quarantine=1,
            available=1,
            foster=1,
            under_treatment=1,
            adopted=1,
            deceased=1,
        )
        assert pop.total == 5  # 5 sheltered statuses (foster counted in total)


# ---------------------------------------------------------------------------
# OccupancyMetrics unit tests
# ---------------------------------------------------------------------------


class TestOccupancyMetrics:
    def test_occupancy_rate_calculation(self) -> None:
        occupancy = OccupancyMetrics(current_count=100, capacity=200)
        assert occupancy.occupancy_rate_pct == 50.0

    def test_full_capacity(self) -> None:
        occupancy = OccupancyMetrics(current_count=200, capacity=200)
        assert occupancy.occupancy_rate_pct == 100.0

    def test_empty_shelter(self) -> None:
        occupancy = OccupancyMetrics(current_count=0, capacity=200)
        assert occupancy.occupancy_rate_pct == 0.0

    def test_zero_capacity_avoids_division_error(self) -> None:
        occupancy = OccupancyMetrics(current_count=5, capacity=0)
        assert occupancy.occupancy_rate_pct == 0.0

    def test_over_capacity(self) -> None:
        occupancy = OccupancyMetrics(current_count=220, capacity=200)
        assert occupancy.occupancy_rate_pct == 110.0


# ---------------------------------------------------------------------------
# _get_population_breakdown tests
# ---------------------------------------------------------------------------


class TestGetPopulationBreakdown:
    @pytest.mark.asyncio
    async def test_maps_db_row_to_breakdown(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _row_result(
            intake=10,
            quarantine=5,
            available=20,
            foster=3,
            under_treatment=2,
            adopted=50,
            deceased=1,
        )
        result = await _get_population_breakdown(mock_db)
        assert result.intake == 10
        assert result.quarantine == 5
        assert result.available == 20
        assert result.foster == 3
        assert result.under_treatment == 2
        assert result.adopted == 50
        assert result.deceased == 1

    @pytest.mark.asyncio
    async def test_handles_none_values_from_empty_table(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _row_result(
            intake=None,
            quarantine=None,
            available=None,
            foster=None,
            under_treatment=None,
            adopted=None,
            deceased=None,
        )
        result = await _get_population_breakdown(mock_db)
        assert result.intake == 0
        assert result.total == 0


# ---------------------------------------------------------------------------
# _get_period_counts tests
# ---------------------------------------------------------------------------


class TestGetPeriodCounts:
    @pytest.mark.asyncio
    async def test_returns_intake_and_outcome(self, mock_db: AsyncMock) -> None:
        mock_db.execute.side_effect = [
            _scalar_result(15),  # intake_count
            _scalar_result(8),  # outcome_count
        ]
        result = await _get_period_counts(mock_db, period_days=30)
        assert result.intake_count == 15
        assert result.outcome_count == 8
        assert result.period_days == 30

    @pytest.mark.asyncio
    async def test_handles_none_counts(self, mock_db: AsyncMock) -> None:
        mock_db.execute.side_effect = [
            _scalar_result(None),
            _scalar_result(None),
        ]
        result = await _get_period_counts(mock_db, period_days=7)
        assert result.intake_count == 0
        assert result.outcome_count == 0


# ---------------------------------------------------------------------------
# _get_species_breakdown tests
# ---------------------------------------------------------------------------


class TestGetSpeciesBreakdown:
    @pytest.mark.asyncio
    async def test_maps_species_counts(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _row_result(dog=40, cat=25, other=5)
        result = await _get_species_breakdown(mock_db)
        assert result.dog == 40
        assert result.cat == 25
        assert result.other == 5

    @pytest.mark.asyncio
    async def test_handles_none_species(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _row_result(dog=None, cat=None, other=None)
        result = await _get_species_breakdown(mock_db)
        assert result.dog == 0
        assert result.cat == 0
        assert result.other == 0


# ---------------------------------------------------------------------------
# _get_avg_los_days tests
# ---------------------------------------------------------------------------


class TestGetAvgLosDays:
    @pytest.mark.asyncio
    async def test_returns_rounded_average(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _scalar_result(18.567)
        result = await _get_avg_los_days(mock_db)
        assert result == 18.6  # rounded to 1 decimal

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_shelter(self, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = _scalar_result(None)
        result = await _get_avg_los_days(mock_db)
        assert result == 0.0


# ---------------------------------------------------------------------------
# get_operational_metrics integration test (mocked DB)
# ---------------------------------------------------------------------------


class TestGetOperationalMetrics:
    @pytest.mark.asyncio
    async def test_assembles_all_metrics(self, mock_db: AsyncMock) -> None:
        mock_db.execute.side_effect = [
            # population
            _row_result(
                intake=5,
                quarantine=2,
                available=15,
                foster=1,
                under_treatment=1,
                adopted=30,
                deceased=0,
            ),
            # period intake
            _scalar_result(8),
            # period outcomes
            _scalar_result(6),
            # species
            _row_result(dog=18, cat=5, other=1),
            # avg los
            _scalar_result(12.3),
        ]
        metrics = await get_operational_metrics(mock_db, period_days=30, capacity=100)

        assert isinstance(metrics, OperationalMetrics)
        assert metrics.population.intake == 5
        assert metrics.population.total == 24  # 5+2+15+1+1
        assert metrics.occupancy.current_count == 24
        assert metrics.occupancy.capacity == 100
        assert metrics.occupancy.occupancy_rate_pct == 24.0
        assert metrics.period.intake_count == 8
        assert metrics.period.outcome_count == 6
        assert metrics.species.dog == 18
        assert metrics.avg_los_days == 12.3

    @pytest.mark.asyncio
    async def test_uses_default_capacity(self, mock_db: AsyncMock) -> None:
        mock_db.execute.side_effect = [
            _row_result(
                intake=0,
                quarantine=0,
                available=0,
                foster=0,
                under_treatment=0,
                adopted=0,
                deceased=0,
            ),
            _scalar_result(0),
            _scalar_result(0),
            _row_result(dog=0, cat=0, other=0),
            _scalar_result(0.0),
        ]
        metrics = await get_operational_metrics(mock_db)
        assert metrics.occupancy.capacity == DEFAULT_SHELTER_CAPACITY

    @pytest.mark.asyncio
    async def test_generated_at_is_iso_string(self, mock_db: AsyncMock) -> None:
        mock_db.execute.side_effect = [
            _row_result(
                intake=1,
                quarantine=0,
                available=0,
                foster=0,
                under_treatment=0,
                adopted=0,
                deceased=0,
            ),
            _scalar_result(1),
            _scalar_result(0),
            _row_result(dog=1, cat=0, other=0),
            _scalar_result(5.0),
        ]
        metrics = await get_operational_metrics(mock_db)
        # Should be a valid ISO 8601 datetime string
        assert "T" in metrics.generated_at
        assert (
            "+" in metrics.generated_at
            or "Z" in metrics.generated_at
            or metrics.generated_at.endswith("+00:00")
        )


# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------


class TestConstants:
    def test_default_capacity_is_positive(self) -> None:
        assert DEFAULT_SHELTER_CAPACITY > 0

    def test_sheltered_statuses_excludes_adopted_and_deceased(self) -> None:
        assert AnimalStatus.ADOPTED not in SHELTERED_STATUSES
        assert AnimalStatus.DECEASED not in SHELTERED_STATUSES

    def test_sheltered_statuses_includes_core_states(self) -> None:
        assert AnimalStatus.INTAKE in SHELTERED_STATUSES
        assert AnimalStatus.AVAILABLE in SHELTERED_STATUSES
        assert AnimalStatus.QUARANTINE in SHELTERED_STATUSES
        assert AnimalStatus.UNDER_TREATMENT in SHELTERED_STATUSES
