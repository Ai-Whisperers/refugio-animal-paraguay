"""Integration tests for the community feed endpoint.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_community_feed.py
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/community/feed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_returns_200(client: AsyncClient) -> None:
    """Feed endpoint returns 200 with correct envelope shape."""
    response = await client.get("/api/community/feed")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert "has_next" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_default_page_is_1(client: AsyncClient) -> None:
    response = await client.get("/api/community/feed")
    assert response.status_code == 200
    assert response.json()["page"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_page_size_respected(client: AsyncClient) -> None:
    response = await client.get("/api/community/feed?page_size=5")
    assert response.status_code == 200
    body = response.json()
    assert body["page_size"] == 5
    assert len(body["items"]) <= 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_page_size_capped_at_50(client: AsyncClient) -> None:
    response = await client.get("/api/community/feed?page_size=9999")
    assert response.status_code == 200
    body = response.json()
    assert body["page_size"] == 50


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_invalid_page_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/community/feed?page=0")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_type_filter_animals_only(client: AsyncClient) -> None:
    response = await client.get("/api/community/feed?types=animal")
    assert response.status_code == 200
    body = response.json()
    for item in body["items"]:
        assert item["event_type"] == "animal"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_type_filter_unknown_type_ignored(client: AsyncClient) -> None:
    """Unknown type values are silently filtered — endpoint returns 200."""
    response = await client.get("/api/community/feed?types=unknown_type")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_items_have_required_fields(client: AsyncClient) -> None:
    """Each feed item has the required response fields."""
    response = await client.get("/api/community/feed")
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert "id" in item
        assert "event_type" in item
        assert "title" in item
        assert "preview" in item
        assert "timestamp" in item
        assert "detail_url" in item
        assert "badge" in item
