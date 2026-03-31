"""Animal intake and outcome analytics API.

Provides analytics on animal intake (arrivals) and outcomes (adoptions,
transfers, returns to owner, euthanasia) with trend analysis, demographic
breakdowns, and length-of-stay metrics.

Endpoints:
    GET /api/admin/analytics/animals/overview    -- intake/outcome overview
    GET /api/admin/analytics/animals/intake       -- intake breakdown
    GET /api/admin/analytics/animals/outcomes      -- outcome breakdown
    GET /api/admin/analytics/animals/demographics  -- species/breed/age analysis
    GET /api/admin/analytics/animals/length-of-stay -- LOS statistics
    GET /api/admin/analytics/animals/trends        -- monthly trends
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/animals",
    tags=["animal-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365
MONTHS_FOR_TREND = 12


class IntakeSource(StrEnum):
    """How animals arrive at the shelter."""

    STRAY_CAPTURE = "stray_capture"
    OWNER_SURRENDER = "owner_surrender"
    TRANSFER_IN = "transfer_in"
    CONFISCATION = "confiscation"
    BORN_IN_SHELTER = "born_in_shelter"
    RETURN = "return"


class OutcomeType(StrEnum):
    """How animals leave the shelter."""

    ADOPTION = "adoption"
    TRANSFER_OUT = "transfer_out"
    RETURN_TO_OWNER = "return_to_owner"
    FOSTER = "foster"
    DECEASED = "deceased"
    ESCAPED = "escaped"


class Species(StrEnum):
    """Animal species tracked."""

    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


INTAKE_LABELS_ES: dict[str, str] = {
    "stray_capture": "Captura callejera",
    "owner_surrender": "Entrega del dueno",
    "transfer_in": "Transferencia entrada",
    "confiscation": "Decomiso",
    "born_in_shelter": "Nacido en refugio",
    "return": "Devolucion",
}

OUTCOME_LABELS_ES: dict[str, str] = {
    "adoption": "Adopcion",
    "transfer_out": "Transferencia salida",
    "return_to_owner": "Devolucion al dueno",
    "foster": "Acogida temporal",
    "deceased": "Fallecido",
    "escaped": "Escapado",
}

SPECIES_LABELS_ES: dict[str, str] = {
    "dog": "Perro",
    "cat": "Gato",
    "other": "Otro",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class IntakeOutcomeOverview(BaseModel):
    """High-level intake/outcome summary."""

    period_days: int
    total_intake: int
    total_outcomes: int
    current_population: int
    net_change: int
    intake_rate_per_day: float
    outcome_rate_per_day: float
    live_release_rate_pct: float
    average_length_of_stay_days: float
    generated_at: str


class IntakeBreakdown(BaseModel):
    """Intake by source."""

    period_days: int
    total: int
    by_source: list[dict[str, Any]]
    by_species: list[dict[str, Any]]
    monthly_trend: list[dict[str, Any]]


class OutcomeBreakdown(BaseModel):
    """Outcome by type."""

    period_days: int
    total: int
    by_type: list[dict[str, Any]]
    by_species: list[dict[str, Any]]
    live_release_rate_pct: float
    monthly_trend: list[dict[str, Any]]


class DemographicAnalysis(BaseModel):
    """Demographics of current population."""

    total_population: int
    by_species: list[dict[str, Any]]
    by_age_group: list[dict[str, Any]]
    by_sex: list[dict[str, Any]]
    by_size: list[dict[str, Any]]
    sterilization_rate_pct: float


class LengthOfStayStats(BaseModel):
    """Length of stay statistics."""

    average_days: float
    median_days: float
    min_days: int
    max_days: int
    by_species: list[dict[str, Any]]
    by_outcome: list[dict[str, Any]]
    distribution: list[dict[str, Any]]


class MonthlyTrend(BaseModel):
    """Monthly intake/outcome trends."""

    months: int
    data: list[dict[str, Any]]
    intake_trend: str
    outcome_trend: str
    population_trend: str


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

MONTHLY_DATA = [
    {
        "month": "2025-04",
        "intake": 28,
        "outcomes": 22,
        "population": 156,
        "adoptions": 15,
        "transfers": 4,
        "returns": 3,
    },
    {
        "month": "2025-05",
        "intake": 32,
        "outcomes": 25,
        "population": 163,
        "adoptions": 18,
        "transfers": 3,
        "returns": 4,
    },
    {
        "month": "2025-06",
        "intake": 25,
        "outcomes": 28,
        "population": 160,
        "adoptions": 20,
        "transfers": 5,
        "returns": 3,
    },
    {
        "month": "2025-07",
        "intake": 35,
        "outcomes": 20,
        "population": 175,
        "adoptions": 12,
        "transfers": 4,
        "returns": 4,
    },
    {
        "month": "2025-08",
        "intake": 30,
        "outcomes": 27,
        "population": 178,
        "adoptions": 19,
        "transfers": 5,
        "returns": 3,
    },
    {
        "month": "2025-09",
        "intake": 22,
        "outcomes": 30,
        "population": 170,
        "adoptions": 22,
        "transfers": 5,
        "returns": 3,
    },
    {
        "month": "2025-10",
        "intake": 27,
        "outcomes": 24,
        "population": 173,
        "adoptions": 16,
        "transfers": 4,
        "returns": 4,
    },
    {
        "month": "2025-11",
        "intake": 33,
        "outcomes": 26,
        "population": 180,
        "adoptions": 18,
        "transfers": 5,
        "returns": 3,
    },
    {
        "month": "2025-12",
        "intake": 38,
        "outcomes": 35,
        "population": 183,
        "adoptions": 25,
        "transfers": 6,
        "returns": 4,
    },
    {
        "month": "2026-01",
        "intake": 29,
        "outcomes": 23,
        "population": 189,
        "adoptions": 15,
        "transfers": 4,
        "returns": 4,
    },
    {
        "month": "2026-02",
        "intake": 26,
        "outcomes": 28,
        "population": 187,
        "adoptions": 20,
        "transfers": 5,
        "returns": 3,
    },
    {
        "month": "2026-03",
        "intake": 31,
        "outcomes": 24,
        "population": 194,
        "adoptions": 16,
        "transfers": 5,
        "returns": 3,
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=IntakeOutcomeOverview)
async def get_overview(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> IntakeOutcomeOverview:
    """Get intake/outcome overview."""
    total_intake = sum(m["intake"] for m in MONTHLY_DATA[-3:])
    total_outcomes = sum(m["outcomes"] for m in MONTHLY_DATA[-3:])
    total_adoptions = sum(m["adoptions"] for m in MONTHLY_DATA[-3:])
    current_pop = MONTHLY_DATA[-1]["population"]

    live_release = round((total_adoptions / total_outcomes) * 100, 1) if total_outcomes else 0.0

    return IntakeOutcomeOverview(
        period_days=period_days,
        total_intake=total_intake,
        total_outcomes=total_outcomes,
        current_population=current_pop,
        net_change=total_intake - total_outcomes,
        intake_rate_per_day=round(total_intake / period_days, 1),
        outcome_rate_per_day=round(total_outcomes / period_days, 1),
        live_release_rate_pct=live_release,
        average_length_of_stay_days=18.5,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.get("/intake", response_model=IntakeBreakdown)
async def get_intake_breakdown(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> IntakeBreakdown:
    """Get intake breakdown by source and species."""
    total = sum(m["intake"] for m in MONTHLY_DATA[-3:])

    return IntakeBreakdown(
        period_days=period_days,
        total=total,
        by_source=[
            {"source": "stray_capture", "label": "Captura callejera", "count": 35, "pct": 40.7},
            {"source": "owner_surrender", "label": "Entrega del dueno", "count": 22, "pct": 25.6},
            {"source": "transfer_in", "label": "Transferencia", "count": 12, "pct": 14.0},
            {"source": "confiscation", "label": "Decomiso", "count": 8, "pct": 9.3},
            {"source": "born_in_shelter", "label": "Nacido en refugio", "count": 5, "pct": 5.8},
            {"source": "return", "label": "Devolucion", "count": 4, "pct": 4.7},
        ],
        by_species=[
            {"species": "dog", "label": "Perros", "count": 52, "pct": 60.5},
            {"species": "cat", "label": "Gatos", "count": 28, "pct": 32.6},
            {"species": "other", "label": "Otros", "count": 6, "pct": 7.0},
        ],
        monthly_trend=[{"month": m["month"], "count": m["intake"]} for m in MONTHLY_DATA[-6:]],
    )


@router.get("/outcomes", response_model=OutcomeBreakdown)
async def get_outcome_breakdown(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> OutcomeBreakdown:
    """Get outcome breakdown by type and species."""
    total = sum(m["outcomes"] for m in MONTHLY_DATA[-3:])
    adoptions = sum(m["adoptions"] for m in MONTHLY_DATA[-3:])

    return OutcomeBreakdown(
        period_days=period_days,
        total=total,
        by_type=[
            {"type": "adoption", "label": "Adopcion", "count": adoptions, "pct": 68.0},
            {"type": "transfer_out", "label": "Transferencia", "count": 14, "pct": 18.7},
            {"type": "return_to_owner", "label": "Devolucion al dueno", "count": 5, "pct": 6.7},
            {"type": "foster", "label": "Acogida temporal", "count": 3, "pct": 4.0},
            {"type": "deceased", "label": "Fallecido", "count": 2, "pct": 2.7},
        ],
        by_species=[
            {"species": "dog", "label": "Perros", "count": 42, "pct": 56.0},
            {"species": "cat", "label": "Gatos", "count": 28, "pct": 37.3},
            {"species": "other", "label": "Otros", "count": 5, "pct": 6.7},
        ],
        live_release_rate_pct=round((adoptions / total) * 100, 1) if total else 0.0,
        monthly_trend=[{"month": m["month"], "count": m["outcomes"]} for m in MONTHLY_DATA[-6:]],
    )


@router.get("/demographics", response_model=DemographicAnalysis)
async def get_demographics() -> DemographicAnalysis:
    """Get demographic analysis of current population."""
    return DemographicAnalysis(
        total_population=194,
        by_species=[
            {"species": "dog", "label": "Perros", "count": 112, "pct": 57.7},
            {"species": "cat", "label": "Gatos", "count": 68, "pct": 35.1},
            {"species": "other", "label": "Otros", "count": 14, "pct": 7.2},
        ],
        by_age_group=[
            {
                "group": "puppy_kitten",
                "label": "Cachorro/Gatito (<1 ano)",
                "count": 45,
                "pct": 23.2,
            },
            {"group": "young", "label": "Joven (1-3 anos)", "count": 62, "pct": 32.0},
            {"group": "adult", "label": "Adulto (3-8 anos)", "count": 58, "pct": 29.9},
            {"group": "senior", "label": "Senior (8+ anos)", "count": 29, "pct": 14.9},
        ],
        by_sex=[
            {"sex": "male", "label": "Macho", "count": 98, "pct": 50.5},
            {"sex": "female", "label": "Hembra", "count": 96, "pct": 49.5},
        ],
        by_size=[
            {"size": "small", "label": "Pequeno", "count": 52, "pct": 26.8},
            {"size": "medium", "label": "Mediano", "count": 78, "pct": 40.2},
            {"size": "large", "label": "Grande", "count": 50, "pct": 25.8},
            {"size": "extra_large", "label": "Extra grande", "count": 14, "pct": 7.2},
        ],
        sterilization_rate_pct=72.3,
    )


@router.get("/length-of-stay", response_model=LengthOfStayStats)
async def get_length_of_stay() -> LengthOfStayStats:
    """Get length-of-stay statistics."""
    return LengthOfStayStats(
        average_days=18.5,
        median_days=14.0,
        min_days=1,
        max_days=365,
        by_species=[
            {"species": "dog", "label": "Perros", "avg_days": 21.3, "median_days": 16.0},
            {"species": "cat", "label": "Gatos", "avg_days": 14.8, "median_days": 11.0},
            {"species": "other", "label": "Otros", "avg_days": 25.1, "median_days": 20.0},
        ],
        by_outcome=[
            {"outcome": "adoption", "label": "Adopcion", "avg_days": 22.4},
            {"outcome": "transfer_out", "label": "Transferencia", "avg_days": 12.1},
            {"outcome": "return_to_owner", "label": "Devolucion", "avg_days": 5.3},
            {"outcome": "foster", "label": "Acogida", "avg_days": 8.7},
        ],
        distribution=[
            {"range": "0-7 dias", "count": 35, "pct": 18.0},
            {"range": "8-14 dias", "count": 48, "pct": 24.7},
            {"range": "15-30 dias", "count": 52, "pct": 26.8},
            {"range": "31-60 dias", "count": 32, "pct": 16.5},
            {"range": "61-90 dias", "count": 15, "pct": 7.7},
            {"range": "90+ dias", "count": 12, "pct": 6.2},
        ],
    )


@router.get("/trends", response_model=MonthlyTrend)
async def get_trends(
    months: int = Query(MONTHS_FOR_TREND, ge=1, le=24),
) -> MonthlyTrend:
    """Get monthly intake/outcome trends."""
    data = MONTHLY_DATA[-months:]

    intakes = [m["intake"] for m in data]
    outcomes = [m["outcomes"] for m in data]
    populations = [m["population"] for m in data]

    def _trend(values: list[int]) -> str:
        if len(values) < 2:
            return "stable"
        first_half = sum(values[: len(values) // 2])
        second_half = sum(values[len(values) // 2 :])
        if second_half > first_half * 1.1:
            return "increasing"
        if second_half < first_half * 0.9:
            return "decreasing"
        return "stable"

    return MonthlyTrend(
        months=len(data),
        data=data,
        intake_trend=_trend(intakes),
        outcome_trend=_trend(outcomes),
        population_trend=_trend(populations),
    )
