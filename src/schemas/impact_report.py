"""Pydantic schemas for impact report generation."""

from datetime import datetime

from pydantic import BaseModel, Field


class ImpactReportRequest(BaseModel):
    """Request parameters for generating an impact report."""

    start_date: datetime
    end_date: datetime


class SpeciesCount(BaseModel):
    """Count of items grouped by species."""

    total: int
    by_species: dict[str, int]


class DonationCurrencyDetail(BaseModel):
    """Donation totals for a single currency."""

    total_cents: int
    count: int


class DonationSummary(BaseModel):
    """Aggregated donation metrics."""

    total_count: int
    by_currency: dict[str, DonationCurrencyDetail]
    by_payment_method: dict[str, int]


class InKindSummary(BaseModel):
    """Aggregated in-kind donation metrics."""

    total: int
    by_type: dict[str, int]


class FundCategoryBreakdown(BaseModel):
    """Fund allocation for a single category."""

    category: str
    total_cents: int
    transaction_count: int
    percentage: float = Field(ge=0.0, le=100.0)


class FundAllocationSummary(BaseModel):
    """Aggregated fund allocation metrics."""

    total_cents: int
    breakdown: list[FundCategoryBreakdown]


class PerformanceMetrics(BaseModel):
    """Computed performance indicators."""

    avg_time_to_adoption_days: float | None = None
    cost_per_adoption_cents: int | None = None


class ReportMetadata(BaseModel):
    """Metadata about the generated report."""

    start_date: str
    end_date: str
    generated_by_user_id: str | None = None


class ImpactReportResponse(BaseModel):
    """Full impact report response."""

    report_metadata: ReportMetadata
    animals_served: SpeciesCount
    adoptions: SpeciesCount
    donations: DonationSummary
    in_kind_donations: InKindSummary
    fund_allocation: FundAllocationSummary
    performance_metrics: PerformanceMetrics
