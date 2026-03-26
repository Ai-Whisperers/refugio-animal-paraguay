"""Integration tests for Sponsorship endpoints.

Tests the Sponsorship API endpoints with mocked Stripe API and live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_sponsorships.py
"""

from unittest.mock import patch
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

_TEST_SPONSOR_DONOR_ID = uuid4()
_TEST_SPONSOR_DONOR_EMAIL = f"sponsor-donor-{uuid4().hex[:8]}@refugio.test"
_TEST_SPONSOR_ANIMAL_ID = uuid4()


async def _ensure_sponsorships_table(settings: Settings) -> None:
    """Create sponsorships table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sponsorships (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
                animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
                tier VARCHAR(20) NOT NULL,
                amount_cents INTEGER NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                interval VARCHAR(20) NOT NULL DEFAULT 'month',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                stripe_customer_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                stripe_price_id VARCHAR(255),
                started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                paused_at TIMESTAMPTZ,
                cancelled_at TIMESTAMPTZ,
                current_period_end TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT chk_sponsorships_tier CHECK (tier IN ('bronze', 'silver', 'gold')),
                CONSTRAINT chk_sponsorships_status CHECK (status IN ('active', 'paused', 'cancelled', 'past_due')),
                CONSTRAINT chk_sponsorships_interval CHECK (interval IN ('month', 'year')),
                CONSTRAINT chk_sponsorships_amount_positive CHECK (amount_cents > 0)
            )
        """))
        await session.commit()


async def _create_test_donor_and_animal(settings: Settings) -> None:
    """Create test donor and animal for sponsorship operations."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Create donor
        await session.execute(
            text("""
                INSERT INTO donors (id, full_name, email, country, currency_preference)
                VALUES (:id, 'Test Sponsor Donor', :email, 'US', 'USD')
                ON CONFLICT (email) DO NOTHING
            """),
            {"id": str(_TEST_SPONSOR_DONOR_ID), "email": _TEST_SPONSOR_DONOR_EMAIL},
        )
        # Create animal
        await session.execute(
            text("""
                INSERT INTO animals (id, name, species, status)
                VALUES (:id, 'Test Sponsored Animal', 'dog', 'available')
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": str(_TEST_SPONSOR_ANIMAL_ID)},
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_sponsorships_tables() -> None:
    """Ensure sponsorships table and test data exist."""
    settings = Settings()
    await _ensure_sponsorships_table(settings)
    await _create_test_donor_and_animal(settings)


# ---------------------------------------------------------------------------
# POST /sponsorships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sponsorship_returns_201(client: AsyncClient) -> None:
    """Creating a sponsorship returns 201 with sponsorship details."""
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}):
        response = await client.post(
            "/sponsorships",
            json={
                "donor_id": str(_TEST_SPONSOR_DONOR_ID),
                "animal_id": str(_TEST_SPONSOR_ANIMAL_ID),
                "tier": "bronze",
                "currency": "USD",
                "interval": "month",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["donor_id"] == str(_TEST_SPONSOR_DONOR_ID)
    assert body["animal_id"] == str(_TEST_SPONSOR_ANIMAL_ID)
    assert body["tier"] == "bronze"
    assert body["amount_cents"] == 1000
    assert body["status"] == "active"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sponsorship_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    """Sponsorship for non-existent donor returns 404."""
    fake_donor_id = uuid4()
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}):
        response = await client.post(
            "/sponsorships",
            json={
                "donor_id": str(fake_donor_id),
                "animal_id": str(_TEST_SPONSOR_ANIMAL_ID),
                "tier": "silver",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sponsorship_nonexistent_animal_returns_404(
    client: AsyncClient,
) -> None:
    """Sponsorship for non-existent animal returns 404."""
    fake_animal_id = uuid4()
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}):
        response = await client.post(
            "/sponsorships",
            json={
                "donor_id": str(_TEST_SPONSOR_DONOR_ID),
                "animal_id": str(fake_animal_id),
                "tier": "gold",
            },
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /donors/{donor_id}/sponsorships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donor_sponsorships(client: AsyncClient) -> None:
    """Listing sponsorships for a donor returns list."""
    response = await client.get(f"/donors/{_TEST_SPONSOR_DONOR_ID}/sponsorships")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert "count" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_sponsorships_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    """Listing sponsorships for non-existent donor returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/donors/{fake_id}/sponsorships")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /animals/{animal_id}/sponsors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animal_sponsors(client: AsyncClient) -> None:
    """Listing sponsors for an animal returns list."""
    response = await client.get(f"/animals/{_TEST_SPONSOR_ANIMAL_ID}/sponsors")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_sponsors_nonexistent_animal_returns_404(
    client: AsyncClient,
) -> None:
    """Listing sponsors for non-existent animal returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/animals/{fake_id}/sponsors")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /sponsorships/{sponsorship_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_nonexistent_sponsorship_returns_404(client: AsyncClient) -> None:
    """Cancelling a non-existent sponsorship returns 404."""
    fake_id = uuid4()
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}):
        response = await client.delete(f"/sponsorships/{fake_id}")
    assert response.status_code == 404
