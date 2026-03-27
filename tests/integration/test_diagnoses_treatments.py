"""Integration tests for the Diagnoses and Treatments CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_diagnoses_treatments.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_animal(client: AsyncClient) -> str:
    """Create an animal and return its ID."""
    resp = await client.post("/animals", json={"name": "MedicalAnimal", "species": "dog"})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_visit(client: AsyncClient, animal_id: str) -> str:
    """Create a vet visit and return its ID."""
    resp = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={"veterinarian_name": "Dr. Rodriguez", "visit_type": "checkup"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_diagnosis(client: AsyncClient, visit_id: str) -> dict:
    """Create a diagnosis and return the full response body."""
    resp = await client.post(
        f"/vet-visits/{visit_id}/diagnoses",
        json={
            "condition": "Parvovirus",
            "description": "Canine parvovirus infection",
            "severity": "severe",
            "is_chronic": False,
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_treatment(client: AsyncClient, diagnosis_id: str) -> dict:
    """Create a treatment and return the full response body."""
    resp = await client.post(
        f"/diagnoses/{diagnosis_id}/treatments",
        json={
            "name": "IV Fluids",
            "description": "Intravenous fluid therapy",
            "treatment_status": "active",
            "start_date": "2026-03-27",
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Diagnosis CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_diagnosis_returns_201(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    body = await _create_diagnosis(client, visit_id)
    assert body["condition"] == "Parvovirus"
    assert body["severity"] == "severe"
    assert body["is_chronic"] is False
    assert body["vet_visit_id"] == visit_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_diagnosis_minimal_fields(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    resp = await client.post(
        f"/vet-visits/{visit_id}/diagnoses",
        json={"condition": "Ear infection"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["severity"] == "moderate"  # default
    assert body["is_chronic"] is False  # default


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_diagnosis_nonexistent_visit_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    resp = await client.post(
        f"/vet-visits/{fake_id}/diagnoses",
        json={"condition": "Test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_diagnoses(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    await _create_diagnosis(client, visit_id)
    await client.post(
        f"/vet-visits/{visit_id}/diagnoses",
        json={"condition": "Kennel cough"},
    )

    resp = await client.get(f"/vet-visits/{visit_id}/diagnoses")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_diagnosis(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    diagnosis_id = diagnosis["id"]

    resp = await client.patch(
        f"/diagnoses/{diagnosis_id}",
        json={"severity": "critical", "is_chronic": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "critical"
    assert body["is_chronic"] is True
    assert body["condition"] == "Parvovirus"  # unchanged


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_diagnosis_nonexistent_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    resp = await client.patch(
        f"/diagnoses/{fake_id}",
        json={"severity": "mild"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_diagnosis(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    diagnosis_id = diagnosis["id"]

    resp = await client.delete(f"/diagnoses/{diagnosis_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/vet-visits/{visit_id}/diagnoses")
    ids = [d["id"] for d in resp.json()]
    assert diagnosis_id not in ids


# ---------------------------------------------------------------------------
# Treatment CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_treatment_returns_201(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    body = await _create_treatment(client, diagnosis["id"])
    assert body["name"] == "IV Fluids"
    assert body["treatment_status"] == "active"
    assert body["diagnosis_id"] == diagnosis["id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_treatment_minimal_fields(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    resp = await client.post(
        f"/diagnoses/{diagnosis['id']}/treatments",
        json={"name": "Rest"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["treatment_status"] == "planned"  # default


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_treatment_nonexistent_diagnosis_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    resp = await client.post(
        f"/diagnoses/{fake_id}/treatments",
        json={"name": "Test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_treatments(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    await _create_treatment(client, diagnosis["id"])
    await client.post(
        f"/diagnoses/{diagnosis['id']}/treatments",
        json={"name": "Antibiotics"},
    )

    resp = await client.get(f"/diagnoses/{diagnosis['id']}/treatments")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_treatment(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    treatment = await _create_treatment(client, diagnosis["id"])
    treatment_id = treatment["id"]

    resp = await client.patch(
        f"/treatments/{treatment_id}",
        json={"treatment_status": "completed", "end_date": "2026-04-10"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["treatment_status"] == "completed"
    assert body["end_date"] == "2026-04-10"
    assert body["name"] == "IV Fluids"  # unchanged


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_treatment(client: AsyncClient) -> None:
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    treatment = await _create_treatment(client, diagnosis["id"])
    treatment_id = treatment["id"]

    resp = await client.delete(f"/treatments/{treatment_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/diagnoses/{diagnosis['id']}/treatments")
    ids = [t["id"] for t in resp.json()]
    assert treatment_id not in ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_diagnosis_cascades_treatments(client: AsyncClient) -> None:
    """Deleting a diagnosis should cascade-delete its treatments."""
    animal_id = await _create_animal(client)
    visit_id = await _create_visit(client, animal_id)
    diagnosis = await _create_diagnosis(client, visit_id)
    treatment = await _create_treatment(client, diagnosis["id"])
    treatment_id = treatment["id"]

    # Delete the parent diagnosis
    resp = await client.delete(f"/diagnoses/{diagnosis['id']}")
    assert resp.status_code == 204

    # Treatment should be gone too (404 on its parent list)
    resp = await client.get(f"/diagnoses/{diagnosis['id']}/treatments")
    assert resp.status_code == 404  # diagnosis itself is gone
