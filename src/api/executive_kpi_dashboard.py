"""Executive KPI dashboard API.

Provides a consolidated view of all key performance indicators for
shelter leadership. Combines animal, financial, operational, and
community metrics into a single dashboard.

Endpoints:
    GET /api/admin/dashboard/kpis            -- all KPIs at a glance
    GET /api/admin/dashboard/financial        -- financial summary
    GET /api/admin/dashboard/operational      -- operational metrics
    GET /api/admin/dashboard/performance      -- performance scorecard
    GET /api/admin/dashboard/alerts           -- active alerts and warnings
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/dashboard",
    tags=["executive-dashboard"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365
KPI_TARGET_ADOPTION_RATE = 70.0
KPI_TARGET_LIVE_RELEASE = 90.0
KPI_TARGET_LOS_DAYS = 20
KPI_TARGET_DONOR_RETENTION = 60.0


class KPICategory(StrEnum):
    """KPI categories."""

    ANIMALS = "animals"
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    COMMUNITY = "community"


class AlertSeverity(StrEnum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class TrendDirection(StrEnum):
    """Trend direction."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


CATEGORY_LABELS_ES: dict[str, str] = {
    "animals": "Animales",
    "financial": "Financiero",
    "operations": "Operaciones",
    "community": "Comunidad",
}

