"""Unit tests for the vet voucher service layer."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.vet_voucher import VALID_VOUCHER_TRANSITIONS, VoucherStatus
from src.services.vet_voucher_service import (
    InvalidVoucherTransitionError,
    VoucherCodeNotFoundError,
    VoucherExpiredError,
    VoucherNotFoundError,
    assign_voucher,
    cancel_voucher,
    create_voucher,
    expire_voucher,
    generate_voucher_code,
    get_voucher,
    get_voucher_by_code,
    redeem_voucher,
)


class TestVoucherCodeGeneration:
    """Tests for voucher code generation."""

    def test_code_has_prefix(self) -> None:
        code = generate_voucher_code()
        assert code.startswith("VV-")

    def test_code_is_correct_length(self) -> None:
        code = generate_voucher_code()
        # VV- prefix + 8 chars = 11 total
        assert len(code) == 11

    def test_codes_are_unique(self) -> None:
        codes = {generate_voucher_code() for _ in range(100)}
        assert len(codes) == 100

    def test_code_contains_no_ambiguous_chars(self) -> None:
        for _ in range(50):
            code = generate_voucher_code()
            random_part = code[3:]  # Remove VV- prefix
            assert "O" not in random_part
            assert "I" not in random_part
            assert "0" not in random_part
            assert "1" not in random_part


class TestStatusTransitions:
    """Tests for voucher status transition rules."""

    def test_purchased_can_be_assigned(self) -> None:
        assert VoucherStatus.ASSIGNED in VALID_VOUCHER_TRANSITIONS[VoucherStatus.PURCHASED]

    def test_purchased_can_be_cancelled(self) -> None:
        assert VoucherStatus.CANCELLED in VALID_VOUCHER_TRANSITIONS[VoucherStatus.PURCHASED]

    def test_purchased_can_expire(self) -> None:
        assert VoucherStatus.EXPIRED in VALID_VOUCHER_TRANSITIONS[VoucherStatus.PURCHASED]

    def test_assigned_can_be_redeemed(self) -> None:
        assert VoucherStatus.REDEEMED in VALID_VOUCHER_TRANSITIONS[VoucherStatus.ASSIGNED]

    def test_assigned_can_be_cancelled(self) -> None:
        assert VoucherStatus.CANCELLED in VALID_VOUCHER_TRANSITIONS[VoucherStatus.ASSIGNED]

    def test_redeemed_is_terminal(self) -> None:
        assert len(VALID_VOUCHER_TRANSITIONS[VoucherStatus.REDEEMED]) == 0

    def test_expired_is_terminal(self) -> None:
        assert len(VALID_VOUCHER_TRANSITIONS[VoucherStatus.EXPIRED]) == 0

    def test_cancelled_is_terminal(self) -> None:
        assert len(VALID_VOUCHER_TRANSITIONS[VoucherStatus.CANCELLED]) == 0


class TestCreateVoucher:
    """Tests for voucher creation."""

    @pytest.mark.asyncio()
    async def test_creates_voucher_with_code(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        data = {
            "amount_pyg": 500000,
            "expires_at": datetime.now(UTC) + timedelta(days=90),
        }

        await create_voucher(db, data)
        assert db.add.called
        assert db.flush.called


class TestGetVoucher:
    """Tests for fetching vouchers."""

    @pytest.mark.asyncio()
    async def test_returns_voucher_when_found(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        db.get.return_value = mock_voucher

        result = await get_voucher(db, uuid4())
        assert result == mock_voucher

    @pytest.mark.asyncio()
    async def test_raises_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(VoucherNotFoundError):
            await get_voucher(db, uuid4())

    @pytest.mark.asyncio()
    async def test_get_by_code_returns_voucher(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_voucher
        db.execute.return_value = mock_result

        result = await get_voucher_by_code(db, "VV-ABCD1234")
        assert result == mock_voucher

    @pytest.mark.asyncio()
    async def test_get_by_code_raises_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(VoucherCodeNotFoundError, match="VV-NOTFOUND"):
            await get_voucher_by_code(db, "VV-NOTFOUND")


class TestAssignVoucher:
    """Tests for voucher assignment."""

    @pytest.mark.asyncio()
    async def test_assigns_purchased_voucher(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.PURCHASED
        mock_voucher.expires_at = datetime.now(UTC) + timedelta(days=30)
        db.get.return_value = mock_voucher

        beneficiary_id = uuid4()
        result = await assign_voucher(db, uuid4(), beneficiary_id)
        assert result.status == VoucherStatus.ASSIGNED
        assert result.beneficiary_id == beneficiary_id
        assert result.assigned_at is not None

    @pytest.mark.asyncio()
    async def test_rejects_assigning_redeemed_voucher(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.REDEEMED
        db.get.return_value = mock_voucher

        with pytest.raises(InvalidVoucherTransitionError, match="Cannot transition"):
            await assign_voucher(db, uuid4(), uuid4())

    @pytest.mark.asyncio()
    async def test_rejects_assigning_expired_voucher(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.PURCHASED
        mock_voucher.expires_at = datetime.now(UTC) - timedelta(days=1)
        mock_voucher.id = uuid4()
        db.get.return_value = mock_voucher

        with pytest.raises(VoucherExpiredError):
            await assign_voucher(db, mock_voucher.id, uuid4())


class TestRedeemVoucher:
    """Tests for voucher redemption."""

    @pytest.mark.asyncio()
    async def test_redeems_assigned_voucher(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        clinic_id = uuid4()
        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.ASSIGNED
        mock_voucher.expires_at = datetime.now(UTC) + timedelta(days=30)
        mock_voucher.clinic_id = None
        db.get.return_value = mock_voucher

        result = await redeem_voucher(db, uuid4(), clinic_id)
        assert result.status == VoucherStatus.REDEEMED
        assert result.redeemed_clinic_id == clinic_id
        assert result.redeemed_at is not None

    @pytest.mark.asyncio()
    async def test_rejects_redeem_at_wrong_clinic(self) -> None:
        db = AsyncMock()
        restricted_clinic = uuid4()
        wrong_clinic = uuid4()

        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.ASSIGNED
        mock_voucher.expires_at = datetime.now(UTC) + timedelta(days=30)
        mock_voucher.clinic_id = restricted_clinic
        db.get.return_value = mock_voucher

        with pytest.raises(InvalidVoucherTransitionError, match="restricted"):
            await redeem_voucher(db, uuid4(), wrong_clinic)

    @pytest.mark.asyncio()
    async def test_rejects_redeeming_purchased_voucher(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.PURCHASED
        db.get.return_value = mock_voucher

        with pytest.raises(InvalidVoucherTransitionError):
            await redeem_voucher(db, uuid4(), uuid4())


class TestCancelVoucher:
    """Tests for voucher cancellation."""

    @pytest.mark.asyncio()
    async def test_cancels_purchased_voucher(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.PURCHASED
        db.get.return_value = mock_voucher

        result = await cancel_voucher(db, uuid4(), "Donor requested refund")
        assert result.status == VoucherStatus.CANCELLED
        assert result.cancellation_reason == "Donor requested refund"
        assert result.cancelled_at is not None

    @pytest.mark.asyncio()
    async def test_rejects_cancelling_redeemed_voucher(self) -> None:
        db = AsyncMock()
        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.REDEEMED
        db.get.return_value = mock_voucher

        with pytest.raises(InvalidVoucherTransitionError):
            await cancel_voucher(db, uuid4(), "Too late")


class TestExpireVoucher:
    """Tests for voucher expiry."""

    @pytest.mark.asyncio()
    async def test_expires_purchased_voucher(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_voucher = MagicMock()
        mock_voucher.status = VoucherStatus.PURCHASED
        db.get.return_value = mock_voucher

        result = await expire_voucher(db, uuid4())
        assert result.status == VoucherStatus.EXPIRED


class TestSchemaValidation:
    """Tests for voucher schemas."""

    def test_voucher_create_rejects_zero_amount(self) -> None:
        from pydantic import ValidationError
        from src.schemas.vet_voucher import VetVoucherCreate

        with pytest.raises(ValidationError, match="amount_pyg"):
            VetVoucherCreate(
                amount_pyg=0,
                expires_at=datetime.now(UTC) + timedelta(days=90),
            )

    def test_voucher_create_valid(self) -> None:
        from src.schemas.vet_voucher import VetVoucherCreate

        voucher = VetVoucherCreate(
            amount_pyg=500000,
            amount_eur=70.00,
            expires_at=datetime.now(UTC) + timedelta(days=90),
        )
        assert voucher.amount_pyg == 500000
        assert voucher.amount_eur == 70.00

    def test_voucher_cancel_requires_reason(self) -> None:
        from pydantic import ValidationError
        from src.schemas.vet_voucher import VetVoucherCancel

        with pytest.raises(ValidationError, match="reason"):
            VetVoucherCancel(reason="")


class TestExceptionMessages:
    """Tests for exception attributes."""

    def test_voucher_not_found_message(self) -> None:
        vid = uuid4()
        err = VoucherNotFoundError(vid)
        assert err.voucher_id == vid
        assert str(vid) in err.message

    def test_code_not_found_message(self) -> None:
        err = VoucherCodeNotFoundError("VV-MISSING")
        assert err.code == "VV-MISSING"
        assert "VV-MISSING" in err.message

    def test_invalid_transition_message(self) -> None:
        err = InvalidVoucherTransitionError("redeemed", "assigned")
        assert "redeemed" in err.message
        assert "none (terminal state)" in err.message

    def test_expired_message(self) -> None:
        vid = uuid4()
        err = VoucherExpiredError(vid)
        assert str(vid) in err.message
