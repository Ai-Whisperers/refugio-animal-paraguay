"""Donation analytics and trends API (RAP-634).

Provides analytical endpoints for donation data including:
- Donation summary (totals, averages, counts)
- Donation trends over time (monthly/weekly)
- Donation by source/channel breakdown
- Currency distribution (EUR/PYG)
- Top donors ranking
- Campaign performance comparison

Endpoints
---------
GET  /api/admin/analytics/donations/summary       -- donation KPI summary
GET  /api/admin/analytics/donations/trends         -- monthly donation trends
GET  /api/admin/analytics/donations/by-source      -- donations grouped by source
GET  /api/admin/analytics/donations/by-currency    -- currency distribution
GET  /api/admin/analytics/donations/top-donors     -- top donors ranking
GET  /api/admin/analytics/donations/campaigns      -- campaign performance
"""

from __future__ import annotations

import logging
from enum import StrEnum

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/donations",
    tags=["donation-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365
CURRENCY_PYG = "PYG"
CURRENCY_EUR = "EUR"
TOP_DONORS_LIMIT = 10

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DonationSource(StrEnum):
    """Channel through which donation was received."""

    ONLINE = "online"
    BANK_TRANSFER = "bank_transfer"
    SEPA = "sepa"
    TIGO_MONEY = "tigo_money"
    CASH = "cash"
    IN_KIND = "in_kind"


class DonationFrequency(StrEnum):
    """Recurring donation frequency."""

    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


SOURCE_LABELS_ES: dict[str, str] = {
    "online": "En linea",
    "bank_transfer": "Transferencia bancaria",
    "sepa": "SEPA (Europa)",
    "tigo_money": "Tigo Money",
    "cash": "Efectivo",
    "in_kind": "Donacion en especie",
}

FREQUENCY_LABELS_ES: dict[str, str] = {
    "one_time": "Unica vez",
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "annual": "Anual",
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DonationKPI(BaseModel):
    """Single KPI metric."""

    label: str
    value: float
    unit: str
    change_percent: float | None = None
    trend: str = "stable"  # up, down, stable


class DonationSummary(BaseModel):
    """Donation summary with KPIs."""

    total_amount_pyg: float
    total_amount_eur: float
    donation_count: int
    unique_donors: int
    average_donation_pyg: float
    average_donation_eur: float
    recurring_percentage: float
    period_days: int
    kpis: list[DonationKPI]


class MonthlyTrend(BaseModel):
    """Monthly donation trend data point."""

    month: str
    year: int
    total_pyg: float
    total_eur: float
    count: int
    average_pyg: float


class DonationTrends(BaseModel):
    """Donation trends over time."""

    months: list[MonthlyTrend]
    period_months: int


class SourceBreakdown(BaseModel):
    """Donation breakdown by source."""

    source: str
    label: str
    amount_pyg: float
    count: int
    percentage: float


class CurrencyDistribution(BaseModel):
    """Currency distribution data."""

    currency: str
    total_amount: float
    count: int
    percentage: float
    average_amount: float


class TopDonor(BaseModel):
    """Top donor entry."""

    rank: int
    donor_name: str
    total_donated_pyg: float
    donation_count: int
    last_donation_date: str
    is_recurring: bool


class CampaignPerformance(BaseModel):
    """Campaign donation performance."""

    campaign_name: str
    goal_pyg: float
    raised_pyg: float
    progress_percent: float
    donor_count: int
    status: str


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_MONTHLY_TRENDS: list[dict] = [
    {
        "month": "Oct",
        "year": 2025,
        "total_pyg": 45_000_000,
        "total_eur": 5_400,
        "count": 42,
        "average_pyg": 1_071_429,
    },
    {
        "month": "Nov",
        "year": 2025,
        "total_pyg": 52_000_000,
        "total_eur": 6_200,
        "count": 48,
        "average_pyg": 1_083_333,
    },
    {
        "month": "Dic",
        "year": 2025,
        "total_pyg": 78_000_000,
        "total_eur": 9_500,
        "count": 67,
        "average_pyg": 1_164_179,
    },
    {
        "month": "Ene",
        "year": 2026,
        "total_pyg": 41_000_000,
        "total_eur": 4_800,
        "count": 38,
        "average_pyg": 1_078_947,
    },
    {
        "month": "Feb",
        "year": 2026,
        "total_pyg": 55_000_000,
        "total_eur": 6_600,
        "count": 51,
        "average_pyg": 1_078_431,
    },
    {
        "month": "Mar",
        "year": 2026,
        "total_pyg": 62_000_000,
        "total_eur": 7_400,
        "count": 56,
        "average_pyg": 1_107_143,
    },
]

SAMPLE_SOURCE_DATA: list[dict] = [
    {"source": "online", "amount_pyg": 120_000_000, "count": 145, "percentage": 36.0},
    {"source": "bank_transfer", "amount_pyg": 85_000_000, "count": 62, "percentage": 25.5},
    {"source": "sepa", "amount_pyg": 68_000_000, "count": 34, "percentage": 20.4},
    {"source": "tigo_money", "amount_pyg": 32_000_000, "count": 89, "percentage": 9.6},
    {"source": "cash", "amount_pyg": 18_000_000, "count": 15, "percentage": 5.4},
    {"source": "in_kind", "amount_pyg": 10_000_000, "count": 7, "percentage": 3.0},
]

SAMPLE_CURRENCY_DATA: list[dict] = [
    {
        "currency": "PYG",
        "total_amount": 213_000_000,
        "count": 248,
        "percentage": 64.0,
        "average_amount": 858_871,
    },
    {
        "currency": "EUR",
        "total_amount": 39_900,
        "count": 104,
        "percentage": 36.0,
        "average_amount": 383,
    },
]

SAMPLE_TOP_DONORS: list[dict] = [
    {
        "rank": 1,
        "donor_name": "Fundacion Esperanza",
        "total_donated_pyg": 45_000_000,
        "donation_count": 12,
        "last_donation_date": "2026-03-15",
        "is_recurring": True,
    },
    {
        "rank": 2,
        "donor_name": "Maria van der Berg",
        "total_donated_pyg": 32_000_000,
        "donation_count": 6,
        "last_donation_date": "2026-03-20",
        "is_recurring": True,
    },
    {
        "rank": 3,
        "donor_name": "Carlos Benitez",
        "total_donated_pyg": 18_000_000,
        "donation_count": 3,
        "last_donation_date": "2026-02-28",
        "is_recurring": False,
    },
    {
        "rank": 4,
        "donor_name": "Stichting Dierenwelzijn",
        "total_donated_pyg": 15_000_000,
        "donation_count": 4,
        "last_donation_date": "2026-03-10",
        "is_recurring": True,
    },
    {
        "rank": 5,
        "donor_name": "Ana Lopez",
        "total_donated_pyg": 12_000_000,
        "donation_count": 8,
        "last_donation_date": "2026-03-22",
        "is_recurring": True,
    },
    {
        "rank": 6,
        "donor_name": "Pedro Gonzalez",
        "total_donated_pyg": 9_500_000,
        "donation_count": 2,
        "last_donation_date": "2026-01-15",
        "is_recurring": False,
    },
    {
        "rank": 7,
        "donor_name": "Elena Ruiz",
        "total_donated_pyg": 8_000_000,
        "donation_count": 5,
        "last_donation_date": "2026-03-18",
        "is_recurring": True,
    },
    {
        "rank": 8,
        "donor_name": "Verein Tierschutz DE",
        "total_donated_pyg": 7_500_000,
        "donation_count": 3,
        "last_donation_date": "2026-02-20",
        "is_recurring": True,
    },
    {
        "rank": 9,
        "donor_name": "Roberto Acosta",
        "total_donated_pyg": 6_000_000,
        "donation_count": 1,
        "last_donation_date": "2026-03-01",
        "is_recurring": False,
    },
    {
        "rank": 10,
        "donor_name": "Sofia Martinez",
        "total_donated_pyg": 5_500_000,
        "donation_count": 4,
        "last_donation_date": "2026-03-25",
        "is_recurring": True,
    },
]

SAMPLE_CAMPAIGNS: list[dict] = [
    {
        "campaign_name": "Campana de Esterilizacion 2026",
        "goal_pyg": 50_000_000,
        "raised_pyg": 38_000_000,
        "progress_percent": 76.0,
        "donor_count": 45,
        "status": "active",
    },
    {
        "campaign_name": "Refugio de Emergencia Invernal",
        "goal_pyg": 80_000_000,
        "raised_pyg": 80_000_000,
        "progress_percent": 100.0,
        "donor_count": 92,
        "status": "completed",
    },
    {
        "campaign_name": "Equipamiento Veterinario",
        "goal_pyg": 120_000_000,
        "raised_pyg": 42_000_000,
        "progress_percent": 35.0,
        "donor_count": 28,
        "status": "active",
    },
    {
        "campaign_name": "Alimentacion Mensual",
        "goal_pyg": 15_000_000,
        "raised_pyg": 12_500_000,
        "progress_percent": 83.3,
        "donor_count": 67,
        "status": "active",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=DonationSummary)
async def get_donation_summary(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> DonationSummary:
    """Get donation KPI summary for a given period."""
    total_pyg = 333_000_000.0
    total_eur = 39_900.0
    count = 302
    unique = 187
    avg_pyg = total_pyg / count if count > 0 else 0
    avg_eur = total_eur / 104 if 104 > 0 else 0
    recurring_pct = 42.5

    kpis = [
        DonationKPI(
            label="Total recaudado (PYG)",
            value=total_pyg,
            unit=CURRENCY_PYG,
            change_percent=12.3,
            trend="up",
        ),
        DonationKPI(
            label="Total recaudado (EUR)",
            value=total_eur,
            unit=CURRENCY_EUR,
            change_percent=8.7,
            trend="up",
        ),
        DonationKPI(
            label="Donaciones recibidas",
            value=float(count),
            unit="donaciones",
            change_percent=5.2,
            trend="up",
        ),
        DonationKPI(
            label="Donantes unicos",
            value=float(unique),
            unit="donantes",
            change_percent=-2.1,
            trend="down",
        ),
    ]

    return DonationSummary(
        total_amount_pyg=total_pyg,
        total_amount_eur=total_eur,
        donation_count=count,
        unique_donors=unique,
        average_donation_pyg=avg_pyg,
        average_donation_eur=avg_eur,
        recurring_percentage=recurring_pct,
        period_days=period_days,
        kpis=kpis,
    )


@router.get("/trends", response_model=DonationTrends)
async def get_donation_trends(
    months: int = Query(default=6, ge=1, le=12),
) -> DonationTrends:
    """Get monthly donation trends."""
    trend_data = SAMPLE_MONTHLY_TRENDS[-months:]
    return DonationTrends(
        months=[MonthlyTrend(**t) for t in trend_data],
        period_months=months,
    )


@router.get("/by-source", response_model=list[SourceBreakdown])
async def get_donations_by_source(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> list[SourceBreakdown]:
    """Get donation breakdown by source channel."""
    return [
        SourceBreakdown(
            source=s["source"],
            label=SOURCE_LABELS_ES.get(s["source"], s["source"]),
            amount_pyg=s["amount_pyg"],
            count=s["count"],
            percentage=s["percentage"],
        )
        for s in SAMPLE_SOURCE_DATA
    ]


@router.get("/by-currency", response_model=list[CurrencyDistribution])
async def get_donations_by_currency(
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> list[CurrencyDistribution]:
    """Get donation distribution by currency."""
    return [CurrencyDistribution(**c) for c in SAMPLE_CURRENCY_DATA]


@router.get("/top-donors", response_model=list[TopDonor])
async def get_top_donors(
    limit: int = Query(default=TOP_DONORS_LIMIT, ge=1, le=50),
    period_days: int = Query(default=DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> list[TopDonor]:
    """Get top donors ranking."""
    return [TopDonor(**d) for d in SAMPLE_TOP_DONORS[:limit]]


@router.get("/campaigns", response_model=list[CampaignPerformance])
async def get_campaign_performance() -> list[CampaignPerformance]:
    """Get campaign donation performance."""
    return [CampaignPerformance(**c) for c in SAMPLE_CAMPAIGNS]
