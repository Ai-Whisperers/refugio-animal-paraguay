"""Unit tests for volunteer hours logging API (RAP-195).

Tests schemas, validators, and helper functions without a live database.
"""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.api.volunteer_hours import (
    HoursLogCreateRequest,
    HoursLogListResponse,
    HoursLogResponse,
    HoursSummaryResponse,
    _to_response,
)
from src.db.models.volunteer_hours import (
    HOURS_MAX_DURATION,
    HOURS_MIN_DURATION,
    VALID_HOUR_CATEGORIES,
    HoursCategory,
    VolunteerHoursLog,
)

# ---------------------------------------------------------------------------
# HoursCategory enum
# ---------------------------------------------------------------------------


class TestHoursCategory:
    def test_values_are_strings(self) -> None:
        assert HoursCategory.ANIMAL_CARE == "animal_care"
        assert HoursCategory.CLEANING == "cleaning"
        assert HoursCategory.TRANSPORT == "transport"

    def test_all_categories_in_valid_set(self) -> None:
        for category in HoursCategory:
            assert category.value in VALID_HOUR_CATEGORIES

    def test_valid_set_covers_all_enum_members(self) -> None:
        assert len(VALID_HOUR_CATEGORIES) == len(HoursCategory)

    def test_duration_constants(self) -> None:
        assert HOURS_MIN_DURATION == 0.25
        assert HOURS_MAX_DURATION == 24.0


# ---------------------------------------------------------------------------
# HoursLogCreateRequest schema validation
# ---------------------------------------------------------------------------


class TestHoursLogCreateRequestValidation:
    def _valid_payload(self, **overrides) -> dict:
        payload = {
            "activity_date": date.today(),
            "duration_hours": 2.0,
            "category": "animal_care",
            "description": None,
            "shift_id": None,
        }
        payload.update(overrides)
        return payload

    def test_valid_minimal_request(self) -> None:
        req = HoursLogCreateRequest(**self._valid_payload())
        assert req.duration_hours == 2.0
        assert req.category == "animal_care"

    def test_valid_with_description_and_shift(self) -> None:
        shift_id = uuid4()
        req = HoursLogCreateRequest(
            **self._valid_payload(
                description="Fed and cleaned kennels",
                shift_id=shift_id,
            )
        )
        assert req.description == "Fed and cleaned kennels"
        assert req.shift_id == shift_id

    # --- activity_date validator ---

    def test_today_is_valid(self) -> None:
        req = HoursLogCreateRequest(**self._valid_payload(activity_date=date.today()))
        assert req.activity_date == date.today()

    def test_past_date_is_valid(self) -> None:
        past = date.today() - timedelta(days=30)
        req = HoursLogCreateRequest(**self._valid_payload(activity_date=past))
        assert req.activity_date == past

    def test_future_date_raises(self) -> None:
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            HoursLogCreateRequest(**self._valid_payload(activity_date=future))
        assert "future" in str(exc_info.value).lower()

    # --- duration_hours validator ---

    def test_minimum_duration_accepted(self) -> None:
        req = HoursLogCreateRequest(**self._valid_payload(duration_hours=HOURS_MIN_DURATION))
        assert req.duration_hours == HOURS_MIN_DURATION

    def test_maximum_duration_accepted(self) -> None:
        req = HoursLogCreateRequest(**self._valid_payload(duration_hours=HOURS_MAX_DURATION))
        assert req.duration_hours == HOURS_MAX_DURATION

    def test_duration_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(duration_hours=0.1))

    def test_duration_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(duration_hours=25.0))

    def test_zero_duration_raises(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(duration_hours=0.0))

    # --- category validator ---

    def test_all_valid_categories_accepted(self) -> None:
        for cat in VALID_HOUR_CATEGORIES:
            req = HoursLogCreateRequest(**self._valid_payload(category=cat))
            assert req.category == cat

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            HoursLogCreateRequest(**self._valid_payload(category="flying"))
        assert "invalid category" in str(exc_info.value).lower()

    def test_empty_category_raises(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(category=""))

    def test_category_case_sensitive(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(category="Animal_Care"))

    # --- description field ---

    def test_description_max_length_accepted(self) -> None:
        long_desc = "x" * 1000
        req = HoursLogCreateRequest(**self._valid_payload(description=long_desc))
        assert len(req.description) == 1000

    def test_description_exceeds_max_length_raises(self) -> None:
        with pytest.raises(ValidationError):
            HoursLogCreateRequest(**self._valid_payload(description="x" * 1001))


