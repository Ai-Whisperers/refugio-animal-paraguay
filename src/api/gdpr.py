"""GDPR data export API endpoints.

Manages data export requests for GDPR Article 15 (right of access)
and Article 20 (right to data portability).

Endpoints:
  POST   /gdpr/data-export              -- request a new data export
  GET    /gdpr/data-export              -- list export requests
  GET    /gdpr/data-export/{id}         -- get export request status
  GET    /gdpr/data-export/{id}/download -- download export data
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.data_export import DataExportStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.gdpr_export import (
    DataExportCreateRequest,
    DataExportDownloadResponse,
    DataExportListResponse,
    DataExportResponse,
)
from src.services.gdpr_export_service import (
    create_export_request,
    get_export_request,
    list_export_requests,
    mark_downloaded,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.post(
    "/data-export",
    response_model=DataExportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_data_export_endpoint(
    payload: DataExportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DataExportResponse:
    """Request a GDPR data export for a data subject."""
    export_req = await create_export_request(
        db=db,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        subject_email=payload.subject_email,
        requested_by_user_id=current_user.id,
    )
    return DataExportResponse.model_validate(export_req)


@router.get(
    "/data-export",
    response_model=DataExportListResponse,
)
async def list_data_exports_endpoint(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DataExportListResponse:
    """List all data export requests."""
    exports = await list_export_requests(db)
    items = [DataExportResponse.model_validate(e) for e in exports]
    return DataExportListResponse(items=items, count=len(items))


@router.get(
    "/data-export/{export_id}",
    response_model=DataExportResponse,
)
async def get_data_export_endpoint(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DataExportResponse:
    """Get status of a specific data export request."""
    export_req = await get_export_request(db, export_id)
    if export_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export request {export_id} not found",
        )
    return DataExportResponse.model_validate(export_req)


@router.get(
    "/data-export/{export_id}/download",
    response_model=DataExportDownloadResponse,
)
async def download_data_export_endpoint(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DataExportDownloadResponse:
    """Download the exported data for a completed export request.

    Marks the export as downloaded (tracks access for audit purposes).
    Returns 404 if not found, 409 if not yet completed or expired.
    """
    export_req = await get_export_request(db, export_id)
    if export_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export request {export_id} not found",
        )

    if export_req.status == DataExportStatus.EXPIRED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Export has expired — please request a new export",
        )

    if export_req.status != DataExportStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export is not ready — current status: {export_req.status}",
        )

    # Track download access
    export_req = await mark_downloaded(db, export_req)

    return DataExportDownloadResponse.model_validate(export_req)
