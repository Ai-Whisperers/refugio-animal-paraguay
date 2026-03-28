"""Public homepage dynamic content — team members and testimonials from CMS.

Endpoints:
  GET /api/public/content/homepage/team          — team member list
  GET /api/public/content/homepage/testimonials   — testimonial list

These endpoints read published CMS content with specific slugs and parse the
structured JSON stored in the body field.  When no matching CMS entry exists
the response is an empty list, allowing the frontend to fall back gracefully.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.cms_content import CMSContent, ContentStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/public/content/homepage",
    tags=["homepage-content"],
)

# Cache-Control header value — 5 minutes public cache
CACHE_MAX_AGE_SECONDS = 300

# Slug conventions for homepage blocks stored in the CMS
TEAM_SLUG = "homepage-team"
TESTIMONIALS_SLUG = "homepage-testimonials"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TeamMemberResponse(BaseModel):
    """A single team member entry."""

    name: str = Field(..., description="Display name")
    role: str = Field(..., description="Role / title")
    image_url: str | None = Field(None, description="Optional avatar URL")


class TestimonialResponse(BaseModel):
    """A single testimonial entry."""

    quote: str = Field(..., description="Testimonial quote text")
    name: str = Field(..., description="Author display name")
    animal: str = Field(..., description="Animal name and species")


class TeamListResponse(BaseModel):
    """List of team members."""

    items: list[TeamMemberResponse]
    source: str = Field("cms", description="'cms' when loaded from DB, 'default' for fallback")


class TestimonialListResponse(BaseModel):
    """List of testimonials."""

    items: list[TestimonialResponse]
    source: str = Field("cms", description="'cms' when loaded from DB, 'default' for fallback")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fetch_homepage_block(slug: str, language: str, db: AsyncSession) -> list[dict[str, Any]]:
    """Fetch a published CMS entry by slug and parse its body as JSON array.

    Returns an empty list when the entry does not exist or parsing fails.
    """
    stmt = (
        select(CMSContent)
        .where(
            CMSContent.slug == slug,
            CMSContent.status == ContentStatus.PUBLISHED,
            CMSContent.language == language,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        return []

    try:
        parsed = json.loads(entry.body)
        if isinstance(parsed, list):
            return parsed
        logger.warning(
            "CMS entry '%s' body is not a JSON array — returning empty list",
            slug,
        )
        return []
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse CMS entry '%s' body as JSON: %s", slug, exc)
        return []


def _cache_response(data: BaseModel) -> JSONResponse:
    """Wrap a Pydantic model in a JSONResponse with Cache-Control header."""
    return JSONResponse(
        content=data.model_dump(),
        headers={"Cache-Control": f"public, max-age={CACHE_MAX_AGE_SECONDS}"},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/team",
    response_model=TeamListResponse,
    summary="Get homepage team members",
    description=(
        "Returns the team member list for the homepage. "
        "Data is sourced from a published CMS entry with slug 'homepage-team'. "
        "Returns an empty list when no entry exists (frontend should fall back)."
    ),
)
async def get_homepage_team(
    lang: str = "es",
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return team members from CMS or empty list."""
    raw = await _fetch_homepage_block(TEAM_SLUG, lang, db)
    items = [TeamMemberResponse(**item) for item in raw if isinstance(item, dict)]
    return _cache_response(TeamListResponse(items=items, source="cms" if items else "default"))


@router.get(
    "/testimonials",
    response_model=TestimonialListResponse,
    summary="Get homepage testimonials",
    description=(
        "Returns the testimonial list for the homepage. "
        "Data is sourced from a published CMS entry with slug 'homepage-testimonials'. "
        "Returns an empty list when no entry exists (frontend should fall back)."
    ),
)
async def get_homepage_testimonials(
    lang: str = "es",
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return testimonials from CMS or empty list."""
    raw = await _fetch_homepage_block(TESTIMONIALS_SLUG, lang, db)
    items = [TestimonialResponse(**item) for item in raw if isinstance(item, dict)]
    return _cache_response(
        TestimonialListResponse(items=items, source="cms" if items else "default")
    )
