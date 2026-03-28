"""API endpoints for survey distribution.

Admin endpoints for distributing surveys via email and WhatsApp,
and tracking delivery status.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.survey_distribution_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DistributionNotFoundError,
    InvalidDistributionError,
    create_bulk_distribution,
    create_distribution,
    get_distribution,
    get_distribution_stats,
    list_distributions,
    update_delivery_status,
)

router = APIRouter(tags=["Survey Distribution"])


# --- Schemas ---


class RecipientItem(BaseModel):
    """A single recipient for bulk distribution."""

    email: str | None = None
    phone: str | None = None


class CreateDistributionRequest(BaseModel):
    """Request body for creating a single distribution."""

    survey_id: UUID
    channel: str
    recipient_email: str | None = None
    recipient_phone: str | None = None


class BulkDistributionRequest(BaseModel):
    """Request body for bulk distribution."""

    survey_id: UUID
    channel: str
    recipients: list[RecipientItem]


class UpdateStatusRequest(BaseModel):
    """Request body for updating delivery status."""

    status: str
    failure_reason: str | None = None


class DistributionResponse(BaseModel):
    """Distribution record details."""

    id: UUID
    survey_id: UUID
    channel: str
    recipient_email: str | None = None
    recipient_phone: str | None = None
    delivery_status: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failure_reason: str | None = None
    sent_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DistributionListResponse(BaseModel):
    """Paginated list of distributions."""

    distributions: list[DistributionResponse]
    total: int
    limit: int
    offset: int


class DistributionStatsResponse(BaseModel):
    """Distribution statistics for a survey."""

    survey_id: UUID
    total: int
    by_status: dict[str, int]


# --- Endpoints ---


@router.post(
    "/api/admin/surveys/distribute",
    response_model=DistributionResponse,
    status_code=201,
)
async def create_distribution_endpoint(
    body: CreateDistributionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Send a survey to a single recipient."""
    try:
        return await create_distribution(
            db=db,
            survey_id=body.survey_id,
            channel=body.channel,
            sent_by=current_user.id,
            recipient_email=body.recipient_email,
            recipient_phone=body.recipient_phone,
        )
    except InvalidDistributionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.post(
    "/api/admin/surveys/distribute/bulk",
    response_model=list[DistributionResponse],
    status_code=201,
)
async def bulk_distribute_endpoint(
    body: BulkDistributionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[dict]:
    """Send a survey to multiple recipients."""
    try:
        recipients = [r.model_dump() for r in body.recipients]
        return await create_bulk_distribution(
            db=db,
            survey_id=body.survey_id,
            channel=body.channel,
            sent_by=current_user.id,
            recipients=recipients,
        )
    except InvalidDistributionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/admin/surveys/distributions",
    response_model=DistributionListResponse,
)
async def list_distributions_endpoint(
    survey_id: UUID | None = Query(default=None),
    channel: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """List survey distributions with optional filters."""
    return await list_distributions(
        db=db,
        survey_id=survey_id,
        channel=channel,
        status_filter=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/admin/surveys/distributions/{distribution_id}",
    response_model=DistributionResponse,
)
async def get_distribution_endpoint(
    distribution_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """Get a distribution record by ID."""
    try:
        return await get_distribution(db=db, distribution_id=distribution_id)
    except DistributionNotFoundError:
        raise HTTPException(status_code=404, detail="Distribution not found") from None


@router.put(
    "/api/admin/surveys/distributions/{distribution_id}/status",
    response_model=DistributionResponse,
)
async def update_status_endpoint(
    distribution_id: UUID,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Update the delivery status of a distribution."""
    try:
        return await update_delivery_status(
            db=db,
            distribution_id=distribution_id,
            new_status=body.status,
            failure_reason=body.failure_reason,
        )
    except DistributionNotFoundError:
        raise HTTPException(status_code=404, detail="Distribution not found") from None
    except InvalidDistributionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/admin/surveys/{survey_id}/distribution-stats",
    response_model=DistributionStatsResponse,
)
async def get_stats_endpoint(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """Get distribution statistics for a survey."""
    return await get_distribution_stats(db=db, survey_id=survey_id)
