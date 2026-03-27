"""Integration tests for the Medications CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_medications.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_chain(client: AsyncClient) -> dict:
    """Create animal > visit > diagnosis > treatment chain, return all IDs."""
    resp = await client.post("/animals", json={"name": "MedAnimal", "species": "dog"})
    assert resp.status_code == 201
    animal_id = resp.json()["id"]

    resp = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={"veterinarian_name": "Dr. Rodriguez"},
    )
    assert resp.status_code == 201
    visit_id = resp.json()["id"]

    resp = await client.post(
        f"/vet-visits/{visit_id}/diagnoses",
        json={"condition": "Infection"},
    )
    assert resp.status_code == 201
    diagnosis_id = resp.json()["id"]

    resp = await client.post(
        f"/diagnoses/{diagnosis_id}/treatments",
        json={"name": "Antibiotics course", "treatment_status": "active"},
    )
    assert resp.status_code == 201
    treatment_id = resp.json()["id"]

    return {
        "animal_id": animal_id,
        "visit_id": visit_id,
        "diagnosis_id": diagnosis_id,
        "treatment_id": treatment_id,
    }


async def _create_medication(client: AsyncClient, treatment_id: str) -> dict:
    """Create a medication and return the response body."""
    resp = await client.post(
        f"/treatments/{treatment_id}/medications",
        json={
            "name": "Amoxicillin",
            "dosage": "250mg",
            "frequency": "twice_daily",
            "route": "oral",
            "start_date": "2026-03-27",
            "end_date": "2026-04-10",
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /treatments/{treatment_id}/medications
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_medication_returns_201(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    body = await _create_medication(client, ids["treatment_id"])
    assert body["name"] == "Amoxicillin"
    assert body["dosage"] == "250mg"
    assert body["frequency"] == "twice_daily"
    assert body["route"] == "oral"
    assert body["medication_status"] == "active"  # default
    assert body["treatment_id"] == ids["treatment_id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_medication_minimal_fields(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    resp = await client.post(
        f"/treatments/{ids['treatment_id']}/medications",
        json={"name": "Metacam", "dosage": "0.1mg/kg", "start_date": "2026-03-27"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["frequency"] == "daily"  # default
    assert body["medication_status"] == "active"  # default


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_medication_nonexistent_treatment_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    resp = await client.post(
        f"/treatments/{fake_id}/medications",
        json={"name": "Test", "dosage": "10mg", "start_date": "2026-03-27"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /treatments/{treatment_id}/medications
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_medications_for_treatment(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    await _create_medication(client, ids["treatment_id"])
    await client.post(
        f"/treatments/{ids['treatment_id']}/medications",
        json={"name": "Metacam", "dosage": "5mg", "start_date": "2026-03-27"},
    )

    resp = await client.get(f"/treatments/{ids['treatment_id']}/medications")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2


# ---------------------------------------------------------------------------
# GET /medications/{medication_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_medication_by_id(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    med = await _create_medication(client, ids["treatment_id"])

    resp = await client.get(f"/medications/{med['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Amoxicillin"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_medication_nonexistent_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/medications/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /medications/{medication_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_medication(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    med = await _create_medication(client, ids["treatment_id"])

    resp = await client.patch(
        f"/medications/{med['id']}",
        json={"medication_status": "discontinued", "notes": "Allergic reaction"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["medication_status"] == "discontinued"
    assert body["notes"] == "Allergic reaction"
    assert body["name"] == "Amoxicillin"  # unchanged


# ---------------------------------------------------------------------------
# DELETE /medications/{medication_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_medication(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    med = await _create_medication(client, ids["treatment_id"])

    resp = await client.delete(f"/medications/{med['id']}")
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/medications/{med['id']}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /animals/{animal_id}/medications (cross-entity query)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_active_medications_for_animal(client: AsyncClient) -> None:
    ids = await _setup_chain(client)
    await _create_medication(client, ids["treatment_id"])

    # Add a discontinued medication
    resp = await client.post(
        f"/treatments/{ids['treatment_id']}/medications",
        json={
            "name": "OldDrug",
            "dosage": "100mg",
            "start_date": "2026-01-01",
            "medication_status": "discontinued",
        },
    )
    assert resp.status_code == 201

    # Default: only active
    resp = await client.get(f"/animals/{ids['animal_id']}/medications")
    assert resp.status_code == 200
    items = resp.json()
    assert all(m["medication_status"] == "active" for m in items)
    assert len(items) >= 1

    # include_all=true: both active and discontinued
    resp = await client.get(f"/animals/{ids['animal_id']}/medications?include_all=true")
    assert resp.status_code == 200
    all_items = resp.json()
    assert len(all_items) >= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_medications_nonexistent_animal_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/animals/{uuid4()}/medications")
    assert resp.status_code == 404
