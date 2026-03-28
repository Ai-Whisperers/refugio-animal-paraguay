"""API endpoints for automated monthly impact emails.

Admin endpoints for managing donor impact email campaigns.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.impact_email_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DuplicateEmailError,
    EmailLogNotFoundError,
    InvalidEmailError,
    create_email_log,
    get_campaign_stats,
    get_email_log,
    increment_retry,
    list_email_logs,
    update_email_status,
)

router = APIRouter(tags=["Impact Emails"])


# --- Schemas ---


class CreateEmailLogRequest(BaseModel):
    """Request body for creating an impact email log."""

    donor_id: UUID
    email_address: str
    subject: str
    report_month: int
    report_year: int
    donation_total: float
    currency: str = "PYG"
    animals_rescued: int = 0
    animals_adopted: int = 0
    castrations_funded: int = 0
    medical_treatments: int = 0


class UpdateStatusRequest(BaseModel):
    """Request body for updating email status."""

    status: str
    failure_reason: str | None = None


class EmailLogResponse(BaseModel):
    """Impact email log details."""

    id: UUID
    donor_id: UUID
    email_address: str
    subject: str
    report_month: int
    report_year: int
    donation_total: float
    currency: str
    animals_rescued: int
    animals_adopted: int
    castrations_funded: int
    medical_treatments: int
    status: str
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    failure_reason: str | None = None
    retry_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailLogListResponse(BaseModel):
    """Paginated list of email logs."""

    email_logs: list[EmailLogResponse]
    total: int
    limit: int
    offset: int


class CampaignStatsResponse(BaseModel):
    """Campaign statistics for a report period."""

    report_year: int
    report_month: int
    total: int
    by_status: dict[str, int]


# --- Endpoints ---


@router.post(
    "/api/admin/impact-emails",
    response_model=EmailLogResponse,
    status_code=201,
)
async def create_email_log_endpoint(
    body: CreateEmailLogRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Create an impact email log entry."""
    try:
        return await create_email_log(
            db=db,
            donor_id=body.donor_id,
            email_address=body.email_address,
            subject=body.subject,
            report_month=body.report_month,
            report_year=body.report_year,
            donation_total=body.donation_total,
            currency=body.currency,
            animals_rescued=body.animals_rescued,
            animals_adopted=body.animals_adopted,
            castrations_funded=body.castrations_funded,
            medical_treatments=body.medical_treatments,
        )
    except InvalidEmailError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@router.get(
    "/api/admin/impact-emails",
    response_model=EmailLogListResponse,
)
async def list_email_logs_endpoint(
    donor_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    report_year: int | None = Query(default=None),
    report_month: int | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """List impact email logs with optional filters."""
    return await list_email_logs(
        db=db,
        donor_id=donor_id,
        status_filter=status,
        report_year=report_year,
        report_month=report_month,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/admin/impact-emails/{log_id}",
    response_model=EmailLogResponse,
)
async def get_email_log_endpoint(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """Get an impact email log by ID."""
    try:
        return await get_email_log(db=db, log_id=log_id)
    except EmailLogNotFoundError:
        raise HTTPException(status_code=404, detail="Email log not found") from None


@router.put(
    "/api/admin/impact-emails/{log_id}/status",
    response_model=EmailLogResponse,
)
async def update_status_endpoint(
    log_id: UUID,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Update the delivery status of an impact email."""
    try:
        return await update_email_status(
            db=db,
            log_id=log_id,
            new_status=body.status,
            failure_reason=body.failure_reason,
        )
    except EmailLogNotFoundError:
        raise HTTPException(status_code=404, detail="Email log not found") from None
    except InvalidEmailError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.post(
    "/api/admin/impact-emails/{log_id}/retry",
    response_model=EmailLogResponse,
)
async def retry_email_endpoint(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Retry a failed impact email (increments retry count, resets to pending)."""
    try:
        return await increment_retry(db=db, log_id=log_id)
    except EmailLogNotFoundError:
        raise HTTPException(status_code=404, detail="Email log not found") from None
    except InvalidEmailError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/admin/impact-emails/campaigns/{report_year}/{report_month}",
    response_model=CampaignStatsResponse,
)
async def get_campaign_stats_endpoint(
    report_year: int,
    report_month: int,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """Get campaign statistics for a specific month."""
    return await get_campaign_stats(
        db=db,
        report_year=report_year,
        report_month=report_month,
    )
