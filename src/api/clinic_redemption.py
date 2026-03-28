"""Clinic voucher redemption API endpoints.

Endpoints:
  GET  /api/clinic/vouchers/lookup/{code}  - Look up voucher by code (staff)
  POST /api/clinic/vouchers/{code}/redeem  - Redeem voucher with proof (staff)
  GET  /api/clinic/{clinic_id}/vouchers    - List clinic vouchers (staff)
  GET  /api/clinic/{clinic_id}/reconciliation - Monthly reconciliation (staff)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.vet_voucher import VetVoucherResponse
from src.services.clinic_redemption_service import (
    VoucherClinicMismatchError,
    VoucherNotAssignedError,
    get_clinic_reconciliation_summary,
    list_clinic_vouchers,
    lookup_voucher_for_redemption,
    redeem_voucher_at_clinic,
)
from src.services.vet_voucher_service import (
    InvalidVoucherTransitionError,
    VoucherCodeNotFoundError,
    VoucherExpiredError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/clinic",
    tags=["clinic-redemption"],
    responses=COMMON_RESPONSES,
)


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class RedeemVoucherRequest(BaseModel):
    """Request body for voucher redemption."""

    clinic_id: UUID = Field(..., description="ID of the clinic performing redemption")
    service_id: UUID | None = Field(None, description="ID of the service performed")
    proof_photo_url: str | None = Field(None, max_length=500, description="URL of proof photo")
    proof_description: str | None = Field(
        None, max_length=1000, description="Description of service performed"
    )
    invoice_url: str | None = Field(None, max_length=500, description="URL of clinic invoice")
    invoice_filename: str | None = Field(
        None, max_length=255, description="Original invoice filename"
    )


class RedemptionResponse(BaseModel):
    """Response after successful voucher redemption."""

    status: str = "success"
    message: str = "Voucher redeemed successfully. Donor will receive notification."
    voucher: VetVoucherResponse


class ClinicVoucherListResponse(BaseModel):
    """Paginated list of clinic vouchers."""

    items: list[VetVoucherResponse]
    total: int
    page: int
    page_size: int


class ReconciliationResponse(BaseModel):
    """Monthly reconciliation summary for a clinic."""

    clinic_id: str
    month: int
    year: int
    total_redeemed: int
    total_amount_pyg: int


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def _handle_redemption_error(exc: Exception) -> HTTPException:
    """Map domain exceptions to HTTP responses."""
    if isinstance(exc, VoucherCodeNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, VoucherNotAssignedError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, VoucherExpiredError):
        return HTTPException(status_code=status.HTTP_410_GONE, detail=exc.message)
    if isinstance(exc, VoucherClinicMismatchError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, InvalidVoucherTransitionError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error."
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/vouchers/lookup/{code}", response_model=VetVoucherResponse)
async def lookup_voucher(
    code: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Look up a voucher by code and validate it is ready for redemption."""
    try:
        voucher = await lookup_voucher_for_redemption(db, code)
    except (VoucherCodeNotFoundError, VoucherNotAssignedError, VoucherExpiredError) as exc:
        raise _handle_redemption_error(exc) from exc
    return VetVoucherResponse.model_validate(voucher)


@router.post("/vouchers/{code}/redeem", response_model=RedemptionResponse)
async def redeem_voucher(
    code: str,
    body: RedeemVoucherRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> RedemptionResponse:
    """Redeem a voucher at a clinic with proof of service."""
    try:
        voucher = await redeem_voucher_at_clinic(
            db,
            code,
            clinic_id=body.clinic_id,
            redeemed_by_user_id=current_user.id,
            service_id=body.service_id,
            proof_photo_url=body.proof_photo_url,
            proof_description=body.proof_description,
            invoice_url=body.invoice_url,
            invoice_filename=body.invoice_filename,
        )
    except (
        VoucherCodeNotFoundError,
        VoucherNotAssignedError,
        VoucherExpiredError,
        VoucherClinicMismatchError,
        InvalidVoucherTransitionError,
    ) as exc:
        raise _handle_redemption_error(exc) from exc

    return RedemptionResponse(voucher=VetVoucherResponse.model_validate(voucher))


@router.get("/{clinic_id}/vouchers", response_model=ClinicVoucherListResponse)
async def list_vouchers_for_clinic(
    clinic_id: UUID,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ClinicVoucherListResponse:
    """List vouchers associated with a clinic (restricted or redeemed)."""
    vouchers, total = await list_clinic_vouchers(
        db, clinic_id, status=status_filter, page=page, page_size=page_size
    )
    return ClinicVoucherListResponse(
        items=[VetVoucherResponse.model_validate(v) for v in vouchers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{clinic_id}/reconciliation", response_model=ReconciliationResponse)
async def get_reconciliation(
    clinic_id: UUID,
    month: int | None = Query(None, ge=1, le=12, description="Month (1-12)"),
    year: int | None = Query(None, ge=2020, le=2099, description="Year"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ReconciliationResponse:
    """Get monthly reconciliation summary for a clinic."""
    summary = await get_clinic_reconciliation_summary(db, clinic_id, month=month, year=year)
    return ReconciliationResponse(**summary)
