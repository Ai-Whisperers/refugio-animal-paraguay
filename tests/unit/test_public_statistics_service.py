"""Unit tests for public statistics service."""

import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.public_statistics_service import (
    CACHE_TTL_SECONDS,
    CASTRATION_SURGERY_TYPE,
    VOLUNTEER_ROLE,
    PublicStatistics,
    PublicStatisticsCache,
    fetch_public_statistics,
    get_public_statistics,
)

# ---------------------------------------------------------------------------
# PublicStatisticsCache tests
# ---------------------------------------------------------------------------


class TestPublicStatisticsCache:
    """Tests for the in-memory cache."""

    def test_empty_cache_is_not_valid(self) -> None:
        cache = PublicStatisticsCache()
        assert cache.is_valid is False
        assert cache.cached_value is None

    def test_set_makes_cache_valid(self) -> None:
        cache = PublicStatisticsCache()
        stats = _make_stats()
        cache.set(stats)
        assert cache.is_valid is True
        assert cache.cached_value is stats

    def test_cache_expires_after_ttl(self) -> None:
        cache = PublicStatisticsCache(ttl_seconds=0)
        stats = _make_stats()
        cache.set(stats)
        # TTL=0 means it should already be expired
        time.sleep(0.01)
        assert cache.is_valid is False
        assert cache.cached_value is None

    def test_invalidate_clears_cache(self) -> None:
        cache = PublicStatisticsCache()
        cache.set(_make_stats())
        assert cache.is_valid is True
        cache.invalidate()
        assert cache.is_valid is False
        assert cache.cached_value is None

    def test_default_ttl_is_300_seconds(self) -> None:
        cache = PublicStatisticsCache()
        assert cache._ttl_seconds == CACHE_TTL_SECONDS


# ---------------------------------------------------------------------------
# PublicStatistics dataclass tests
# ---------------------------------------------------------------------------


class TestPublicStatistics:
    """Tests for the statistics dataclass."""

    def test_immutable(self) -> None:
        stats = _make_stats()
        with pytest.raises(AttributeError):
            stats.total_animals_rescued = 999  # type: ignore[misc]

    def test_fields_populated(self) -> None:
        stats = _make_stats(
            total_animals_rescued=10,
            total_adopted=5,
            total_castrated=3,
            total_donors=7,
            total_donations_amount_cents=50000,
            total_volunteers=12,
        )
        assert stats.total_animals_rescued == 10
        assert stats.total_adopted == 5
        assert stats.total_castrated == 3
        assert stats.total_donors == 7
        assert stats.total_donations_amount_cents == 50000
        assert stats.total_volunteers == 12
        assert isinstance(stats.last_updated, datetime)


# ---------------------------------------------------------------------------
# fetch_public_statistics tests
# ---------------------------------------------------------------------------


class TestFetchPublicStatistics:
    """Tests for the DB query orchestrator."""

    @pytest.mark.asyncio
    async def test_fetches_all_metrics(self) -> None:
        db = _mock_db_with_counts(
            animals=42, adopted=15, castrated=8, donors=20, amount=100000, volunteers=6
        )
        stats = await fetch_public_statistics(db)

        assert stats.total_animals_rescued == 42
        assert stats.total_adopted == 15
        assert stats.total_castrated == 8
        assert stats.total_donors == 20
        assert stats.total_donations_amount_cents == 100000
        assert stats.total_volunteers == 6
        assert isinstance(stats.last_updated, datetime)

    @pytest.mark.asyncio
    async def test_handles_zero_values(self) -> None:
        db = _mock_db_with_counts(
            animals=0, adopted=0, castrated=0, donors=0, amount=0, volunteers=0
        )
        stats = await fetch_public_statistics(db)

        assert stats.total_animals_rescued == 0
        assert stats.total_adopted == 0
        assert stats.total_castrated == 0
        assert stats.total_donors == 0
        assert stats.total_donations_amount_cents == 0
        assert stats.total_volunteers == 0


# ---------------------------------------------------------------------------
# get_public_statistics (with cache) tests
# ---------------------------------------------------------------------------


class TestGetPublicStatistics:
    """Tests for the cached wrapper."""

    @pytest.mark.asyncio
    async def test_returns_cached_value_when_valid(self) -> None:
        cache = PublicStatisticsCache()
        expected = _make_stats(total_animals_rescued=99)
        cache.set(expected)

        db = AsyncMock()  # Should NOT be called
        result = await get_public_statistics(db, cache=cache)

        assert result is expected
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetches_from_db_when_cache_empty(self) -> None:
        cache = PublicStatisticsCache()
        db = _mock_db_with_counts(
            animals=10, adopted=5, castrated=2, donors=3, amount=5000, volunteers=1
        )

        result = await get_public_statistics(db, cache=cache)

        assert result.total_animals_rescued == 10
        assert cache.is_valid is True

    @pytest.mark.asyncio
    async def test_refreshes_after_ttl_expires(self) -> None:
        cache = PublicStatisticsCache(ttl_seconds=0)
        old_stats = _make_stats(total_animals_rescued=1)
        cache.set(old_stats)
        time.sleep(0.01)

        db = _mock_db_with_counts(
            animals=50, adopted=25, castrated=10, donors=15, amount=200000, volunteers=8
        )

        result = await get_public_statistics(db, cache=cache)
        assert result.total_animals_rescued == 50

    @pytest.mark.asyncio
    async def test_populates_cache_after_fetch(self) -> None:
        cache = PublicStatisticsCache()
        db = _mock_db_with_counts(
            animals=7, adopted=3, castrated=1, donors=2, amount=3000, volunteers=4
        )

        await get_public_statistics(db, cache=cache)

        assert cache.is_valid is True
        assert cache.cached_value is not None
        assert cache.cached_value.total_animals_rescued == 7


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_cache_ttl(self) -> None:
        assert CACHE_TTL_SECONDS == 300

    def test_castration_type(self) -> None:
        assert CASTRATION_SURGERY_TYPE == "castration"

    def test_volunteer_role(self) -> None:
        assert VOLUNTEER_ROLE == "volunteer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stats(**overrides: int) -> PublicStatistics:
    """Create a PublicStatistics with sensible defaults."""
    defaults = {
        "total_animals_rescued": 0,
        "total_adopted": 0,
        "total_castrated": 0,
        "total_donors": 0,
        "total_donations_amount_cents": 0,
        "total_volunteers": 0,
        "last_updated": datetime.now(UTC),
    }
    defaults.update(overrides)
    return PublicStatistics(**defaults)  # type: ignore[arg-type]


def _mock_db_with_counts(
    *,
    animals: int,
    adopted: int,
    castrated: int,
    donors: int,
    amount: int,
    volunteers: int,
) -> AsyncMock:
    """Create a mock AsyncSession that returns the given counts in order.

    The service calls db.execute() 6 times (one per metric), each returning
    a result with scalar_one().
    """
    db = AsyncMock()

    results = []
    for value in [animals, adopted, castrated, donors, amount, volunteers]:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = value
        results.append(mock_result)

    db.execute = AsyncMock(side_effect=results)
    return db
