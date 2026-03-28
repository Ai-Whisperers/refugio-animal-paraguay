"""Veterinary voucher lifecycle API endpoints.

Endpoints:
  GET    /api/vet-vouchers           - List vouchers (staff/admin)
  POST   /api/vet-vouchers           - Create voucher (staff/admin)
  GET    /api/vet-vouchers/{id}      - Get voucher detail (staff/admin)
  GET    /api/vet-vouchers/code/{code} - Lookup by code (staff/admin)
  POST   /api/vet-vouchers/{id}/assign - Assign to beneficiary (staff/admin)
  POST   /api/vet-vouchers/{id}/redeem - Redeem at clinic (staff/admin)
  POST   /api/vet-vouchers/{id}/cancel - Cancel with reason (admin)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.vet_voucher import (
    VetVoucherAssign,
    VetVoucherCancel,
    VetVoucherCreate,
    VetVoucherListResponse,
    VetVoucherRedeem,
    VetVoucherResponse,
)
from src.services.vet_voucher_service import (
    InvalidVoucherTransitionError,
    VoucherCodeNotFoundError,
    VoucherExpiredError,
    VoucherNotFoundError,
    assign_voucher,
    cancel_voucher,
    create_voucher,
    get_voucher,
    get_voucher_by_code,
    list_vouchers,
    redeem_voucher,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vet-vouchers",
    tags=["vet-vouchers"],
    responses=COMMON_RESPONSES,
)


def _handle_voucher_errors(exc: Exception) -> HTTPException:
    """Map service exceptions to HTTP responses."""
    if isinstance(exc, (VoucherNotFoundError, VoucherCodeNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, InvalidVoucherTransitionError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, VoucherExpiredError):
        return HTTPException(status_code=status.HTTP_410_GONE, detail=exc.message)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error"
    )


@router.get("", response_model=VetVoucherListResponse)
async def list_vet_vouchers(
    voucher_status: str | None = Query(None, alias="status", description="Filter by status"),
    donor_id: UUID | None = Query(None, description="Filter by donor"),
    beneficiary_id: UUID | None = Query(None, description="Filter by beneficiary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherListResponse:
    """List vouchers with optional filters."""
    vouchers, total = await list_vouchers(
        db,
        status=voucher_status,
        donor_id=donor_id,
        beneficiary_id=beneficiary_id,
        page=page,
        page_size=page_size,
    )
    return VetVoucherListResponse(
        items=[VetVoucherResponse.model_validate(v) for v in vouchers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=VetVoucherResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_voucher(
    body: VetVoucherCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Create a new veterinary voucher."""
    voucher = await create_voucher(db, body.model_dump())
    return VetVoucherResponse.model_validate(voucher)


@router.get("/{voucher_id}", response_model=VetVoucherResponse)
async def get_vet_voucher(
    voucher_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Get details of a single voucher by ID."""
    try:
        voucher = await get_voucher(db, voucher_id)
    except VoucherNotFoundError as exc:
        raise _handle_voucher_errors(exc) from exc
    return VetVoucherResponse.model_validate(voucher)


@router.get("/code/{code}", response_model=VetVoucherResponse)
async def lookup_voucher_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Look up a voucher by its human-readable code."""
    try:
        voucher = await get_voucher_by_code(db, code)
    except VoucherCodeNotFoundError as exc:
        raise _handle_voucher_errors(exc) from exc
    return VetVoucherResponse.model_validate(voucher)


@router.post("/{voucher_id}/assign", response_model=VetVoucherResponse)
async def assign_vet_voucher(
    voucher_id: UUID,
    body: VetVoucherAssign,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Assign a purchased voucher to a beneficiary."""
    try:
        voucher = await assign_voucher(db, voucher_id, body.beneficiary_id)
    except (VoucherNotFoundError, InvalidVoucherTransitionError, VoucherExpiredError) as exc:
        raise _handle_voucher_errors(exc) from exc
    return VetVoucherResponse.model_validate(voucher)


@router.post("/{voucher_id}/redeem", response_model=VetVoucherResponse)
async def redeem_vet_voucher(
    voucher_id: UUID,
    body: VetVoucherRedeem,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetVoucherResponse:
    """Redeem a voucher at a clinic."""
    try:
        voucher = await redeem_voucher(db, voucher_id, body.clinic_id, body.service_id)
    except (VoucherNotFoundError, InvalidVoucherTransitionError, VoucherExpiredError) as exc:
        raise _handle_voucher_errors(exc) from exc
    return VetVoucherResponse.model_validate(voucher)


@router.post("/{voucher_id}/cancel", response_model=VetVoucherResponse)
async def cancel_vet_voucher(
    voucher_id: UUID,
    body: VetVoucherCancel,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> VetVoucherResponse:
    """Cancel a voucher with a reason. Admin only."""
    try:
        voucher = await cancel_voucher(db, voucher_id, body.reason)
    except (VoucherNotFoundError, InvalidVoucherTransitionError) as exc:
        raise _handle_voucher_errors(exc) from exc
    return VetVoucherResponse.model_validate(voucher)
