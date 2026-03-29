"""Unit tests for donor_retention_service (RAP-258)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.donor_retention_service import (
    ACTIVE_THRESHOLD_DAYS,
    CHURNED_THRESHOLD_DAYS,
    LAPSED_THRESHOLD_DAYS,
    DonorSegmentCounts,
    _safe_rate,
    get_cohort_retention,
    get_donor_segments,
    get_retention_metrics,
)

# ---------------------------------------------------------------------------
# _safe_rate helper
# ---------------------------------------------------------------------------


def test_safe_rate_normal() -> None:
    assert _safe_rate(75, 100) == 75.0


def test_safe_rate_zero_denominator() -> None:
    assert _safe_rate(5, 0) == 0.0


def test_safe_rate_rounding() -> None:
    assert _safe_rate(1, 3) == 33.3


def test_safe_rate_full_retention() -> None:
    assert _safe_rate(50, 50) == 100.0


# ---------------------------------------------------------------------------
# Threshold constants — sanity check
# ---------------------------------------------------------------------------


def test_thresholds_are_ordered() -> None:
    assert ACTIVE_THRESHOLD_DAYS < LAPSED_THRESHOLD_DAYS < CHURNED_THRESHOLD_DAYS


# ---------------------------------------------------------------------------
# DonorSegmentCounts.total
# ---------------------------------------------------------------------------


def test_donor_segment_counts_total() -> None:
    counts = DonorSegmentCounts(new=10, active=20, at_risk=5, lapsed=8, churned=3)
    assert counts.total == 46


def test_donor_segment_counts_total_zeros() -> None:
    counts = DonorSegmentCounts(new=0, active=0, at_risk=0, lapsed=0, churned=0)
    assert counts.total == 0


# ---------------------------------------------------------------------------
# get_donor_segments — async with mocked DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_donor_segments_empty_db() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    row = MagicMock()
    row.new = None
    row.active = None
    row.at_risk = None
    row.lapsed = None
    row.churned = None
    mock_result.one.return_value = row
    db.execute.return_value = mock_result

    segments = await get_donor_segments(db)

    assert segments.new == 0
    assert segments.active == 0
    assert segments.at_risk == 0
    assert segments.lapsed == 0
    assert segments.churned == 0
    assert segments.total == 0


@pytest.mark.asyncio
async def test_get_donor_segments_with_counts() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    row = MagicMock()
    row.new = 5
    row.active = 20
    row.at_risk = 8
    row.lapsed = 3
    row.churned = 12
    mock_result.one.return_value = row
    db.execute.return_value = mock_result

    segments = await get_donor_segments(db)

    assert segments.new == 5
    assert segments.active == 20
    assert segments.at_risk == 8
    assert segments.lapsed == 3
    assert segments.churned == 12
    assert segments.total == 48


# ---------------------------------------------------------------------------
# get_retention_metrics — async with mocked DB
# ---------------------------------------------------------------------------


def _make_id_result(ids: list[Any]) -> MagicMock:
    """Mock a SQLAlchemy result that yields (id,) tuples."""
    mock = MagicMock()
    mock.__iter__ = MagicMock(return_value=iter([(i,) for i in ids]))
    return mock


@pytest.mark.asyncio
async def test_get_retention_metrics_no_prior_donors() -> None:
    """When no prior-window donors exist, retention rate should be 0."""
    db = AsyncMock()
    segment_row = MagicMock()
    segment_row.new = 5
    segment_row.active = 5
    segment_row.at_risk = 0
    segment_row.lapsed = 0
    segment_row.churned = 0

    call_count = 0

    async def execute_side_effect(stmt: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            # prior window query — empty
            result.__iter__ = MagicMock(return_value=iter([]))
        elif call_count == 2:
            # current window query — 3 donors
            donor_ids = [uuid4() for _ in range(3)]
            result.__iter__ = MagicMock(return_value=iter([(d,) for d in donor_ids]))
        elif call_count == 3:
            # new donors query — 3 donors
            donor_ids_new = [uuid4() for _ in range(3)]
            result.__iter__ = MagicMock(return_value=iter([(d,) for d in donor_ids_new]))
        else:
            # segments query
            result.one.return_value = segment_row
        return result

    db.execute = execute_side_effect

    metrics = await get_retention_metrics(db, period_days=30)

    assert metrics.retained_donors == 0
    assert metrics.churned_donors == 0
    assert metrics.retention_rate_pct == 0.0
    assert metrics.churn_rate_pct == 0.0
    assert metrics.period_days == 30


@pytest.mark.asyncio
async def test_get_retention_metrics_perfect_retention() -> None:
    """All prior donors also donated in current window → 100% retention."""
    db = AsyncMock()
    shared_ids = [uuid4() for _ in range(5)]

    segment_row = MagicMock()
    segment_row.new = 0
    segment_row.active = 5
    segment_row.at_risk = 0
    segment_row.lapsed = 0
    segment_row.churned = 0

    call_count = 0

    async def execute_side_effect(stmt: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            # prior window — same 5 donors
            result.__iter__ = MagicMock(return_value=iter([(d,) for d in shared_ids]))
        elif call_count == 2:
            # current window — same 5 donors
            result.__iter__ = MagicMock(return_value=iter([(d,) for d in shared_ids]))
        elif call_count == 3:
            # new donors — none
            result.__iter__ = MagicMock(return_value=iter([]))
        else:
            result.one.return_value = segment_row
        return result

    db.execute = execute_side_effect

    metrics = await get_retention_metrics(db, period_days=30)

    assert metrics.retained_donors == 5
    assert metrics.churned_donors == 0
    assert metrics.retention_rate_pct == 100.0
    assert metrics.churn_rate_pct == 0.0


@pytest.mark.asyncio
async def test_get_retention_metrics_generated_at_is_iso8601() -> None:
    from datetime import datetime

    db = AsyncMock()
    segment_row = MagicMock()
    for attr in ("new", "active", "at_risk", "lapsed", "churned"):
        setattr(segment_row, attr, 0)

    call_count = 0

    async def execute_side_effect(stmt: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count < 4:
            result.__iter__ = MagicMock(return_value=iter([]))
        else:
            result.one.return_value = segment_row
        return result

    db.execute = execute_side_effect

    metrics = await get_retention_metrics(db, period_days=30)
    datetime.fromisoformat(metrics.generated_at)  # must not raise


# ---------------------------------------------------------------------------
# get_cohort_retention — async with mocked DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cohort_retention_empty_db() -> None:
    db = AsyncMock()

    call_count = 0

    async def execute_side_effect(stmt: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        # cohort query returns empty
        result.all.return_value = []
        return result

    db.execute = execute_side_effect

    result = await get_cohort_retention(db, lookback_months=6)

    assert result.lookback_months == 6
    assert result.cohorts == []


@pytest.mark.asyncio
async def test_get_cohort_retention_zero_size_cohort_skipped() -> None:
    """Cohorts with size=0 are skipped to avoid division by zero."""
    from datetime import UTC, datetime

    db = AsyncMock()
    zero_cohort = MagicMock()
    zero_cohort.cohort_month = datetime(2025, 1, 1, tzinfo=UTC)
    zero_cohort.cohort_size = 0

    call_count = 0

    async def execute_side_effect(stmt: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.all.return_value = [zero_cohort]
        else:
            mock_scalar = MagicMock()
            mock_scalar.scalar_one.return_value = 0
            return mock_scalar
        return result

    db.execute = execute_side_effect

    result = await get_cohort_retention(db, lookback_months=3)
    assert result.cohorts == []
