"""Impact report generation endpoint.

Endpoints:
  GET /reports/impact — generate shelter impact report for a date range
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.impact_report import ImpactReport
from src.services.impact_report_service import generate_impact_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/impact", response_model=ImpactReport)
async def get_impact_report(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> ImpactReport:
    """Generate a shelter impact report for the specified date range.

    Defaults to last 12 months if no dates provided. Aggregates data from
    animals, adoption requests, monetary donations, and in-kind donations.
    """
    if end_date is None:
        end_date = datetime.now(UTC)
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    return await generate_impact_report(db, start_date, end_date)
