"""API endpoints for annual financial report generation.

Provides admin endpoints for generating, exporting (CSV), and
previewing annual financial reports.  The ``POST /annual`` endpoint
now queries the database for real metrics.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.services.annual_report import (
    export_campaigns_csv,
    export_expenses_csv,
    export_monthly_csv,
    export_summary_csv,
    generate_annual_report_from_db,
)

router = APIRouter(
    prefix="/api/admin/reports",
    tags=["annual-reports"],
    responses=AUTHENTICATED_RESPONSES,
)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MonthlyBreakdownResponse(BaseModel):
    """Monthly income/expense for chart rendering."""

    month: int
    month_name: str
    income_cents: int
    expenses_cents: int
    net_cents: int


class CategoryBreakdownResponse(BaseModel):
    """Expense category entry."""

    category: str
    amount_cents: int
    percentage: float


class DonorMetricsResponse(BaseModel):
    """Donor-level metrics for the year."""

    total_donors: int
    new_donors: int
    recurring_donors: int
    average_donation_cents: int


class AnimalOutcomesResponse(BaseModel):
    """Animal outcome counts for the year."""

    rescued: int
    adopted: int
    castrated: int
    treated: int


class EfficiencyResponse(BaseModel):
    """Financial efficiency metrics."""

    direct_care_percentage: float
    admin_percentage: float
    direct_care_cents: int
    admin_cents: int


class AnnualReportResponse(BaseModel):
    """Full annual report response including chart-ready data."""

    year: int
    generated_at: str
    generated_by: str
    total_income_cents: int
    total_expenses_cents: int
    net_result_cents: int
    currency: str
    income_by_source: dict[str, int]
    expense_categories: list[CategoryBreakdownResponse]
    monthly_breakdown: list[MonthlyBreakdownResponse]
    donor_metrics: DonorMetricsResponse
    animal_outcomes: AnimalOutcomesResponse
    efficiency: EfficiencyResponse


class ReportGenerateRequest(BaseModel):
    """Request to generate an annual report."""

    year: int = Field(..., ge=2020, le=2030)
    admin_name: str = Field(default="Administrador", max_length=200)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/annual",
    response_model=AnnualReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate annual financial report",
)
async def generate_report(
    body: ReportGenerateRequest,
    _: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> AnnualReportResponse:
    """Generate a comprehensive annual financial report from DB data.

    Returns all sections needed for dashboard visualizations including
    monthly income/expense breakdown, donor metrics, and animal outcomes.
    """
    report = await generate_annual_report_from_db(db, body.year, body.admin_name)

    return AnnualReportResponse(
        year=report.year,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        total_income_cents=report.total_income_cents,
        total_expenses_cents=report.total_expenses_cents,
        net_result_cents=report.net_result_cents,
        currency=report.currency,
        income_by_source=report.income_by_source,
        expense_categories=[
            CategoryBreakdownResponse(
                category=c.category,
                amount_cents=c.amount_cents,
                percentage=c.percentage,
            )
            for c in report.expense_categories
        ],
        monthly_breakdown=[
            MonthlyBreakdownResponse(
                month=m.month,
                month_name=m.month_name,
                income_cents=m.income_cents,
                expenses_cents=m.expenses_cents,
                net_cents=m.net_cents,
            )
            for m in report.monthly_breakdown
        ],
        donor_metrics=DonorMetricsResponse(
            total_donors=report.donor_metrics.total_donors,
            new_donors=report.donor_metrics.new_donors,
            recurring_donors=report.donor_metrics.recurring_donors,
            average_donation_cents=report.donor_metrics.average_donation_cents,
        ),
        animal_outcomes=AnimalOutcomesResponse(
            rescued=report.animal_outcomes.rescued,
            adopted=report.animal_outcomes.adopted,
            castrated=report.animal_outcomes.castrated,
            treated=report.animal_outcomes.treated,
        ),
        efficiency=EfficiencyResponse(
            direct_care_percentage=report.efficiency.direct_care_percentage,
            admin_percentage=report.efficiency.admin_percentage,
            direct_care_cents=report.efficiency.direct_care_cents,
            admin_cents=report.efficiency.admin_cents,
        ),
    )


@router.get(
    "/annual/{year}/csv/summary",
    response_class=PlainTextResponse,
    summary="Export annual report summary as CSV",
)
async def export_summary(
    year: int,
    _: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export executive summary and donor metrics as CSV."""
    report = await generate_annual_report_from_db(db, year)
    csv_content = export_summary_csv(report)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="reporte-anual-{year}-resumen.csv"'},
    )


@router.get(
    "/annual/{year}/csv/expenses",
    response_class=PlainTextResponse,
    summary="Export annual expense breakdown as CSV",
)
async def export_expenses(
    year: int,
    _: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export expense categories and amounts as CSV."""
    report = await generate_annual_report_from_db(db, year)
    csv_content = export_expenses_csv(report)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="reporte-anual-{year}-gastos.csv"'},
    )


@router.get(
    "/annual/{year}/csv/monthly",
    response_class=PlainTextResponse,
    summary="Export monthly breakdown as CSV",
)
async def export_monthly(
    year: int,
    _: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export month-by-month income and expenses as CSV."""
    report = await generate_annual_report_from_db(db, year)
    csv_content = export_monthly_csv(report)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="reporte-anual-{year}-mensual.csv"'},
    )


@router.get(
    "/annual/{year}/csv/campaigns",
    response_class=PlainTextResponse,
    summary="Export campaign summary as CSV",
)
async def export_campaigns(
    year: int,
    _: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export top campaigns data as CSV."""
    report = await generate_annual_report_from_db(db, year)
    csv_content = export_campaigns_csv(report)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="reporte-anual-{year}-campanas.csv"'
        },
    )


@router.get(
    "/annual/available-years",
    summary="List available report years",
)
async def available_years(
    _: User = Depends(require_staff),
) -> dict[str, list[int]]:
    """Return list of years for which reports can be generated."""
    current_year = datetime.now(tz=UTC).year
    return {"years": list(range(current_year, current_year - 5, -1))}
