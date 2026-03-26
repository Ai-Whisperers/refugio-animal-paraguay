"""Integration tests for the Animal Intake Workflow endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_intake.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import make_intake_data

# ---------------------------------------------------------------------------
# POST /animals/intake
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_returns_201(client: AsyncClient) -> None:
    response = await client.post("/animals/intake", json=make_intake_data())
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "stray"
    assert body["finder_name"] == "Carlos Lopez"
    assert body["requires_quarantine"] is False
    assert "id" in body
    assert "animal_id" in body
    assert "animal" in body
    assert body["animal"]["name"] == "Rescatado"
    assert body["animal"]["status"] == "intake"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_with_quarantine_sets_animal_quarantine_status(
    client: AsyncClient,
) -> None:
    data = make_intake_data(requires_quarantine=True)
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["requires_quarantine"] is True
    assert body["animal"]["status"] == "quarantine"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_surrender_source(client: AsyncClient) -> None:
    data = make_intake_data(source="surrender", finder_name=None, location_found=None)
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    assert response.json()["source"] == "surrender"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_rescue_source(client: AsyncClient) -> None:
    data = make_intake_data(source="rescue")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    assert response.json()["source"] == "rescue"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_transfer_source(client: AsyncClient) -> None:
    data = make_intake_data(source="transfer")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    assert response.json()["source"] == "transfer"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_with_photos(client: AsyncClient) -> None:
    data = make_intake_data(
        photo_urls=["https://example.com/intake1.jpg", "https://example.com/intake2.jpg"]
    )
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    body = response.json()
    # Verify animal was created and photos are linkable
    animal_id = body["animal_id"]
    animal_response = await client.get(f"/animals/{animal_id}")
    assert animal_response.status_code == 200
    animal_body = animal_response.json()
    assert len(animal_body["photos"]) == 2
    assert animal_body["primary_photo_url"] == "https://example.com/intake1.jpg"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_with_cat_species(client: AsyncClient) -> None:
    data = make_intake_data(name="Michi", species="cat")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 201
    assert response.json()["animal"]["species"] == "cat"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_invalid_source_returns_422(client: AsyncClient) -> None:
    data = make_intake_data(source="found_on_street")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_missing_name_returns_422(client: AsyncClient) -> None:
    data = make_intake_data()
    del data["name"]
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_missing_source_returns_422(client: AsyncClient) -> None:
    data = make_intake_data()
    del data["source"]
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_invalid_email_returns_422(client: AsyncClient) -> None:
    data = make_intake_data(finder_email="not-an-email")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_invalid_birth_date_returns_422(client: AsyncClient) -> None:
    data = make_intake_data(birth_date="not-a-date")
    response = await client.post("/animals/intake", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /animals/intake
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_intakes_returns_200(client: AsyncClient) -> None:
    # Create an intake first
    await client.post("/animals/intake", json=make_intake_data())
    response = await client.get("/animals/intake")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_intakes_filter_by_source(client: AsyncClient) -> None:
    # Create intakes with different sources
    await client.post("/animals/intake", json=make_intake_data(source="rescue", name="Rescue1"))
    response = await client.get("/animals/intake", params={"source": "rescue"})
    assert response.status_code == 200
    body = response.json()
    for intake in body:
        assert intake["source"] == "rescue"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_intakes_filter_by_quarantine(client: AsyncClient) -> None:
    await client.post(
        "/animals/intake",
        json=make_intake_data(requires_quarantine=True, name="Quarantine1"),
    )
    response = await client.get(
        "/animals/intake", params={"requires_quarantine": True}
    )
    assert response.status_code == 200
    body = response.json()
    for intake in body:
        assert intake["requires_quarantine"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_intakes_pagination(client: AsyncClient) -> None:
    response = await client.get("/animals/intake", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert len(body) <= 1


# ---------------------------------------------------------------------------
# GET /animals/intake/{intake_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_intake_returns_200(client: AsyncClient) -> None:
    create_resp = await client.post("/animals/intake", json=make_intake_data())
    intake_id = create_resp.json()["id"]

    response = await client.get(f"/animals/intake/{intake_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == intake_id
    assert "animal" in body
    assert "staff" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_intake_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/animals/intake/{uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Auth enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_intake_without_auth_returns_403(client: AsyncClient) -> None:
    """Verify that unauthenticated requests are rejected."""
    from httpx import ASGITransport, AsyncClient as _AC

    from src.app import app

    async with _AC(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as unauthed:
        response = await unauthed.post("/animals/intake", json=make_intake_data())
        assert response.status_code == 403
