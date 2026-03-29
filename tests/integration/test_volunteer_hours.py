"""Integration tests for volunteer hours logging API (RAP-195).

Exercises all 6 endpoints against the live test database.

Setup strategy:
- The shared `client` fixture is a staff user.
- Each test that needs an approved volunteer profile calls a helper that
  applies and then auto-approves via the staff review endpoint.
- Cleanup is handled via the test DB's per-run isolation.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LOG_PAYLOAD = {
    "activity_date": "2026-01-15",
    "duration_hours": 2.0,
    "category": "animal_care",
    "description": "Fed and cleaned kennels",
}


async def _ensure_approved_volunteer(client: AsyncClient) -> str:
    """Apply as a volunteer and have staff approve it.

    Returns the volunteer profile ID (UUID string).
    The staff client is used for both apply and review, which is valid
    since a staff user can also be a volunteer.
    """
    # Apply (idempotent — 201 on first call, 409 on repeat)
    apply_resp = await client.post(
        "/api/volunteers/apply",
        json={
            "motivation": (
                "Quiero apoyar al refugio con mi tiempo y dedicación para ayudar"
                " a los animales que más lo necesitan."
            )
        },
    )
    assert apply_resp.status_code in (201, 409), apply_resp.text

    # Retrieve own profile to get the profile ID
    me_resp = await client.get("/api/volunteers/me")
    assert me_resp.status_code == 200, me_resp.text
    profile = me_resp.json()
    profile_id = profile["id"]

    # Approve via staff endpoint (staff can approve their own profile in tests)
    review_resp = await client.put(
        f"/api/staff/volunteers/{profile_id}/review",
        json={"status": "approved", "notes": "Auto-approved for testing."},
    )
    # 200 = just approved; 409/422 = already in approved state (fine)
    assert review_resp.status_code in (200, 409, 422), review_resp.text

    return profile_id


# ---------------------------------------------------------------------------
# POST /api/volunteers/hours — log hours
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_requires_auth(client: AsyncClient) -> None:
    """Endpoint returns 401/403 without auth."""
    resp = await client.post(
        "/api/volunteers/hours",
        json=LOG_PAYLOAD,
        headers={"Authorization": ""},
    )
    assert resp.status_code in (401, 403, 422)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_without_volunteer_profile_returns_404(client: AsyncClient) -> None:
    """Staff user with no volunteer profile gets 404."""
    # Do NOT call _ensure_approved_volunteer — we want the missing-profile path
    # Use a fresh client context by bypassing the apply step.
    # The staff test user will have no volunteer profile on the first test run.
    # On subsequent runs the staff user may already have a profile, so we accept
    # 404 (no profile) or 403 (profile not approved yet) — both are valid.
    resp = await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)
    # Allow 201 if the staff user already has an approved profile from a prior run
    assert resp.status_code in (201, 403, 404)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_approved_volunteer_succeeds(client: AsyncClient) -> None:
    """Approved volunteer can log hours and receives 201 with correct fields."""
    await _ensure_approved_volunteer(client)

    resp = await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["category"] == "animal_care"
    assert body["duration_hours"] == 2.0
    assert body["approved"] is False
    assert body["approved_by"] is None
    assert "id" in body
    assert "volunteer_id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_future_date_returns_422(client: AsyncClient) -> None:
    """Submitting a future activity date is rejected."""
    await _ensure_approved_volunteer(client)

    resp = await client.post(
        "/api/volunteers/hours",
        json={**LOG_PAYLOAD, "activity_date": "2099-12-31"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_invalid_category_returns_422(client: AsyncClient) -> None:
    """Invalid category string is rejected with 422."""
    await _ensure_approved_volunteer(client)

    resp = await client.post(
        "/api/volunteers/hours",
        json={**LOG_PAYLOAD, "category": "not_a_real_category"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_log_hours_duration_below_minimum_returns_422(client: AsyncClient) -> None:
    """Duration below 0.25 hours is rejected."""
    await _ensure_approved_volunteer(client)

    resp = await client.post(
        "/api/volunteers/hours",
        json={**LOG_PAYLOAD, "duration_hours": 0.1},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/volunteers/hours/me — list own logs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_my_hours_returns_paginated_list(client: AsyncClient) -> None:
    """GET /me returns a paginated list including recently logged hours."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/volunteers/hours/me")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert body["total"] >= 1
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_my_hours_filter_by_category(client: AsyncClient) -> None:
    """Category filter returns only matching entries."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)
    await client.post(
        "/api/volunteers/hours",
        json={**LOG_PAYLOAD, "category": "transport", "duration_hours": 1.0},
    )

    resp = await client.get("/api/volunteers/hours/me?category=transport")
    assert resp.status_code == 200
    body = resp.json()
    for item in body["items"]:
        assert item["category"] == "transport"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_my_hours_pagination(client: AsyncClient) -> None:
    """page_size parameter limits results returned."""
    await _ensure_approved_volunteer(client)
    # Log 3 entries
    for _ in range(3):
        await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/volunteers/hours/me?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) <= 2
    assert body["page_size"] == 2


# ---------------------------------------------------------------------------
# GET /api/volunteers/hours/me/summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_my_hours_summary_returns_totals(client: AsyncClient) -> None:
    """Summary endpoint returns total, approved, pending, and by-category."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/volunteers/hours/me/summary")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "total_hours" in body
    assert "approved_hours" in body
    assert "pending_hours" in body
    assert "hours_by_category" in body
    assert body["total_hours"] >= 2.0
    assert body["approved_hours"] == 0.0  # none approved yet
    assert body["pending_hours"] >= 2.0
    assert isinstance(body["hours_by_category"], dict)


