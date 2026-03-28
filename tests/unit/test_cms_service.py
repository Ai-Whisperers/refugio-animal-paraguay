"""Unit tests for CMS content service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.cms_service import (
    CMSError,
    ContentNotFoundError,
    InvalidContentTypeError,
    InvalidStatusTransitionError,
    SlugConflictError,
    change_content_status,
    create_content,
    delete_content,
    generate_slug,
    get_content_by_id,
    get_content_by_slug,
    list_content,
    list_public_content,
    update_content,
    validate_body,
    validate_content_type,
    validate_summary,
    validate_tags,
    validate_title,
)

# ---------------------------------------------------------------------------
# generate_slug
# ---------------------------------------------------------------------------


class TestGenerateSlug:
    """Tests for slug generation from titles."""

    def test_basic_slug(self) -> None:
        assert generate_slug("Hello World") == "hello-world"

    def test_special_characters_removed(self) -> None:
        assert generate_slug("Hello! @World #2024") == "hello-world-2024"

    def test_accented_characters_stripped(self) -> None:
        assert generate_slug("Cafe Resumen") == "cafe-resumen"

    def test_unicode_accents_normalized(self) -> None:
        result = generate_slug("Adopcion de Animales")
        assert result == "adopcion-de-animales"

    def test_multiple_spaces_collapsed(self) -> None:
        assert generate_slug("Hello    World") == "hello-world"

    def test_leading_trailing_hyphens_stripped(self) -> None:
        assert generate_slug("---Hello World---") == "hello-world"

    def test_long_title_truncated(self) -> None:
        long_title = "a" * 300
        slug = generate_slug(long_title)
        assert len(slug) <= 200

    def test_empty_title_returns_content(self) -> None:
        # All non-ASCII characters stripped => empty => fallback
        assert generate_slug("") == "content"

    def test_all_special_chars_returns_content(self) -> None:
        assert generate_slug("!!!@@@###") == "content"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TestValidateTitle:
    """Tests for title validation."""

    def test_valid_title(self) -> None:
        validate_title("A valid title")

    def test_empty_title_raises(self) -> None:
        with pytest.raises(CMSError, match="Title too short"):
            validate_title("")

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(CMSError, match="Title too long"):
            validate_title("x" * 301)

    def test_title_at_max_length(self) -> None:
        validate_title("x" * 300)

    def test_single_char_title(self) -> None:
        validate_title("A")


class TestValidateBody:
    """Tests for body validation."""

    def test_valid_body(self) -> None:
        validate_body("Some content here.")

    def test_empty_body_raises(self) -> None:
        with pytest.raises(CMSError, match="Body is required"):
            validate_body("")

    def test_whitespace_only_body_raises(self) -> None:
        with pytest.raises(CMSError, match="Body is required"):
            validate_body("   \n\t  ")

    def test_body_too_long_raises(self) -> None:
        with pytest.raises(CMSError, match="Body too long"):
            validate_body("x" * 100_001)

    def test_body_at_max_length(self) -> None:
        validate_body("x" * 100_000)


class TestValidateContentType:
    """Tests for content type validation."""

    def test_valid_types(self) -> None:
        for ct in ("page", "blog_post", "success_story", "announcement", "faq"):
            validate_content_type(ct)

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(InvalidContentTypeError):
            validate_content_type("newsletter")


class TestValidateSummary:
    """Tests for summary validation."""

    def test_none_summary_ok(self) -> None:
        validate_summary(None)

    def test_valid_summary(self) -> None:
        validate_summary("A short summary.")

    def test_summary_too_long_raises(self) -> None:
        with pytest.raises(CMSError, match="Summary too long"):
            validate_summary("x" * 501)

    def test_summary_at_max_length(self) -> None:
        validate_summary("x" * 500)


class TestValidateTags:
    """Tests for tags validation."""

    def test_none_tags_ok(self) -> None:
        validate_tags(None)

    def test_empty_list_ok(self) -> None:
        validate_tags([])

    def test_valid_tags(self) -> None:
        validate_tags(["adoption", "dogs", "cats"])

    def test_too_many_tags_raises(self) -> None:
        with pytest.raises(CMSError, match="Too many tags"):
            validate_tags([f"tag-{i}" for i in range(21)])

    def test_tag_too_long_raises(self) -> None:
        with pytest.raises(CMSError, match="Invalid tag"):
            validate_tags(["x" * 51])

    def test_non_string_tag_raises(self) -> None:
        with pytest.raises(CMSError, match="Invalid tag"):
            validate_tags([123])


# ---------------------------------------------------------------------------
# create_content
# ---------------------------------------------------------------------------


class TestCreateContent:
    """Tests for content creation."""

    @pytest.fixture()
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        # _ensure_unique_slug: no existing slug
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock
        return db

    @pytest.mark.asyncio()
    async def test_creates_content_as_draft(self, mock_db: AsyncMock) -> None:
        content = await create_content(
            content_type="blog_post",
            title="Test Post",
            body="<p>Hello world</p>",
            db=mock_db,
        )
        assert content.content_type == "blog_post"
        assert content.title == "Test Post"
        assert content.slug == "test-post"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_creates_with_all_optional_fields(self, mock_db: AsyncMock) -> None:
        author_id = uuid4()
        content = await create_content(
            content_type="page",
            title="About Us",
            body="<p>About</p>",
            summary="About the shelter",
            featured_image_url="https://example.com/img.jpg",
            meta_description="About page",
            tags=["about", "shelter"],
            author_id=author_id,
            sort_order=5,
            db=mock_db,
        )
        assert content.summary == "About the shelter"
        assert content.tags == ["about", "shelter"]
        assert content.author_id == author_id
        assert content.sort_order == 5

    @pytest.mark.asyncio()
    async def test_rejects_invalid_content_type(self, mock_db: AsyncMock) -> None:
        with pytest.raises(InvalidContentTypeError):
            await create_content(
                content_type="newsletter",
                title="Test",
                body="body",
                db=mock_db,
            )

    @pytest.mark.asyncio()
    async def test_rejects_empty_title(self, mock_db: AsyncMock) -> None:
        with pytest.raises(CMSError, match="Title too short"):
            await create_content(
                content_type="page",
                title="",
                body="body",
                db=mock_db,
            )

    @pytest.mark.asyncio()
    async def test_rejects_empty_body(self, mock_db: AsyncMock) -> None:
        with pytest.raises(CMSError, match="Body is required"):
            await create_content(
                content_type="page",
                title="Title",
                body="",
                db=mock_db,
            )


# ---------------------------------------------------------------------------
# get_content_by_id
# ---------------------------------------------------------------------------


class TestGetContentById:
    """Tests for fetching content by ID."""

    @pytest.mark.asyncio()
    async def test_returns_content_when_found(self) -> None:
        content_id = uuid4()
        mock_content = MagicMock()
        mock_content.id = content_id

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_content
        db.execute.return_value = result

        found = await get_content_by_id(content_id, db)
        assert found.id == content_id

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_missing(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ContentNotFoundError):
            await get_content_by_id(uuid4(), db)


# ---------------------------------------------------------------------------
# get_content_by_slug
# ---------------------------------------------------------------------------


class TestGetContentBySlug:
    """Tests for fetching published content by slug."""

    @pytest.mark.asyncio()
    async def test_returns_published_content(self) -> None:
        mock_content = MagicMock()
        mock_content.slug = "about-us"
        mock_content.status = "published"

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_content
        db.execute.return_value = result

        found, is_fallback = await get_content_by_slug("about-us", db)
        assert found.slug == "about-us"
        assert is_fallback is False

    @pytest.mark.asyncio()
    async def test_raises_not_found_for_missing_slug(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ContentNotFoundError):
            await get_content_by_slug("nonexistent", db)


# ---------------------------------------------------------------------------
# list_content
# ---------------------------------------------------------------------------


class TestListContent:
    """Tests for listing content with filters."""

    @pytest.mark.asyncio()
    async def test_returns_items_and_total(self) -> None:
        mock_items = [MagicMock(), MagicMock()]

        db = AsyncMock()
        # First execute: items query
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = mock_items
        # Second execute: count query
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        db.execute.side_effect = [items_result, count_result]

        items, total = await list_content(db)
        assert len(items) == 2
        assert total == 2

    @pytest.mark.asyncio()
    async def test_filters_by_content_type(self) -> None:
        db = AsyncMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.side_effect = [items_result, count_result]

        _items, total = await list_content(db, content_type="blog_post")
        assert total == 0

    @pytest.mark.asyncio()
    async def test_rejects_invalid_content_type_filter(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidContentTypeError):
            await list_content(db, content_type="invalid")


# ---------------------------------------------------------------------------
# list_public_content
# ---------------------------------------------------------------------------


class TestListPublicContent:
    """Tests for listing published content."""

    @pytest.mark.asyncio()
    async def test_delegates_with_published_status(self) -> None:
        db = AsyncMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.side_effect = [items_result, count_result]

        _items, total = await list_public_content(db)
        assert total == 0


# ---------------------------------------------------------------------------
# update_content
# ---------------------------------------------------------------------------


class TestUpdateContent:
    """Tests for content updates."""

    @pytest.fixture()
    def mock_db_with_content(self) -> tuple[AsyncMock, MagicMock]:
        content = MagicMock()
        content.id = uuid4()
        content.title = "Original Title"
        content.slug = "original-title"
        content.body = "<p>Original</p>"
        content.summary = "Original summary"
        content.tags = ["old"]
        content.sort_order = 0

        db = AsyncMock()
        # get_content_by_id query
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = content
        # _ensure_unique_slug query
        slug_result = MagicMock()
        slug_result.scalar_one_or_none.return_value = None

        db.execute.side_effect = [get_result, slug_result]
        return db, content

    @pytest.mark.asyncio()
    async def test_updates_title_and_regenerates_slug(
        self, mock_db_with_content: tuple[AsyncMock, MagicMock]
    ) -> None:
        db, content = mock_db_with_content
        result = await update_content(
            content_id=content.id,
            title="New Title",
            db=db,
        )
        assert result.title == "New Title"
        assert result.slug == "new-title"

    @pytest.mark.asyncio()
    async def test_updates_body(self) -> None:
        content = MagicMock()
        content.id = uuid4()
        content.body = "<p>Original</p>"
        db = AsyncMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = content
        db.execute.return_value = get_result

        await update_content(
            content_id=content.id,
            body="<p>Updated body</p>",
            db=db,
        )
        assert content.body == "<p>Updated body</p>"

    @pytest.mark.asyncio()
    async def test_updates_sort_order(self) -> None:
        content = MagicMock()
        content.id = uuid4()
        content.sort_order = 0
        db = AsyncMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = content
        db.execute.return_value = get_result

        await update_content(
            content_id=content.id,
            sort_order=10,
            db=db,
        )
        assert content.sort_order == 10

    @pytest.mark.asyncio()
    async def test_rejects_invalid_title(
        self, mock_db_with_content: tuple[AsyncMock, MagicMock]
    ) -> None:
        db, content = mock_db_with_content
        with pytest.raises(CMSError, match="Title too long"):
            await update_content(
                content_id=content.id,
                title="x" * 301,
                db=db,
            )


# ---------------------------------------------------------------------------
# change_content_status
# ---------------------------------------------------------------------------


class TestChangeContentStatus:
    """Tests for status transitions."""

    def _make_db_with_content(self, current_status: str) -> tuple[AsyncMock, MagicMock]:
        content = MagicMock()
        content.id = uuid4()
        content.status = current_status
        content.published_at = None

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = content
        db.execute.return_value = result
        return db, content

    @pytest.mark.asyncio()
    async def test_draft_to_published(self) -> None:
        db, content = self._make_db_with_content("draft")
        result = await change_content_status(
            content_id=content.id,
            new_status="published",
            db=db,
        )
        assert result.status == "published"
        assert result.published_at is not None

    @pytest.mark.asyncio()
    async def test_published_to_archived(self) -> None:
        db, content = self._make_db_with_content("published")
        result = await change_content_status(
            content_id=content.id,
            new_status="archived",
            db=db,
        )
        assert result.status == "archived"

    @pytest.mark.asyncio()
    async def test_published_to_draft(self) -> None:
        db, content = self._make_db_with_content("published")
        result = await change_content_status(
            content_id=content.id,
            new_status="draft",
            db=db,
        )
        assert result.status == "draft"

    @pytest.mark.asyncio()
    async def test_archived_to_draft(self) -> None:
        db, content = self._make_db_with_content("archived")
        result = await change_content_status(
            content_id=content.id,
            new_status="draft",
            db=db,
        )
        assert result.status == "draft"

    @pytest.mark.asyncio()
    async def test_archived_to_published_rejected(self) -> None:
        db, content = self._make_db_with_content("archived")
        with pytest.raises(InvalidStatusTransitionError):
            await change_content_status(
                content_id=content.id,
                new_status="published",
                db=db,
            )

    @pytest.mark.asyncio()
    async def test_draft_to_draft_rejected(self) -> None:
        db, content = self._make_db_with_content("draft")
        with pytest.raises(InvalidStatusTransitionError):
            await change_content_status(
                content_id=content.id,
                new_status="draft",
                db=db,
            )

    @pytest.mark.asyncio()
    async def test_published_at_not_overwritten_on_republish(self) -> None:
        db, content = self._make_db_with_content("draft")
        original_time = datetime(2025, 1, 1, tzinfo=UTC)
        content.published_at = original_time
        await change_content_status(
            content_id=content.id,
            new_status="published",
            db=db,
        )
        # published_at should not be overwritten since it was already set
        assert content.published_at == original_time


# ---------------------------------------------------------------------------
# delete_content
# ---------------------------------------------------------------------------


class TestDeleteContent:
    """Tests for content deletion."""

    @pytest.mark.asyncio()
    async def test_deletes_existing_content(self) -> None:
        content = MagicMock()
        content.id = uuid4()

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = content
        db.execute.return_value = result

        await delete_content(content.id, db)
        db.delete.assert_awaited_once_with(content)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_raises_not_found_for_missing(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(ContentNotFoundError):
            await delete_content(uuid4(), db)


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for CMS error hierarchy."""

    def test_content_not_found_error(self) -> None:
        err = ContentNotFoundError("some-slug")
        assert err.message == "Content not found"
        assert "some-slug" in err.details
        assert err.identifier == "some-slug"

    def test_slug_conflict_error(self) -> None:
        err = SlugConflictError("test-slug")
        assert err.message == "Slug already exists"
        assert "test-slug" in err.details
        assert err.slug == "test-slug"

    def test_invalid_content_type_error(self) -> None:
        err = InvalidContentTypeError("newsletter")
        assert err.message == "Invalid content type"

    def test_invalid_status_transition_error(self) -> None:
        err = InvalidStatusTransitionError("draft", "archived_deleted")
        assert "draft" in err.details
        assert "archived_deleted" in err.details
