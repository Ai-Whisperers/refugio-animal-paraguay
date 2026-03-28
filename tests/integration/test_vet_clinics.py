"""Integration tests for vet clinic CRUD API (EPIC-77, RAP-507).

Tests cover: create, list, get, update, status transitions, delete,
and access control (staff vs admin vs unauthenticated).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000088")
_ADMIN_EMAIL = "vet-clinic-admin@refugio.test"


@pytest_asyncio.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client with admin role for admin-only endpoints."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'admin', true)
                ON CONFLICT (id) DO UPDATE SET role = 'admin'
            """),
            {
                "id": str(_ADMIN_USER_ID),
                "email": _ADMIN_EMAIL,
                "pwd": hash_password("AdminPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_ADMIN_USER_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac


def _clinic_data(**overrides: object) -> dict:
    """Return a valid vet clinic creation payload."""
    unique = uuid.uuid4().hex[:8]
    defaults: dict = {
        "name": f"Clinica Test {unique}",
        "email": f"vet-{unique}@example.com.py",
        "phone": "+595981234567",
        "contact_person": "Dr. Test",
        "address": "Av. Mariscal Lopez 1234",
        "city": "Asuncion",
        "department": "Central",
        "specialties": "surgery,dentistry",
        "accepts_emergencies": True,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Create (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_clinic_returns_201(client: AsyncClient) -> None:
    """Staff can create a vet clinic."""
    data = _clinic_data()
    response = await client.post("/api/vet-clinics", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == data["name"]
    assert body["status"] == "pending"
    assert body["id"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_clinic_validates_phone_format(client: AsyncClient) -> None:
    """Invalid phone format returns 422."""
    data = _clinic_data(phone="12345")
    response = await client.post("/api/vet-clinics", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_clinics_returns_paginated(client: AsyncClient) -> None:
    """List endpoint returns paginated results."""
    await client.post("/api/vet-clinics", json=_clinic_data())

    response = await client.get("/api/vet-clinics")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert body["page"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_clinics_filters_by_city(client: AsyncClient) -> None:
    """City filter returns matching clinics."""
    await client.post("/api/vet-clinics", json=_clinic_data(city="Encarnacion"))

    response = await client.get("/api/vet-clinics", params={"city": "Encarnacion"})
    body = response.json()
    assert response.status_code == 200
    for item in body["items"]:
        assert "encarnacion" in item["city"].lower()


# ---------------------------------------------------------------------------
# Get single (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_clinic_by_id(client: AsyncClient) -> None:
    """Get clinic by ID returns full details."""
    create_resp = await client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    response = await client.get(f"/api/vet-clinics/{clinic_id}")
    assert response.status_code == 200
    assert response.json()["id"] == clinic_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_clinic_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent clinic returns 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/vet-clinics/{fake_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update fields (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_clinic_fields(client: AsyncClient) -> None:
    """PATCH updates specified fields."""
    create_resp = await client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/vet-clinics/{clinic_id}",
        json={"name": "Clinica Renovada", "accepts_emergencies": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Clinica Renovada"
    assert body["accepts_emergencies"] is False


# ---------------------------------------------------------------------------
# Status transitions (admin)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_activate_pending_clinic(admin_client: AsyncClient) -> None:
    """Admin can activate a pending clinic."""
    create_resp = await admin_client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    response = await admin_client.patch(
        f"/api/vet-clinics/{clinic_id}/status", json={"status": "active"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["partnership_start"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_status_transition_returns_400(admin_client: AsyncClient) -> None:
    """Invalid status transition returns 400."""
    create_resp = await admin_client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    # pending -> suspended is not allowed
    response = await admin_client.patch(
        f"/api/vet-clinics/{clinic_id}/status", json={"status": "suspended"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_cannot_change_status(client: AsyncClient) -> None:
    """Staff (non-admin) cannot change clinic status."""
    create_resp = await client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/vet-clinics/{clinic_id}/status", json={"status": "active"}
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Delete (admin)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_pending_clinic(admin_client: AsyncClient) -> None:
    """Admin can delete a pending clinic."""
    create_resp = await admin_client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    response = await admin_client.delete(f"/api/vet-clinics/{clinic_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await admin_client.get(f"/api/vet-clinics/{clinic_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_active_clinic_returns_400(admin_client: AsyncClient) -> None:
    """Cannot delete an active clinic."""
    create_resp = await admin_client.post("/api/vet-clinics", json=_clinic_data())
    clinic_id = create_resp.json()["id"]

    # Activate first
    await admin_client.patch(
        f"/api/vet-clinics/{clinic_id}/status", json={"status": "active"}
    )

    response = await admin_client.delete(f"/api/vet-clinics/{clinic_id}")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_returns_401() -> None:
    """Unauthenticated requests return 401."""
    settings = Settings()
    init_engine(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/vet-clinics")
        assert response.status_code == 401
