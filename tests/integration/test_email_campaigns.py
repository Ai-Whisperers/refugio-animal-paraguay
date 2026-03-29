"""Integration tests for email campaign endpoints.

Covers:
  POST   /email-campaigns                    -- create draft campaign (staff)
  GET    /email-campaigns                    -- list campaigns (staff)
  GET    /email-campaigns/{id}               -- get detail (staff)
  PATCH  /email-campaigns/{id}               -- update draft (staff)
  DELETE /email-campaigns/{id}               -- cancel campaign (staff)
  POST   /email-campaigns/{id}/schedule      -- schedule draft (staff)
  POST   /email-campaigns/{id}/send          -- immediate send (staff)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_campaigns.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _make_campaign_data(email_list_id: str, **overrides: object) -> dict:
    defaults: dict = {
        "name": f"Test Campaign {uuid4().hex[:6]}",
        "description": "Integration test email campaign",
        "email_list_id": email_list_id,
        "email_template_id": str(uuid4()),
        "scheduled_at": None,
    }
    defaults.update(overrides)
    return defaults


async def _create_list(client: AsyncClient) -> str:
    """Create a supporting email list and return its ID."""
    response = await client.post(
        "/email-lists",
        json={
            "name": f"Campaign Test List {uuid4().hex[:6]}",
            "list_type": "general",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_returns_201(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    data = _make_campaign_data(list_id)
    response = await client.post("/email-campaigns", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == data["name"]
    assert body["status"] == "draft"
    assert body["sent_count"] == 0
    assert body["total_recipients"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_without_name_returns_422(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    data = _make_campaign_data(list_id)
    del data["name"]
    response = await client.post("/email-campaigns", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_campaigns_returns_200(client: AsyncClient) -> None:
    response = await client.get("/email-campaigns")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_campaign_returns_200(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    response = await client.get(f"/email-campaigns/{campaign_id}")
    assert response.status_code == 200
    assert response.json()["id"] == campaign_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/email-campaigns/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_campaigns_filter_by_status(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    await client.post("/email-campaigns", json=_make_campaign_data(list_id))

    response = await client.get("/email-campaigns?status=draft")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert all(c["status"] == "draft" for c in body)


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_draft_campaign_updates_name(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    new_name = f"Updated {uuid4().hex[:6]}"
    response = await client.patch(
        f"/email-campaigns/{campaign_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    assert response.json()["name"] == new_name


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        f"/email-campaigns/{uuid4()}",
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Cancel (DELETE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_draft_campaign_returns_204(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    response = await client.delete(f"/email-campaigns/{campaign_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"/email-campaigns/{uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schedule_draft_campaign_transitions_to_scheduled(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    data = _make_campaign_data(list_id, scheduled_at="2027-01-01T12:00:00Z")
    create_resp = await client.post("/email-campaigns", json=data)
    campaign_id = create_resp.json()["id"]

    response = await client.post(f"/email-campaigns/{campaign_id}/schedule")
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schedule_campaign_without_scheduled_at_returns_409(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    response = await client.post(f"/email-campaigns/{campaign_id}/schedule")
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schedule_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    response = await client.post(f"/email-campaigns/{uuid4()}/schedule")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_draft_campaign_transitions_to_sent(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    response = await client.post(f"/email-campaigns/{campaign_id}/send")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_already_sent_campaign_returns_409(client: AsyncClient) -> None:
    list_id = await _create_list(client)
    create_resp = await client.post("/email-campaigns", json=_make_campaign_data(list_id))
    campaign_id = create_resp.json()["id"]

    await client.post(f"/email-campaigns/{campaign_id}/send")
    response = await client.post(f"/email-campaigns/{campaign_id}/send")
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    response = await client.post(f"/email-campaigns/{uuid4()}/send")
    assert response.status_code == 404
