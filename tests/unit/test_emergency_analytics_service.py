"""Unit tests for emergency analytics service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.emergency_analytics_service import (
    MAX_DAYS_RANGE,
    AnalyticsError,
    InvalidDateRangeError,
    get_daily_time_series,
    get_emergency_summary,
    get_funding_performance,
    get_top_funded_emergencies,
    get_urgency_distribution,
    validate_date_range,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_emergency_mock(**overrides):
    """Create a mock EmergencyCase."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "title": "Test emergency",
        "status": "active",
        "urgency": "high",
        "amount_needed_cents": 50000,
        "amount_raised_cents": 25000,
        "currency": "USD",
        "is_deleted": False,
        "created_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for analytics error hierarchy."""

    def test_analytics_error_base(self) -> None:
        err = AnalyticsError("test", details="detail")
        assert err.message == "test"
        assert err.details == "detail"

    def test_invalid_date_range(self) -> None:
        err = InvalidDateRangeError("too wide")
        assert "too wide" in err.details


# ---------------------------------------------------------------------------
# validate_date_range
# ---------------------------------------------------------------------------


class TestValidateDateRange:
    """Tests for date range validation."""

    def test_valid_range(self) -> None:
        now = datetime.now(UTC)
        validate_date_range(now - timedelta(days=7), now)

    def test_start_after_end_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(InvalidDateRangeError):
            validate_date_range(now, now - timedelta(days=1))

    def test_same_dates_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(InvalidDateRangeError):
            validate_date_range(now, now)

    def test_too_wide_range_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(InvalidDateRangeError):
            validate_date_range(now - timedelta(days=MAX_DAYS_RANGE + 1), now)


# ---------------------------------------------------------------------------
# get_emergency_summary
# ---------------------------------------------------------------------------


