"""Integration tests for vaccination API endpoints.

Tests vaccine type CRUD, vaccination schedule CRUD, and vaccination
record CRUD (administration recording).
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_animal(client: AsyncClient) -> str:
    """Create a test animal and return its ID."""
    resp = await client.post("/animals", json={
        "name": "Firulais Test",
        "species": "dog",
        "breed": "mixed",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_vaccine_type(client: AsyncClient, **overrides: object) -> dict:
    """Create a vaccine type and return full response."""
    import uuid
    data = {
        "name": f"Rabies-{uuid.uuid4().hex[:6]}",
        "description": "Anti-rabies vaccine",
        "manufacturer": "MSD",
        "target_species": "all",
        "is_required": True,
    }
    data.update(overrides)
    resp = await client.post("/vaccine-types", json=data)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Vaccine Type CRUD
# ---------------------------------------------------------------------------


class TestVaccineTypeCRUD:
    """Tests for /vaccine-types endpoints."""

    async def test_create_vaccine_type(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        assert vt["is_required"] is True
        assert vt["target_species"] == "all"
        assert "id" in vt

    async def test_get_vaccine_type(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        resp = await client.get(f"/vaccine-types/{vt['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == vt["name"]

    async def test_list_vaccine_types(self, client: AsyncClient) -> None:
        await _create_vaccine_type(client, target_species="dog")
        resp = await client.get("/vaccine-types", params={"species": "dog"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert len(body["items"]) >= 1

    async def test_update_vaccine_type(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        resp = await client.patch(
            f"/vaccine-types/{vt['id']}",
            json={"is_required": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_required"] is False

    async def test_delete_vaccine_type(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        resp = await client.delete(f"/vaccine-types/{vt['id']}")
        assert resp.status_code == 204

        resp = await client.get(f"/vaccine-types/{vt['id']}")
        assert resp.status_code == 404

    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/vaccine-types/00000000-0000-0000-0000-000000000099"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vaccination Schedule CRUD
# ---------------------------------------------------------------------------


class TestVaccinationScheduleCRUD:
    """Tests for vaccination schedule endpoints."""

    async def test_create_schedule(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        resp = await client.post(
            f"/vaccine-types/{vt['id']}/schedules",
            json={
                "vaccine_type_id": vt["id"],
                "species": "dog",
                "dose_number": 1,
                "age_weeks_min": 8,
                "age_weeks_max": 12,
                "is_booster": False,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["species"] == "dog"
        assert body["dose_number"] == 1

    async def test_list_schedules(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        await client.post(
            f"/vaccine-types/{vt['id']}/schedules",
            json={
                "vaccine_type_id": vt["id"],
                "species": "dog",
                "dose_number": 1,
            },
        )
        resp = await client.get(f"/vaccine-types/{vt['id']}/schedules")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_update_schedule(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        create_resp = await client.post(
            f"/vaccine-types/{vt['id']}/schedules",
            json={
                "vaccine_type_id": vt["id"],
                "species": "dog",
                "dose_number": 1,
            },
        )
        sched_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/vaccination-schedules/{sched_id}",
            json={"interval_days": 28, "is_booster": True},
        )
        assert resp.status_code == 200
        assert resp.json()["interval_days"] == 28
        assert resp.json()["is_booster"] is True

    async def test_delete_schedule(self, client: AsyncClient) -> None:
        vt = await _create_vaccine_type(client)
        create_resp = await client.post(
            f"/vaccine-types/{vt['id']}/schedules",
            json={
                "vaccine_type_id": vt["id"],
                "species": "dog",
                "dose_number": 1,
            },
        )
        sched_id = create_resp.json()["id"]

        resp = await client.delete(f"/vaccination-schedules/{sched_id}")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Vaccination Record CRUD — Administration Recording
# ---------------------------------------------------------------------------


class TestVaccinationRecordCRUD:
    """Tests for /animals/{id}/vaccinations and /vaccinations/{id}."""

    async def test_create_scheduled_vaccination(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["vaccination_status"] == "scheduled"
        assert body["animal_id"] == animal_id
        assert body["vaccine_type"]["id"] == vt["id"]

    async def test_create_administered_vaccination(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
                "administered_date": "2026-04-15",
                "administered_by": "Dr. Martinez",
                "batch_number": "LOT-2026-001",
                "vaccination_status": "administered",
                "next_due_date": "2027-04-15",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["vaccination_status"] == "administered"
        assert body["administered_by"] == "Dr. Martinez"
        assert body["batch_number"] == "LOT-2026-001"

    async def test_mark_vaccination_as_administered(self, client: AsyncClient) -> None:
        """Record administration via PATCH — the core 'vaccine administration recording' flow."""
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        # Schedule first
        create_resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
            },
        )
        vacc_id = create_resp.json()["id"]

        # Administer
        resp = await client.patch(
            f"/vaccinations/{vacc_id}",
            json={
                "vaccination_status": "administered",
                "administered_date": "2026-04-15",
                "administered_by": "Dr. Lopez",
                "batch_number": "LOT-2026-002",
                "next_due_date": "2027-04-15",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["vaccination_status"] == "administered"
        assert body["administered_by"] == "Dr. Lopez"

    async def test_list_vaccinations_with_status_filter(
        self, client: AsyncClient
    ) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        # Create one scheduled, one administered
        await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-05-01",
            },
        )
        await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-01",
                "administered_date": "2026-04-01",
                "vaccination_status": "administered",
            },
        )

        # Filter scheduled
        resp = await client.get(
            f"/animals/{animal_id}/vaccinations",
            params={"vaccination_status": "scheduled"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        for item in body["items"]:
            assert item["vaccination_status"] == "scheduled"

    async def test_get_vaccination_by_id(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)
        create_resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
            },
        )
        vacc_id = create_resp.json()["id"]

        resp = await client.get(f"/vaccinations/{vacc_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == vacc_id

    async def test_delete_vaccination(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)
        create_resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
            },
        )
        vacc_id = create_resp.json()["id"]

        resp = await client.delete(f"/vaccinations/{vacc_id}")
        assert resp.status_code == 204

        resp = await client.get(f"/vaccinations/{vacc_id}")
        assert resp.status_code == 404

    async def test_create_vaccination_nonexistent_animal_404(
        self, client: AsyncClient
    ) -> None:
        vt = await _create_vaccine_type(client)
        resp = await client.post(
            "/animals/00000000-0000-0000-0000-000000000099/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": "2026-04-15",
            },
        )
        assert resp.status_code == 404

    async def test_create_vaccination_nonexistent_vaccine_type_404(
        self, client: AsyncClient
    ) -> None:
        animal_id = await _create_animal(client)
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": "00000000-0000-0000-0000-000000000099",
                "scheduled_date": "2026-04-15",
            },
        )
        assert resp.status_code == 404
