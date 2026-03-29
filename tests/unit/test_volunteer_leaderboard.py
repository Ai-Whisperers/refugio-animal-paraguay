"""Unit tests for volunteer leaderboard API (RAP-196).

Tests schemas, period helpers, and response building without a live database.
"""

from datetime import UTC, date, datetime
from uuid import uuid4

from src.api.volunteer_leaderboard import (
    LEADERBOARD_DEFAULT_LIMIT,
    LEADERBOARD_MAX_LIMIT,
    VALID_PERIODS,
    LeaderboardEntry,
    LeaderboardResponse,
    _period_start_date,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestLeaderboardConstants:
    def test_default_limit(self) -> None:
        assert LEADERBOARD_DEFAULT_LIMIT == 10

    def test_max_limit(self) -> None:
        assert LEADERBOARD_MAX_LIMIT == 50

    def test_valid_periods_contains_expected_values(self) -> None:
        assert "all" in VALID_PERIODS
        assert "month" in VALID_PERIODS
        assert "quarter" in VALID_PERIODS
        assert "year" in VALID_PERIODS

    def test_valid_periods_count(self) -> None:
        assert len(VALID_PERIODS) == 4


# ---------------------------------------------------------------------------
# _period_start_date helper
# ---------------------------------------------------------------------------


class TestPeriodStartDate:
    def test_all_returns_none(self) -> None:
        assert _period_start_date("all") is None

    def test_month_returns_first_day_of_month(self) -> None:
        result = _period_start_date("month")
        assert result is not None
        assert result.day == 1
        today = datetime.now(UTC).date()
        assert result.month == today.month
        assert result.year == today.year

    def test_year_returns_january_first(self) -> None:
        result = _period_start_date("year")
        assert result is not None
        assert result.month == 1
        assert result.day == 1
        today = datetime.now(UTC).date()
        assert result.year == today.year

    def test_quarter_returns_start_of_current_quarter(self) -> None:
        result = _period_start_date("quarter")
        assert result is not None
        assert result.day == 1
        # Quarter start months: Jan, Apr, Jul, Oct
        assert result.month in (1, 4, 7, 10)
        today = datetime.now(UTC).date()
        assert result.year == today.year

    def test_quarter_month_maps_correctly(self) -> None:
        result = _period_start_date("quarter")
        today = datetime.now(UTC).date()
        expected_quarter_month = ((today.month - 1) // 3) * 3 + 1
        assert result.month == expected_quarter_month

    def test_unknown_period_returns_none(self) -> None:
        # Unmapped periods default to None (same as "all")
        assert _period_start_date("unknown") is None

    def test_result_is_date_not_datetime(self) -> None:
        result = _period_start_date("month")
        assert isinstance(result, date)
        assert not isinstance(result, datetime)


# ---------------------------------------------------------------------------
# LeaderboardEntry schema
# ---------------------------------------------------------------------------


class TestLeaderboardEntry:
    def _make_entry(self, **overrides) -> dict:
        data = {
            "rank": 1,
            "volunteer_id": uuid4(),
            "user_id": uuid4(),
            "full_name": "Ana García",
            "email": "ana@example.com",
            "total_hours_logged": 42.5,
            "skills": ["animal_care", "transport"],
        }
        data.update(overrides)
        return data

    def test_valid_entry(self) -> None:
        entry = LeaderboardEntry(**self._make_entry())
        assert entry.rank == 1
        assert entry.full_name == "Ana García"
        assert entry.total_hours_logged == 42.5
        assert len(entry.skills) == 2

    def test_null_full_name_accepted(self) -> None:
        entry = LeaderboardEntry(**self._make_entry(full_name=None))
        assert entry.full_name is None

    def test_empty_skills_list(self) -> None:
        entry = LeaderboardEntry(**self._make_entry(skills=[]))
        assert entry.skills == []

    def test_rank_ordering(self) -> None:
        e1 = LeaderboardEntry(**self._make_entry(rank=1, total_hours_logged=100.0))
        e2 = LeaderboardEntry(**self._make_entry(rank=2, total_hours_logged=50.0))
        assert e1.rank < e2.rank
        assert e1.total_hours_logged > e2.total_hours_logged


# ---------------------------------------------------------------------------
# LeaderboardResponse schema
# ---------------------------------------------------------------------------


class TestLeaderboardResponse:
    def _make_entry(self, rank: int, hours: float) -> dict:
        return {
            "rank": rank,
            "volunteer_id": uuid4(),
            "user_id": uuid4(),
            "full_name": f"Volunteer {rank}",
            "email": f"volunteer{rank}@example.com",
            "total_hours_logged": hours,
            "skills": [],
        }

    def test_empty_leaderboard(self) -> None:
        resp = LeaderboardResponse(
            period="all",
            period_start=None,
            entries=[],
            total_approved_volunteers=0,
        )
        assert resp.entries == []
        assert resp.total_approved_volunteers == 0

    def test_leaderboard_with_entries(self) -> None:
        entries = [
            LeaderboardEntry(**self._make_entry(1, 100.0)),
            LeaderboardEntry(**self._make_entry(2, 75.0)),
            LeaderboardEntry(**self._make_entry(3, 50.0)),
        ]
        resp = LeaderboardResponse(
            period="month",
            period_start=date.today().replace(day=1),
            entries=entries,
            total_approved_volunteers=10,
        )
        assert len(resp.entries) == 3
        assert resp.entries[0].rank == 1
        assert resp.total_approved_volunteers == 10

    def test_period_field_preserved(self) -> None:
        resp = LeaderboardResponse(
            period="quarter",
            period_start=date(2026, 1, 1),
            entries=[],
            total_approved_volunteers=5,
        )
        assert resp.period == "quarter"
        assert resp.period_start == date(2026, 1, 1)

    def test_all_period_has_null_start(self) -> None:
        resp = LeaderboardResponse(
            period="all",
            period_start=None,
            entries=[],
            total_approved_volunteers=3,
        )
        assert resp.period_start is None
