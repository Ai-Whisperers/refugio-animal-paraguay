"""Castration photo gallery API endpoints.

Endpoints:
  POST /api/castration-photos                          - Upload photo (staff/vet)
  GET  /public/castration-campaigns/{id}/gallery       - Public gallery
  GET  /api/castration-campaigns/{id}/photos           - Admin photo list
  PATCH /api/castration-photos/{id}                    - Update photo metadata (staff)
  DELETE /api/castration-photos/{id}                   - Delete photo (staff)
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.castration_photo import CastrationPhoto
from src.db.models.user import User
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/castration",
    tags=["castration-photos"],
)

public_router = APIRouter(
    prefix="/public/castration-campaigns",
    tags=["castration-photos-public"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

VALID_PHOTO_TYPES = {"before", "after", "recovery"}

MAX_PHOTO_URL_LENGTH = 500
MAX_ANIMAL_NAME_LENGTH = 200
MAX_SPECIES_LENGTH = 50


class PhotoUploadRequest(BaseModel):
    """Request body for uploading a castration photo."""

    vet_voucher_id: UUID
    campaign_id: UUID
    photo_url: str = Field(..., max_length=MAX_PHOTO_URL_LENGTH)
    photo_type: str = Field(..., pattern="^(before|after|recovery)$")
    animal_name: str = Field(..., max_length=MAX_ANIMAL_NAME_LENGTH)
    animal_species: str | None = Field(None, max_length=MAX_SPECIES_LENGTH)
    notes: str | None = None
    public_consent: bool = False
    uploaded_by_clinic_id: UUID | None = None


class PhotoUpdateRequest(BaseModel):
    """Request body for updating photo metadata."""

    notes: str | None = None
    public_consent: bool | None = None
    is_featured: bool | None = None
    animal_name: str | None = Field(None, max_length=MAX_ANIMAL_NAME_LENGTH)


class PhotoResponse(BaseModel):
    """Full photo response for authenticated endpoints."""

    id: UUID
    vet_voucher_id: UUID
    campaign_id: UUID
    photo_url: str
    photo_type: str
    animal_name: str
    animal_species: str | None
    notes: str | None
    public_consent: bool
    is_featured: bool
    uploaded_by_clinic_id: UUID | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PublicPhotoResponse(BaseModel):
    """Public-safe photo response (only consent=True photos)."""

    id: UUID
    photo_url: str
    photo_type: str
    animal_name: str
    animal_species: str | None
    is_featured: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PhotoListResponse(BaseModel):
    """Paginated photo list."""

    items: list[PhotoResponse]
    total: int
    page: int
    page_size: int


class PublicGalleryResponse(BaseModel):
    """Public gallery response with featured photos first."""

    items: list[PublicPhotoResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Admin / Staff endpoints
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@admin_router.post(
    "/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a castration photo",
)
async def upload_photo(
    body: PhotoUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PhotoResponse:
    """Upload a before/after/recovery photo for a castration voucher redemption."""
    photo = CastrationPhoto(
        vet_voucher_id=body.vet_voucher_id,
        campaign_id=body.campaign_id,
        photo_url=body.photo_url,
        photo_type=body.photo_type,
        animal_name=body.animal_name,
        animal_species=body.animal_species,
        notes=body.notes,
        public_consent=body.public_consent,
        uploaded_by_clinic_id=body.uploaded_by_clinic_id,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    logger.info(
        "Castration photo uploaded",
        extra={"photo_id": str(photo.id), "campaign_id": str(body.campaign_id)},
    )
    return PhotoResponse.model_validate(photo)


@admin_router.get(
    "/campaigns/{campaign_id}/photos",
    response_model=PhotoListResponse,
    summary="List all photos for a campaign (staff)",
)
async def list_campaign_photos(
    campaign_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    photo_type: str | None = Query(None, pattern="^(before|after|recovery)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PhotoListResponse:
    """List all photos for a campaign with optional type filter."""
    base = select(CastrationPhoto).where(CastrationPhoto.campaign_id == campaign_id)
    if photo_type:
        base = base.where(CastrationPhoto.photo_type == photo_type)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(CastrationPhoto.uploaded_at.desc()).offset(offset).limit(page_size)
    )
    photos = list(rows_result.scalars().all())

    return PhotoListResponse(
        items=[PhotoResponse.model_validate(p) for p in photos],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.patch(
    "/photos/{photo_id}",
    response_model=PhotoResponse,
    summary="Update photo metadata",
)
async def update_photo(
    photo_id: UUID,
    body: PhotoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PhotoResponse:
    """Update notes, consent, featured status, or animal name on a photo."""
    result = await db.execute(select(CastrationPhoto).where(CastrationPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo {photo_id} not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(photo, field, value)

    await db.commit()
    await db.refresh(photo)
    return PhotoResponse.model_validate(photo)


@admin_router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo",
)
async def delete_photo(
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    """Delete a castration photo."""
    result = await db.execute(select(CastrationPhoto).where(CastrationPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo {photo_id} not found",
        )
    await db.delete(photo)
    await db.commit()
    logger.info("Castration photo deleted", extra={"photo_id": str(photo_id)})


# ---------------------------------------------------------------------------
# Public gallery endpoint
# ---------------------------------------------------------------------------


@public_router.get(
    "/{campaign_id}/gallery",
    response_model=PublicGalleryResponse,
    summary="Public photo gallery for a castration campaign",
)
async def public_gallery(
    campaign_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    photo_type: str | None = Query(None, pattern="^(before|after|recovery)$"),
    db: AsyncSession = Depends(get_db),
) -> PublicGalleryResponse:
    """Return consented photos for a campaign, featured first."""
    base = select(CastrationPhoto).where(
        CastrationPhoto.campaign_id == campaign_id,
        CastrationPhoto.public_consent.is_(True),
    )
    if photo_type:
        base = base.where(CastrationPhoto.photo_type == photo_type)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(
            CastrationPhoto.is_featured.desc(),
            CastrationPhoto.uploaded_at.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )
    photos = list(rows_result.scalars().all())

    return PublicGalleryResponse(
        items=[PublicPhotoResponse.model_validate(p) for p in photos],
        total=total,
        page=page,
        page_size=page_size,
    )
