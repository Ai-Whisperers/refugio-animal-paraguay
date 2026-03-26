"""Unit tests for the post-adoption follow-up service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.follow_up import (
    FOLLOW_UP_SCHEDULE_DAYS,
    FollowUp,
    FollowUpStatus,
    ReturnReasonCode,
)
from src.services.follow_up_service import (
    record_return,
    schedule_follow_ups,
    submit_survey,
)


class TestFollowUpModels:
    """Tests for the FollowUp model enums and constants."""

    def test_follow_up_schedule_has_four_intervals(self) -> None:
        assert len(FOLLOW_UP_SCHEDULE_DAYS) == 4

    def test_schedule_days_are_7_30_90_365(self) -> None:
        assert FOLLOW_UP_SCHEDULE_DAYS == (7, 30, 90, 365)

    def test_follow_up_status_values(self) -> None:
        assert FollowUpStatus.PENDING == "pending"
        assert FollowUpStatus.SENT == "sent"
        assert FollowUpStatus.COMPLETED == "completed"
        assert FollowUpStatus.OVERDUE == "overdue"
        assert FollowUpStatus.CANCELLED == "cancelled"

    def test_return_reason_code_values(self) -> None:
        assert ReturnReasonCode.MOVED_AWAY == "moved_away"
        assert ReturnReasonCode.BEHAVIOR_ISSUES == "behavior_issues"
        assert ReturnReasonCode.ALLERGIES == "allergies"
        assert ReturnReasonCode.FINANCIAL == "financial"
        assert ReturnReasonCode.OTHER == "other"

    def test_return_reason_has_eight_codes(self) -> None:
        assert len(ReturnReasonCode) == 8


class TestScheduleFollowUps:
    """Tests for the schedule_follow_ups service function."""

    @pytest.mark.asyncio
    async def test_creates_four_follow_ups(self) -> None:
        db = AsyncMock()
        # Mock count query returning 0 (no existing follow-ups)
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        request_id = uuid4()
        completed_at = datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)

        result = await schedule_follow_ups(db, request_id, completed_at)

        assert len(result) == 4
        assert db.add.call_count == 4

    @pytest.mark.asyncio
    async def test_schedule_days_match_constants(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        request_id = uuid4()
        completed_at = datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)

        result = await schedule_follow_ups(db, request_id, completed_at)

        day_offsets = [fu.day_offset for fu in result]
        assert day_offsets == [7, 30, 90, 365]

    @pytest.mark.asyncio
    async def test_scheduled_dates_calculated_from_completion(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        request_id = uuid4()
        completed_at = datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)

        result = await schedule_follow_ups(db, request_id, completed_at)

        for fu in result:
            expected_date = completed_at + timedelta(days=fu.day_offset)
            assert fu.scheduled_date == expected_date

    @pytest.mark.asyncio
    async def test_idempotent_when_already_scheduled(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 4  # already exists
        db.execute.return_value = count_result

        request_id = uuid4()
        completed_at = datetime.now(UTC)

        result = await schedule_follow_ups(db, request_id, completed_at)

        assert result == []
        db.add.assert_not_called()


class TestSubmitSurvey:
    """Tests for the submit_survey service function."""

    @pytest.mark.asyncio
    async def test_raises_on_nonexistent_follow_up(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await submit_survey(db, uuid4(), welfare_score=4, satisfaction_score=5)

    @pytest.mark.asyncio
    async def test_sets_survey_fields(self) -> None:
        fu = MagicMock(spec=FollowUp)
        db = AsyncMock()
        db.get.return_value = fu
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        await submit_survey(
            db,
            uuid4(),
            welfare_score=4,
            satisfaction_score=5,
            comments="Doing great",
            issues_noted=None,
        )

        assert fu.welfare_score == 4
        assert fu.satisfaction_score == 5
        assert fu.comments == "Doing great"
        assert fu.status == FollowUpStatus.COMPLETED.value


class TestRecordReturn:
    """Tests for the record_return service function."""

    @pytest.mark.asyncio
    async def test_raises_on_nonexistent_follow_up(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await record_return(db, uuid4(), return_reason_code="moved_away")

    @pytest.mark.asyncio
    async def test_sets_return_fields(self) -> None:
        fu = MagicMock(spec=FollowUp)
        db = AsyncMock()
        db.get.return_value = fu
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        await record_return(
            db,
            uuid4(),
            return_reason_code="behavior_issues",
            return_notes="Dog was aggressive with children",
        )

        assert fu.return_reason_code == "behavior_issues"
        assert fu.return_notes == "Dog was aggressive with children"
        assert fu.return_date is not None
        assert fu.status == FollowUpStatus.COMPLETED.value
