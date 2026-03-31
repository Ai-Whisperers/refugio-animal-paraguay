"""Unit tests for donation summary service (RAP-255)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.donation_summary_service import (
    BreakdownDimension,
    CurrencyTotals,
    DonationSummaryResult,
    _period_label,
    get_donation_summary,
)

# ---------------------------------------------------------------------------
# Unit tests for _period_label helper
# ---------------------------------------------------------------------------


class TestPeriodLabel:
    def test_daily_format(self) -> None:
        dt = datetime(2026, 3, 15, tzinfo=UTC)
        assert _period_label(dt, "daily") == "15/03/2026"

    def test_weekly_format(self) -> None:
        dt = datetime(2026, 3, 9, tzinfo=UTC)
        label = _period_label(dt, "weekly")
        assert "2026" in label

    def test_monthly_format(self) -> None:
        dt = datetime(2026, 3, 1, tzinfo=UTC)
        label = _period_label(dt, "monthly")
        assert "2026" in label
        assert "Mar" in label

    def test_quarterly_format_q1(self) -> None:
        dt = datetime(2026, 1, 1, tzinfo=UTC)
        assert _period_label(dt, "quarterly") == "Q1 2026"

    def test_quarterly_format_q2(self) -> None:
        dt = datetime(2026, 4, 1, tzinfo=UTC)
        assert _period_label(dt, "quarterly") == "Q2 2026"

    def test_quarterly_format_q3(self) -> None:
        dt = datetime(2026, 7, 1, tzinfo=UTC)
        assert _period_label(dt, "quarterly") == "Q3 2026"

    def test_quarterly_format_q4(self) -> None:
        dt = datetime(2026, 10, 1, tzinfo=UTC)
        assert _period_label(dt, "quarterly") == "Q4 2026"

    def test_annual_format(self) -> None:
        dt = datetime(2026, 1, 1, tzinfo=UTC)
        assert _period_label(dt, "annual") == "2026"


# ---------------------------------------------------------------------------
# Unit tests for CurrencyTotals.total_amount_display
# ---------------------------------------------------------------------------


class TestCurrencyTotals:
    def test_eur_display(self) -> None:
        ct = CurrencyTotals(currency="EUR", donation_count=5, total_amount_cents=150000)
        assert ct.total_amount_display == "1,500.00 EUR"

    def test_pyg_display(self) -> None:
        ct = CurrencyTotals(currency="PYG", donation_count=3, total_amount_cents=500000)
        assert ct.total_amount_display == "500,000 PYG"

    def test_usd_display(self) -> None:
        ct = CurrencyTotals(currency="USD", donation_count=2, total_amount_cents=10000)
        assert ct.total_amount_display == "100.00 USD"


# ---------------------------------------------------------------------------
# Integration-style tests with mocked DB
# ---------------------------------------------------------------------------


def _make_mock_row(
    period_start: datetime,
    dimension_value: str,
    currency: str,
    donation_count: int,
    total_amount_cents: int,
) -> MagicMock:
    """Build a mock row mimicking SQLAlchemy result row."""
    row = MagicMock()
    row.period_start = period_start
    row.dimension_value = dimension_value
    row.currency = currency
    row.donation_count = donation_count
    row.total_amount_cents = total_amount_cents
    return row


class TestGetDonationSummary:
    @pytest.mark.asyncio
    async def test_empty_result(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, grouping="monthly")

        assert isinstance(result, DonationSummaryResult)
        assert result.total_donations == 0
        assert result.rows == []
        assert result.currency_totals == []
        assert result.grouping == "monthly"
        assert result.breakdown_by == "currency"

    @pytest.mark.asyncio
    async def test_single_eur_row(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            _make_mock_row(
                period_start=datetime(2026, 3, 1, tzinfo=UTC),
                dimension_value="EUR",
                currency="EUR",
                donation_count=5,
                total_amount_cents=50000,
            )
        ]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, grouping="monthly")

        assert result.total_donations == 5
        assert len(result.rows) == 1
        assert result.rows[0].currency == "EUR"
        assert result.rows[0].donation_count == 5
        assert result.rows[0].total_amount_cents == 50000
        assert len(result.currency_totals) == 1
        assert result.currency_totals[0].currency == "EUR"

    @pytest.mark.asyncio
    async def test_multi_currency_totals(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "EUR", "EUR", 3, 30000),
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "PYG", "PYG", 7, 700000),
        ]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db)

        assert result.total_donations == 10
        currencies = {ct.currency for ct in result.currency_totals}
        assert "EUR" in currencies
        assert "PYG" in currencies

    @pytest.mark.asyncio
    async def test_breakdown_by_payment_method(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "stripe", "EUR", 4, 40000),
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "cash", "PYG", 2, 200000),
        ]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, breakdown_by=BreakdownDimension.PAYMENT_METHOD)

        assert result.breakdown_by == "payment_method"
        assert result.rows[0].dimension_value == "stripe"
        assert result.rows[1].dimension_value == "cash"

    @pytest.mark.asyncio
    async def test_breakdown_by_target_type(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "general", "EUR", 10, 100000),
            _make_mock_row(datetime(2026, 3, 1, tzinfo=UTC), "animal", "EUR", 5, 50000),
        ]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, breakdown_by=BreakdownDimension.TARGET_TYPE)

        assert result.breakdown_by == "target_type"
        assert result.total_donations == 15

    @pytest.mark.asyncio
    async def test_lookback_days_respected(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, lookback_days=90)

        assert result.lookback_days == 90

    @pytest.mark.asyncio
    async def test_default_lookback_per_grouping(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result_daily = await get_donation_summary(db, grouping="daily")
        assert result_daily.lookback_days == 30

        result_annual = await get_donation_summary(db, grouping="annual")
        assert result_annual.lookback_days == 1825

    @pytest.mark.asyncio
    async def test_period_from_to_set(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_donation_summary(db, grouping="monthly")

        assert result.period_from != ""
        assert result.period_to != ""
        assert result.generated_at != ""

    @pytest.mark.asyncio
    async def test_null_period_start_handled(self) -> None:
        """Null period_start should not crash."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            _make_mock_row(None, "EUR", "EUR", 1, 10000),
        ]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db)
        assert len(result.rows) == 1
        assert result.rows[0].period_start == ""

    @pytest.mark.asyncio
    async def test_null_dimension_value_becomes_unknown(self) -> None:
        """None dimension_value should be replaced with 'unknown'."""
        db = AsyncMock()
        mock_result = MagicMock()
        row = MagicMock()
        row.period_start = datetime(2026, 3, 1, tzinfo=UTC)
        row.dimension_value = None
        row.currency = "EUR"
        row.donation_count = 1
        row.total_amount_cents = 5000
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await get_donation_summary(db)
        assert result.rows[0].dimension_value == "unknown"
