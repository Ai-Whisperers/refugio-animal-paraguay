"""Integration tests for post-op checklist generation endpoint."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


async def _create_animal(client: AsyncClient) -> str:
    resp = await client.post("/animals", json={
        "name": f"Checklist-Dog-{uuid.uuid4().hex[:6]}",
        "species": "dog",
        "breed": "mixed",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_surgery(
    client: AsyncClient,
    animal_id: str,
    surgery_type: str = "spay",
) -> dict:
    resp = await client.post(f"/animals/{animal_id}/surgeries", json={
        "surgery_type": surgery_type,
        "surgery_status": "completed",
        "veterinarian_name": "Dr. Martinez",
        "scheduled_date": date.today().isoformat(),
        "performed_date": date.today().isoformat(),
    })
    assert resp.status_code == 201
    return resp.json()


class TestPostOpChecklistGeneration:
    """Tests for POST /surgeries/{id}/generate-checklist."""

    async def test_generate_spay_checklist(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="spay")

        resp = await client.post(f"/surgeries/{surgery['id']}/generate-checklist")
        assert resp.status_code == 201
        body = resp.json()
        assert body["surgery_id"] == surgery["id"]
        assert body["checks_created"] == 7  # spay has 7 checks
        assert len(body["check_ids"]) == 7

    async def test_generate_neuter_checklist(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="neuter")

        resp = await client.post(f"/surgeries/{surgery['id']}/generate-checklist")
        assert resp.status_code == 201
        body = resp.json()
        assert body["checks_created"] == 6  # neuter has 6 checks

    async def test_generate_emergency_checklist(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="emergency")

        resp = await client.post(f"/surgeries/{surgery['id']}/generate-checklist")
        assert resp.status_code == 201
        body = resp.json()
        assert body["checks_created"] == 9  # emergency has 9 checks

    async def test_generate_unknown_type_uses_default(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="other")

        resp = await client.post(f"/surgeries/{surgery['id']}/generate-checklist")
        assert resp.status_code == 201
        body = resp.json()
        assert body["checks_created"] == 5  # default has 5 checks

    async def test_checks_visible_in_listing(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="dental")

        await client.post(f"/surgeries/{surgery['id']}/generate-checklist")

        resp = await client.get(f"/surgeries/{surgery['id']}/post-op-checks")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5  # dental has 5 checks
        # All should be pending
        for check in body["items"]:
            assert check["check_status"] == "pending"
            assert check["notes"] is not None

    async def test_nonexistent_surgery_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/surgeries/{fake_id}/generate-checklist")
        assert resp.status_code == 404

    async def test_checks_ordered_by_scheduled_time(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id, surgery_type="spay")

        await client.post(f"/surgeries/{surgery['id']}/generate-checklist")

        resp = await client.get(f"/surgeries/{surgery['id']}/post-op-checks")
        items = resp.json()["items"]
        times = [item["scheduled_time"] for item in items]
        assert times == sorted(times), "Checks should be ordered by scheduled_time"
