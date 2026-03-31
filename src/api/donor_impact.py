"""Donor impact summary API.

Provides personalized impact summaries for authenticated donors.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.services.donor_impact import (
    CampaignContribution,
    generate_donor_impact_summary,
    impact_summary_to_dict,
)

router = APIRouter(prefix="/api/portal", tags=["donor-impact"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ImpactMetricsResponse(BaseModel):
    """Impact metrics in the response."""

    animals_rescued: int
    emergency_cases_funded: int
    castrations_funded: int
    animals_treated: int
    animals_fed_estimate_days: int


class ComparisonResponse(BaseModel):
    """Donor comparison data."""

    rank_this_year: int
    total_donors_this_year: int
    castration_goal_percentage: float
    comparison_text: str


class CampaignContributionResponse(BaseModel):
    """Campaign contribution in the response."""

    campaign_id: str
    campaign_name: str
    amount_pyg: int
    amount_usd: float


class DonorImpactResponse(BaseModel):
    """Full donor impact API response."""

    donor_id: str
    donor_name: str
    total_donated_pyg: int
    total_donated_usd: float
    donated_last_12_months_pyg: int
    donated_last_12_months_usd: float
    currency: str
    allocation: dict[str, float]
    allocation_labels: dict[str, str]
    impact: ImpactMetricsResponse
    impact_statements: list[str]
    top_campaigns: list[CampaignContributionResponse]
    comparison: ComparisonResponse
    cache_ttl_seconds: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/impact",
    response_model=DonorImpactResponse,
    summary="Get personalized donor impact summary",
    description="Returns a personalized impact summary for the authenticated donor. "
    "Includes donation totals, category allocation, impact metrics, and statements.",
)
async def get_donor_impact(
    donor_id: str = Query("donor-1", description="Donor ID (from auth in production)"),
    donor_name: str = Query("Donante", description="Donor name"),
    total_donated_pyg: int = Query(0, ge=0, description="Total donated in PYG"),
    donated_last_12_months_pyg: int = Query(0, ge=0, description="Donated in last 12 months"),
) -> dict[str, Any]:
    """Return personalized impact summary for a donor.

    In production, donor_id and name come from JWT auth.
    For MVP, accept as query params for testing.
    """
    top_campaigns = (
        [
            CampaignContribution(
                campaign_id="camp-esterilizacion",
                campaign_name="Campana de Esterilizacion 2026",
                amount_pyg=int(total_donated_pyg * 0.4),
                amount_usd=round(total_donated_pyg * 0.4 * 0.000137, 2),
            ),
            CampaignContribution(
                campaign_id="camp-rescate",
                campaign_name="Fondo de Rescate de Emergencia",
                amount_pyg=int(total_donated_pyg * 0.3),
                amount_usd=round(total_donated_pyg * 0.3 * 0.000137, 2),
            ),
        ]
        if total_donated_pyg > 0
        else []
    )

    summary = generate_donor_impact_summary(
        donor_id=donor_id,
        donor_name=donor_name,
        total_donated_pyg=total_donated_pyg,
        donated_last_12_months_pyg=donated_last_12_months_pyg,
        top_campaigns=top_campaigns,
    )

    return impact_summary_to_dict(summary)


@router.get(
    "/impact/statements",
    response_model=list[str],
    summary="Get impact statements only",
    description="Returns just the personalized impact statements for display.",
)
async def get_impact_statements(
    donor_name: str = Query("Donante", description="Donor name"),
    total_donated_pyg: int = Query(0, ge=0, description="Total donated in PYG"),
) -> list[str]:
    """Return impact statements for a donor."""
    summary = generate_donor_impact_summary(
        donor_id="",
        donor_name=donor_name,
        total_donated_pyg=total_donated_pyg,
    )
    return summary.impact_statements
