"""Integration tests for the Vet Visits CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_vet_visits.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_animal(client: AsyncClient) -> str:
    """Create an animal and return its ID."""
    response = await client.post("/animals", json={"name": "TestAnimal", "species": "dog"})
    assert response.status_code == 201
    return response.json()["id"]


async def _create_visit(client: AsyncClient, animal_id: str) -> dict:
    """Create a vet visit and return its full body."""
    response = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={
            "veterinarian_name": "Dr. Rodriguez",
            "visit_type": "checkup",
            "visit_status": "completed",
            "reason": "Annual checkup",
            "weight_kg": 12.5,
            "temperature_celsius": 38.5,
        },
    )
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# POST /animals/{animal_id}/vet-visits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_vet_visit_returns_201(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    body = await _create_visit(client, animal_id)
    assert body["veterinarian_name"] == "Dr. Rodriguez"
    assert body["visit_type"] == "checkup"
    assert body["visit_status"] == "completed"
    assert body["weight_kg"] == 12.5
    assert body["animal_id"] == animal_id
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_vet_visit_minimal_fields(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={"veterinarian_name": "Dr. Lopez"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["veterinarian_name"] == "Dr. Lopez"
    assert body["visit_type"] == "checkup"  # default
    assert body["visit_status"] == "scheduled"  # default


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_vet_visit_missing_vet_name_returns_422(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={"visit_type": "emergency"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_vet_visit_nonexistent_animal_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    response = await client.post(
        f"/animals/{fake_id}/vet-visits",
        json={"veterinarian_name": "Dr. X"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /animals/{animal_id}/vet-visits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_vet_visits_returns_paginated(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    await _create_visit(client, animal_id)
    await _create_visit(client, animal_id)

    response = await client.get(f"/animals/{animal_id}/vet-visits")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 2
    assert body["page"] == 1
    assert body["page_size"] == 20


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_vet_visits_pagination(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    for _ in range(3):
        await _create_visit(client, animal_id)

    response = await client.get(
        f"/animals/{animal_id}/vet-visits?page=1&page_size=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_vet_visits_nonexistent_animal_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    response = await client.get(f"/animals/{fake_id}/vet-visits")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /animals/{animal_id}/vet-visits/{visit_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_vet_visit_by_id(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    created = await _create_visit(client, animal_id)
    visit_id = created["id"]

    response = await client.get(f"/animals/{animal_id}/vet-visits/{visit_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == visit_id
    assert body["veterinarian_name"] == "Dr. Rodriguez"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_vet_visit_nonexistent_returns_404(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    fake_id = str(uuid4())
    response = await client.get(f"/animals/{animal_id}/vet-visits/{fake_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /animals/{animal_id}/vet-visits/{visit_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_vet_visit(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    created = await _create_visit(client, animal_id)
    visit_id = created["id"]

    response = await client.patch(
        f"/animals/{animal_id}/vet-visits/{visit_id}",
        json={"notes": "Follow-up needed in 2 weeks", "weight_kg": 13.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["notes"] == "Follow-up needed in 2 weeks"
    assert body["weight_kg"] == 13.0
    # Unchanged fields stay the same
    assert body["veterinarian_name"] == "Dr. Rodriguez"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_vet_visit_nonexistent_returns_404(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    fake_id = str(uuid4())
    response = await client.patch(
        f"/animals/{animal_id}/vet-visits/{fake_id}",
        json={"notes": "test"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /animals/{animal_id}/vet-visits/{visit_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_vet_visit(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    created = await _create_visit(client, animal_id)
    visit_id = created["id"]

    response = await client.delete(f"/animals/{animal_id}/vet-visits/{visit_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/animals/{animal_id}/vet-visits/{visit_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_vet_visit_nonexistent_returns_404(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    fake_id = str(uuid4())
    response = await client.delete(f"/animals/{animal_id}/vet-visits/{fake_id}")
    assert response.status_code == 404