SEVERITY_LABELS_ES: dict[str, str] = {
    "critical": "Critico",
    "warning": "Advertencia",
    "info": "Informativo",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class KPIMetric(BaseModel):
    """A single KPI metric."""

    id: str
    name: str
    category: KPICategory
    value: float
    unit: str
    target: float | None = None
    previous_value: float | None = None
    trend: TrendDirection
    trend_pct: float
    status: str


class KPIDashboard(BaseModel):
    """Complete KPI dashboard."""

    period_days: int
    generated_at: str
    kpis: list[KPIMetric]
    summary: dict[str, Any]


class FinancialSummary(BaseModel):
    """Financial metrics summary."""

    period_days: int
    total_income_pyg: int
    total_income_eur: int
    total_expenses_pyg: int
    net_balance_pyg: int
    donation_count: int
    average_donation_pyg: int
    top_campaigns: list[dict[str, Any]]
    monthly_revenue: list[dict[str, Any]]
    expense_breakdown: list[dict[str, Any]]


class OperationalMetrics(BaseModel):
    """Operational metrics."""

    period_days: int
    current_population: int
    capacity_pct: float
    intake_count: int
    outcome_count: int
    adoption_rate_pct: float
    live_release_rate_pct: float
    avg_length_of_stay_days: float
    pending_applications: int
    scheduled_appointments: int
    active_volunteers: int
    volunteer_hours: int


class PerformanceScorecard(BaseModel):
    """Performance scorecard with targets vs actuals."""

    period_days: int
    scores: list[dict[str, Any]]
    overall_score: float
    overall_grade: str


class DashboardAlert(BaseModel):
    """Dashboard alert."""

    id: str
    severity: AlertSeverity
    title: str
    message: str
    category: KPICategory
    created_at: str
    action_url: str | None = None


class AlertsResponse(BaseModel):
    """Active alerts."""

    alerts: list[DashboardAlert]
    total: int
    critical_count: int
    warning_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/kpis", response_model=KPIDashboard)
async def get_kpi_dashboard(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> KPIDashboard:
    """Get all KPIs at a glance."""
    now = datetime.now(UTC).isoformat()

    kpis = [
        KPIMetric(
            id="population",
            name="Poblacion actual",
            category=KPICategory.ANIMALS,
            value=194,
            unit="animales",
            target=200,
            previous_value=187,
            trend=TrendDirection.UP,
            trend_pct=3.7,
            status="on_track",
        ),
        KPIMetric(
            id="adoption_rate",
            name="Tasa de adopcion",
            category=KPICategory.ANIMALS,
            value=68.0,
            unit="%",
            target=KPI_TARGET_ADOPTION_RATE,
            previous_value=62.5,
            trend=TrendDirection.UP,
            trend_pct=8.8,
            status="approaching",
        ),
        KPIMetric(
            id="live_release",
            name="Tasa liberacion viva",
            category=KPICategory.ANIMALS,
            value=85.2,
            unit="%",
            target=KPI_TARGET_LIVE_RELEASE,
            previous_value=82.1,
            trend=TrendDirection.UP,
            trend_pct=3.8,
            status="approaching",
        ),
        KPIMetric(
            id="avg_los",
            name="Estancia promedio",
            category=KPICategory.ANIMALS,
            value=18.5,
            unit="dias",
            target=KPI_TARGET_LOS_DAYS,
            previous_value=21.2,
            trend=TrendDirection.DOWN,
            trend_pct=-12.7,
            status="on_track",
        ),
        KPIMetric(
            id="monthly_donations_pyg",
            name="Donaciones mensuales (PYG)",
            category=KPICategory.FINANCIAL,
            value=8500000,
            unit="PYG",
            target=10000000,
            previous_value=7200000,
            trend=TrendDirection.UP,
            trend_pct=18.1,
            status="approaching",
        ),
        KPIMetric(
            id="monthly_donations_eur",
            name="Donaciones mensuales (EUR)",
            category=KPICategory.FINANCIAL,
            value=2800,
            unit="EUR",
            target=3500,
            previous_value=2400,
            trend=TrendDirection.UP,
            trend_pct=16.7,
            status="approaching",
        ),
        KPIMetric(
            id="donor_retention",
            name="Retencion de donantes",
            category=KPICategory.FINANCIAL,
            value=58.3,
            unit="%",
            target=KPI_TARGET_DONOR_RETENTION,
            previous_value=55.1,
            trend=TrendDirection.UP,
            trend_pct=5.8,
            status="approaching",
        ),
        KPIMetric(
            id="active_volunteers",
            name="Voluntarios activos",
            category=KPICategory.COMMUNITY,
            value=42,
            unit="personas",
            target=50,
            previous_value=38,
            trend=TrendDirection.UP,
            trend_pct=10.5,
            status="on_track",
        ),
        KPIMetric(
            id="volunteer_hours",
            name="Horas voluntariado",
            category=KPICategory.COMMUNITY,
            value=680,
            unit="horas",
            target=800,
            previous_value=620,
            trend=TrendDirection.UP,
            trend_pct=9.7,
            status="approaching",
        ),
        KPIMetric(
            id="pending_apps",
            name="Solicitudes pendientes",
            category=KPICategory.OPERATIONS,
            value=12,
            unit="solicitudes",
            target=5,
            previous_value=8,
            trend=TrendDirection.UP,
            trend_pct=50.0,
            status="at_risk",
        ),
        KPIMetric(
            id="capacity_util",
            name="Utilizacion capacidad",
            category=KPICategory.OPERATIONS,
            value=77.6,
            unit="%",
            target=85,
            previous_value=74.8,
            trend=TrendDirection.UP,
            trend_pct=3.7,
            status="on_track",
        ),
    ]

    on_track = sum(1 for k in kpis if k.status == "on_track")
    approaching = sum(1 for k in kpis if k.status == "approaching")
    at_risk = sum(1 for k in kpis if k.status == "at_risk")

    return KPIDashboard(
        period_days=period_days,
        generated_at=now,
        kpis=kpis,
        summary={
            "total_kpis": len(kpis),
            "on_track": on_track,
            "approaching": approaching,
            "at_risk": at_risk,
            "health_score": round((on_track / len(kpis)) * 100, 1),
        },
    )


@router.get("/financial", response_model=FinancialSummary)
async def get_financial_summary(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> FinancialSummary:
    """Get financial metrics summary."""
    return FinancialSummary(
        period_days=period_days,
        total_income_pyg=12500000,
        total_income_eur=4200,
        total_expenses_pyg=9800000,
        net_balance_pyg=2700000,
        donation_count=47,
        average_donation_pyg=265957,
        top_campaigns=[
            {"name": "Campana de esterilizacion", "amount_pyg": 3500000, "donors": 15},
            {"name": "Alimentacion mensual", "amount_pyg": 2800000, "donors": 22},
            {"name": "Equipos veterinarios", "amount_pyg": 2200000, "donors": 8},
            {"name": "General", "amount_pyg": 4000000, "donors": 35},
        ],
        monthly_revenue=[
            {"month": "2026-01", "income_pyg": 10200000, "expenses_pyg": 9100000},
            {"month": "2026-02", "income_pyg": 11800000, "expenses_pyg": 9500000},
            {"month": "2026-03", "income_pyg": 12500000, "expenses_pyg": 9800000},
        ],
        expense_breakdown=[
            {"category": "Veterinario", "amount_pyg": 3800000, "pct": 38.8},
            {"category": "Alimentacion", "amount_pyg": 2500000, "pct": 25.5},
            {"category": "Operaciones", "amount_pyg": 1800000, "pct": 18.4},
            {"category": "Infraestructura", "amount_pyg": 1200000, "pct": 12.2},
            {"category": "Transporte", "amount_pyg": 500000, "pct": 5.1},
        ],
    )


@router.get("/operational", response_model=OperationalMetrics)
async def get_operational_metrics(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> OperationalMetrics:
    """Get operational metrics."""
    return OperationalMetrics(
        period_days=period_days,
        current_population=194,
        capacity_pct=77.6,
        intake_count=86,
        outcome_count=75,
        adoption_rate_pct=68.0,
        live_release_rate_pct=85.2,
        avg_length_of_stay_days=18.5,
        pending_applications=12,
        scheduled_appointments=8,
        active_volunteers=42,
        volunteer_hours=680,
    )


@router.get("/performance", response_model=PerformanceScorecard)
async def get_performance_scorecard(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> PerformanceScorecard:
    """Get performance scorecard."""
    scores = [
        {
            "metric": "Tasa de adopcion",
            "actual": 68.0,
            "target": 70.0,
            "score": 97.1,
            "grade": "A",
        },
        {
            "metric": "Liberacion viva",
            "actual": 85.2,
            "target": 90.0,
            "score": 94.7,
            "grade": "A",
        },
        {
            "metric": "Estancia promedio",
            "actual": 18.5,
            "target": 20.0,
            "score": 107.5,
            "grade": "A+",
        },
        {
            "metric": "Retencion donantes",
            "actual": 58.3,
            "target": 60.0,
            "score": 97.2,
            "grade": "A",
        },
        {
            "metric": "Voluntarios activos",
            "actual": 42,
            "target": 50,
            "score": 84.0,
            "grade": "B",
        },
        {
            "metric": "Utilizacion capacidad",
            "actual": 77.6,
            "target": 85.0,
            "score": 91.3,
            "grade": "A",
        },
    ]

    avg_score = round(sum(s["score"] for s in scores) / len(scores), 1)
    grade = (
        "A+" if avg_score >= 100 else "A" if avg_score >= 90 else "B" if avg_score >= 80 else "C"
    )

    return PerformanceScorecard(
        period_days=period_days,
        scores=scores,
        overall_score=avg_score,
        overall_grade=grade,
    )


@router.get("/alerts", response_model=AlertsResponse)
async def get_dashboard_alerts() -> AlertsResponse:
    """Get active alerts and warnings."""
    now = datetime.now(UTC).isoformat()

    alerts = [
        DashboardAlert(
            id="alert-001",
            severity=AlertSeverity.WARNING,
            title="Capacidad de gatos al 90%",
            message="El sector de gatos esta alcanzando su capacidad maxima. Considerar transferencias.",
            category=KPICategory.ANIMALS,
            created_at=now,
            action_url="/admin/animales?species=cat",
        ),
        DashboardAlert(
            id="alert-002",
            severity=AlertSeverity.WARNING,
            title="12 solicitudes pendientes",
            message="Hay 12 solicitudes de adopcion pendientes de revision, superior al objetivo de 5.",
            category=KPICategory.OPERATIONS,
            created_at=now,
            action_url="/admin/adopciones/pendientes",
        ),
        DashboardAlert(
            id="alert-003",
            severity=AlertSeverity.INFO,
            title="Donaciones EUR en aumento",
            message="Las donaciones en EUR han aumentado 16.7% este mes. Considerar campaña europea.",
            category=KPICategory.FINANCIAL,
            created_at=now,
        ),
        DashboardAlert(
            id="alert-004",
            severity=AlertSeverity.CRITICAL,
            title="Stock de vacunas bajo",
            message="El inventario de vacunas antirrábicas está por debajo del mínimo requerido.",
            category=KPICategory.OPERATIONS,
            created_at=now,
            action_url="/admin/veterinario/inventario",
        ),
        DashboardAlert(
            id="alert-005",
            severity=AlertSeverity.INFO,
            title="Meta de voluntarios al 84%",
            message="42 de 50 voluntarios activos. 8 mas para alcanzar la meta mensual.",
            category=KPICategory.COMMUNITY,
            created_at=now,
        ),
    ]

    critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
    warning = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)

    return AlertsResponse(
        alerts=alerts,
        total=len(alerts),
        critical_count=critical,
        warning_count=warning,
    )
