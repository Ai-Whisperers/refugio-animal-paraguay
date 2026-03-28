"""Unit tests for the pipeline tracking service.

Tests stage transitions, rejection, history retrieval, timeout
detection, and pipeline summary aggregation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.pipeline_tracking_service import (
    ACTION_ADVANCE,
    ACTION_REJECT,
    REJECTION_STATUS,
    VALID_ACTIONS,
    AdoptionNotFoundError,
    AlreadyCompletedError,
    InvalidTransitionError,
    PipelineTrackingError,
    StageNotFoundError,
    advance_adoption,
    get_adoption_with_stage,
    get_next_stage,
    get_pipeline_summary,
    get_stage_history,
    get_timed_out_adoptions,
    reject_adoption,
)

# ── Error class tests ──────────────────────────────────────────


class TestErrorClasses:
    """Verify error hierarchy and instantiation."""

    def test_base_error_is_exception(self) -> None:
        err = PipelineTrackingError("base")
        assert isinstance(err, Exception)
        assert str(err) == "base"

    def test_adoption_not_found_inherits_base(self) -> None:
        err = AdoptionNotFoundError("not found")
        assert isinstance(err, PipelineTrackingError)

    def test_invalid_transition_inherits_base(self) -> None:
        err = InvalidTransitionError("bad transition")
        assert isinstance(err, PipelineTrackingError)

    def test_already_completed_inherits_base(self) -> None:
        err = AlreadyCompletedError("done")
        assert isinstance(err, PipelineTrackingError)

    def test_stage_not_found_inherits_base(self) -> None:
        err = StageNotFoundError("no stage")
        assert isinstance(err, PipelineTrackingError)


# ── Constants tests ────────────────────────────────────────────


class TestConstants:
    """Verify module-level constants."""

    def test_valid_actions_contains_expected(self) -> None:
        assert ACTION_ADVANCE in VALID_ACTIONS
        assert ACTION_REJECT in VALID_ACTIONS
        assert "reset" in VALID_ACTIONS

    def test_rejection_status_value(self) -> None:
        assert REJECTION_STATUS == "rejected"


# ── get_adoption_with_stage tests ──────────────────────────────


class TestGetAdoptionWithStage:
    """Tests for fetching adoption with stage details."""

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(AdoptionNotFoundError):
            await get_adoption_with_stage(db, uuid4())

    @pytest.mark.asyncio
    async def test_returns_adoption_without_stage(self) -> None:
        adoption_id = uuid4()
        animal_id = uuid4()
        adopter_id = uuid4()

        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.animal_id = animal_id
        mock_adoption.adopter_id = adopter_id
        mock_adoption.status = "pending"
        mock_adoption.current_stage_id = None
        mock_adoption.current_stage_started_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        result = await get_adoption_with_stage(db, adoption_id)

        assert result["id"] == adoption_id
        assert result["status"] == "pending"
        assert result["current_stage"] is None
        assert result["days_in_current_stage"] is None

    @pytest.mark.asyncio
    async def test_returns_adoption_with_stage_info(self) -> None:
        adoption_id = uuid4()
        stage_id = uuid4()

        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.animal_id = uuid4()
        mock_adoption.adopter_id = uuid4()
        mock_adoption.status = "approved"
        mock_adoption.current_stage_id = stage_id
        mock_adoption.current_stage_started_at = datetime.now(UTC) - timedelta(days=3)

        mock_stage = MagicMock()
        mock_stage.id = stage_id
        mock_stage.name = "Home Visit"
        mock_stage.position = 2
        mock_stage.color = "#F59E0B"
        mock_stage.requires_approval = True
        mock_stage.max_days = 7

        db = AsyncMock()
        # First call returns adoption, second returns stage
        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_stage = MagicMock()
        mock_result_stage.scalar_one_or_none.return_value = mock_stage
        db.execute.side_effect = [mock_result_adoption, mock_result_stage]

        result = await get_adoption_with_stage(db, adoption_id)

        assert result["current_stage"]["name"] == "Home Visit"
        assert result["days_in_current_stage"] == 3


# ── get_next_stage tests ──────────────────────────────────────


class TestGetNextStage:
    """Tests for finding the next pipeline stage."""

    @pytest.mark.asyncio
    async def test_returns_first_stage_when_no_current(self) -> None:
        stage_id = uuid4()
        mock_stage = MagicMock()
        mock_stage.id = stage_id
        mock_stage.name = "Application Review"
        mock_stage.position = 1
        mock_stage.color = "#3B82F6"
        mock_stage.requires_approval = True
        mock_stage.max_days = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stage
        db.execute.return_value = mock_result

        result = await get_next_stage(db, None)

        assert result is not None
        assert result["name"] == "Application Review"
        assert result["position"] == 1

    @pytest.mark.asyncio
    async def test_returns_none_when_no_stages(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await get_next_stage(db, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_next_stage_after_current(self) -> None:
        current_id = uuid4()
        next_id = uuid4()

        mock_current = MagicMock()
        mock_current.id = current_id
        mock_current.position = 2

        mock_next = MagicMock()
        mock_next.id = next_id
        mock_next.name = "Trial Period"
        mock_next.position = 3
        mock_next.color = "#10B981"
        mock_next.requires_approval = True
        mock_next.max_days = 14

        db = AsyncMock()
        mock_result_current = MagicMock()
        mock_result_current.scalar_one_or_none.return_value = mock_current
        mock_result_next = MagicMock()
        mock_result_next.scalar_one_or_none.return_value = mock_next
        db.execute.side_effect = [mock_result_current, mock_result_next]

        result = await get_next_stage(db, current_id)

        assert result is not None
        assert result["name"] == "Trial Period"

    @pytest.mark.asyncio
    async def test_returns_none_at_last_stage(self) -> None:
        current_id = uuid4()

        mock_current = MagicMock()
        mock_current.id = current_id
        mock_current.position = 5

        db = AsyncMock()
        mock_result_current = MagicMock()
        mock_result_current.scalar_one_or_none.return_value = mock_current
        mock_result_next = MagicMock()
        mock_result_next.scalar_one_or_none.return_value = None
        db.execute.side_effect = [mock_result_current, mock_result_next]

        result = await get_next_stage(db, current_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_current_stage_missing(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await get_next_stage(db, uuid4())

        assert result is None


# ── advance_adoption tests ────────────────────────────────────


class TestAdvanceAdoption:
    """Tests for advancing an adoption through stages."""

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(AdoptionNotFoundError):
            await advance_adoption(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_already_rejected(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "rejected"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        with pytest.raises(AlreadyCompletedError, match="rejected"):
            await advance_adoption(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_already_cancelled(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "cancelled"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        with pytest.raises(AlreadyCompletedError, match="cancelled"):
            await advance_adoption(db, uuid4())

    @pytest.mark.asyncio
    @patch("src.services.pipeline_tracking_service.get_next_stage")
    async def test_raises_when_no_next_stage(self, mock_get_next: AsyncMock) -> None:
        mock_get_next.return_value = None

        mock_adoption = MagicMock()
        mock_adoption.status = "approved"
        mock_adoption.current_stage_id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        with pytest.raises(InvalidTransitionError, match="final stage"):
            await advance_adoption(db, uuid4())

    @pytest.mark.asyncio
    @patch("src.services.pipeline_tracking_service.get_next_stage")
    async def test_advances_pending_to_first_stage(self, mock_get_next: AsyncMock) -> None:
        next_stage_id = uuid4()
        mock_get_next.return_value = {
            "id": next_stage_id,
            "name": "Application Review",
            "position": 1,
            "color": "#3B82F6",
            "requires_approval": True,
            "max_days": None,
        }

        adoption_id = uuid4()
        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.status = "pending"
        mock_adoption.current_stage_id = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        user_id = uuid4()
        result = await advance_adoption(db, adoption_id, user_id=user_id, notes="Starting pipeline")

        assert result["action"] == ACTION_ADVANCE
        assert result["to_stage_id"] == next_stage_id
        assert result["to_stage_name"] == "Application Review"
        assert result["notes"] == "Starting pipeline"
        # Verify status changed from pending to approved
        assert mock_adoption.status == "approved"
        assert mock_adoption.current_stage_id == next_stage_id
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.pipeline_tracking_service.get_next_stage")
    async def test_advances_to_next_stage(self, mock_get_next: AsyncMock) -> None:
        from_stage_id = uuid4()
        to_stage_id = uuid4()
        mock_get_next.return_value = {
            "id": to_stage_id,
            "name": "Home Visit",
            "position": 2,
            "color": "#F59E0B",
            "requires_approval": True,
            "max_days": 7,
        }

        mock_adoption = MagicMock()
        mock_adoption.id = uuid4()
        mock_adoption.status = "approved"
        mock_adoption.current_stage_id = from_stage_id

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        result = await advance_adoption(db, mock_adoption.id)

        assert result["from_stage_id"] == from_stage_id
        assert result["to_stage_id"] == to_stage_id
        assert result["to_stage_name"] == "Home Visit"
        assert mock_adoption.current_stage_id == to_stage_id


# ── reject_adoption tests ─────────────────────────────────────


class TestRejectAdoption:
    """Tests for rejecting an adoption at any stage."""

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(AdoptionNotFoundError):
            await reject_adoption(db, uuid4(), reason="test")

    @pytest.mark.asyncio
    async def test_raises_when_already_rejected(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "rejected"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        with pytest.raises(AlreadyCompletedError, match="rejected"):
            await reject_adoption(db, uuid4(), reason="test")

    @pytest.mark.asyncio
    async def test_rejects_successfully(self) -> None:
        adoption_id = uuid4()
        stage_id = uuid4()

        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.status = "approved"
        mock_adoption.current_stage_id = stage_id

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        user_id = uuid4()
        result = await reject_adoption(db, adoption_id, reason="Failed home visit", user_id=user_id)

        assert result["action"] == ACTION_REJECT
        assert result["from_stage_id"] == stage_id
        assert result["reason"] == "Failed home visit"
        assert mock_adoption.status == REJECTION_STATUS
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reject_sets_decided_at(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.id = uuid4()
        mock_adoption.status = "pending"
        mock_adoption.current_stage_id = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        await reject_adoption(db, mock_adoption.id, reason="Not suitable")

        assert mock_adoption.decided_at is not None


# ── get_stage_history tests ───────────────────────────────────


class TestGetStageHistory:
    """Tests for retrieving stage transition history."""

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(AdoptionNotFoundError):
            await get_stage_history(db, uuid4())

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_history(self) -> None:
        adoption_id = uuid4()

        db = AsyncMock()
        # First call: exists check
        mock_exists = MagicMock()
        mock_exists.scalar_one_or_none.return_value = adoption_id
        # Second call: history query
        mock_logs = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_logs.scalars.return_value = mock_scalars
        db.execute.side_effect = [mock_exists, mock_logs]

        result = await get_stage_history(db, adoption_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_ordered_history(self) -> None:
        adoption_id = uuid4()

        log1 = MagicMock()
        log1.id = uuid4()
        log1.adoption_request_id = adoption_id
        log1.from_stage_id = None
        log1.to_stage_id = uuid4()
        log1.action = "advance"
        log1.notes = "Started"
        log1.transitioned_by = uuid4()
        log1.transitioned_at = datetime(2026, 3, 1, tzinfo=UTC)

        log2 = MagicMock()
        log2.id = uuid4()
        log2.adoption_request_id = adoption_id
        log2.from_stage_id = log1.to_stage_id
        log2.to_stage_id = uuid4()
        log2.action = "advance"
        log2.notes = None
        log2.transitioned_by = uuid4()
        log2.transitioned_at = datetime(2026, 3, 5, tzinfo=UTC)

        db = AsyncMock()
        mock_exists = MagicMock()
        mock_exists.scalar_one_or_none.return_value = adoption_id
        mock_logs = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [log1, log2]
        mock_logs.scalars.return_value = mock_scalars
        db.execute.side_effect = [mock_exists, mock_logs]

        result = await get_stage_history(db, adoption_id)

        assert len(result) == 2
        assert result[0]["action"] == "advance"
        assert result[0]["notes"] == "Started"
        assert result[1]["from_stage_id"] == log1.to_stage_id


# ── get_timed_out_adoptions tests ─────────────────────────────


class TestGetTimedOutAdoptions:
    """Tests for timeout detection."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_none_timed_out(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_timed_out_adoptions(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_detects_overdue_adoption(self) -> None:
        adoption_id = uuid4()
        stage_id = uuid4()

        row = MagicMock()
        row.id = adoption_id
        row.animal_id = uuid4()
        row.adopter_id = uuid4()
        row.stage_id = stage_id
        row.stage_name = "Home Visit"
        row.max_days = 7
        row.current_stage_started_at = datetime.now(UTC) - timedelta(days=10)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await get_timed_out_adoptions(db)

        assert len(result) == 1
        assert result[0]["adoption_request_id"] == adoption_id
        assert result[0]["stage_name"] == "Home Visit"
        assert result[0]["days_in_stage"] == 10
        assert result[0]["overdue_by"] == 3

    @pytest.mark.asyncio
    async def test_excludes_non_overdue(self) -> None:
        row = MagicMock()
        row.id = uuid4()
        row.animal_id = uuid4()
        row.adopter_id = uuid4()
        row.stage_id = uuid4()
        row.stage_name = "Trial Period"
        row.max_days = 14
        row.current_stage_started_at = datetime.now(UTC) - timedelta(days=5)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await get_timed_out_adoptions(db)

        assert result == []


# ── get_pipeline_summary tests ────────────────────────────────


class TestGetPipelineSummary:
    """Tests for pipeline summary aggregation."""

    @pytest.mark.asyncio
    async def test_returns_summary_rows(self) -> None:
        stage1_id = uuid4()
        stage2_id = uuid4()

        row1 = MagicMock()
        row1.id = stage1_id
        row1.name = "Application Review"
        row1.position = 1
        row1.color = "#3B82F6"
        row1.adoption_count = 5

        row2 = MagicMock()
        row2.id = stage2_id
        row2.name = "Home Visit"
        row2.position = 2
        row2.color = "#F59E0B"
        row2.adoption_count = 3

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [row1, row2]
        db.execute.return_value = mock_result

        result = await get_pipeline_summary(db)

        assert len(result) == 2
        assert result[0]["stage_name"] == "Application Review"
        assert result[0]["adoption_count"] == 5
        assert result[1]["stage_name"] == "Home Visit"
        assert result[1]["adoption_count"] == 3

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_stages(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_pipeline_summary(db)

        assert result == []
