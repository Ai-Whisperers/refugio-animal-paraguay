"""API endpoints for annual financial report generation.

Provides admin endpoints for generating, exporting (CSV), and
previewing annual financial reports.
"""

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.services.annual_report import (
    export_campaigns_csv,
    export_expenses_csv,
    export_monthly_csv,
    export_summary_csv,
    generate_annual_report,
)

router = APIRouter(
    prefix="/api/admin/reports",
    tags=["annual-reports"],
)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ReportSummary(BaseModel):
    """Summary response for a generated annual report."""

    year: int
    generated_at: str
    generated_by: str
    total_income_cents: int
    total_expenses_cents: int
    net_result_cents: int
    currency: str = "PYG"


class ReportGenerateRequest(BaseModel):
    """Request to generate an annual report."""

    year: int = Field(..., ge=2020, le=2030)
    admin_name: str = Field(default="Administrador", max_length=200)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/annual",
    response_model=ReportSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Generate annual financial report",
)
async def generate_report(body: ReportGenerateRequest) -> ReportSummary:
    """Generate a comprehensive annual financial report.

    Returns an executive summary. Use the CSV export endpoints
    for detailed data.
    """
    report = generate_annual_report(body.year, body.admin_name)
    return ReportSummary(
        year=report.year,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        total_income_cents=report.total_income_cents,
        total_expenses_cents=report.total_expenses_cents,
        net_result_cents=report.net_result_cents,
        currency=report.currency,
    )


@router.get(
    "/annual/{year}/csv/summary",
    response_class=PlainTextResponse,
    summary="Export annual report summary as CSV",
)
async def export_summary(year: int) -> PlainTextResponse:
    """Export executive summary and donor metrics as CSV."""
    report = generate_annual_report(year)
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
async def export_expenses(year: int) -> PlainTextResponse:
    """Export expense categories and amounts as CSV."""
    report = generate_annual_report(year)
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
async def export_monthly(year: int) -> PlainTextResponse:
    """Export month-by-month income and expenses as CSV."""
    report = generate_annual_report(year)
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
async def export_campaigns(year: int) -> PlainTextResponse:
    """Export top campaigns data as CSV."""
    report = generate_annual_report(year)
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
async def available_years() -> dict[str, list[int]]:
    """Return list of years for which reports can be generated.

    In production, this queries the DB for years with data.
    """
    from datetime import datetime

    current_year = datetime.now().year
    return {"years": list(range(current_year, current_year - 5, -1))}
