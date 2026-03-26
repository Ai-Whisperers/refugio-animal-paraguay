"""Unit tests for CashDonationCreate schema."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.donation import CurrencyCode
from src.schemas.donation import CashDonationCreate


class TestCashDonationCreate:
    """Tests for the cash donation creation schema."""

    def test_minimal_valid_payload(self) -> None:
        schema = CashDonationCreate(amount_cents=50000)
        assert schema.amount_cents == 50000
        assert schema.currency == CurrencyCode.PYG
        assert schema.donor_id is None
        assert schema.receipt_number is None
        assert schema.notes is None

    def test_full_payload(self) -> None:
        donor_id = uuid4()
        schema = CashDonationCreate(
            donor_id=donor_id,
            amount_cents=100000,
            currency=CurrencyCode.PYG,
            receipt_number="REC-2026-0042",
            notes="Monthly shelter donation",
        )
        assert schema.donor_id == donor_id
        assert schema.amount_cents == 100000
        assert schema.currency == CurrencyCode.PYG
        assert schema.receipt_number == "REC-2026-0042"
        assert schema.notes == "Monthly shelter donation"

    def test_default_currency_is_pyg(self) -> None:
        schema = CashDonationCreate(amount_cents=1000)
        assert schema.currency == CurrencyCode.PYG

    def test_supports_eur_currency(self) -> None:
        schema = CashDonationCreate(amount_cents=500, currency=CurrencyCode.EUR)
        assert schema.currency == CurrencyCode.EUR

    def test_supports_usd_currency(self) -> None:
        schema = CashDonationCreate(amount_cents=500, currency=CurrencyCode.USD)
        assert schema.currency == CurrencyCode.USD

    def test_amount_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            CashDonationCreate(amount_cents=0)

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CashDonationCreate(amount_cents=-100)

    def test_receipt_number_max_length(self) -> None:
        with pytest.raises(ValidationError):
            CashDonationCreate(amount_cents=1000, receipt_number="X" * 51)

    def test_receipt_number_at_max_length(self) -> None:
        schema = CashDonationCreate(amount_cents=1000, receipt_number="X" * 50)
        assert len(schema.receipt_number) == 50  # type: ignore[arg-type]

    def test_anonymous_donation_no_donor(self) -> None:
        schema = CashDonationCreate(amount_cents=25000)
        assert schema.donor_id is None
