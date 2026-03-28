"""Smart matching endpoints for ranking animals against adopter profiles.

Endpoints:
    POST /api/adoption/match  -- find best-fit animals for adopter answers
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import limiter
from src.schemas.error import RESOURCE_RESPONSES
from src.services.smart_matching_service import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    find_matches,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/adoption",
    tags=["adoption-matching"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class MatchRequest(BaseModel):
    """Request body for smart matching."""

    answers: dict[str, dict]


class MatchedAnimalSchema(BaseModel):
    """A matched animal with score and explanations."""

    id: UUID
    name: str
    species: str
    breed: str | None = None
    birth_date: date | None = None
    photo_url: str | None = None
    match_score: int
    why_match: list[str]


class MatchResponse(BaseModel):
    """Smart matching response with ranked animals."""

    animals: list[MatchedAnimalSchema]
    total_count: int


# --- Endpoints ---


@router.post(
    "/match",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def match_animals(
    request: Request,
    body: MatchRequest,
    species: str | None = Query(default=None, description="Filter by species"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> MatchResponse:
    """Find and rank available animals against adopter answers.

    Accepts the same answer format as pre-qualification and returns
    the top matching animals sorted by match_score descending.
    Includes human-readable match explanations for each animal.
    """
    result = await find_matches(
        db=db,
        answers=body.answers,
        species=species,
        limit=limit,
        offset=offset,
    )

    return MatchResponse(
        animals=[
            MatchedAnimalSchema(
                id=UUID(a["id"]),
                name=a["name"],
                species=a["species"],
                breed=a["breed"],
                birth_date=date.fromisoformat(a["birth_date"]) if a["birth_date"] else None,
                photo_url=a["photo_url"],
                match_score=a["match_score"],
                why_match=a["why_match"],
            )
            for a in result["animals"]
        ],
        total_count=result["total_count"],
    )
