"""Blog/news post CRUD endpoints.

Admin endpoints:
  POST   /api/admin/blog          -- create post
  GET    /api/admin/blog          -- list all posts (inc. drafts)
  PUT    /api/admin/blog/{id}     -- update post
  DELETE /api/admin/blog/{id}     -- soft delete post

Public endpoints:
  GET  /api/blog            -- published posts, paginated
  GET  /api/blog/{slug}     -- single post by slug
  GET  /api/blog/tag/{tag}  -- posts filtered by tag
  GET  /api/blog/latest     -- latest 3 posts (for homepage)
"""

import logging
import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.blog_post import BlogPost
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

PUBLIC_PAGE_SIZE = 10
ADMIN_PAGE_SIZE = 20
EXCERPT_LENGTH = 150
LATEST_COUNT = 3

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BlogPostCreateRequest(BaseModel):
    """Payload for creating a blog post."""

    title: str = Field(..., min_length=1, max_length=300)
    slug: str | None = Field(default=None, max_length=350)
    body_html: str = Field(..., min_length=1)
    author_id: UUID | None = None
    featured_image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list)
    publish: bool = False


class BlogPostUpdateRequest(BaseModel):
    """Payload for updating a blog post."""

    title: str | None = Field(default=None, max_length=300)
    slug: str | None = Field(default=None, max_length=350)
    body_html: str | None = None
    featured_image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    publish: bool | None = None


class BlogPostResponse(BaseModel):
    """Blog post response."""

    id: UUID
    title: str
    slug: str
    body_html: str
    excerpt: str
    author_id: UUID | None = None
    featured_image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    published_at: str | None = None
    is_published: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BlogPostListResponse(BaseModel):
    """Paginated blog post list."""

    items: list[BlogPostResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:350]


def _excerpt(html: str) -> str:
    """Extract plain text excerpt from HTML."""
    text = re.sub(r"<[^>]+>", "", html)
    text = text.strip()
    if len(text) > EXCERPT_LENGTH:
        return text[:EXCERPT_LENGTH].rsplit(" ", 1)[0] + "..."
    return text


async def _unique_slug(db: AsyncSession, base_slug: str, exclude_id: UUID | None = None) -> str:
    """Ensure slug uniqueness by appending -2, -3, etc."""
    slug = base_slug
    counter = 1
    while True:
        stmt = (
            select(func.count())
            .select_from(BlogPost)
            .where(
                BlogPost.slug == slug,
                BlogPost.is_deleted.is_(False),
            )
        )
        if exclude_id is not None:
            stmt = stmt.where(BlogPost.id != exclude_id)
        count = (await db.execute(stmt)).scalar_one()
        if count == 0:
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


def _serialise(p: BlogPost) -> dict:
    """Convert blog post to response dict."""
    return {
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "body_html": p.body_html,
        "excerpt": _excerpt(p.body_html),
        "author_id": p.author_id,
        "featured_image_url": p.featured_image_url,
        "tags": p.tags or [],
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "is_published": p.is_published,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Admin Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/blog",
    tags=["admin-blog"],
    dependencies=[Depends(require_staff)],
)


