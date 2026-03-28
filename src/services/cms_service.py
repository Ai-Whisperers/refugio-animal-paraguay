"""CMS content service — CRUD operations for pages, posts, and announcements.

Handles content creation, updates, publishing, archiving, and public listing
with filtering by content type and status.
"""

import logging
import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.cms_content import CMSContent, ContentStatus, ContentType

logger = logging.getLogger(__name__)

# Validation constraints
MAX_TITLE_LENGTH = 300
MIN_TITLE_LENGTH = 1
MAX_SUMMARY_LENGTH = 500
MAX_SLUG_LENGTH = 200
MAX_META_DESCRIPTION_LENGTH = 300
MAX_FEATURED_IMAGE_URL_LENGTH = 500
MAX_BODY_LENGTH = 100_000
MAX_TAGS = 20
MAX_TAG_LENGTH = 50

VALID_CONTENT_TYPES = frozenset({t.value for t in ContentType})
VALID_STATUSES = frozenset({s.value for s in ContentStatus})


class CMSError(Exception):
    """Base error for CMS operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ContentNotFoundError(CMSError):
    """Raised when content is not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Content not found",
            details=f"No content found for: {identifier}",
        )
        self.identifier = identifier


class SlugConflictError(CMSError):
    """Raised when a slug already exists."""

    def __init__(self, slug: str) -> None:
        super().__init__(
            message="Slug already exists",
            details=f"Content with slug '{slug}' already exists",
        )
        self.slug = slug


class InvalidContentTypeError(CMSError):
    """Raised for invalid content type."""

    def __init__(self, content_type: str) -> None:
        super().__init__(
            message="Invalid content type",
            details=f"Must be one of: {', '.join(sorted(VALID_CONTENT_TYPES))}",
        )


class InvalidStatusTransitionError(CMSError):
    """Raised for invalid status transition."""

    def __init__(self, current: str, requested: str) -> None:
        super().__init__(
            message="Invalid status transition",
            details=f"Cannot transition from '{current}' to '{requested}'",
        )


# Valid status transitions
VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    ContentStatus.DRAFT: {ContentStatus.PUBLISHED, ContentStatus.ARCHIVED},
    ContentStatus.PUBLISHED: {ContentStatus.DRAFT, ContentStatus.ARCHIVED},
    ContentStatus.ARCHIVED: {ContentStatus.DRAFT},
}


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower())
    slug = slug.strip("-")
    if len(slug) > MAX_SLUG_LENGTH:
        slug = slug[:MAX_SLUG_LENGTH].rstrip("-")
    return slug or "content"


def validate_title(title: str) -> None:
    """Validate content title."""
    if len(title) < MIN_TITLE_LENGTH:
        raise CMSError(
            message="Title too short",
            details=f"Minimum {MIN_TITLE_LENGTH} character required",
        )
    if len(title) > MAX_TITLE_LENGTH:
        raise CMSError(
            message="Title too long",
            details=f"Maximum {MAX_TITLE_LENGTH} characters allowed",
        )


def validate_body(body: str) -> None:
    """Validate content body."""
    if not body or not body.strip():
        raise CMSError(
            message="Body is required",
            details="Content body cannot be empty",
        )
    if len(body) > MAX_BODY_LENGTH:
        raise CMSError(
            message="Body too long",
            details=f"Maximum {MAX_BODY_LENGTH} characters allowed",
        )


def validate_content_type(content_type: str) -> None:
    """Validate content type."""
    if content_type not in VALID_CONTENT_TYPES:
        raise InvalidContentTypeError(content_type)


def validate_summary(summary: str | None) -> None:
    """Validate summary length."""
    if summary and len(summary) > MAX_SUMMARY_LENGTH:
        raise CMSError(
            message="Summary too long",
            details=f"Maximum {MAX_SUMMARY_LENGTH} characters allowed",
        )


def validate_tags(tags: list | None) -> None:
    """Validate tags list."""
    if not tags:
        return
    if len(tags) > MAX_TAGS:
        raise CMSError(
            message="Too many tags",
            details=f"Maximum {MAX_TAGS} tags allowed",
        )
    for tag in tags:
        if not isinstance(tag, str) or len(tag) > MAX_TAG_LENGTH:
            raise CMSError(
                message="Invalid tag",
                details=f"Each tag must be a string of max {MAX_TAG_LENGTH} characters",
            )


