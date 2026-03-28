"""Unit tests for the monthly impact service cache and data structures."""

from datetime import UTC, datetime

import pytest

from src.services.impact_monthly_service import (
    ImpactSummary,
    MonthlyImpact,
    _ImpactCache,
    _month_range,
)


class TestMonthRange:
    """Tests for _month_range helper."""

    def test_returns_start_and_end_of_month(self) -> None:
        start, end = _month_range(2026, 3)
        assert start == datetime(2026, 3, 1, tzinfo=UTC)
        assert end == datetime(2026, 4, 1, tzinfo=UTC)

    def test_december_wraps_to_january(self) -> None:
        start, end = _month_range(2025, 12)
        assert start == datetime(2025, 12, 1, tzinfo=UTC)
        assert end == datetime(2026, 1, 1, tzinfo=UTC)

    def test_february_non_leap(self) -> None:
        start, end = _month_range(2025, 2)
        assert start == datetime(2025, 2, 1, tzinfo=UTC)
        assert end == datetime(2025, 3, 1, tzinfo=UTC)

    def test_february_leap_year(self) -> None:
        start, end = _month_range(2024, 2)
        assert start == datetime(2024, 2, 1, tzinfo=UTC)
        assert end == datetime(2024, 3, 1, tzinfo=UTC)


class TestImpactCache:
    """Tests for in-memory impact cache."""

    def test_empty_cache_returns_none(self) -> None:
        cache = _ImpactCache(ttl=300)
        assert cache.cached is None

    def test_set_and_retrieve(self) -> None:
        cache = _ImpactCache(ttl=300)
        summary = _make_summary()
        cache.set(summary)
        assert cache.cached is summary

    def test_expired_cache_returns_none(self) -> None:
        cache = _ImpactCache(ttl=0)  # Immediately expires
        summary = _make_summary()
        cache.set(summary)
        # With TTL=0, reading after set should return None
        assert cache.cached is None

    def test_invalidate_clears_cache(self) -> None:
        cache = _ImpactCache(ttl=300)
        cache.set(_make_summary())
        cache.invalidate()
        assert cache.cached is None


class TestMonthlyImpact:
    """Tests for the MonthlyImpact dataclass."""

    def test_frozen_fields(self) -> None:
        item = MonthlyImpact(
            year=2026,
            month=3,
            animals_rescued=10,
            adoptions_completed=5,
            castrations_performed=8,
            donations_total_cents=150000,
        )
        assert item.year == 2026
        assert item.month == 3
        assert item.animals_rescued == 10
        assert item.donations_total_cents == 150000

        with pytest.raises(AttributeError):
            item.year = 2025  # type: ignore[misc]


class TestImpactSummary:
    """Tests for the ImpactSummary dataclass."""

    def test_summary_has_12_months(self) -> None:
        summary = _make_summary(n_months=12)
        assert len(summary.months) == 12

    def test_summary_totals(self) -> None:
        summary = _make_summary()
        assert summary.total_animals_rescued == 100
        assert summary.total_adopted == 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_summary(n_months: int = 3) -> ImpactSummary:
    months = [
        MonthlyImpact(
            year=2026,
            month=i + 1,
            animals_rescued=10,
            adoptions_completed=5,
            castrations_performed=8,
            donations_total_cents=50000,
        )
        for i in range(n_months)
    ]
    return ImpactSummary(
        total_animals_rescued=100,
        total_adopted=50,
        total_castrated=40,
        total_donations_cents=500000,
        months=months,
        last_updated=datetime.now(UTC),
    )
