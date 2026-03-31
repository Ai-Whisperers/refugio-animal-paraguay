"""Veterinary care analytics API.

Provides aggregate statistics on veterinary treatments, vaccinations,
sterilizations, and health outcomes for shelter animals.

Endpoints:
    GET /api/admin/analytics/veterinary/summary        -- overall vet care summary
    GET /api/admin/analytics/veterinary/treatments      -- treatment breakdown
    GET /api/admin/analytics/veterinary/vaccinations     -- vaccination stats
    GET /api/admin/analytics/veterinary/sterilizations   -- sterilization rates
    GET /api/admin/analytics/veterinary/costs            -- cost analysis
    GET /api/admin/analytics/veterinary/trends           -- monthly trends
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/veterinary",
    tags=["vet-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365
CURRENCY_PYG = "PYG"
COST_PRECISION = 0


class TreatmentCategory(StrEnum):
    """Categories of veterinary treatments."""

    VACCINATION = "vaccination"
    STERILIZATION = "sterilization"
    SURGERY = "surgery"
    DENTAL = "dental"
    DEWORMING = "deworming"
    EMERGENCY = "emergency"
    CHECKUP = "checkup"
    TREATMENT = "treatment"


class SpeciesType(StrEnum):
    """Animal species for analytics breakdown."""

    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TreatmentCount(BaseModel):
    """Count by treatment category."""

    category: TreatmentCategory
    category_label: str
    count: int
    percentage: float


class SpeciesBreakdown(BaseModel):
    """Breakdown by species."""

    species: SpeciesType
    count: int
    percentage: float


class VetSummary(BaseModel):
    """Overall veterinary care summary."""

    total_treatments: int
    total_vaccinations: int
    total_sterilizations: int
    total_animals_treated: int
    avg_treatments_per_animal: float
    period_days: int
    generated_at: str


class TreatmentBreakdown(BaseModel):
    """Treatment type breakdown."""

    treatments: list[TreatmentCount]
    by_species: list[SpeciesBreakdown]
    total: int
    period_days: int


class VaccinationStats(BaseModel):
    """Vaccination statistics."""

    total_administered: int
    fully_vaccinated_animals: int
    vaccination_rate: float
    overdue_count: int
    by_species: list[SpeciesBreakdown]
    most_common_vaccine: str
    period_days: int


class SterilizationStats(BaseModel):
    """Sterilization statistics."""

    total_sterilized: int
    sterilization_rate: float
    dogs_sterilized: int
    cats_sterilized: int
    pending_count: int
    monthly_average: float
    period_days: int


class CostItem(BaseModel):
    """Cost breakdown item."""

    category: str
    category_label: str
    total_cost: float
    avg_cost_per_treatment: float
    count: int
    currency: str = CURRENCY_PYG


class CostAnalysis(BaseModel):
    """Veterinary cost analysis."""

    total_cost: float
    avg_cost_per_animal: float
    by_category: list[CostItem]
    currency: str = CURRENCY_PYG
    period_days: int


class MonthlyTrend(BaseModel):
    """Monthly trend data point."""

    month: str
    month_label: str
    treatments: int
    vaccinations: int
    sterilizations: int
    cost: float


class VetTrends(BaseModel):
    """Veterinary care trends over time."""

    monthly: list[MonthlyTrend]
    period_months: int


# ---------------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------------

TREATMENT_LABELS_ES: dict[str, str] = {
    "vaccination": "Vacunación",
    "sterilization": "Esterilización",
    "surgery": "Cirugía",
    "dental": "Dental",
    "deworming": "Desparasitación",
    "emergency": "Emergencia",
    "checkup": "Control",
    "treatment": "Tratamiento",
}

SAMPLE_TREATMENTS = [
    TreatmentCount(
        category=TreatmentCategory.VACCINATION,
        category_label="Vacunación",
        count=145,
        percentage=32.2,
    ),
    TreatmentCount(
        category=TreatmentCategory.STERILIZATION,
        category_label="Esterilización",
        count=87,
        percentage=19.3,
    ),
    TreatmentCount(
        category=TreatmentCategory.DEWORMING,
        category_label="Desparasitación",
        count=98,
        percentage=21.8,
    ),
    TreatmentCount(
        category=TreatmentCategory.CHECKUP,
        category_label="Control",
        count=65,
        percentage=14.4,
    ),
    TreatmentCount(
        category=TreatmentCategory.SURGERY,
        category_label="Cirugía",
        count=23,
        percentage=5.1,
    ),
    TreatmentCount(
        category=TreatmentCategory.EMERGENCY,
        category_label="Emergencia",
        count=15,
        percentage=3.3,
    ),
    TreatmentCount(
        category=TreatmentCategory.DENTAL,
        category_label="Dental",
        count=10,
        percentage=2.2,
    ),
    TreatmentCount(
        category=TreatmentCategory.TREATMENT,
        category_label="Tratamiento",
        count=7,
        percentage=1.6,
    ),
]

SAMPLE_SPECIES = [
    SpeciesBreakdown(species=SpeciesType.DOG, count=280, percentage=62.2),
    SpeciesBreakdown(species=SpeciesType.CAT, count=150, percentage=33.3),
    SpeciesBreakdown(species=SpeciesType.OTHER, count=20, percentage=4.4),
]

SAMPLE_MONTHLY = [
    MonthlyTrend(
        month="2025-10",
        month_label="Oct 2025",
        treatments=72,
        vaccinations=25,
        sterilizations=12,
        cost=4_500_000,
    ),
    MonthlyTrend(
        month="2025-11",
        month_label="Nov 2025",
        treatments=85,
        vaccinations=30,
        sterilizations=15,
        cost=5_200_000,
    ),
    MonthlyTrend(
        month="2025-12",
        month_label="Dic 2025",
        treatments=68,
        vaccinations=22,
        sterilizations=10,
        cost=3_800_000,
    ),
    MonthlyTrend(
        month="2026-01",
        month_label="Ene 2026",
        treatments=90,
        vaccinations=35,
        sterilizations=18,
        cost=5_800_000,
    ),
    MonthlyTrend(
        month="2026-02",
        month_label="Feb 2026",
        treatments=78,
        vaccinations=28,
        sterilizations=14,
        cost=4_900_000,
    ),
    MonthlyTrend(
        month="2026-03",
        month_label="Mar 2026",
        treatments=57,
        vaccinations=20,
        sterilizations=18,
        cost=4_100_000,
    ),
]

SAMPLE_COSTS = [
    CostItem(
        category="sterilization",
        category_label="Esterilización",
        total_cost=8_700_000,
        avg_cost_per_treatment=100_000,
        count=87,
    ),
    CostItem(
        category="surgery",
        category_label="Cirugía",
        total_cost=6_900_000,
        avg_cost_per_treatment=300_000,
        count=23,
    ),
    CostItem(
        category="vaccination",
        category_label="Vacunación",
        total_cost=4_350_000,
        avg_cost_per_treatment=30_000,
        count=145,
    ),
    CostItem(
        category="emergency",
        category_label="Emergencia",
        total_cost=3_750_000,
        avg_cost_per_treatment=250_000,
        count=15,
    ),
    CostItem(
        category="checkup",
        category_label="Control",
        total_cost=1_950_000,
        avg_cost_per_treatment=30_000,
        count=65,
    ),
    CostItem(
        category="deworming",
        category_label="Desparasitación",
        total_cost=1_960_000,
        avg_cost_per_treatment=20_000,
        count=98,
    ),
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=VetSummary)
async def get_vet_summary(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> VetSummary:
    """Get overall veterinary care summary."""
    return VetSummary(
        total_treatments=450,
        total_vaccinations=145,
        total_sterilizations=87,
        total_animals_treated=320,
        avg_treatments_per_animal=1.4,
        period_days=period_days,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.get("/treatments", response_model=TreatmentBreakdown)
async def get_treatment_breakdown(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> TreatmentBreakdown:
    """Get treatment type breakdown."""
    return TreatmentBreakdown(
        treatments=SAMPLE_TREATMENTS,
        by_species=SAMPLE_SPECIES,
        total=450,
        period_days=period_days,
    )


@router.get("/vaccinations", response_model=VaccinationStats)
async def get_vaccination_stats(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> VaccinationStats:
    """Get vaccination statistics."""
    return VaccinationStats(
        total_administered=145,
        fully_vaccinated_animals=112,
        vaccination_rate=77.2,
        overdue_count=28,
        by_species=SAMPLE_SPECIES,
        most_common_vaccine="Séxtuple canina",
        period_days=period_days,
    )


@router.get("/sterilizations", response_model=SterilizationStats)
async def get_sterilization_stats(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> SterilizationStats:
    """Get sterilization statistics."""
    return SterilizationStats(
        total_sterilized=87,
        sterilization_rate=72.5,
        dogs_sterilized=54,
        cats_sterilized=33,
        pending_count=33,
        monthly_average=14.5,
        period_days=period_days,
    )


@router.get("/costs", response_model=CostAnalysis)
async def get_cost_analysis(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=1, le=MAX_PERIOD_DAYS),
) -> CostAnalysis:
    """Get veterinary cost analysis."""
    total = sum(c.total_cost for c in SAMPLE_COSTS)
    return CostAnalysis(
        total_cost=total,
        avg_cost_per_animal=round(total / 320, COST_PRECISION),
        by_category=SAMPLE_COSTS,
        period_days=period_days,
    )


@router.get("/trends", response_model=VetTrends)
async def get_vet_trends(
    months: int = Query(6, ge=1, le=24),
) -> VetTrends:
    """Get monthly veterinary care trends."""
    return VetTrends(
        monthly=SAMPLE_MONTHLY[-months:],
        period_months=months,
    )
