"""Unit tests for the follow-up automation service.

Tests batch processing, reminders, skip, alerts, and completion stats.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.followup_automation_service import (
    ALERT_WELFARE_THRESHOLD,
    DEFAULT_BATCH_SIZE,
    REMINDER_GRACE_DAYS,
    STATUS_SKIPPED,
    FollowUpAutomationError,
    FollowUpNotFoundError,
    InvalidFollowUpStateError,
    check_for_alerts,
    get_followup_completion_stats,
    process_due_followups,
    send_followup_reminders,
    skip_followup,
)

# -- Error classes --


class TestErrorClasses:
    """Verify error hierarchy."""

    def test_base_error(self) -> None:
        err = FollowUpAutomationError("base")
        assert isinstance(err, Exception)

    def test_not_found_inherits(self) -> None:
        err = FollowUpNotFoundError("x")
        assert isinstance(err, FollowUpAutomationError)

    def test_invalid_state_inherits(self) -> None:
        err = InvalidFollowUpStateError("x")
        assert isinstance(err, FollowUpAutomationError)


# -- Constants --


class TestConstants:
    """Verify module constants."""

    def test_reminder_grace_days(self) -> None:
        assert REMINDER_GRACE_DAYS == 3

    def test_alert_threshold(self) -> None:
        assert ALERT_WELFARE_THRESHOLD == 2

    def test_batch_size(self) -> None:
        assert DEFAULT_BATCH_SIZE == 100

    def test_skipped_status(self) -> None:
        assert STATUS_SKIPPED == "skipped"


# -- process_due_followups --


class TestProcessDueFollowups:
    """Tests for processing due follow-ups."""

    @pytest.mark.asyncio
    async def test_processes_pending_followups(self) -> None:
        fu1 = MagicMock()
        fu1.status = "pending"
        fu1.survey_sent_at = None
        fu2 = MagicMock()
        fu2.status = "pending"
        fu2.survey_sent_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fu1, fu2]
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await process_due_followups(db, batch_size=50)

        assert result["processed_count"] == 2
        assert fu1.status == "sent"
        assert fu2.status == "sent"
        assert fu1.survey_sent_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_none_due(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await process_due_followups(db)

        assert result["processed_count"] == 0
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_respects_batch_size(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await process_due_followups(db, batch_size=10)

        assert result["batch_size"] == 10


# -- send_followup_reminders --


class TestSendFollowupReminders:
    """Tests for sending reminders."""

    @pytest.mark.asyncio
    async def test_marks_overdue_followups(self) -> None:
        fu = MagicMock()
        fu.status = "sent"
        fu.survey_sent_at = datetime.now(UTC) - timedelta(days=5)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fu]
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await send_followup_reminders(db)

        assert result["reminder_count"] == 1
        assert fu.status == "overdue"
        assert result["grace_days"] == REMINDER_GRACE_DAYS
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_overdue(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await send_followup_reminders(db)

        assert result["reminder_count"] == 0
        db.flush.assert_not_awaited()


# -- skip_followup --


class TestSkipFollowup:
    """Tests for skipping a follow-up."""

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(FollowUpNotFoundError):
            await skip_followup(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_already_completed(self) -> None:
        fu = MagicMock()
        fu.status = "completed"

        db = AsyncMock()
        db.get.return_value = fu

        with pytest.raises(InvalidFollowUpStateError, match="terminal"):
            await skip_followup(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_already_skipped(self) -> None:
        fu = MagicMock()
        fu.status = "skipped"

        db = AsyncMock()
        db.get.return_value = fu

        with pytest.raises(InvalidFollowUpStateError, match="terminal"):
            await skip_followup(db, uuid4())

    @pytest.mark.asyncio
    async def test_skips_pending_followup(self) -> None:
        fu_id = uuid4()
        fu = MagicMock()
        fu.id = fu_id
        fu.status = "pending"

        db = AsyncMock()
        db.get.return_value = fu

        result = await skip_followup(db, fu_id)

        assert result["status"] == STATUS_SKIPPED
        assert result["follow_up_id"] == fu_id
        assert fu.status == STATUS_SKIPPED
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_sent_followup(self) -> None:
        fu = MagicMock()
        fu.id = uuid4()
        fu.status = "sent"

        db = AsyncMock()
        db.get.return_value = fu

        result = await skip_followup(db, fu.id)

        assert result["status"] == STATUS_SKIPPED
        assert fu.status == STATUS_SKIPPED

    @pytest.mark.asyncio
    async def test_skips_overdue_followup(self) -> None:
        fu = MagicMock()
        fu.id = uuid4()
        fu.status = "overdue"

        db = AsyncMock()
        db.get.return_value = fu

        result = await skip_followup(db, fu.id)

        assert result["status"] == STATUS_SKIPPED


# -- check_for_alerts --


class TestCheckForAlerts:
    """Tests for alert detection."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_alerts(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await check_for_alerts(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_flags_low_welfare_score(self) -> None:
        fu = MagicMock()
        fu.id = uuid4()
        fu.adoption_request_id = uuid4()
        fu.welfare_score = 1
        fu.satisfaction_score = 2
        fu.issues_noted = None
        fu.day_offset = 30
        fu.survey_completed_at = datetime.now(UTC)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fu]
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await check_for_alerts(db)

        assert len(result) == 1
        assert result[0]["welfare_score"] == 1

    @pytest.mark.asyncio
    async def test_flags_reported_issues(self) -> None:
        fu = MagicMock()
        fu.id = uuid4()
        fu.adoption_request_id = uuid4()
        fu.welfare_score = 4
        fu.satisfaction_score = 4
        fu.issues_noted = "Limping on back leg"
        fu.day_offset = 7
        fu.survey_completed_at = datetime.now(UTC)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fu]
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await check_for_alerts(db)

        assert len(result) == 1
        assert result[0]["issues_noted"] == "Limping on back leg"


# -- get_followup_completion_stats --


class TestGetFollowupCompletionStats:
    """Tests for completion statistics."""

    @pytest.mark.asyncio
    async def test_returns_global_stats(self) -> None:
        mock_row = MagicMock()
        mock_row.total = 20
        mock_row.completed = 12
        mock_row.overdue = 3
        mock_row.pending = 3
        mock_row.sent = 2

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db.execute.return_value = mock_result

        result = await get_followup_completion_stats(db)

        assert result["total_followups"] == 20
        assert result["completed"] == 12
        assert result["completion_pct"] == 60.0
        assert result["adoption_request_id"] is None

    @pytest.mark.asyncio
    async def test_returns_stats_for_adoption(self) -> None:
        adoption_id = uuid4()

        mock_row = MagicMock()
        mock_row.total = 4
        mock_row.completed = 2
        mock_row.overdue = 1
        mock_row.pending = 1
        mock_row.sent = 0

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db.execute.return_value = mock_result

        result = await get_followup_completion_stats(db, adoption_request_id=adoption_id)

        assert result["total_followups"] == 4
        assert result["completion_pct"] == 50.0
        assert result["adoption_request_id"] == adoption_id

    @pytest.mark.asyncio
    async def test_returns_zero_pct_when_no_followups(self) -> None:
        mock_row = MagicMock()
        mock_row.total = 0
        mock_row.completed = 0
        mock_row.overdue = 0
        mock_row.pending = 0
        mock_row.sent = 0

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db.execute.return_value = mock_result

        result = await get_followup_completion_stats(db)

        assert result["completion_pct"] == 0.0
