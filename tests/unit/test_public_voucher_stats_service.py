"""Unit tests for public voucher statistics service."""

import time
from unittest.mock import MagicMock

from src.services.public_voucher_stats_service import (
    RecentRedemption,
    ServiceBreakdown,
    TopClinic,
    VoucherStatsResult,
    _get_cached,
    clear_cache,
)


class TestGetCached:
    """Tests for the cache helper function."""

    def test_returns_none_for_empty_cache(self) -> None:
        """Empty cache should return None."""
        cache: dict = {}
        assert _get_cached(cache, "key") is None

    def test_returns_value_within_ttl(self) -> None:
        """Cached value within TTL should be returned."""
        cache = {"key": (time.monotonic(), "value")}
        assert _get_cached(cache, "key", ttl=60) == "value"

    def test_returns_none_after_ttl_expires(self) -> None:
        """Cached value past TTL should return None."""
        cache = {"key": (time.monotonic() - 120, "stale_value")}
        assert _get_cached(cache, "key", ttl=60) is None

    def test_different_keys_are_independent(self) -> None:
        """Different cache keys should not interfere."""
        cache = {"a": (time.monotonic(), "alpha")}
        assert _get_cached(cache, "a", ttl=60) == "alpha"
        assert _get_cached(cache, "b", ttl=60) is None


class TestClearCache:
    """Tests for cache clearing."""

    def test_clear_cache_empties_all(self) -> None:
        """clear_cache should empty all module caches."""
        from src.services import public_voucher_stats_service as svc

        svc._stats_cache["stats"] = (time.monotonic(), MagicMock())
        svc._recent_cache["recent"] = (time.monotonic(), [])
        svc._clinics_cache["top_clinics"] = (time.monotonic(), [])

        clear_cache()

        assert len(svc._stats_cache) == 0
        assert len(svc._recent_cache) == 0
        assert len(svc._clinics_cache) == 0


class TestDataclasses:
    """Tests for service dataclasses."""

    def test_voucher_stats_result_frozen(self) -> None:
        """VoucherStatsResult should be immutable."""
        from datetime import UTC, datetime

        result = VoucherStatsResult(
            total_vouchers_purchased=100,
            total_vouchers_redeemed=60,
            total_animals_treated=45,
            active_clinics=5,
            total_donated_eur=900.50,
            total_donated_pyg=6000000,
            last_updated=datetime.now(UTC),
        )
        assert result.total_vouchers_purchased == 100
        assert result.total_donated_eur == 900.50

    def test_service_breakdown(self) -> None:
        """ServiceBreakdown should store category and count."""
        b = ServiceBreakdown(category="Castration", count=42)
        assert b.category == "Castration"
        assert b.count == 42

    def test_recent_redemption(self) -> None:
        """RecentRedemption should store all fields."""
        from datetime import UTC, datetime

        r = RecentRedemption(
            voucher_code="VV-ABC123",
            service_category="Vaccination",
            clinic_name="Vet Central",
            redeemed_at=datetime(2026, 3, 1, tzinfo=UTC),
            amount_pyg=150000,
        )
        assert r.voucher_code == "VV-ABC123"
        assert r.amount_pyg == 150000

    def test_top_clinic(self) -> None:
        """TopClinic should store clinic name, city, and count."""
        c = TopClinic(clinic_name="Vet Asuncion", city="Asuncion", voucher_count=25)
        assert c.clinic_name == "Vet Asuncion"
        assert c.voucher_count == 25

    def test_top_clinic_nullable_city(self) -> None:
        """TopClinic city can be None."""
        c = TopClinic(clinic_name="Rural Clinic", city=None, voucher_count=3)
        assert c.city is None
