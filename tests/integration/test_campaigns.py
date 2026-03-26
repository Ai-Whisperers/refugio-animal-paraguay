"""Integration tests for Campaign endpoints.

Tests the Campaign API endpoints with live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_campaigns.py
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


async def _ensure_campaigns_table(settings: Settings) -> None:
    """Create campaigns table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                goal_amount_cents INTEGER NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                category VARCHAR(20) NOT NULL DEFAULT 'other',
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                featured BOOLEAN NOT NULL DEFAULT false,
                deadline DATE,
                created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT chk_campaigns_category CHECK (
                    category IN ('medical', 'food', 'operations', 'rescue', 'facility', 'other')
                ),
                CONSTRAINT chk_campaigns_status CHECK (
                    status IN ('draft', 'active', 'paused', 'completed', 'archived')
                ),
                CONSTRAINT chk_campaigns_goal_positive CHECK (goal_amount_cents > 0)
            )
        """))
        # Add campaign_id to donations if not exists
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'donations' AND column_name = 'campaign_id'
                ) THEN
                    ALTER TABLE donations ADD COLUMN campaign_id UUID
                        REFERENCES campaigns(id) ON DELETE SET NULL;
                    CREATE INDEX IF NOT EXISTS ix_donations_campaign_id
                        ON donations(campaign_id);
                END IF;
            END $$;
        """))
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_campaigns_table() -> None:
    """Ensure campaigns table exists."""
    settings = Settings()
    await _ensure_campaigns_table(settings)


# ---------------------------------------------------------------------------
# POST /campaigns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_returns_201(client: AsyncClient) -> None:
    """Creating a campaign returns 201 with campaign details."""
    response = await client.post(
        "/campaigns",
        json={
            "title": "Emergency Medical Fund",
            "goal_amount_cents": 100000,
            "currency": "USD",
            "category": "medical",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Emergency Medical Fund"
    assert body["goal_amount_cents"] == 100000
    assert body["status"] == "draft"
    assert body["raised_amount_cents"] == 0
    assert body["progress_pct"] == 0.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_invalid_category_returns_422(
    client: AsyncClient,
) -> None:
    """Invalid category returns 422."""
    response = await client.post(
        "/campaigns",
        json={
            "title": "Bad Campaign",
            "goal_amount_cents": 50000,
            "category": "invalid_category",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_campaign_zero_goal_returns_422(client: AsyncClient) -> None:
    """Zero goal amount returns 422."""
    response = await client.post(
        "/campaigns",
        json={
            "title": "Zero Goal",
            "goal_amount_cents": 0,
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /campaigns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_campaigns_returns_200(client: AsyncClient) -> None:
    """Listing campaigns returns 200 with list."""
    response = await client.get("/campaigns")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert "count" in body


# ---------------------------------------------------------------------------
# GET /campaigns/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent campaign returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/campaigns/{fake_id}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /campaigns/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    """Updating a non-existent campaign returns 404."""
    fake_id = uuid4()
    response = await client.patch(
        f"/campaigns/{fake_id}",
        json={"title": "Updated"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /campaigns/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_nonexistent_campaign_returns_404(client: AsyncClient) -> None:
    """Deleting a non-existent campaign returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/campaigns/{fake_id}")

    assert response.status_code == 404
