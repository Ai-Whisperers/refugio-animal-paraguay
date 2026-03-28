"""API endpoints for adoption return/exchange management.

Provides endpoints to create, process, list, and analyze return requests.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_db
from src.services.return_management_service import (
    AdoptionNotFoundError,
    DuplicateReturnError,
    InvalidReturnError,
    ReturnNotFoundError,
    create_return_request,
    get_return_analytics,
    get_return_request,
    list_return_requests,
    process_return,
)

router = APIRouter(tags=["Return Management"])


# --- Schemas ---


class CreateReturnRequest(BaseModel):
    """Request body for creating a return request."""

    reason: str = Field(..., min_length=1, max_length=2000)
    animal_condition: str = Field(default="healthy", max_length=20)
    is_emergency: bool = False


class ProcessReturnRequest(BaseModel):
    """Request body for processing a return."""

    staff_notes: str | None = Field(None, max_length=2000)


class ReturnRequestResponse(BaseModel):
    """Response for a return request."""

    id: UUID
    adoption_request_id: UUID
    reason: str
    animal_condition: str
    is_emergency: bool
    status: str
    staff_notes: str | None = None
    requested_by: UUID | None = None
    requested_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReturnListItem(BaseModel):
    """Abbreviated return request for list views."""

    id: UUID
    adoption_request_id: UUID
    reason: str
    animal_condition: str
    is_emergency: bool
    status: str
    requested_at: datetime

    model_config = {"from_attributes": True}


class ReturnAnalyticsResponse(BaseModel):
    """Return analytics summary."""

    total_returns: int
    by_condition: dict[str, int]
    emergency_count: int
    emergency_pct: float

    model_config = {"from_attributes": True}


# --- Endpoints ---


@router.post(
    "/api/adoptions/{adoption_request_id}/return",
    response_model=ReturnRequestResponse,
    status_code=201,
)
async def create_return(
    adoption_request_id: UUID,
    body: CreateReturnRequest,
    db: AsyncSession = Depends(get_db),
    staff: object = Depends(require_staff),
) -> dict:
    """Create a return request for an adoption."""
    user_id = getattr(staff, "id", None)
    try:
        result = await create_return_request(
            db,
            adoption_request_id,
            reason=body.reason,
            animal_condition=body.animal_condition,
            is_emergency=body.is_emergency,
            requested_by=user_id,
        )
        await db.commit()
        return result
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None
    except InvalidReturnError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except DuplicateReturnError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post(
    "/api/admin/returns/{return_request_id}/process",
    response_model=ReturnRequestResponse,
)
async def process_return_endpoint(
    return_request_id: UUID,
    body: ProcessReturnRequest,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Process an approved return (update animal + adoption status)."""
    try:
        result = await process_return(db, return_request_id, staff_notes=body.staff_notes)
        await db.commit()
        return result
    except ReturnNotFoundError:
        raise HTTPException(status_code=404, detail="Return request not found") from None
    except InvalidReturnError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.get(
    "/api/admin/returns/{return_request_id}",
    response_model=ReturnRequestResponse,
)
async def get_return(
    return_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get a single return request by ID."""
    try:
        return await get_return_request(db, return_request_id)
    except ReturnNotFoundError:
        raise HTTPException(status_code=404, detail="Return request not found") from None


@router.get(
    "/api/admin/returns",
    response_model=list[ReturnListItem],
)
async def list_returns(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """List return requests with optional status filter."""
    return await list_return_requests(db, status_filter=status, limit=limit, offset=offset)


@router.get(
    "/api/admin/returns/analytics",
    response_model=ReturnAnalyticsResponse,
)
async def return_analytics(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get return analytics: by condition, emergency rate."""
    return await get_return_analytics(db)
