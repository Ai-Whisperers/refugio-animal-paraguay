"""Integration tests for surgery and post-op monitoring endpoints."""

import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


async def _create_animal(client: AsyncClient) -> str:
    resp = await client.post("/animals", json={
        "name": f"Surgery-Dog-{uuid.uuid4().hex[:6]}",
        "species": "dog",
        "breed": "mixed",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_surgery(client: AsyncClient, animal_id: str, **kwargs) -> dict:
    payload = {
        "surgery_type": "spay",
        "veterinarian_name": "Dr. Martinez",
        "scheduled_date": date.today().isoformat(),
        **kwargs,
    }
    resp = await client.post(f"/animals/{animal_id}/surgeries", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Surgery CRUD
# ---------------------------------------------------------------------------


class TestSurgeryCRUD:
    """Tests for surgery record CRUD endpoints."""

    async def test_create_scheduled_surgery(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        resp = await client.post(f"/animals/{animal_id}/surgeries", json={
            "surgery_type": "neuter",
            "veterinarian_name": "Dr. Martinez",
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["surgery_type"] == "neuter"
        assert body["surgery_status"] == "scheduled"
        assert body["veterinarian_name"] == "Dr. Martinez"

    async def test_create_completed_surgery(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        resp = await client.post(f"/animals/{animal_id}/surgeries", json={
            "surgery_type": "spay",
            "surgery_status": "completed",
            "veterinarian_name": "Dr. Lopez",
            "scheduled_date": date.today().isoformat(),
            "performed_date": date.today().isoformat(),
            "anesthesia_type": "general",
            "outcome": "successful",
            "weight_kg": 8.5,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["surgery_status"] == "completed"
        assert body["outcome"] == "successful"

    async def test_create_surgery_nonexistent_animal_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/animals/{fake_id}/surgeries", json={
            "veterinarian_name": "Dr. A",
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 404

    async def test_get_surgery_by_id(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        resp = await client.get(f"/surgeries/{surgery['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == surgery["id"]

    async def test_get_nonexistent_surgery_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/surgeries/{fake_id}")
        assert resp.status_code == 404

    async def test_list_surgeries(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        await _create_surgery(client, animal_id, surgery_type="spay")
        await _create_surgery(client, animal_id, surgery_type="dental")

        resp = await client.get(f"/animals/{animal_id}/surgeries")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_list_surgeries_filter_by_type(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        await _create_surgery(client, animal_id, surgery_type="spay")
        await _create_surgery(client, animal_id, surgery_type="dental")

        resp = await client.get(
            f"/animals/{animal_id}/surgeries",
            params={"surgery_type": "spay"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["surgery_type"] == "spay"

    async def test_update_surgery(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        resp = await client.patch(f"/surgeries/{surgery['id']}", json={
            "surgery_status": "completed",
            "outcome": "successful",
            "performed_date": date.today().isoformat(),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["surgery_status"] == "completed"
        assert body["outcome"] == "successful"

    async def test_delete_surgery(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        resp = await client.delete(f"/surgeries/{surgery['id']}")
        assert resp.status_code == 204

        resp = await client.get(f"/surgeries/{surgery['id']}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Post-op check CRUD
# ---------------------------------------------------------------------------


class TestPostOpCheckCRUD:
    """Tests for post-op monitoring check endpoints."""

    async def test_create_post_op_check(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        scheduled = datetime.now(UTC).isoformat()
        resp = await client.post(f"/surgeries/{surgery['id']}/post-op-checks", json={
            "scheduled_time": scheduled,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["check_status"] == "pending"
        assert body["surgery_id"] == surgery["id"]

    async def test_create_completed_check(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        now = datetime.now(UTC).isoformat()
        resp = await client.post(f"/surgeries/{surgery['id']}/post-op-checks", json={
            "scheduled_time": now,
            "check_status": "completed",
            "completed_time": now,
            "checked_by": "Dr. Martinez",
            "temperature_celsius": 38.5,
            "pain_level": 3,
            "appetite": "normal",
            "mobility": "limited",
            "wound_condition": "clean",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["check_status"] == "completed"
        assert body["pain_level"] == 3

    async def test_list_post_op_checks(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        now = datetime.now(UTC).isoformat()
        await client.post(f"/surgeries/{surgery['id']}/post-op-checks", json={
            "scheduled_time": now,
        })
        await client.post(f"/surgeries/{surgery['id']}/post-op-checks", json={
            "scheduled_time": now,
        })

        resp = await client.get(f"/surgeries/{surgery['id']}/post-op-checks")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    async def test_get_post_op_check(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        now = datetime.now(UTC).isoformat()
        create_resp = await client.post(
            f"/surgeries/{surgery['id']}/post-op-checks",
            json={"scheduled_time": now},
        )
        check_id = create_resp.json()["id"]

        resp = await client.get(f"/post-op-checks/{check_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == check_id

    async def test_update_post_op_check(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        now = datetime.now(UTC).isoformat()
        create_resp = await client.post(
            f"/surgeries/{surgery['id']}/post-op-checks",
            json={"scheduled_time": now},
        )
        check_id = create_resp.json()["id"]

        resp = await client.patch(f"/post-op-checks/{check_id}", json={
            "check_status": "completed",
            "completed_time": now,
            "checked_by": "Nurse Garcia",
            "pain_level": 2,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["check_status"] == "completed"
        assert body["pain_level"] == 2

    async def test_delete_post_op_check(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        surgery = await _create_surgery(client, animal_id)

        now = datetime.now(UTC).isoformat()
        create_resp = await client.post(
            f"/surgeries/{surgery['id']}/post-op-checks",
            json={"scheduled_time": now},
        )
        check_id = create_resp.json()["id"]

        resp = await client.delete(f"/post-op-checks/{check_id}")
        assert resp.status_code == 204

        resp = await client.get(f"/post-op-checks/{check_id}")
        assert resp.status_code == 404

    async def test_post_op_check_nonexistent_surgery_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        resp = await client.post(f"/surgeries/{fake_id}/post-op-checks", json={
            "scheduled_time": now,
        })
        assert resp.status_code == 404
