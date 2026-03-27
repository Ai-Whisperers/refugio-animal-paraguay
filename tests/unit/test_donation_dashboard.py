"""Unit tests for donation dashboard helpers and schemas.

Covers:
  - _donation_to_csv_row: correct field ordering and empty-value handling
  - DonationStatsResponse schema construction
  - CurrencyBreakdown / StatusBreakdown / PaymentMethodBreakdown schemas
  - _apply_common_filters: returns statement unmodified when all params are None
  - _CSV_HEADERS: correct column count
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from src.api.donations import (
    _CSV_HEADERS,
    _apply_common_filters,
    _donation_to_csv_row,
)
from src.schemas.donation import (
    CurrencyBreakdown,
    DonationStatsResponse,
    PaymentMethodBreakdown,
    StatusBreakdown,
)

# ---------------------------------------------------------------------------
# _donation_to_csv_row
# ---------------------------------------------------------------------------


def _make_donation(
    *,
    donor_id: UUID | None = None,
    amount_cents: int = 1000,
    currency: str = "EUR",
    payment_method: str = "stripe",
    status: str = "completed",
    fund_category: str | None = None,
    is_recurring: bool = False,
    recurring_interval: str | None = None,
    receipt_number: str | None = None,
    stripe_payment_intent_id: str | None = None,
    stripe_subscription_id: str | None = None,
    notes: str | None = None,
) -> MagicMock:
    """Build a minimal Donation mock with the fields accessed by _donation_to_csv_row."""
    d = MagicMock()
    d.id = uuid4()
    d.donor_id = donor_id
    d.amount_cents = amount_cents
    d.currency = currency
    d.payment_method = payment_method
    d.status = status
    d.fund_category = fund_category
    d.is_recurring = is_recurring
    d.recurring_interval = recurring_interval
    d.receipt_number = receipt_number
    d.stripe_payment_intent_id = stripe_payment_intent_id
    d.stripe_subscription_id = stripe_subscription_id
    d.notes = notes
    d.created_at = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
    d.updated_at = datetime(2026, 1, 15, 11, 0, 0, tzinfo=UTC)
    return d


def test_donation_to_csv_row_field_count() -> None:
    """CSV row must have exactly as many columns as the header."""
    d = _make_donation()
    row = _donation_to_csv_row(d)
    assert len(row) == len(_CSV_HEADERS)


def test_donation_to_csv_row_basic_values() -> None:
    donation_id = uuid4()
    donor_id = uuid4()
    d = _make_donation(
        donor_id=donor_id,
        amount_cents=5000,
        currency="EUR",
        payment_method="stripe",
        status="completed",
        stripe_payment_intent_id="pi_test123",
    )
    d.id = donation_id
    row = _donation_to_csv_row(d)

    assert row[0] == str(donation_id)
    assert row[1] == str(donor_id)
    assert row[2] == "5000"
    assert row[3] == "EUR"
    assert row[4] == "stripe"
    assert row[5] == "completed"
    assert row[10] == "pi_test123"


def test_donation_to_csv_row_empty_optional_fields() -> None:
    """None optional fields must become empty strings in the CSV row."""
    d = _make_donation(
        donor_id=None,
        fund_category=None,
        receipt_number=None,
        stripe_payment_intent_id=None,
        stripe_subscription_id=None,
        notes=None,
    )
    row = _donation_to_csv_row(d)

    assert row[1] == ""  # donor_id
    assert row[6] == ""  # fund_category
    assert row[9] == ""  # receipt_number
    assert row[10] == ""  # stripe_payment_intent_id
    assert row[11] == ""  # stripe_subscription_id
    assert row[12] == ""  # notes


def test_donation_to_csv_row_recurring_fields() -> None:
    d = _make_donation(is_recurring=True, recurring_interval="month")
    row = _donation_to_csv_row(d)
    assert row[7] == "True"  # is_recurring
    assert row[8] == "month"  # recurring_interval


def test_donation_to_csv_row_iso_timestamps() -> None:
    d = _make_donation()
    row = _donation_to_csv_row(d)
    assert row[13] == "2026-01-15T10:00:00+00:00"
    assert row[14] == "2026-01-15T11:00:00+00:00"


# ---------------------------------------------------------------------------
# _CSV_HEADERS
# ---------------------------------------------------------------------------


def test_csv_headers_content() -> None:
    assert "id" in _CSV_HEADERS
    assert "amount_cents" in _CSV_HEADERS
    assert "currency" in _CSV_HEADERS
    assert "payment_method" in _CSV_HEADERS
    assert "status" in _CSV_HEADERS
    assert "created_at" in _CSV_HEADERS


def test_csv_headers_no_pii_fields() -> None:
    """Email and full_name must not appear in the CSV headers — these belong to the donor record."""
    assert "email" not in _CSV_HEADERS
    assert "full_name" not in _CSV_HEADERS


# ---------------------------------------------------------------------------
# _apply_common_filters: no-op when all params are None
# ---------------------------------------------------------------------------


def test_apply_common_filters_noop_when_all_none() -> None:
    """When every filter param is None, the returned statement should be the same object."""
    stmt = MagicMock()
    result = _apply_common_filters(
        stmt,
        currency=None,
        donation_status=None,
        donor_id=None,
        fund_category=None,
        payment_method=None,
        date_from=None,
        date_to=None,
    )
    # No .where() calls should have been made
    stmt.where.assert_not_called()
    assert result is stmt


# ---------------------------------------------------------------------------
# Schema construction — DonationStatsResponse
# ---------------------------------------------------------------------------


def test_donation_stats_response_schema() -> None:
    stats = DonationStatsResponse(
        total_donations=42,
        by_currency=[
            CurrencyBreakdown(currency="EUR", count=30, total_amount_cents=150000),
            CurrencyBreakdown(currency="PYG", count=12, total_amount_cents=5000000),
        ],
        by_status=[
            StatusBreakdown(status="completed", count=40),
            StatusBreakdown(status="pending", count=2),
        ],
        by_payment_method=[
            PaymentMethodBreakdown(payment_method="stripe", count=30, total_amount_cents=150000),
            PaymentMethodBreakdown(payment_method="cash", count=12, total_amount_cents=5000000),
        ],
        date_from=None,
        date_to=None,
    )
    assert stats.total_donations == 42
    assert len(stats.by_currency) == 2
    assert stats.by_currency[0].currency == "EUR"
    assert stats.by_currency[0].total_amount_cents == 150000
    assert stats.by_status[0].count == 40
    assert stats.by_payment_method[1].payment_method == "cash"


def test_donation_stats_with_date_range() -> None:
    date_from = datetime(2026, 1, 1, tzinfo=UTC)
    date_to = datetime(2026, 1, 31, tzinfo=UTC)
    stats = DonationStatsResponse(
        total_donations=5,
        by_currency=[],
        by_status=[],
        by_payment_method=[],
        date_from=date_from,
        date_to=date_to,
    )
    assert stats.date_from == date_from
    assert stats.date_to == date_to


def test_currency_breakdown_zero_total() -> None:
    bd = CurrencyBreakdown(currency="USD", count=0, total_amount_cents=0)
    assert bd.total_amount_cents == 0
    assert bd.count == 0


def test_status_breakdown_fields() -> None:
    sb = StatusBreakdown(status="refunded", count=3)
    assert sb.status == "refunded"
    assert sb.count == 3
