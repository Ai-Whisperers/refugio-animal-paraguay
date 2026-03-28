"""Partner veterinary clinic management API endpoints.

Endpoints:
  GET    /api/vet-clinics           - List clinics (staff/admin, with filters)
  POST   /api/vet-clinics           - Register a new clinic (staff/admin)
  GET    /api/vet-clinics/{id}      - Get clinic details (staff/admin)
  PATCH  /api/vet-clinics/{id}      - Update clinic fields (staff/admin)
  PATCH  /api/vet-clinics/{id}/status - Update clinic status (admin)
  DELETE /api/vet-clinics/{id}      - Delete pending/inactive clinic (admin)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.vet_clinic import (
    VetClinicCreate,
    VetClinicListResponse,
    VetClinicResponse,
    VetClinicStatusUpdate,
    VetClinicUpdate,
)
from src.services.vet_clinic_service import (
    ClinicNotFoundError,
    InvalidStatusTransitionError,
    create_clinic,
    delete_clinic,
    get_clinic,
    list_clinics,
    update_clinic,
    update_clinic_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vet-clinics",
    tags=["vet-clinics"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=VetClinicListResponse)
async def list_vet_clinics(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    city: str | None = Query(None, description="Filter by city (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetClinicListResponse:
    """List partner vet clinics with optional filters."""
    clinics, total = await list_clinics(
        db, status=status_filter, city=city, page=page, page_size=page_size
    )
    return VetClinicListResponse(
        items=[VetClinicResponse.model_validate(c) for c in clinics],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=VetClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_clinic(
    body: VetClinicCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetClinicResponse:
    """Register a new partner vet clinic (starts in 'pending' status)."""
    clinic = await create_clinic(db, body.model_dump())
    return VetClinicResponse.model_validate(clinic)


@router.get("/{clinic_id}", response_model=VetClinicResponse)
async def get_vet_clinic(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetClinicResponse:
    """Get details of a single vet clinic."""
    try:
        clinic = await get_clinic(db, clinic_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    return VetClinicResponse.model_validate(clinic)


@router.patch("/{clinic_id}", response_model=VetClinicResponse)
async def update_vet_clinic(
    clinic_id: UUID,
    body: VetClinicUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> VetClinicResponse:
    """Update fields of an existing vet clinic."""
    try:
        clinic = await update_clinic(
            db, clinic_id, body.model_dump(exclude_unset=True)
        )
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    return VetClinicResponse.model_validate(clinic)


@router.patch("/{clinic_id}/status", response_model=VetClinicResponse)
async def change_clinic_status(
    clinic_id: UUID,
    body: VetClinicStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> VetClinicResponse:
    """Change clinic status (admin only). Validates status transitions."""
    try:
        clinic = await update_clinic_status(db, clinic_id, body.status)
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc
    return VetClinicResponse.model_validate(clinic)


@router.delete("/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vet_clinic(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> None:
    """Delete a vet clinic (only pending/inactive clinics). Admin only."""
    try:
        await delete_clinic(db, clinic_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or inactive clinics can be deleted.",
        ) from exc
