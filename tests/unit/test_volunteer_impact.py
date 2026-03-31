"""Unit tests for volunteer impact metrics API (RAP-199).

Tests helpers and schema validation without a live database.
"""

from datetime import date
from unittest.mock import MagicMock

from src.api.volunteer_impact import (
    CATEGORY_LABELS,
    IMPACT_DEFAULT_WINDOW_DAYS,
    IMPACT_MAX_WINDOW_DAYS,
    CategoryBreakdown,
    ImpactMetricsResponse,
    TopContributor,
    _category_breakdown,
)
from src.db.models.volunteer_hours import HoursCategory, VolunteerHoursLog

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestImpactConstants:
    def test_default_window_positive(self) -> None:
        assert IMPACT_DEFAULT_WINDOW_DAYS > 0

    def test_max_window_gte_default(self) -> None:
        assert IMPACT_MAX_WINDOW_DAYS >= IMPACT_DEFAULT_WINDOW_DAYS

    def test_category_labels_covers_all_categories(self) -> None:
        for cat in HoursCategory:
            assert cat in CATEGORY_LABELS, f"Missing label for {cat}"


# ---------------------------------------------------------------------------
# _category_breakdown helper
# ---------------------------------------------------------------------------


def _make_log(category: str, hours: float, approved: bool = True) -> MagicMock:
    log = MagicMock(spec=VolunteerHoursLog)
    log.category = category
    log.duration_hours = hours
    log.approved = approved
    return log


class TestCategoryBreakdown:
    def test_empty_logs(self) -> None:
        result = _category_breakdown([])
        assert result == []

    def test_single_approved_log(self) -> None:
        logs = [_make_log(HoursCategory.ANIMAL_CARE, 3.0)]
        result = _category_breakdown(logs)
        assert len(result) == 1
        assert result[0].category == HoursCategory.ANIMAL_CARE
        assert result[0].hours == 3.0

    def test_unapproved_excluded_by_default(self) -> None:
        logs = [
            _make_log(HoursCategory.ANIMAL_CARE, 3.0, approved=True),
            _make_log(HoursCategory.EVENT, 2.0, approved=False),
        ]
        result = _category_breakdown(logs)
        categories = {r.category for r in result}
        assert HoursCategory.EVENT not in categories

    def test_unapproved_included_when_flag_false(self) -> None:
        logs = [
            _make_log(HoursCategory.ANIMAL_CARE, 3.0, approved=True),
            _make_log(HoursCategory.EVENT, 2.0, approved=False),
        ]
        result = _category_breakdown(logs, approved_only=False)
        categories = {r.category for r in result}
        assert HoursCategory.EVENT in categories

    def test_aggregated_across_same_category(self) -> None:
        logs = [
            _make_log(HoursCategory.CLEANING, 1.5),
            _make_log(HoursCategory.CLEANING, 2.5),
        ]
        result = _category_breakdown(logs)
        assert len(result) == 1
        assert result[0].hours == 4.0

    def test_sorted_by_hours_descending(self) -> None:
        logs = [
            _make_log(HoursCategory.CLEANING, 1.0),
            _make_log(HoursCategory.ANIMAL_CARE, 5.0),
            _make_log(HoursCategory.EVENT, 3.0),
        ]
        result = _category_breakdown(logs)
        hours = [r.hours for r in result]
        assert hours == sorted(hours, reverse=True)

    def test_returns_category_breakdown_objects(self) -> None:
        logs = [_make_log(HoursCategory.ADMIN, 1.0)]
        result = _category_breakdown(logs)
        assert isinstance(result[0], CategoryBreakdown)

    def test_label_populated_from_category_labels(self) -> None:
        logs = [_make_log(HoursCategory.ANIMAL_CARE, 1.0)]
        result = _category_breakdown(logs)
        assert result[0].label == CATEGORY_LABELS[HoursCategory.ANIMAL_CARE]

    def test_hours_rounded_to_two_decimals(self) -> None:
        logs = [_make_log(HoursCategory.TRANSPORT, 1.123456)]
        result = _category_breakdown(logs)
        assert result[0].hours == round(1.123456, 2)

    def test_zero_hour_entries_excluded(self) -> None:
        logs = [
            _make_log(HoursCategory.ANIMAL_CARE, 0.0),
            _make_log(HoursCategory.EVENT, 2.0),
        ]
        result = _category_breakdown(logs)
        categories = {r.category for r in result}
        assert HoursCategory.ANIMAL_CARE not in categories


# ---------------------------------------------------------------------------
# ImpactMetricsResponse schema
# ---------------------------------------------------------------------------


class TestImpactMetricsResponse:
    def _make_response(self, **overrides) -> dict:
        today = date.today()
        data = {
            "generated_at": today,
            "total_approved_volunteers": 15,
            "total_volunteers_with_hours": 10,
            "total_hours_contributed": 500.0,
            "window_days": 30,
            "window_start": today,
            "hours_logged_in_window": 45.0,
            "hours_pending_approval": 5.0,
            "hours_by_category": [],
            "animal_care_hours_total": 200.0,
            "top_contributors": [],
        }
        data.update(overrides)
        return data

    def test_valid_response(self) -> None:
        resp = ImpactMetricsResponse(**self._make_response())
        assert resp.total_approved_volunteers == 15
        assert resp.total_hours_contributed == 500.0
        assert resp.window_days == 30

    def test_zero_state(self) -> None:
        resp = ImpactMetricsResponse(
            **self._make_response(
                total_approved_volunteers=0,
                total_volunteers_with_hours=0,
                total_hours_contributed=0.0,
                hours_logged_in_window=0.0,
                hours_pending_approval=0.0,
                animal_care_hours_total=0.0,
            )
        )
        assert resp.total_approved_volunteers == 0
        assert resp.animal_care_hours_total == 0.0

    def test_with_category_breakdown(self) -> None:
        cats = [CategoryBreakdown(category="animal_care", label="Cuidado animal", hours=10.0)]
        resp = ImpactMetricsResponse(**self._make_response(hours_by_category=cats))
        assert len(resp.hours_by_category) == 1
        assert resp.hours_by_category[0].hours == 10.0

    def test_with_top_contributors(self) -> None:
        import uuid

        contributors = [TopContributor(volunteer_id=str(uuid.uuid4()), total_hours_logged=100.0)]
        resp = ImpactMetricsResponse(**self._make_response(top_contributors=contributors))
        assert len(resp.top_contributors) == 1

    def test_generated_at_is_date(self) -> None:
        resp = ImpactMetricsResponse(**self._make_response())
        assert isinstance(resp.generated_at, date)

    def test_window_start_is_date(self) -> None:
        resp = ImpactMetricsResponse(**self._make_response())
        assert isinstance(resp.window_start, date)
