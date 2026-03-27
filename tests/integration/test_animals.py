"""Integration tests for the Animals CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_animals.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# POST /animals
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_animal_returns_201(client: AsyncClient) -> None:
    response = await client.post("/animals", json={"name": "Bolt", "species": "dog"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Bolt"
    assert body["species"] == "dog"
    assert body["status"] == "intake"
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_animal_with_all_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/animals",
        json={
            "name": "Luna",
            "species": "cat",
            "status": "available",
            "birth_date": "2022-06-01",
            "description": "Friendly indoor cat",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["species"] == "cat"
    assert body["status"] == "available"
    assert body["birth_date"] == "2022-06-01"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_animal_invalid_species_returns_422(client: AsyncClient) -> None:
    response = await client.post("/animals", json={"name": "Rex", "species": "fish"})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_animal_missing_name_returns_422(client: AsyncClient) -> None:
    response = await client.post("/animals", json={"species": "dog"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /animals
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animals_returns_200(client: AsyncClient) -> None:
    response = await client.get("/animals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animals_filter_by_species(client: AsyncClient) -> None:
    # Create a known animal
    await client.post("/animals", json={"name": "FilterDog", "species": "dog"})
    response = await client.get("/animals?species=dog")
    assert response.status_code == 200
    body = response.json()
    assert all(a["species"] == "dog" for a in body)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animals_filter_by_status(client: AsyncClient) -> None:
    await client.post(
        "/animals", json={"name": "FilterCat", "species": "cat", "status": "available"}
    )
    response = await client.get("/animals?status=available")
    assert response.status_code == 200
    assert all(a["status"] == "available" for a in response.json())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animals_pagination(client: AsyncClient) -> None:
    response = await client.get("/animals?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()) <= 2


# ---------------------------------------------------------------------------
# GET /animals/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_animal_returns_200(client: AsyncClient) -> None:
    create = await client.post("/animals", json={"name": "Fetch", "species": "dog"})
    animal_id = create.json()["id"]

    response = await client.get(f"/animals/{animal_id}")
    assert response.status_code == 200
    assert response.json()["id"] == animal_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_animal_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/animals/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["message"] == "Animal not found"


# ---------------------------------------------------------------------------
# PATCH /animals/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_updates_fields(client: AsyncClient) -> None:
    create = await client.post("/animals", json={"name": "Patch", "species": "dog"})
    animal_id = create.json()["id"]

    response = await client.patch(
        f"/animals/{animal_id}", json={"status": "available", "name": "Updated"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["name"] == "Updated"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.patch(f"/animals/{uuid4()}", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_empty_payload_leaves_unchanged(client: AsyncClient) -> None:
    create = await client.post("/animals", json={"name": "NoChange", "species": "cat"})
    animal_id = create.json()["id"]

    response = await client.patch(f"/animals/{animal_id}", json={})
    assert response.status_code == 200
    assert response.json()["name"] == "NoChange"


# ---------------------------------------------------------------------------
# DELETE /animals/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_animal_returns_204(client: AsyncClient) -> None:
    create = await client.post("/animals", json={"name": "Delete Me", "species": "dog"})
    animal_id = create.json()["id"]

    response = await client.delete(f"/animals/{animal_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_animal_then_get_returns_404(client: AsyncClient) -> None:
    create = await client.post("/animals", json={"name": "Gone", "species": "dog"})
    animal_id = create.json()["id"]

    await client.delete(f"/animals/{animal_id}")
    response = await client.get(f"/animals/{animal_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_animal_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"/animals/{uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /animals/{id} — Status transition validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_valid_status_transition_succeeds(client: AsyncClient) -> None:
    """intake -> available is a valid transition."""
    create = await client.post("/animals", json={"name": "StatusTest", "species": "dog"})
    animal_id = create.json()["id"]
    assert create.json()["status"] == "intake"

    response = await client.patch(f"/animals/{animal_id}", json={"status": "available"})
    assert response.status_code == 200
    assert response.json()["status"] == "available"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_invalid_status_transition_returns_422(client: AsyncClient) -> None:
    """intake -> adopted is not a valid transition."""
    create = await client.post("/animals", json={"name": "BadTransition", "species": "cat"})
    animal_id = create.json()["id"]
    assert create.json()["status"] == "intake"

    response = await client.patch(f"/animals/{animal_id}", json={"status": "adopted"})
    assert response.status_code == 422
    body = response.json()
    error_text = (body.get("message") or body.get("detail") or "").lower()
    assert "intake" in error_text or "transicion" in error_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_deceased_is_terminal(client: AsyncClient) -> None:
    """Deceased animals cannot transition to any other status."""
    create = await client.post("/animals", json={"name": "Terminal", "species": "dog"})
    animal_id = create.json()["id"]

    # intake -> quarantine -> deceased
    await client.patch(f"/animals/{animal_id}", json={"status": "quarantine"})
    await client.patch(f"/animals/{animal_id}", json={"status": "deceased"})

    response = await client.patch(f"/animals/{animal_id}", json={"status": "available"})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_same_status_is_noop(client: AsyncClient) -> None:
    """Setting the same status should succeed (no-op)."""
    create = await client.post("/animals", json={"name": "SameStatus", "species": "dog"})
    animal_id = create.json()["id"]

    response = await client.patch(f"/animals/{animal_id}", json={"status": "intake"})
    assert response.status_code == 200
    assert response.json()["status"] == "intake"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_animal_multi_step_transition(client: AsyncClient) -> None:
    """Full lifecycle: intake -> available -> adopted."""
    create = await client.post("/animals", json={"name": "Lifecycle", "species": "cat"})
    animal_id = create.json()["id"]

    r1 = await client.patch(f"/animals/{animal_id}", json={"status": "available"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "available"

    r2 = await client.patch(f"/animals/{animal_id}", json={"status": "adopted"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "adopted"

    # adopted -> available (returned animal)
    r3 = await client.patch(f"/animals/{animal_id}", json={"status": "available"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "available"