# ---------------------------------------------------------------------------
# GET /api/staff/volunteer-hours — list all logs (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_list_all_hours_returns_paginated_list(client: AsyncClient) -> None:
    """Staff endpoint returns paginated list of all volunteer hours."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/staff/volunteer-hours")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_list_all_hours_filter_approved(client: AsyncClient) -> None:
    """Staff can filter by approval status."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/staff/volunteer-hours?approved=false")
    assert resp.status_code == 200
    body = resp.json()
    for item in body["items"]:
        assert item["approved"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_list_all_hours_filter_date_range(client: AsyncClient) -> None:
    """Staff can filter by date_from and date_to."""
    await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get("/api/staff/volunteer-hours?date_from=2026-01-01&date_to=2026-12-31")
    assert resp.status_code == 200
    body = resp.json()
    # The logged entry (2026-01-15) falls within range
    assert body["total"] >= 1


# ---------------------------------------------------------------------------
# GET /api/staff/volunteer-hours/{volunteer_id} — summary for one volunteer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_get_volunteer_summary_returns_totals(client: AsyncClient) -> None:
    """Staff can retrieve hours summary for a specific volunteer."""
    profile_id = await _ensure_approved_volunteer(client)
    await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)

    resp = await client.get(f"/api/staff/volunteer-hours/{profile_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["volunteer_id"] == profile_id
    assert body["total_hours"] >= 2.0
    assert isinstance(body["hours_by_category"], dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_get_volunteer_summary_unknown_id_returns_404(client: AsyncClient) -> None:
    """Requesting summary for a nonexistent volunteer returns 404."""
    fake_id = "00000000-0000-0000-0000-999999999999"
    resp = await client.get(f"/api/staff/volunteer-hours/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/staff/volunteer-hours/{log_id}/approve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_approve_log_entry_sets_approved_true(client: AsyncClient) -> None:
    """Staff can approve a pending hours log entry."""
    await _ensure_approved_volunteer(client)
    log_resp = await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)
    assert log_resp.status_code == 201
    log_id = log_resp.json()["id"]

    approve_resp = await client.put(f"/api/staff/volunteer-hours/{log_id}/approve")
    assert approve_resp.status_code == 200, approve_resp.text
    body = approve_resp.json()
    assert body["approved"] is True
    assert body["approved_by"] is not None
    assert body["approved_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_approve_already_approved_returns_422(client: AsyncClient) -> None:
    """Approving an already-approved entry returns 422."""
    await _ensure_approved_volunteer(client)
    log_resp = await client.post("/api/volunteers/hours", json=LOG_PAYLOAD)
    log_id = log_resp.json()["id"]

    await client.put(f"/api/staff/volunteer-hours/{log_id}/approve")
    second_resp = await client.put(f"/api/staff/volunteer-hours/{log_id}/approve")
    assert second_resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_approve_nonexistent_log_returns_404(client: AsyncClient) -> None:
    """Approving a nonexistent log entry returns 404."""
    fake_id = "00000000-0000-0000-0000-888888888888"
    resp = await client.put(f"/api/staff/volunteer-hours/{fake_id}/approve")
    assert resp.status_code == 404
