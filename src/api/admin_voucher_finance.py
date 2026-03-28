"""Admin voucher financial reconciliation endpoints.

All endpoints require admin role authentication.

Endpoints:
  GET /api/admin/vouchers/finance/summary       — aggregate voucher stats
  GET /api/admin/vouchers/finance/clinics        — paginated clinic breakdown
  GET /api/admin/vouchers/finance/clinics/{id}   — clinic detail
  GET /api/admin/vouchers/finance/report         — monthly settlement report
  GET /api/admin/vouchers/finance/report/csv     — settlement report as CSV
"""

import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.voucher_finance import (
    ClinicDetailResponse,
    ClinicFinanceListResponse,
    SettlementReportResponse,
    VoucherFinanceSummary,
)
from src.services.voucher_finance_service import (
    format_settlement_csv,
    get_clinic_breakdown,
    get_clinic_detail,
    get_finance_summary,
    get_settlement_report,
)

logger = logging.getLogger(__name__)

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 10
VALID_SORT_FIELDS = {"clinic_name", "redeemed_vouchers", "amount_redeemed_pyg", "active_vouchers"}
VALID_SORT_DIRS = {"asc", "desc"}

router = APIRouter(
    prefix="/admin/vouchers/finance",
    tags=["admin", "voucher-finance"],
    responses=AUTHENTICATED_RESPONSES,
)


@router.get(
    "/summary",
    response_model=VoucherFinanceSummary,
    summary="Voucher program financial summary",
    description="Aggregate stats: total purchased, redeemed, expired, amounts collected/owed.",
)
async def finance_summary(
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> VoucherFinanceSummary:
    """Return aggregate financial summary for the entire voucher program."""
    return await get_finance_summary(db)


@router.get(
    "/clinics",
    response_model=ClinicFinanceListResponse,
    summary="Per-clinic financial breakdown",
    description="Paginated list of clinics with voucher counts and outstanding balances.",
)
async def clinic_finance_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    search: str | None = Query(default=None, max_length=200, description="Filter by clinic name"),
    sort_by: str = Query(default="clinic_name", description="Sort field"),
    sort_dir: str = Query(default="asc", description="Sort direction (asc/desc)"),
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ClinicFinanceListResponse:
    """Return paginated per-clinic financial breakdown."""
    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "clinic_name"
    if sort_dir not in VALID_SORT_DIRS:
        sort_dir = "asc"

    return await get_clinic_breakdown(
        db,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get(
    "/clinics/{clinic_id}",
    response_model=ClinicDetailResponse,
    summary="Detailed voucher view for a clinic",
    description="All vouchers associated with a specific clinic, grouped by status.",
)
async def clinic_finance_detail(
    clinic_id: UUID,
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ClinicDetailResponse:
    """Return detailed voucher breakdown for a single clinic."""
    result = await get_clinic_detail(db, clinic_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Clinic {clinic_id} not found"},
        )
    return result


@router.get(
    "/report",
    response_model=SettlementReportResponse,
    summary="Monthly settlement report",
    description="Redeemed vouchers grouped by month with totals. Optional date range filter.",
)
async def settlement_report(
    start_date: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SettlementReportResponse:
    """Return monthly settlement report for redeemed vouchers."""
    return await get_settlement_report(db, start_date=start_date, end_date=end_date)


@router.get(
    "/report/csv",
    summary="Download settlement report as CSV",
    description="Returns the settlement report as a downloadable CSV file.",
    responses={200: {"content": {"text/csv": {}}}},
)
async def settlement_report_csv(
    start_date: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Return the settlement report as a downloadable CSV file."""
    report = await get_settlement_report(db, start_date=start_date, end_date=end_date)
    csv_content = format_settlement_csv(report)

    filename = f"voucher_settlement_report_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
