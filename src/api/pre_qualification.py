"""Pre-qualification endpoints for adoption screening.

Endpoints:
    POST /api/adoption/pre-qualify  -- score adopter answers against animal requirements
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import limiter
from src.schemas.error import RESOURCE_RESPONSES
from src.services.anti_gaming_service import AntiGamingError, check_rate_limits
from src.services.pre_qualification_service import (
    AnimalNotFoundError,
    PreQualificationResult,
    pre_qualify_adopter,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/adoption",
    tags=["adoption-pre-qualify"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class PreQualifyRequest(BaseModel):
    """Request body for pre-qualification scoring."""

    animal_id: UUID
    answers: dict[str, dict]


class FailedRequirementSchema(BaseModel):
    """A requirement the adopter did not meet."""

    requirement_type: str
    message: str
    is_mandatory: bool


class SuggestedAnimalSchema(BaseModel):
    """An animal that matches the adopter's profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    species: str
    photo_url: str | None = None
    match_score: int


class PreQualifyResponse(BaseModel):
    """Full pre-qualification result."""

    qualified: bool
    score: int
    failed_requirements: list[FailedRequirementSchema]
    suggested_animals: list[SuggestedAnimalSchema]
    estimated_wait_time: str


# --- Endpoints ---


@router.post(
    "/pre-qualify",
    response_model=PreQualifyResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("1/day")
async def pre_qualify(
    request: Request,
    body: PreQualifyRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> PreQualifyResponse:
    """Score adopter answers against an animal's requirements.

    Returns qualification status, score (0-100), failed requirements,
    suggested alternative animals, and estimated wait time.
    """
    # Anti-gaming check before processing
    try:
        await check_rate_limits(db, user_id=_current_user.id, animal_id=body.animal_id)
    except AntiGamingError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.message,
            headers=(
                {"Retry-After": str(exc.retry_after_seconds)} if exc.retry_after_seconds else None
            ),
        ) from None

    try:
        result: PreQualificationResult = await pre_qualify_adopter(db, body.animal_id, body.answers)
    except AnimalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {body.animal_id} not found or not available for adoption.",
        ) from None

    return PreQualifyResponse(
        qualified=result.qualified,
        score=result.score,
        failed_requirements=[
            FailedRequirementSchema(
                requirement_type=f.requirement_type,
                message=f.message,
                is_mandatory=f.is_mandatory,
            )
            for f in result.failed_requirements
        ],
        suggested_animals=[
            SuggestedAnimalSchema(
                id=a.id,
                name=a.name,
                species=a.species,
                photo_url=a.photo_url,
                match_score=a.match_score,
            )
            for a in result.suggested_animals
        ],
        estimated_wait_time=result.estimated_wait_time,
    )
