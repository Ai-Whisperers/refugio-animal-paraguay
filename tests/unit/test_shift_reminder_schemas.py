"""Unit tests for shift reminder API schemas (RAP-184).

Tests ShiftReminderResponse schema validation.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from src.api.shift_reminders import ShiftReminderResponse


class TestShiftReminderResponse:
    def test_valid_response(self) -> None:
        now = datetime.now(UTC)
        resp = ShiftReminderResponse(sent_count=5, hours_ahead=24, sent_at=now)
        assert resp.sent_count == 5
        assert resp.hours_ahead == 24
        assert resp.sent_at == now

    def test_zero_sent_count(self) -> None:
        resp = ShiftReminderResponse(sent_count=0, hours_ahead=24, sent_at=datetime.now(UTC))
        assert resp.sent_count == 0

    def test_missing_sent_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftReminderResponse(hours_ahead=24, sent_at=datetime.now(UTC))  # type: ignore[call-arg]

    def test_missing_hours_ahead_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftReminderResponse(sent_count=0, sent_at=datetime.now(UTC))  # type: ignore[call-arg]

    def test_missing_sent_at_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftReminderResponse(sent_count=0, hours_ahead=24)  # type: ignore[call-arg]

    def test_large_sent_count(self) -> None:
        resp = ShiftReminderResponse(sent_count=500, hours_ahead=168, sent_at=datetime.now(UTC))
        assert resp.sent_count == 500
        assert resp.hours_ahead == 168
