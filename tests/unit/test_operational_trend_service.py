"""Unit tests for the operational dashboard trend data functions (RAP-252)."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.operational_metrics_service import (
    _INTERVAL_CONFIG,
    _LABEL_FORMAT,
    TrendData,
    TrendDataPoint,
    get_trend_data,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_rows(periods_and_counts: list[tuple]) -> MagicMock:
    """Build a mock execute result that iterates over (period, count) rows."""
    rows = []
    for period, count in periods_and_counts:
        row = MagicMock()
        row.period = period
        # Rows returned for intake queries have intake_count; for outcome, outcome_count.
        # The service accesses the dict representation so we just store both.
        row.intake_count = count
        row.outcome_count = count
        rows.append(row)
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter(rows))
    return result


def _make_db_with_results(intake_rows, outcome_rows) -> AsyncMock:
    """Return a mock db that yields intake rows then outcome rows in sequence."""
    db = AsyncMock()
    intake_result = MagicMock()
    intake_result.__iter__ = MagicMock(return_value=iter(intake_rows))
    outcome_result = MagicMock()
    outcome_result.__iter__ = MagicMock(return_value=iter(outcome_rows))
    db.execute = AsyncMock(side_effect=[intake_result, outcome_result])
    return db


# ---------------------------------------------------------------------------
# TrendDataPoint
# ---------------------------------------------------------------------------


class TestTrendDataPoint:
    def test_stores_all_fields(self) -> None:
        dp = TrendDataPoint(period_label="Mar 2026", intake_count=10, outcome_count=7)
        assert dp.period_label == "Mar 2026"
        assert dp.intake_count == 10
        assert dp.outcome_count == 7

    def test_zero_counts_valid(self) -> None:
        dp = TrendDataPoint(period_label="01/04", intake_count=0, outcome_count=0)
        assert dp.intake_count == 0
        assert dp.outcome_count == 0


# ---------------------------------------------------------------------------
# TrendData
# ---------------------------------------------------------------------------


class TestTrendData:
    def test_stores_all_fields(self) -> None:
        dp = TrendDataPoint("Abr 2026", 5, 3)
        td = TrendData(
            interval="monthly",
            lookback_days=365,
            data_points=[dp],
            generated_at="2026-03-29T10:00:00Z",
        )
        assert td.interval == "monthly"
        assert td.lookback_days == 365
        assert len(td.data_points) == 1
        assert td.generated_at == "2026-03-29T10:00:00Z"

    def test_empty_data_points_allowed(self) -> None:
        td = TrendData(
            interval="daily",
            lookback_days=30,
            data_points=[],
            generated_at="2026-03-29T00:00:00Z",
        )
        assert td.data_points == []


# ---------------------------------------------------------------------------
# Interval config constants
# ---------------------------------------------------------------------------


class TestIntervalConfig:
    def test_all_three_intervals_present(self) -> None:
        assert "daily" in _INTERVAL_CONFIG
        assert "weekly" in _INTERVAL_CONFIG
        assert "monthly" in _INTERVAL_CONFIG

    def test_daily_default_days_is_30(self) -> None:
        assert _INTERVAL_CONFIG["daily"]["default_days"] == 30

    def test_weekly_default_days_is_90(self) -> None:
        assert _INTERVAL_CONFIG["weekly"]["default_days"] == 90

    def test_monthly_default_days_is_365(self) -> None:
        assert _INTERVAL_CONFIG["monthly"]["default_days"] == 365

    def test_label_formats_present(self) -> None:
        for interval in ("daily", "weekly", "monthly"):
            assert interval in _LABEL_FORMAT


# ---------------------------------------------------------------------------
# get_trend_data
# ---------------------------------------------------------------------------


class TestGetTrendData:
    @pytest.mark.asyncio
    async def test_returns_trend_data_instance(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="monthly")
        assert isinstance(result, TrendData)

    @pytest.mark.asyncio
    async def test_interval_is_preserved(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="weekly")
        assert result.interval == "weekly"

    @pytest.mark.asyncio
    async def test_lookback_days_uses_default_when_none(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="monthly", lookback_days=None)
        assert result.lookback_days == 365  # monthly default

    @pytest.mark.asyncio
    async def test_lookback_days_override_respected(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="monthly", lookback_days=60)
        assert result.lookback_days == 60

    @pytest.mark.asyncio
    async def test_empty_data_returns_empty_points(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="monthly")
        assert result.data_points == []

    @pytest.mark.asyncio
    async def test_generated_at_is_iso_string(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="daily")
        assert "T" in result.generated_at

    @pytest.mark.asyncio
    async def test_data_points_have_correct_labels_for_datetime_periods(self) -> None:
        period = datetime(2026, 3, 1)
        intake_row = MagicMock()
        intake_row.period = period
        outcome_row = MagicMock()
        outcome_row.period = period

        intake_result = MagicMock()
        intake_result.__iter__ = MagicMock(return_value=iter([intake_row]))
        outcome_result = MagicMock()
        outcome_result.__iter__ = MagicMock(return_value=iter([outcome_row]))

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[intake_result, outcome_result])

        result = await get_trend_data(db, interval="monthly")
        assert len(result.data_points) == 1
        # Monthly label: "%b %Y" → "Mar 2026" (locale-dependent but should match)
        assert "2026" in result.data_points[0].period_label

    @pytest.mark.asyncio
    async def test_db_execute_called_twice(self) -> None:
        """One call for intake, one for outcomes."""
        db = _make_db_with_results([], [])
        await get_trend_data(db, interval="monthly")
        assert db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_daily_interval_uses_daily_default(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="daily", lookback_days=None)
        assert result.lookback_days == 30

    @pytest.mark.asyncio
    async def test_weekly_interval_uses_weekly_default(self) -> None:
        db = _make_db_with_results([], [])
        result = await get_trend_data(db, interval="weekly", lookback_days=None)
        assert result.lookback_days == 90
