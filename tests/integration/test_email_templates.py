"""Integration tests for email template management endpoints.

Covers:
  POST   /email-templates          — create template (staff only)
  GET    /email-templates          — list templates (staff only)
  GET    /email-templates/{id}     — get detail (staff only)
  PATCH  /email-templates/{id}     — update template
  DELETE /email-templates/{id}     — archive template

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_templates.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _make_template_data(**overrides: object) -> dict:
    defaults: dict = {
        "name": f"Test Template {uuid4().hex[:6]}",
        "description": "Integration test template",
        "subject": "Test Subject Line",
        "html_body": "<html><body><h1>Hello</h1></body></html>",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_template_returns_201(client: AsyncClient) -> None:
    data = _make_template_data()
    response = await client.post("/email-templates", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == data["name"]
    assert body["subject"] == "Test Subject Line"
    assert body["status"] == "draft"
    assert body["html_body"] == "<html><body><h1>Hello</h1></body></html>"
    assert body["text_body"] is None
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_template_with_text_body(client: AsyncClient) -> None:
    data = _make_template_data(text_body="Plain text fallback")
    response = await client.post("/email-templates", json=data)
    assert response.status_code == 201
    assert response.json()["text_body"] == "Plain text fallback"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_templates(client: AsyncClient) -> None:
    await client.post("/email-templates", json=_make_template_data())
    response = await client.get("/email-templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    # Summary shape: no html_body in list view
    first = response.json()[0]
    assert "name" in first
    assert "subject" in first
    assert "status" in first


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_template_detail(client: AsyncClient) -> None:
    create = await client.post("/email-templates", json=_make_template_data())
    template_id = create.json()["id"]

    response = await client.get(f"/email-templates/{template_id}")
    assert response.status_code == 200
    assert response.json()["id"] == template_id
    assert "html_body" in response.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_template_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/email-templates/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_template_subject(client: AsyncClient) -> None:
    create = await client.post("/email-templates", json=_make_template_data())
    template_id = create.json()["id"]

    response = await client.patch(
        f"/email-templates/{template_id}",
        json={"subject": "Updated Subject"},
    )
    assert response.status_code == 200
    assert response.json()["subject"] == "Updated Subject"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_activate_template(client: AsyncClient) -> None:
    create = await client.post("/email-templates", json=_make_template_data())
    template_id = create.json()["id"]

    response = await client.patch(f"/email-templates/{template_id}", json={"status": "active"})
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_archive_template(client: AsyncClient) -> None:
    create = await client.post("/email-templates", json=_make_template_data())
    template_id = create.json()["id"]

    response = await client.delete(f"/email-templates/{template_id}")
    assert response.status_code == 204

    detail = await client.get(f"/email-templates/{template_id}")
    assert detail.json()["status"] == "archived"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_filter_by_status(client: AsyncClient) -> None:
    create = await client.post("/email-templates", json=_make_template_data())
    template_id = create.json()["id"]
    await client.patch(f"/email-templates/{template_id}", json={"status": "active"})

    response = await client.get("/email-templates?status=active")
    assert response.status_code == 200
    statuses = [t["status"] for t in response.json()]
    assert all(s == "active" for s in statuses)
