"""Impact reports router.

Endpoints:
  POST /impact-reports/generate      -- generate impact report JSON (staff only)
  POST /impact-reports/generate-pdf  -- generate impact report PDF (staff only)
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.impact_report import ImpactReportRequest, ImpactReportResponse
from src.services import impact_report_service
from src.services.impact_report_pdf_service import (
    ImpactReportData,
    ImpactReportPDFGenerator,
)

router = APIRouter(
    prefix="/impact-reports", tags=["impact-reports"], responses=AUTHENTICATED_RESPONSES
)

_pdf_generator = ImpactReportPDFGenerator()


@router.post("/generate", response_model=ImpactReportResponse)
async def generate_report(
    body: ImpactReportRequest,
    user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> ImpactReportResponse:
    """Generate an impact report for the given date range.

    Aggregates: animals served, adoptions (by species), donations (by
    currency and method), in-kind donations, fund allocation breakdown,
    average time-to-adoption, and cost-per-adoption.
    """
    report_data = await impact_report_service.generate_impact_report(
        db=db,
        start_date=body.start_date,
        end_date=body.end_date,
        generated_by_user_id=user.id,
    )
    return ImpactReportResponse(**report_data)


@router.post(
    "/generate-pdf",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Impact report as a downloadable PDF file.",
        },
        **AUTHENTICATED_RESPONSES,
    },
)
async def generate_report_pdf(
    body: ImpactReportRequest,
    user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate a branded impact report PDF for the given date range.

    Returns the PDF as a downloadable file with a suggested filename derived
    from the requested date range.  The report covers animals served,
    adoptions, donations, fund allocation, and performance KPIs.
    """
    report_data = await impact_report_service.generate_impact_report(
        db=db,
        start_date=body.start_date,
        end_date=body.end_date,
        generated_by_user_id=user.id,
    )
    data = ImpactReportData.from_report_dict(report_data)
    pdf_bytes = _pdf_generator.generate_bytes(data)

    start_str = body.start_date.strftime("%Y%m%d")
    end_str = body.end_date.strftime("%Y%m%d")
    filename = f"impact-report-{start_str}-{end_str}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
