"""Integration tests for GDPR data export endpoints.

Tests the GDPR API endpoints with live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_gdpr.py
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


async def _ensure_data_export_table(settings: Settings) -> None:
    """Create data_export_requests table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS data_export_requests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                requested_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                subject_type VARCHAR(20) NOT NULL,
                subject_id UUID NOT NULL,
                subject_email VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                export_data JSON,
                error_message TEXT,
                requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                completed_at TIMESTAMPTZ,
                downloaded_at TIMESTAMPTZ,
                expires_at TIMESTAMPTZ,
                CONSTRAINT chk_data_export_subject_type CHECK (
                    subject_type IN ('donor', 'adopter', 'staff')
                ),
                CONSTRAINT chk_data_export_status CHECK (
                    status IN ('pending', 'processing', 'completed', 'failed', 'expired')
                )
            )
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_data_export_subject
                ON data_export_requests(subject_type, subject_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_data_export_requested_by
                ON data_export_requests(requested_by_user_id)
        """))
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_data_export_table() -> None:
    """Ensure data_export_requests table exists."""
    settings = Settings()
    await _ensure_data_export_table(settings)


# ---------------------------------------------------------------------------
# POST /gdpr/data-export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_export_returns_201(client: AsyncClient) -> None:
    """Creating a data export request returns 201."""
    response = await client.post(
        "/gdpr/data-export",
        json={
            "subject_type": "donor",
            "subject_id": str(uuid4()),
            "subject_email": "test@example.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["subject_type"] == "donor"
    assert body["status"] in ("completed", "failed")
    assert body["subject_email"] == "test@example.com"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_export_invalid_subject_type_returns_422(
    client: AsyncClient,
) -> None:
    """Invalid subject type returns 422."""
    response = await client.post(
        "/gdpr/data-export",
        json={
            "subject_type": "invalid_type",
            "subject_id": str(uuid4()),
            "subject_email": "test@example.com",
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /gdpr/data-export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_exports_returns_200(client: AsyncClient) -> None:
    """Listing export requests returns 200."""
    response = await client.get("/gdpr/data-export")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert "count" in body


# ---------------------------------------------------------------------------
# GET /gdpr/data-export/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_export_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent export returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/gdpr/data-export/{fake_id}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /gdpr/data-export/{id}/download
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_download_nonexistent_export_returns_404(client: AsyncClient) -> None:
    """Downloading a non-existent export returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/gdpr/data-export/{fake_id}/download")

    assert response.status_code == 404
