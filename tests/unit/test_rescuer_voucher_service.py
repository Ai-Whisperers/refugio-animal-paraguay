"""Unit tests for rescuer voucher wallet and claim service.

Tests voucher discovery, claim flow, wallet listing, and summary.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.vet_voucher import VetVoucher, VoucherStatus
from src.services.rescuer_voucher_service import (
    DEFAULT_DISCOVERY_RADIUS_KM,
    DEFAULT_PAGE_SIZE,
    VoucherAlreadyClaimedError,
    VoucherClaimRequest,
    VoucherClaimResult,
    VoucherNotClaimableError,
    claim_voucher,
    get_available_vouchers,
    get_rescuer_wallet,
    get_rescuer_wallet_summary,
)
from src.services.vet_voucher_service import VoucherCodeNotFoundError, VoucherExpiredError

# --- Helpers ---


def _make_voucher(**overrides) -> MagicMock:
    """Create a mock VetVoucher with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "code": "VV-TEST1234",
        "amount_pyg": 500000,
        "amount_eur": 10.00,
        "donor_id": uuid4(),
        "beneficiary_id": None,
        "clinic_id": None,
        "redeemed_clinic_id": None,
        "service_id": None,
        "service_category": "sterilization",
        "status": VoucherStatus.PURCHASED,
        "purchased_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC) + timedelta(days=30),
        "assigned_at": None,
        "redeemed_at": None,
        "cancelled_at": None,
        "notes": None,
        "cancellation_reason": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    voucher = MagicMock(spec=VetVoucher)
    for k, v in defaults.items():
        setattr(voucher, k, v)
    return voucher


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


# --- Constants Tests ---


