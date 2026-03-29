"""Integration tests for email campaign open/click tracking endpoints.

Covers:
  GET /email-campaigns/track/open/{campaign_id}   — pixel endpoint (public)
  GET /email-campaigns/track/click/{campaign_id}  — redirect endpoint (public)
  GET /email-campaigns/{campaign_id}/stats        — stats endpoint (staff)

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_tracking.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_list_and_campaign(client: AsyncClient) -> tuple[str, str]:
    """Create a supporting list and a sent campaign, return (list_id, campaign_id)."""
    list_resp = await client.post(
        "/email-lists",
        json={"name": f"Tracking List {uuid4().hex[:6]}", "list_type": "general"},
    )
    assert list_resp.status_code == 201
    list_id = list_resp.json()["id"]

    campaign_resp = await client.post(
        "/email-campaigns",
        json={
            "name": f"Tracking Campaign {uuid4().hex[:6]}",
            "email_list_id": list_id,
            "email_template_id": str(uuid4()),
        },
    )
    assert campaign_resp.status_code == 201
    campaign_id = campaign_resp.json()["id"]

    # Transition to SENT via send endpoint
    send_resp = await client.post(f"/email-campaigns/{campaign_id}/send")
    assert send_resp.status_code == 200
    assert send_resp.json()["status"] == "sent"

    return list_id, campaign_id


# ---------------------------------------------------------------------------
# Open tracking (pixel)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_track_open_returns_gif_pixel(client: AsyncClient) -> None:
    """Pixel endpoint returns a 1x1 GIF with cache-control headers."""
    _, campaign_id = await _create_list_and_campaign(client)

    response = await client.get(f"/email-campaigns/track/open/{campaign_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert "no-cache" in response.headers.get("cache-control", "")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_track_open_for_nonexistent_campaign_still_returns_pixel(
    client: AsyncClient,
) -> None:
    """Pixel is returned even for unknown campaigns — never breaks email display."""
    response = await client.get(f"/email-campaigns/track/open/{uuid4()}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"


# ---------------------------------------------------------------------------
# Click tracking (redirect)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_track_click_redirects_to_target_url(client: AsyncClient) -> None:
    """Click endpoint returns 302 to the specified destination."""
    _, campaign_id = await _create_list_and_campaign(client)
    target = "https://refugio.example.com/adopt"

    response = await client.get(
        f"/email-campaigns/track/click/{campaign_id}",
        params={"url": target},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == target


@pytest.mark.asyncio
@pytest.mark.integration
async def test_track_click_nonexistent_campaign_still_redirects(
    client: AsyncClient,
) -> None:
    """Click endpoint redirects even for unknown campaigns to not strand users."""
    target = "https://refugio.example.com"
    response = await client.get(
        f"/email-campaigns/track/click/{uuid4()}",
        params={"url": target},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == target


# ---------------------------------------------------------------------------
# Stats endpoint (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_returns_zero_counts_before_any_events(client: AsyncClient) -> None:
    """Stats for a freshly sent campaign shows zero events."""
    _, campaign_id = await _create_list_and_campaign(client)

    response = await client.get(f"/email-campaigns/{campaign_id}/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["opens"] == 0
    assert body["clicks"] == 0
    assert body["campaign_id"] == campaign_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_counts_increase_after_open_event(client: AsyncClient) -> None:
    """Opens counter increments after pixel endpoint is called."""
    _, campaign_id = await _create_list_and_campaign(client)

    # Trigger open
    await client.get(f"/email-campaigns/track/open/{campaign_id}")

    stats = await client.get(f"/email-campaigns/{campaign_id}/stats")
    assert stats.status_code == 200
    assert stats.json()["opens"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_counts_increase_after_click_event(client: AsyncClient) -> None:
    """Clicks counter increments after click tracking endpoint is called."""
    _, campaign_id = await _create_list_and_campaign(client)

    await client.get(
        f"/email-campaigns/track/click/{campaign_id}",
        params={"url": "https://example.com"},
        follow_redirects=False,
    )

    stats = await client.get(f"/email-campaigns/{campaign_id}/stats")
    assert stats.status_code == 200
    assert stats.json()["clicks"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_stats_returns_404_for_nonexistent_campaign(client: AsyncClient) -> None:
    """Stats endpoint returns 404 for unknown campaign ID."""
    response = await client.get(f"/email-campaigns/{uuid4()}/stats")
    assert response.status_code == 404
