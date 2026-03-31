"""Unit tests for adopter satisfaction survey management service (RAP-264, EPIC-53)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.survey_management_service import (
    MarkSentResult,
    PendingSurvey,
    SurveyResult,
    SurveyStats,
    _safe_avg,
    _safe_pct,
    get_pending_surveys,
    get_survey_results,
    get_survey_stats,
    mark_surveys_sent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_follow_up(**overrides):
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "adoption_request_id": uuid4(),
        "scheduled_date": now - timedelta(days=5),
        "day_offset": 30,
        "status": "pending",
        "survey_sent_at": None,
        "survey_completed_at": None,
        "welfare_score": None,
        "satisfaction_score": None,
        "comments": None,
        "issues_noted": None,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ---------------------------------------------------------------------------
# _safe_avg
# ---------------------------------------------------------------------------


class TestSafeAvg:
    def test_normal(self):
        result = _safe_avg(10.0, 4)
        assert result == 2.5

    def test_below_threshold_returns_none(self):
        assert _safe_avg(5.0, 0) is None

    def test_rounds_to_one_decimal(self):
        result = _safe_avg(10.0, 3)
        assert result == 3.3


# ---------------------------------------------------------------------------
# _safe_pct
# ---------------------------------------------------------------------------


class TestSafePct:
    def test_normal(self):
        assert _safe_pct(3, 10) == 30.0

    def test_zero_denominator(self):
        assert _safe_pct(5, 0) == 0.0

    def test_rounding(self):
        assert _safe_pct(1, 3) == 33.33


# ---------------------------------------------------------------------------
# get_pending_surveys
# ---------------------------------------------------------------------------


class TestGetPendingSurveys:
    @pytest.mark.asyncio
    async def test_returns_pending_surveys(self):
        db = AsyncMock()
        fu1 = _make_follow_up(day_offset=7)
        fu2 = _make_follow_up(day_offset=30)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [fu1, fu2]
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_pending_surveys(db)

        assert len(result) == 2
        assert all(isinstance(s, PendingSurvey) for s in result)

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_pending_surveys(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_days_overdue_computed(self):
        db = AsyncMock()
        past_date = datetime.now(UTC) - timedelta(days=10)
        fu = _make_follow_up(scheduled_date=past_date)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [fu]
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_pending_surveys(db)

        assert result[0].days_overdue >= 10


# ---------------------------------------------------------------------------
# get_survey_stats
# ---------------------------------------------------------------------------


class TestGetSurveyStats:
    @pytest.mark.asyncio
    async def test_returns_stats(self):
        db = AsyncMock()

        count_row = MagicMock()
        count_row.total = 100
        count_row.sent = 80
        count_row.completed = 60
        count_result = MagicMock()
        count_result.one.return_value = count_row

        avg_row = MagicMock()
        avg_row.welfare_sum = 240.0
        avg_row.satisfaction_sum = 270.0
        avg_row.welfare_count = 60
        avg_row.satisfaction_count = 60
        avg_result = MagicMock()
        avg_result.one.return_value = avg_row

        db.execute = AsyncMock(side_effect=[count_result, avg_result])

        stats = await get_survey_stats(db)

        assert isinstance(stats, SurveyStats)
        assert stats.total_scheduled == 100
        assert stats.total_sent == 80
        assert stats.total_completed == 60
        assert stats.send_rate_pct == 80.0
        assert stats.completion_rate_pct == 75.0

    @pytest.mark.asyncio
    async def test_empty_database(self):
        db = AsyncMock()

        count_row = MagicMock()
        count_row.total = 0
        count_row.sent = 0
        count_row.completed = 0
        count_result = MagicMock()
        count_result.one.return_value = count_row

        avg_row = MagicMock()
        avg_row.welfare_sum = None
        avg_row.satisfaction_sum = None
        avg_row.welfare_count = 0
        avg_row.satisfaction_count = 0
        avg_result = MagicMock()
        avg_result.one.return_value = avg_row

        db.execute = AsyncMock(side_effect=[count_result, avg_result])

        stats = await get_survey_stats(db)

        assert stats.send_rate_pct == 0.0
        assert stats.completion_rate_pct == 0.0
        assert stats.avg_welfare_score is None
        assert stats.avg_satisfaction_score is None


# ---------------------------------------------------------------------------
# mark_surveys_sent
# ---------------------------------------------------------------------------


class TestMarkSurveysSent:
    @pytest.mark.asyncio
    async def test_marks_unsent_rows(self):
        db = AsyncMock()
        ids = [uuid4(), uuid4()]

        # Already-sent query returns empty
        already_result = MagicMock()
        already_result.scalars.return_value.all.return_value = []

        # To-update query returns both IDs
        fu1 = MagicMock()
        fu1.id = ids[0]
        fu2 = MagicMock()
        fu2.id = ids[1]
        to_update_result = MagicMock()
        to_update_result.scalars.return_value = [fu1, fu2]

        update_result = MagicMock()
        db.execute = AsyncMock(side_effect=[already_result, to_update_result, update_result])
        db.flush = AsyncMock()

        result = await mark_surveys_sent(db, follow_up_ids=ids)

        assert isinstance(result, MarkSentResult)
        assert result.marked_count == 2
        assert result.already_sent_count == 0

    @pytest.mark.asyncio
    async def test_empty_list_returns_zeros(self):
        db = AsyncMock()

        result = await mark_surveys_sent(db, follow_up_ids=[])

        assert result.marked_count == 0
        assert result.already_sent_count == 0
        db.execute.assert_not_called()


# ---------------------------------------------------------------------------
# get_survey_results
# ---------------------------------------------------------------------------


class TestGetSurveyResults:
    @pytest.mark.asyncio
    async def test_returns_completed_surveys(self):
        db = AsyncMock()
        fu1 = _make_follow_up(
            welfare_score=4,
            satisfaction_score=5,
            survey_completed_at=datetime.now(UTC),
        )
        fu2 = _make_follow_up(
            welfare_score=3,
            satisfaction_score=4,
            survey_completed_at=datetime.now(UTC),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter([fu1, fu2])
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_survey_results(db)

        assert len(result) == 2
        assert all(isinstance(r, SurveyResult) for r in result)

    @pytest.mark.asyncio
    async def test_empty_results(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter([])
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_survey_results(db)

        assert result == []
