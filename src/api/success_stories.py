"""Success stories CRUD endpoints.

Admin endpoints:
  POST   /api/admin/stories          -- create story
  GET    /api/admin/stories          -- list all stories (inc. unpublished)
  PUT    /api/admin/stories/{id}     -- update story
  DELETE /api/admin/stories/{id}     -- soft delete story

Public endpoints:
  GET  /api/stories          -- published stories, featured first
  GET  /api/stories/{id}     -- single story detail
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.success_story import SuccessStory
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

PUBLIC_PAGE_SIZE = 6
ADMIN_PAGE_SIZE = 20


class SuccessStoryCreateRequest(BaseModel):
    """Payload for creating a success story."""

    title: str = Field(..., min_length=1, max_length=200)
    animal_id: UUID | None = None
    adopter_name: str = Field(..., min_length=1, max_length=200)
    story_text: str = Field(..., min_length=10)
    quote: str | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    is_featured: bool = False
    publish: bool = False


class SuccessStoryUpdateRequest(BaseModel):
    """Payload for updating a success story."""

    title: str | None = Field(default=None, max_length=200)
    animal_id: UUID | None = None
    adopter_name: str | None = Field(default=None, max_length=200)
    story_text: str | None = None
    quote: str | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    is_featured: bool | None = None
    publish: bool | None = None


class SuccessStoryResponse(BaseModel):
    """Success story response."""

    id: UUID
    title: str
    animal_id: UUID | None = None
    adopter_name: str
    story_text: str
    quote: str | None = None
    photo_url: str | None = None
    published_at: str | None = None
    is_featured: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SuccessStoryListResponse(BaseModel):
    """Paginated list of success stories."""

    items: list[SuccessStoryResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise(s: SuccessStory) -> dict:
    """Convert story to response dict."""
    return {
        "id": s.id,
        "title": s.title,
        "animal_id": s.animal_id,
        "adopter_name": s.adopter_name,
        "story_text": s.story_text,
        "quote": s.quote,
        "photo_url": s.photo_url,
        "published_at": s.published_at.isoformat() if s.published_at else None,
        "is_featured": s.is_featured,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Admin Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/stories",
    tags=["admin-stories"],
    dependencies=[Depends(require_staff)],
)


@admin_router.post(
    "",
    response_model=SuccessStoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a success story",
)
async def create_story(
    payload: SuccessStoryCreateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a new adoption success story."""
    story = SuccessStory(
        title=payload.title,
        animal_id=payload.animal_id,
        adopter_name=payload.adopter_name,
        story_text=payload.story_text,
        quote=payload.quote,
        photo_url=payload.photo_url,
        is_featured=payload.is_featured,
        published_at=datetime.now(UTC) if payload.publish else None,
    )
    db.add(story)
    await db.flush()
    await db.refresh(story)
    return _serialise(story)


@admin_router.get(
    "",
    response_model=SuccessStoryListResponse,
    summary="List all stories (admin)",
)
async def list_stories_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(ADMIN_PAGE_SIZE, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """List all stories including unpublished, sorted by created_at DESC."""
    base_where = [SuccessStory.is_deleted.is_(False)]
    offset = (page - 1) * page_size

    count_stmt = select(func.count()).select_from(SuccessStory).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(SuccessStory)
        .where(*base_where)
        .order_by(SuccessStory.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    result = await db.execute(stmt)
    stories = list(result.scalars().all())

    return {
        "items": [_serialise(s) for s in stories],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.put(
    "/{story_id}",
    response_model=SuccessStoryResponse,
    summary="Update a success story",
)
async def update_story(
    story_id: UUID,
    payload: SuccessStoryUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update an existing success story."""
    story = await db.get(SuccessStory, story_id)
    if story is None or story.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Story not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Handle publish toggle
    if "publish" in update_data:
        if update_data.pop("publish"):
            if story.published_at is None:
                story.published_at = datetime.now(UTC)
        else:
            story.published_at = None

    for field, value in update_data.items():
        setattr(story, field, value)

    await db.flush()
    await db.refresh(story)
    return _serialise(story)


@admin_router.delete(
    "/{story_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a success story",
)
async def delete_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Soft delete a success story."""
    story = await db.get(SuccessStory, story_id)
    if story is None or story.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Story not found"},
        )
    story.is_deleted = True
    await db.flush()


# ---------------------------------------------------------------------------
# Public Router
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/stories",
    tags=["stories"],
)


@public_router.get(
    "",
    response_model=SuccessStoryListResponse,
    summary="List published success stories",
)
async def list_stories_public(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return published stories, featured first, then by published_at DESC."""
    base_where = [
        SuccessStory.is_deleted.is_(False),
        SuccessStory.published_at.is_not(None),
    ]
    offset = (page - 1) * PUBLIC_PAGE_SIZE

    count_stmt = select(func.count()).select_from(SuccessStory).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(SuccessStory)
        .where(*base_where)
        .order_by(
            SuccessStory.is_featured.desc(),
            SuccessStory.published_at.desc(),
        )
        .limit(PUBLIC_PAGE_SIZE)
        .offset(offset)
    )
    result = await db.execute(stmt)
    stories = list(result.scalars().all())

    return {
        "items": [_serialise(s) for s in stories],
        "total": total,
        "page": page,
        "page_size": PUBLIC_PAGE_SIZE,
    }


@public_router.get(
    "/{story_id}",
    response_model=SuccessStoryResponse,
    summary="Get a single success story",
)
async def get_story_public(
    story_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return a single published success story."""
    story = await db.get(SuccessStory, story_id)
    if story is None or story.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Story not found"},
        )
    return _serialise(story)