@admin_router.post(
    "",
    response_model=BlogPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a blog post",
)
async def create_post(
    payload: BlogPostCreateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a new blog post with auto-generated slug."""
    base_slug = _slugify(payload.slug or payload.title)
    slug = await _unique_slug(db, base_slug)

    now = datetime.now(UTC) if payload.publish else None

    post = BlogPost(
        title=payload.title,
        slug=slug,
        body_html=payload.body_html,
        author_id=payload.author_id,
        featured_image_url=payload.featured_image_url,
        tags=payload.tags,
        is_published=payload.publish,
        published_at=now,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return _serialise(post)


@admin_router.get(
    "",
    response_model=BlogPostListResponse,
    summary="List all posts (admin)",
)
async def list_posts_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(ADMIN_PAGE_SIZE, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """List all posts including drafts."""
    base_where = [BlogPost.is_deleted.is_(False)]
    offset = (page - 1) * page_size

    count_stmt = select(func.count()).select_from(BlogPost).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(BlogPost)
        .where(*base_where)
        .order_by(BlogPost.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    result = await db.execute(stmt)
    posts = list(result.scalars().all())

    return {
        "items": [_serialise(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.put(
    "/{post_id}",
    response_model=BlogPostResponse,
    summary="Update a blog post",
)
async def update_post(
    post_id: UUID,
    payload: BlogPostUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update an existing blog post."""
    post = await db.get(BlogPost, post_id)
    if post is None or post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Post not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "publish" in update_data:
        should_publish = update_data.pop("publish")
        if should_publish and not post.is_published:
            post.is_published = True
            post.published_at = datetime.now(UTC)
        elif not should_publish:
            post.is_published = False
            post.published_at = None

    if update_data.get("slug"):
        base_slug = _slugify(update_data.pop("slug"))
        post.slug = await _unique_slug(db, base_slug, exclude_id=post.id)

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.flush()
    await db.refresh(post)
    return _serialise(post)


@admin_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a blog post",
)
async def delete_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Soft delete a blog post."""
    post = await db.get(BlogPost, post_id)
    if post is None or post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Post not found"},
        )
    post.is_deleted = True
    await db.flush()


# ---------------------------------------------------------------------------
# Public Router
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/blog",
    tags=["blog"],
)


@public_router.get(
    "/latest",
    response_model=list[BlogPostResponse],
    summary="Latest posts for homepage",
)
async def list_latest_posts(
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Return the latest 3 published posts for the homepage."""
    stmt = (
        select(BlogPost)
        .where(
            BlogPost.is_deleted.is_(False),
            BlogPost.is_published.is_(True),
        )
        .order_by(BlogPost.published_at.desc())
        .limit(LATEST_COUNT)
    )
    result = await db.execute(stmt)
    posts = list(result.scalars().all())
    return [_serialise(p) for p in posts]


@public_router.get(
    "/tag/{tag}",
    response_model=BlogPostListResponse,
    summary="Posts filtered by tag",
)
async def list_posts_by_tag(
    tag: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return published posts matching a tag."""
    offset = (page - 1) * PUBLIC_PAGE_SIZE
    base_where = [
        BlogPost.is_deleted.is_(False),
        BlogPost.is_published.is_(True),
        BlogPost.tags.contains([tag]),
    ]

    count_stmt = select(func.count()).select_from(BlogPost).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(BlogPost)
        .where(*base_where)
        .order_by(BlogPost.published_at.desc())
        .limit(PUBLIC_PAGE_SIZE)
        .offset(offset)
    )
    result = await db.execute(stmt)
    posts = list(result.scalars().all())

    return {
        "items": [_serialise(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": PUBLIC_PAGE_SIZE,
    }


@public_router.get(
    "/{slug}",
    response_model=BlogPostResponse,
    summary="Get a single blog post by slug",
)
async def get_post_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return a single published blog post by slug."""
    stmt = select(BlogPost).where(
        BlogPost.slug == slug,
        BlogPost.is_deleted.is_(False),
    )
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Post not found"},
        )
    return _serialise(post)


@public_router.get(
    "",
    response_model=BlogPostListResponse,
    summary="List published blog posts",
)
async def list_posts_public(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return published posts sorted by published_at DESC."""
    base_where = [
        BlogPost.is_deleted.is_(False),
        BlogPost.is_published.is_(True),
    ]
    offset = (page - 1) * PUBLIC_PAGE_SIZE

    count_stmt = select(func.count()).select_from(BlogPost).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(BlogPost)
        .where(*base_where)
        .order_by(BlogPost.published_at.desc())
        .limit(PUBLIC_PAGE_SIZE)
        .offset(offset)
    )
    result = await db.execute(stmt)
    posts = list(result.scalars().all())

    return {
        "items": [_serialise(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": PUBLIC_PAGE_SIZE,
    }
