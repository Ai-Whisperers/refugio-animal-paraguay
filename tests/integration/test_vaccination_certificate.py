"""Integration tests for vaccination certificate PDF endpoint."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


async def _create_animal(client: AsyncClient) -> str:
    resp = await client.post(
        "/animals",
        json={
            "name": f"Cert-Dog-{uuid.uuid4().hex[:6]}",
            "species": "dog",
            "breed": "Labrador",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_vaccine_type(client: AsyncClient) -> dict:
    resp = await client.post(
        "/vaccine-types",
        json={
            "name": f"Cert-Vaccine-{uuid.uuid4().hex[:6]}",
            "target_species": "all",
            "is_required": True,
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _administer_vaccination(
    client: AsyncClient,
    animal_id: str,
    vaccine_type_id: str,
) -> dict:
    """Create and mark a vaccination as administered."""
    resp = await client.post(
        f"/animals/{animal_id}/vaccinations",
        json={
            "vaccine_type_id": vaccine_type_id,
            "scheduled_date": date.today().isoformat(),
            "administered_date": date.today().isoformat(),
            "administered_by": "Dr. Martinez",
            "batch_number": "LOT-CERT-001",
            "vaccination_status": "administered",
            "dose_number": 1,
        },
    )
    assert resp.status_code == 201
    return resp.json()


class TestVaccinationCertificate:
    """Tests for GET /animals/{id}/vaccination-certificate."""

    async def test_generate_certificate_with_vaccinations(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)
        await _administer_vaccination(client, animal_id, vt["id"])

        resp = await client.get(f"/animals/{animal_id}/vaccination-certificate")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # Valid PDF starts with %PDF
        assert resp.content[:4] == b"%PDF"

    async def test_generate_certificate_no_vaccinations(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)

        resp = await client.get(f"/animals/{animal_id}/vaccination-certificate")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    async def test_certificate_nonexistent_animal_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/animals/{fake_id}/vaccination-certificate")
        assert resp.status_code == 404

    async def test_certificate_content_disposition(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)

        resp = await client.get(f"/animals/{animal_id}/vaccination-certificate")
        assert resp.status_code == 200
        # FileResponse sets content-disposition with filename
        disposition = resp.headers.get("content-disposition", "")
        assert "vaccination_certificate_" in disposition

    async def test_certificate_with_multiple_vaccinations(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt1 = await _create_vaccine_type(client)
        vt2 = await _create_vaccine_type(client)

        await _administer_vaccination(client, animal_id, vt1["id"])
        await _administer_vaccination(client, animal_id, vt2["id"])

        resp = await client.get(f"/animals/{animal_id}/vaccination-certificate")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 0