class TestConstants:
    """Tests for service-level constants."""

    def test_default_radius(self) -> None:
        assert DEFAULT_DISCOVERY_RADIUS_KM == 100

    def test_default_page_size(self) -> None:
        assert DEFAULT_PAGE_SIZE == 10


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exception classes."""

    def test_voucher_already_claimed_error(self) -> None:
        error = VoucherAlreadyClaimedError("VV-TEST1234")
        assert error.code == "VV-TEST1234"
        assert "already been claimed" in error.message

    def test_voucher_not_claimable_error(self) -> None:
        error = VoucherNotClaimableError("VV-TEST1234", "redeemed")
        assert error.code == "VV-TEST1234"
        assert error.status == "redeemed"
        assert "purchased" in error.message

    def test_exceptions_are_exceptions(self) -> None:
        assert isinstance(VoucherAlreadyClaimedError("X"), Exception)
        assert isinstance(VoucherNotClaimableError("X", "Y"), Exception)


# --- VoucherClaimRequest Tests ---


class TestVoucherClaimRequest:
    """Tests for claim request dataclass."""

    def test_required_fields(self) -> None:
        rescuer_id = uuid4()
        req = VoucherClaimRequest(rescuer_id=rescuer_id)
        assert req.rescuer_id == rescuer_id
        assert req.animal_id is None
        assert req.note is None

    def test_all_fields(self) -> None:
        rescuer_id = uuid4()
        animal_id = uuid4()
        req = VoucherClaimRequest(
            rescuer_id=rescuer_id,
            animal_id=animal_id,
            note="For wound treatment",
        )
        assert req.animal_id == animal_id
        assert req.note == "For wound treatment"


# --- get_available_vouchers ---


class TestGetAvailableVouchers:
    """Tests for available voucher discovery."""

    @pytest.mark.asyncio
    async def test_returns_purchased_vouchers(self) -> None:
        db = _mock_db()
        vouchers = [_make_voucher(), _make_voucher()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = vouchers
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2
        db.execute.side_effect = [mock_result, mock_count_result]

        result, total = await get_available_vouchers(db)

        assert len(result) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_returns_empty_when_none_available(self) -> None:
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        db.execute.side_effect = [mock_result, mock_count_result]

        result, total = await get_available_vouchers(db)

        assert result == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_respects_pagination(self) -> None:
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        db.execute.side_effect = [mock_result, mock_count_result]

        await get_available_vouchers(db, page=2, page_size=5)

        assert db.execute.await_count == 2


# --- claim_voucher ---


class TestClaimVoucher:
    """Tests for voucher claim flow."""

    @pytest.mark.asyncio
    async def test_successful_claim(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status=VoucherStatus.PURCHASED)
        rescuer_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        claim_req = VoucherClaimRequest(rescuer_id=rescuer_id)
        result = await claim_voucher(db, voucher.code, claim_req)

        assert isinstance(result, VoucherClaimResult)
        assert voucher.status == VoucherStatus.ASSIGNED
        assert voucher.beneficiary_id == rescuer_id
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_claim_sets_note(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status=VoucherStatus.PURCHASED)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        claim_req = VoucherClaimRequest(
            rescuer_id=uuid4(),
            note="For surgical wound treatment",
        )
        await claim_voucher(db, voucher.code, claim_req)

        assert voucher.notes == "For surgical wound treatment"

    @pytest.mark.asyncio
    async def test_claim_not_found_raises(self) -> None:
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(VoucherCodeNotFoundError):
            await claim_voucher(
                db,
                "VV-NOTFOUND",
                VoucherClaimRequest(rescuer_id=uuid4()),
            )

    @pytest.mark.asyncio
    async def test_claim_expired_raises(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(
            status=VoucherStatus.PURCHASED,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        with pytest.raises(VoucherExpiredError):
            await claim_voucher(
                db,
                voucher.code,
                VoucherClaimRequest(rescuer_id=uuid4()),
            )

    @pytest.mark.asyncio
    async def test_claim_already_assigned_raises(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status=VoucherStatus.ASSIGNED)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        with pytest.raises(VoucherAlreadyClaimedError):
            await claim_voucher(
                db,
                voucher.code,
                VoucherClaimRequest(rescuer_id=uuid4()),
            )

    @pytest.mark.asyncio
    async def test_claim_redeemed_raises_not_claimable(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status=VoucherStatus.REDEEMED)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        with pytest.raises(VoucherNotClaimableError):
            await claim_voucher(
                db,
                voucher.code,
                VoucherClaimRequest(rescuer_id=uuid4()),
            )

    @pytest.mark.asyncio
    async def test_claim_cancelled_raises_not_claimable(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status=VoucherStatus.CANCELLED)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = voucher
        db.execute.return_value = mock_result

        with pytest.raises(VoucherNotClaimableError):
            await claim_voucher(
                db,
                voucher.code,
                VoucherClaimRequest(rescuer_id=uuid4()),
            )


# --- get_rescuer_wallet ---


class TestGetRescuerWallet:
    """Tests for rescuer wallet listing."""

    @pytest.mark.asyncio
    async def test_returns_assigned_and_redeemed(self) -> None:
        db = _mock_db()
        rescuer_id = uuid4()
        vouchers = [
            _make_voucher(beneficiary_id=rescuer_id, status=VoucherStatus.ASSIGNED),
            _make_voucher(beneficiary_id=rescuer_id, status=VoucherStatus.REDEEMED),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = vouchers
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2
        db.execute.side_effect = [mock_result, mock_count_result]

        result, total = await get_rescuer_wallet(db, rescuer_id)

        assert len(result) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_empty_wallet(self) -> None:
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        db.execute.side_effect = [mock_result, mock_count_result]

        result, total = await get_rescuer_wallet(db, uuid4())

        assert result == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_filter_by_status(self) -> None:
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        db.execute.side_effect = [mock_result, mock_count_result]

        await get_rescuer_wallet(db, uuid4(), status_filter="assigned")

        assert db.execute.await_count == 2


# --- get_rescuer_wallet_summary ---


class TestGetRescuerWalletSummary:
    """Tests for wallet summary counts."""

    @pytest.mark.asyncio
    async def test_returns_counts(self) -> None:
        db = _mock_db()

        mock_claimed = MagicMock()
        mock_claimed.scalar_one.return_value = 3
        mock_redeemed = MagicMock()
        mock_redeemed.scalar_one.return_value = 1
        db.execute.side_effect = [mock_claimed, mock_redeemed]

        summary = await get_rescuer_wallet_summary(db, uuid4())

        assert summary["claimed"] == 3
        assert summary["redeemed"] == 1

    @pytest.mark.asyncio
    async def test_zero_counts(self) -> None:
        db = _mock_db()

        mock_claimed = MagicMock()
        mock_claimed.scalar_one.return_value = 0
        mock_redeemed = MagicMock()
        mock_redeemed.scalar_one.return_value = 0
        db.execute.side_effect = [mock_claimed, mock_redeemed]

        summary = await get_rescuer_wallet_summary(db, uuid4())

        assert summary["claimed"] == 0
        assert summary["redeemed"] == 0
