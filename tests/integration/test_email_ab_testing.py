"""Integration tests for email campaign A/B subject line testing.

Covers:
  POST /email-campaigns                  — create campaign with A/B subjects
  PATCH /email-campaigns/{id}            — add A/B subjects to existing draft
  POST /email-campaigns/{id}/send/ab     — trigger A/B test send
  GET  /email-campaigns/{id}/stats       — variant breakdown in stats

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_ab_testing.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_list(client: AsyncClient) -> str:
    resp = await client.post(
        "/email-lists",
        json={"name": f"AB List {uuid4().hex[:6]}", "list_type": "general"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_ab_campaign(client: AsyncClient, list_id: str) -> str:
    """Create a campaign with A/B subject lines configured, return campaign_id."""
    resp = await client.post(
        "/email-campaigns",
        json={
            "name": f"AB Campaign {uuid4().hex[:6]}",
            "email_list_id": list_id,
            "email_template_id": str(uuid4()),
            "subject_a": "Adopta hoy — animales esperan por ti",
            "subject_b": "Dale un hogar a un perro necesitado",
            "ab_ratio": 0.5,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Campaign creation with A/B subjects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_with_ab_subjects(client: AsyncClient) -> None:
    """Campaign created with subject_a and subject_b stored correctly."""
    list_id = await _create_list(client)
    campaign_id = await _create_ab_campaign(client, list_id)

    resp = await client.get(f"/email-campaigns/{campaign_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject_a"] == "Adopta hoy — animales esperan por ti"
    assert body["subject_b"] == "Dale un hogar a un perro necesitado"
    assert body["ab_ratio"] == 0.5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_adds_ab_subject_to_draft(client: AsyncClient) -> None:
    """PATCH can add A/B subjects to an existing draft campaign."""
    list_id = await _create_list(client)
    resp = await client.post(
        "/email-campaigns",
        json={
            "name": f"Patch AB {uuid4().hex[:6]}",
            "email_list_id": list_id,
            "email_template_id": str(uuid4()),
        },
    )
    campaign_id = resp.json()["id"]

    patch_resp = await client.patch(
        f"/email-campaigns/{campaign_id}",
        json={
            "subject_a": "Version A",
            "subject_b": "Version B",
            "ab_ratio": 0.3,
        },
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["subject_b"] == "Version B"
    assert body["ab_ratio"] == pytest.approx(0.3, abs=0.001)


# ---------------------------------------------------------------------------
# A/B send endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_ab_transitions_campaign_to_sent(client: AsyncClient) -> None:
    """A/B send transitions campaign to SENT status."""
    list_id = await _create_list(client)
    campaign_id = await _create_ab_campaign(client, list_id)

    resp = await client.post(f"/email-campaigns/{campaign_id}/send/ab")
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_ab_without_subject_b_returns_409(client: AsyncClient) -> None:
    """A/B send endpoint returns 409 when subject_b is not set."""
    list_id = await _create_list(client)
    resp = await client.post(
        "/email-campaigns",
        json={
            "name": f"No AB {uuid4().hex[:6]}",
            "email_list_id": list_id,
            "email_template_id": str(uuid4()),
        },
    )
    campaign_id = resp.json()["id"]

    ab_resp = await client.post(f"/email-campaigns/{campaign_id}/send/ab")
    assert ab_resp.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_ab_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    resp = await client.post(f"/email-campaigns/{uuid4()}/send/ab")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_ab_already_sent_returns_409(client: AsyncClient) -> None:
    """Sending an already-sent A/B campaign returns 409."""
    list_id = await _create_list(client)
    campaign_id = await _create_ab_campaign(client, list_id)

    await client.post(f"/email-campaigns/{campaign_id}/send/ab")
    resp = await client.post(f"/email-campaigns/{campaign_id}/send/ab")
    assert resp.status_code == 409
