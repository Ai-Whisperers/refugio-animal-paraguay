"""CMS content endpoints — CRUD for pages, blog posts, and announcements.

Endpoints:
  POST   /api/cms/content              -- create content (staff)
  GET    /api/cms/content               -- list content (staff, all statuses)
  GET    /api/cms/content/{id}          -- get content by ID (staff)
  PUT    /api/cms/content/{id}          -- update content (staff)
  POST   /api/cms/content/{id}/status   -- change status (staff)
  DELETE /api/cms/content/{id}          -- delete content (staff)
  GET    /api/public/cms/{slug}         -- public content by slug
  GET    /api/public/cms                -- public content listing
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.cms_service import (
    CMSError,
    ContentNotFoundError,
    InvalidContentTypeError,
    InvalidStatusTransitionError,
    SlugConflictError,
    change_content_status,
    create_content,
    delete_content,
    get_content_by_id,
    get_content_by_slug,
    list_content,
    list_public_content,
    update_content,
)

logger = logging.getLogger(__name__)

# Staff CMS router
router = APIRouter(
    prefix="/api/cms",
    tags=["cms"],
)

# Public CMS router
public_router = APIRouter(
    prefix="/api/public/cms",
    tags=["cms-public"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CMSCreateRequest(BaseModel):
    """Request body for creating content."""

    content_type: str = Field(..., max_length=30, description="Content type")
    title: str = Field(..., min_length=1, max_length=300, description="Content title")
    body: str = Field(..., min_length=1, description="Content body (HTML or Markdown)")
    summary: str | None = Field(default=None, max_length=500)
    featured_image_url: str | None = Field(default=None, max_length=500)
    meta_description: str | None = Field(default=None, max_length=300)
    tags: list[str] | None = Field(default=None, max_length=20)
    sort_order: int = Field(default=0)


class CMSUpdateRequest(BaseModel):
    """Request body for updating content."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    body: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    featured_image_url: str | None = None
    meta_description: str | None = Field(default=None, max_length=300)
    tags: list[str] | None = None
    sort_order: int | None = None


class CMSStatusRequest(BaseModel):
    """Request body for changing content status."""

    status: str = Field(..., description="New status: draft, published, or archived")


class CMSContentResponse(BaseModel):
    """Response schema for CMS content."""

    id: UUID
    content_type: str
    slug: str
    title: str
    summary: str | None
    body: str
    status: str
    featured_image_url: str | None
    meta_description: str | None
    tags: list | None
    author_id: UUID | None
    sort_order: int
    published_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CMSListResponse(BaseModel):
    """Paginated list of CMS content."""

    items: list[CMSContentResponse]
    total: int
    limit: int
    offset: int


class CMSPublicResponse(BaseModel):
    """Public-facing content response (no author_id)."""

    id: UUID
    content_type: str
    slug: str
    title: str
    summary: str | None
    body: str
    featured_image_url: str | None
    meta_description: str | None
    tags: list | None
    published_at: str | None

    model_config = {"from_attributes": True}


class CMSPublicListResponse(BaseModel):
    """Paginated public content list."""

    items: list[CMSPublicResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Staff endpoints
# ---------------------------------------------------------------------------


def _handle_cms_error(exc: CMSError) -> HTTPException:
    """Map CMS errors to HTTP responses."""
    if isinstance(exc, ContentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": exc.message, "details": exc.details},
        )
    if isinstance(exc, SlugConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "conflict", "message": exc.message, "details": exc.details},
        )
    if isinstance(exc, InvalidContentTypeError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": exc.message, "details": exc.details},
        )
    if isinstance(exc, InvalidStatusTransitionError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "conflict", "message": exc.message, "details": exc.details},
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "validation_error", "message": exc.message, "details": exc.details},
    )


