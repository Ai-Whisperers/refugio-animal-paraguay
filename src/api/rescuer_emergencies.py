"""Rescuer emergency creation endpoint.

Allows verified rescuers to create emergency cases via the portal.
Staff/admin can also use this endpoint.

Endpoints:
  POST /api/portal/emergencies  -- create emergency (verified rescuer)
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_verified_rescuer
from src.db.models.user import User
from src.db.session import get_async_session
from src.services.emergency_service import (
    EmergencyError,
    InvalidDeadlineError,
    create_emergency_case,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_DEADLINE_HOURS = 24
MAX_DEADLINE_DAYS = 30
MAX_PHOTOS = 3
SUPPORTED_CURRENCIES = ("USD", "PYG")

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RescuerEmergencyCreateRequest(BaseModel):
    """Request body for a rescuer creating an emergency case."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    animal_id: UUID | None = None
    photos: list[str] = Field(default_factory=list)
    amount_needed_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD")
    deadline: datetime

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in SUPPORTED_CURRENCIES:
            msg = f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}"
            raise ValueError(msg)
        return v

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, v: list[str]) -> list[str]:
        return v[:MAX_PHOTOS]

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: datetime) -> datetime:
        now = datetime.now(UTC)
        min_deadline = now + timedelta(hours=MIN_DEADLINE_HOURS)
        max_deadline = now + timedelta(days=MAX_DEADLINE_DAYS)
        if v < min_deadline:
            msg = f"Deadline must be at least {MIN_DEADLINE_HOURS} hours from now"
            raise ValueError(msg)
        if v > max_deadline:
            msg = f"Deadline must be within {MAX_DEADLINE_DAYS} days"
            raise ValueError(msg)
        return v


class RescuerEmergencyResponse(BaseModel):
    """Response schema for a created emergency case."""

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
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/portal/emergencies",
    tags=["rescuer-emergencies"],
    dependencies=[Depends(require_verified_rescuer)],
)


def _serialise(case: object) -> dict:
    """Convert an EmergencyCase ORM object to a response dict."""
    return {
        "id": case.id,  # type: ignore[attr-defined]
        "title": case.title,  # type: ignore[attr-defined]
        "description": case.description,  # type: ignore[attr-defined]
        "animal_id": case.animal_id,  # type: ignore[attr-defined]
        "rescuer_id": case.rescuer_id,  # type: ignore[attr-defined]
        "campaign_id": case.campaign_id,  # type: ignore[attr-defined]
        "photos": case.photos or [],  # type: ignore[attr-defined]
        "amount_needed_cents": case.amount_needed_cents,  # type: ignore[attr-defined]
        "amount_raised_cents": case.amount_raised_cents,  # type: ignore[attr-defined]
        "currency": case.currency,  # type: ignore[attr-defined]
        "deadline": case.deadline.isoformat(),  # type: ignore[attr-defined]
        "status": case.status,  # type: ignore[attr-defined]
        "urgency": case.urgency,  # type: ignore[attr-defined]
        "created_at": case.created_at.isoformat(),  # type: ignore[attr-defined]
    }


@router.post(
    "",
    response_model=RescuerEmergencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an emergency case (rescuer portal)",
)
async def create_rescuer_emergency(
    body: RescuerEmergencyCreateRequest,
    user: User = Depends(require_verified_rescuer),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create an emergency case as a verified rescuer.

    Auto-publishes immediately for verified rescuers. The emergency
    case is linked to the authenticated user as rescuer_id.
    """
    try:
        case = await create_emergency_case(
            title=body.title,
            description=body.description,
            rescuer_id=user.id,
            amount_needed_cents=body.amount_needed_cents,
            deadline=body.deadline,
            animal_id=body.animal_id,
            photos=body.photos[:MAX_PHOTOS],
            currency=body.currency,
            urgency="high",
            db=db,
        )
        await db.commit()
        logger.info(
            "Rescuer %s created emergency case %s",
            user.id,
            case.id,  # type: ignore[attr-defined]
        )
        return _serialise(case)
    except InvalidDeadlineError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    except EmergencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
