"""Service layer for educational article management.

Handles CRUD for educational articles with slug generation,
category validation, and search/filter functionality.
"""

import logging
import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.educational_article import (
    VALID_CATEGORIES,
    VALID_STATUSES,
    ArticleStatus,
    EducationalArticle,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class ArticleError(Exception):
    """Base error for article operations."""


class ArticleNotFoundError(ArticleError):
    """Raised when an article does not exist."""


class DuplicateSlugError(ArticleError):
    """Raised when a slug already exists."""


class InvalidArticleError(ArticleError):
    """Raised when article validation fails."""


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from a title.

    Handles Spanish characters by transliterating to ASCII.
    """
    # Normalize unicode, decompose accented chars
    normalized = unicodedata.normalize("NFKD", title)
    # Remove non-ASCII characters (accents)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


async def create_article(
    db: AsyncSession,
    title: str,
    content: str,
    author_id: UUID,
    category: str = "general",
    summary: str | None = None,
    tags: list[str] | None = None,
    cover_image_url: str | None = None,
    status: str = "draft",
) -> dict:
    """Create a new educational article."""
    if category not in VALID_CATEGORIES:
        raise InvalidArticleError(
            f"Invalid category '{category}', must be one of {VALID_CATEGORIES}"
        )
    if status not in VALID_STATUSES:
        raise InvalidArticleError(f"Invalid status '{status}', must be one of {VALID_STATUSES}")
    if not title.strip():
        raise InvalidArticleError("Title is required")
    if not content.strip():
        raise InvalidArticleError("Content is required")

    slug = generate_slug(title)

    # Check for duplicate slug
    existing = await db.execute(
        select(func.count()).select_from(EducationalArticle).where(EducationalArticle.slug == slug)
    )
    if existing.scalar_one() > 0:
        raise DuplicateSlugError(f"An article with slug '{slug}' already exists")

    published_at = datetime.now(UTC) if status == ArticleStatus.PUBLISHED else None

    article = EducationalArticle(
        title=title.strip(),
        slug=slug,
        summary=summary,
        content=content.strip(),
        category=category,
        tags=tags or [],
        cover_image_url=cover_image_url,
        status=status,
        author_id=author_id,
        published_at=published_at,
    )
    db.add(article)
    await db.flush()
    await db.refresh(article)

    return _article_to_dict(article)


async def get_article(db: AsyncSession, article_id: UUID) -> dict:
    """Get an article by ID."""
    result = await db.execute(select(EducationalArticle).where(EducationalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise ArticleNotFoundError(f"Article {article_id} not found")
    return _article_to_dict(article)


async def get_article_by_slug(db: AsyncSession, slug: str) -> dict:
    """Get an article by slug (for public URLs)."""
    result = await db.execute(select(EducationalArticle).where(EducationalArticle.slug == slug))
    article = result.scalar_one_or_none()
    if article is None:
        raise ArticleNotFoundError(f"Article with slug '{slug}' not found")
    return _article_to_dict(article)


async def list_articles(
    db: AsyncSession,
    category: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List articles with optional filters and search."""
    base_query = select(EducationalArticle)

    if category is not None:
        base_query = base_query.where(EducationalArticle.category == category)
    if status_filter is not None:
        base_query = base_query.where(EducationalArticle.status == status_filter)
    if search is not None:
        pattern = f"%{search}%"
        base_query = base_query.where(
            or_(
                EducationalArticle.title.ilike(pattern),
                EducationalArticle.summary.ilike(pattern),
            )
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(EducationalArticle.created_at.desc()).limit(limit).offset(offset)
    )
    articles = list(result.scalars().all())

    return {
        "articles": [_article_to_dict(a) for a in articles],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_article(
    db: AsyncSession,
    article_id: UUID,
    title: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    cover_image_url: str | None = None,
    status: str | None = None,
) -> dict:
    """Update an existing article."""
    result = await db.execute(select(EducationalArticle).where(EducationalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise ArticleNotFoundError(f"Article {article_id} not found")

    if category is not None and category not in VALID_CATEGORIES:
        raise InvalidArticleError(f"Invalid category '{category}'")
    if status is not None and status not in VALID_STATUSES:
        raise InvalidArticleError(f"Invalid status '{status}'")

    if title is not None:
        article.title = title.strip()
        article.slug = generate_slug(title)
    if content is not None:
        article.content = content.strip()
    if summary is not None:
        article.summary = summary
    if category is not None:
        article.category = category
    if tags is not None:
        article.tags = tags
    if cover_image_url is not None:
        article.cover_image_url = cover_image_url
    if status is not None:
        old_status = article.status
        article.status = status
        # Set published_at when transitioning to published
        if status == ArticleStatus.PUBLISHED and old_status != ArticleStatus.PUBLISHED:
            article.published_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(article)

    return _article_to_dict(article)


async def delete_article(db: AsyncSession, article_id: UUID) -> None:
    """Delete an article."""
    result = await db.execute(select(EducationalArticle).where(EducationalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise ArticleNotFoundError(f"Article {article_id} not found")

    await db.delete(article)
    await db.flush()


def _article_to_dict(article: EducationalArticle) -> dict:
    """Convert an EducationalArticle to a dict."""
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "summary": article.summary,
        "content": article.content,
        "category": article.category,
        "tags": article.tags,
        "cover_image_url": article.cover_image_url,
        "status": article.status,
        "author_id": article.author_id,
        "published_at": article.published_at,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }
