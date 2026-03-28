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

from src.db.models.cms_content import (
    CMSContent,
    ContentLanguage,
    ContentStatus,
    ContentType,
    TranslationStatus,
)

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

DEFAULT_LANGUAGE = ContentLanguage.ES
FALLBACK_LANGUAGE = ContentLanguage.ES

VALID_CONTENT_TYPES = frozenset({t.value for t in ContentType})
VALID_STATUSES = frozenset({s.value for s in ContentStatus})
VALID_LANGUAGES = frozenset({lang.value for lang in ContentLanguage})
VALID_TRANSLATION_STATUSES = frozenset({s.value for s in TranslationStatus})


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


class InvalidLanguageError(CMSError):
    """Raised for unsupported language code."""

    def __init__(self, language: str) -> None:
        super().__init__(
            message="Invalid language",
            details=f"Must be one of: {', '.join(sorted(VALID_LANGUAGES))}",
        )


class TranslationExistsError(CMSError):
    """Raised when a translation already exists for the given language."""

    def __init__(self, slug: str, language: str) -> None:
        super().__init__(
            message="Translation already exists",
            details=f"Content '{slug}' already has a '{language}' translation",
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


def validate_language(language: str) -> None:
    """Validate language code."""
    if language not in VALID_LANGUAGES:
        raise InvalidLanguageError(language)


async def _ensure_unique_slug(
    db: AsyncSession,
    slug: str,
    language: str = DEFAULT_LANGUAGE,
    exclude_id: UUID | None = None,
) -> str:
    """Ensure slug is unique within the same language, appending a number if needed."""
    base_slug = slug
    counter = 1

    while True:
        query = select(CMSContent.id).where(
            CMSContent.slug == slug,
            CMSContent.language == language,
        )
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
    language: str = DEFAULT_LANGUAGE,
    db: AsyncSession,
) -> CMSContent:
    """Create a new CMS content item (starts as draft).

    Raises:
        CMSError: If validation fails.
        InvalidContentTypeError: If content type is invalid.
        InvalidLanguageError: If language code is invalid.
    """
    validate_content_type(content_type)
    validate_title(title)
    validate_body(body)
    validate_summary(summary)
    validate_tags(tags)
    validate_language(language)

    base_slug = generate_slug(title)
    slug = await _ensure_unique_slug(db, base_slug, language=language)

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
        language=language,
        translation_status=TranslationStatus.ORIGINAL,
    )

    db.add(content)
    await db.flush()

    logger.info(
        "CMS content created: type=%s slug=%s lang=%s",
        content_type,
        slug,
        language,
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


async def get_content_by_slug(
    slug: str,
    db: AsyncSession,
    language: str | None = None,
) -> tuple[CMSContent, bool]:
    """Get published content by slug with language fallback.

    Returns (content, language_fallback) where language_fallback is True
    if the requested language was not available and the fallback language
    was used instead.

    Raises:
        ContentNotFoundError: If not found or not published.
        InvalidLanguageError: If language code is invalid.
    """
    if language:
        validate_language(language)

    target_lang = language or DEFAULT_LANGUAGE

    # Try requested language first
    result = await db.execute(
        select(CMSContent).where(
            CMSContent.slug == slug,
            CMSContent.language == target_lang,
            CMSContent.status == ContentStatus.PUBLISHED,
        )
    )
    content = result.scalar_one_or_none()
    if content is not None:
        return content, False

    # Fallback to default language (Spanish) if different from requested
    if target_lang != FALLBACK_LANGUAGE:
        result = await db.execute(
            select(CMSContent).where(
                CMSContent.slug == slug,
                CMSContent.language == FALLBACK_LANGUAGE,
                CMSContent.status == ContentStatus.PUBLISHED,
            )
        )
        content = result.scalar_one_or_none()
        if content is not None:
            return content, True

    raise ContentNotFoundError(slug)


async def list_content(
    db: AsyncSession,
    *,
    content_type: str | None = None,
    status: str | None = None,
    language: str | None = None,
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

    if language:
        validate_language(language)
        query = query.where(CMSContent.language == language)
        count_query = count_query.where(CMSContent.language == language)

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
    language: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[CMSContent], int]:
    """List published content for public consumption."""
    return await list_content(
        db,
        content_type=content_type,
        status=ContentStatus.PUBLISHED,
        language=language or DEFAULT_LANGUAGE,
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


# ---------------------------------------------------------------------------
# Translation management
# ---------------------------------------------------------------------------


async def create_translation(
    *,
    source_content_id: UUID,
    language: str,
    title: str,
    body: str,
    summary: str | None = None,
    meta_description: str | None = None,
    author_id: UUID | None = None,
    db: AsyncSession,
) -> CMSContent:
    """Create a translation of an existing content item.

    Raises:
        ContentNotFoundError: If source content not found.
        InvalidLanguageError: If language code is invalid.
        TranslationExistsError: If translation already exists for the language.
        CMSError: If validation fails.
    """
    validate_language(language)
    validate_title(title)
    validate_body(body)
    validate_summary(summary)

    source = await get_content_by_id(source_content_id, db)

    if language == source.language:
        raise CMSError(
            message="Cannot translate to same language",
            details=f"Source content is already in '{language}'",
        )

    # Check if translation already exists for this slug + language
    existing = await db.execute(
        select(CMSContent.id).where(
            CMSContent.slug == source.slug,
            CMSContent.language == language,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise TranslationExistsError(source.slug, language)

    translation = CMSContent(
        content_type=source.content_type,
        slug=source.slug,  # Same slug, different language
        title=title,
        body=body,
        summary=summary,
        featured_image_url=source.featured_image_url,
        meta_description=meta_description,
        tags=source.tags,
        author_id=author_id,
        sort_order=source.sort_order,
        language=language,
        translation_status=TranslationStatus.TRANSLATED,
        source_content_id=source_content_id,
    )

    db.add(translation)
    await db.flush()

    logger.info(
        "CMS translation created: slug=%s lang=%s source_id=%s",
        source.slug,
        language,
        source_content_id,
    )
    return translation


async def get_translation_status(
    content_id: UUID,
    db: AsyncSession,
) -> dict:
    """Get translation status for a content item and all its translations.

    Returns dict with available languages, their statuses, and completion count.
    """
    content = await get_content_by_id(content_id, db)

    # Find the source: either this content is the original, or follow source_content_id
    source_id = content.source_content_id or content.id

    # Get all translations sharing the same source (or the source itself)
    result = await db.execute(
        select(CMSContent).where(
            (CMSContent.id == source_id) | (CMSContent.source_content_id == source_id)
        )
    )
    all_versions = list(result.scalars().all())

    languages: dict[str, dict] = {}
    for version in all_versions:
        languages[version.language] = {
            "content_id": str(version.id),
            "translation_status": version.translation_status,
            "status": version.status,
            "updated_at": str(version.updated_at),
        }

    total_languages = len(VALID_LANGUAGES)
    completed = sum(
        1
        for lang_info in languages.values()
        if lang_info["translation_status"]
        in (TranslationStatus.ORIGINAL, TranslationStatus.TRANSLATED)
    )

    return {
        "source_content_id": str(source_id),
        "languages": languages,
        "total_supported_languages": total_languages,
        "completed_translations": completed,
        "completion_label": f"{completed}/{total_languages} languages completed",
    }


async def mark_translations_outdated(
    content_id: UUID,
    db: AsyncSession,
) -> int:
    """Mark all translations of a content item as outdated.

    Called when the source content is updated, so translators know
    the translations need updating.

    Returns the number of translations marked outdated.
    """
    result = await db.execute(
        select(CMSContent).where(
            CMSContent.source_content_id == content_id,
            CMSContent.translation_status == TranslationStatus.TRANSLATED,
        )
    )
    translations = list(result.scalars().all())

    for translation in translations:
        translation.translation_status = TranslationStatus.OUTDATED

    if translations:
        await db.flush()
        logger.info(
            "Marked %d translations as outdated for content_id=%s",
            len(translations),
            content_id,
        )

    return len(translations)
