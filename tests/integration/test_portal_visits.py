"""Integration tests for portal visit scheduling endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_portal_visits.py
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

_ADOPTER_VISIT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000030")
_ADOPTER_VISIT_EMAIL = "test-portal-visits@refugio.test"


@pytest_asyncio.fixture
async def adopter_visit_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient for an adopter with a matching adopter profile."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'adopter', true)
                ON CONFLICT (email) DO NOTHING
                """),
            {
                "id": str(_ADOPTER_VISIT_USER_ID),
                "email": _ADOPTER_VISIT_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        await session.execute(
            text("""
                INSERT INTO adopters (full_name, email, gdpr_consent_at)
                VALUES (:full_name, :email, NOW())
                ON CONFLICT (email) DO NOTHING
                """),
            {"full_name": "Visit Test Adopter", "email": _ADOPTER_VISIT_EMAIL},
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_ADOPTER_VISIT_USER_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# GET /portal/visits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_visits_returns_empty_for_new_adopter(
    adopter_visit_client: AsyncClient,
) -> None:
    """Newly created adopter with no visits or requests gets empty dashboard."""
    resp = await adopter_visit_client.get("/portal/visits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "scheduled_visits" in body
    assert "pending_requests" in body
    assert body["total_scheduled"] == 0
    assert body["total_pending"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_visits_requires_auth() -> None:
    """Unauthenticated request returns 401 or 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as unauthenticated:
        resp = await unauthenticated.get("/portal/visits")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# POST /portal/visit-requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_visit_fails_for_nonexistent_adoption(
    adopter_visit_client: AsyncClient,
) -> None:
    """Visit request for an adoption that doesn't exist returns 404."""
    payload = {
        "adoption_request_id": str(uuid.uuid4()),
        "proposed_slots": ["2026-04-10T10:00:00Z"],
        "address": "Test Street 1, Asunción",
    }
    resp = await adopter_visit_client.post("/portal/visit-requests", json=payload)
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_visit_requires_at_least_one_slot(
    adopter_visit_client: AsyncClient,
) -> None:
    """Visit request with zero slots is rejected by validation."""
    payload = {
        "adoption_request_id": str(uuid.uuid4()),
        "proposed_slots": [],
        "address": "Test Street 1, Asunción",
    }
    resp = await adopter_visit_client.post("/portal/visit-requests", json=payload)
    # FastAPI schema validation (422) or service validation (400)
    assert resp.status_code in (400, 422), resp.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_visit_requires_auth() -> None:
    """Unauthenticated visit request returns 401 or 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as unauthenticated:
        resp = await unauthenticated.post(
            "/portal/visit-requests",
            json={
                "adoption_request_id": str(uuid.uuid4()),
                "proposed_slots": ["2026-04-10T10:00:00Z"],
                "address": "Test address",
            },
        )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# DELETE /portal/visit-requests/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_nonexistent_request_returns_404(
    adopter_visit_client: AsyncClient,
) -> None:
    """Cancelling a request that doesn't exist returns 404."""
    fake_id = uuid.uuid4()
    resp = await adopter_visit_client.delete(f"/portal/visit-requests/{fake_id}")
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# GET /admin/visit-requests (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_can_list_pending_requests(client: AsyncClient) -> None:
    """Staff can view all pending visit requests."""
    resp = await client.get("/admin/visit-requests")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adopter_cannot_access_staff_visit_requests(
    adopter_visit_client: AsyncClient,
) -> None:
    """Adopter role cannot access the admin visit requests endpoint."""
    resp = await adopter_visit_client.get("/admin/visit-requests")
    assert resp.status_code in (401, 403)
