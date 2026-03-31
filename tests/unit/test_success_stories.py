"""Unit tests for src/api/success_stories.py."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from src.api.success_stories import (
    _serialise,
    create_story,
    delete_story,
    get_story_public,
    list_stories_admin,
    list_stories_public,
    update_story,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_story(**overrides):
    """Create a mock SuccessStory object."""
    defaults = {
        "id": uuid4(),
        "title": "Luna encontro su hogar",
        "animal_id": uuid4(),
        "adopter_name": "Maria Garcia",
        "story_text": "Luna fue rescatada de la calle y ahora vive feliz con su nueva familia.",
        "quote": "Luna cambio nuestras vidas",
        "photo_url": "https://example.com/luna.jpg",
        "published_at": datetime(2026, 3, 20, 10, 0, 0, tzinfo=UTC),
        "is_featured": False,
        "is_deleted": False,
        "created_at": datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 3, 20, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def _mock_db_returning(obj):
    """Create a mock db session where db.get returns obj."""
    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=obj)
    return mock_db


# ---------------------------------------------------------------------------
# Test _serialise
# ---------------------------------------------------------------------------


class TestSerialise:
    """Tests for the _serialise helper."""

    def test_serialises_all_fields(self) -> None:
        sid = uuid4()
        story = _make_story(id=sid, title="Test Story")
        result = _serialise(story)

        assert result["id"] == sid
        assert result["title"] == "Test Story"
        assert result["adopter_name"] == "Maria Garcia"
        assert isinstance(result["published_at"], str)
        assert isinstance(result["created_at"], str)

    def test_none_published_at(self) -> None:
        story = _make_story(published_at=None)
        result = _serialise(story)
        assert result["published_at"] is None


# ---------------------------------------------------------------------------
# Test create_story
# ---------------------------------------------------------------------------


class TestCreateStory:
    """Tests for the POST endpoint."""

    @pytest.mark.asyncio
    async def test_creates_story_successfully(self) -> None:
        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime(2026, 3, 20, tzinfo=UTC)
            obj.updated_at = datetime(2026, 3, 20, tzinfo=UTC)
            obj.published_at = None

        mock_db.refresh = fake_refresh

        payload = MagicMock()
        payload.title = "New Story"
        payload.animal_id = None
        payload.adopter_name = "Juan"
        payload.story_text = "A wonderful adoption story that changed lives."
        payload.quote = None
        payload.photo_url = None
        payload.is_featured = False
        payload.publish = False

        result = await create_story(payload=payload, db=mock_db)

        assert mock_db.add.called
        assert mock_db.flush.called
        assert result["title"] == "New Story"

    @pytest.mark.asyncio
    async def test_publishes_when_flag_set(self) -> None:
        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime(2026, 3, 20, tzinfo=UTC)
            obj.updated_at = datetime(2026, 3, 20, tzinfo=UTC)

        mock_db.refresh = fake_refresh

        payload = MagicMock()
        payload.title = "Published Story"
        payload.animal_id = None
        payload.adopter_name = "Ana"
        payload.story_text = "Published immediately when created."
        payload.quote = None
        payload.photo_url = None
        payload.is_featured = True
        payload.publish = True

        result = await create_story(payload=payload, db=mock_db)
        assert mock_db.add.called
        assert result["published_at"] is not None


# ---------------------------------------------------------------------------
# Test list_stories_admin
# ---------------------------------------------------------------------------


class TestListStoriesAdmin:
    """Tests for the admin GET endpoint."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        s1 = _make_story(title="Story 1")
        s2 = _make_story(title="Story 2")

        mock_db = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2
        mock_select_result = MagicMock()
        mock_select_result.scalars.return_value.all.return_value = [s1, s2]
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_select_result])

        result = await list_stories_admin(page=1, page_size=20, db=mock_db)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1


# ---------------------------------------------------------------------------
# Test update_story
# ---------------------------------------------------------------------------


class TestUpdateStory:
    """Tests for the PUT endpoint."""

    @pytest.mark.asyncio
    async def test_updates_title(self) -> None:
        story = _make_story(title="Old Title")
        mock_db = _mock_db_returning(story)

        payload = MagicMock()
        payload.model_dump.return_value = {"title": "New Title"}

        await update_story(story_id=story.id, payload=payload, db=mock_db)
        assert story.title == "New Title"

    @pytest.mark.asyncio
    async def test_404_for_deleted_story(self) -> None:
        story = _make_story(is_deleted=True)
        mock_db = _mock_db_returning(story)

        payload = MagicMock()
        payload.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_story(story_id=story.id, payload=payload, db=mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_404_for_missing_story(self) -> None:
        mock_db = _mock_db_returning(None)

        payload = MagicMock()
        payload.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_story(story_id=uuid4(), payload=payload, db=mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_publish_sets_published_at(self) -> None:
        story = _make_story(published_at=None)
        mock_db = _mock_db_returning(story)

        payload = MagicMock()
        payload.model_dump.return_value = {"publish": True}

        await update_story(story_id=story.id, payload=payload, db=mock_db)
        assert story.published_at is not None

    @pytest.mark.asyncio
    async def test_unpublish_clears_published_at(self) -> None:
        story = _make_story(published_at=datetime(2026, 3, 20, tzinfo=UTC))
        mock_db = _mock_db_returning(story)

        payload = MagicMock()
        payload.model_dump.return_value = {"publish": False}

        await update_story(story_id=story.id, payload=payload, db=mock_db)
        assert story.published_at is None


# ---------------------------------------------------------------------------
# Test delete_story
# ---------------------------------------------------------------------------


class TestDeleteStory:
    """Tests for the DELETE endpoint."""

    @pytest.mark.asyncio
    async def test_soft_deletes_story(self) -> None:
        story = _make_story(is_deleted=False)
        mock_db = _mock_db_returning(story)

        await delete_story(story_id=story.id, db=mock_db)
        assert story.is_deleted is True

    @pytest.mark.asyncio
    async def test_404_for_already_deleted(self) -> None:
        story = _make_story(is_deleted=True)
        mock_db = _mock_db_returning(story)

        with pytest.raises(HTTPException) as exc_info:
            await delete_story(story_id=story.id, db=mock_db)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test public endpoints
# ---------------------------------------------------------------------------


class TestListStoriesPublic:
    """Tests for the public GET endpoint."""

    @pytest.mark.asyncio
    async def test_returns_published_stories(self) -> None:
        s1 = _make_story(title="Published Story")

        mock_db = AsyncMock()
        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_select = MagicMock()
        mock_select.scalars.return_value.all.return_value = [s1]
        mock_db.execute = AsyncMock(side_effect=[mock_count, mock_select])

        result = await list_stories_public(page=1, db=mock_db)

        assert result["total"] == 1
        assert result["page_size"] == 6


class TestGetStoryPublic:
    """Tests for the public GET /{id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_story(self) -> None:
        sid = uuid4()
        story = _make_story(id=sid, title="Detail Story")
        mock_db = _mock_db_returning(story)

        result = await get_story_public(story_id=sid, db=mock_db)
        assert result["id"] == sid

    @pytest.mark.asyncio
    async def test_404_for_deleted(self) -> None:
        story = _make_story(is_deleted=True)
        mock_db = _mock_db_returning(story)

        with pytest.raises(HTTPException) as exc_info:
            await get_story_public(story_id=story.id, db=mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_404_for_missing(self) -> None:
        mock_db = _mock_db_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_story_public(story_id=uuid4(), db=mock_db)
        assert exc_info.value.status_code == 404
