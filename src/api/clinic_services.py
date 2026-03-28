"""Clinic service catalog API endpoints.

Endpoints (nested under vet-clinics):
  GET    /api/vet-clinics/{clinic_id}/services           - List services
  POST   /api/vet-clinics/{clinic_id}/services           - Create service (staff/admin)
  GET    /api/vet-clinics/{clinic_id}/services/{id}      - Get service detail
  PATCH  /api/vet-clinics/{clinic_id}/services/{id}      - Update service (staff/admin)
  DELETE /api/vet-clinics/{clinic_id}/services/{id}      - Delete service (admin)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.clinic_service import (
    ClinicServiceCreate,
    ClinicServiceListResponse,
    ClinicServiceResponse,
    ClinicServiceUpdate,
)
from src.schemas.error import COMMON_RESPONSES
from src.services.clinic_service_catalog import (
    ClinicNotFoundError,
    ClinicServiceNotFoundError,
    create_service,
    delete_service,
    get_service,
    list_services,
    update_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vet-clinics/{clinic_id}/services",
    tags=["clinic-services"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=ClinicServiceListResponse)
async def list_clinic_services(
    clinic_id: UUID,
    category: str | None = Query(None, description="Filter by service category"),
    active_only: bool = Query(False, description="Only show active services"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ClinicServiceListResponse:
    """List services offered by a clinic."""
    try:
        services, total = await list_services(
            db,
            clinic_id,
            category=category,
            active_only=active_only,
            page=page,
            page_size=page_size,
        )
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc

    return ClinicServiceListResponse(
        items=[ClinicServiceResponse.model_validate(s) for s in services],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ClinicServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic_service(
    clinic_id: UUID,
    body: ClinicServiceCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ClinicServiceResponse:
    """Add a new service to a clinic's catalog."""
    try:
        service = await create_service(db, clinic_id, body.model_dump())
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ClinicServiceResponse.model_validate(service)


@router.get("/{service_id}", response_model=ClinicServiceResponse)
async def get_clinic_service(
    clinic_id: UUID,
    service_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ClinicServiceResponse:
    """Get details of a single clinic service."""
    try:
        service = await get_service(db, clinic_id, service_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ClinicServiceResponse.model_validate(service)


@router.patch("/{service_id}", response_model=ClinicServiceResponse)
async def update_clinic_service(
    clinic_id: UUID,
    service_id: UUID,
    body: ClinicServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ClinicServiceResponse:
    """Update fields of an existing clinic service."""
    try:
        service = await update_service(
            db, clinic_id, service_id, body.model_dump(exclude_unset=True)
        )
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ClinicServiceResponse.model_validate(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinic_service(
    clinic_id: UUID,
    service_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> None:
    """Delete a service from a clinic's catalog. Admin only."""
    try:
        await delete_service(db, clinic_id, service_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
