"""Emergency case API endpoints.

Rescuers and staff can create emergency cases which auto-link to campaigns.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.emergency_service import (
    EmergencyError,
    EmergencyNotFoundError,
    InvalidDeadlineError,
    InvalidStatusTransitionError,
    create_emergency_case,
    get_emergency_case,
    list_active_emergencies,
    soft_delete_emergency,
    update_emergency_status,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EmergencyCreateRequest(BaseModel):
    """Request body for creating an emergency case."""

    title: str = Field(..., max_length=200)
    description: str
    animal_id: UUID | None = None
    photos: list[str] = Field(default_factory=list)
    amount_needed_cents: int = Field(..., gt=0)
    currency: str = "USD"
    urgency: str = "high"
    deadline: datetime


class EmergencyStatusUpdateRequest(BaseModel):
    """Request body for updating emergency status."""

    status: str


class EmergencyResponse(BaseModel):
    """Emergency case response."""

    id: UUID
    title: str
    description: str
    animal_id: UUID | None = None
    rescuer_id: UUID
    campaign_id: UUID | None = None
    photos: list = Field(default_factory=list)
    amount_needed_cents: int
    amount_raised_cents: int
    currency: str
    deadline: str
    status: str
    urgency: str
    is_deleted: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/emergencies",
    tags=["emergencies"],
    dependencies=[Depends(require_staff)],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_emergency(case: object) -> dict:
    """Convert an EmergencyCase ORM object to a response dict."""
    return {
        "id": case.id,  # type: ignore[attr-defined]
        "title": case.title,  # type: ignore[attr-defined]
        "description": case.description,  # type: ignore[attr-defined]
        "animal_id": case.animal_id,  # type: ignore[attr-defined]
        "rescuer_id": case.rescuer_id,  # type: ignore[attr-defined]
        "campaign_id": case.campaign_id,  # type: ignore[attr-defined]
        "photos": case.photos,  # type: ignore[attr-defined]
        "amount_needed_cents": case.amount_needed_cents,  # type: ignore[attr-defined]
        "amount_raised_cents": case.amount_raised_cents,  # type: ignore[attr-defined]
        "currency": case.currency,  # type: ignore[attr-defined]
        "deadline": case.deadline.isoformat(),  # type: ignore[attr-defined]
        "status": case.status,  # type: ignore[attr-defined]
        "urgency": case.urgency,  # type: ignore[attr-defined]
        "is_deleted": case.is_deleted,  # type: ignore[attr-defined]
        "created_at": case.created_at.isoformat(),  # type: ignore[attr-defined]
        "updated_at": case.updated_at.isoformat(),  # type: ignore[attr-defined]
    }


def _handle_emergency_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, EmergencyNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, InvalidDeadlineError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, InvalidStatusTransitionError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, EmergencyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=EmergencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_emergency(
    body: EmergencyCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    _user=Depends(require_staff),
) -> dict:
    """Create an emergency case with auto-linked campaign."""
    try:
        # For now, use a placeholder rescuer_id from the auth context.
        # In production, this comes from the authenticated user.
        rescuer_id = getattr(_user, "id", None)
        if rescuer_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User ID not available",
            )
        case = await create_emergency_case(
            title=body.title,
            description=body.description,
            rescuer_id=rescuer_id,
            amount_needed_cents=body.amount_needed_cents,
            deadline=body.deadline,
            animal_id=body.animal_id,
            photos=body.photos,
            currency=body.currency,
            urgency=body.urgency,
            db=db,
        )
        await db.commit()
        return _serialise_emergency(case)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_emergency_error(exc)
        raise


@router.get("/{emergency_id}", response_model=EmergencyResponse)
async def get_emergency(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get an emergency case by ID."""
    try:
        case = await get_emergency_case(emergency_id, db)
        return _serialise_emergency(case)
    except Exception as exc:
        _handle_emergency_error(exc)
        raise


@router.patch("/{emergency_id}/status", response_model=EmergencyResponse)
async def update_status(
    emergency_id: UUID,
    body: EmergencyStatusUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update the status of an emergency case."""
    try:
        case = await update_emergency_status(
            emergency_id=emergency_id,
            new_status=body.status,
            db=db,
        )
        await db.commit()
        return _serialise_emergency(case)
    except Exception as exc:
        _handle_emergency_error(exc)
        raise


@router.delete("/{emergency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emergency(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Soft-delete an emergency case."""
    try:
        await soft_delete_emergency(emergency_id=emergency_id, db=db)
        await db.commit()
    except Exception as exc:
        _handle_emergency_error(exc)
        raise


@router.get("", response_model=list[EmergencyResponse])
async def list_emergencies(
    urgency: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """List active emergency cases."""
    cases = await list_active_emergencies(db, urgency=urgency, limit=limit, offset=offset)
    return [_serialise_emergency(c) for c in cases]
