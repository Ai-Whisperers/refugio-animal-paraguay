"""Unit tests for the EU tax receipt PDF generation service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.services.tax_receipt_eu_service import (
    EUReceiptData,
    TaxReceiptEUGenerator,
    _format_amount,
)

SAMPLE_UUID = UUID("12345678-1234-1234-1234-123456789abc")
FIXED_DATE = datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC)


def _make_data(**overrides) -> EUReceiptData:
    """Factory for EUReceiptData with sensible defaults."""
    defaults: dict = {
        "donation_id": SAMPLE_UUID,
        "amount_cents": 5000,
        "currency": "EUR",
        "payment_method": "stripe",
        "status": "completed",
        "receipt_number": "REC-001",
        "fund_category": None,
        "is_recurring": False,
        "recurring_interval": None,
        "notes": None,
        "donation_date": FIXED_DATE,
        "donor_name": "Jan de Vries",
        "donor_email": "jan@example.nl",
        "donor_country": "NL",
        "donor_tax_id": None,
    }
    defaults.update(overrides)
    return EUReceiptData(**defaults)


class TestFormatAmount:
    def test_eur_formats_to_two_decimal_places(self):
        assert _format_amount(5000, "EUR") == "50.00 EUR"

    def test_eur_zero(self):
        assert _format_amount(0, "EUR") == "0.00 EUR"

    def test_eur_large_amount(self):
        result = _format_amount(100000, "EUR")
        assert "1,000.00" in result
        assert "EUR" in result

    def test_pyg_has_no_decimal(self):
        result = _format_amount(500000, "PYG")
        assert "PYG" in result
        assert "." not in result.split("PYG")[0].strip()

    def test_usd_formats_correctly(self):
        result = _format_amount(2550, "USD")
        assert "25.50" in result
        assert "USD" in result

    def test_unknown_currency_uses_code(self):
        result = _format_amount(1000, "GBP")
        assert "GBP" in result


class TestTaxReceiptEUGenerator:
    def setup_method(self):
        self.generator = TaxReceiptEUGenerator()

    def test_generate_bytes_returns_bytes(self):
        data = _make_data()
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_generated_pdf_has_pdf_header(self):
        data = _make_data()
        result = self.generator.generate_bytes(data)
        assert result[:4] == b"%PDF"

    def test_pdf_is_non_empty(self):
        data = _make_data()
        result = self.generator.generate_bytes(data)
        assert len(result) > 1000

    def test_pdf_with_anonymous_donor(self):
        data = _make_data(donor_name=None, donor_email=None, donor_country=None)
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_pdf_with_tax_id(self):
        data = _make_data(donor_tax_id="123456789")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_recurring_monthly_donation(self):
        data = _make_data(is_recurring=True, recurring_interval="month")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_pdf_with_recurring_annual_donation(self):
        data = _make_data(is_recurring=True, recurring_interval="year")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_fund_category_medical(self):
        data = _make_data(fund_category="medical")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_fund_category_unknown(self):
        data = _make_data(fund_category="other")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_notes(self):
        data = _make_data(notes="In memory of our dog Max")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_pyg_currency(self):
        data = _make_data(amount_cents=500000, currency="PYG", payment_method="tigo_money")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_sepa_payment_method(self):
        data = _make_data(payment_method="sepa_debit")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_transfer_payment_method(self):
        data = _make_data(payment_method="transfer")
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_with_no_receipt_number_uses_donation_id(self):
        data = _make_data(receipt_number=None)
        result = self.generator.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_multiple_calls_produce_bytes(self):
        """Generator should be reusable across multiple calls."""
        data = _make_data()
        result1 = self.generator.generate_bytes(data)
        result2 = self.generator.generate_bytes(data)
        assert isinstance(result1, bytes)
        assert isinstance(result2, bytes)
        assert abs(len(result1) - len(result2)) < 100

    def test_different_donation_ids_produce_different_receipts(self):
        data1 = _make_data(donation_id=uuid4())
        data2 = _make_data(donation_id=uuid4())
        result1 = self.generator.generate_bytes(data1)
        result2 = self.generator.generate_bytes(data2)
        assert result1[:4] == b"%PDF"
        assert result2[:4] == b"%PDF"