async def _ensure_unique_slug(db: AsyncSession, slug: str, exclude_id: UUID | None = None) -> str:
    """Ensure slug is unique, appending a number if needed."""
    base_slug = slug
    counter = 1

    while True:
        query = select(CMSContent.id).where(CMSContent.slug == slug)
        if exclude_id:
            query = query.where(CMSContent.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            raise CMSError(
                message="Could not generate unique slug",
                details=f"Too many contents with similar title to '{base_slug}'",
            )


async def create_content(
    *,
    content_type: str,
    title: str,
    body: str,
    summary: str | None = None,
    featured_image_url: str | None = None,
    meta_description: str | None = None,
    tags: list | None = None,
    author_id: UUID | None = None,
    sort_order: int = 0,
    db: AsyncSession,
) -> CMSContent:
    """Create a new CMS content item (starts as draft).

    Raises:
        CMSError: If validation fails.
        InvalidContentTypeError: If content type is invalid.
    """
    validate_content_type(content_type)
    validate_title(title)
    validate_body(body)
    validate_summary(summary)
    validate_tags(tags)

    base_slug = generate_slug(title)
    slug = await _ensure_unique_slug(db, base_slug)

    content = CMSContent(
        content_type=content_type,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        featured_image_url=featured_image_url,
        meta_description=meta_description,
        tags=tags,
        author_id=author_id,
        sort_order=sort_order,
    )

    db.add(content)
    await db.flush()

    logger.info(
        "CMS content created: type=%s slug=%s",
        content_type,
        slug,
    )
    return content


async def get_content_by_id(content_id: UUID, db: AsyncSession) -> CMSContent:
    """Get content by ID.

    Raises:
        ContentNotFoundError: If not found.
    """
    result = await db.execute(select(CMSContent).where(CMSContent.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise ContentNotFoundError(str(content_id))
    return content


async def get_content_by_slug(slug: str, db: AsyncSession) -> CMSContent:
    """Get published content by slug (public endpoint).

    Raises:
        ContentNotFoundError: If not found or not published.
    """
    result = await db.execute(
        select(CMSContent).where(
            CMSContent.slug == slug,
            CMSContent.status == ContentStatus.PUBLISHED,
        )
    )
    content = result.scalar_one_or_none()
    if content is None:
        raise ContentNotFoundError(slug)
    return content


async def list_content(
    db: AsyncSession,
    *,
    content_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CMSContent], int]:
    """List content with optional filters and pagination.

    Returns (items, total_count).
    """
    query = select(CMSContent)
    count_query = select(func.count(CMSContent.id))

    if content_type:
        validate_content_type(content_type)
        query = query.where(CMSContent.content_type == content_type)
        count_query = count_query.where(CMSContent.content_type == content_type)

    if status:
        query = query.where(CMSContent.status == status)
        count_query = count_query.where(CMSContent.status == status)

    query = query.order_by(CMSContent.sort_order.asc(), CMSContent.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return items, total


async def list_public_content(
    db: AsyncSession,
    *,
    content_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[CMSContent], int]:
    """List published content for public consumption."""
    return await list_content(
        db,
        content_type=content_type,
        status=ContentStatus.PUBLISHED,
        limit=limit,
        offset=offset,
    )


async def update_content(
    *,
    content_id: UUID,
    title: str | None = None,
    body: str | None = None,
    summary: str | None = ...,  # type: ignore[assignment]
    featured_image_url: str | None = ...,  # type: ignore[assignment]
    meta_description: str | None = ...,  # type: ignore[assignment]
    tags: list | None = ...,  # type: ignore[assignment]
    sort_order: int | None = None,
    db: AsyncSession,
) -> CMSContent:
    """Update an existing content item.

    Uses sentinel ... to distinguish 'not provided' from None.

    Raises:
        ContentNotFoundError: If not found.
        CMSError: If validation fails.
    """
    content = await get_content_by_id(content_id, db)

    if title is not None:
        validate_title(title)
        content.title = title
        # Regenerate slug if title changed
        base_slug = generate_slug(title)
        content.slug = await _ensure_unique_slug(db, base_slug, exclude_id=content_id)

    if body is not None:
        validate_body(body)
        content.body = body

    if summary is not ...:
        validate_summary(summary)
        content.summary = summary

    if featured_image_url is not ...:
        content.featured_image_url = featured_image_url

    if meta_description is not ...:
        content.meta_description = meta_description

    if tags is not ...:
        validate_tags(tags)
        content.tags = tags

    if sort_order is not None:
        content.sort_order = sort_order

    await db.flush()

    logger.info("CMS content updated: id=%s slug=%s", content_id, content.slug)
    return content


async def change_content_status(
    *,
    content_id: UUID,
    new_status: str,
    db: AsyncSession,
) -> CMSContent:
    """Change the status of a content item (publish, archive, unpublish).

    Raises:
        ContentNotFoundError: If not found.
        InvalidStatusTransitionError: If transition not allowed.
    """
    content = await get_content_by_id(content_id, db)

    allowed = VALID_STATUS_TRANSITIONS.get(content.status, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(content.status, new_status)

    content.status = new_status

    # Set published_at on first publish
    if new_status == ContentStatus.PUBLISHED and content.published_at is None:
        content.published_at = datetime.now(UTC)

    await db.flush()

    logger.info(
        "CMS content status changed: id=%s status=%s",
        content_id,
        new_status,
    )
    return content


async def delete_content(content_id: UUID, db: AsyncSession) -> None:
    """Delete a content item.

    Raises:
        ContentNotFoundError: If not found.
    """
    content = await get_content_by_id(content_id, db)
    await db.delete(content)
    await db.flush()

    logger.info("CMS content deleted: id=%s slug=%s", content_id, content.slug)
