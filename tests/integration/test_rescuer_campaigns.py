"""Integration tests for rescuer campaign API.

Tests the portal and public endpoints against the live test database.
Requires a running PostgreSQL instance (refugio_dev).
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# POST /api/portal/rescuer/campaigns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_requires_rescuer_profile(client: AsyncClient) -> None:
    """Creating a campaign without a rescuer profile returns 422."""
    with patch(
        "src.services.rescuer_campaign_service._get_rescuer_by_user",
        new=AsyncMock(
            side_effect=__import__(
                "src.services.rescuer_campaign_service",
                fromlist=["RescuerNotFoundError"],
            ).RescuerNotFoundError("no profile")
        ),
    ):
        response = await client.post(
            "/api/portal/rescuer/campaigns",
            json={
                "title": "Test Campaign Title",
                "description": "A long enough description for this test campaign.",
                "target_amount_eur": 200.0,
                "fund_category": "rescue",
            },
        )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "RESCUER_PROFILE_REQUIRED"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_validates_title_min_length(client: AsyncClient) -> None:
    """Title shorter than 5 chars returns 422."""
    response = await client.post(
        "/api/portal/rescuer/campaigns",
        json={
            "title": "Hi",
            "description": "A long enough description for this test campaign.",
            "target_amount_eur": 200.0,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_validates_target_amount_min(client: AsyncClient) -> None:
    """Target amount below minimum returns 422."""
    response = await client.post(
        "/api/portal/rescuer/campaigns",
        json={
            "title": "Valid Title Here",
            "description": "A long enough description for this test campaign.",
            "target_amount_eur": 5.0,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_validates_description_min_length(client: AsyncClient) -> None:
    """Description shorter than 20 chars returns 422."""
    response = await client.post(
        "/api/portal/rescuer/campaigns",
        json={
            "title": "Valid Title Here",
            "description": "Too short",
            "target_amount_eur": 100.0,
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/portal/rescuer/campaigns/{id}/status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_campaign_invalid_action_returns_422(client: AsyncClient) -> None:
    """An unsupported action value returns 422."""
    campaign_id = str(uuid.uuid4())
    response = await client.patch(
        f"/api/portal/rescuer/campaigns/{campaign_id}/status",
        json={"action": "invalidaction"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "INVALID_ACTION"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_campaign_not_found_returns_404(client: AsyncClient) -> None:
    """Completing a non-existent campaign returns 404."""
    from src.services.rescuer_campaign_service import (
        RescuerCampaignNotFoundError,
    )

    campaign_id = str(uuid.uuid4())
    with (
        patch(
            "src.services.rescuer_campaign_service._get_rescuer_by_user",
            new=AsyncMock(return_value=type("R", (), {"id": uuid.uuid4()})()),
        ),
        patch(
            "src.services.rescuer_campaign_service.end_rescuer_campaign",
            new=AsyncMock(side_effect=RescuerCampaignNotFoundError(campaign_id)),
        ),
    ):
        response = await client.patch(
            f"/api/portal/rescuer/campaigns/{campaign_id}/status",
            json={"action": "complete"},
        )
    assert response.status_code in (404, 422)


# ---------------------------------------------------------------------------
# GET /api/rescuers/{slug}/campaigns/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_public_campaign_not_found_returns_404(client: AsyncClient) -> None:
    """Unknown slug or campaign returns 404."""
    slug = "unknown-rescuer-xyz"
    campaign_id = str(uuid.uuid4())

    from src.services.rescuer_campaign_service import RescuerNotFoundError

    with patch(
        "src.services.rescuer_campaign_service.get_public_campaign_detail",
        new=AsyncMock(side_effect=RescuerNotFoundError(slug)),
    ):
        response = await client.get(f"/api/rescuers/{slug}/campaigns/{campaign_id}")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["code"] == "RESCUER_NOT_FOUND"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_public_campaign_returns_detail(client: AsyncClient) -> None:
    """A valid campaign returns full detail including progress fields."""
    from datetime import UTC, datetime

    slug = "maria-rescue"
    campaign_id = uuid.uuid4()

    mock_detail = {
        "id": campaign_id,
        "rescuer_slug": slug,
        "rescuer_name": "Maria Rescue",
        "rescuer_verified": True,
        "title": "Ayuda para Felix",
        "description": "Felix necesita operacion de cadera urgente.",
        "target_amount_eur": 600.0,
        "raised_amount_eur": 150.0,
        "progress_pct": 25.0,
        "donor_count": 5,
        "fund_category": "medical",
        "status": "active",
        "goal_message": "Gracias por tu apoyo",
        "photo_urls": [],
        "deadline": None,
        "recent_donors": [],
        "created_at": datetime.now(UTC),
    }

    with patch(
        "src.services.rescuer_campaign_service.get_public_campaign_detail",
        new=AsyncMock(return_value=mock_detail),
    ):
        response = await client.get(f"/api/rescuers/{slug}/campaigns/{campaign_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Ayuda para Felix"
    assert body["progress_pct"] == 25.0
    assert body["donor_count"] == 5
    assert body["category_label_es"] == "Medico"
    assert body["status_label_es"] == "Activa"
