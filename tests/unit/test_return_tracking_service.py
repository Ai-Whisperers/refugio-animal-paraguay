"""Unit tests for return/surrender tracking service (RAP-262, EPIC-53)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.return_tracking_service import (
    ReturnAnalytics,
    ReturnRecord,
    ReturnTrendPoint,
    _month_label,
    _safe_pct,
    get_return_analytics,
    get_return_trend,
    list_return_records,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_follow_up(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "adoption_request_id": uuid4(),
        "return_date": now - timedelta(days=10),
        "return_reason_code": "behavior_issues",
        "return_notes": "Animal was too energetic",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_reason_row(reason_code, count):
    row = MagicMock()
    row.return_reason_code = reason_code
    row.count = count
    return row


def _make_trend_row(year, month, return_count):
    row = MagicMock()
    row.year = year
    row.month = month
    row.return_count = return_count
    return row


# ---------------------------------------------------------------------------
# _safe_pct
# ---------------------------------------------------------------------------


class TestSafePct:
    def test_normal(self):
        assert _safe_pct(3, 10) == 30.0

    def test_zero_denominator(self):
        assert _safe_pct(5, 0) == 0.0

    def test_rounding(self):
        result = _safe_pct(1, 3)
        assert result == 33.33


# ---------------------------------------------------------------------------
# _month_label
# ---------------------------------------------------------------------------


class TestMonthLabel:
    def test_march_2026(self):
        assert _month_label(2026, 3) == "Mar 2026"

    def test_january(self):
        assert _month_label(2025, 1) == "Jan 2025"

    def test_december(self):
        assert _month_label(2024, 12) == "Dec 2024"


# ---------------------------------------------------------------------------
# get_return_analytics
# ---------------------------------------------------------------------------


class TestGetReturnAnalytics:
    @pytest.mark.asyncio
    async def test_returns_analytics(self):
        db = AsyncMock()

        # total returns
        total_result = MagicMock()
        total_result.scalar_one.return_value = 8

        # total follow-ups
        total_fu_result = MagicMock()
        total_fu_result.scalar_one.return_value = 40

        # reason breakdown
        reason_result = MagicMock()
        reason_rows = [
            _make_reason_row("behavior_issues", 5),
            _make_reason_row("moved_away", 2),
            _make_reason_row(None, 1),
        ]
        reason_result.fetchall.return_value = reason_rows

        db.execute = AsyncMock(side_effect=[total_result, total_fu_result, reason_result])

        analytics = await get_return_analytics(db)

        assert isinstance(analytics, ReturnAnalytics)
        assert analytics.total_returns == 8
        assert analytics.return_rate_pct == 20.0
        assert len(analytics.reason_breakdown) == 3
        assert analytics.reason_breakdown[0].reason_code == "behavior_issues"
        assert analytics.reason_breakdown[0].count == 5
        assert analytics.reason_breakdown[2].reason_code == "unknown"

    @pytest.mark.asyncio
    async def test_empty_database(self):
        db = AsyncMock()

        total_result = MagicMock()
        total_result.scalar_one.return_value = 0

        total_fu_result = MagicMock()
        total_fu_result.scalar_one.return_value = 0

        reason_result = MagicMock()
        reason_result.fetchall.return_value = []

        db.execute = AsyncMock(side_effect=[total_result, total_fu_result, reason_result])

        analytics = await get_return_analytics(db)

        assert analytics.total_returns == 0
        assert analytics.return_rate_pct == 0.0
        assert analytics.reason_breakdown == []

    @pytest.mark.asyncio
    async def test_generated_at_is_iso8601(self):
        db = AsyncMock()

        for mock_result in [MagicMock(), MagicMock()]:
            mock_result.scalar_one.return_value = 0

        empty_result = MagicMock()
        empty_result.fetchall.return_value = []

        total_r = MagicMock()
        total_r.scalar_one.return_value = 0
        fu_r = MagicMock()
        fu_r.scalar_one.return_value = 0

        db.execute = AsyncMock(side_effect=[total_r, fu_r, empty_result])

        analytics = await get_return_analytics(db)

        datetime.fromisoformat(analytics.generated_at)


# ---------------------------------------------------------------------------
# get_return_trend
# ---------------------------------------------------------------------------


class TestGetReturnTrend:
    @pytest.mark.asyncio
    async def test_returns_trend_points(self):
        db = AsyncMock()
        rows = [
            _make_trend_row(2026, 1, 2),
            _make_trend_row(2026, 2, 5),
            _make_trend_row(2026, 3, 3),
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = rows
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_return_trend(db)

        assert len(result) == 3
        assert all(isinstance(p, ReturnTrendPoint) for p in result)
        assert result[0].period_label == "Jan 2026"
        assert result[2].return_count == 3

    @pytest.mark.asyncio
    async def test_empty_trend(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_return_trend(db)

        assert result == []


# ---------------------------------------------------------------------------
# list_return_records
# ---------------------------------------------------------------------------


class TestListReturnRecords:
    @pytest.mark.asyncio
    async def test_returns_records(self):
        fu1 = _make_follow_up()
        fu2 = _make_follow_up()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter([fu1, fu2])
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_return_records(db)

        assert len(result) == 2
        assert all(isinstance(r, ReturnRecord) for r in result)

    @pytest.mark.asyncio
    async def test_empty(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter([])
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_return_records(db)

        assert result == []
