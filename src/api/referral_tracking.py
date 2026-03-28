"""Referral tracking API endpoints.

Public endpoints for creating and converting referrals.
Admin endpoints for metrics, leaderboard, and analytics.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.referral_service import (
    InvalidConversionTypeError,
    ReferralExpiredError,
    ReferralNotFoundError,
    SelfReferralError,
    convert_referral,
    create_referral,
    get_referral_analytics,
    get_referral_metrics,
    get_referrer_leaderboard,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReferralCreateRequest(BaseModel):
    """Create a referral when a user lands via a ref link."""

    referrer_user_id: UUID
    landing_path: str | None = None


class ReferralConvertRequest(BaseModel):
    """Convert a referral to a donation, adoption application, etc."""

    referred_user_id: UUID
    conversion_type: str
    conversion_entity_id: UUID | None = None


class ReferralResponse(BaseModel):
    """Referral record returned to the client."""

    id: UUID
    referrer_user_id: UUID
    referred_user_id: UUID | None = None
    conversion_type: str | None = None
    conversion_entity_id: UUID | None = None
    landing_path: str | None = None
    converted_at: str | None = None
    expires_at: str
    created_at: str

    model_config = {"from_attributes": True}


class ReferralMetricsResponse(BaseModel):
    """Overall referral metrics."""

    total_referrals: int
    total_referrers: int
    total_conversions: int
    conversions_by_type: dict[str, int]
    conversion_rate_pct: float
    period_days: int


class LeaderboardEntryResponse(BaseModel):
    """Single entry in the referrer leaderboard."""

    referrer_user_id: str
    total_referrals: int
    total_conversions: int
    conversions_by_type: dict[str, int]


class ReferralAnalyticsResponse(BaseModel):
    """Daily referral analytics time series."""

    daily_data: list[dict]
    period_days: int


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

public_router = APIRouter(prefix="/api/referrals", tags=["referrals"])
admin_router = APIRouter(
    prefix="/api/admin/referrals",
    tags=["admin-referrals"],
    dependencies=[Depends(require_staff)],
)

REFERRAL_DEFAULT_DAYS = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_referral(referral: object) -> dict:
    """Convert a Referral ORM object to a dict suitable for ReferralResponse."""
    return {
        "id": referral.id,  # type: ignore[attr-defined]
        "referrer_user_id": referral.referrer_user_id,  # type: ignore[attr-defined]
        "referred_user_id": referral.referred_user_id,  # type: ignore[attr-defined]
        "conversion_type": referral.conversion_type,  # type: ignore[attr-defined]
        "conversion_entity_id": referral.conversion_entity_id,  # type: ignore[attr-defined]
        "landing_path": referral.landing_path,  # type: ignore[attr-defined]
        "converted_at": (
            referral.converted_at.isoformat()  # type: ignore[attr-defined]
            if referral.converted_at  # type: ignore[attr-defined]
            else None
        ),
        "expires_at": referral.expires_at.isoformat(),  # type: ignore[attr-defined]
        "created_at": referral.created_at.isoformat(),  # type: ignore[attr-defined]
    }


def _handle_referral_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, ReferralNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, ReferralExpiredError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, SelfReferralError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, InvalidConversionTypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.post(
    "/track",
    response_model=ReferralResponse,
    status_code=status.HTTP_201_CREATED,
)
async def track_referral(
    body: ReferralCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Record a referral when a user lands via a share link."""
    ip_address = request.client.host if request.client else None
    try:
        referral = await create_referral(
            referrer_user_id=body.referrer_user_id,
            landing_path=body.landing_path,
            ip_address=ip_address,
            db=db,
        )
        await db.commit()
        return _serialise_referral(referral)
    except Exception as exc:
        _handle_referral_error(exc)
        raise


@public_router.post(
    "/{referral_id}/convert",
    response_model=ReferralResponse,
)
async def convert_referral_endpoint(
    referral_id: UUID,
    body: ReferralConvertRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Mark a referral as converted (donation, adoption application, etc)."""
    try:
        referral = await convert_referral(
            referral_id=referral_id,
            referred_user_id=body.referred_user_id,
            conversion_type=body.conversion_type,
            conversion_entity_id=body.conversion_entity_id,
            db=db,
        )
        await db.commit()
        return _serialise_referral(referral)
    except Exception as exc:
        _handle_referral_error(exc)
        raise


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@admin_router.get("/metrics", response_model=ReferralMetricsResponse)
async def referral_metrics(
    days: int = REFERRAL_DEFAULT_DAYS,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get overall referral metrics for the specified period."""
    return await get_referral_metrics(db, days=days)


@admin_router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntryResponse],
)
async def referral_leaderboard(
    days: int = REFERRAL_DEFAULT_DAYS,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Get top referrers ranked by conversion count."""
    return await get_referrer_leaderboard(db, days=days, limit=limit)


@admin_router.get("/analytics", response_model=ReferralAnalyticsResponse)
async def referral_analytics(
    days: int = REFERRAL_DEFAULT_DAYS,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get daily referral analytics time series."""
    return await get_referral_analytics(db, days=days)
