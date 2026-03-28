"""Unit tests for homepage dynamic content endpoints.

Tests:
  GET /api/public/content/homepage/team
  GET /api/public/content/homepage/testimonials
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api.homepage_content import router

# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Return an async mock database session."""
    return AsyncMock()


def _make_cms_entry(
    slug: str, body: str, status: str = "published", language: str = "es"
) -> MagicMock:
    """Create a mock CMSContent row."""
    entry = MagicMock()
    entry.slug = slug
    entry.body = body
    entry.status = status
    entry.language = language
    entry.id = uuid4()
    return entry


# ---------------------------------------------------------------------------
# Team endpoint tests
# ---------------------------------------------------------------------------


class TestGetHomepageTeam:
    """Tests for GET /api/public/content/homepage/team."""

    @pytest.mark.asyncio
    async def test_returns_team_from_cms(self) -> None:
        """When CMS has a published entry, return parsed team members."""
        team_data = [
            {"name": "Ana Rodriguez", "role": "Directora", "image_url": None},
            {"name": "Carlos Benitez", "role": "Veterinario"},
        ]
        entry = _make_cms_entry("homepage-team", json.dumps(team_data))

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/team?lang=es")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "cms"
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Ana Rodriguez"
        assert data["items"][0]["role"] == "Directora"
        assert data["items"][1]["name"] == "Carlos Benitez"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_cms_entry(self) -> None:
        """When no CMS entry exists, return empty list with 'default' source."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/team")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "default"
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_invalid_json(self) -> None:
        """When CMS body is not valid JSON, return empty list gracefully."""
        entry = _make_cms_entry("homepage-team", "this is not json")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/team")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "default"
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_cache_control_header(self) -> None:
        """Response must include Cache-Control: public, max-age=300."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/team")
                _app.dependency_overrides.clear()

        assert "public, max-age=300" in response.headers.get("cache-control", "")

    @pytest.mark.asyncio
    async def test_skips_non_dict_items(self) -> None:
        """Non-dict items in the JSON array are silently skipped."""
        body = json.dumps(
            [
                {"name": "Ana", "role": "Director"},
                "invalid-string-item",
                42,
                {"name": "Carlos", "role": "Vet"},
            ]
        )
        entry = _make_cms_entry("homepage-team", body)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/team")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2


# ---------------------------------------------------------------------------
# Testimonials endpoint tests
# ---------------------------------------------------------------------------


class TestGetHomepageTestimonials:
    """Tests for GET /api/public/content/homepage/testimonials."""

    @pytest.mark.asyncio
    async def test_returns_testimonials_from_cms(self) -> None:
        """When CMS has published testimonials, return parsed list."""
        testimonial_data = [
            {"quote": "Great shelter!", "name": "Maria", "animal": "Max (perro)"},
            {"quote": "Love Mia!", "name": "Sofia", "animal": "Mia (gata)"},
        ]
        entry = _make_cms_entry("homepage-testimonials", json.dumps(testimonial_data))

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/testimonials?lang=es")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "cms"
        assert len(data["items"]) == 2
        assert data["items"][0]["quote"] == "Great shelter!"
        assert data["items"][0]["name"] == "Maria"
        assert data["items"][0]["animal"] == "Max (perro)"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_cms_entry(self) -> None:
        """When no CMS entry exists, return empty list."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/testimonials")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "default"
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_non_array_json(self) -> None:
        """When CMS body is a JSON object (not array), return empty list."""
        entry = _make_cms_entry(
            "homepage-testimonials",
            json.dumps({"not": "an array"}),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/testimonials")
                _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "default"
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_cache_control_header(self) -> None:
        """Testimonials response must include Cache-Control header."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async with AsyncClient(
            transport=ASGITransport(app=_app),
            base_url="http://test",
        ) as client:
            with patch("src.api.homepage_content.get_db", return_value=mock_db):
                _app.dependency_overrides[
                    __import__("src.db.session", fromlist=["get_db"]).get_db
                ] = lambda: mock_db
                response = await client.get("/api/public/content/homepage/testimonials")
                _app.dependency_overrides.clear()

        assert "public, max-age=300" in response.headers.get("cache-control", "")
