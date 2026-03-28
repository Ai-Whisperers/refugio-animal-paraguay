"""Donor analytics and retention API (RAP-635).

Provides analytical endpoints for donor behavior and retention:
- Donor retention metrics (churn, retention rate, LTV)
- Donor segmentation (new, active, lapsed, churned)
- Donor acquisition trends
- Recurring vs one-time donor analysis
- Donor engagement scoring
- Reactivation opportunities

Endpoints
---------
GET  /api/admin/analytics/donors/retention      -- retention metrics
GET  /api/admin/analytics/donors/segments        -- donor segmentation
GET  /api/admin/analytics/donors/acquisition     -- acquisition trends
GET  /api/admin/analytics/donors/recurring       -- recurring donor analysis
GET  /api/admin/analytics/donors/engagement      -- engagement scores
GET  /api/admin/analytics/donors/reactivation    -- reactivation opportunities
"""

from __future__ import annotations

import logging
from enum import StrEnum

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/donors",
    tags=["donor-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365
ACTIVE_THRESHOLD_DAYS = 90
LAPSED_THRESHOLD_DAYS = 180
CHURNED_THRESHOLD_DAYS = 365

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DonorSegment(StrEnum):
    """Donor lifecycle segment."""

    NEW = "new"
    ACTIVE = "active"
    AT_RISK = "at_risk"
    LAPSED = "lapsed"
    CHURNED = "churned"


class EngagementLevel(StrEnum):
    """Donor engagement level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INACTIVE = "inactive"


SEGMENT_LABELS_ES: dict[str, str] = {
    "new": "Nuevo",
    "active": "Activo",
    "at_risk": "En riesgo",
    "lapsed": "Inactivo",
    "churned": "Perdido",
}

ENGAGEMENT_LABELS_ES: dict[str, str] = {
    "high": "Alto",
    "medium": "Medio",
    "low": "Bajo",
    "inactive": "Inactivo",
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RetentionMetric(BaseModel):
    """Single retention metric."""

    label: str
    value: float
    unit: str
    change_percent: float | None = None
    trend: str = "stable"


class RetentionSummary(BaseModel):
    """Overall donor retention summary."""

    retention_rate: float
    churn_rate: float
    average_donor_lifetime_months: float
    average_ltv_pyg: float
    total_active_donors: int
    total_donors: int
    period_days: int
    metrics: list[RetentionMetric]


class SegmentData(BaseModel):
    """Donor segment data."""

    segment: str
    label: str
    count: int
    percentage: float
    average_donation_pyg: float
    total_donated_pyg: float


class AcquisitionTrend(BaseModel):
    """Monthly donor acquisition data."""

    month: str
    year: int
    new_donors: int
    returning_donors: int
    churned_donors: int
    net_growth: int


class RecurringAnalysis(BaseModel):
    """Recurring vs one-time donor analysis."""

    recurring_donors: int
    one_time_donors: int
    recurring_percentage: float
    recurring_total_pyg: float
    one_time_total_pyg: float
    recurring_avg_pyg: float
    one_time_avg_pyg: float
    conversion_rate: float


class EngagementScore(BaseModel):
    """Donor engagement breakdown."""

    level: str
    label: str
    count: int
    percentage: float
    avg_donations_per_year: float
    avg_amount_pyg: float


class ReactivationOpportunity(BaseModel):
    """Donor reactivation opportunity."""

    donor_name: str
    last_donation_date: str
    days_since_last: int
    total_historical_pyg: float
    donation_count: int
    segment: str
    reactivation_priority: str


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_ACQUISITION_TRENDS: list[dict] = [
    {
        "month": "Oct",
        "year": 2025,
        "new_donors": 18,
        "returning_donors": 24,
        "churned_donors": 5,
        "net_growth": 13,
    },
    {
        "month": "Nov",
        "year": 2025,
        "new_donors": 22,
        "returning_donors": 26,
        "churned_donors": 7,
        "net_growth": 15,
    },
    {
        "month": "Dic",
        "year": 2025,
        "new_donors": 35,
        "returning_donors": 32,
        "churned_donors": 4,
        "net_growth": 31,
    },
    {
        "month": "Ene",
        "year": 2026,
        "new_donors": 15,
        "returning_donors": 22,
        "churned_donors": 8,
        "net_growth": 7,
    },
    {
        "month": "Feb",
        "year": 2026,
        "new_donors": 20,
        "returning_donors": 28,
        "churned_donors": 6,
        "net_growth": 14,
    },
    {
        "month": "Mar",
        "year": 2026,
        "new_donors": 25,
        "returning_donors": 31,
        "churned_donors": 3,
        "net_growth": 22,
    },
]

SAMPLE_SEGMENTS: list[dict] = [
    {
        "segment": "new",
        "label": "Nuevo",
        "count": 45,
        "percentage": 24.1,
        "average_donation_pyg": 850_000,
        "total_donated_pyg": 38_250_000,
    },
    {
        "segment": "active",
        "label": "Activo",
        "count": 78,
        "percentage": 41.7,
        "average_donation_pyg": 1_200_000,
        "total_donated_pyg": 93_600_000,
    },
    {
        "segment": "at_risk",
        "label": "En riesgo",
        "count": 28,
        "percentage": 15.0,
        "average_donation_pyg": 950_000,
        "total_donated_pyg": 26_600_000,
    },
    {
        "segment": "lapsed",
        "label": "Inactivo",
        "count": 23,
        "percentage": 12.3,
        "average_donation_pyg": 700_000,
        "total_donated_pyg": 16_100_000,
    },
    {
        "segment": "churned",
        "label": "Perdido",
        "count": 13,
        "percentage": 7.0,
        "average_donation_pyg": 500_000,
        "total_donated_pyg": 6_500_000,
    },
]

SAMPLE_ENGAGEMENT: list[dict] = [
    {
        "level": "high",
        "label": "Alto",
        "count": 42,
        "percentage": 22.5,
        "avg_donations_per_year": 8.5,
        "avg_amount_pyg": 1_500_000,
    },
    {
        "level": "medium",
        "label": "Medio",
        "count": 65,
        "percentage": 34.8,
        "avg_donations_per_year": 4.2,
        "avg_amount_pyg": 1_000_000,
    },
    {
        "level": "low",
        "label": "Bajo",
        "count": 48,
        "percentage": 25.7,
        "avg_donations_per_year": 1.8,
        "avg_amount_pyg": 600_000,
    },
    {
        "level": "inactive",
        "label": "Inactivo",
        "count": 32,
        "percentage": 17.1,
        "avg_donations_per_year": 0.3,
        "avg_amount_pyg": 350_000,
    },
]

SAMPLE_REACTIVATION: list[dict] = [
    {
        "donor_name": "Elena Fernandez",
        "last_donation_date": "2025-09-15",
        "days_since_last": 194,
        "total_historical_pyg": 12_000_000,
        "donation_count": 8,
        "segment": "lapsed",
        "reactivation_priority": "high",
    },
    {
        "donor_name": "Marco Villalba",
        "last_donation_date": "2025-10-02",
        "days_since_last": 177,
        "total_historical_pyg": 8_500_000,
        "donation_count": 5,
        "segment": "lapsed",
        "reactivation_priority": "high",
    },
    {
        "donor_name": "Stichting Dierenhulp NL",
        "last_donation_date": "2025-08-20",
        "days_since_last": 220,
        "total_historical_pyg": 25_000_000,
        "donation_count": 12,
        "segment": "churned",
        "reactivation_priority": "critical",
    },
    {
        "donor_name": "Patricia Gomez",
        "last_donation_date": "2025-11-10",
        "days_since_last": 138,
        "total_historical_pyg": 4_200_000,
        "donation_count": 3,
        "segment": "at_risk",
        "reactivation_priority": "medium",
    },
    {
        "donor_name": "Verein Tierfreunde AT",
        "last_donation_date": "2025-07-05",
        "days_since_last": 266,
        "total_historical_pyg": 18_000_000,
        "donation_count": 6,
        "segment": "churned",
        "reactivation_priority": "critical",
    },
    {
        "donor_name": "Jose Benitez",
        "last_donation_date": "2025-12-01",
        "days_since_last": 117,
        "total_historical_pyg": 3_000_000,
        "donation_count": 2,
        "segment": "at_risk",
        "reactivation_priority": "medium",
    },
    {
        "donor_name": "Laura Acuna",
        "last_donation_date": "2025-10-20",
        "days_since_last": 159,
        "total_historical_pyg": 6_800_000,
        "donation_count": 4,
        "segment": "lapsed",
        "reactivation_priority": "high",
    },
    {
        "donor_name": "Diego Ramirez",
        "last_donation_date": "2025-11-25",
        "days_since_last": 123,
        "total_historical_pyg": 2_500_000,
        "donation_count": 2,
        "segment": "at_risk",
        "reactivation_priority": "low",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/retention", response_model=RetentionSummary)
async def get_retention_metrics(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> RetentionSummary:
    """Get donor retention metrics."""
    retention_rate = 72.5
    churn_rate = 27.5
    avg_lifetime = 14.3
    avg_ltv = 8_500_000.0
    active = 123
    total = 187

    metrics = [
        RetentionMetric(
            label="Tasa de retencion",
            value=retention_rate,
            unit="%",
            change_percent=3.2,
            trend="up",
        ),
        RetentionMetric(
            label="Tasa de abandono", value=churn_rate, unit="%", change_percent=-3.2, trend="down"
        ),
        RetentionMetric(
            label="Vida promedio (meses)",
            value=avg_lifetime,
            unit="meses",
            change_percent=1.5,
            trend="up",
        ),
        RetentionMetric(
            label="LTV promedio (PYG)", value=avg_ltv, unit="PYG", change_percent=5.8, trend="up"
        ),
    ]

    return RetentionSummary(
        retention_rate=retention_rate,
        churn_rate=churn_rate,
        average_donor_lifetime_months=avg_lifetime,
        average_ltv_pyg=avg_ltv,
        total_active_donors=active,
        total_donors=total,
        period_days=period_days,
        metrics=metrics,
    )


@router.get("/segments", response_model=list[SegmentData])
async def get_donor_segments(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> list[SegmentData]:
    """Get donor segmentation data."""
    return [SegmentData(**s) for s in SAMPLE_SEGMENTS]


@router.get("/acquisition", response_model=list[AcquisitionTrend])
async def get_acquisition_trends(
    months: int = Query(default=6, ge=1, le=12),
) -> list[AcquisitionTrend]:
    """Get monthly donor acquisition trends."""
    return [AcquisitionTrend(**t) for t in SAMPLE_ACQUISITION_TRENDS[-months:]]


@router.get("/recurring", response_model=RecurringAnalysis)
async def get_recurring_analysis(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> RecurringAnalysis:
    """Get recurring vs one-time donor analysis."""
    return RecurringAnalysis(
        recurring_donors=79,
        one_time_donors=108,
        recurring_percentage=42.2,
        recurring_total_pyg=142_000_000,
        one_time_total_pyg=89_000_000,
        recurring_avg_pyg=1_797_468,
        one_time_avg_pyg=824_074,
        conversion_rate=18.5,
    )


@router.get("/engagement", response_model=list[EngagementScore])
async def get_engagement_scores(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> list[EngagementScore]:
    """Get donor engagement score breakdown."""
    return [EngagementScore(**e) for e in SAMPLE_ENGAGEMENT]


@router.get("/reactivation", response_model=list[ReactivationOpportunity])
async def get_reactivation_opportunities(
    limit: int = Query(default=10, ge=1, le=50),
) -> list[ReactivationOpportunity]:
    """Get donor reactivation opportunities sorted by priority."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_opps = sorted(
        SAMPLE_REACTIVATION,
        key=lambda x: priority_order.get(x["reactivation_priority"], 99),
    )
    return [ReactivationOpportunity(**o) for o in sorted_opps[:limit]]
