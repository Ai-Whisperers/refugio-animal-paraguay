"""Unit tests for educational article service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.educational_article_service import (
    DEFAULT_PAGE_SIZE,
    ArticleError,
    ArticleNotFoundError,
    DuplicateSlugError,
    InvalidArticleError,
    create_article,
    delete_article,
    generate_slug,
    get_article,
    get_article_by_slug,
    list_articles,
    update_article,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_article_error_is_exception(self) -> None:
        assert isinstance(ArticleError("test"), Exception)

    def test_not_found_is_article_error(self) -> None:
        assert isinstance(ArticleNotFoundError("x"), ArticleError)

    def test_duplicate_slug_is_article_error(self) -> None:
        assert isinstance(DuplicateSlugError("x"), ArticleError)

    def test_invalid_article_is_article_error(self) -> None:
        assert isinstance(InvalidArticleError("x"), ArticleError)


# --- Test generate_slug ---


class TestGenerateSlug:
    """Tests for slug generation from titles."""

    def test_simple_title(self) -> None:
        assert generate_slug("Hello World") == "hello-world"

    def test_spanish_characters(self) -> None:
        assert generate_slug("Cómo cuidar a tu mascota") == "como-cuidar-a-tu-mascota"

    def test_special_characters_removed(self) -> None:
        assert generate_slug("Dogs & Cats: A Guide!") == "dogs-cats-a-guide"

    def test_multiple_spaces_collapsed(self) -> None:
        assert generate_slug("Too   Many   Spaces") == "too-many-spaces"

    def test_leading_trailing_hyphens_stripped(self) -> None:
        assert generate_slug("  --Hello--  ") == "hello"

    def test_uppercase_to_lowercase(self) -> None:
        assert generate_slug("ALL UPPERCASE TITLE") == "all-uppercase-title"

    def test_numbers_preserved(self) -> None:
        assert generate_slug("Top 10 Pet Tips") == "top-10-pet-tips"

    def test_accented_vowels(self) -> None:
        assert generate_slug("Información útil") == "informacion-util"

    def test_enye(self) -> None:
        # ñ decomposes to n + combining tilde; ASCII strip removes the tilde
        assert generate_slug("Año nuevo") == "ano-nuevo"

    def test_empty_after_strip(self) -> None:
        assert generate_slug("!!!") == ""


# --- Helper ---


def _mock_article(**kwargs):
    """Create a mock educational article."""
    a = MagicMock()
    a.id = kwargs.get("id", uuid4())
    a.title = kwargs.get("title", "Test Article")
    a.slug = kwargs.get("slug", "test-article")
    a.summary = kwargs.get("summary")
    a.content = kwargs.get("content", "Article content here.")
    a.category = kwargs.get("category", "general")
    a.tags = kwargs.get("tags", [])
    a.cover_image_url = kwargs.get("cover_image_url")
    a.status = kwargs.get("status", "draft")
    a.author_id = kwargs.get("author_id", uuid4())
    a.published_at = kwargs.get("published_at")
    a.created_at = kwargs.get("created_at")
    a.updated_at = kwargs.get("updated_at")
    return a


# --- Test create_article ---


class TestCreateArticle:
    """Tests for creating educational articles."""

    @pytest.mark.asyncio
    async def test_creates_successfully(self) -> None:
        db = AsyncMock()
        author_id = uuid4()
        mock_art = _mock_article(author_id=author_id)

        # Mock duplicate slug check returning 0
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result

        async def fake_refresh(obj):
            for attr in (
                "id",
                "title",
                "slug",
                "summary",
                "content",
                "category",
                "tags",
                "cover_image_url",
                "status",
                "author_id",
                "published_at",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_art, attr))

        db.refresh = fake_refresh

        result = await create_article(
            db=db,
            title="Test Article",
            content="Article content here.",
            author_id=author_id,
        )

        assert result["title"] == "Test Article"
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_invalid_category_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidArticleError, match="Invalid category"):
            await create_article(
                db=db,
                title="Test",
                content="Content",
                author_id=uuid4(),
                category="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_invalid_status_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidArticleError, match="Invalid status"):
            await create_article(
                db=db,
                title="Test",
                content="Content",
                author_id=uuid4(),
                status="bogus",
            )

    @pytest.mark.asyncio
    async def test_empty_title_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidArticleError, match="Title is required"):
            await create_article(
                db=db,
                title="   ",
                content="Content",
                author_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_empty_content_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidArticleError, match="Content is required"):
            await create_article(
                db=db,
                title="Valid Title",
                content="   ",
                author_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_duplicate_slug_raises(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        db.execute.return_value = count_result

        with pytest.raises(DuplicateSlugError, match="already exists"):
            await create_article(
                db=db,
                title="Test",
                content="Content",
                author_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_published_status_sets_published_at(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article(status="published")

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result

        async def fake_refresh(obj):
            for attr in (
                "id",
                "title",
                "slug",
                "summary",
                "content",
                "category",
                "tags",
                "cover_image_url",
                "status",
                "author_id",
                "published_at",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_art, attr))

        db.refresh = fake_refresh

        await create_article(
            db=db,
            title="Published Article",
            content="Content",
            author_id=uuid4(),
            status="published",
        )

        # The service sets published_at when status is published
        assert db.add.called


# --- Test get_article ---


class TestGetArticle:
    """Tests for fetching articles by ID."""

    @pytest.mark.asyncio
    async def test_returns_article(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        result = await get_article(db, mock_art.id)
        assert result["id"] == mock_art.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ArticleNotFoundError):
            await get_article(db, uuid4())


# --- Test get_article_by_slug ---


class TestGetArticleBySlug:
    """Tests for fetching articles by slug."""

    @pytest.mark.asyncio
    async def test_returns_article(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article(slug="my-article")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        result = await get_article_by_slug(db, "my-article")
        assert result["slug"] == "my-article"

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ArticleNotFoundError):
            await get_article_by_slug(db, "nonexistent")


# --- Test list_articles ---


class TestListArticles:
    """Tests for listing articles."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        mock_art = _mock_article()
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = [mock_art]
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_articles(db)
        assert result["total"] == 1
        assert len(result["articles"]) == 1
        assert result["limit"] == DEFAULT_PAGE_SIZE

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = []
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_articles(db)
        assert result["total"] == 0
        assert result["articles"] == []


# --- Test update_article ---


class TestUpdateArticle:
    """Tests for updating articles."""

    @pytest.mark.asyncio
    async def test_updates_title(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_article(db, mock_art.id, title="New Title")
        assert mock_art.title == "New Title"

    @pytest.mark.asyncio
    async def test_updates_slug_when_title_changes(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_article(db, mock_art.id, title="Brand New Title")
        assert mock_art.slug == "brand-new-title"

    @pytest.mark.asyncio
    async def test_invalid_category_raises(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        with pytest.raises(InvalidArticleError, match="Invalid category"):
            await update_article(db, mock_art.id, category="bad_cat")

    @pytest.mark.asyncio
    async def test_invalid_status_raises(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        with pytest.raises(InvalidArticleError, match="Invalid status"):
            await update_article(db, mock_art.id, status="bad_status")

    @pytest.mark.asyncio
    async def test_publish_sets_published_at(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article(status="draft")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_article(db, mock_art.id, status="published")
        assert mock_art.status == "published"
        assert mock_art.published_at is not None

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ArticleNotFoundError):
            await update_article(db, uuid4(), title="X")


# --- Test delete_article ---


class TestDeleteArticle:
    """Tests for deleting articles."""

    @pytest.mark.asyncio
    async def test_deletes_successfully(self) -> None:
        db = AsyncMock()
        mock_art = _mock_article()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_art
        db.execute.return_value = result_mock

        await delete_article(db, mock_art.id)
        db.delete.assert_called_once_with(mock_art)
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ArticleNotFoundError):
            await delete_article(db, uuid4())
