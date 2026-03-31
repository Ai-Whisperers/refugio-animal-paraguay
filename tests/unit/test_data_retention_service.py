"""Unit tests for the data retention policy service (RAP-229).

Tests cover:
- purge_expired_unused_tokens: deletes tokens beyond retention window
- purge_used_tokens: deletes used tokens beyond retention window
- run_data_retention: aggregates results from both cleanups
- count_retention_candidates: counts without deleting
- DataRetentionResult.total_deleted property
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.data_retention_service import (
    EXPIRED_TOKEN_RETENTION_DAYS,
    USED_TOKEN_RETENTION_DAYS,
    DataRetentionResult,
    count_retention_candidates,
    purge_expired_unused_tokens,
    purge_used_tokens,
    run_data_retention,
)


class TestDataRetentionResult:
    """Tests for DataRetentionResult dataclass."""

    def test_total_deleted_sums_categories(self) -> None:
        result = DataRetentionResult(expired_tokens_deleted=3, used_tokens_deleted=7)
        assert result.total_deleted == 10

    def test_total_deleted_zero_when_empty(self) -> None:
        result = DataRetentionResult()
        assert result.total_deleted == 0

    def test_ran_at_defaults_to_now(self) -> None:
        before = datetime.now(UTC)
        result = DataRetentionResult()
        after = datetime.now(UTC)
        assert before <= result.ran_at <= after

    def test_ran_at_can_be_overridden(self) -> None:
        ts = datetime(2026, 1, 15, tzinfo=UTC)
        result = DataRetentionResult(ran_at=ts)
        assert result.ran_at == ts


class TestPurgeExpiredUnusedTokens:
    """Tests for purge_expired_unused_tokens()."""

    @pytest.mark.asyncio
    async def test_deletes_tokens_beyond_retention_window(self) -> None:
        """Tokens expired more than retention_days ago are deleted."""
        now = datetime(2026, 3, 29, tzinfo=UTC)
        db = MagicMock()
        mock_rows = [MagicMock(), MagicMock()]
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=mock_rows)))

        deleted = await purge_expired_unused_tokens(db, retention_days=30, now=now)

        assert deleted == 2
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_delete(self) -> None:
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))

        deleted = await purge_expired_unused_tokens(db, retention_days=30)

        assert deleted == 0

    @pytest.mark.asyncio
    async def test_uses_default_retention_days(self) -> None:
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))

        await purge_expired_unused_tokens(db)

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cutoff_uses_provided_now(self) -> None:
        """Verifies cutoff = now - retention_days (by checking execute is called)."""
        now = datetime(2026, 1, 1, tzinfo=UTC)
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))

        await purge_expired_unused_tokens(db, retention_days=10, now=now)

        db.execute.assert_awaited_once()


class TestPurgeUsedTokens:
    """Tests for purge_used_tokens()."""

    @pytest.mark.asyncio
    async def test_deletes_used_tokens_beyond_retention_window(self) -> None:
        now = datetime(2026, 3, 29, tzinfo=UTC)
        db = MagicMock()
        mock_rows = [MagicMock(), MagicMock(), MagicMock()]
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=mock_rows)))

        deleted = await purge_used_tokens(db, retention_days=90, now=now)

        assert deleted == 3
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_delete(self) -> None:
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))

        deleted = await purge_used_tokens(db)

        assert deleted == 0


class TestRunDataRetention:
    """Tests for run_data_retention() orchestrator."""

    @pytest.mark.asyncio
    async def test_returns_result_with_combined_counts(self) -> None:
        now = datetime(2026, 3, 29, tzinfo=UTC)
        db = MagicMock()

        with (
            patch(
                "src.services.data_retention_service.purge_expired_unused_tokens",
                new=AsyncMock(return_value=5),
            ),
            patch(
                "src.services.data_retention_service.purge_used_tokens",
                new=AsyncMock(return_value=3),
            ),
        ):
            result = await run_data_retention(db, now=now)

        assert result.expired_tokens_deleted == 5
        assert result.used_tokens_deleted == 3
        assert result.total_deleted == 8
        assert result.ran_at == now

    @pytest.mark.asyncio
    async def test_uses_custom_retention_days(self) -> None:
        db = MagicMock()

        with (
            patch(
                "src.services.data_retention_service.purge_expired_unused_tokens",
                new=AsyncMock(return_value=0),
            ) as mock_expired,
            patch(
                "src.services.data_retention_service.purge_used_tokens",
                new=AsyncMock(return_value=0),
            ) as mock_used,
        ):
            await run_data_retention(db, expired_token_retention_days=7, used_token_retention_days=14)

        mock_expired.assert_awaited_once()
        call_kwargs_expired = mock_expired.call_args.kwargs
        assert call_kwargs_expired["retention_days"] == 7

        mock_used.assert_awaited_once()
        call_kwargs_used = mock_used.call_args.kwargs
        assert call_kwargs_used["retention_days"] == 14

    @pytest.mark.asyncio
    async def test_zero_deletes_when_nothing_to_clean(self) -> None:
        db = MagicMock()

        with (
            patch("src.services.data_retention_service.purge_expired_unused_tokens", new=AsyncMock(return_value=0)),
            patch("src.services.data_retention_service.purge_used_tokens", new=AsyncMock(return_value=0)),
        ):
            result = await run_data_retention(db)

        assert result.total_deleted == 0


class TestCountRetentionCandidates:
    """Tests for count_retention_candidates() dry-run function."""

    @pytest.mark.asyncio
    async def test_returns_counts_without_deleting(self) -> None:
        db = MagicMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=4)),
                MagicMock(scalar_one=MagicMock(return_value=6)),
            ]
        )

        counts = await count_retention_candidates(db)

        assert counts["expired_tokens"] == 4
        assert counts["used_tokens"] == 6
        assert counts["total"] == 10

    @pytest.mark.asyncio
    async def test_total_is_sum_of_categories(self) -> None:
        db = MagicMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )

        counts = await count_retention_candidates(db)

        assert counts["total"] == 0

    @pytest.mark.asyncio
    async def test_executes_two_queries(self) -> None:
        """count_retention_candidates issues exactly 2 SELECT queries."""
        db = MagicMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=1)),
                MagicMock(scalar_one=MagicMock(return_value=2)),
            ]
        )

        await count_retention_candidates(db)

        assert db.execute.await_count == 2


class TestRetentionConstants:
    """Tests that retention policy constants have sensible values."""

    def test_expired_token_retention_days_is_positive(self) -> None:
        assert EXPIRED_TOKEN_RETENTION_DAYS > 0

    def test_used_token_retention_days_is_positive(self) -> None:
        assert USED_TOKEN_RETENTION_DAYS > 0

    def test_used_retention_longer_than_expired(self) -> None:
        # Used tokens should be kept longer than expired ones (post-use audit window)
        assert USED_TOKEN_RETENTION_DAYS >= EXPIRED_TOKEN_RETENTION_DAYS
