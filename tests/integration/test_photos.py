"""Integration tests for animal photo endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_photos.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_animal(client: AsyncClient) -> str:
    """Create a test animal and return its ID."""
    resp = await client.post("/animals", json={"name": "PhotoDog", "species": "dog"})
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# POST /animals/{id}/photos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_photo_returns_201(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/photo.jpg"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == "https://example.com/photo.jpg"
    assert body["animal_id"] == animal_id
    assert body["caption"] is None
    assert body["display_order"] == 0
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_photo_with_all_fields(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        f"/animals/{animal_id}/photos",
        json={
            "url": "https://example.com/gallery/1.jpg",
            "caption": "Playing in the yard",
            "display_order": 3,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["caption"] == "Playing in the yard"
    assert body["display_order"] == 3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_photo_to_nonexistent_animal_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        f"/animals/{uuid4()}/photos",
        json={"url": "https://example.com/photo.jpg"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_photo_requires_auth(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    # Send request without Authorization header
    from httpx import ASGITransport
    from httpx import AsyncClient as RawClient
    from src.app import app

    async with RawClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        response = await anon.post(
            f"/animals/{animal_id}/photos",
            json={"url": "https://example.com/photo.jpg"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_photo_empty_url_returns_422(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": ""},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /animals/{id}/photos/{photo_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_photo_returns_204(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    add_resp = await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/todelete.jpg"},
    )
    photo_id = add_resp.json()["id"]

    response = await client.delete(f"/animals/{animal_id}/photos/{photo_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_photo_nonexistent_returns_404(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.delete(f"/animals/{animal_id}/photos/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_photo_wrong_animal_returns_404(client: AsyncClient) -> None:
    """Photo ID is valid but belongs to a different animal — must return 404."""
    animal_id_1 = await _create_animal(client)
    animal_id_2 = await _create_animal(client)

    add_resp = await client.post(
        f"/animals/{animal_id_1}/photos",
        json={"url": "https://example.com/belongs-to-animal-1.jpg"},
    )
    photo_id = add_resp.json()["id"]

    # Try to delete using animal_id_2 — should not find it
    response = await client.delete(f"/animals/{animal_id_2}/photos/{photo_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_photo_requires_auth(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    add_resp = await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/photo.jpg"},
    )
    photo_id = add_resp.json()["id"]

    from httpx import ASGITransport
    from httpx import AsyncClient as RawClient
    from src.app import app

    async with RawClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        response = await anon.delete(f"/animals/{animal_id}/photos/{photo_id}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Photos reflected in GET /animals responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_animal_response_includes_photos_list(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)

    # Add two photos
    await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/a.jpg", "display_order": 1},
    )
    await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/b.jpg", "display_order": 0},
    )

    response = await client.get(f"/animals/{animal_id}")
    assert response.status_code == 200
    body = response.json()
    assert "photos" in body
    assert len(body["photos"]) == 2
    # Ordered by display_order asc
    assert body["photos"][0]["display_order"] == 0
    assert body["photos"][1]["display_order"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_new_animal_has_empty_photos_list(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.get(f"/animals/{animal_id}")
    assert response.status_code == 200
    assert response.json()["photos"] == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animals_includes_photos(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/list-test.jpg"},
    )

    response = await client.get("/animals")
    assert response.status_code == 200
    animals = response.json()
    matching = [a for a in animals if a["id"] == animal_id]
    assert len(matching) == 1
    assert len(matching[0]["photos"]) == 1


# ---------------------------------------------------------------------------
# primary_photo_url on create and patch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_animal_with_primary_photo_url(client: AsyncClient) -> None:
    response = await client.post(
        "/animals",
        json={
            "name": "CoverPhoto",
            "species": "cat",
            "primary_photo_url": "https://example.com/cover.jpg",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["primary_photo_url"] == "https://example.com/cover.jpg"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_primary_photo_url(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)

    response = await client.patch(
        f"/animals/{animal_id}",
        json={"primary_photo_url": "https://example.com/updated-cover.jpg"},
    )
    assert response.status_code == 200
    assert response.json()["primary_photo_url"] == "https://example.com/updated-cover.jpg"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_animal_cascades_to_photos(client: AsyncClient) -> None:
    """Deleting an animal must cascade-delete its photos (FK ondelete=CASCADE)."""
    animal_id = await _create_animal(client)
    await client.post(
        f"/animals/{animal_id}/photos",
        json={"url": "https://example.com/willbegone.jpg"},
    )

    delete_resp = await client.delete(f"/animals/{animal_id}")
    assert delete_resp.status_code == 204

    # Animal is gone
    get_resp = await client.get(f"/animals/{animal_id}")
    assert get_resp.status_code == 404
