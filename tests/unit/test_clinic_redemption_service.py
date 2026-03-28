"""Unit tests for clinic voucher redemption service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.vet_voucher import VoucherStatus
from src.services.clinic_redemption_service import (
    VoucherClinicMismatchError,
    VoucherNotAssignedError,
    get_clinic_reconciliation_summary,
    list_clinic_vouchers,
    lookup_voucher_for_redemption,
    redeem_voucher_at_clinic,
)
from src.services.vet_voucher_service import (
    VoucherCodeNotFoundError,
    VoucherExpiredError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_voucher(
    status: VoucherStatus = VoucherStatus.ASSIGNED,
    code: str = "VV-TEST1234",
    amount_pyg: int = 500_000,
    clinic_id=None,
    expires_at=None,
) -> MagicMock:
    """Create a mock VetVoucher for testing."""
    voucher = MagicMock()
    voucher.id = uuid4()
    voucher.code = code
    voucher.status = status
    voucher.amount_pyg = amount_pyg
    voucher.clinic_id = clinic_id
    voucher.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=30))
    voucher.redeemed_clinic_id = None
    voucher.redeemed_by_user_id = None
    voucher.service_id = None
    voucher.redeemed_at = None
    voucher.proof_photo_url = None
    voucher.proof_description = None
    voucher.invoice_url = None
    voucher.invoice_filename = None
    return voucher


# ---------------------------------------------------------------------------
# lookup_voucher_for_redemption
# ---------------------------------------------------------------------------


class TestLookupVoucherForRedemption:
    """Tests for voucher lookup before redemption."""

    @pytest.mark.asyncio
    async def test_returns_assigned_voucher(self) -> None:
        voucher = _make_voucher(VoucherStatus.ASSIGNED)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        result = await lookup_voucher_for_redemption(mock_db, "VV-TEST1234")
        assert result == voucher

    @pytest.mark.asyncio
    async def test_raises_for_purchased_voucher(self) -> None:
        voucher = _make_voucher(VoucherStatus.PURCHASED)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherNotAssignedError) as exc_info:
            await lookup_voucher_for_redemption(mock_db, "VV-TEST1234")
        assert "purchased" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_raises_for_redeemed_voucher(self) -> None:
        voucher = _make_voucher(VoucherStatus.REDEEMED)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherNotAssignedError):
            await lookup_voucher_for_redemption(mock_db, "VV-TEST1234")

    @pytest.mark.asyncio
    async def test_raises_for_expired_voucher(self) -> None:
        voucher = _make_voucher(
            VoucherStatus.ASSIGNED,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherExpiredError):
            await lookup_voucher_for_redemption(mock_db, "VV-TEST1234")

    @pytest.mark.asyncio
    async def test_raises_for_not_found_code(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherCodeNotFoundError):
            await lookup_voucher_for_redemption(mock_db, "VV-NOEXIST1")


# ---------------------------------------------------------------------------
# redeem_voucher_at_clinic
# ---------------------------------------------------------------------------


class TestRedeemVoucherAtClinic:
    """Tests for the full redemption flow."""

    @pytest.mark.asyncio
    async def test_successful_redemption(self) -> None:
        voucher = _make_voucher(VoucherStatus.ASSIGNED)
        clinic_id = uuid4()
        user_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        result = await redeem_voucher_at_clinic(
            mock_db,
            "VV-TEST1234",
            clinic_id=clinic_id,
            redeemed_by_user_id=user_id,
            proof_photo_url="https://storage.example.com/proof/123.jpg",
            proof_description="Performed castration surgery",
            invoice_url="https://storage.example.com/invoices/456.pdf",
            invoice_filename="invoice-march-2026.pdf",
        )

        assert result.status == VoucherStatus.REDEEMED
        assert result.redeemed_clinic_id == clinic_id
        assert result.redeemed_by_user_id == user_id
        assert result.proof_photo_url == "https://storage.example.com/proof/123.jpg"
        assert result.proof_description == "Performed castration surgery"
        assert result.invoice_url == "https://storage.example.com/invoices/456.pdf"
        assert result.invoice_filename == "invoice-march-2026.pdf"
        assert result.redeemed_at is not None
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_redemption_without_proof(self) -> None:
        """Proof fields are optional — redemption should work without them."""
        voucher = _make_voucher(VoucherStatus.ASSIGNED)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        result = await redeem_voucher_at_clinic(
            mock_db,
            "VV-TEST1234",
            clinic_id=uuid4(),
            redeemed_by_user_id=uuid4(),
        )
        assert result.status == VoucherStatus.REDEEMED
        assert result.proof_photo_url is None
        assert result.invoice_url is None

    @pytest.mark.asyncio
    async def test_redemption_with_service_id(self) -> None:
        voucher = _make_voucher(VoucherStatus.ASSIGNED)
        service_id = uuid4()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        result = await redeem_voucher_at_clinic(
            mock_db,
            "VV-TEST1234",
            clinic_id=uuid4(),
            redeemed_by_user_id=uuid4(),
            service_id=service_id,
        )
        assert result.service_id == service_id

    @pytest.mark.asyncio
    async def test_clinic_restriction_mismatch(self) -> None:
        restricted_clinic = uuid4()
        wrong_clinic = uuid4()
        voucher = _make_voucher(VoucherStatus.ASSIGNED, clinic_id=restricted_clinic)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherClinicMismatchError) as exc_info:
            await redeem_voucher_at_clinic(
                mock_db,
                "VV-TEST1234",
                clinic_id=wrong_clinic,
                redeemed_by_user_id=uuid4(),
            )
        assert str(restricted_clinic) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_clinic_restriction_match_succeeds(self) -> None:
        clinic_id = uuid4()
        voucher = _make_voucher(VoucherStatus.ASSIGNED, clinic_id=clinic_id)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        result = await redeem_voucher_at_clinic(
            mock_db,
            "VV-TEST1234",
            clinic_id=clinic_id,
            redeemed_by_user_id=uuid4(),
        )
        assert result.status == VoucherStatus.REDEEMED

    @pytest.mark.asyncio
    async def test_expired_voucher_cannot_be_redeemed(self) -> None:
        voucher = _make_voucher(
            VoucherStatus.ASSIGNED,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        mock_db.execute.return_value = mock_result

        with pytest.raises(VoucherExpiredError):
            await redeem_voucher_at_clinic(
                mock_db,
                "VV-TEST1234",
                clinic_id=uuid4(),
                redeemed_by_user_id=uuid4(),
            )


# ---------------------------------------------------------------------------
# list_clinic_vouchers
# ---------------------------------------------------------------------------


class TestListClinicVouchers:
    """Tests for listing vouchers by clinic."""

    @pytest.mark.asyncio
    async def test_returns_vouchers_and_count(self) -> None:
        mock_db = AsyncMock()
        v1 = _make_voucher()
        v2 = _make_voucher()

        # First call: SELECT vouchers
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [v1, v2]
        mock_result.scalars.return_value = mock_scalars

        # Second call: SELECT COUNT
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        vouchers, total = await list_clinic_vouchers(mock_db, uuid4())
        assert len(vouchers) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_vouchers(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        vouchers, total = await list_clinic_vouchers(mock_db, uuid4())
        assert vouchers == []
        assert total == 0


# ---------------------------------------------------------------------------
# get_clinic_reconciliation_summary
# ---------------------------------------------------------------------------


class TestGetClinicReconciliationSummary:
    """Tests for monthly reconciliation summary."""

    @pytest.mark.asyncio
    async def test_returns_summary_for_month(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_redeemed = 5
        mock_row.total_amount_pyg = 2_500_000
        mock_result.one.return_value = mock_row
        mock_db.execute.return_value = mock_result

        clinic_id = uuid4()
        summary = await get_clinic_reconciliation_summary(mock_db, clinic_id, month=3, year=2026)

        assert summary["total_redeemed"] == 5
        assert summary["total_amount_pyg"] == 2_500_000
        assert summary["month"] == 3
        assert summary["year"] == 2026
        assert summary["clinic_id"] == str(clinic_id)

    @pytest.mark.asyncio
    async def test_defaults_to_current_month(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_redeemed = 0
        mock_row.total_amount_pyg = 0
        mock_result.one.return_value = mock_row
        mock_db.execute.return_value = mock_result

        now = datetime.now(UTC)
        summary = await get_clinic_reconciliation_summary(mock_db, uuid4())
        assert summary["month"] == now.month
        assert summary["year"] == now.year

    @pytest.mark.asyncio
    async def test_zero_when_no_redemptions(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_redeemed = 0
        mock_row.total_amount_pyg = 0
        mock_result.one.return_value = mock_row
        mock_db.execute.return_value = mock_result

        summary = await get_clinic_reconciliation_summary(mock_db, uuid4(), month=1, year=2026)
        assert summary["total_redeemed"] == 0
        assert summary["total_amount_pyg"] == 0


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------


class TestVoucherNotAssignedError:
    """Tests for VoucherNotAssignedError."""

    def test_message_includes_status(self) -> None:
        err = VoucherNotAssignedError("VV-ABC123", "purchased")
        assert "purchased" in err.message
        assert "VV-ABC123" in err.message
        assert "assigned" in err.message.lower()

    def test_stores_code_and_status(self) -> None:
        err = VoucherNotAssignedError("VV-XYZ", "redeemed")
        assert err.code == "VV-XYZ"
        assert err.status == "redeemed"


class TestVoucherClinicMismatchError:
    """Tests for VoucherClinicMismatchError."""

    def test_message_includes_both_clinics(self) -> None:
        restricted = uuid4()
        attempted = uuid4()
        err = VoucherClinicMismatchError("VV-TEST", restricted, attempted)
        assert str(restricted) in err.message
        assert str(attempted) in err.message

    def test_stores_all_fields(self) -> None:
        restricted = uuid4()
        attempted = uuid4()
        err = VoucherClinicMismatchError("VV-CODE", restricted, attempted)
        assert err.code == "VV-CODE"
        assert err.restricted_clinic_id == restricted
        assert err.attempted_clinic_id == attempted
