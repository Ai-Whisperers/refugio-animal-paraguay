"""Unit tests for pre-qualification analytics service."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.pre_qualification_attempt import (
    QualificationOutcome,
)
from src.services.pre_qualification_analytics_service import (
    MAX_TOP_ANIMALS,
    MAX_TOP_FAILURES,
    SCORE_BUCKETS,
    get_analytics,
    record_attempt,
)

# --- Helpers ---


def _make_result(
    qualified: bool = True,
    score: int = 80,
    failed_requirements: list | None = None,
) -> MagicMock:
    """Create a mock PreQualificationResult."""
    result = MagicMock()
    result.qualified = qualified
    result.score = score
    result.failed_requirements = failed_requirements or []
    return result


def _make_failed_req(requirement_type: str, is_mandatory: bool = True) -> MagicMock:
    """Create a mock FailedRequirement."""
    req = MagicMock()
    req.requirement_type = requirement_type
    req.is_mandatory = is_mandatory
    return req


# --- Test record_attempt ---


class TestRecordAttempt:
    """Tests for record_attempt."""

    @pytest.mark.asyncio
    async def test_records_qualified_attempt(self) -> None:
        db = AsyncMock()
        animal_id = uuid4()
        user_id = uuid4()
        result = _make_result(qualified=True, score=85)

        await record_attempt(db, animal_id, result, user_id)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        added = db.add.call_args[0][0]
        assert added.animal_id == animal_id
        assert added.user_id == user_id
        assert added.outcome == QualificationOutcome.QUALIFIED
        assert added.score == 85
        assert added.mandatory_failures == 0
        assert added.preferred_failures == 0

    @pytest.mark.asyncio
    async def test_records_disqualified_attempt(self) -> None:
        db = AsyncMock()
        animal_id = uuid4()
        failed = [
            _make_failed_req("yard_required", is_mandatory=True),
            _make_failed_req("home_type", is_mandatory=False),
        ]
        result = _make_result(qualified=False, score=40, failed_requirements=failed)

        await record_attempt(db, animal_id, result)

        added = db.add.call_args[0][0]
        assert added.outcome == QualificationOutcome.DISQUALIFIED
        assert added.score == 40
        assert added.mandatory_failures == 1
        assert added.preferred_failures == 1
        parsed_types = json.loads(added.failed_requirement_types)
        assert "yard_required" in parsed_types
        assert "home_type" in parsed_types

    @pytest.mark.asyncio
    async def test_records_without_user_id(self) -> None:
        db = AsyncMock()
        result = _make_result(qualified=True, score=100)

        await record_attempt(db, uuid4(), result, user_id=None)

        added = db.add.call_args[0][0]
        assert added.user_id is None

    @pytest.mark.asyncio
    async def test_no_failures_stores_null_types(self) -> None:
        db = AsyncMock()
        result = _make_result(qualified=True, score=100, failed_requirements=[])

        await record_attempt(db, uuid4(), result)

        added = db.add.call_args[0][0]
        assert added.failed_requirement_types is None


# --- Test get_analytics ---


class TestGetAnalytics:
    """Tests for get_analytics."""

    @pytest.mark.asyncio
    async def test_returns_zero_stats_when_no_attempts(self) -> None:
        db = AsyncMock()

        # Mock the count query
        count_row = MagicMock()
        count_row.total = 0
        count_row.qualified = 0
        count_row.disqualified = 0
        count_row.avg_score = 0

        # Mock execute to return appropriate results for each call
        bucket_scalar = MagicMock()
        bucket_scalar.scalar_one.return_value = 0

        failure_result = MagicMock()
        failure_result.__iter__ = MagicMock(return_value=iter([]))

        animal_result = MagicMock()
        animal_result.__iter__ = MagicMock(return_value=iter([]))

        count_result = MagicMock()
        count_result.one.return_value = count_row

        # Execute returns different results based on call order
        db.execute = AsyncMock(
            side_effect=[
                count_result,  # count query
                bucket_scalar,  # bucket 0-20
                bucket_scalar,  # bucket 21-40
                bucket_scalar,  # bucket 41-60
                bucket_scalar,  # bucket 61-80
                bucket_scalar,  # bucket 81-100
                failure_result,  # failures
                animal_result,  # top animals
            ]
        )

        result = await get_analytics(db)

        assert result["total_attempts"] == 0
        assert result["qualified_count"] == 0
        assert result["disqualified_count"] == 0
        assert result["qualification_rate"] == 0.0
        assert result["average_score"] == 0
        assert len(result["score_distribution"]) == 5
        assert result["top_failure_reasons"] == []
        assert result["top_animals"] == []

    @pytest.mark.asyncio
    async def test_returns_analytics_with_data(self) -> None:
        db = AsyncMock()

        count_row = MagicMock()
        count_row.total = 10
        count_row.qualified = 7
        count_row.disqualified = 3
        count_row.avg_score = 72.5

        count_result = MagicMock()
        count_result.one.return_value = count_row

        # Bucket results
        bucket_results = [2, 1, 3, 3, 1]  # counts for each bucket
        bucket_mocks = []
        for count in bucket_results:
            m = MagicMock()
            m.scalar_one.return_value = count
            bucket_mocks.append(m)

        # Failure types
        failure_rows = [
            ('["yard_required", "home_type"]',),
            ('["yard_required"]',),
        ]
        failure_result = MagicMock()
        failure_result.__iter__ = MagicMock(return_value=iter(failure_rows))

        # Top animals
        animal_row = MagicMock()
        animal_row.animal_id = uuid4()
        animal_row.attempt_count = 5
        animal_row.qualified_count = 3
        animal_result = MagicMock()
        animal_result.__iter__ = MagicMock(return_value=iter([animal_row]))

        db.execute = AsyncMock(
            side_effect=[
                count_result,
                *bucket_mocks,
                failure_result,
                animal_result,
            ]
        )

        result = await get_analytics(db)

        assert result["total_attempts"] == 10
        assert result["qualified_count"] == 7
        assert result["disqualified_count"] == 3
        assert result["qualification_rate"] == 70.0
        assert result["average_score"] == 72.5
        assert len(result["score_distribution"]) == 5
        assert result["score_distribution"][0]["count"] == 2
        assert len(result["top_failure_reasons"]) == 2
        # yard_required appears twice
        assert result["top_failure_reasons"][0]["requirement_type"] == "yard_required"
        assert result["top_failure_reasons"][0]["count"] == 2
        assert len(result["top_animals"]) == 1

    @pytest.mark.asyncio
    async def test_passes_date_filters(self) -> None:
        db = AsyncMock()
        date_from = datetime(2026, 1, 1, tzinfo=UTC)
        date_to = datetime(2026, 3, 31, tzinfo=UTC)

        count_row = MagicMock()
        count_row.total = 0
        count_row.qualified = 0
        count_row.disqualified = 0
        count_row.avg_score = 0

        count_result = MagicMock()
        count_result.one.return_value = count_row

        bucket_scalar = MagicMock()
        bucket_scalar.scalar_one.return_value = 0

        empty_iter = MagicMock()
        empty_iter.__iter__ = MagicMock(return_value=iter([]))

        db.execute = AsyncMock(
            side_effect=[
                count_result,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                empty_iter,
                empty_iter,
            ]
        )

        result = await get_analytics(db, date_from=date_from, date_to=date_to)

        assert result["date_from"] == date_from.isoformat()
        assert result["date_to"] == date_to.isoformat()

    @pytest.mark.asyncio
    async def test_handles_malformed_json_in_failures(self) -> None:
        db = AsyncMock()

        count_row = MagicMock()
        count_row.total = 1
        count_row.qualified = 0
        count_row.disqualified = 1
        count_row.avg_score = 30.0

        count_result = MagicMock()
        count_result.one.return_value = count_row

        bucket_scalar = MagicMock()
        bucket_scalar.scalar_one.return_value = 0

        # Malformed JSON in failure types
        failure_rows = [
            ("not valid json",),
            ('["yard_required"]',),
        ]
        failure_result = MagicMock()
        failure_result.__iter__ = MagicMock(return_value=iter(failure_rows))

        empty_iter = MagicMock()
        empty_iter.__iter__ = MagicMock(return_value=iter([]))

        db.execute = AsyncMock(
            side_effect=[
                count_result,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                bucket_scalar,
                failure_result,
                empty_iter,
            ]
        )

        result = await get_analytics(db)

        # Should still return the valid failure
        assert len(result["top_failure_reasons"]) == 1
        assert result["top_failure_reasons"][0]["requirement_type"] == "yard_required"


# --- Test model ---


class TestPreQualificationAttemptModel:
    """Tests for the PreQualificationAttempt model."""

    def test_qualification_outcome_values(self) -> None:
        assert QualificationOutcome.QUALIFIED == "qualified"
        assert QualificationOutcome.DISQUALIFIED == "disqualified"


# --- Test constants ---


class TestConstants:
    """Tests for analytics constants."""

    def test_score_buckets_cover_full_range(self) -> None:
        assert SCORE_BUCKETS[0][0] == 0
        assert SCORE_BUCKETS[-1][1] == 100
        assert len(SCORE_BUCKETS) == 5

    def test_max_top_failures(self) -> None:
        assert MAX_TOP_FAILURES == 10

    def test_max_top_animals(self) -> None:
        assert MAX_TOP_ANIMALS == 10
