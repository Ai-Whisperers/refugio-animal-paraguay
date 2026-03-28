"""Integration tests for attendance tracking API (RAP-183).

Tests GET /api/shifts/{id}/signups and PATCH /api/shifts/{id}/signups/{signup_id}.
Requires a running PostgreSQL instance (refugio_dev).
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_test_shift(client: AsyncClient, **kwargs: object) -> dict:
    """Create a shift and return the response body."""
    defaults = {
        "shift_date": "2026-10-01",
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "role": "general",
        "capacity": 5,
        "title": "Attendance test shift",
    }
    defaults.update(kwargs)
    resp = await client.post("/api/shifts", json=defaults)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def signup_for_shift(client: AsyncClient, shift_id: str) -> dict:
    """Sign up the test user for a shift."""
    resp = await client.post(f"/api/shifts/{shift_id}/signup")
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# GET /api/shifts/{id}/signups
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_signups_empty_for_new_shift(client: AsyncClient) -> None:
    """Shift with no signups returns empty list."""
    shift = await create_test_shift(client, shift_date="2026-10-02")
    response = await client.get(f"/api/shifts/{shift['id']}/signups")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_signups_shows_signup(client: AsyncClient) -> None:
    """After signing up, signup appears in list."""
    shift = await create_test_shift(client, shift_date="2026-10-03")
    signup = await signup_for_shift(client, shift["id"])

    response = await client.get(f"/api/shifts/{shift['id']}/signups")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == signup["id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_signups_for_nonexistent_shift_returns_404(client: AsyncClient) -> None:
    """Listing signups for a nonexistent shift returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000097"
    response = await client.get(f"/api/shifts/{fake_id}/signups")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/shifts/{id}/signups/{signup_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mark_attended_true(client: AsyncClient) -> None:
    """Staff can mark a signup as attended."""
    shift = await create_test_shift(client, shift_date="2026-10-04")
    signup = await signup_for_shift(client, shift["id"])

    response = await client.patch(
        f"/api/shifts/{shift['id']}/signups/{signup['id']}",
        json={"attended": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["attended"] is True
    assert body["id"] == signup["id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mark_no_show(client: AsyncClient) -> None:
    """Staff can mark a signup as no-show (attended=false)."""
    shift = await create_test_shift(client, shift_date="2026-10-05")
    signup = await signup_for_shift(client, shift["id"])

    response = await client.patch(
        f"/api/shifts/{shift['id']}/signups/{signup['id']}",
        json={"attended": False},
    )
    assert response.status_code == 200
    assert response.json()["attended"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_clear_attendance(client: AsyncClient) -> None:
    """Staff can clear attendance by setting attended=null."""
    shift = await create_test_shift(client, shift_date="2026-10-06")
    signup = await signup_for_shift(client, shift["id"])

    # First mark as attended
    await client.patch(
        f"/api/shifts/{shift['id']}/signups/{signup['id']}",
        json={"attended": True},
    )

    # Then clear it
    response = await client.patch(
        f"/api/shifts/{shift['id']}/signups/{signup['id']}",
        json={"attended": None},
    )
    assert response.status_code == 200
    assert response.json()["attended"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_attendance_with_note(client: AsyncClient) -> None:
    """Staff can add a note when recording attendance."""
    shift = await create_test_shift(client, shift_date="2026-10-07")
    signup = await signup_for_shift(client, shift["id"])

    response = await client.patch(
        f"/api/shifts/{shift['id']}/signups/{signup['id']}",
        json={"attended": True, "notes": "Arrived 5 minutes early"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["attended"] is True
    assert body["notes"] == "Arrived 5 minutes early"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_attendance_wrong_shift_returns_404(client: AsyncClient) -> None:
    """Updating attendance with a mismatched shift returns 404."""
    shift_a = await create_test_shift(client, shift_date="2026-10-08")
    shift_b = await create_test_shift(client, shift_date="2026-10-09")
    signup = await signup_for_shift(client, shift_a["id"])

    # Try to update signup from shift_a using shift_b's ID
    response = await client.patch(
        f"/api/shifts/{shift_b['id']}/signups/{signup['id']}",
        json={"attended": True},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_attendance_nonexistent_signup_returns_404(client: AsyncClient) -> None:
    """Updating a nonexistent signup returns 404."""
    shift = await create_test_shift(client, shift_date="2026-10-10")
    fake_signup_id = "00000000-0000-0000-0000-000000000096"

    response = await client.patch(
        f"/api/shifts/{shift['id']}/signups/{fake_signup_id}",
        json={"attended": True},
    )
    assert response.status_code == 404
