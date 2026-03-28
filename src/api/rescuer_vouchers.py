"""Rescuer voucher wallet and claim flow API endpoints.

Endpoints:
    GET  /api/rescuer/vouchers/available  -- discover available vouchers
    POST /api/rescuer/vouchers/{code}/claim -- claim a voucher
    GET  /api/rescuer/vouchers/wallet     -- list rescuer's claimed/redeemed vouchers
    GET  /api/rescuer/vouchers/summary    -- wallet summary counts
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.rescuer_voucher_service import (
    VoucherAlreadyClaimedError,
    VoucherClaimRequest,
    VoucherNotClaimableError,
    claim_voucher,
    get_available_vouchers,
    get_rescuer_wallet,
    get_rescuer_wallet_summary,
)
from src.services.vet_voucher_service import VoucherCodeNotFoundError, VoucherExpiredError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuer/vouchers",
    tags=["rescuer-vouchers"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class AvailableVoucherResponse(BaseModel):
    """Voucher available for claiming."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    amount_pyg: int
    amount_eur: float | None = None
    clinic_id: UUID | None = None
    service_category: str | None = None
    expires_at: str
    notes: str | None = None


class AvailableVoucherListResponse(BaseModel):
    """Paginated list of available vouchers."""

    items: list[AvailableVoucherResponse]
    total: int
    page: int
    page_size: int


class ClaimVoucherRequest(BaseModel):
    """Request to claim a voucher."""

    animal_id: UUID | None = None
    note: str | None = None


class ClaimVoucherResponse(BaseModel):
    """Response after successfully claiming a voucher."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    status: str
    amount_pyg: int
    amount_eur: float | None = None
    clinic_id: UUID | None = None
    service_category: str | None = None
    claimed_at: str


class WalletVoucherResponse(BaseModel):
    """Voucher in rescuer's wallet."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    status: str
    amount_pyg: int
    amount_eur: float | None = None
    clinic_id: UUID | None = None
    service_category: str | None = None
    assigned_at: str | None = None
    redeemed_at: str | None = None
    notes: str | None = None


class WalletVoucherListResponse(BaseModel):
    """Paginated wallet listing."""

    items: list[WalletVoucherResponse]
    total: int
    page: int
    page_size: int


class WalletSummaryResponse(BaseModel):
    """Wallet summary counts."""

    claimed: int
    redeemed: int


# --- Endpoints ---


@router.get("/available", response_model=AvailableVoucherListResponse)
async def list_available_vouchers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    service_category: str | None = Query(None, description="Filter by service category"),
    clinic_id: UUID | None = Query(None, description="Filter by clinic"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> AvailableVoucherListResponse:
    """List available vouchers for claiming.

    Returns purchased vouchers that haven't expired, sorted by expiry (soonest first).
    """
    vouchers, total = await get_available_vouchers(
        db,
        page=page,
        page_size=page_size,
        service_category=service_category,
        clinic_id=clinic_id,
    )
    return AvailableVoucherListResponse(
        items=[AvailableVoucherResponse.model_validate(v) for v in vouchers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{code}/claim",
    response_model=ClaimVoucherResponse,
    status_code=status.HTTP_201_CREATED,
)
async def claim_voucher_endpoint(
    code: str,
    body: ClaimVoucherRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> ClaimVoucherResponse:
    """Claim a voucher for the current rescuer.

    Transitions the voucher from 'purchased' to 'assigned' with the
    current user as beneficiary.
    """
    claim_request = VoucherClaimRequest(
        rescuer_id=current_user.id,
        animal_id=body.animal_id,
        note=body.note,
    )

    try:
        result = await claim_voucher(db, code, claim_request)
    except VoucherCodeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voucher with code '{code}' not found.",
        ) from None
    except VoucherExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Voucher '{code}' has expired and cannot be claimed.",
        ) from None
    except VoucherAlreadyClaimedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Voucher '{code}' has already been claimed by another rescuer.",
        ) from None
    except VoucherNotClaimableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()

    voucher = result.voucher
    return ClaimVoucherResponse(
        id=voucher.id,
        code=voucher.code,
        status=voucher.status,
        amount_pyg=voucher.amount_pyg,
        amount_eur=voucher.amount_eur,
        clinic_id=voucher.clinic_id,
        service_category=voucher.service_category,
        claimed_at=str(result.claimed_at),
    )


@router.get("/wallet", response_model=WalletVoucherListResponse)
async def list_rescuer_wallet(
    status_filter: str | None = Query(None, description="Filter by status (assigned/redeemed)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> WalletVoucherListResponse:
    """List vouchers in the current rescuer's wallet."""
    vouchers, total = await get_rescuer_wallet(
        db,
        rescuer_id=current_user.id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )
    return WalletVoucherListResponse(
        items=[WalletVoucherResponse.model_validate(v) for v in vouchers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=WalletSummaryResponse)
async def get_wallet_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> WalletSummaryResponse:
    """Get wallet summary counts for the current rescuer."""
    summary = await get_rescuer_wallet_summary(db, rescuer_id=current_user.id)
    return WalletSummaryResponse(**summary)
