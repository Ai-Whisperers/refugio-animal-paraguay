"""Integration tests for shift scheduling API (RAP-180).

Tests CRUD endpoints for volunteer shift management.
Requires a running PostgreSQL instance (refugio_dev).
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/shifts/roles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_roles_returns_all_valid_roles(client: AsyncClient) -> None:
    """Roles endpoint returns the full list of valid shift roles."""
    response = await client.get("/api/shifts/roles")
    assert response.status_code == 200
    body = response.json()
    assert "roles" in body
    assert isinstance(body["roles"], list)
    assert len(body["roles"]) > 0
    assert "general" in body["roles"]
    assert "animal_care" in body["roles"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_roles_is_sorted(client: AsyncClient) -> None:
    """Roles are returned in sorted order."""
    response = await client.get("/api/shifts/roles")
    roles = response.json()["roles"]
    assert roles == sorted(roles)


# ---------------------------------------------------------------------------
# POST /api/shifts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_shift_success(client: AsyncClient) -> None:
    """Staff can create a new shift."""
    response = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-05-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "role": "animal_care",
            "capacity": 3,
            "title": "Morning animal care shift",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["shift_date"] == "2026-05-01"
    assert body["start_time"] == "09:00:00"
    assert body["end_time"] == "13:00:00"
    assert body["role"] == "animal_care"
    assert body["capacity"] == 3
    assert body["slots_filled"] == 0
    assert body["status"] == "open"
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_shift_minimal_fields(client: AsyncClient) -> None:
    """Shift can be created with just required fields."""
    response = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-05-02",
            "start_time": "14:00:00",
            "end_time": "18:00:00",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "general"
    assert body["capacity"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_shift_end_before_start_rejected(client: AsyncClient) -> None:
    """Shift with end_time before start_time is rejected."""
    response = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-05-01",
            "start_time": "14:00:00",
            "end_time": "09:00:00",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_shift_invalid_role_rejected(client: AsyncClient) -> None:
    """Invalid role value is rejected with 422."""
    response = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-05-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "role": "not_a_valid_role",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_shift_requires_auth(client: AsyncClient) -> None:
    """Creating a shift without auth returns 401 or 403."""
    response = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-05-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
        },
        headers={"Authorization": ""},
    )
    assert response.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/shifts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_shifts_returns_paginated_results(client: AsyncClient) -> None:
    """List endpoint returns paginated shift results."""
    # Create a shift first so list is not empty
    await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-06-01",
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "role": "cleaning",
        },
    )
    response = await client.get("/api/shifts")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert isinstance(body["items"], list)
    assert body["page"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_shifts_filter_by_status(client: AsyncClient) -> None:
    """List can be filtered by shift_status."""
    response = await client.get("/api/shifts?shift_status=open")
    assert response.status_code == 200
    body = response.json()
    for shift in body["items"]:
        assert shift["status"] == "open"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_shifts_invalid_status_rejected(client: AsyncClient) -> None:
    """Invalid status filter returns 422."""
    response = await client.get("/api/shifts?shift_status=invalid_status")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_shifts_filter_by_date(client: AsyncClient) -> None:
    """List can be filtered by shift_date."""
    response = await client.get("/api/shifts?shift_date=2026-06-01")
    assert response.status_code == 200
    body = response.json()
    for shift in body["items"]:
        assert shift["shift_date"] == "2026-06-01"


# ---------------------------------------------------------------------------
# GET /api/shifts/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_shift_by_id(client: AsyncClient) -> None:
    """Can retrieve a specific shift by ID."""
    create_resp = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-07-01",
            "start_time": "10:00:00",
            "end_time": "14:00:00",
            "role": "admin_office",
            "title": "Admin shift",
        },
    )
    shift_id = create_resp.json()["id"]

    response = await client.get(f"/api/shifts/{shift_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == shift_id
    assert body["title"] == "Admin shift"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_shift_not_found(client: AsyncClient) -> None:
    """Non-existent shift returns 404."""
    response = await client.get("/api/shifts/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/shifts/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_shift_capacity(client: AsyncClient) -> None:
    """Staff can update shift capacity."""
    create_resp = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-08-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "capacity": 2,
        },
    )
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["id"]

    update_resp = await client.patch(f"/api/shifts/{shift_id}", json={"capacity": 5})
    assert update_resp.status_code == 200
    assert update_resp.json()["capacity"] == 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_shift_not_found(client: AsyncClient) -> None:
    """Updating a non-existent shift returns 404."""
    response = await client.patch(
        "/api/shifts/00000000-0000-0000-0000-000000000099",
        json={"capacity": 5},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_shift_notes_and_location(client: AsyncClient) -> None:
    """Staff can update shift notes and location."""
    create_resp = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-09-01",
            "start_time": "07:00:00",
            "end_time": "11:00:00",
        },
    )
    shift_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/shifts/{shift_id}",
        json={"notes": "Please bring ID", "location": "Block B"},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["notes"] == "Please bring ID"
    assert body["location"] == "Block B"


# ---------------------------------------------------------------------------
# DELETE /api/shifts/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_shift_success(client: AsyncClient) -> None:
    """Staff can delete an open shift."""
    create_resp = await client.post(
        "/api/shifts",
        json={
            "shift_date": "2026-10-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
        },
    )
    shift_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/shifts/{shift_id}")
    assert delete_resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/shifts/{shift_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_shift_not_found(client: AsyncClient) -> None:
    """Deleting a non-existent shift returns 404."""
    response = await client.delete("/api/shifts/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404
