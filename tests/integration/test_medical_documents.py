"""Integration tests for the Medical Documents CRUD endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_medical_documents.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_animal_and_visit(client: AsyncClient) -> tuple[str, str]:
    """Create animal + visit, return (animal_id, visit_id)."""
    resp = await client.post("/animals", json={"name": "DocAnimal", "species": "cat"})
    assert resp.status_code == 201
    animal_id = resp.json()["id"]

    resp = await client.post(
        f"/animals/{animal_id}/vet-visits",
        json={"veterinarian_name": "Dr. Lopez"},
    )
    assert resp.status_code == 201
    visit_id = resp.json()["id"]
    return animal_id, visit_id


async def _create_document(client: AsyncClient, visit_id: str) -> dict:
    """Create a medical document and return the response body."""
    resp = await client.post(
        f"/vet-visits/{visit_id}/documents",
        json={
            "document_type": "lab_result",
            "title": "CBC Panel Results",
            "description": "Complete blood count analysis",
            "file_url": "https://storage.example.com/docs/cbc-2026-03-27.pdf",
            "file_name": "cbc-2026-03-27.pdf",
            "file_size_bytes": 125000,
            "mime_type": "application/pdf",
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /vet-visits/{visit_id}/documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_document_returns_201(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    body = await _create_document(client, visit_id)
    assert body["document_type"] == "lab_result"
    assert body["title"] == "CBC Panel Results"
    assert body["file_url"] == "https://storage.example.com/docs/cbc-2026-03-27.pdf"
    assert body["file_size_bytes"] == 125000
    assert body["mime_type"] == "application/pdf"
    assert body["vet_visit_id"] == visit_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_document_minimal_fields(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    resp = await client.post(
        f"/vet-visits/{visit_id}/documents",
        json={
            "title": "X-ray image",
            "file_url": "https://storage.example.com/xray.png",
            "file_name": "xray.png",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["document_type"] == "other"  # default
    assert body["file_size_bytes"] is None
    assert body["mime_type"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_document_nonexistent_visit_returns_404(client: AsyncClient) -> None:
    fake_id = str(uuid4())
    resp = await client.post(
        f"/vet-visits/{fake_id}/documents",
        json={
            "title": "Test",
            "file_url": "https://example.com/doc.pdf",
            "file_name": "doc.pdf",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_document_missing_required_fields_returns_422(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    resp = await client.post(
        f"/vet-visits/{visit_id}/documents",
        json={"title": "Incomplete"},  # missing file_url and file_name
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /vet-visits/{visit_id}/documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_documents_for_visit(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    await _create_document(client, visit_id)
    await client.post(
        f"/vet-visits/{visit_id}/documents",
        json={
            "document_type": "xray",
            "title": "Chest X-ray",
            "file_url": "https://storage.example.com/xray.dcm",
            "file_name": "chest-xray.dcm",
        },
    )

    resp = await client.get(f"/vet-visits/{visit_id}/documents")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_documents_nonexistent_visit_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/vet-visits/{uuid4()}/documents")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /medical-documents/{document_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_document_by_id(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    doc = await _create_document(client, visit_id)

    resp = await client.get(f"/medical-documents/{doc['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "CBC Panel Results"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_document_nonexistent_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/medical-documents/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /medical-documents/{document_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_document(client: AsyncClient) -> None:
    _, visit_id = await _create_animal_and_visit(client)
    doc = await _create_document(client, visit_id)

    resp = await client.delete(f"/medical-documents/{doc['id']}")
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/medical-documents/{doc['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_document_nonexistent_returns_404(client: AsyncClient) -> None:
    resp = await client.delete(f"/medical-documents/{uuid4()}")
    assert resp.status_code == 404
