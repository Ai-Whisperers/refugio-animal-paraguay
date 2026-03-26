"""GDPR data deletion API endpoints.

Manages data deletion requests for GDPR Article 17 (right to erasure).

Endpoints:
  POST   /gdpr/deletion-requests              -- create a deletion request
  GET    /gdpr/deletion-requests              -- list deletion requests
  GET    /gdpr/deletion-requests/{id}         -- get request status
  POST   /gdpr/deletion-requests/{id}/approve -- approve and execute
  POST   /gdpr/deletion-requests/{id}/deny    -- deny with reason
  POST   /gdpr/deletion-requests/{id}/cancel  -- cancel pending request
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.gdpr_deletion import (
    DeletionRequestCreate,
    DeletionRequestDenial,
    DeletionRequestListResponse,
    DeletionRequestResponse,
)
from src.services.gdpr_deletion_service import (
    approve_deletion_request,
    cancel_deletion_request,
    create_deletion_request,
    deny_deletion_request,
    get_deletion_request,
    list_deletion_requests,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.post(
    "/deletion-requests",
    response_model=DeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_deletion_request_endpoint(
    payload: DeletionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> DeletionRequestResponse:
    """Create a GDPR deletion request for a data subject."""
    deletion_req = await create_deletion_request(
        db=db,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        subject_email=payload.subject_email,
        reason=payload.reason,
        requested_by_user_id=current_user.id,
    )
    return DeletionRequestResponse.model_validate(deletion_req)


@router.get(
    "/deletion-requests",
    response_model=DeletionRequestListResponse,
)
async def list_deletion_requests_endpoint(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
    status_filter: str | None = Query(default=None, alias="status"),
) -> DeletionRequestListResponse:
    """List deletion requests with optional status filter."""
    requests = await list_deletion_requests(db, status_filter=status_filter)
    items = [DeletionRequestResponse.model_validate(r) for r in requests]
    return DeletionRequestListResponse(items=items, count=len(items))


@router.get(
    "/deletion-requests/{request_id}",
    response_model=DeletionRequestResponse,
)
async def get_deletion_request_endpoint(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DeletionRequestResponse:
    """Get a specific deletion request."""
    deletion_req = await get_deletion_request(db, request_id)
    if deletion_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found",
        )
    return DeletionRequestResponse.model_validate(deletion_req)


@router.post(
    "/deletion-requests/{request_id}/approve",
    response_model=DeletionRequestResponse,
)
async def approve_deletion_request_endpoint(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DeletionRequestResponse:
    """Approve and execute a pending deletion request. Admin only."""
    try:
        deletion_req = await approve_deletion_request(
            db=db,
            request_id=request_id,
            approved_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    if deletion_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found",
        )
    return DeletionRequestResponse.model_validate(deletion_req)


@router.post(
    "/deletion-requests/{request_id}/deny",
    response_model=DeletionRequestResponse,
)
async def deny_deletion_request_endpoint(
    request_id: UUID,
    payload: DeletionRequestDenial,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DeletionRequestResponse:
    """Deny a pending deletion request with optional reason. Admin only."""
    try:
        deletion_req = await deny_deletion_request(
            db=db,
            request_id=request_id,
            denied_by_user_id=current_user.id,
            denial_reason=payload.denial_reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    if deletion_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found",
        )
    return DeletionRequestResponse.model_validate(deletion_req)


@router.post(
    "/deletion-requests/{request_id}/cancel",
    response_model=DeletionRequestResponse,
)
async def cancel_deletion_request_endpoint(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DeletionRequestResponse:
    """Cancel a pending deletion request."""
    try:
        deletion_req = await cancel_deletion_request(db=db, request_id=request_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    if deletion_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deletion request {request_id} not found",
        )
    return DeletionRequestResponse.model_validate(deletion_req)
