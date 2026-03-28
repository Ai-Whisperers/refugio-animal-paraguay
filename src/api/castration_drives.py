"""Castration drive scheduling API endpoints.

Endpoints:
  POST   /api/castration/drives                       - Create drive (staff)
  GET    /api/castration/drives                       - List all drives (staff)
  GET    /api/castration/drives/{id}                  - Get drive detail (staff)
  PATCH  /api/castration/drives/{id}                  - Update drive (staff)
  DELETE /api/castration/drives/{id}                  - Delete drive (staff)
  GET    /public/castration-campaigns/{id}/drives     - Upcoming drives (public)
"""

import logging
from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.castration_drive import CastrationDrive
from src.db.models.user import User
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/castration/drives",
    tags=["castration-drives"],
)

public_router = APIRouter(
    prefix="/public/castration-campaigns",
    tags=["castration-drives-public"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_TITLE_LENGTH = 200
MAX_LOCATION_LENGTH = 300
MAX_ADDRESS_LENGTH = 500
MAX_PHONE_LENGTH = 30
MAX_CONTACT_NAME_LENGTH = 200
VALID_STATUSES = {"scheduled", "in_progress", "completed", "cancelled"}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DriveCreateRequest(BaseModel):
    """Request body for creating a castration drive."""

    campaign_id: UUID
    clinic_id: UUID | None = None
    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    description: str | None = None
    location_name: str = Field(..., max_length=MAX_LOCATION_LENGTH)
    location_address: str | None = Field(None, max_length=MAX_ADDRESS_LENGTH)
    drive_date: date
    start_time: time | None = None
    end_time: time | None = None
    max_capacity: int = Field(..., gt=0)
    notes: str | None = None
    contact_phone: str | None = Field(None, max_length=MAX_PHONE_LENGTH)
    contact_name: str | None = Field(None, max_length=MAX_CONTACT_NAME_LENGTH)


class DriveUpdateRequest(BaseModel):
    """Request body for updating a drive."""

    title: str | None = Field(None, max_length=MAX_TITLE_LENGTH)
    description: str | None = None
    location_name: str | None = Field(None, max_length=MAX_LOCATION_LENGTH)
    location_address: str | None = Field(None, max_length=MAX_ADDRESS_LENGTH)
    drive_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    max_capacity: int | None = Field(None, gt=0)
    status: str | None = Field(None, pattern="^(scheduled|in_progress|completed|cancelled)$")
    registered_count: int | None = Field(None, ge=0)
    completed_count: int | None = Field(None, ge=0)
    notes: str | None = None
    contact_phone: str | None = Field(None, max_length=MAX_PHONE_LENGTH)
    contact_name: str | None = Field(None, max_length=MAX_CONTACT_NAME_LENGTH)


class DriveResponse(BaseModel):
    """Full drive response for authenticated endpoints."""

    id: UUID
    campaign_id: UUID
    clinic_id: UUID | None
    title: str
    description: str | None
    location_name: str
    location_address: str | None
    drive_date: date
    start_time: time | None
    end_time: time | None
    max_capacity: int
    registered_count: int
    completed_count: int
    spots_available: int
    is_full: bool
    status: str
    notes: str | None
    contact_phone: str | None
    contact_name: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PublicDriveResponse(BaseModel):
    """Public-safe drive response."""

    id: UUID
    campaign_id: UUID
    title: str
    description: str | None
    location_name: str
    location_address: str | None
    drive_date: date
    start_time: time | None
    end_time: time | None
    max_capacity: int
    registered_count: int
    spots_available: int
    is_full: bool
    status: str
    contact_phone: str | None
    contact_name: str | None

    model_config = {"from_attributes": True}


class DriveListResponse(BaseModel):
    """Paginated drive list."""

    items: list[DriveResponse]
    total: int
    page: int
    page_size: int


class PublicDriveListResponse(BaseModel):
    """Public paginated drive list."""

    items: list[PublicDriveResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@admin_router.post(
    "",
    response_model=DriveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a castration drive",
)
async def create_drive(
    body: DriveCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DriveResponse:
    """Create a new castration drive event."""
    drive = CastrationDrive(
        campaign_id=body.campaign_id,
        clinic_id=body.clinic_id,
        title=body.title,
        description=body.description,
        location_name=body.location_name,
        location_address=body.location_address,
        drive_date=body.drive_date,
        start_time=body.start_time,
        end_time=body.end_time,
        max_capacity=body.max_capacity,
        notes=body.notes,
        contact_phone=body.contact_phone,
        contact_name=body.contact_name,
    )
    db.add(drive)
    await db.commit()
    await db.refresh(drive)
    logger.info(
        "Castration drive created",
        extra={"drive_id": str(drive.id), "campaign_id": str(body.campaign_id)},
    )
    return DriveResponse.model_validate(drive)


@admin_router.get(
    "",
    response_model=DriveListResponse,
    summary="List all drives (staff)",
)
async def list_drives(
    campaign_id: UUID | None = Query(None),
    drive_status: str | None = Query(
        None, alias="status", pattern="^(scheduled|in_progress|completed|cancelled)$"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DriveListResponse:
    """List castration drives with optional filters."""
    base = select(CastrationDrive)
    if campaign_id:
        base = base.where(CastrationDrive.campaign_id == campaign_id)
    if drive_status:
        base = base.where(CastrationDrive.status == drive_status)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(CastrationDrive.drive_date.asc()).offset(offset).limit(page_size)
    )
    drives = list(rows_result.scalars().all())

    return DriveListResponse(
        items=[DriveResponse.model_validate(d) for d in drives],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.get(
    "/{drive_id}",
    response_model=DriveResponse,
    summary="Get drive detail",
)
async def get_drive(
    drive_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DriveResponse:
    """Get a single castration drive by ID."""
    result = await db.execute(select(CastrationDrive).where(CastrationDrive.id == drive_id))
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found",
        )
    return DriveResponse.model_validate(drive)


@admin_router.patch(
    "/{drive_id}",
    response_model=DriveResponse,
    summary="Update a drive",
)
async def update_drive(
    drive_id: UUID,
    body: DriveUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DriveResponse:
    """Update castration drive details."""
    result = await db.execute(select(CastrationDrive).where(CastrationDrive.id == drive_id))
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drive, field, value)

    await db.commit()
    await db.refresh(drive)
    return DriveResponse.model_validate(drive)


@admin_router.delete(
    "/{drive_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drive",
)
async def delete_drive(
    drive_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    """Delete a castration drive."""
    result = await db.execute(select(CastrationDrive).where(CastrationDrive.id == drive_id))
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found",
        )
    await db.delete(drive)
    await db.commit()
    logger.info("Castration drive deleted", extra={"drive_id": str(drive_id)})


# ---------------------------------------------------------------------------
# Public endpoint
# ---------------------------------------------------------------------------


@public_router.get(
    "/{campaign_id}/drives",
    response_model=PublicDriveListResponse,
    summary="Upcoming drives for a campaign (public)",
)
async def public_campaign_drives(
    campaign_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    include_past: bool = Query(False, description="Include completed/past drives"),
    db: AsyncSession = Depends(get_db),
) -> PublicDriveListResponse:
    """Return scheduled drives for a campaign, upcoming first."""
    base = select(CastrationDrive).where(
        CastrationDrive.campaign_id == campaign_id,
        CastrationDrive.status != "cancelled",
    )
    if not include_past:
        today = date.today()
        base = base.where(CastrationDrive.drive_date >= today)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(CastrationDrive.drive_date.asc()).offset(offset).limit(page_size)
    )
    drives = list(rows_result.scalars().all())

    return PublicDriveListResponse(
        items=[PublicDriveResponse.model_validate(d) for d in drives],
        total=total,
        page=page,
        page_size=page_size,
    )
