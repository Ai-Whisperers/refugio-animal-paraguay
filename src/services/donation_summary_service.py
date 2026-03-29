"""Donation summary service for financial reporting (RAP-255).

Aggregates completed donation data by configurable dimensions:
- Period (daily / weekly / monthly / quarterly / annual)
- Currency (EUR / PYG / USD)
- Type (payment_method or target_type)

All amounts stored as integer cents to avoid float precision issues.
PYG donations are stored as whole units (no cents subdivision).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import CurrencyCode, Donation, DonationStatus, PaymentMethod

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums and constants
# ---------------------------------------------------------------------------

PeriodGrouping = Literal["daily", "weekly", "monthly", "quarterly", "annual"]

# Default lookback windows per grouping interval.
DEFAULT_LOOKBACK_DAYS: dict[PeriodGrouping, int] = {
    "daily": 30,
    "weekly": 90,
    "monthly": 365,
    "quarterly": 730,
    "annual": 1825,
}

MAX_LOOKBACK_DAYS = 3650  # 10 years

# PostgreSQL date_trunc values per grouping.
_DATE_TRUNC: dict[PeriodGrouping, str] = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
    "quarterly": "quarter",
    "annual": "year",
}

# Human-readable label format strings per grouping.
_LABEL_FORMAT: dict[PeriodGrouping, str] = {
    "daily": "%d/%m/%Y",
    "weekly": "Sem %W %Y",
    "monthly": "%b %Y",
    "quarterly": "Q%q %Y",
    "annual": "%Y",
}


class BreakdownDimension(StrEnum):
    """Dimension to use when breaking down donation totals."""

    PAYMENT_METHOD = "payment_method"
    TARGET_TYPE = "target_type"
    CURRENCY = "currency"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurrencyTotals:
    """Aggregated donation totals for one currency."""

    currency: str
    donation_count: int
    total_amount_cents: int

    @property
    def total_amount_display(self) -> str:
        """Human-readable amount string."""
        if self.currency == CurrencyCode.PYG:
            return f"{self.total_amount_cents:,} PYG"
        return f"{self.total_amount_cents / 100:,.2f} {self.currency}"


@dataclass(frozen=True)
class PeriodSummaryRow:
    """Donation totals for a single time period + dimension value."""

    period_label: str
    period_start: str
    dimension_value: str
    currency: str
    donation_count: int
    total_amount_cents: int


@dataclass(frozen=True)
class DonationSummaryResult:
    """Complete donation summary response."""

    generated_at: str
    grouping: str
    breakdown_by: str
    lookback_days: int
    period_from: str
    period_to: str
    total_donations: int
    currency_totals: list[CurrencyTotals]
    rows: list[PeriodSummaryRow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _period_label(period_start: datetime, grouping: PeriodGrouping) -> str:
    """Generate human-readable period label from a datetime."""
    if grouping == "quarterly":
        quarter = (period_start.month - 1) // 3 + 1
        return f"Q{quarter} {period_start.year}"
    fmt = _LABEL_FORMAT[grouping]
    return period_start.strftime(fmt)


# ---------------------------------------------------------------------------
# Service function
# ---------------------------------------------------------------------------


async def get_donation_summary(
    db: AsyncSession,
    grouping: PeriodGrouping = "monthly",
    breakdown_by: BreakdownDimension = BreakdownDimension.CURRENCY,
    lookback_days: int | None = None,
) -> DonationSummaryResult:
    """Aggregate completed donations by period + breakdown dimension.

    Args:
        db: Async SQLAlchemy session.
        grouping: Time bucket for aggregation (daily/weekly/monthly/quarterly/annual).
        breakdown_by: Dimension for sub-grouping within each period.
        lookback_days: Days of history to include. Defaults per grouping interval.

    Returns:
        DonationSummaryResult with per-period rows and currency totals.
    """
    days = lookback_days if lookback_days is not None else DEFAULT_LOOKBACK_DAYS[grouping]
    since = datetime.now(UTC) - timedelta(days=days)
    trunc_value = _DATE_TRUNC[grouping]

    # Dimension column to group by
    if breakdown_by == BreakdownDimension.PAYMENT_METHOD:
        dimension_col = Donation.payment_method
    elif breakdown_by == BreakdownDimension.TARGET_TYPE:
        dimension_col = Donation.target_type
    else:
        dimension_col = Donation.currency

    stmt = (
        select(
            func.date_trunc(trunc_value, Donation.created_at).label("period_start"),
            dimension_col.label("dimension_value"),
            Donation.currency.label("currency"),
            func.count(Donation.id).label("donation_count"),
            func.sum(Donation.amount_cents).label("total_amount_cents"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= since,
        )
        .group_by(text("period_start"), text("dimension_value"), Donation.currency)
        .order_by(text("period_start"), Donation.currency, text("dimension_value"))
    )

    result = await db.execute(stmt)
    rows_raw = result.all()

    rows = [
        PeriodSummaryRow(
            period_label=_period_label(
                row.period_start.replace(tzinfo=UTC) if row.period_start else datetime.now(UTC),
                grouping,
            ),
            period_start=row.period_start.isoformat() if row.period_start else "",
            dimension_value=row.dimension_value or "unknown",
            currency=row.currency,
            donation_count=row.donation_count or 0,
            total_amount_cents=row.total_amount_cents or 0,
        )
        for row in rows_raw
    ]

    # Compute currency-level totals
    currency_agg: dict[str, dict[str, int]] = {}
    for row in rows:
        if row.currency not in currency_agg:
            currency_agg[row.currency] = {"count": 0, "total": 0}
        currency_agg[row.currency]["count"] += row.donation_count
        currency_agg[row.currency]["total"] += row.total_amount_cents

    currency_totals = [
        CurrencyTotals(
            currency=currency,
            donation_count=agg["count"],
            total_amount_cents=agg["total"],
        )
        for currency, agg in sorted(currency_agg.items())
    ]

    total_count = sum(ct.donation_count for ct in currency_totals)

    return DonationSummaryResult(
        generated_at=datetime.now(UTC).isoformat(),
        grouping=grouping,
        breakdown_by=breakdown_by.value,
        lookback_days=days,
        period_from=since.date().isoformat(),
        period_to=datetime.now(UTC).date().isoformat(),
        total_donations=total_count,
        currency_totals=currency_totals,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Payment method label helpers
# ---------------------------------------------------------------------------

PAYMENT_METHOD_LABELS_ES: dict[str, str] = {
    PaymentMethod.STRIPE: "Tarjeta (Stripe)",
    PaymentMethod.CASH: "Efectivo",
    PaymentMethod.TRANSFER: "Transferencia bancaria",
    PaymentMethod.SEPA_DEBIT: "SEPA (Europa)",
    PaymentMethod.TIGO_MONEY: "Tigo Money",
}

TARGET_TYPE_LABELS_ES: dict[str, str] = {
    "general": "General",
    "animal": "Animal especifico",
    "rescuer": "Rescatista",
    "clinic": "Clinica",
    "campaign": "Campana",
    "need": "Necesidad especifica",
    "emergency": "Emergencia",
}
