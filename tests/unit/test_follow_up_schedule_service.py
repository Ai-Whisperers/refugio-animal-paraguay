"""Unit tests for follow-up schedule service (RAP-261, EPIC-53)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.db.models.follow_up import FollowUpStatus
from src.services.follow_up_schedule_service import (
    DEFAULT_DUE_WINDOW_DAYS,
    FollowUpScheduleItem,
    MarkOverdueResult,
    _to_schedule_item,
    get_due_follow_ups,
    get_overdue_follow_ups,
    get_schedule_for_adoption,
    mark_overdue_follow_ups,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_follow_up(status="pending", days_from_now=5, **overrides):
    """Create a mock FollowUp object."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "adoption_request_id": uuid4(),
        "scheduled_date": now + timedelta(days=days_from_now),
        "day_offset": 30,
        "status": status,
        "welfare_score": None,
        "satisfaction_score": None,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_db_with_scalars(items):
    """Create async DB mock that returns the given items from execute().scalars()."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = iter(items)
    db.execute = AsyncMock(return_value=mock_result)
    return db


def _make_db_with_update(row_count=3):
    """Create async DB mock that returns rows from an update().returning()."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [MagicMock()] * row_count
    db.execute = AsyncMock(return_value=mock_result)
    return db


# ---------------------------------------------------------------------------
# _to_schedule_item
# ---------------------------------------------------------------------------


class TestToScheduleItem:
    def test_due_in_future_is_not_overdue(self):
        fu = _make_follow_up(status="pending", days_from_now=5)
        item = _to_schedule_item(fu)
        assert not item.is_overdue
        assert item.days_until_due >= 4

    def test_past_due_pending_is_overdue(self):
        fu = _make_follow_up(status="pending", days_from_now=-3)
        item = _to_schedule_item(fu)
        assert item.is_overdue
        assert item.days_until_due < 0

    def test_completed_past_date_is_not_overdue(self):
        fu = _make_follow_up(status="completed", days_from_now=-10)
        item = _to_schedule_item(fu)
        assert not item.is_overdue

    def test_status_is_preserved(self):
        fu = _make_follow_up(status="overdue", days_from_now=-1)
        item = _to_schedule_item(fu)
        assert item.status == "overdue"

    def test_fields_are_correct(self):
        adoption_request_id = uuid4()
        fu_id = uuid4()
        fu = _make_follow_up(
            id=fu_id,
            adoption_request_id=adoption_request_id,
            day_offset=90,
            days_from_now=2,
        )
        item = _to_schedule_item(fu)
        assert item.id == fu_id
        assert item.adoption_request_id == adoption_request_id
        assert item.day_offset == 90
        assert isinstance(item, FollowUpScheduleItem)


# ---------------------------------------------------------------------------
# get_due_follow_ups
# ---------------------------------------------------------------------------


class TestGetDueFollowUps:
    @pytest.mark.asyncio
    async def test_returns_items(self):
        fu1 = _make_follow_up(days_from_now=2)
        fu2 = _make_follow_up(days_from_now=5)
        db = _make_db_with_scalars([fu1, fu2])

        result = await get_due_follow_ups(db)

        assert len(result) == 2
        assert all(isinstance(item, FollowUpScheduleItem) for item in result)

    @pytest.mark.asyncio
    async def test_empty_database(self):
        db = _make_db_with_scalars([])

        result = await get_due_follow_ups(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_uses_default_window(self):
        db = _make_db_with_scalars([])

        await get_due_follow_ups(db)

        db.execute.assert_awaited_once()
        # Verify the call was made (default window should be DEFAULT_DUE_WINDOW_DAYS)
        assert DEFAULT_DUE_WINDOW_DAYS == 7


# ---------------------------------------------------------------------------
# get_overdue_follow_ups
# ---------------------------------------------------------------------------


class TestGetOverdueFollowUps:
    @pytest.mark.asyncio
    async def test_returns_overdue_items(self):
        fu = _make_follow_up(status="pending", days_from_now=-5)
        db = _make_db_with_scalars([fu])

        result = await get_overdue_follow_ups(db)

        assert len(result) == 1
        assert result[0].is_overdue

    @pytest.mark.asyncio
    async def test_empty_when_none_overdue(self):
        db = _make_db_with_scalars([])

        result = await get_overdue_follow_ups(db)

        assert result == []


# ---------------------------------------------------------------------------
# get_schedule_for_adoption
# ---------------------------------------------------------------------------


class TestGetScheduleForAdoption:
    @pytest.mark.asyncio
    async def test_returns_items_for_adoption(self):
        adoption_id = uuid4()
        fu1 = _make_follow_up(adoption_request_id=adoption_id, day_offset=7)
        fu2 = _make_follow_up(adoption_request_id=adoption_id, day_offset=30)
        fu3 = _make_follow_up(adoption_request_id=adoption_id, day_offset=90)
        db = _make_db_with_scalars([fu1, fu2, fu3])

        result = await get_schedule_for_adoption(db, adoption_id)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_when_no_schedule(self):
        db = _make_db_with_scalars([])

        result = await get_schedule_for_adoption(db, uuid4())

        assert result == []


# ---------------------------------------------------------------------------
# mark_overdue_follow_ups
# ---------------------------------------------------------------------------


class TestMarkOverdueFollowUps:
    @pytest.mark.asyncio
    async def test_returns_marked_count(self):
        db = _make_db_with_update(row_count=5)

        result = await mark_overdue_follow_ups(db)

        assert isinstance(result, MarkOverdueResult)
        assert result.marked_count == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_none_overdue(self):
        db = _make_db_with_update(row_count=0)

        result = await mark_overdue_follow_ups(db)

        assert result.marked_count == 0

    @pytest.mark.asyncio
    async def test_run_at_is_iso8601(self):
        db = _make_db_with_update(row_count=0)

        result = await mark_overdue_follow_ups(db)

        datetime.fromisoformat(result.run_at)

    @pytest.mark.asyncio
    async def test_executes_update_statement(self):
        db = _make_db_with_update(row_count=2)

        await mark_overdue_follow_ups(db)

        db.execute.assert_awaited_once()
