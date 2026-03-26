"""Pydantic schemas for fund allocation tracking."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.fund_allocation import FundCategory


class FundAllocationCreate(BaseModel):
    """Fields for recording a new fund allocation (expense)."""

    category: FundCategory
    amount_cents: int = Field(..., gt=0, description="Amount in smallest currency unit")
    currency: str = Field(default="PYG", pattern=r"^(EUR|PYG|USD)$")
    description: str = Field(..., min_length=1, max_length=500)
    transaction_date: datetime
    receipt_reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class FundAllocationUpdate(BaseModel):
    """Fields for updating an existing fund allocation."""

    category: FundCategory | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, pattern=r"^(EUR|PYG|USD)$")
    description: str | None = Field(default=None, min_length=1, max_length=500)
    transaction_date: datetime | None = None
    receipt_reference: str | None = None
    notes: str | None = None


class FundAllocationResponse(BaseModel):
    """Shape returned for a fund allocation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    amount_cents: int
    currency: str
    description: str
    transaction_date: datetime
    recorded_by_user_id: UUID | None
    receipt_reference: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CategoryBreakdown(BaseModel):
    """Fund allocation breakdown for a single category."""

    category: str
    total_cents: int
    transaction_count: int
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of total allocations",
    )


class FundAllocationSummary(BaseModel):
    """Aggregated fund allocation summary for a date range."""

    start_date: datetime
    end_date: datetime
    currency: str
    total_allocated_cents: int
    breakdown: list[CategoryBreakdown]


class CategoryTrend(BaseModel):
    """Fund allocation trend for a category across two periods."""

    category: str
    current_period_cents: int
    previous_period_cents: int
    change_cents: int
    change_percentage: float | None = Field(
        default=None,
        description="Percentage change; None if previous period was zero",
    )


class FundAllocationTrends(BaseModel):
    """Trend comparison between two periods."""

    current_start: datetime
    current_end: datetime
    previous_start: datetime
    previous_end: datetime
    currency: str
    trends: list[CategoryTrend]
