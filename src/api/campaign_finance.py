"""Campaign financial reports and expense allocation API.

Endpoints for viewing campaign-specific financial reports and
allocating expenses to campaigns.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.services.campaign_finance import (
    AllocationRequest,
    AllocationStatus,
    ExpenseAllocation,
    allocate_expense_to_campaigns,
    format_allocation_summary,
    generate_campaign_financial_summary,
)

router = APIRouter(prefix="/api/admin/campaigns", tags=["campaign-finance"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AllocationInput(BaseModel):
    """Single allocation entry."""

    campaign_id: str = Field(min_length=1)
    percentage: float = Field(gt=0, le=100)


class AllocateExpenseRequest(BaseModel):
    """Request to allocate an expense to campaigns."""

    expense_id: str = Field(min_length=1)
    expense_amount_pyg: int = Field(gt=0)
    allocations: list[AllocationInput] = Field(min_length=1)


class AllocationResponse(BaseModel):
    """Allocation operation result."""

    success: bool
    message: str
    total_allocated_percentage: float
    allocation_count: int


class CampaignFinancialReport(BaseModel):
    """Financial report for a single campaign."""

    campaign_id: str
    campaign_name: str
    total_raised_pyg: int
    total_raised_usd: float
    total_spent_pyg: int
    total_spent_usd: float
    remaining_balance_pyg: int
    remaining_balance_usd: float
    expense_count: int
    allocation_count: int
    category_breakdown: list[dict[str, Any]]
    allocation_summary: str


class AllocationHistoryEntry(BaseModel):
    """Single allocation history entry."""

    id: str
    expense_id: str
    campaign_id: str
    percentage: float
    amount_pyg: int
    allocated_by: str
    allocated_at: str
    status: str


# ---------------------------------------------------------------------------
# In-memory store (MVP)
# ---------------------------------------------------------------------------

_allocations: list[ExpenseAllocation] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{campaign_id}/expenses/allocate",
    response_model=AllocationResponse,
    status_code=201,
    summary="Allocate expense to campaign(s)",
)
async def allocate_expense(
    campaign_id: str = Path(description="Campaign ID"),
    body: AllocateExpenseRequest = ...,
) -> AllocationResponse:
    """Allocate an expense to one or more campaigns."""
    request = AllocationRequest(
        expense_id=body.expense_id,
        expense_amount_pyg=body.expense_amount_pyg,
        allocations=[
            {"campaign_id": a.campaign_id, "percentage": a.percentage} for a in body.allocations
        ],
    )

    result = allocate_expense_to_campaigns(request, allocated_by="admin")

    if not result.success:
        raise HTTPException(status_code=422, detail=result.message)

    _allocations.extend(result.allocations)

    return AllocationResponse(
        success=True,
        message=result.message,
        total_allocated_percentage=result.total_allocated_percentage,
        allocation_count=len(result.allocations),
    )


@router.get(
    "/{campaign_id}/financial-report",
    response_model=CampaignFinancialReport,
    summary="Get campaign financial report",
)
async def get_campaign_financial_report(
    campaign_id: str = Path(description="Campaign ID"),
    campaign_name: str = Query("Campana", description="Campaign name"),
    total_raised_pyg: int = Query(0, ge=0, description="Total raised in PYG"),
) -> CampaignFinancialReport:
    """Return financial summary for a specific campaign."""
    summary = generate_campaign_financial_summary(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        total_raised_pyg=total_raised_pyg,
        allocations=_allocations,
    )

    return CampaignFinancialReport(
        campaign_id=summary.campaign_id,
        campaign_name=summary.campaign_name,
        total_raised_pyg=summary.total_raised_pyg,
        total_raised_usd=summary.total_raised_usd,
        total_spent_pyg=summary.total_spent_pyg,
        total_spent_usd=summary.total_spent_usd,
        remaining_balance_pyg=summary.remaining_balance_pyg,
        remaining_balance_usd=summary.remaining_balance_usd,
        expense_count=summary.expense_count,
        allocation_count=summary.allocation_count,
        category_breakdown=summary.category_breakdown,
        allocation_summary=format_allocation_summary(summary.allocations),
    )


@router.get(
    "/{campaign_id}/allocations",
    response_model=list[AllocationHistoryEntry],
    summary="Get allocation history for campaign",
)
async def get_campaign_allocations(
    campaign_id: str = Path(description="Campaign ID"),
    status: str | None = Query(None, description="Filter by status"),
) -> list[AllocationHistoryEntry]:
    """Return allocation history for a campaign."""
    filtered = [a for a in _allocations if a.campaign_id == campaign_id]

    if status:
        filtered = [a for a in filtered if a.status == status]

    return [
        AllocationHistoryEntry(
            id=a.id,
            expense_id=a.expense_id,
            campaign_id=a.campaign_id,
            percentage=a.percentage,
            amount_pyg=a.amount_pyg,
            allocated_by=a.allocated_by,
            allocated_at=a.allocated_at,
            status=a.status,
        )
        for a in filtered
    ]


@router.delete(
    "/{campaign_id}/allocations/{allocation_id}",
    summary="Revoke an expense allocation",
)
async def revoke_allocation(
    campaign_id: str = Path(description="Campaign ID"),
    allocation_id: str = Path(description="Allocation ID"),
) -> dict[str, str]:
    """Revoke (soft delete) an expense allocation."""
    for alloc in _allocations:
        if alloc.id == allocation_id and alloc.campaign_id == campaign_id:
            alloc.status = AllocationStatus.REVOKED
            return {"message": "Asignacion revocada", "id": allocation_id}

    raise HTTPException(status_code=404, detail="Asignacion no encontrada")