# ---------------------------------------------------------------------------
# HoursLogResponse schema
# ---------------------------------------------------------------------------


class TestHoursLogResponse:
    def _make_response(self, **overrides) -> dict:
        now = datetime.now(UTC)
        data = {
            "id": uuid4(),
            "volunteer_id": uuid4(),
            "activity_date": date.today(),
            "duration_hours": 3.0,
            "category": "transport",
            "description": None,
            "shift_id": None,
            "approved": False,
            "approved_by": None,
            "approved_at": None,
            "created_at": now,
            "updated_at": now,
        }
        data.update(overrides)
        return data

    def test_unapproved_response(self) -> None:
        resp = HoursLogResponse(**self._make_response())
        assert resp.approved is False
        assert resp.approved_by is None
        assert resp.approved_at is None

    def test_approved_response(self) -> None:
        approver_id = uuid4()
        approved_at = datetime.now(UTC)
        resp = HoursLogResponse(
            **self._make_response(
                approved=True,
                approved_by=approver_id,
                approved_at=approved_at,
            )
        )
        assert resp.approved is True
        assert resp.approved_by == approver_id
        assert resp.approved_at == approved_at


# ---------------------------------------------------------------------------
# HoursSummaryResponse schema
# ---------------------------------------------------------------------------


class TestHoursSummaryResponse:
    def test_summary_fields(self) -> None:
        vid = uuid4()
        summary = HoursSummaryResponse(
            volunteer_id=vid,
            total_hours=10.5,
            approved_hours=7.0,
            pending_hours=3.5,
            hours_by_category={"animal_care": 6.0, "transport": 4.5},
        )
        assert summary.total_hours == 10.5
        assert summary.pending_hours == 3.5
        assert summary.hours_by_category["transport"] == 4.5


# ---------------------------------------------------------------------------
# HoursLogListResponse schema
# ---------------------------------------------------------------------------


class TestHoursLogListResponse:
    def test_empty_list(self) -> None:
        resp = HoursLogListResponse(items=[], total=0, page=1, page_size=20)
        assert resp.items == []
        assert resp.total == 0


# ---------------------------------------------------------------------------
# _to_response helper
# ---------------------------------------------------------------------------


class TestToResponseHelper:
    def _make_log(self, **overrides) -> MagicMock:
        """Build a MagicMock mimicking a VolunteerHoursLog ORM row."""
        now = datetime.now(UTC)
        log = MagicMock(spec=VolunteerHoursLog)
        defaults = {
            "id": uuid4(),
            "volunteer_id": uuid4(),
            "activity_date": date.today(),
            "duration_hours": 1.5,
            "category": "event",
            "description": "Adoption fair booth",
            "shift_id": None,
            "approved": False,
            "approved_by": None,
            "approved_at": None,
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(log, k, v)
        return log

    def test_converts_orm_to_response(self) -> None:
        log = self._make_log()
        resp = _to_response(log)
        assert resp.id == log.id
        assert resp.volunteer_id == log.volunteer_id
        assert resp.duration_hours == float(log.duration_hours)
        assert resp.category == log.category
        assert resp.approved is False

    def test_float_conversion_for_numeric_duration(self) -> None:
        log = self._make_log(duration_hours=2.5)
        resp = _to_response(log)
        assert isinstance(resp.duration_hours, float)
        assert resp.duration_hours == 2.5

    def test_approved_fields_preserved(self) -> None:
        approver_id = uuid4()
        approved_at = datetime.now(UTC)
        log = self._make_log(
            approved=True,
            approved_by=approver_id,
            approved_at=approved_at,
        )
        resp = _to_response(log)
        assert resp.approved is True
        assert resp.approved_by == approver_id
        assert resp.approved_at == approved_at
