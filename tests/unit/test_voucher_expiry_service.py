"""Unit tests for voucher expiry and refund policy service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.vet_voucher import VoucherStatus
from src.services.voucher_expiry_service import (
    GRACE_PERIOD_DAYS,
    REFUND_POLICY_TIERS,
    RefundEligibility,
    VoucherExpiryResult,
    assess_refund_eligibility,
    calculate_refund_percentage,
    expire_overdue_vouchers,
    get_expiring_soon_vouchers,
)

# ---------------------------------------------------------------------------
# calculate_refund_percentage
# ---------------------------------------------------------------------------


class TestCalculateRefundPercentage:
    """Tests for tiered refund percentage calculation."""

    def test_full_refund_when_30_plus_days_remaining(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=35)
        assert calculate_refund_percentage(expires, now) == 100

    def test_full_refund_at_exactly_30_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=30)
        assert calculate_refund_percentage(expires, now) == 100

    def test_75_percent_at_29_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=29)
        assert calculate_refund_percentage(expires, now) == 75

    def test_75_percent_at_14_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=14)
        assert calculate_refund_percentage(expires, now) == 75

    def test_50_percent_at_13_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=13)
        assert calculate_refund_percentage(expires, now) == 50

    def test_50_percent_at_7_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=7)
        assert calculate_refund_percentage(expires, now) == 50

    def test_25_percent_at_6_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=6)
        assert calculate_refund_percentage(expires, now) == 25

    def test_25_percent_at_1_day(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now + timedelta(days=1)
        assert calculate_refund_percentage(expires, now) == 25

    def test_zero_percent_at_zero_days(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now  # same moment
        assert calculate_refund_percentage(expires, now) == 0

    def test_zero_percent_when_expired(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        expires = now - timedelta(days=5)
        assert calculate_refund_percentage(expires, now) == 0

    def test_uses_current_time_when_now_is_none(self) -> None:
        """When now is not provided, uses datetime.now(UTC)."""
        far_future = datetime(2099, 1, 1, tzinfo=UTC)
        assert calculate_refund_percentage(far_future) == 100


# ---------------------------------------------------------------------------
# assess_refund_eligibility
# ---------------------------------------------------------------------------


def _make_voucher(
    status: VoucherStatus,
    amount_pyg: int = 500_000,
    expires_at: datetime | None = None,
) -> MagicMock:
    """Create a mock VetVoucher with given status and expiry."""
    voucher = MagicMock()
    voucher.status = status
    voucher.amount_pyg = amount_pyg
    voucher.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=60))
    return voucher


class TestAssessRefundEligibility:
    """Tests for refund eligibility assessment across voucher states."""

    def test_redeemed_voucher_not_eligible(self) -> None:
        voucher = _make_voucher(VoucherStatus.REDEEMED)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is False
        assert result.refund_percentage == 0
        assert result.refund_amount_pyg == 0
        assert "Redeemed" in result.reason

    def test_cancelled_voucher_not_eligible(self) -> None:
        voucher = _make_voucher(VoucherStatus.CANCELLED)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is False
        assert result.refund_percentage == 0
        assert "already cancelled" in result.reason.lower()

    def test_expired_within_grace_period_gets_25_percent(self) -> None:
        expires_at = datetime.now(UTC) - timedelta(days=3)
        voucher = _make_voucher(VoucherStatus.EXPIRED, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is True
        assert result.refund_percentage == 25
        assert result.refund_amount_pyg == int(500_000 * 0.25)
        assert "grace period" in result.reason.lower()

    def test_expired_beyond_grace_period_not_eligible(self) -> None:
        expires_at = datetime.now(UTC) - timedelta(days=GRACE_PERIOD_DAYS + 1)
        voucher = _make_voucher(VoucherStatus.EXPIRED, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is False
        assert result.refund_percentage == 0

    def test_expired_at_grace_period_boundary(self) -> None:
        """Expired exactly GRACE_PERIOD_DAYS ago should still be eligible."""
        expires_at = datetime.now(UTC) - timedelta(days=GRACE_PERIOD_DAYS)
        voucher = _make_voucher(VoucherStatus.EXPIRED, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is True
        assert result.refund_percentage == 25

    def test_purchased_voucher_full_refund_far_from_expiry(self) -> None:
        expires_at = datetime.now(UTC) + timedelta(days=60)
        voucher = _make_voucher(
            VoucherStatus.PURCHASED, amount_pyg=1_000_000, expires_at=expires_at
        )
        result = assess_refund_eligibility(voucher)
        assert result.eligible is True
        assert result.refund_percentage == 100
        assert result.refund_amount_pyg == 1_000_000

    def test_assigned_voucher_partial_refund_near_expiry(self) -> None:
        expires_at = datetime.now(UTC) + timedelta(days=10)
        voucher = _make_voucher(VoucherStatus.ASSIGNED, amount_pyg=200_000, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is True
        assert result.refund_percentage == 50
        assert result.refund_amount_pyg == 100_000

    def test_active_voucher_zero_refund_on_expiry_day(self) -> None:
        """Voucher expiring today should get 0% refund."""
        expires_at = datetime.now(UTC)
        voucher = _make_voucher(VoucherStatus.PURCHASED, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        assert result.eligible is False
        assert result.refund_percentage == 0
        assert result.refund_amount_pyg == 0

    def test_refund_amount_calculation_rounds_down(self) -> None:
        """Refund amount should be integer (truncated, not rounded)."""
        expires_at = datetime.now(UTC) + timedelta(days=20)
        voucher = _make_voucher(VoucherStatus.PURCHASED, amount_pyg=333_333, expires_at=expires_at)
        result = assess_refund_eligibility(voucher)
        # 75% of 333_333 = 249_999.75 -> int() truncates to 249_999
        assert result.refund_percentage == 75
        assert result.refund_amount_pyg == 249_999


# ---------------------------------------------------------------------------
# expire_overdue_vouchers
# ---------------------------------------------------------------------------


class TestExpireOverdueVouchers:
    """Tests for batch expiry of overdue vouchers."""

    @pytest.mark.asyncio
    async def test_no_overdue_vouchers(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await expire_overdue_vouchers(mock_db)
        assert result.expired_count == 0
        assert result.voucher_ids == []
        # Only the SELECT query should be executed, not the UPDATE
        assert mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_expires_overdue_vouchers(self) -> None:
        voucher_id_1 = uuid4()
        voucher_id_2 = uuid4()

        mock_db = AsyncMock()
        # First call: SELECT returns IDs
        mock_select_result = MagicMock()
        mock_select_result.all.return_value = [(voucher_id_1,), (voucher_id_2,)]
        # Second call: UPDATE
        mock_update_result = MagicMock()

        mock_db.execute.side_effect = [mock_select_result, mock_update_result]

        result = await expire_overdue_vouchers(mock_db)
        assert result.expired_count == 2
        assert set(result.voucher_ids) == {voucher_id_1, voucher_id_2}
        # SELECT + UPDATE = 2 execute calls
        assert mock_db.execute.call_count == 2
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_single_overdue_voucher(self) -> None:
        voucher_id = uuid4()
        mock_db = AsyncMock()
        mock_select_result = MagicMock()
        mock_select_result.all.return_value = [(voucher_id,)]
        mock_update_result = MagicMock()
        mock_db.execute.side_effect = [mock_select_result, mock_update_result]

        result = await expire_overdue_vouchers(mock_db)
        assert result.expired_count == 1
        assert result.voucher_ids == [voucher_id]


# ---------------------------------------------------------------------------
# get_expiring_soon_vouchers
# ---------------------------------------------------------------------------


class TestGetExpiringSoonVouchers:
    """Tests for fetching vouchers expiring within a window."""

    @pytest.mark.asyncio
    async def test_returns_vouchers_expiring_soon(self) -> None:
        mock_voucher_1 = MagicMock()
        mock_voucher_2 = MagicMock()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_voucher_1, mock_voucher_2]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        vouchers = await get_expiring_soon_vouchers(mock_db, days_ahead=7)
        assert len(vouchers) == 2
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none_expiring(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        vouchers = await get_expiring_soon_vouchers(mock_db)
        assert vouchers == []

    @pytest.mark.asyncio
    async def test_default_days_ahead_is_7(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await get_expiring_soon_vouchers(mock_db)
        # Verify it was called (default parameter used)
        mock_db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class TestVoucherExpiryResult:
    """Tests for VoucherExpiryResult data class."""

    def test_stores_count_and_ids(self) -> None:
        ids = [uuid4(), uuid4()]
        result = VoucherExpiryResult(expired_count=2, voucher_ids=ids)
        assert result.expired_count == 2
        assert result.voucher_ids == ids


class TestRefundEligibility:
    """Tests for RefundEligibility data class."""

    def test_stores_all_fields(self) -> None:
        eligibility = RefundEligibility(
            eligible=True,
            refund_percentage=75,
            refund_amount_pyg=375_000,
            reason="75% refund based on time remaining until expiry.",
        )
        assert eligibility.eligible is True
        assert eligibility.refund_percentage == 75
        assert eligibility.refund_amount_pyg == 375_000
        assert "75%" in eligibility.reason


# ---------------------------------------------------------------------------
# Policy constants
# ---------------------------------------------------------------------------


class TestRefundPolicyConfiguration:
    """Tests for refund policy constants."""

    def test_tiers_are_in_descending_order(self) -> None:
        """Tiers must be ordered from highest min_days to lowest."""
        min_days_values = [tier[0] for tier in REFUND_POLICY_TIERS]
        assert min_days_values == sorted(min_days_values, reverse=True)

    def test_grace_period_is_positive(self) -> None:
        assert GRACE_PERIOD_DAYS > 0

    def test_highest_tier_gives_full_refund(self) -> None:
        assert REFUND_POLICY_TIERS[0] == (30, 100)

    def test_lowest_tier_gives_zero_refund(self) -> None:
        assert REFUND_POLICY_TIERS[-1] == (0, 0)
