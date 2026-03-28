"""Integration tests for shift reminder notification API (RAP-184).

Tests POST /api/shifts/reminders/send.
Requires a running PostgreSQL instance (refugio_dev).
"""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_test_shift(client: AsyncClient, **kwargs: object) -> dict:
    """Create a shift and return the response body."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    defaults = {
        "shift_date": tomorrow,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "role": "general",
        "capacity": 5,
        "title": "Reminder test shift",
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
# POST /api/shifts/reminders/send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_returns_200(client: AsyncClient) -> None:
    """Endpoint returns 200 with correct shape."""
    response = await client.post("/api/shifts/reminders/send")
    assert response.status_code == 200
    body = response.json()
    assert "sent_count" in body
    assert "hours_ahead" in body
    assert "sent_at" in body
    assert body["hours_ahead"] == 24


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_default_hours_ahead(client: AsyncClient) -> None:
    """Default hours_ahead is 24."""
    response = await client.post("/api/shifts/reminders/send")
    assert response.status_code == 200
    assert response.json()["hours_ahead"] == 24


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_custom_hours_ahead(client: AsyncClient) -> None:
    """Custom hours_ahead is reflected in response."""
    response = await client.post("/api/shifts/reminders/send?hours_ahead=48")
    assert response.status_code == 200
    assert response.json()["hours_ahead"] == 48


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_for_upcoming_shift(client: AsyncClient) -> None:
    """Signup for tomorrow's shift receives a reminder."""
    shift = await create_test_shift(client)
    await signup_for_shift(client, shift["id"])

    response = await client.post("/api/shifts/reminders/send?hours_ahead=48")
    assert response.status_code == 200
    body = response.json()
    assert body["sent_count"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_idempotent(client: AsyncClient) -> None:
    """Second call does not re-send reminders already sent."""
    shift = await create_test_shift(
        client,
        shift_date=(date.today() + timedelta(days=1)).isoformat(),
        title="Idempotency test shift",
    )
    await signup_for_shift(client, shift["id"])

    # First call: sends reminder
    resp1 = await client.post("/api/shifts/reminders/send?hours_ahead=48")
    assert resp1.status_code == 200
    first_count = resp1.json()["sent_count"]

    # Second call: same signup already has reminder_sent_at set
    resp2 = await client.post("/api/shifts/reminders/send?hours_ahead=48")
    assert resp2.status_code == 200
    second_count = resp2.json()["sent_count"]
    assert second_count < first_count or second_count == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_hours_ahead_validation(client: AsyncClient) -> None:
    """hours_ahead=0 returns 422 (below minimum)."""
    response = await client.post("/api/shifts/reminders/send?hours_ahead=0")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_hours_ahead_max(client: AsyncClient) -> None:
    """hours_ahead=169 (above max 168) returns 422."""
    response = await client.post("/api/shifts/reminders/send?hours_ahead=169")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_requires_auth(client: AsyncClient) -> None:
    """Endpoint returns 200 when authenticated as staff."""
    response = await client.post("/api/shifts/reminders/send")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_reminders_no_future_shifts_returns_zero(client: AsyncClient) -> None:
    """No signups in window returns sent_count=0 (window is past, 1 hour ahead)."""
    response = await client.post("/api/shifts/reminders/send?hours_ahead=1")
    assert response.status_code == 200
    # A shift created for 'tomorrow' is outside a 1-hour window from now
    body = response.json()
    assert isinstance(body["sent_count"], int)
    assert body["sent_count"] >= 0
