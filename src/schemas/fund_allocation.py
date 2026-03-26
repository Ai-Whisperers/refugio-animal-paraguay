"""Pydantic schemas for fund allocation endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.fund_allocation import FundCategory


class FundAllocationCreate(BaseModel):
    """Create a new fund allocation (expense) record."""

    category: FundCategory
    amount_cents: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="PYG", max_length=3)
    description: str = Field(..., min_length=1)
    transaction_date: datetime
    receipt_reference: str | None = None
    notes: str | None = None


class FundAllocationResponse(BaseModel):
    """Full fund allocation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    amount_cents: int
    currency: str
    description: str
    transaction_date: datetime
    recorded_by_user_id: UUID | None = None
    receipt_reference: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CategoryBreakdown(BaseModel):
    """Single category in the fund allocation breakdown."""

    category: str
    total_cents: int
    percentage: float
    transaction_count: int


class FundAllocationSummary(BaseModel):
    """Aggregated fund allocation breakdown for transparency reporting."""

    start_date: datetime
    end_date: datetime
    total_expenses_cents: int
    total_donations_cents: int
    currency: str
    breakdown: list[CategoryBreakdown]
