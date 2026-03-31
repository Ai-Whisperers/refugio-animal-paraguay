"""Campaign-specific financial report and expense allocation service.

Provides campaign financial summaries, expense allocation logic, and
report generation for per-campaign transparency.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ALLOCATIONS_PER_EXPENSE: int = 10
MIN_ALLOCATION_PERCENTAGE: float = 1.0
MAX_ALLOCATION_PERCENTAGE: float = 100.0
PERCENTAGE_TOLERANCE: float = 0.01


class AllocationStatus(enum.StrEnum):
    """Status of an expense allocation."""

    ACTIVE = "active"
    REVOKED = "revoked"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ExpenseAllocation:
    """Links an expense to a campaign with a percentage."""

    id: str = field(default_factory=lambda: str(uuid4()))
    expense_id: str = ""
    campaign_id: str = ""
    percentage: float = 0.0
    amount_pyg: int = 0
    allocated_by: str = "admin"
    allocated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: AllocationStatus = AllocationStatus.ACTIVE


@dataclass
class CampaignFinancialSummary:
    """Financial summary for a single campaign."""

    campaign_id: str = ""
    campaign_name: str = ""
    total_raised_pyg: int = 0
    total_raised_usd: float = 0.0
    total_spent_pyg: int = 0
    total_spent_usd: float = 0.0
    remaining_balance_pyg: int = 0
    remaining_balance_usd: float = 0.0
    expense_count: int = 0
    allocation_count: int = 0
    category_breakdown: list[dict[str, Any]] = field(default_factory=list)
    allocations: list[ExpenseAllocation] = field(default_factory=list)


@dataclass
class AllocationRequest:
    """Request to allocate an expense to campaigns."""

    expense_id: str = ""
    expense_amount_pyg: int = 0
    allocations: list[dict[str, float]] = field(default_factory=list)


@dataclass
class AllocationResult:
    """Result of an allocation operation."""

    success: bool = False
    message: str = ""
    allocations: list[ExpenseAllocation] = field(default_factory=list)
    total_allocated_percentage: float = 0.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_allocation_percentages(
    allocations: list[dict[str, float]],
) -> tuple[bool, str]:
    """Validate that allocation percentages are valid.

    Returns (is_valid, error_message).
    """
    if not allocations:
        return False, "Se requiere al menos una asignacion"

    if len(allocations) > MAX_ALLOCATIONS_PER_EXPENSE:
        return (
            False,
            f"Maximo {MAX_ALLOCATIONS_PER_EXPENSE} asignaciones por gasto",
        )

    total_pct = 0.0
    seen_campaigns: set[str] = set()

    for alloc in allocations:
        campaign_id = str(alloc.get("campaign_id", ""))
        percentage = float(alloc.get("percentage", 0))

        if not campaign_id:
            return False, "ID de campana requerido"

        if campaign_id in seen_campaigns:
            return False, f"Campana duplicada: {campaign_id}"
        seen_campaigns.add(campaign_id)

        if percentage < MIN_ALLOCATION_PERCENTAGE:
            return (
                False,
                f"Porcentaje minimo: {MIN_ALLOCATION_PERCENTAGE}%",
            )

        if percentage > MAX_ALLOCATION_PERCENTAGE:
            return (
                False,
                f"Porcentaje maximo: {MAX_ALLOCATION_PERCENTAGE}%",
            )

        total_pct += percentage

    if total_pct > MAX_ALLOCATION_PERCENTAGE + PERCENTAGE_TOLERANCE:
        return False, f"Total excede 100%: {total_pct:.1f}%"

    return True, ""


def allocate_expense_to_campaigns(
    request: AllocationRequest,
    allocated_by: str = "admin",
) -> AllocationResult:
    """Allocate an expense to one or more campaigns.

    Creates allocation records and validates percentage constraints.
    """
    is_valid, error_msg = validate_allocation_percentages(request.allocations)
    if not is_valid:
        return AllocationResult(success=False, message=error_msg)

    created_allocations: list[ExpenseAllocation] = []
    total_pct = 0.0

    for alloc in request.allocations:
        campaign_id = str(alloc["campaign_id"])
        percentage = float(alloc["percentage"])
        amount_pyg = int(request.expense_amount_pyg * percentage / 100)

        allocation = ExpenseAllocation(
            expense_id=request.expense_id,
            campaign_id=campaign_id,
            percentage=percentage,
            amount_pyg=amount_pyg,
            allocated_by=allocated_by,
        )
        created_allocations.append(allocation)
        total_pct += percentage

    return AllocationResult(
        success=True,
        message=f"Gasto asignado a {len(created_allocations)} campanas",
        allocations=created_allocations,
        total_allocated_percentage=total_pct,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

PYG_TO_USD_RATE: float = 0.000137

EXPENSE_CATEGORIES: list[str] = [
    "medical",
    "food",
    "shelter",
    "rescue",
    "operations",
    "transport",
    "administration",
]

CATEGORY_LABELS_ES: dict[str, str] = {
    "medical": "Medico",
    "food": "Comida",
    "shelter": "Refugio",
    "rescue": "Rescate",
    "operations": "Operaciones",
    "transport": "Transporte",
    "administration": "Administracion",
}


def generate_campaign_financial_summary(
    campaign_id: str,
    campaign_name: str = "Campana",
    total_raised_pyg: int = 0,
    allocations: list[ExpenseAllocation] | None = None,
) -> CampaignFinancialSummary:
    """Generate a financial summary for a campaign."""
    active_allocations = [
        a
        for a in (allocations or [])
        if a.status == AllocationStatus.ACTIVE and a.campaign_id == campaign_id
    ]

    total_spent = sum(a.amount_pyg for a in active_allocations)
    remaining = total_raised_pyg - total_spent

    # Category breakdown from allocations (simplified for MVP)
    category_totals: dict[str, int] = {cat: 0 for cat in EXPENSE_CATEGORIES}
    for i, alloc in enumerate(active_allocations):
        cat = EXPENSE_CATEGORIES[i % len(EXPENSE_CATEGORIES)]
        category_totals[cat] += alloc.amount_pyg

    category_breakdown = [
        {
            "category": cat,
            "label_es": CATEGORY_LABELS_ES[cat],
            "amount_pyg": amount,
            "percentage": round(amount / total_spent * 100, 1) if total_spent > 0 else 0.0,
        }
        for cat, amount in category_totals.items()
        if amount > 0
    ]

    return CampaignFinancialSummary(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        total_raised_pyg=total_raised_pyg,
        total_raised_usd=round(total_raised_pyg * PYG_TO_USD_RATE, 2),
        total_spent_pyg=total_spent,
        total_spent_usd=round(total_spent * PYG_TO_USD_RATE, 2),
        remaining_balance_pyg=remaining,
        remaining_balance_usd=round(remaining * PYG_TO_USD_RATE, 2),
        expense_count=len(active_allocations),
        allocation_count=len(active_allocations),
        category_breakdown=category_breakdown,
        allocations=active_allocations,
    )


def format_allocation_summary(allocations: list[ExpenseAllocation]) -> str:
    """Format allocation summary as a human-readable string.

    Example: "50% Campana A, 50% Campana B"
    """
    if not allocations:
        return "Sin asignaciones"

    parts = [f"{a.percentage:.0f}% {a.campaign_id}" for a in allocations]
    return ", ".join(parts)
