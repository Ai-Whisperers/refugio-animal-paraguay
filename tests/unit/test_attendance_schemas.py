"""Unit tests for attendance tracking API schemas (RAP-183).

Tests AttendanceUpdateRequest and ShiftSignupListResponse schemas.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.api.shifts import AttendanceUpdateRequest, ShiftSignupListResponse, ShiftSignupResponse


class TestAttendanceUpdateRequest:
    def test_attended_true(self) -> None:
        req = AttendanceUpdateRequest(attended=True)
        assert req.attended is True

    def test_attended_false_no_show(self) -> None:
        req = AttendanceUpdateRequest(attended=False)
        assert req.attended is False

    def test_attended_none_clears(self) -> None:
        req = AttendanceUpdateRequest(attended=None)
        assert req.attended is None

    def test_attended_with_note(self) -> None:
        req = AttendanceUpdateRequest(attended=True, notes="Arrived on time")
        assert req.notes == "Arrived on time"

    def test_notes_optional(self) -> None:
        req = AttendanceUpdateRequest(attended=True)
        assert req.notes is None

    def test_notes_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            AttendanceUpdateRequest(attended=True, notes="x" * 501)

    def test_notes_at_max_length_is_valid(self) -> None:
        req = AttendanceUpdateRequest(attended=False, notes="x" * 500)
        assert len(req.notes) == 500  # type: ignore[arg-type]

    def test_missing_attended_raises(self) -> None:
        with pytest.raises(ValidationError):
            AttendanceUpdateRequest()  # type: ignore[call-arg]


class TestShiftSignupListResponse:
    def test_empty_list(self) -> None:
        resp = ShiftSignupListResponse(items=[], total=0)
        assert resp.items == []
        assert resp.total == 0

    def test_list_with_signups(self) -> None:
        now = datetime.now(UTC)
        signup = ShiftSignupResponse(
            id=uuid4(),
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=False,
            attended=None,
            signed_up_at=now,
        )
        resp = ShiftSignupListResponse(items=[signup], total=1)
        assert len(resp.items) == 1
        assert resp.total == 1

    def test_total_matches_items_count(self) -> None:
        now = datetime.now(UTC)
        signups = [
            ShiftSignupResponse(
                id=uuid4(),
                shift_id=uuid4(),
                volunteer_id=uuid4(),
                confirmed=i % 2 == 0,
                attended=True if i == 0 else None,
                signed_up_at=now,
            )
            for i in range(5)
        ]
        resp = ShiftSignupListResponse(items=signups, total=5)
        assert resp.total == 5
        assert len(resp.items) == 5
