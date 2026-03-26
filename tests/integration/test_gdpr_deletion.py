"""Integration tests for GDPR data deletion endpoints.

Tests the GDPR deletion API endpoints with live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_gdpr_deletion.py
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_deletion_requests_table(settings: Settings) -> None:
    """Create deletion_requests table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subject_type VARCHAR(20) NOT NULL,
                subject_id UUID NOT NULL,
                subject_email VARCHAR(255) NOT NULL,
                reason TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                requested_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                approved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                denial_reason TEXT,
                requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                approved_at TIMESTAMPTZ,
                executed_at TIMESTAMPTZ,
                cancelled_at TIMESTAMPTZ,
                CONSTRAINT chk_deletion_request_subject_type CHECK (
                    subject_type IN ('donor', 'adopter', 'staff')
                ),
                CONSTRAINT chk_deletion_request_status CHECK (
                    status IN ('pending', 'approved', 'executed', 'cancelled', 'denied')
                )
            )
        """))
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_deletion_table() -> None:
    """Ensure deletion_requests table exists."""
    settings = Settings()
    await _ensure_deletion_requests_table(settings)


# ---------------------------------------------------------------------------
# POST /gdpr/deletion-requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_deletion_request_returns_201(client: AsyncClient) -> None:
    """Creating a deletion request returns 201."""
    response = await client.post(
        "/gdpr/deletion-requests",
        json={
            "subject_type": "donor",
            "subject_id": str(uuid4()),
            "subject_email": "test@example.com",
            "reason": "Data subject requested deletion",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["subject_type"] == "donor"
    assert body["status"] == "pending"
    assert body["reason"] == "Data subject requested deletion"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_deletion_request_invalid_type_returns_422(
    client: AsyncClient,
) -> None:
    """Invalid subject type returns 422."""
    response = await client.post(
        "/gdpr/deletion-requests",
        json={
            "subject_type": "invalid",
            "subject_id": str(uuid4()),
            "subject_email": "test@example.com",
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /gdpr/deletion-requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_deletion_requests_returns_200(client: AsyncClient) -> None:
    """Listing deletion requests returns 200."""
    response = await client.get("/gdpr/deletion-requests")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert "count" in body


# ---------------------------------------------------------------------------
# GET /gdpr/deletion-requests/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_request_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent request returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/gdpr/deletion-requests/{fake_id}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /gdpr/deletion-requests/{id}/cancel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_nonexistent_request_returns_404(client: AsyncClient) -> None:
    """Cancelling a non-existent request returns 404."""
    fake_id = uuid4()
    response = await client.post(f"/gdpr/deletion-requests/{fake_id}/cancel")

    assert response.status_code == 404