class TestGetEmergencySummary:
    """Tests for get_emergency_summary."""

    @pytest.mark.asyncio
    async def test_returns_summary(self) -> None:
        db = AsyncMock()

        # Status counts query result
        status_row_active = MagicMock()
        status_row_active.status = "active"
        status_row_active.count = 5
        status_row_funded = MagicMock()
        status_row_funded.status = "funded"
        status_row_funded.count = 3

        status_result = MagicMock()
        status_result.__iter__ = MagicMock(
            return_value=iter([status_row_active, status_row_funded])
        )

        # Funding totals
        funding_row = MagicMock()
        funding_row.total_needed = 500000
        funding_row.total_raised = 250000
        funding_result = MagicMock()
        funding_result.one.return_value = funding_row

        db.execute.side_effect = [status_result, funding_result]

        summary = await get_emergency_summary(db)
        assert summary["total_cases"] == 8
        assert summary["active"] == 5
        assert summary["funded"] == 3
        assert summary["total_needed_cents"] == 500000
        assert summary["total_raised_cents"] == 250000
        assert summary["average_funding_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_empty_database(self) -> None:
        db = AsyncMock()

        status_result = MagicMock()
        status_result.__iter__ = MagicMock(return_value=iter([]))

        funding_row = MagicMock()
        funding_row.total_needed = 0
        funding_row.total_raised = 0
        funding_result = MagicMock()
        funding_result.one.return_value = funding_row

        db.execute.side_effect = [status_result, funding_result]

        summary = await get_emergency_summary(db)
        assert summary["total_cases"] == 0
        assert summary["average_funding_percentage"] == 0


# ---------------------------------------------------------------------------
# get_urgency_distribution
# ---------------------------------------------------------------------------


class TestGetUrgencyDistribution:
    """Tests for get_urgency_distribution."""

    @pytest.mark.asyncio
    async def test_returns_distribution(self) -> None:
        db = AsyncMock()

        row_high = MagicMock()
        row_high.urgency = "high"
        row_high.count = 10
        row_high.total_needed = 300000
        row_high.total_raised = 150000

        row_critical = MagicMock()
        row_critical.urgency = "critical"
        row_critical.count = 5
        row_critical.total_needed = 200000
        row_critical.total_raised = 180000

        result = MagicMock()
        result.__iter__ = MagicMock(return_value=iter([row_high, row_critical]))
        db.execute.return_value = result

        dist = await get_urgency_distribution(db)
        assert len(dist) == 2
        assert dist[0]["urgency"] == "high"
        assert dist[0]["count"] == 10
        assert dist[1]["urgency"] == "critical"
        assert dist[1]["average_funding_percentage"] == 90.0


# ---------------------------------------------------------------------------
# get_daily_time_series
# ---------------------------------------------------------------------------


class TestGetDailyTimeSeries:
    """Tests for get_daily_time_series."""

    @pytest.mark.asyncio
    async def test_returns_time_series(self) -> None:
        db = AsyncMock()

        day1 = MagicMock()
        day1.day = datetime(2026, 3, 20, tzinfo=UTC)
        day1.cases_created = 2
        day1.total_raised = 10000

        day2 = MagicMock()
        day2.day = datetime(2026, 3, 21, tzinfo=UTC)
        day2.cases_created = 1
        day2.total_raised = 5000

        result = MagicMock()
        result.__iter__ = MagicMock(return_value=iter([day1, day2]))
        db.execute.return_value = result

        ts = await get_daily_time_series(db)
        assert len(ts) == 2
        assert ts[0]["cases_created"] == 2
        assert ts[1]["total_raised_cents"] == 5000

    @pytest.mark.asyncio
    async def test_custom_date_range(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.__iter__ = MagicMock(return_value=iter([]))
        db.execute.return_value = result

        now = datetime.now(UTC)
        ts = await get_daily_time_series(
            db,
            start_date=now - timedelta(days=7),
            end_date=now,
        )
        assert ts == []

    @pytest.mark.asyncio
    async def test_invalid_range_raises(self) -> None:
        db = AsyncMock()
        now = datetime.now(UTC)

        with pytest.raises(InvalidDateRangeError):
            await get_daily_time_series(
                db,
                start_date=now,
                end_date=now - timedelta(days=1),
            )


# ---------------------------------------------------------------------------
# get_funding_performance
# ---------------------------------------------------------------------------


class TestGetFundingPerformance:
    """Tests for get_funding_performance."""

    @pytest.mark.asyncio
    async def test_returns_performance(self) -> None:
        db = AsyncMock()

        row_funded = MagicMock()
        row_funded.status = "funded"
        row_funded.count = 7
        row_closed = MagicMock()
        row_closed.status = "closed"
        row_closed.count = 3
        row_expired = MagicMock()
        row_expired.status = "expired"
        row_expired.count = 2

        completed_result = MagicMock()
        completed_result.__iter__ = MagicMock(
            return_value=iter([row_funded, row_closed, row_expired])
        )

        avg_row = MagicMock()
        avg_row.avg_pct = 75.5
        avg_result = MagicMock()
        avg_result.one.return_value = avg_row

        db.execute.side_effect = [completed_result, avg_result]

        perf = await get_funding_performance(db)
        assert perf["total_completed"] == 12
        assert perf["funded_count"] == 10  # funded + closed
        assert perf["expired_count"] == 2
        assert perf["success_rate"] == 83.3
        assert perf["average_funding_percentage"] == 75.5

    @pytest.mark.asyncio
    async def test_no_completed_cases(self) -> None:
        db = AsyncMock()

        completed_result = MagicMock()
        completed_result.__iter__ = MagicMock(return_value=iter([]))

        avg_row = MagicMock()
        avg_row.avg_pct = 0
        avg_result = MagicMock()
        avg_result.one.return_value = avg_row

        db.execute.side_effect = [completed_result, avg_result]

        perf = await get_funding_performance(db)
        assert perf["success_rate"] == 0


# ---------------------------------------------------------------------------
# get_top_funded_emergencies
# ---------------------------------------------------------------------------


class TestGetTopFundedEmergencies:
    """Tests for get_top_funded_emergencies."""

    @pytest.mark.asyncio
    async def test_returns_top_funded(self) -> None:
        cases = [
            _make_emergency_mock(
                amount_raised_cents=80000,
                amount_needed_cents=100000,
            ),
            _make_emergency_mock(
                amount_raised_cents=50000,
                amount_needed_cents=50000,
            ),
        ]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = cases
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        top = await get_top_funded_emergencies(db, limit=5)
        assert len(top) == 2
        assert top[0]["amount_raised_cents"] == 80000
        assert top[1]["funding_percentage"] == 100

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        top = await get_top_funded_emergencies(db, limit=5)
        assert top == []
