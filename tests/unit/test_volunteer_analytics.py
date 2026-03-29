"""Unit tests for volunteer analytics API (RAP-197).

Tests helpers, schemas, and response building without a live database.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

from src.api.volunteer_analytics import (
    ANALYTICS_HISTORY_MONTHS,
    MonthlyCount,
    SkillFrequency,
    VolunteerAnalyticsResponse,
    _monthly_joins,
    _skills_distribution,
)
from src.db.models.volunteer_profile import VolunteerProfile

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestAnalyticsConstants:
    def test_history_months_is_positive(self) -> None:
        assert ANALYTICS_HISTORY_MONTHS > 0

    def test_history_months_reasonable(self) -> None:
        # Sanity: should be between 3 and 24
        assert 3 <= ANALYTICS_HISTORY_MONTHS <= 24


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(**overrides) -> MagicMock:
    """Build a MagicMock mimicking a VolunteerProfile ORM row."""
    now = datetime.now(UTC)
    profile = MagicMock(spec=VolunteerProfile)
    defaults = {
        "skills": [],
        "total_hours_logged": 0.0,
        "status": "approved",
        "created_at": now,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(profile, k, v)
    return profile


# ---------------------------------------------------------------------------
# _skills_distribution
# ---------------------------------------------------------------------------


class TestSkillsDistribution:
    def test_empty_profiles(self) -> None:
        result = _skills_distribution([])
        assert result == []

    def test_single_skill(self) -> None:
        profiles = [_make_profile(skills=["animal_care"])]
        result = _skills_distribution(profiles)
        assert len(result) == 1
        assert result[0].skill == "animal_care"
        assert result[0].count == 1

    def test_multiple_profiles_aggregated(self) -> None:
        profiles = [
            _make_profile(skills=["animal_care", "photography"]),
            _make_profile(skills=["animal_care", "transport_driving"]),
            _make_profile(skills=["animal_care"]),
        ]
        result = _skills_distribution(profiles)
        # animal_care appears 3 times — should be first
        assert result[0].skill == "animal_care"
        assert result[0].count == 3

    def test_sorted_by_count_descending(self) -> None:
        profiles = [
            _make_profile(skills=["photography"]),
            _make_profile(skills=["animal_care", "photography"]),
            _make_profile(skills=["animal_care", "photography", "social_media"]),
        ]
        result = _skills_distribution(profiles)
        counts = [s.count for s in result]
        assert counts == sorted(counts, reverse=True)

    def test_none_skills_ignored(self) -> None:
        profiles = [
            _make_profile(skills=None),
            _make_profile(skills=["animal_care"]),
        ]
        result = _skills_distribution(profiles)
        assert len(result) == 1
        assert result[0].skill == "animal_care"

    def test_returns_skill_frequency_objects(self) -> None:
        profiles = [_make_profile(skills=["animal_care"])]
        result = _skills_distribution(profiles)
        assert isinstance(result[0], SkillFrequency)


# ---------------------------------------------------------------------------
# _monthly_joins
# ---------------------------------------------------------------------------


class TestMonthlyJoins:
    def test_returns_n_months(self) -> None:
        result = _monthly_joins([], ANALYTICS_HISTORY_MONTHS)
        assert len(result) == ANALYTICS_HISTORY_MONTHS

    def test_returns_monthly_count_objects(self) -> None:
        result = _monthly_joins([], 3)
        for item in result:
            assert isinstance(item, MonthlyCount)

    def test_empty_profiles_all_zeros(self) -> None:
        result = _monthly_joins([], 6)
        assert all(item.count == 0 for item in result)

    def test_chronological_order(self) -> None:
        result = _monthly_joins([], 6)
        # (year, month) pairs must be ascending
        pairs = [(item.year, item.month) for item in result]
        assert pairs == sorted(pairs)

    def test_profile_in_current_month_counted(self) -> None:
        today = datetime.now(UTC)
        profile = _make_profile(created_at=today)
        result = _monthly_joins([profile], 6)
        current_slot = next(
            item for item in result if item.year == today.year and item.month == today.month
        )
        assert current_slot.count == 1

    def test_old_profile_not_counted(self) -> None:
        # Profile created 10 years ago should not appear in last 6 months
        old_date = datetime(2015, 1, 15, tzinfo=UTC)
        profile = _make_profile(created_at=old_date)
        result = _monthly_joins([profile], 6)
        assert all(item.count == 0 for item in result)

    def test_month_and_year_fields_valid(self) -> None:
        result = _monthly_joins([], 6)
        for item in result:
            assert 1 <= item.month <= 12
            assert item.year >= 2020


# ---------------------------------------------------------------------------
# VolunteerAnalyticsResponse schema
# ---------------------------------------------------------------------------


class TestVolunteerAnalyticsResponse:
    def _make_response(self, **overrides) -> dict:
        today = date.today()
        data = {
            "generated_at": today,
            "total_volunteers": 20,
            "total_approved": 12,
            "total_pending": 5,
            "total_rejected": 2,
            "total_inactive": 1,
            "total_hours_logged": 345.5,
            "avg_hours_per_volunteer": 28.79,
            "skills_distribution": [],
            "monthly_joins": [],
        }
        data.update(overrides)
        return data

    def test_valid_response(self) -> None:
        resp = VolunteerAnalyticsResponse(**self._make_response())
        assert resp.total_volunteers == 20
        assert resp.total_approved == 12
        assert resp.total_hours_logged == 345.5

    def test_zero_volunteers(self) -> None:
        resp = VolunteerAnalyticsResponse(
            **self._make_response(
                total_volunteers=0,
                total_approved=0,
                total_pending=0,
                total_rejected=0,
                total_inactive=0,
                total_hours_logged=0.0,
                avg_hours_per_volunteer=0.0,
            )
        )
        assert resp.total_volunteers == 0
        assert resp.avg_hours_per_volunteer == 0.0

    def test_skills_distribution_field(self) -> None:
        skills = [SkillFrequency(skill="animal_care", count=5)]
        resp = VolunteerAnalyticsResponse(**self._make_response(skills_distribution=skills))
        assert len(resp.skills_distribution) == 1
        assert resp.skills_distribution[0].skill == "animal_care"

    def test_monthly_joins_field(self) -> None:
        joins = [MonthlyCount(year=2026, month=3, count=3)]
        resp = VolunteerAnalyticsResponse(**self._make_response(monthly_joins=joins))
        assert len(resp.monthly_joins) == 1
        assert resp.monthly_joins[0].count == 3

    def test_generated_at_is_date(self) -> None:
        resp = VolunteerAnalyticsResponse(**self._make_response())
        assert isinstance(resp.generated_at, date)
