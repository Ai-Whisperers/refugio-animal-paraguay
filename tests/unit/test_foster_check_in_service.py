"""Unit tests for foster check-in service (RAP-192).

Tests the service layer logic using mocked AsyncSession to avoid database
access.  Focuses on state-machine transitions, auto-scheduling, and
overdue-marking logic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.foster_check_in import (
    DEFAULT_INTERVAL_DAYS,
    CheckInStatus,
    CheckInType,
    FosterCheckIn,
)
from src.services.foster_check_in_service import (
    cancel_check_in,
    complete_check_in,
    get_check_in_or_raise,
    mark_overdue_as_missed,
    record_reminder_sent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PLACEMENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CHECK_IN_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _make_check_in(
    *,
    status: str = CheckInStatus.PENDING,
    interval_days: int = DEFAULT_INTERVAL_DAYS,
    scheduled_at: datetime | None = None,
) -> Any:
    """Build a minimal FosterCheckIn-like namespace for unit testing."""
    if scheduled_at is None:
        scheduled_at = datetime.now(UTC) + timedelta(days=1)
    ci = MagicMock(spec=FosterCheckIn)
    ci.id = CHECK_IN_ID
    ci.foster_placement_id = PLACEMENT_ID
    ci.status = status
    ci.scheduled_at = scheduled_at
    ci.completed_at = None
    ci.notes = None
    ci.cancellation_reason = None
    ci.interval_days = interval_days
    ci.reminder_sent_at = None
    ci.created_by = None
    ci.created_at = datetime.now(UTC)
    ci.updated_at = datetime.now(UTC)
    ci.check_in_type = CheckInType.SCHEDULED
    return ci


def _make_session_with_check_in(check_in: Any) -> AsyncMock:
    """Return a mock AsyncSession that returns check_in from scalar_one_or_none."""
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = check_in
    session.execute.return_value = result_mock
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


# ---------------------------------------------------------------------------
# get_check_in_or_raise
# ---------------------------------------------------------------------------


class TestGetCheckInOrRaise:
    @pytest.mark.asyncio
    async def test_returns_check_in_when_found(self) -> None:
        check_in = _make_check_in()
        session = _make_session_with_check_in(check_in)

        result = await get_check_in_or_raise(session, CHECK_IN_ID)

        assert result is check_in

    @pytest.mark.asyncio
    async def test_raises_value_error_when_not_found(self) -> None:
        session = _make_session_with_check_in(None)

        with pytest.raises(ValueError, match=str(CHECK_IN_ID)):
            await get_check_in_or_raise(session, CHECK_IN_ID)


# ---------------------------------------------------------------------------
# complete_check_in
# ---------------------------------------------------------------------------


class TestCompleteCheckIn:
    @pytest.mark.asyncio
    async def test_marks_pending_check_in_as_completed(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING)
        session = _make_session_with_check_in(check_in)

        await complete_check_in(session, CHECK_IN_ID, notes="All good")

        assert check_in.status == CheckInStatus.COMPLETED
        assert check_in.notes == "All good"
        assert check_in.completed_at is not None
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_auto_schedules_next_check_in_when_enabled(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING, interval_days=7)
        session = _make_session_with_check_in(check_in)

        await complete_check_in(session, CHECK_IN_ID, auto_schedule_next=True)

        # session.add should have been called with the new check-in
        session.add.assert_called_once()
        new_ci = session.add.call_args[0][0]
        assert isinstance(new_ci, FosterCheckIn)
        assert new_ci.status == CheckInStatus.PENDING.value
        assert new_ci.interval_days == 7

    @pytest.mark.asyncio
    async def test_does_not_auto_schedule_when_disabled(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING, interval_days=7)
        session = _make_session_with_check_in(check_in)

        await complete_check_in(session, CHECK_IN_ID, auto_schedule_next=False)

        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_check_in_already_completed(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.COMPLETED)
        session = _make_session_with_check_in(check_in)

        with pytest.raises(ValueError, match="completed"):
            await complete_check_in(session, CHECK_IN_ID)

    @pytest.mark.asyncio
    async def test_raises_when_check_in_cancelled(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.CANCELLED)
        session = _make_session_with_check_in(check_in)

        with pytest.raises(ValueError, match="cancelled"):
            await complete_check_in(session, CHECK_IN_ID)


# ---------------------------------------------------------------------------
# cancel_check_in
# ---------------------------------------------------------------------------


class TestCancelCheckIn:
    @pytest.mark.asyncio
    async def test_cancels_pending_check_in(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING)
        session = _make_session_with_check_in(check_in)

        await cancel_check_in(session, CHECK_IN_ID, reason="Foster family unavailable")

        assert check_in.status == CheckInStatus.CANCELLED
        assert check_in.cancellation_reason == "Foster family unavailable"
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_without_reason_is_allowed(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING)
        session = _make_session_with_check_in(check_in)

        await cancel_check_in(session, CHECK_IN_ID, reason=None)

        assert check_in.status == CheckInStatus.CANCELLED
        assert check_in.cancellation_reason is None

    @pytest.mark.asyncio
    async def test_raises_when_check_in_not_pending(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.COMPLETED)
        session = _make_session_with_check_in(check_in)

        with pytest.raises(ValueError, match="completed"):
            await cancel_check_in(session, CHECK_IN_ID)


# ---------------------------------------------------------------------------
# record_reminder_sent
# ---------------------------------------------------------------------------


class TestRecordReminderSent:
    @pytest.mark.asyncio
    async def test_updates_reminder_sent_at(self) -> None:
        check_in = _make_check_in(status=CheckInStatus.PENDING)
        session = _make_session_with_check_in(check_in)

        before = datetime.now(UTC)
        await record_reminder_sent(session, CHECK_IN_ID)
        after = datetime.now(UTC)

        assert check_in.reminder_sent_at is not None
        assert before <= check_in.reminder_sent_at <= after
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_when_check_in_not_found(self) -> None:
        session = _make_session_with_check_in(None)

        with pytest.raises(ValueError, match=str(CHECK_IN_ID)):
            await record_reminder_sent(session, CHECK_IN_ID)


# ---------------------------------------------------------------------------
# mark_overdue_as_missed
# ---------------------------------------------------------------------------


class TestMarkOverdueAsMissed:
    @pytest.mark.asyncio
    async def test_marks_overdue_check_ins_as_missed(self) -> None:
        overdue_1 = _make_check_in(
            status=CheckInStatus.PENDING,
            scheduled_at=datetime.now(UTC) - timedelta(days=2),
        )
        overdue_2 = _make_check_in(
            status=CheckInStatus.PENDING,
            scheduled_at=datetime.now(UTC) - timedelta(hours=3),
        )

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [overdue_1, overdue_2]
        session.execute.return_value = result_mock
        session.commit = AsyncMock()

        count = await mark_overdue_as_missed(session)

        assert count == 2
        assert overdue_1.status == CheckInStatus.MISSED
        assert overdue_2.status == CheckInStatus.MISSED
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_overdue(self) -> None:
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock
        session.commit = AsyncMock()

        count = await mark_overdue_as_missed(session)

        assert count == 0
        session.commit.assert_not_awaited()
