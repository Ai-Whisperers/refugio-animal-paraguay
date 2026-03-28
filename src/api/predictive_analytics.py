"""Predictive analytics and forecasting API (RAP-639).

Provides forecasting endpoints for shelter operations including animal
intake/adoption predictions, donation forecasting, resource needs,
and capacity planning.

Endpoints:
    GET /api/admin/analytics/predictions/intake       -- animal intake forecast
    GET /api/admin/analytics/predictions/adoptions     -- adoption rate forecast
    GET /api/admin/analytics/predictions/donations     -- donation forecast
    GET /api/admin/analytics/predictions/capacity      -- shelter capacity forecast
    GET /api/admin/analytics/predictions/resources     -- resource needs forecast
    GET /api/admin/analytics/predictions/summary       -- overall prediction summary
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/predictions",
    tags=["predictive-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_FORECAST_MONTHS = 3
MAX_FORECAST_MONTHS = 12
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.70
CONFIDENCE_LOW = 0.55


class ForecastType(StrEnum):
    INTAKE = "intake"
    ADOPTIONS = "adoptions"
    DONATIONS = "donations"
    CAPACITY = "capacity"
    RESOURCES = "resources"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnimalCategory(StrEnum):
    DOGS = "dogs"
    CATS = "cats"
    OTHER = "other"


FORECAST_LABELS_ES: dict[str, str] = {
    ForecastType.INTAKE: "Ingreso de animales",
    ForecastType.ADOPTIONS: "Adopciones",
    ForecastType.DONATIONS: "Donaciones",
    ForecastType.CAPACITY: "Capacidad",
    ForecastType.RESOURCES: "Recursos",
}

CATEGORY_LABELS_ES: dict[str, str] = {
    AnimalCategory.DOGS: "Perros",
    AnimalCategory.CATS: "Gatos",
    AnimalCategory.OTHER: "Otros",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ForecastPoint(BaseModel):
    month: str
    predicted: float
    lower_bound: float
    upper_bound: float
    confidence: float


class IntakeForecast(BaseModel):
    forecast_months: int
    by_category: dict[str, list[ForecastPoint]]
    total_predicted: int
    confidence_level: ConfidenceLevel
    factors: list[str]


class AdoptionForecast(BaseModel):
    forecast_months: int
    monthly: list[ForecastPoint]
    total_predicted: int
    adoption_rate_trend: str
    bottlenecks: list[str]


class DonationForecast(BaseModel):
    forecast_months: int
    monthly_pyg: list[ForecastPoint]
    monthly_eur: list[ForecastPoint]
    total_predicted_pyg: int
    total_predicted_eur: int
    seasonal_factors: list[dict[str, Any]]


class CapacityForecast(BaseModel):
    forecast_months: int
    monthly: list[ForecastPoint]
    current_occupancy_pct: float
    predicted_peak_pct: float
    peak_month: str
    recommendations: list[str]


class ResourceForecast(BaseModel):
    forecast_months: int
    food_kg: list[ForecastPoint]
    medical_supplies: list[ForecastPoint]
    volunteer_hours: list[ForecastPoint]
    budget_needed_pyg: int


class PredictionSummary(BaseModel):
    generated_at: str
    forecast_months: int
    highlights: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    opportunities: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Sample data generators
# ---------------------------------------------------------------------------

FORECAST_MONTHS_LIST = [
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09",
    "2026-10",
    "2026-11",
    "2026-12",
    "2027-01",
    "2027-02",
    "2027-03",
]


def _make_points(
    months: list[str], base: float, growth: float, variance: float
) -> list[ForecastPoint]:
    points = []
    val = base
    for month in months:
        val = val * (1 + growth)
        lower = val * (1 - variance)
        upper = val * (1 + variance)
        conf = CONFIDENCE_HIGH if variance < 0.15 else CONFIDENCE_MEDIUM
        points.append(
            ForecastPoint(
                month=month,
                predicted=round(val, 1),
                lower_bound=round(lower, 1),
                upper_bound=round(upper, 1),
                confidence=conf,
            )
        )
    return points


def _generate_intake(n: int) -> IntakeForecast:
    months = FORECAST_MONTHS_LIST[:n]
    return IntakeForecast(
        forecast_months=n,
        by_category={
            AnimalCategory.DOGS: _make_points(months, 18, 0.03, 0.12),
            AnimalCategory.CATS: _make_points(months, 12, 0.05, 0.15),
            AnimalCategory.OTHER: _make_points(months, 3, 0.02, 0.20),
        },
        total_predicted=int(sum(p.predicted for p in _make_points(months, 33, 0.035, 0.13))),
        confidence_level=ConfidenceLevel.MEDIUM,
        factors=[
            "Temporada de cria (octubre-marzo) aumenta ingresos",
            "Campanas de esterilizacion reducen ingresos a largo plazo",
            "Abandonos aumentan en epoca de vacaciones",
        ],
    )


def _generate_adoptions(n: int) -> AdoptionForecast:
    months = FORECAST_MONTHS_LIST[:n]
    return AdoptionForecast(
        forecast_months=n,
        monthly=_make_points(months, 15, 0.04, 0.10),
        total_predicted=int(sum(p.predicted for p in _make_points(months, 15, 0.04, 0.10))),
        adoption_rate_trend="increasing",
        bottlenecks=[
            "Proceso de verificacion toma 5+ dias promedio",
            "Falta de voluntarios para visitas domiciliarias",
            "Limite de adopciones simultaneas por adoptante",
        ],
    )


def _generate_donations(n: int) -> DonationForecast:
    months = FORECAST_MONTHS_LIST[:n]
    return DonationForecast(
        forecast_months=n,
        monthly_pyg=_make_points(months, 2500000, 0.05, 0.18),
        monthly_eur=_make_points(months, 450, 0.03, 0.15),
        total_predicted_pyg=int(
            sum(p.predicted for p in _make_points(months, 2500000, 0.05, 0.18))
        ),
        total_predicted_eur=int(sum(p.predicted for p in _make_points(months, 450, 0.03, 0.15))),
        seasonal_factors=[
            {"month": "Diciembre", "factor": 1.8, "reason": "Temporada navidena"},
            {"month": "Marzo", "factor": 1.3, "reason": "Dia del animal"},
            {"month": "Julio", "factor": 0.7, "reason": "Temporada baja"},
        ],
    )


def _generate_capacity(n: int) -> CapacityForecast:
    months = FORECAST_MONTHS_LIST[:n]
    return CapacityForecast(
        forecast_months=n,
        monthly=_make_points(months, 72, 0.02, 0.08),
        current_occupancy_pct=72.0,
        predicted_peak_pct=89.5,
        peak_month="2026-11",
        recommendations=[
            "Expandir area de gatos antes de octubre",
            "Incrementar campanas de adopcion en septiembre",
            "Coordinar con refugios aliados para redistribucion",
            "Preparar plan de emergencia para capacidad >90%",
        ],
    )


def _generate_resources(n: int) -> ResourceForecast:
    months = FORECAST_MONTHS_LIST[:n]
    return ResourceForecast(
        forecast_months=n,
        food_kg=_make_points(months, 850, 0.03, 0.10),
        medical_supplies=_make_points(months, 120, 0.04, 0.15),
        volunteer_hours=_make_points(months, 280, 0.05, 0.12),
        budget_needed_pyg=45000000,
    )


def _generate_summary(n: int) -> PredictionSummary:
    return PredictionSummary(
        generated_at=datetime.now(UTC).isoformat(),
        forecast_months=n,
        highlights=[
            {
                "title": "Adopciones en aumento",
                "description": "Tasa de adopcion proyectada +15% en proximos 3 meses",
                "impact": "positive",
            },
            {
                "title": "Donaciones estables",
                "description": "Ingresos por donaciones se mantienen con crecimiento del 5%",
                "impact": "positive",
            },
            {
                "title": "Pico de capacidad en noviembre",
                "description": "Se espera 89.5% de ocupacion — preparar plan de contingencia",
                "impact": "warning",
            },
        ],
        risks=[
            {
                "title": "Temporada de cria",
                "probability": "high",
                "impact": "Aumento de 30-40% en ingresos de animales",
                "mitigation": "Intensificar campanas de esterilizacion",
            },
            {
                "title": "Escasez de voluntarios",
                "probability": "medium",
                "impact": "Reduccion en horas de servicio y visitas domiciliarias",
                "mitigation": "Lanzar campana de reclutamiento en universidades",
            },
        ],
        opportunities=[
            {
                "title": "Temporada navidena",
                "description": "Historicamente las donaciones aumentan 80% en diciembre",
                "action": "Preparar campana de recaudacion navidena",
            },
            {
                "title": "Alianzas con veterinarias",
                "description": "3 clinicas interesadas en programa de descuentos",
                "action": "Formalizar convenios antes de junio",
            },
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/intake", response_model=IntakeForecast)
async def get_intake_forecast(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> IntakeForecast:
    """Get animal intake forecast."""
    return _generate_intake(months)


@router.get("/adoptions", response_model=AdoptionForecast)
async def get_adoption_forecast(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> AdoptionForecast:
    """Get adoption rate forecast."""
    return _generate_adoptions(months)


@router.get("/donations", response_model=DonationForecast)
async def get_donation_forecast(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> DonationForecast:
    """Get donation forecast."""
    return _generate_donations(months)


@router.get("/capacity", response_model=CapacityForecast)
async def get_capacity_forecast(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> CapacityForecast:
    """Get shelter capacity forecast."""
    return _generate_capacity(months)


@router.get("/resources", response_model=ResourceForecast)
async def get_resources_forecast(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> ResourceForecast:
    """Get resource needs forecast."""
    return _generate_resources(months)


@router.get("/summary", response_model=PredictionSummary)
async def get_prediction_summary(
    months: int = Query(DEFAULT_FORECAST_MONTHS, ge=1, le=MAX_FORECAST_MONTHS),
) -> PredictionSummary:
    """Get overall prediction summary with highlights, risks, and opportunities."""
    return _generate_summary(months)
