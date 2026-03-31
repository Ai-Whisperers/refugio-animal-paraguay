"""Financial reporting API endpoints (RAP-255, RAP-257, RAP-258).

Staff-only financial reporting suite for the shelter management platform.

Endpoints:
  GET /api/admin/financial-reporting/donation-summary       — donation totals by period/currency/type
  GET /api/admin/financial-reporting/eu-tax-export/{year}  — bulk EU donor CSV for tax authorities
  GET /api/admin/financial-reporting/donor-retention        — retention rate, churn rate, segments
  GET /api/admin/financial-reporting/donor-cohorts          — monthly cohort retention table
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.donation_summary_service import (
    BreakdownDimension,
    DonationSummaryResult,
    PeriodGrouping,
    get_donation_summary,
)
from src.services.donor_retention_service import (
    CohortRetentionResult,
    DonorSegmentCounts,
    RetentionMetrics,
    get_cohort_retention,
    get_retention_metrics,
)
from src.services.eu_tax_export_service import get_eu_tax_export, render_eu_tax_csv

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/financial-reporting",
    tags=["financial-reporting"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_LOOKBACK_DAYS = 3650
MIN_LOOKBACK_DAYS = 1

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CurrencyTotalsSchema(BaseModel):
    currency: str
    donation_count: int
    total_amount_cents: int
    total_amount_display: str


class PeriodSummaryRowSchema(BaseModel):
    period_label: str
    period_start: str
    dimension_value: str
    currency: str
    donation_count: int
    total_amount_cents: int


class DonationSummaryResponse(BaseModel):
    generated_at: str
    grouping: str
    breakdown_by: str
    lookback_days: int
    period_from: str
    period_to: str
    total_donations: int
    currency_totals: list[CurrencyTotalsSchema]
    rows: list[PeriodSummaryRowSchema]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/donation-summary",
    response_model=DonationSummaryResponse,
    summary="Donation summary by period, currency, and type",
)
async def get_donation_summary_endpoint(
    grouping: Annotated[
        PeriodGrouping,
        Query(
            description=(
                "Time bucket for aggregation: daily, weekly, monthly, quarterly, or annual "
                "(default: monthly)"
            )
        ),
    ] = "monthly",
    breakdown_by: Annotated[
        BreakdownDimension,
        Query(
            description=(
                "Dimension for sub-grouping within each period: "
                "currency, payment_method, or target_type (default: currency)"
            )
        ),
    ] = BreakdownDimension.CURRENCY,
    lookback_days: Annotated[
        int,
        Query(
            ge=MIN_LOOKBACK_DAYS,
            le=MAX_LOOKBACK_DAYS,
            description=(
                "Days of history to include. Defaults per grouping: "
                "daily=30, weekly=90, monthly=365, quarterly=730, annual=1825."
            ),
        ),
    ] = 0,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> DonationSummaryResponse:
    """Return aggregated donation totals grouped by time period and a breakdown dimension.

    Only **completed** donations are included. Response includes:

    - **currency_totals**: overall totals per currency across the full lookback window
    - **rows**: one row per (period, dimension_value, currency) combination
    - **total_donations**: count of completed donations in the window

    Use `grouping` to control the time bucket (daily → 30d default, monthly → 365d default).
    Use `breakdown_by` to sub-group rows by `currency`, `payment_method`, or `target_type`.

    Auth: requires staff or admin role.
    """
    resolved_lookback = lookback_days if lookback_days > 0 else None
    summary: DonationSummaryResult = await get_donation_summary(
        db,
        grouping=grouping,
        breakdown_by=breakdown_by,
        lookback_days=resolved_lookback,
    )

    return DonationSummaryResponse(
        generated_at=summary.generated_at,
        grouping=summary.grouping,
        breakdown_by=summary.breakdown_by,
        lookback_days=summary.lookback_days,
        period_from=summary.period_from,
        period_to=summary.period_to,
        total_donations=summary.total_donations,
        currency_totals=[
            CurrencyTotalsSchema(
                currency=ct.currency,
                donation_count=ct.donation_count,
                total_amount_cents=ct.total_amount_cents,
                total_amount_display=ct.total_amount_display,
            )
            for ct in summary.currency_totals
        ],
        rows=[
            PeriodSummaryRowSchema(
                period_label=row.period_label,
                period_start=row.period_start,
                dimension_value=row.dimension_value,
                currency=row.currency,
                donation_count=row.donation_count,
                total_amount_cents=row.total_amount_cents,
            )
            for row in summary.rows
        ],
    )


# ---------------------------------------------------------------------------
# EU tax compliance export — RAP-257
# ---------------------------------------------------------------------------

MIN_EXPORT_YEAR = 2020
MAX_EXPORT_YEAR = 2100


@router.get(
    "/eu-tax-export/{year}",
    summary="EU donor tax compliance CSV export (annual)",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV file with per-donor, per-currency donation totals for the year",
        },
        400: {"description": "Invalid year"},
    },
)
async def get_eu_tax_export_endpoint(
    year: Annotated[
        int,
        Path(
            ge=MIN_EXPORT_YEAR,
            le=MAX_EXPORT_YEAR,
            description="Calendar year for which to export EU donor donations",
        ),
    ],
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export completed EU donor donations for a calendar year as a CSV file.

    Returns a UTF-8 encoded CSV with one row per **(donor x currency)** combination.
    Only donors whose `country` is an EU member state (ISO 3166-1 alpha-2) are included.
    Only **completed** donations are counted.

    CSV columns: `donor_id`, `donor_name`, `donor_email`, `donor_country`,
    `tax_id_type`, `year`, `currency`, `donation_count`, `total_amount_cents`,
    `total_amount_display`.

    Suitable for batch tax authority submission or internal compliance records.

    Auth: requires staff or admin role.
    """
    if year < MIN_EXPORT_YEAR or year > MAX_EXPORT_YEAR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Year must be between {MIN_EXPORT_YEAR} and {MAX_EXPORT_YEAR}",
        )

    export = await get_eu_tax_export(db, year=year)
    csv_bytes = render_eu_tax_csv(export)

    filename = f"eu-tax-export-{year}.csv"
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Donor-Count": str(export.donor_count),
            "X-Total-Donations": str(export.total_donations),
            "X-Generated-At": export.generated_at,
        },
    )


