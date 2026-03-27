"""Integration tests for bulk vaccination recording endpoint."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


async def _create_animal(client: AsyncClient, name_prefix: str = "Bulk") -> str:
    resp = await client.post("/animals", json={
        "name": f"{name_prefix}-{uuid.uuid4().hex[:6]}",
        "species": "dog",
        "breed": "mixed",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_vaccine_type(client: AsyncClient) -> dict:
    resp = await client.post("/vaccine-types", json={
        "name": f"Bulk-Vaccine-{uuid.uuid4().hex[:6]}",
        "target_species": "all",
        "is_required": True,
    })
    assert resp.status_code == 201
    return resp.json()


class TestBulkVaccinationRecording:
    """Tests for POST /vaccinations/bulk."""

    async def test_bulk_create_scheduled(self, client: AsyncClient) -> None:
        """Create scheduled vaccinations for multiple animals."""
        animal_ids = [await _create_animal(client) for _ in range(3)]
        vt = await _create_vaccine_type(client)

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": animal_ids,
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["total_requested"] == 3
        assert body["total_created"] == 3
        assert body["total_failed"] == 0
        assert len(body["results"]) == 3
        for result in body["results"]:
            assert result["success"] is True
            assert result["vaccination_id"] is not None

    async def test_bulk_create_administered(self, client: AsyncClient) -> None:
        """Create administered vaccinations for a batch of animals."""
        animal_ids = [await _create_animal(client) for _ in range(2)]
        vt = await _create_vaccine_type(client)

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": animal_ids,
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
            "administered_date": date.today().isoformat(),
            "administered_by": "Dr. Martinez",
            "batch_number": "LOT-BATCH-001",
            "vaccination_status": "administered",
            "dose_number": 1,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["total_created"] == 2
        assert body["total_failed"] == 0

    async def test_bulk_partial_failure_nonexistent_animal(self, client: AsyncClient) -> None:
        """One valid animal and one nonexistent animal."""
        real_id = await _create_animal(client)
        fake_id = str(uuid.uuid4())
        vt = await _create_vaccine_type(client)

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": [real_id, fake_id],
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["total_requested"] == 2
        assert body["total_created"] == 1
        assert body["total_failed"] == 1

        # Check individual results
        success_results = [r for r in body["results"] if r["success"]]
        failed_results = [r for r in body["results"] if not r["success"]]
        assert len(success_results) == 1
        assert len(failed_results) == 1
        assert "not found" in failed_results[0]["error"].lower()

    async def test_bulk_nonexistent_vaccine_type_404(self, client: AsyncClient) -> None:
        """Nonexistent vaccine type should return 404."""
        animal_id = await _create_animal(client)
        fake_vt_id = str(uuid.uuid4())

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": [animal_id],
            "vaccine_type_id": fake_vt_id,
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 404

    async def test_bulk_single_animal(self, client: AsyncClient) -> None:
        """Bulk endpoint works with a single animal."""
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": [animal_id],
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["total_requested"] == 1
        assert body["total_created"] == 1

    async def test_bulk_vaccinations_visible_per_animal(self, client: AsyncClient) -> None:
        """Vaccinations created via bulk should appear in per-animal listing."""
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        await client.post("/vaccinations/bulk", json={
            "animal_ids": [animal_id],
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
            "vaccination_status": "scheduled",
        })

        resp = await client.get(f"/animals/{animal_id}/vaccinations")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        assert any(v["vaccine_type_id"] == vt["id"] for v in items)

    async def test_bulk_empty_animal_ids_rejected(self, client: AsyncClient) -> None:
        """Empty animal_ids list should be rejected by validation."""
        vt = await _create_vaccine_type(client)

        resp = await client.post("/vaccinations/bulk", json={
            "animal_ids": [],
            "vaccine_type_id": vt["id"],
            "scheduled_date": date.today().isoformat(),
        })
        assert resp.status_code == 422
