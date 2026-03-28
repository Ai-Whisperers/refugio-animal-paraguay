"""Admin article editor API for educational content management.

Provides CRUD for educational articles with rich text support,
category management, reading time estimation, and SEO fields.

Endpoints:
    POST   /api/admin/articles           -- create article
    GET    /api/admin/articles           -- list articles (filterable)
    GET    /api/admin/articles/{id}      -- get article by ID
    PUT    /api/admin/articles/{id}      -- update article
    DELETE /api/admin/articles/{id}      -- soft-delete article
    POST   /api/admin/articles/{id}/publish  -- publish draft
    POST   /api/admin/articles/{id}/unpublish -- unpublish article
    GET    /api/articles/public          -- public article listing
"""

import logging
import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH = 300
MAX_SLUG_LENGTH = 350
MAX_BODY_LENGTH = 100_000
MAX_EXCERPT_LENGTH = 500
MAX_TAGS = 20
WORDS_PER_MINUTE = 200
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_TITLE_LENGTH = 3
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ArticleStatus(StrEnum):
    """Article publication status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ArticleCategory(StrEnum):
    """Educational article categories."""

    RESPONSIBLE_OWNERSHIP = "tenencia_responsable"
    HEALTH = "salud"
    NUTRITION = "nutricion"
    BEHAVIOR = "comportamiento"
    LEGAL = "legal"
    STERILIZATION = "esterilizacion"
    ADOPTION = "adopcion"
    GENERAL = "general"


CATEGORY_LABELS_ES: dict[str, str] = {
    "tenencia_responsable": "Tenencia Responsable",
    "salud": "Salud Animal",
    "nutricion": "Nutrición",
    "comportamiento": "Comportamiento",
    "legal": "Legal",
    "esterilizacion": "Esterilización",
    "adopcion": "Adopción",
    "general": "General",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ArticleCreateRequest(BaseModel):
    """Request to create an article."""

    title: str = Field(..., min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH)
    slug: str | None = Field(default=None, max_length=MAX_SLUG_LENGTH)
    body_html: str = Field(..., min_length=1, max_length=MAX_BODY_LENGTH)
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT_LENGTH)
    category: ArticleCategory = ArticleCategory.GENERAL
    tags: list[str] = Field(default_factory=list, max_length=MAX_TAGS)
    featured_image_url: str | None = Field(default=None, max_length=500)
    meta_title: str | None = Field(default=None, max_length=200)
    meta_description: str | None = Field(default=None, max_length=300)
    publish: bool = False
    author_name: str | None = Field(default=None, max_length=200)


class ArticleUpdateRequest(BaseModel):
    """Request to update an article."""

    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    slug: str | None = Field(default=None, max_length=MAX_SLUG_LENGTH)
    body_html: str | None = Field(default=None, max_length=MAX_BODY_LENGTH)
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT_LENGTH)
    category: ArticleCategory | None = None
    tags: list[str] | None = None
    featured_image_url: str | None = Field(default=None, max_length=500)
    meta_title: str | None = Field(default=None, max_length=200)
    meta_description: str | None = Field(default=None, max_length=300)
    author_name: str | None = Field(default=None, max_length=200)


class ArticleResponse(BaseModel):
    """Article response schema."""

    id: str
    title: str
    slug: str
    body_html: str
    excerpt: str | None = None
    category: ArticleCategory
    category_label: str
    tags: list[str]
    status: ArticleStatus
    featured_image_url: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    author_name: str | None = None
    reading_time_minutes: int
    word_count: int
    created_at: str
    updated_at: str
    published_at: str | None = None


class ArticleListResponse(BaseModel):
    """Paginated article list response."""

    articles: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_articles: dict[str, dict[str, Any]] = {}


def _reset_store() -> None:
    """Reset in-memory store (for testing)."""
    _articles.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_slug(title: str) -> str:
    """Generate URL-safe slug from title."""
    slug = title.lower().strip()
    # Replace accented characters common in Spanish
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ü": "u",
    }
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug[:MAX_SLUG_LENGTH]


def _estimate_reading_time(html_content: str) -> int:
    """Estimate reading time from HTML content."""
    text = re.sub(r"<[^>]+>", "", html_content)
    word_count = len(text.split())
    minutes = max(1, round(word_count / WORDS_PER_MINUTE))
    return minutes


def _count_words(html_content: str) -> int:
    """Count words in HTML content."""
    text = re.sub(r"<[^>]+>", "", html_content)
    return len(text.split())


def _generate_excerpt(html_content: str, max_length: int = 160) -> str:
    """Generate excerpt from HTML content."""
    text = re.sub(r"<[^>]+>", "", html_content)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def _validate_slug_unique(slug: str, exclude_id: str | None = None) -> None:
    """Ensure slug is unique among articles."""
    for article_id, article in _articles.items():
        if article["slug"] == slug and article_id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slug '{slug}' already exists",
            )


def _build_response(article: dict[str, Any]) -> ArticleResponse:
    """Build article response from stored data."""
    return ArticleResponse(
        id=article["id"],
        title=article["title"],
        slug=article["slug"],
        body_html=article["body_html"],
        excerpt=article.get("excerpt"),
        category=article["category"],
        category_label=CATEGORY_LABELS_ES.get(article["category"], article["category"]),
        tags=article.get("tags", []),
        status=article["status"],
        featured_image_url=article.get("featured_image_url"),
        meta_title=article.get("meta_title"),
        meta_description=article.get("meta_description"),
        author_name=article.get("author_name"),
        reading_time_minutes=_estimate_reading_time(article["body_html"]),
        word_count=_count_words(article["body_html"]),
        created_at=article["created_at"],
        updated_at=article["updated_at"],
        published_at=article.get("published_at"),
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/articles",
    tags=["article-editor"],
)

public_router = APIRouter(
    prefix="/api/articles",
    tags=["articles-public"],
)


# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------


@admin_router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(request: ArticleCreateRequest) -> ArticleResponse:
    """Create a new educational article."""
    slug = request.slug or _generate_slug(request.title)
    _validate_slug_unique(slug)

    now = datetime.now(UTC).isoformat()
    article_id = str(uuid4())
    article_status = ArticleStatus.PUBLISHED if request.publish else ArticleStatus.DRAFT
    excerpt = request.excerpt or _generate_excerpt(request.body_html)

    article: dict[str, Any] = {
        "id": article_id,
        "title": request.title,
        "slug": slug,
        "body_html": request.body_html,
        "excerpt": excerpt,
        "category": request.category,
        "tags": request.tags,
        "status": article_status,
        "featured_image_url": request.featured_image_url,
        "meta_title": request.meta_title or request.title,
        "meta_description": request.meta_description or excerpt,
        "author_name": request.author_name,
        "created_at": now,
        "updated_at": now,
        "published_at": now if request.publish else None,
    }
    _articles[article_id] = article

    logger.info(
        "Article created",
        extra={"article_id": article_id, "slug": slug, "status": article_status},
    )
    return _build_response(article)


@admin_router.get("", response_model=ArticleListResponse)
async def list_articles(
    status_filter: ArticleStatus | None = Query(None, alias="status"),
    category: ArticleCategory | None = Query(None),
    search: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> ArticleListResponse:
    """List articles with optional filtering."""
    articles = list(_articles.values())

    if status_filter is not None:
        articles = [a for a in articles if a["status"] == status_filter]
    if category is not None:
        articles = [a for a in articles if a["category"] == category]
    if search:
        search_lower = search.lower()
        articles = [
            a
            for a in articles
            if search_lower in a["title"].lower() or search_lower in a.get("excerpt", "").lower()
        ]

    articles.sort(key=lambda a: a["updated_at"], reverse=True)
    total = len(articles)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_articles = articles[start:end]

    return ArticleListResponse(
        articles=[_build_response(a) for a in page_articles],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@admin_router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str) -> ArticleResponse:
    """Get a single article by ID."""
    article = _articles.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found",
        )
    return _build_response(article)


@admin_router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, request: ArticleUpdateRequest) -> ArticleResponse:
    """Update an existing article."""
    article = _articles.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found",
        )

    if request.slug is not None:
        _validate_slug_unique(request.slug, exclude_id=article_id)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        article[key] = value

    article["updated_at"] = datetime.now(UTC).isoformat()

    if "body_html" in update_data and article.get("excerpt") is None:
        article["excerpt"] = _generate_excerpt(article["body_html"])

    logger.info("Article updated", extra={"article_id": article_id})
    return _build_response(article)


@admin_router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: str) -> None:
    """Soft-delete an article by archiving it."""
    article = _articles.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found",
        )
    article["status"] = ArticleStatus.ARCHIVED
    article["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Article archived", extra={"article_id": article_id})


@admin_router.post("/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(article_id: str) -> ArticleResponse:
    """Publish a draft article."""
    article = _articles.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found",
        )
    if article["status"] == ArticleStatus.PUBLISHED:
        return _build_response(article)

    now = datetime.now(UTC).isoformat()
    article["status"] = ArticleStatus.PUBLISHED
    article["published_at"] = now
    article["updated_at"] = now
    logger.info("Article published", extra={"article_id": article_id})
    return _build_response(article)


@admin_router.post("/{article_id}/unpublish", response_model=ArticleResponse)
async def unpublish_article(article_id: str) -> ArticleResponse:
    """Unpublish a published article back to draft."""
    article = _articles.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found",
        )
    article["status"] = ArticleStatus.DRAFT
    article["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Article unpublished", extra={"article_id": article_id})
    return _build_response(article)


# ---------------------------------------------------------------------------
# Public Endpoints
# ---------------------------------------------------------------------------


@public_router.get("/public", response_model=ArticleListResponse)
async def list_public_articles(
    category: ArticleCategory | None = Query(None),
    search: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> ArticleListResponse:
    """List published articles for public consumption."""
    articles = [a for a in _articles.values() if a["status"] == ArticleStatus.PUBLISHED]

    if category is not None:
        articles = [a for a in articles if a["category"] == category]
    if search:
        search_lower = search.lower()
        articles = [
            a
            for a in articles
            if search_lower in a["title"].lower() or search_lower in a.get("excerpt", "").lower()
        ]

    articles.sort(key=lambda a: a.get("published_at", a["created_at"]), reverse=True)
    total = len(articles)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size

    return ArticleListResponse(
        articles=[_build_response(a) for a in articles[start:end]],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
