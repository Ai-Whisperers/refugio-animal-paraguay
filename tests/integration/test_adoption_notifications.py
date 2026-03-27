"""Integration tests for adoption notification event publishing.

Tests that adoption request API endpoints correctly function with
event_bus dependency injected.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_adoption_notifications.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_animal(client: AsyncClient, name: str = "NotifyAnimal") -> str:
    resp = await client.post("/animals", json={"name": name, "species": "dog"})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_adopter(client: AsyncClient) -> str:
    email = f"notify-adopter-{uuid4().hex[:8]}@example.com"
    resp = await client.post("/adopters", json={"full_name": "Notify Adopter", "email": email})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_adoption_request(
    client: AsyncClient,
) -> tuple[str, str, str]:
    """Create an animal, adopter, and pending adoption request."""
    animal_id = await _create_animal(client)
    adopter_id = await _create_adopter(client)
    resp = await client.post(
        "/adoption-requests",
        json={"animal_id": animal_id, "adopter_id": adopter_id},
    )
    assert resp.status_code == 201
    return resp.json()["id"], animal_id, adopter_id


class TestAdoptionRequestCreationWithEvents:
    """Tests that request creation works with event_bus dependency."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_request_returns_201(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        adopter_id = await _create_adopter(client)

        resp = await client.post(
            "/adoption-requests",
            json={"animal_id": animal_id, "adopter_id": adopter_id},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_request_has_all_fields(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        adopter_id = await _create_adopter(client)

        resp = await client.post(
            "/adoption-requests",
            json={"animal_id": animal_id, "adopter_id": adopter_id},
        )
        data = resp.json()
        assert "id" in data
        assert data["animal_id"] == animal_id
        assert data["adopter_id"] == adopter_id
        assert data["submitted_at"] is not None


class TestAdoptionStatusChangeWithEvents:
    """Tests that status changes work with event_bus dependency."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_approve_request(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_adoption_request(client)

        resp = await client.patch(
            f"/adoption-requests/{request_id}/status",
            json={"status": "approved"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["decided_at"] is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reject_request(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_adoption_request(client)

        resp = await client.patch(
            f"/adoption-requests/{request_id}/status",
            json={"status": "rejected"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_approve_sets_animal_adopted(self, client: AsyncClient) -> None:
        request_id, animal_id, _ = await _create_adoption_request(client)

        await client.patch(
            f"/adoption-requests/{request_id}/status",
            json={"status": "approved"},
        )

        animal_resp = await client.get(f"/animals/{animal_id}")
        assert animal_resp.json()["status"] == "adopted"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_transition_returns_422(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_adoption_request(client)

        # Reject first
        await client.patch(
            f"/adoption-requests/{request_id}/status",
            json={"status": "rejected"},
        )

        # Try approved from rejected (invalid)
        resp = await client.patch(
            f"/adoption-requests/{request_id}/status",
            json={"status": "approved"},
        )
        assert resp.status_code == 422
