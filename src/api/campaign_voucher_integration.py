"""Endpoints for castration campaign / vet voucher integration.

Endpoints:
    POST /admin/campaigns/castration/{id}/voucher-redeemed  -- record voucher redemption
    GET  /admin/campaigns/castration/{id}/stats              -- campaign voucher stats
    GET  /admin/campaigns/castration/{id}/vouchers           -- list campaign vouchers
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.campaign_voucher_integration_service import (
    VoucherNotLinkedError,
    get_campaign_stats,
    get_campaign_vouchers,
    handle_voucher_redeemed,
)
from src.services.castration_campaign_service import CampaignNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/campaigns/castration",
    tags=["campaign-voucher-integration"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class VoucherRedeemedRequest(BaseModel):
    """Request body for recording a voucher redemption."""

    voucher_id: UUID


class VoucherRedeemedResponse(BaseModel):
    """Response from voucher redemption recording."""

    skipped: bool
    reason: str | None = None
    campaign_id: str | None = None
    completed_count: int | None = None
    target_count: int | None = None
    progress_percent: int | None = None
    is_complete: bool | None = None
    milestone: str | None = None


class CampaignStatsResponse(BaseModel):
    """Campaign stats including voucher breakdown."""

    campaign_id: str
    title: str
    target_count: int
    completed_count: int
    progress_percent: int
    status: str
    partner_clinic_count: int
    total_vouchers: int
    vouchers_by_status: dict[str, int]


class CampaignVoucherResponse(BaseModel):
    """A voucher linked to a campaign."""

    id: UUID
    code: str
    status: str
    service_category: str | None = None
    amount_pyg: int
    clinic_id: UUID | None = None


class CampaignVoucherListResponse(BaseModel):
    """List of campaign vouchers."""

    items: list[CampaignVoucherResponse]
    total: int


# --- Endpoints ---


@router.post(
    "/{campaign_id}/voucher-redeemed",
    response_model=VoucherRedeemedResponse,
)
async def record_voucher_redeemed(
    campaign_id: UUID,
    body: VoucherRedeemedRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> VoucherRedeemedResponse:
    """Record a voucher redemption and update campaign progress."""
    try:
        result = await handle_voucher_redeemed(db, body.voucher_id, campaign_id)
    except VoucherNotLinkedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None

    await db.commit()
    return VoucherRedeemedResponse(**result)


@router.get(
    "/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
)
async def get_stats(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> CampaignStatsResponse:
    """Get campaign statistics including voucher breakdown."""
    try:
        stats = await get_campaign_stats(db, campaign_id)
    except CampaignNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Castration campaign {campaign_id} not found.",
        ) from None

    return CampaignStatsResponse(**stats)


@router.get(
    "/{campaign_id}/vouchers",
    response_model=CampaignVoucherListResponse,
)
async def list_vouchers(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> CampaignVoucherListResponse:
    """List all vouchers associated with a campaign's partner clinics."""
    try:
        vouchers = await get_campaign_vouchers(db, campaign_id)
    except CampaignNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Castration campaign {campaign_id} not found.",
        ) from None

    return CampaignVoucherListResponse(
        items=[
            CampaignVoucherResponse(
                id=v.id,
                code=v.code,
                status=v.status,
                service_category=v.service_category,
                amount_pyg=v.amount_pyg,
                clinic_id=v.clinic_id,
            )
            for v in vouchers
        ],
        total=len(vouchers),
    )
