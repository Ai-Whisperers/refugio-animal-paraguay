"""API endpoints for driver reimbursements.

Authenticated endpoints for submitting and managing transport expense claims.
Admin endpoints for reviewing (approve/reject) and marking as paid.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.services.driver_reimbursement_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    InvalidReimbursementError,
    InvalidStatusTransitionError,
    ReimbursementNotFoundError,
    create_reimbursement,
    delete_reimbursement,
    get_reimbursement,
    list_reimbursements,
    mark_paid,
    review_reimbursement,
)

router = APIRouter(tags=["Driver Reimbursements"])


# --- Schemas ---


class CreateReimbursementRequest(BaseModel):
    """Request body for creating a reimbursement."""

    transport_request_id: UUID
    expense_type: str = "fuel"
    amount: float
    currency: str = "PYG"
    description: str | None = None
    receipt_url: str | None = None


class ReviewReimbursementRequest(BaseModel):
    """Request body for reviewing a reimbursement."""

    status: str
    rejection_reason: str | None = None


class ReimbursementResponse(BaseModel):
    """Reimbursement details."""

    id: UUID
    transport_request_id: UUID
    driver_id: UUID
    expense_type: str
    amount: float
    currency: str
    description: str | None = None
    receipt_url: str | None = None
    status: str
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReimbursementListResponse(BaseModel):
    """Paginated list of reimbursements."""

    reimbursements: list[ReimbursementResponse]
    total: int
    limit: int
    offset: int


# --- Endpoints ---


@router.post(
    "/api/reimbursements",
    response_model=ReimbursementResponse,
    status_code=201,
)
async def create_reimbursement_endpoint(
    body: CreateReimbursementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> dict:
    """Submit a reimbursement request for a transport."""
    try:
        return await create_reimbursement(
            db=db,
            transport_request_id=body.transport_request_id,
            driver_id=current_user.id,
            expense_type=body.expense_type,
            amount=body.amount,
            currency=body.currency,
            description=body.description,
            receipt_url=body.receipt_url,
        )
    except InvalidReimbursementError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/reimbursements",
    response_model=ReimbursementListResponse,
)
async def list_reimbursements_endpoint(
    driver_id: UUID | None = Query(default=None),
    transport_request_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(_get_current_user),
) -> dict:
    """List reimbursements with optional filters."""
    return await list_reimbursements(
        db=db,
        driver_id=driver_id,
        transport_request_id=transport_request_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/reimbursements/{reimbursement_id}",
    response_model=ReimbursementResponse,
)
async def get_reimbursement_endpoint(
    reimbursement_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(_get_current_user),
) -> dict:
    """Get a reimbursement by ID."""
    try:
        return await get_reimbursement(db=db, reimbursement_id=reimbursement_id)
    except ReimbursementNotFoundError:
        raise HTTPException(status_code=404, detail="Reimbursement not found") from None


@router.post(
    "/api/admin/reimbursements/{reimbursement_id}/review",
    response_model=ReimbursementResponse,
)
async def review_reimbursement_endpoint(
    reimbursement_id: UUID,
    body: ReviewReimbursementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Approve or reject a reimbursement (admin only)."""
    try:
        return await review_reimbursement(
            db=db,
            reimbursement_id=reimbursement_id,
            reviewer_id=current_user.id,
            new_status=body.status,
            rejection_reason=body.rejection_reason,
        )
    except ReimbursementNotFoundError:
        raise HTTPException(status_code=404, detail="Reimbursement not found") from None
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    except InvalidReimbursementError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.post(
    "/api/admin/reimbursements/{reimbursement_id}/pay",
    response_model=ReimbursementResponse,
)
async def mark_paid_endpoint(
    reimbursement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Mark an approved reimbursement as paid (admin only)."""
    try:
        return await mark_paid(
            db=db,
            reimbursement_id=reimbursement_id,
            reviewer_id=current_user.id,
        )
    except ReimbursementNotFoundError:
        raise HTTPException(status_code=404, detail="Reimbursement not found") from None
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@router.delete(
    "/api/reimbursements/{reimbursement_id}",
    status_code=204,
)
async def delete_reimbursement_endpoint(
    reimbursement_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(_get_current_user),
) -> None:
    """Delete a pending reimbursement."""
    try:
        await delete_reimbursement(db=db, reimbursement_id=reimbursement_id)
    except ReimbursementNotFoundError:
        raise HTTPException(status_code=404, detail="Reimbursement not found") from None
    except InvalidReimbursementError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