@router.post(
    "/content",
    response_model=CMSContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create CMS content",
)
async def create_content_endpoint(
    body: CMSCreateRequest,
    staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CMSContentResponse:
    """Create a new CMS content item."""
    try:
        content = await create_content(
            content_type=body.content_type,
            title=body.title,
            body=body.body,
            summary=body.summary,
            featured_image_url=body.featured_image_url,
            meta_description=body.meta_description,
            tags=body.tags,
            author_id=staff_user.id,
            sort_order=body.sort_order,
            db=db,
        )
    except CMSError as exc:
        raise _handle_cms_error(exc) from None

    await db.commit()
    return CMSContentResponse.model_validate(content)


@router.get(
    "/content",
    response_model=CMSListResponse,
    summary="List CMS content",
)
async def list_content_endpoint(
    content_type: str | None = Query(None, description="Filter by content type"),
    content_status: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CMSListResponse:
    """List all CMS content with optional filters."""
    try:
        items, total = await list_content(
            db,
            content_type=content_type,
            status=content_status,
            limit=limit,
            offset=offset,
        )
    except CMSError as exc:
        raise _handle_cms_error(exc) from None

    return CMSListResponse(
        items=[CMSContentResponse.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/content/{content_id}",
    response_model=CMSContentResponse,
    summary="Get CMS content by ID",
)
async def get_content_endpoint(
    content_id: UUID,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CMSContentResponse:
    """Get a single CMS content item by ID."""
    try:
        content = await get_content_by_id(content_id, db)
    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Content not found"},
        ) from None

    return CMSContentResponse.model_validate(content)


@router.put(
    "/content/{content_id}",
    response_model=CMSContentResponse,
    summary="Update CMS content",
)
async def update_content_endpoint(
    content_id: UUID,
    body: CMSUpdateRequest,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CMSContentResponse:
    """Update an existing CMS content item."""
    kwargs: dict = {"content_id": content_id, "db": db}
    if body.title is not None:
        kwargs["title"] = body.title
    if body.body is not None:
        kwargs["body"] = body.body
    if body.summary is not None:
        kwargs["summary"] = body.summary
    if body.featured_image_url is not None:
        kwargs["featured_image_url"] = body.featured_image_url
    if body.meta_description is not None:
        kwargs["meta_description"] = body.meta_description
    if body.tags is not None:
        kwargs["tags"] = body.tags
    if body.sort_order is not None:
        kwargs["sort_order"] = body.sort_order

    try:
        content = await update_content(**kwargs)
    except CMSError as exc:
        raise _handle_cms_error(exc) from None

    await db.commit()
    return CMSContentResponse.model_validate(content)


@router.post(
    "/content/{content_id}/status",
    response_model=CMSContentResponse,
    summary="Change content status",
)
async def change_status_endpoint(
    content_id: UUID,
    body: CMSStatusRequest,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CMSContentResponse:
    """Publish, archive, or unpublish content."""
    try:
        content = await change_content_status(
            content_id=content_id,
            new_status=body.status,
            db=db,
        )
    except CMSError as exc:
        raise _handle_cms_error(exc) from None

    await db.commit()
    return CMSContentResponse.model_validate(content)


@router.delete(
    "/content/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete CMS content",
)
async def delete_content_endpoint(
    content_id: UUID,
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a CMS content item."""
    try:
        await delete_content(content_id, db)
    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Content not found"},
        ) from None

    await db.commit()


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.get(
    "/{slug}",
    response_model=CMSPublicResponse,
    summary="Get published content by slug",
)
async def get_public_content(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> CMSPublicResponse:
    """Get published content by slug (public, no auth)."""
    try:
        content = await get_content_by_slug(slug, db)
    except ContentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Content not found"},
        ) from None

    return CMSPublicResponse.model_validate(content)


@public_router.get(
    "",
    response_model=CMSPublicListResponse,
    summary="List published content",
)
async def list_public_content_endpoint(
    content_type: str | None = Query(None, description="Filter by content type"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> CMSPublicListResponse:
    """List published content (public, no auth)."""
    try:
        items, total = await list_public_content(
            db,
            content_type=content_type,
            limit=limit,
            offset=offset,
        )
    except CMSError as exc:
        raise _handle_cms_error(exc) from None

    return CMSPublicListResponse(
        items=[CMSPublicResponse.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )
