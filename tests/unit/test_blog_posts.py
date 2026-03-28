"""Unit tests for src/api/blog_posts.py."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from src.api.blog_posts import (
    _excerpt,
    _serialise,
    _slugify,
    create_post,
    delete_post,
    get_post_by_slug,
    list_latest_posts,
    list_posts_public,
    update_post,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_post(**overrides):
    """Create a mock BlogPost object."""
    defaults = {
        "id": uuid4(),
        "title": "Nuevo programa de vacunacion",
        "slug": "nuevo-programa-de-vacunacion",
        "body_html": "<p>Lanzamos un nuevo programa de vacunacion para animales rescatados.</p>",
        "author_id": uuid4(),
        "featured_image_url": "https://example.com/img.jpg",
        "tags": ["vacunacion", "salud"],
        "published_at": datetime(2026, 3, 20, 10, 0, 0, tzinfo=UTC),
        "is_published": True,
        "is_deleted": False,
        "created_at": datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 3, 20, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class TestSlugify:
    """Tests for _slugify helper."""

    def test_basic_slug(self) -> None:
        assert _slugify("Hello World") == "hello-world"

    def test_removes_special_chars(self) -> None:
        assert _slugify("Hello! @World #2026") == "hello-world-2026"

    def test_collapses_dashes(self) -> None:
        assert _slugify("hello---world") == "hello-world"

    def test_spanish_text(self) -> None:
        result = _slugify("Programa de Vacunacion 2026")
        assert result == "programa-de-vacunacion-2026"


class TestExcerpt:
    """Tests for _excerpt helper."""

    def test_strips_html_tags(self) -> None:
        result = _excerpt("<p>Hello <strong>world</strong></p>")
        assert "<" not in result
        assert result == "Hello world"

    def test_truncates_long_text(self) -> None:
        long_text = "<p>" + "x " * 200 + "</p>"
        result = _excerpt(long_text)
        assert len(result) <= 155  # 150 + "..."
        assert result.endswith("...")

    def test_short_text_not_truncated(self) -> None:
        result = _excerpt("<p>Short text</p>")
        assert result == "Short text"


class TestSerialise:
    """Tests for _serialise helper."""

    def test_serialises_all_fields(self) -> None:
        pid = uuid4()
        post = _make_post(id=pid)
        result = _serialise(post)

        assert result["id"] == pid
        assert result["slug"] == "nuevo-programa-de-vacunacion"
        assert "excerpt" in result
        assert isinstance(result["published_at"], str)

    def test_none_published_at(self) -> None:
        post = _make_post(published_at=None)
        result = _serialise(post)
        assert result["published_at"] is None

    def test_empty_tags(self) -> None:
        post = _make_post(tags=None)
        result = _serialise(post)
        assert result["tags"] == []


# ---------------------------------------------------------------------------
# Test create_post
# ---------------------------------------------------------------------------


class TestCreatePost:
    """Tests for the POST endpoint."""

    @pytest.mark.asyncio
    async def test_creates_post(self) -> None:
        mock_db = AsyncMock()
        # unique_slug calls db.execute for slug check
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_count)

        async def fake_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime(2026, 3, 20, tzinfo=UTC)
            obj.updated_at = datetime(2026, 3, 20, tzinfo=UTC)
            obj.published_at = None
            obj.is_published = False

        mock_db.refresh = fake_refresh

        payload = MagicMock()
        payload.title = "Test Post"
        payload.slug = None
        payload.body_html = "<p>Content</p>"
        payload.author_id = None
        payload.featured_image_url = None
        payload.tags = ["test"]
        payload.publish = False

        result = await create_post(payload=payload, db=mock_db)
        assert result["title"] == "Test Post"
        assert result["slug"] == "test-post"


# ---------------------------------------------------------------------------
# Test update_post
# ---------------------------------------------------------------------------


class TestUpdatePost:
    """Tests for the PUT endpoint."""

    @pytest.mark.asyncio
    async def test_updates_title(self) -> None:
        post = _make_post(title="Old")
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=post)

        payload = MagicMock()
        payload.model_dump.return_value = {"title": "New Title"}

        await update_post(post_id=post.id, payload=payload, db=mock_db)
        assert post.title == "New Title"

    @pytest.mark.asyncio
    async def test_404_for_deleted(self) -> None:
        post = _make_post(is_deleted=True)
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=post)

        payload = MagicMock()
        payload.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_post(post_id=post.id, payload=payload, db=mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_publish_sets_published_at(self) -> None:
        post = _make_post(is_published=False, published_at=None)
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=post)

        payload = MagicMock()
        payload.model_dump.return_value = {"publish": True}

        await update_post(post_id=post.id, payload=payload, db=mock_db)
        assert post.is_published is True
        assert post.published_at is not None


# ---------------------------------------------------------------------------
# Test delete_post
# ---------------------------------------------------------------------------


class TestDeletePost:
    """Tests for the DELETE endpoint."""

    @pytest.mark.asyncio
    async def test_soft_deletes(self) -> None:
        post = _make_post(is_deleted=False)
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=post)

        await delete_post(post_id=post.id, db=mock_db)
        assert post.is_deleted is True

    @pytest.mark.asyncio
    async def test_404_for_missing(self) -> None:
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await delete_post(post_id=uuid4(), db=mock_db)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test public endpoints
# ---------------------------------------------------------------------------


class TestListPostsPublic:
    """Tests for the public GET endpoint."""

    @pytest.mark.asyncio
    async def test_returns_posts(self) -> None:
        p1 = _make_post(title="Post 1")

        mock_db = AsyncMock()
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_select = MagicMock()
        mock_select.scalars.return_value.all.return_value = [p1]
        mock_db.execute = AsyncMock(side_effect=[mock_count, mock_select])

        result = await list_posts_public(page=1, db=mock_db)
        assert result["total"] == 1
        assert result["page_size"] == 10


class TestGetPostBySlug:
    """Tests for the public GET /{slug} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_post(self) -> None:
        post = _make_post(slug="test-slug")
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = post
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_post_by_slug(slug="test-slug", db=mock_db)
        assert result["slug"] == "test-slug"

    @pytest.mark.asyncio
    async def test_404_for_missing(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_post_by_slug(slug="nonexistent", db=mock_db)
        assert exc_info.value.status_code == 404


class TestListLatestPosts:
    """Tests for the GET /latest endpoint."""

    @pytest.mark.asyncio
    async def test_returns_latest(self) -> None:
        p1 = _make_post(title="Latest")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p1]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await list_latest_posts(db=mock_db)
        assert len(result) == 1
        assert result[0]["title"] == "Latest"
