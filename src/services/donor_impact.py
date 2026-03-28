"""Donor impact summary service.

Calculates personalized impact metrics for donors based on their
donation history and the shelter's expense allocations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PYG_TO_USD_RATE: float = 0.000137
CACHE_TTL_SECONDS: int = 86_400  # 1 day

# Cost estimates for impact calculations (PYG)
AVERAGE_RESCUE_COST_PYG: int = 350_000
AVERAGE_CASTRATION_COST_PYG: int = 200_000
AVERAGE_MEDICAL_TREATMENT_COST_PYG: int = 150_000
AVERAGE_DAILY_FOOD_COST_PYG: int = 15_000

# Default allocation percentages (when no real data available)
DEFAULT_ALLOCATION: dict[str, float] = {
    "medical": 0.30,
    "food": 0.25,
    "shelter": 0.15,
    "rescue": 0.10,
    "operations": 0.08,
    "transport": 0.07,
    "administration": 0.05,
}

CATEGORY_LABELS_ES: dict[str, str] = {
    "medical": "Medico",
    "food": "Comida",
    "shelter": "Refugio",
    "rescue": "Rescate",
    "operations": "Operaciones",
    "transport": "Transporte",
    "administration": "Administracion",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ImpactMetrics:
    """Calculated impact metrics from donations."""

    animals_rescued: int = 0
    emergency_cases_funded: int = 0
    castrations_funded: int = 0
    animals_treated: int = 0
    animals_fed_estimate_days: int = 0


@dataclass
class CampaignContribution:
    """Donor's contribution to a specific campaign."""

    campaign_id: str = ""
    campaign_name: str = ""
    amount_pyg: int = 0
    amount_usd: float = 0.0


@dataclass
class DonorComparison:
    """Donor ranking and goal comparison."""

    rank_this_year: int = 0
    total_donors_this_year: int = 0
    castration_goal_percentage: float = 0.0
    comparison_text: str = ""


@dataclass
class DonorImpactSummary:
    """Complete personalized impact summary for a donor."""

    donor_id: str = ""
    donor_name: str = ""
    total_donated_pyg: int = 0
    total_donated_usd: float = 0.0
    donated_last_12_months_pyg: int = 0
    donated_last_12_months_usd: float = 0.0
    currency: str = "PYG"
    allocation: dict[str, float] = field(default_factory=dict)
    allocation_labels: dict[str, str] = field(default_factory=dict)
    impact: ImpactMetrics = field(default_factory=ImpactMetrics)
    impact_statements: list[str] = field(default_factory=list)
    top_campaigns: list[CampaignContribution] = field(default_factory=list)
    comparison: DonorComparison = field(default_factory=DonorComparison)
    cache_ttl_seconds: int = CACHE_TTL_SECONDS


# ---------------------------------------------------------------------------
# Impact calculations
# ---------------------------------------------------------------------------


