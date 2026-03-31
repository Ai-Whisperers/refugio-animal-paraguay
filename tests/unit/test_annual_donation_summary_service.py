"""Unit tests for the annual donation summary PDF generation service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.services.annual_donation_summary_service import (
    AnnualDonationSummaryGenerator,
    AnnualSummaryData,
    DonationLineItem,
    _format_amount,
)

DONOR_UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
NOW = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
JAN = datetime(2026, 1, 10, 9, 0, 0, tzinfo=UTC)
FEB = datetime(2026, 2, 5, 12, 0, 0, tzinfo=UTC)


def _make_line(
    amount_cents=5000,
    currency="EUR",
    payment_method="stripe",
    fund_category=None,
    receipt_number=None,
) -> DonationLineItem:
    return DonationLineItem(
        donation_id=uuid4(),
        date=JAN,
        amount_cents=amount_cents,
        currency=currency,
        payment_method=payment_method,
        fund_category=fund_category,
        receipt_number=receipt_number,
    )


def _make_summary(**overrides) -> AnnualSummaryData:
    defaults: dict = {
        "donor_id": DONOR_UUID,
        "donor_name": "Jan de Vries",
        "donor_email": "jan@example.nl",
        "donor_country": "NL",
        "year": 2026,
        "donations": [_make_line()],
        "totals_by_currency": {"EUR": 5000},
        "generated_at": NOW,
    }
    defaults.update(overrides)
    return AnnualSummaryData(**defaults)


class TestFormatAmount:
    def test_eur_two_decimals(self):
        assert "50.00" in _format_amount(5000, "EUR")
        assert "EUR" in _format_amount(5000, "EUR")

    def test_pyg_no_decimal(self):
        result = _format_amount(200000, "PYG")
        assert "PYG" in result
        assert "." not in result.split("PYG")[0].strip()

    def test_zero_eur(self):
        assert "0.00" in _format_amount(0, "EUR")


class TestAnnualDonationSummaryGenerator:
    def setup_method(self):
        self.gen = AnnualDonationSummaryGenerator()

    def test_returns_bytes(self):
        data = _make_summary()
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_pdf_header(self):
        data = _make_summary()
        result = self.gen.generate_bytes(data)
        assert result[:4] == b"%PDF"

    def test_pdf_non_empty(self):
        data = _make_summary()
        result = self.gen.generate_bytes(data)
        assert len(result) > 1000

    def test_no_donations(self):
        data = _make_summary(donations=[], totals_by_currency={})
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_multiple_donations(self):
        donations = [
            _make_line(amount_cents=5000, currency="EUR"),
            _make_line(amount_cents=10000, currency="EUR"),
            _make_line(amount_cents=300000, currency="PYG", payment_method="tigo_money"),
        ]
        data = _make_summary(
            donations=donations,
            totals_by_currency={"EUR": 15000, "PYG": 300000},
        )
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_no_country(self):
        data = _make_summary(donor_country=None)
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_donation_with_receipt_number(self):
        line = _make_line(receipt_number="REC-2026-001")
        data = _make_summary(donations=[line])
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_donation_with_fund_category(self):
        line = _make_line(fund_category="medical")
        data = _make_summary(donations=[line])
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_many_donations_pagination(self):
        """Many donations should not raise - PDF auto-paginates."""
        donations = [_make_line(amount_cents=1000 * i) for i in range(1, 31)]
        total = sum(d.amount_cents for d in donations)
        data = _make_summary(donations=donations, totals_by_currency={"EUR": total})
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_sepa_payment_method(self):
        line = _make_line(payment_method="sepa_debit")
        data = _make_summary(donations=[line])
        result = self.gen.generate_bytes(data)
        assert isinstance(result, bytes)

    def test_multiple_currencies_in_totals(self):
        donations = [
            _make_line(5000, "EUR"),
            _make_line(200000, "PYG", "tigo_money"),
        ]
        data = _make_summary(
            donations=donations,
            totals_by_currency={"EUR": 5000, "PYG": 200000},
        )
        result = self.gen.generate_bytes(data)
        assert result[:4] == b"%PDF"
