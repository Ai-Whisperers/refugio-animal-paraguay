"""Unit tests for the donation receipt PDF generation service."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.services.donation_receipt_service import (
    DonationReceiptGenerator,
    ReceiptData,
    _format_amount,
)


@pytest.fixture
def generator() -> DonationReceiptGenerator:
    """Return a fresh receipt generator."""
    return DonationReceiptGenerator()


@pytest.fixture
def sample_receipt_data() -> ReceiptData:
    """Return sample receipt data for testing."""
    return ReceiptData(
        donation_id=uuid4(),
        amount_cents=5000,
        currency="EUR",
        payment_method="stripe",
        status="completed",
        receipt_number="REC-001",
        fund_category="medical",
        is_recurring=False,
        recurring_interval=None,
        notes="Test donation",
        donation_date=datetime(2026, 3, 15, 10, 30, tzinfo=UTC),
        donor_name="Jan de Vries",
        donor_email="jan@example.nl",
        donor_country="NL",
    )


@pytest.fixture
def anonymous_receipt_data() -> ReceiptData:
    """Return receipt data for an anonymous donation."""
    return ReceiptData(
        donation_id=uuid4(),
        amount_cents=100000,
        currency="PYG",
        payment_method="cash",
        status="completed",
        receipt_number=None,
        fund_category=None,
        is_recurring=False,
        recurring_interval=None,
        notes=None,
        donation_date=datetime(2026, 3, 20, 14, 0, tzinfo=UTC),
        donor_name=None,
        donor_email=None,
        donor_country=None,
    )


@pytest.fixture
def recurring_receipt_data() -> ReceiptData:
    """Return receipt data for a recurring donation."""
    return ReceiptData(
        donation_id=uuid4(),
        amount_cents=2500,
        currency="EUR",
        payment_method="sepa_debit",
        status="completed",
        receipt_number=None,
        fund_category="food",
        is_recurring=True,
        recurring_interval="month",
        notes=None,
        donation_date=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        donor_name="Maria Garcia",
        donor_email="maria@example.es",
        donor_country="ES",
    )


class TestFormatAmount:
    """Tests for the _format_amount helper."""

    def test_eur_cents_to_readable(self) -> None:
        result = _format_amount(5000, "EUR")
        assert "50.00" in result
        assert "EUR" in result

    def test_usd_cents_to_readable(self) -> None:
        result = _format_amount(1234, "USD")
        assert "12.34" in result
        assert "USD" in result

    def test_pyg_no_decimals(self) -> None:
        result = _format_amount(100000, "PYG")
        assert "100,000" in result
        assert "PYG" in result

    def test_zero_amount(self) -> None:
        result = _format_amount(0, "EUR")
        assert "0.00" in result

    def test_large_amount(self) -> None:
        result = _format_amount(1000000, "EUR")
        assert "10,000.00" in result


class TestDonationReceiptGenerator:
    """Tests for PDF receipt generation."""

    def test_generate_bytes_returns_bytes(
        self, generator: DonationReceiptGenerator, sample_receipt_data: ReceiptData
    ) -> None:
        result = generator.generate_bytes(sample_receipt_data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_bytes_starts_with_pdf_header(
        self, generator: DonationReceiptGenerator, sample_receipt_data: ReceiptData
    ) -> None:
        result = generator.generate_bytes(sample_receipt_data)
        assert result[:5] == b"%PDF-"

    def test_anonymous_donation_receipt(
        self, generator: DonationReceiptGenerator, anonymous_receipt_data: ReceiptData
    ) -> None:
        result = generator.generate_bytes(anonymous_receipt_data)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:5] == b"%PDF-"

    def test_recurring_donation_receipt(
        self, generator: DonationReceiptGenerator, recurring_receipt_data: ReceiptData
    ) -> None:
        result = generator.generate_bytes(recurring_receipt_data)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:5] == b"%PDF-"

    def test_different_currencies_generate_valid_pdfs(
        self, generator: DonationReceiptGenerator, sample_receipt_data: ReceiptData
    ) -> None:
        for currency in ["EUR", "USD", "PYG"]:
            data = ReceiptData(
                donation_id=uuid4(),
                amount_cents=5000,
                currency=currency,
                payment_method="stripe",
                status="completed",
                receipt_number=None,
                fund_category=None,
                is_recurring=False,
                recurring_interval=None,
                notes=None,
                donation_date=datetime(2026, 1, 1, tzinfo=UTC),
                donor_name="Test Donor",
                donor_email="test@example.com",
                donor_country=None,
            )
            result = generator.generate_bytes(data)
            assert result[:5] == b"%PDF-", f"Failed for currency {currency}"

    def test_all_payment_methods_generate_valid_pdfs(
        self, generator: DonationReceiptGenerator
    ) -> None:
        methods = ["stripe", "cash", "transfer", "sepa_debit", "tigo_money"]
        for method in methods:
            data = ReceiptData(
                donation_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                payment_method=method,
                status="completed",
                receipt_number=None,
                fund_category=None,
                is_recurring=False,
                recurring_interval=None,
                notes=None,
                donation_date=datetime(2026, 1, 1, tzinfo=UTC),
                donor_name="Test",
                donor_email=None,
                donor_country=None,
            )
            result = generator.generate_bytes(data)
            assert result[:5] == b"%PDF-", f"Failed for method {method}"

    def test_all_fund_categories_generate_valid_pdfs(
        self, generator: DonationReceiptGenerator
    ) -> None:
        categories = ["medical", "food", "operations", "infrastructure", "emergency", None]
        for category in categories:
            data = ReceiptData(
                donation_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                payment_method="stripe",
                status="completed",
                receipt_number=None,
                fund_category=category,
                is_recurring=False,
                recurring_interval=None,
                notes=None,
                donation_date=datetime(2026, 1, 1, tzinfo=UTC),
                donor_name="Test",
                donor_email=None,
                donor_country=None,
            )
            result = generator.generate_bytes(data)
            assert result[:5] == b"%PDF-", f"Failed for category {category}"

    def test_receipt_with_notes(self, generator: DonationReceiptGenerator) -> None:
        data = ReceiptData(
            donation_id=uuid4(),
            amount_cents=5000,
            currency="EUR",
            payment_method="transfer",
            status="completed",
            receipt_number="REC-123",
            fund_category="medical",
            is_recurring=False,
            recurring_interval=None,
            notes="In memory of our beloved pet Max",
            donation_date=datetime(2026, 3, 1, tzinfo=UTC),
            donor_name="Test Donor",
            donor_email="test@example.com",
            donor_country="DE",
        )
        result = generator.generate_bytes(data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_receipt_yearly_recurring(self, generator: DonationReceiptGenerator) -> None:
        data = ReceiptData(
            donation_id=uuid4(),
            amount_cents=12000,
            currency="EUR",
            payment_method="sepa_debit",
            status="completed",
            receipt_number=None,
            fund_category=None,
            is_recurring=True,
            recurring_interval="year",
            notes=None,
            donation_date=datetime(2026, 1, 1, tzinfo=UTC),
            donor_name="Annual Donor",
            donor_email="annual@example.com",
            donor_country="NL",
        )
        result = generator.generate_bytes(data)
        assert result[:5] == b"%PDF-"
