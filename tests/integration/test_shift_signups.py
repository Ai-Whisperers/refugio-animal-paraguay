"""Integration tests for shift self-signup API (RAP-182).

Tests POST/DELETE /api/shifts/{id}/signup and GET /api/shifts/my-signups.
Requires a running PostgreSQL instance (refugio_dev).
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_test_shift(client: AsyncClient, **kwargs: object) -> dict:
    """Create a shift via API and return the response body."""
    defaults = {
        "shift_date": "2026-08-01",
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "role": "general",
        "capacity": 3,
        "title": "Integration test shift",
    }
    defaults.update(kwargs)
    resp = await client.post("/api/shifts", json=defaults)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# GET /api/shifts/my-signups
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_my_signups_returns_empty_when_no_signups(client: AsyncClient) -> None:
    """Authenticated user with no signups receives empty list."""
    response = await client.get("/api/shifts/my-signups")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


# ---------------------------------------------------------------------------
# POST /api/shifts/{id}/signup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_for_open_shift_succeeds(client: AsyncClient) -> None:
    """Volunteer can sign up for an open shift."""
    shift = await create_test_shift(client, shift_date="2026-09-01")

    response = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert response.status_code == 201
    body = response.json()
    assert body["shift_id"] == shift["id"]
    assert "volunteer_id" in body
    assert body["confirmed"] is False
    assert body["attended"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_increments_slots_filled(client: AsyncClient) -> None:
    """Signup increments the shift's slots_filled count."""
    shift = await create_test_shift(client, shift_date="2026-09-02", capacity=5)
    initial_filled = shift["slots_filled"]

    await client.post(f"/api/shifts/{shift['id']}/signup")

    detail_resp = await client.get(f"/api/shifts/{shift['id']}")
    assert detail_resp.status_code == 200
    updated = detail_resp.json()
    assert updated["slots_filled"] == initial_filled + 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_transitions_shift_to_full(client: AsyncClient) -> None:
    """When all slots are taken, shift status changes to full."""
    shift = await create_test_shift(client, shift_date="2026-09-03", capacity=1)

    resp = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert resp.status_code == 201

    detail_resp = await client.get(f"/api/shifts/{shift['id']}")
    updated = detail_resp.json()
    assert updated["status"] == "full"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_for_full_shift_returns_409(client: AsyncClient) -> None:
    """Cannot sign up for a full shift."""
    shift = await create_test_shift(client, shift_date="2026-09-04", capacity=1)
    # First signup fills it
    r1 = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert r1.status_code == 201

    # Second signup (same user is already signed up — caught by duplicate check)
    r2 = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert r2.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_signup_returns_409(client: AsyncClient) -> None:
    """Cannot sign up twice for the same shift."""
    shift = await create_test_shift(client, shift_date="2026-09-05", capacity=5)

    r1 = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert r1.status_code == 201

    r2 = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert r2.status_code == 409
    assert "Already signed up" in r2.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_for_nonexistent_shift_returns_404(client: AsyncClient) -> None:
    """Signing up for a nonexistent shift returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000099"
    response = await client.post(f"/api/shifts/{fake_id}/signup")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signup_appears_in_my_signups(client: AsyncClient) -> None:
    """After signup, the shift appears in GET /api/shifts/my-signups."""
    shift = await create_test_shift(client, shift_date="2026-09-06", capacity=5)

    signup_resp = await client.post(f"/api/shifts/{shift['id']}/signup")
    assert signup_resp.status_code == 201

    my_resp = await client.get("/api/shifts/my-signups")
    assert my_resp.status_code == 200
    body = my_resp.json()
    shift_ids = [s["shift_id"] for s in body["items"]]
    assert shift["id"] in shift_ids


# ---------------------------------------------------------------------------
# DELETE /api/shifts/{id}/signup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_signup_succeeds(client: AsyncClient) -> None:
    """Volunteer can cancel their own signup."""
    shift = await create_test_shift(client, shift_date="2026-09-07", capacity=5)
    await client.post(f"/api/shifts/{shift['id']}/signup")

    cancel_resp = await client.delete(f"/api/shifts/{shift['id']}/signup")
    assert cancel_resp.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_signup_decrements_slots_filled(client: AsyncClient) -> None:
    """Cancelling a signup decrements slots_filled."""
    shift = await create_test_shift(client, shift_date="2026-09-08", capacity=5)
    await client.post(f"/api/shifts/{shift['id']}/signup")

    detail_before = (await client.get(f"/api/shifts/{shift['id']}")).json()
    filled_before = detail_before["slots_filled"]

    await client.delete(f"/api/shifts/{shift['id']}/signup")

    detail_after = (await client.get(f"/api/shifts/{shift['id']}")).json()
    assert detail_after["slots_filled"] == filled_before - 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_signup_reopens_full_shift(client: AsyncClient) -> None:
    """Cancelling the last signup transitions a full shift back to open."""
    shift = await create_test_shift(client, shift_date="2026-09-09", capacity=1)
    await client.post(f"/api/shifts/{shift['id']}/signup")

    full_resp = await client.get(f"/api/shifts/{shift['id']}")
    assert full_resp.json()["status"] == "full"

    await client.delete(f"/api/shifts/{shift['id']}/signup")

    open_resp = await client.get(f"/api/shifts/{shift['id']}")
    assert open_resp.json()["status"] == "open"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_without_signup_returns_404(client: AsyncClient) -> None:
    """Cancelling a signup that doesn't exist returns 404."""
    shift = await create_test_shift(client, shift_date="2026-09-10", capacity=5)

    cancel_resp = await client.delete(f"/api/shifts/{shift['id']}/signup")
    assert cancel_resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_for_nonexistent_shift_returns_404(client: AsyncClient) -> None:
    """Cancelling a signup for nonexistent shift returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000098"
    response = await client.delete(f"/api/shifts/{fake_id}/signup")
    assert response.status_code == 404
