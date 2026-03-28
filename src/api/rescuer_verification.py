"""Rescuer verification endpoints — submit, review, and list verification requests.

Endpoints:
  POST /api/rescuers/verification         -- submit verification request (authenticated rescuer)
  GET  /api/rescuers/verification/mine     -- list own verification requests (authenticated rescuer)
  GET  /api/rescuers/verification/pending  -- list pending requests (staff only)
  GET  /api/rescuers/verification/{id}     -- get single request (staff only)
  POST /api/rescuers/verification/{id}/review -- approve/reject (staff only)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.rescuer_verification_service import (
    AlreadyVerifiedError,
    InvalidReviewTransitionError,
    RescuerNotFoundError,
    TooManyPendingRequestsError,
    VerificationError,
    VerificationNotFoundError,
    get_my_verification_requests,
    get_verification_request,
    list_pending_requests,
    review_verification_request,
    submit_verification_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuers/verification",
    tags=["rescuer-verification"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VerificationSubmitRequest(BaseModel):
    """Request body for submitting a verification request."""

    method: str = Field(
        ...,
        description="Verification method: whatsapp, social, or manual",
        max_length=20,
    )
    evidence_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to evidence (social profile, document, etc.)",
    )
    evidence_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional notes or explanation",
    )


class VerificationReviewRequest(BaseModel):
    """Request body for reviewing a verification request."""

    approved: bool = Field(..., description="True to approve, False to reject")
    reviewer_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Notes from the reviewer",
    )


class VerificationRequestResponse(BaseModel):
    """Response schema for a verification request."""

    id: UUID
    rescuer_profile_id: UUID
    method: str
    status: str
    evidence_url: str | None
    evidence_notes: str | None
    reviewer_user_id: UUID | None
    reviewer_notes: str | None
    reviewed_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=VerificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit verification request",
    description="Submit a verification request for the authenticated rescuer.",
)
async def submit_verification_endpoint(
    body: VerificationSubmitRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VerificationRequestResponse:
    """Submit a new verification request."""
    try:
        request = await submit_verification_request(
            user_id=current_user.id,
            method=body.method,
            evidence_url=body.evidence_url,
            evidence_notes=body.evidence_notes,
            db=db,
        )
    except RescuerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile. Register first.",
            },
        ) from None
    except AlreadyVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": "Your profile is already verified.",
            },
        ) from None
    except TooManyPendingRequestsError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()
    return VerificationRequestResponse.model_validate(request)


@router.get(
    "/mine",
    response_model=list[VerificationRequestResponse],
    summary="List my verification requests",
    description="Get all verification requests for the authenticated rescuer.",
)
async def list_my_verifications_endpoint(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VerificationRequestResponse]:
    """List the current user's verification requests."""
    try:
        requests = await get_my_verification_requests(current_user.id, db)
    except RescuerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile.",
            },
        ) from None

    return [VerificationRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/pending",
    response_model=list[VerificationRequestResponse],
    summary="List pending verification requests",
    description="List all pending verification requests (staff only).",
)
async def list_pending_endpoint(
    limit: int = 50,
    offset: int = 0,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[VerificationRequestResponse]:
    """List pending verification requests for admin review."""
    requests = await list_pending_requests(db, limit=limit, offset=offset)
    return [VerificationRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/{request_id}",
    response_model=VerificationRequestResponse,
    summary="Get verification request",
    description="Get a single verification request by ID (staff only).",
)
async def get_verification_endpoint(
    request_id: UUID,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> VerificationRequestResponse:
    """Get a single verification request."""
    try:
        request = await get_verification_request(request_id, db)
    except VerificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Verification request not found"},
        ) from None

    return VerificationRequestResponse.model_validate(request)


@router.post(
    "/{request_id}/review",
    response_model=VerificationRequestResponse,
    summary="Review verification request",
    description="Approve or reject a pending verification request (staff only).",
)
async def review_verification_endpoint(
    request_id: UUID,
    body: VerificationReviewRequest,
    staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> VerificationRequestResponse:
    """Approve or reject a verification request."""
    try:
        request = await review_verification_request(
            request_id=request_id,
            reviewer_user_id=staff_user.id,
            approved=body.approved,
            reviewer_notes=body.reviewer_notes,
            db=db,
        )
    except VerificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Verification request not found"},
        ) from None
    except InvalidReviewTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()
    return VerificationRequestResponse.model_validate(request)
