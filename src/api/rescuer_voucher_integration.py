"""Rescuer-voucher integration endpoints — eligibility, history, and stats.

Endpoints:
  GET  /api/rescuers/vouchers/eligibility   -- check voucher eligibility (authenticated rescuer)
  GET  /api/rescuers/vouchers/history       -- voucher history (authenticated rescuer)
  GET  /api/rescuers/vouchers/stats         -- voucher statistics (authenticated rescuer)
  POST /api/rescuers/vouchers/check         -- pre-check voucher request (authenticated rescuer)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.services.rescuer_voucher_integration_service import (
    InvalidServiceCategoryError,
    RescuerProfileRequiredError,
    RescuerVoucherError,
    VoucherLimitExceededError,
    check_voucher_request_eligibility,
    get_rescuer_voucher_eligibility,
    get_rescuer_voucher_history,
    get_rescuer_voucher_stats,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuers/vouchers",
    tags=["rescuer-voucher-integration"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VoucherEligibilityResponse(BaseModel):
    """Response for voucher eligibility check."""

    rescuer_profile_id: str
    is_verified: bool
    voucher_limit: int
    active_vouchers: int
    remaining_slots: int
    can_request_more: bool
    lifetime_redeemed: int
    lifetime_redeemed_pyg: int


class VoucherHistoryItemResponse(BaseModel):
    """Response for a single voucher in history."""

    id: UUID
    code: str
    status: str
    amount_pyg: int
    amount_eur: float | None = None
    service_category: str | None = None
    clinic_id: UUID | None = None

    model_config = {"from_attributes": True}


class VoucherStatsResponse(BaseModel):
    """Response for voucher statistics."""

    rescuer_profile_id: str
    is_verified: bool
    by_status: dict
    by_category: dict
    total_vouchers: int
    total_value_pyg: int


class VoucherCheckRequest(BaseModel):
    """Request body for voucher eligibility pre-check."""

    service_category: str | None = Field(
        default=None,
        max_length=50,
        description="Service category to check eligibility for",
    )


class VoucherCheckResponse(BaseModel):
    """Response for voucher eligibility pre-check."""

    eligible: bool
    rescuer_profile_id: str
    is_verified: bool
    remaining_slots: int
    service_category: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/eligibility",
    response_model=VoucherEligibilityResponse,
    summary="Check voucher eligibility",
    description="Check the authenticated rescuer's voucher eligibility and usage.",
)
async def get_eligibility_endpoint(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoucherEligibilityResponse:
    """Check rescuer's voucher eligibility."""
    try:
        result = await get_rescuer_voucher_eligibility(current_user.id, db)
    except RescuerProfileRequiredError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile. Register first.",
            },
        ) from None

    return VoucherEligibilityResponse(**result)


@router.get(
    "/history",
    response_model=list[VoucherHistoryItemResponse],
    summary="Voucher history",
    description="Get the authenticated rescuer's voucher history.",
)
async def get_history_endpoint(
    status_filter: str | None = Query(None, description="Filter by voucher status"),
    service_category: str | None = Query(None, description="Filter by service category"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherHistoryItemResponse]:
    """Get rescuer's voucher history."""
    try:
        vouchers = await get_rescuer_voucher_history(
            current_user.id,
            db,
            status_filter=status_filter,
            service_category=service_category,
            limit=limit,
            offset=offset,
        )
    except RescuerProfileRequiredError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile.",
            },
        ) from None
    except RescuerVoucherError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    return [VoucherHistoryItemResponse.model_validate(v) for v in vouchers]


@router.get(
    "/stats",
    response_model=VoucherStatsResponse,
    summary="Voucher statistics",
    description="Get the authenticated rescuer's voucher statistics.",
)
async def get_stats_endpoint(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoucherStatsResponse:
    """Get rescuer's voucher statistics."""
    try:
        result = await get_rescuer_voucher_stats(current_user.id, db)
    except RescuerProfileRequiredError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile.",
            },
        ) from None

    return VoucherStatsResponse(**result)


@router.post(
    "/check",
    response_model=VoucherCheckResponse,
    summary="Pre-check voucher request",
    description="Pre-check whether the rescuer can request a voucher.",
)
async def check_eligibility_endpoint(
    body: VoucherCheckRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoucherCheckResponse:
    """Pre-check voucher request eligibility."""
    try:
        result = await check_voucher_request_eligibility(
            current_user.id,
            body.service_category,
            db,
        )
    except RescuerProfileRequiredError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile. Register first.",
            },
        ) from None
    except VoucherLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "limit_exceeded",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None
    except InvalidServiceCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()
    return VoucherCheckResponse(**result)