# ---------------------------------------------------------------------------
# Donor retention and churn analysis — RAP-258
# ---------------------------------------------------------------------------

MAX_PERIOD_DAYS = 365
MIN_PERIOD_DAYS = 7
MAX_COHORT_MONTHS = 24
MIN_COHORT_MONTHS = 1


class DonorSegmentCountsSchema(BaseModel):
    new: int
    active: int
    at_risk: int
    lapsed: int
    churned: int
    total: int


class RetentionMetricsResponse(BaseModel):
    generated_at: str
    period_days: int
    retained_donors: int
    churned_donors: int
    new_donors: int
    retention_rate_pct: float
    churn_rate_pct: float
    segments: DonorSegmentCountsSchema


class CohortRetentionRowSchema(BaseModel):
    cohort_month: str
    cohort_size: int
    retained_month_1: int
    retained_month_3: int
    retained_month_6: int
    retention_pct_1: float
    retention_pct_3: float
    retention_pct_6: float


class CohortRetentionResponse(BaseModel):
    generated_at: str
    lookback_months: int
    cohorts: list[CohortRetentionRowSchema]


@router.get(
    "/donor-retention",
    response_model=RetentionMetricsResponse,
    summary="Donor retention and churn metrics for a rolling period",
)
async def get_donor_retention_endpoint(
    period_days: Annotated[
        int,
        Query(
            ge=MIN_PERIOD_DAYS,
            le=MAX_PERIOD_DAYS,
            description=(
                "Length of each comparison window in days. "
                "Retention = donors who donated in both the prior and current window. "
                "Default: 30."
            ),
        ),
    ] = 30,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> RetentionMetricsResponse:
    """Return live donor retention and churn metrics.

    Compares two consecutive windows of `period_days` each:

    - **prior window**: `[now - 2*period_days, now - period_days)`
    - **current window**: `[now - period_days, now)`

    Returns:
    - **retained_donors**: donated in both windows
    - **churned_donors**: donated in prior window only
    - **new_donors**: first-ever donation in current window
    - **retention_rate_pct**: retained / (retained + churned)
    - **churn_rate_pct**: churned / (retained + churned)
    - **segments**: current lifecycle segment breakdown (new/active/at_risk/lapsed/churned)

    Auth: requires staff or admin role.
    """
    metrics: RetentionMetrics = await get_retention_metrics(db, period_days=period_days)
    segments: DonorSegmentCounts = metrics.segments
    return RetentionMetricsResponse(
        generated_at=metrics.generated_at,
        period_days=metrics.period_days,
        retained_donors=metrics.retained_donors,
        churned_donors=metrics.churned_donors,
        new_donors=metrics.new_donors,
        retention_rate_pct=metrics.retention_rate_pct,
        churn_rate_pct=metrics.churn_rate_pct,
        segments=DonorSegmentCountsSchema(
            new=segments.new,
            active=segments.active,
            at_risk=segments.at_risk,
            lapsed=segments.lapsed,
            churned=segments.churned,
            total=segments.total,
        ),
    )


@router.get(
    "/donor-cohorts",
    response_model=CohortRetentionResponse,
    summary="Monthly donor cohort retention table",
)
async def get_donor_cohorts_endpoint(
    lookback_months: Annotated[
        int,
        Query(
            ge=MIN_COHORT_MONTHS,
            le=MAX_COHORT_MONTHS,
            description="How many months of cohorts to include (default: 12)",
        ),
    ] = 12,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CohortRetentionResponse:
    """Return monthly cohort retention table.

    For each month in the lookback window, groups donors by their first donation
    month and reports how many of them also donated 1, 3, and 6 months later.

    Useful for identifying whether early-cohort donors are more loyal and
    how retention changes over acquisition periods.

    Auth: requires staff or admin role.
    """
    result: CohortRetentionResult = await get_cohort_retention(db, lookback_months=lookback_months)
    return CohortRetentionResponse(
        generated_at=result.generated_at,
        lookback_months=result.lookback_months,
        cohorts=[
            CohortRetentionRowSchema(
                cohort_month=row.cohort_month,
                cohort_size=row.cohort_size,
                retained_month_1=row.retained_month_1,
                retained_month_3=row.retained_month_3,
                retained_month_6=row.retained_month_6,
                retention_pct_1=row.retention_pct_1,
                retention_pct_3=row.retention_pct_3,
                retention_pct_6=row.retention_pct_6,
            )
            for row in result.cohorts
        ],
    )
