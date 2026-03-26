"""Integration tests for the Adoption Requests workflow endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_adoption_requests.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_animal(client: AsyncClient, name: str = "TestAnimal") -> str:
    resp = await client.post("/animals", json={"name": name, "species": "dog"})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_adopter(client: AsyncClient) -> str:
    email = f"adopter-{uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/adopters", json={"full_name": "Test Adopter", "email": email}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# POST /adoption-requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_returns_201(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)

    response = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["animal_id"] == animal_id
    assert body["adopter_id"] == adopter_id
    assert body["status"] == "pending"
    assert body["submitted_at"] is not None
    assert body["decided_at"] is None
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_with_notes(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)

    response = await client.post(
        "/adoption-requests",
        json={
            "animal_id": animal_id,
            "adopter_id": adopter_id,
            "notes": "Large yard, experienced with dogs",
        },
    )
    assert response.status_code == 201
    assert response.json()["notes"] == "Large yard, experienced with dogs"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_unknown_animal_returns_404(
    client: AsyncClient,
) -> None:
    adopter_id = await _create_adopter(client)
    response = await client.post(
        "/adoption-requests",
        json={"animal_id": str(uuid4()), "adopter_id": adopter_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Animal not found"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_unknown_adopter_returns_404(
    client: AsyncClient,
) -> None:
    animal_id = await _create_animal(client)
    response = await client.post(
        "/adoption-requests",
        json={"animal_id": animal_id, "adopter_id": str(uuid4())},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Adopter not found"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_soft_deleted_adopter_returns_404(
    client: AsyncClient,
) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    await client.delete(f"/adopters/{adopter_id}")

    response = await client.post(
        "/adoption-requests",
        json={"animal_id": animal_id, "adopter_id": adopter_id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adoption_request_missing_fields_returns_422(
    client: AsyncClient,
) -> None:
    response = await client.post("/adoption-requests", json={"animal_id": str(uuid4())})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /adoption-requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adoption_requests_returns_200(client: AsyncClient) -> None:
    response = await client.get("/adoption-requests")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adoption_requests_filter_by_status(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )

    response = await client.get("/adoption-requests?status=pending")
    assert response.status_code == 200
    assert all(r["status"] == "pending" for r in response.json())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adoption_requests_filter_by_animal_id(client: AsyncClient) -> None:
    animal_id = await _create_animal(client, name="FilterAnimal")
    adopter_id = await _create_adopter(client)
    await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )

    response = await client.get(f"/adoption-requests?animal_id={animal_id}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all(r["animal_id"] == animal_id for r in body)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adoption_requests_pagination(client: AsyncClient) -> None:
    response = await client.get("/adoption-requests?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()) <= 2


# ---------------------------------------------------------------------------
# GET /adoption-requests/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_adoption_request_returns_200(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    response = await client.get(f"/adoption-requests/{request_id}")
    assert response.status_code == 200
    assert response.json()["id"] == request_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_adoption_request_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/adoption-requests/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Adoption request not found"


# ---------------------------------------------------------------------------
# PATCH /adoption-requests/{id}/status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_adoption_request(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "approved"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["decided_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_sets_animal_status_to_adopted(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "approved"}
    )

    animal_response = await client.get(f"/animals/{animal_id}")
    assert animal_response.json()["status"] == "adopted"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reject_adoption_request(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "rejected"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_pending_adoption_request(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "cancelled"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_transition_returns_422(client: AsyncClient) -> None:
    """Cannot go from pending → pending (no-op transition is invalid)."""
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "pending"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cannot_approve_already_rejected(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "rejected"}
    )
    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "approved"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cannot_transition_from_cancelled(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    create = await client.post(
        "/adoption-requests", json={"animal_id": animal_id, "adopter_id": adopter_id}
    )
    request_id = create.json()["id"]

    await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "cancelled"}
    )
    response = await client.patch(
        f"/adoption-requests/{request_id}/status", json={"status": "approved"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_status_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        f"/adoption-requests/{uuid4()}/status", json={"status": "approved"}
    )
    assert response.status_code == 404
