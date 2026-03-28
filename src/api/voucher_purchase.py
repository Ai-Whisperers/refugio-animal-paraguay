"""Voucher purchase API endpoints.

Endpoints:
  GET  /api/vouchers/price-check           - Calculate purchase price
  POST /api/vouchers/purchase              - Create voucher purchase
  GET  /api/vouchers/my-vouchers           - List donor's vouchers
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
from src.services.voucher_purchase_service import (
    DEFAULT_VOUCHER_VALIDITY_DAYS,
    ClinicServiceNotFoundError,
    InvalidQuantityError,
    VoucherPurchaseRequest,
    calculate_purchase_price,
    create_vouchers_for_purchase,
    get_donor_vouchers,
    get_service_for_purchase,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vouchers",
    tags=["voucher-purchase"],
    responses=COMMON_RESPONSES,
)


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class PriceCheckRequest(BaseModel):
    """Query parameters for price calculation."""

    service_id: UUID = Field(..., description="Clinic service to purchase vouchers for")
    quantity: int = Field(1, ge=1, le=100, description="Number of vouchers to purchase")


class PriceCheckResponse(BaseModel):
    """Price breakdown response."""

    service_name: str
    service_category: str
    unit_price_pyg: int
    unit_price_eur: float | None
    quantity: int
    total_pyg: int
    total_eur: float | None


class PurchaseRequest(BaseModel):
    """Request body for voucher purchase."""

    clinic_id: UUID = Field(..., description="Clinic to restrict vouchers to")
    service_id: UUID = Field(..., description="Clinic service")
    quantity: int = Field(1, ge=1, le=100, description="Number of vouchers")
    payment_method: str = Field(
        ..., pattern="^(stripe|sepa)$", description="Payment method: 'stripe' or 'sepa'"
    )
    validity_days: int = Field(
        DEFAULT_VOUCHER_VALIDITY_DAYS,
        ge=1,
        le=365,
        description="Voucher validity in days",
    )


class PurchaseResponse(BaseModel):
    """Response after successful voucher purchase."""

    status: str = "success"
    message: str
    voucher_codes: list[str]
    total_pyg: int
    total_eur: float | None
    quantity: int
    service_name: str
    expires_at: str


class DonorVoucherListResponse(BaseModel):
    """Paginated list of donor's vouchers."""

    items: list[VetVoucherResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/price-check", response_model=PriceCheckResponse)
async def check_price(
    body: PriceCheckRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> PriceCheckResponse:
    """Calculate purchase price for vouchers without creating them."""
    try:
        service = await get_service_for_purchase(db, body.service_id)
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc

    try:
        breakdown = calculate_purchase_price(service, body.quantity)
    except InvalidQuantityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    return PriceCheckResponse(
        service_name=breakdown.service_name,
        service_category=breakdown.service_category,
        unit_price_pyg=breakdown.unit_price_pyg,
        unit_price_eur=breakdown.unit_price_eur,
        quantity=breakdown.quantity,
        total_pyg=breakdown.total_pyg,
        total_eur=breakdown.total_eur,
    )


@router.post("/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase_vouchers(
    body: PurchaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PurchaseResponse:
    """Purchase vouchers for a clinic service.

    Creates N voucher records (one per quantity) and returns
    the codes for the donor to share with rescuers.
    """
    try:
        service = await get_service_for_purchase(db, body.service_id)
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc

    request = VoucherPurchaseRequest(
        donor_id=current_user.id,
        clinic_id=body.clinic_id,
        service_id=body.service_id,
        quantity=body.quantity,
        payment_method=body.payment_method,
        validity_days=body.validity_days,
    )

    try:
        result = await create_vouchers_for_purchase(db, request, service)
    except InvalidQuantityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    return PurchaseResponse(
        message=f"Successfully purchased {result.quantity} voucher(s) for {result.service_name}.",
        voucher_codes=result.voucher_codes,
        total_pyg=result.total_pyg,
        total_eur=result.total_eur,
        quantity=result.quantity,
        service_name=result.service_name,
        expires_at=result.expires_at.isoformat(),
    )


@router.get("/my-vouchers", response_model=DonorVoucherListResponse)
async def list_my_vouchers(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DonorVoucherListResponse:
    """List vouchers purchased by the current donor."""
    vouchers, total = await get_donor_vouchers(
        db, current_user.id, status=status_filter, page=page, page_size=page_size
    )
    return DonorVoucherListResponse(
        items=[VetVoucherResponse.model_validate(v) for v in vouchers],
        total=total,
        page=page,
        page_size=page_size,
    )
