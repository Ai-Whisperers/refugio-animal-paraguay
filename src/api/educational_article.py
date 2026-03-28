"""API endpoints for educational articles.

Admin endpoints for CRUD, public endpoints for browsing published articles.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.educational_article_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ArticleNotFoundError,
    DuplicateSlugError,
    InvalidArticleError,
    create_article,
    delete_article,
    get_article,
    get_article_by_slug,
    list_articles,
    update_article,
)

admin_router = APIRouter(tags=["Educational Articles (Admin)"])
public_router = APIRouter(tags=["Educational Articles (Public)"])


# --- Schemas ---


class CreateArticleRequest(BaseModel):
    """Request body for creating an article."""

    title: str
    content: str
    category: str = "general"
    summary: str | None = None
    tags: list[str] | None = None
    cover_image_url: str | None = None
    status: str = "draft"


class UpdateArticleRequest(BaseModel):
    """Request body for updating an article."""

    title: str | None = None
    content: str | None = None
    summary: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    cover_image_url: str | None = None
    status: str | None = None


class ArticleResponse(BaseModel):
    """Article details."""

    id: UUID
    title: str
    slug: str
    summary: str | None = None
    content: str
    category: str
    tags: list[str] | None = None
    cover_image_url: str | None = None
    status: str
    author_id: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    """Paginated list of articles."""

    articles: list[ArticleResponse]
    total: int
    limit: int
    offset: int


# --- Admin Endpoints ---


@admin_router.post(
    "/api/admin/articles",
    response_model=ArticleResponse,
    status_code=201,
)
async def create_article_endpoint(
    body: CreateArticleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Create a new educational article."""
    try:
        return await create_article(
            db=db,
            title=body.title,
            content=body.content,
            author_id=current_user.id,
            category=body.category,
            summary=body.summary,
            tags=body.tags,
            cover_image_url=body.cover_image_url,
            status=body.status,
        )
    except InvalidArticleError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    except DuplicateSlugError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@admin_router.get(
    "/api/admin/articles",
    response_model=ArticleListResponse,
)
async def list_articles_admin(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """List all articles (admin view, includes drafts)."""
    return await list_articles(
        db=db, category=category, status_filter=status, search=search, limit=limit, offset=offset
    )


@admin_router.get(
    "/api/admin/articles/{article_id}",
    response_model=ArticleResponse,
)
async def get_article_admin(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get an article by ID (admin view)."""
    try:
        return await get_article(db=db, article_id=article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found") from None


@admin_router.put(
    "/api/admin/articles/{article_id}",
    response_model=ArticleResponse,
)
async def update_article_endpoint(
    article_id: UUID,
    body: UpdateArticleRequest,
    db: AsyncSession = Depends(get_db),
    _admin: object = Depends(require_admin),
) -> dict:
    """Update an existing article."""
    try:
        return await update_article(
            db=db,
            article_id=article_id,
            title=body.title,
            content=body.content,
            summary=body.summary,
            category=body.category,
            tags=body.tags,
            cover_image_url=body.cover_image_url,
            status=body.status,
        )
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found") from None
    except InvalidArticleError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@admin_router.delete(
    "/api/admin/articles/{article_id}",
    status_code=204,
)
async def delete_article_endpoint(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: object = Depends(require_admin),
) -> None:
    """Delete an article."""
    try:
        await delete_article(db=db, article_id=article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found") from None


# --- Public Endpoints ---


@public_router.get(
    "/api/articles",
    response_model=ArticleListResponse,
)
async def list_published_articles(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List published articles (public view)."""
    return await list_articles(
        db=db,
        category=category,
        status_filter="published",
        search=search,
        limit=limit,
        offset=offset,
    )


@public_router.get(
    "/api/articles/{slug}",
    response_model=ArticleResponse,
)
async def get_published_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a published article by slug."""
    try:
        article = await get_article_by_slug(db=db, slug=slug)
        if article["status"] != "published":
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found") from None
