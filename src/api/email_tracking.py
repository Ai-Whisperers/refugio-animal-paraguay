"""Email campaign open/click tracking endpoints.

Public (no auth required):
  GET  /email-campaigns/track/open/{campaign_id}          — record open, return 1x1 pixel
  GET  /email-campaigns/track/click/{campaign_id}?url=... — record click, redirect

Staff-only:
  GET  /email-campaigns/{campaign_id}/stats               — campaign engagement stats
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.email_tracking_service import (
    get_campaign_stats,
    record_click,
    record_open,
)

# 1x1 transparent GIF — standard tracking pixel payload
_TRACKING_PIXEL = bytes.fromhex(
    "47494638396101000100800000ffffff" "00000021f90400000000002c00000000" "010001000002024c01003b"
)

router = APIRouter(tags=["email-tracking"])


@router.get(
    "/email-campaigns/track/open/{campaign_id}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    include_in_schema=True,
    summary="Record email open event (tracking pixel)",
)
async def track_open(
    campaign_id: UUID,
    request: Request,
    recipient: str | None = Query(default=None, description="Encoded recipient email"),
    variant: str | None = Query(default=None, description="A/B variant (a or b)"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Return a 1x1 GIF pixel and record the open event.

    This endpoint is embedded as an img src in outbound campaign emails.
    Errors are swallowed and the pixel is always returned so email clients
    do not show a broken image.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    try:
        await record_open(
            db,
            campaign_id=campaign_id,
            recipient_email=recipient,
            ip_address=ip,
            user_agent=ua,
            variant=variant,
        )
        await db.commit()
    except Exception:
        # Never break the pixel response — silently ignore errors
        await db.rollback()

    return Response(
        content=_TRACKING_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get(
    "/email-campaigns/track/click/{campaign_id}",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    include_in_schema=True,
    summary="Record email click event and redirect",
)
async def track_click(
    campaign_id: UUID,
    request: Request,
    url: str = Query(..., description="Destination URL to redirect to after recording click"),
    recipient: str | None = Query(default=None, description="Encoded recipient email"),
    variant: str | None = Query(default=None, description="A/B variant (a or b)"),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Record a click event and redirect the user to the target URL.

    If the campaign is not found or in a non-trackable state, still
    redirects the user — the click just won't be recorded.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    redirect_url = url

    try:
        _, redirect_url = await record_click(
            db,
            campaign_id=campaign_id,
            clicked_url=url,
            recipient_email=recipient,
            ip_address=ip,
            user_agent=ua,
            variant=variant,
        )
        await db.commit()
    except Exception:
        await db.rollback()

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.get(
    "/email-campaigns/{campaign_id}/stats",
    summary="Get campaign engagement statistics (staff only)",
)
async def campaign_stats(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> dict:
    """Return aggregated opens/clicks statistics for a campaign."""
    try:
        return await get_campaign_stats(db, campaign_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
