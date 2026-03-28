"""Voucher expiry and refund policy API endpoints.

Endpoints:
  POST /api/vet-vouchers/expire     - Run batch expiry (admin)
  GET  /api/vet-vouchers/expiring   - List vouchers expiring soon (staff)
  GET  /api/vet-vouchers/{id}/refund-eligibility - Check refund eligibility (staff)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.vet_voucher import VetVoucherResponse
from src.services.vet_voucher_service import VoucherNotFoundError, get_voucher
from src.services.voucher_expiry_service import (
    GRACE_PERIOD_DAYS,
    REFUND_POLICY_TIERS,
    assess_refund_eligibility,
    expire_overdue_vouchers,
    get_expiring_soon_vouchers,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vet-vouchers",
    tags=["voucher-expiry"],
    responses=COMMON_RESPONSES,
)


class ExpiryRunResponse(BaseModel):
    """Response from a batch expiry run."""

    expired_count: int = Field(..., description="Number of vouchers expired.")
    voucher_ids: list[UUID] = Field(..., description="IDs of expired vouchers.")


class RefundEligibilityResponse(BaseModel):
    """Response for refund eligibility check."""

    eligible: bool
    refund_percentage: int
    refund_amount_pyg: int
    reason: str


class RefundPolicyResponse(BaseModel):
    """Response describing the current refund policy."""

    tiers: list[dict] = Field(..., description="Refund tiers by days remaining.")
    grace_period_days: int = Field(..., description="Days after expiry for grace refund.")


class ExpiringSoonResponse(BaseModel):
    """Response for vouchers expiring soon."""

    items: list[VetVoucherResponse]
    days_ahead: int


@router.post("/expire", response_model=ExpiryRunResponse)
async def run_batch_expiry(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> ExpiryRunResponse:
    """Run batch expiry on all overdue vouchers. Admin only."""
    result = await expire_overdue_vouchers(db)
    return ExpiryRunResponse(
        expired_count=result.expired_count,
        voucher_ids=result.voucher_ids,
    )


@router.get("/expiring", response_model=ExpiringSoonResponse)
async def list_expiring_soon(
    days_ahead: int = Query(7, ge=1, le=90, description="Days ahead to check"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ExpiringSoonResponse:
    """List vouchers expiring within the specified number of days."""
    vouchers = await get_expiring_soon_vouchers(db, days_ahead)
    return ExpiringSoonResponse(
        items=[VetVoucherResponse.model_validate(v) for v in vouchers],
        days_ahead=days_ahead,
    )


@router.get("/{voucher_id}/refund-eligibility", response_model=RefundEligibilityResponse)
async def check_refund_eligibility(
    voucher_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> RefundEligibilityResponse:
    """Check if a voucher is eligible for a refund and the refund amount."""
    try:
        voucher = await get_voucher(db, voucher_id)
    except VoucherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc

    eligibility = assess_refund_eligibility(voucher)
    return RefundEligibilityResponse(
        eligible=eligibility.eligible,
        refund_percentage=eligibility.refund_percentage,
        refund_amount_pyg=eligibility.refund_amount_pyg,
        reason=eligibility.reason,
    )


@router.get("/refund-policy", response_model=RefundPolicyResponse)
async def get_refund_policy(
    _current_user: User = Depends(require_staff),
) -> RefundPolicyResponse:
    """Get the current refund policy tiers and grace period."""
    tiers = [
        {"min_days_remaining": min_days, "refund_percentage": pct}
        for min_days, pct in REFUND_POLICY_TIERS
    ]
    return RefundPolicyResponse(
        tiers=tiers,
        grace_period_days=GRACE_PERIOD_DAYS,
    )
