"""Admin API endpoints for Paraguayan government reporting (RAP-248).

Endpoints:
  GET  /admin/reports/government/annual-census         — JSON annual census report
  GET  /admin/reports/government/annual-census/export  — CSV export for SENACSA submission
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.services.government_report_service import (
    generate_annual_census,
    render_annual_census_csv,
)

router = APIRouter(
    prefix="/admin/reports/government",
    tags=["admin-government-reports"],
    responses=AUTHENTICATED_RESPONSES,
)

# Default reporting year: current calendar year
_CURRENT_YEAR = datetime.now(UTC).year


@router.get("/annual-census", summary="Paraguayan government annual census report (JSON)")
async def get_annual_census_report(
    year: int = Query(
        default=_CURRENT_YEAR,
        ge=2000,
        le=2100,
        description="Calendar year to report on (e.g. 2025). Defaults to current year.",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Generate an annual census report for submission to SENACSA.

    Returns counts of animal intakes, adoptions, vaccinations, and current
    shelter inventory for the requested calendar year, broken down by species
    and status. Legal basis: Ley 4840/2013 Art. 12, Ley 3140/2006 Art. 5.

    Admin-only.
    """
    report = await generate_annual_census(db, year)
    return report.to_dict()


@router.get(
    "/annual-census/export",
    summary="Paraguayan government annual census report (CSV export)",
    response_class=PlainTextResponse,
)
async def export_annual_census_csv(
    year: int = Query(
        default=_CURRENT_YEAR,
        ge=2000,
        le=2100,
        description="Calendar year to export (e.g. 2025). Defaults to current year.",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> PlainTextResponse:
    """Export the annual census report as a CSV file for SENACSA submission.

    Returns a UTF-8 with BOM encoded CSV compatible with Microsoft Excel (Paraguay standard).
    Filename suggestion: ``informe_anual_senacsa_{year}.csv``

    Admin-only.
    """
    report = await generate_annual_census(db, year)
    csv_content = render_annual_census_csv(report)
    filename = f"informe_anual_senacsa_{year}.csv"
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