def calculate_impact_metrics(
    total_donated_pyg: int,
    allocation: dict[str, float] | None = None,
) -> ImpactMetrics:
    """Calculate impact metrics from total donations and allocation."""
    alloc = allocation if allocation is not None else DEFAULT_ALLOCATION

    rescue_amount = int(total_donated_pyg * alloc.get("rescue", 0))
    medical_amount = int(total_donated_pyg * alloc.get("medical", 0))
    food_amount = int(total_donated_pyg * alloc.get("food", 0))

    animals_rescued = rescue_amount // AVERAGE_RESCUE_COST_PYG if AVERAGE_RESCUE_COST_PYG > 0 else 0
    castrations_funded = (
        medical_amount // (AVERAGE_CASTRATION_COST_PYG * 2)
        if AVERAGE_CASTRATION_COST_PYG > 0
        else 0
    )
    animals_treated = (
        medical_amount // AVERAGE_MEDICAL_TREATMENT_COST_PYG
        if AVERAGE_MEDICAL_TREATMENT_COST_PYG > 0
        else 0
    )
    animals_fed_days = (
        food_amount // AVERAGE_DAILY_FOOD_COST_PYG if AVERAGE_DAILY_FOOD_COST_PYG > 0 else 0
    )

    return ImpactMetrics(
        animals_rescued=animals_rescued,
        emergency_cases_funded=max(1, animals_rescued // 3),
        castrations_funded=castrations_funded,
        animals_treated=animals_treated,
        animals_fed_estimate_days=animals_fed_days,
    )


def generate_impact_statements(
    donor_name: str,
    impact: ImpactMetrics,
) -> list[str]:
    """Generate personalized impact statements in Spanish."""
    statements: list[str] = []

    if impact.animals_rescued > 0:
        statements.append(
            f"Gracias a tus donaciones, {donor_name}, ayudaste a rescatar "
            f"{impact.animals_rescued} animales"
        )

    if impact.emergency_cases_funded > 0:
        statements.append(
            f"Tus donaciones financiaron {impact.emergency_cases_funded} " f"rescates de emergencia"
        )

    if impact.castrations_funded > 0:
        statements.append(f"Tus donaciones ayudaron a castrar {impact.castrations_funded} animales")

    if impact.animals_treated > 0:
        statements.append(
            f"Tus donaciones proporcionaron atencion medica a " f"{impact.animals_treated} animales"
        )

    if impact.animals_fed_estimate_days > 0:
        statements.append(
            f"Tus donaciones proporcionaron alimento por "
            f"{impact.animals_fed_estimate_days} dias"
        )

    if not statements:
        statements.append(f"Gracias por tu apoyo, {donor_name}. Cada donacion cuenta.")

    return statements


def calculate_donor_comparison(
    donor_total_pyg: int,
    all_donor_totals: list[int] | None = None,
    castration_goal_pyg: int = 10_000_000,
) -> DonorComparison:
    """Calculate donor ranking and goal comparison."""
    totals = all_donor_totals if all_donor_totals is not None else []
    sorted_totals = sorted(totals, reverse=True)
    rank = 1
    for total in sorted_totals:
        if donor_total_pyg >= total:
            break
        rank += 1

    castration_pct = min(
        100.0,
        round(donor_total_pyg / castration_goal_pyg * 100, 1) if castration_goal_pyg > 0 else 0,
    )

    comparison_text = (
        f"Eres el donante #{rank} este ano"
        if sorted_totals
        else "Gracias por ser parte de nuestra comunidad de donantes"
    )

    return DonorComparison(
        rank_this_year=rank,
        total_donors_this_year=len(sorted_totals),
        castration_goal_percentage=castration_pct,
        comparison_text=comparison_text,
    )


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------


def generate_donor_impact_summary(
    donor_id: str,
    donor_name: str = "Donante",
    total_donated_pyg: int = 0,
    donated_last_12_months_pyg: int = 0,
    allocation: dict[str, float] | None = None,
    top_campaigns: list[CampaignContribution] | None = None,
    all_donor_totals: list[int] | None = None,
) -> DonorImpactSummary:
    """Generate a complete personalized impact summary."""
    effective_allocation = allocation if allocation is not None else DEFAULT_ALLOCATION

    impact = calculate_impact_metrics(total_donated_pyg, effective_allocation)
    statements = generate_impact_statements(donor_name, impact)
    comparison = calculate_donor_comparison(total_donated_pyg, all_donor_totals)

    allocation_labels = {cat: CATEGORY_LABELS_ES.get(cat, cat) for cat in effective_allocation}

    return DonorImpactSummary(
        donor_id=donor_id,
        donor_name=donor_name,
        total_donated_pyg=total_donated_pyg,
        total_donated_usd=round(total_donated_pyg * PYG_TO_USD_RATE, 2),
        donated_last_12_months_pyg=donated_last_12_months_pyg,
        donated_last_12_months_usd=round(donated_last_12_months_pyg * PYG_TO_USD_RATE, 2),
        allocation=effective_allocation,
        allocation_labels=allocation_labels,
        impact=impact,
        impact_statements=statements,
        top_campaigns=top_campaigns or [],
        comparison=comparison,
    )


def impact_summary_to_dict(summary: DonorImpactSummary) -> dict[str, Any]:
    """Convert impact summary to API-friendly dict."""
    return {
        "donor_id": summary.donor_id,
        "donor_name": summary.donor_name,
        "total_donated_pyg": summary.total_donated_pyg,
        "total_donated_usd": summary.total_donated_usd,
        "donated_last_12_months_pyg": summary.donated_last_12_months_pyg,
        "donated_last_12_months_usd": summary.donated_last_12_months_usd,
        "currency": summary.currency,
        "allocation": summary.allocation,
        "allocation_labels": summary.allocation_labels,
        "impact": {
            "animals_rescued": summary.impact.animals_rescued,
            "emergency_cases_funded": summary.impact.emergency_cases_funded,
            "castrations_funded": summary.impact.castrations_funded,
            "animals_treated": summary.impact.animals_treated,
            "animals_fed_estimate_days": summary.impact.animals_fed_estimate_days,
        },
        "impact_statements": summary.impact_statements,
        "top_campaigns": [
            {
                "campaign_id": c.campaign_id,
                "campaign_name": c.campaign_name,
                "amount_pyg": c.amount_pyg,
                "amount_usd": c.amount_usd,
            }
            for c in summary.top_campaigns
        ],
        "comparison": {
            "rank_this_year": summary.comparison.rank_this_year,
            "total_donors_this_year": summary.comparison.total_donors_this_year,
            "castration_goal_percentage": summary.comparison.castration_goal_percentage,
            "comparison_text": summary.comparison.comparison_text,
        },
        "cache_ttl_seconds": summary.cache_ttl_seconds,
    }
