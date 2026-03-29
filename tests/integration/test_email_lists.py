"""Integration tests for email list management endpoints.

Covers:
  POST   /email-lists              -- create list (staff only)
  GET    /email-lists              -- list all (staff only)
  GET    /email-lists/{id}         -- get detail (staff only)
  PATCH  /email-lists/{id}         -- update (staff only)
  DELETE /email-lists/{id}         -- archive (staff only)
  POST   /email-lists/{id}/members -- add member (staff only)
  GET    /email-lists/{id}/members -- list members (staff only)
  PATCH  /email-lists/{id}/members/{mid} -- update member
  DELETE /email-lists/{id}/members/{mid} -- remove member
  GET    /email-lists/unsubscribe/{token} -- public opt-out

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_lists.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


def _make_list_data(**overrides: object) -> dict:
    defaults: dict = {
        "name": f"Test List {uuid4().hex[:6]}",
        "description": "Integration test email list",
        "list_type": "general",
    }
    defaults.update(overrides)
    return defaults


def _make_member_data(**overrides: object) -> dict:
    defaults: dict = {
        "email": f"test-{uuid4().hex[:6]}@example.com",
        "name": "Test Subscriber",
        "source_type": "manual",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# List CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_email_list_returns_201(client: AsyncClient) -> None:
    data = _make_list_data()
    response = await client.post("/email-lists", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == data["name"]
    assert body["list_type"] == "general"
    assert body["status"] == "active"
    assert body["subscriber_count"] == 0
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_email_list_with_type(client: AsyncClient) -> None:
    data = _make_list_data(list_type="donors", description=None)
    response = await client.post("/email-lists", json=data)
    assert response.status_code == 201
    assert response.json()["list_type"] == "donors"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_email_lists(client: AsyncClient) -> None:
    # Create a list first
    await client.post("/email-lists", json=_make_list_data())
    response = await client.get("/email-lists")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_email_list_detail(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    response = await client.get(f"/email-lists/{list_id}")
    assert response.status_code == 200
    assert response.json()["id"] == list_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_email_list_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/email-lists/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_email_list_name(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    response = await client.patch(f"/email-lists/{list_id}", json={"name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_archive_email_list(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    response = await client.delete(f"/email-lists/{list_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/email-lists/{list_id}")
    assert get_resp.json()["status"] == "archived"


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_member_returns_201(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    member_data = _make_member_data()
    response = await client.post(f"/email-lists/{list_id}/members", json=member_data)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == member_data["email"].lower()
    assert body["status"] == "subscribed"
    assert "unsubscribe_token" not in body  # token not exposed in API


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_duplicate_member_returns_409(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    member_data = _make_member_data()
    await client.post(f"/email-lists/{list_id}/members", json=member_data)
    response = await client.post(f"/email-lists/{list_id}/members", json=member_data)
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_members(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    await client.post(f"/email-lists/{list_id}/members", json=_make_member_data())
    response = await client.get(f"/email-lists/{list_id}/members")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_member_status(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    add = await client.post(f"/email-lists/{list_id}/members", json=_make_member_data())
    member_id = add.json()["id"]

    response = await client.patch(
        f"/email-lists/{list_id}/members/{member_id}",
        json={"status": "unsubscribed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "unsubscribed"
    assert response.json()["unsubscribed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_remove_member(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    add = await client.post(f"/email-lists/{list_id}/members", json=_make_member_data())
    member_id = add.json()["id"]

    response = await client.delete(f"/email-lists/{list_id}/members/{member_id}")
    assert response.status_code == 204

    members = await client.get(f"/email-lists/{list_id}/members")
    assert len(members.json()) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_subscriber_count_updates_after_member_add(client: AsyncClient) -> None:
    create = await client.post("/email-lists", json=_make_list_data())
    list_id = create.json()["id"]

    await client.post(f"/email-lists/{list_id}/members", json=_make_member_data())
    await client.post(f"/email-lists/{list_id}/members", json=_make_member_data())

    detail = await client.get(f"/email-lists/{list_id}")
    assert detail.json()["subscriber_count"] == 2


# ---------------------------------------------------------------------------
# Unsubscribe (public)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unsubscribe_invalid_token_returns_404(client: AsyncClient) -> None:
    response = await client.get("/email-lists/unsubscribe/invalid_token_that_does_not_exist")
    assert response.status_code == 404
