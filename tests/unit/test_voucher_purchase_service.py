"""Unit tests for voucher purchase service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.voucher_purchase_service import (
    DEFAULT_VOUCHER_VALIDITY_DAYS,
    MAX_QUANTITY,
    MIN_QUANTITY,
    ClinicServiceNotFoundError,
    InvalidQuantityError,
    VoucherPurchaseRequest,
    calculate_purchase_price,
    create_vouchers_for_purchase,
    get_donor_vouchers,
    get_service_for_purchase,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_clinic_service(
    price_pyg: int = 150_000,
    price_eur: float | None = 25.0,
    name: str = "Castration",
    category: str = "surgery",
    is_active: bool = True,
) -> MagicMock:
    """Create a mock ClinicService."""
    service = MagicMock()
    service.id = uuid4()
    service.name = name
    service.category = category
    service.price_pyg = price_pyg
    service.price_eur = price_eur
    service.is_active = is_active
    return service


# ---------------------------------------------------------------------------
# get_service_for_purchase
# ---------------------------------------------------------------------------


class TestGetServiceForPurchase:
    """Tests for fetching and validating a service for purchase."""

    @pytest.mark.asyncio
    async def test_returns_active_service(self) -> None:
        service = _make_clinic_service()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = service
        mock_db.execute.return_value = mock_result

        result = await get_service_for_purchase(mock_db, service.id)
        assert result == service

    @pytest.mark.asyncio
    async def test_raises_for_not_found_service(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ClinicServiceNotFoundError):
            await get_service_for_purchase(mock_db, uuid4())


# ---------------------------------------------------------------------------
# calculate_purchase_price
# ---------------------------------------------------------------------------


class TestCalculatePurchasePrice:
    """Tests for price calculation."""

    def test_single_voucher_price(self) -> None:
        service = _make_clinic_service(price_pyg=150_000, price_eur=25.0)
        result = calculate_purchase_price(service, 1)
        assert result.total_pyg == 150_000
        assert result.total_eur == 25.0
        assert result.quantity == 1
        assert result.unit_price_pyg == 150_000

    def test_multiple_vouchers_price(self) -> None:
        service = _make_clinic_service(price_pyg=200_000, price_eur=30.0)
        result = calculate_purchase_price(service, 5)
        assert result.total_pyg == 1_000_000
        assert result.total_eur == 150.0
        assert result.quantity == 5

    def test_price_without_eur(self) -> None:
        service = _make_clinic_service(price_pyg=100_000, price_eur=None)
        result = calculate_purchase_price(service, 3)
        assert result.total_pyg == 300_000
        assert result.total_eur is None
        assert result.unit_price_eur is None

    def test_max_quantity(self) -> None:
        service = _make_clinic_service(price_pyg=50_000)
        result = calculate_purchase_price(service, MAX_QUANTITY)
        assert result.total_pyg == 50_000 * MAX_QUANTITY
        assert result.quantity == MAX_QUANTITY

    def test_invalid_quantity_zero(self) -> None:
        service = _make_clinic_service()
        with pytest.raises(InvalidQuantityError):
            calculate_purchase_price(service, 0)

    def test_invalid_quantity_negative(self) -> None:
        service = _make_clinic_service()
        with pytest.raises(InvalidQuantityError):
            calculate_purchase_price(service, -1)

    def test_invalid_quantity_over_max(self) -> None:
        service = _make_clinic_service()
        with pytest.raises(InvalidQuantityError):
            calculate_purchase_price(service, MAX_QUANTITY + 1)

    def test_returns_service_metadata(self) -> None:
        service = _make_clinic_service(name="Vaccination", category="preventive")
        result = calculate_purchase_price(service, 1)
        assert result.service_name == "Vaccination"
        assert result.service_category == "preventive"


# ---------------------------------------------------------------------------
# create_vouchers_for_purchase
# ---------------------------------------------------------------------------


class TestCreateVouchersForPurchase:
    """Tests for voucher creation from a purchase."""

    @pytest.mark.asyncio
    async def test_creates_single_voucher(self) -> None:
        service = _make_clinic_service(price_pyg=150_000, price_eur=25.0)
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=1,
            payment_method="stripe",
        )

        mock_db = AsyncMock()

        result = await create_vouchers_for_purchase(mock_db, request, service)
        assert result.quantity == 1
        assert len(result.voucher_codes) == 1
        assert len(result.voucher_ids) == 1
        assert result.total_pyg == 150_000
        assert result.total_eur == 25.0
        assert result.service_name == "Castration"
        assert all(code.startswith("VV-") for code in result.voucher_codes)

    @pytest.mark.asyncio
    async def test_creates_multiple_vouchers(self) -> None:
        service = _make_clinic_service(price_pyg=100_000)
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=5,
            payment_method="sepa",
        )

        mock_db = AsyncMock()

        result = await create_vouchers_for_purchase(mock_db, request, service)
        assert result.quantity == 5
        assert len(result.voucher_codes) == 5
        assert len(result.voucher_ids) == 5
        assert result.total_pyg == 500_000
        # All codes should be unique
        assert len(set(result.voucher_codes)) == 5

    @pytest.mark.asyncio
    async def test_voucher_expiry_defaults_to_90_days(self) -> None:
        service = _make_clinic_service()
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=1,
            payment_method="stripe",
        )

        mock_db = AsyncMock()
        result = await create_vouchers_for_purchase(mock_db, request, service)

        now = datetime.now(UTC)
        expected_expiry = now + timedelta(days=DEFAULT_VOUCHER_VALIDITY_DAYS)
        # Allow 5 seconds tolerance
        assert abs((result.expires_at - expected_expiry).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_custom_validity_days(self) -> None:
        service = _make_clinic_service()
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=1,
            payment_method="stripe",
            validity_days=180,
        )

        mock_db = AsyncMock()
        result = await create_vouchers_for_purchase(mock_db, request, service)

        now = datetime.now(UTC)
        expected_expiry = now + timedelta(days=180)
        assert abs((result.expires_at - expected_expiry).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_invalid_quantity_raises_error(self) -> None:
        service = _make_clinic_service()
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=0,
            payment_method="stripe",
        )

        mock_db = AsyncMock()
        with pytest.raises(InvalidQuantityError):
            await create_vouchers_for_purchase(mock_db, request, service)

    @pytest.mark.asyncio
    async def test_flushes_after_each_voucher(self) -> None:
        service = _make_clinic_service()
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=3,
            payment_method="stripe",
        )

        mock_db = AsyncMock()
        await create_vouchers_for_purchase(mock_db, request, service)

        # 3 vouchers = 3 flush + 3 refresh calls
        assert mock_db.flush.await_count == 3
        assert mock_db.refresh.await_count == 3

    @pytest.mark.asyncio
    async def test_total_eur_none_when_no_eur_price(self) -> None:
        service = _make_clinic_service(price_eur=None)
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=service.id,
            quantity=2,
            payment_method="stripe",
        )

        mock_db = AsyncMock()
        result = await create_vouchers_for_purchase(mock_db, request, service)
        assert result.total_eur is None


# ---------------------------------------------------------------------------
# get_donor_vouchers
# ---------------------------------------------------------------------------


class TestGetDonorVouchers:
    """Tests for listing donor's vouchers."""

    @pytest.mark.asyncio
    async def test_returns_vouchers_and_count(self) -> None:
        mock_db = AsyncMock()
        v1 = MagicMock()
        v2 = MagicMock()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [v1, v2]
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        vouchers, total = await get_donor_vouchers(mock_db, uuid4())
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

        vouchers, total = await get_donor_vouchers(mock_db, uuid4())
        assert vouchers == []
        assert total == 0


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------


class TestClinicServiceNotFoundError:
    """Tests for ClinicServiceNotFoundError."""

    def test_message_includes_service_id(self) -> None:
        sid = uuid4()
        err = ClinicServiceNotFoundError(sid)
        assert str(sid) in err.message
        assert "not found" in err.message.lower()


class TestInvalidQuantityError:
    """Tests for InvalidQuantityError."""

    def test_message_includes_quantity(self) -> None:
        err = InvalidQuantityError(999)
        assert "999" in err.message
        assert str(MIN_QUANTITY) in err.message
        assert str(MAX_QUANTITY) in err.message


# ---------------------------------------------------------------------------
# Data class defaults
# ---------------------------------------------------------------------------


class TestVoucherPurchaseRequestDefaults:
    """Tests for VoucherPurchaseRequest default values."""

    def test_default_validity_days(self) -> None:
        request = VoucherPurchaseRequest(
            donor_id=uuid4(),
            clinic_id=uuid4(),
            service_id=uuid4(),
            quantity=1,
            payment_method="stripe",
        )
        assert request.validity_days == DEFAULT_VOUCHER_VALIDITY_DAYS
