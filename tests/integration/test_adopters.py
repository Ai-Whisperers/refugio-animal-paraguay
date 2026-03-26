"""Integration tests for the Adopters CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_adopters.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _unique_email() -> str:
    """Return a unique email address to avoid 409 conflicts between tests."""
    return f"adopter-{uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# POST /adopters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adopter_returns_201(client: AsyncClient) -> None:
    response = await client.post(
        "/adopters", json={"full_name": "Juan Pérez", "email": _unique_email()}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Juan Pérez"
    assert "id" in body
    assert "deleted_at" not in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adopter_with_all_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/adopters",
        json={
            "full_name": "Ana García",
            "email": _unique_email(),
            "phone": "+595 21 555 1234",
            "address": "Calle Principal 123",
            "gdpr_consent_at": "2026-03-01T12:00:00Z",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["phone"] == "+595 21 555 1234"
    assert body["address"] == "Calle Principal 123"
    assert body["gdpr_consent_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adopter_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post("/adopters", json={"full_name": "First", "email": email})
    response = await client.post("/adopters", json={"full_name": "Second", "email": email})
    assert response.status_code == 409
    assert "already exists" in response.json()["message"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adopter_invalid_email_returns_422(client: AsyncClient) -> None:
    response = await client.post("/adopters", json={"full_name": "Juan", "email": "not-an-email"})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_adopter_missing_full_name_returns_422(
    client: AsyncClient,
) -> None:
    response = await client.post("/adopters", json={"email": _unique_email()})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /adopters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adopters_returns_200(client: AsyncClient) -> None:
    response = await client.get("/adopters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adopters_excludes_soft_deleted(client: AsyncClient) -> None:
    email = _unique_email()
    create = await client.post("/adopters", json={"full_name": "ToDelete", "email": email})
    adopter_id = create.json()["id"]

    await client.delete(f"/adopters/{adopter_id}")

    response = await client.get("/adopters")
    ids = [a["id"] for a in response.json()]
    assert adopter_id not in ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_adopters_pagination(client: AsyncClient) -> None:
    response = await client.get("/adopters?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()) <= 2


# ---------------------------------------------------------------------------
# GET /adopters/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_adopter_returns_200(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "Fetch Me", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    response = await client.get(f"/adopters/{adopter_id}")
    assert response.status_code == 200
    assert response.json()["id"] == adopter_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_adopter_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/adopters/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["message"] == "Adopter not found"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_adopter_soft_deleted_returns_404(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "Deleted One", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    await client.delete(f"/adopters/{adopter_id}")

    response = await client.get(f"/adopters/{adopter_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /adopters/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adopter_updates_fields(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "Original Name", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    response = await client.patch(
        f"/adopters/{adopter_id}",
        json={"full_name": "Updated Name", "phone": "+595 981 000 000"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Name"
    assert body["phone"] == "+595 981 000 000"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adopter_grants_gdpr_consent(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "No Consent Yet", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]
    assert create.json()["gdpr_consent_at"] is None

    response = await client.patch(
        f"/adopters/{adopter_id}", json={"gdpr_consent_at": "2026-03-25T10:00:00Z"}
    )
    assert response.status_code == 200
    assert response.json()["gdpr_consent_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adopter_empty_payload_leaves_unchanged(
    client: AsyncClient,
) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "No Change", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    response = await client.patch(f"/adopters/{adopter_id}", json={})
    assert response.status_code == 200
    assert response.json()["full_name"] == "No Change"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adopter_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.patch(f"/adopters/{uuid4()}", json={"full_name": "X"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /adopters/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_adopter_returns_204(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "Delete Me", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    response = await client.delete(f"/adopters/{adopter_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_adopter_is_soft_delete_not_hard(client: AsyncClient) -> None:
    """Record is not physically removed — only deleted_at is set."""
    create = await client.post(
        "/adopters", json={"full_name": "Soft Delete Me", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    await client.delete(f"/adopters/{adopter_id}")

    # Should be 404 via API (soft-deleted excluded)
    get_response = await client.get(f"/adopters/{adopter_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_adopter_twice_returns_404(client: AsyncClient) -> None:
    create = await client.post(
        "/adopters", json={"full_name": "Double Delete", "email": _unique_email()}
    )
    adopter_id = create.json()["id"]

    await client.delete(f"/adopters/{adopter_id}")
    response = await client.delete(f"/adopters/{adopter_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_adopter_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"/adopters/{uuid4()}")
    assert response.status_code == 404
