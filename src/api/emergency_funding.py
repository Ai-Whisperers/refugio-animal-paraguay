"""Emergency funding API endpoints.

Handles donation recording, funding status checks, and batch processing
for emergency case auto-close functionality.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.emergency_funding_service import (
    EmergencyNotFoundError,
    FundingCheckError,
    batch_check_active_emergencies,
    check_and_update_funding,
    get_funding_progress,
    process_donation_for_emergency,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DonationRecordRequest(BaseModel):
    """Request body for recording a donation to an emergency."""

    donation_amount_cents: int = Field(..., gt=0)


class FundingCheckResponse(BaseModel):
    """Response for a funding check."""

    emergency_id: UUID
    previous_status: str
    new_status: str
    amount_needed_cents: int
    amount_raised_cents: int
    is_funded: bool
    action_taken: str


class FundingProgressResponse(BaseModel):
    """Funding progress for an emergency."""

    emergency_id: UUID
    status: str
    amount_needed_cents: int
    amount_raised_cents: int
    amount_remaining_cents: int
    funding_percentage: float
    is_fully_funded: bool
    currency: str
    deadline: str | None = None


class BatchCheckResponse(BaseModel):
    """Response for batch funding check."""

    processed: int
    results: list[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_funding_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, EmergencyNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, FundingCheckError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/emergencies",
    tags=["emergency-funding"],
)


@public_router.get(
    "/{emergency_id}/funding",
    response_model=FundingProgressResponse,
)
async def funding_progress(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get funding progress for an emergency case."""
    try:
        return await get_funding_progress(
            emergency_id=emergency_id,
            db=db,
        )
    except Exception as exc:
        _handle_funding_error(exc)
        raise


@public_router.post(
    "/{emergency_id}/donate",
    response_model=FundingCheckResponse,
)
async def record_donation(
    emergency_id: UUID,
    body: DonationRecordRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Record a donation for an emergency case and check funding status.

    Auto-transitions the emergency to 'funded' if the target is reached.
    """
    try:
        result = await process_donation_for_emergency(
            emergency_id=emergency_id,
            donation_amount_cents=body.donation_amount_cents,
            db=db,
        )
        await db.commit()
        return result
    except Exception as exc:
        _handle_funding_error(exc)
        raise


# ---------------------------------------------------------------------------
# Admin router
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/emergencies",
    tags=["emergency-funding-admin"],
    dependencies=[Depends(require_staff)],
)


@admin_router.post(
    "/{emergency_id}/check-funding",
    response_model=FundingCheckResponse,
)
async def check_funding(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Manually trigger a funding check for an emergency case."""
    try:
        result = await check_and_update_funding(
            emergency_id=emergency_id,
            db=db,
        )
        await db.commit()
        return result
    except Exception as exc:
        _handle_funding_error(exc)
        raise


@admin_router.post(
    "/batch-check",
    response_model=BatchCheckResponse,
)
async def batch_check(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Run batch funding and expiry check on all active emergencies.

    Finds cases that are fully funded or past deadline and updates
    their status accordingly.
    """
    results = await batch_check_active_emergencies(db)
    await db.commit()
    return {
        "processed": len(results),
        "results": results,
    }
