"""Impact reports router.

Endpoints:
  POST /impact-reports/generate  -- generate impact report for date range (staff only)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.impact_report import ImpactReportRequest, ImpactReportResponse
from src.services import impact_report_service

router = APIRouter(prefix="/impact-reports", tags=["impact-reports"])


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
