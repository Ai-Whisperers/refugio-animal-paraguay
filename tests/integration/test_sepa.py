"""Integration tests for SEPA Direct Debit endpoints.

Tests the SEPA API endpoints with mocked Stripe API and live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_sepa.py
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.auth.utils import hash_password
from src.config import Settings
from src.db.session import init_engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_SEPA_USER_ID = uuid4()
_TEST_SEPA_USER_EMAIL = f"sepa-user-{uuid4().hex[:8]}@refugio.test"
_TEST_SEPA_DONOR_ID = uuid4()
_TEST_SEPA_DONOR_EMAIL = f"sepa-donor-{uuid4().hex[:8]}@refugio.test"

# Valid Dutch IBAN for testing
_TEST_IBAN = "NL91ABNA0417164300"


async def _ensure_sepa_table(settings: Settings) -> None:
    """Create sepa_mandates table if it doesn't exist (for test environments)."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sepa_mandates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
                stripe_customer_id VARCHAR(255) NOT NULL,
                stripe_setup_intent_id VARCHAR(255),
                stripe_payment_method_id VARCHAR(255),
                stripe_mandate_id VARCHAR(255),
                iban_last4 VARCHAR(4),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                amount_cents INTEGER NOT NULL,
                interval VARCHAR(20) NOT NULL DEFAULT 'month',
                stripe_subscription_id VARCHAR(255),
                activated_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ,
                failure_reason VARCHAR(500),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT chk_sepa_mandates_status CHECK (status IN ('pending', 'active', 'revoked', 'failed')),
                CONSTRAINT chk_sepa_mandates_interval CHECK (interval IN ('month', 'year')),
                CONSTRAINT chk_sepa_mandates_amount_positive CHECK (amount_cents > 0)
            )
        """))
        await session.commit()


async def _ensure_payment_method_check(settings: Settings) -> None:
    """Ensure donations payment_method CHECK includes sepa_debit."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Drop and recreate the constraint to include sepa_debit
        await session.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.check_constraints
                    WHERE constraint_name = 'chk_donations_payment_method'
                ) THEN
                    ALTER TABLE donations DROP CONSTRAINT chk_donations_payment_method;
                END IF;
                ALTER TABLE donations ADD CONSTRAINT chk_donations_payment_method
                    CHECK (payment_method IN ('stripe', 'cash', 'transfer', 'sepa_debit'));
            END $$;
        """))
        await session.commit()


async def _create_test_user_and_donor(settings: Settings) -> None:
    """Create test user and donor for SEPA operations."""
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Create staff user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (email) DO NOTHING
            """),
            {
                "id": str(_TEST_SEPA_USER_ID),
                "email": _TEST_SEPA_USER_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        # Create donor
        await session.execute(
            text("""
                INSERT INTO donors (id, full_name, email, country, currency_preference)
                VALUES (:id, 'Test SEPA Donor', :email, 'NL', 'EUR')
                ON CONFLICT (email) DO NOTHING
            """),
            {"id": str(_TEST_SEPA_DONOR_ID), "email": _TEST_SEPA_DONOR_EMAIL},
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _setup_sepa_tables() -> None:
    """Ensure sepa_mandates table, payment_method check, and test data exist."""
    settings = Settings()
    await _ensure_sepa_table(settings)
    await _ensure_payment_method_check(settings)
    await _create_test_user_and_donor(settings)


def _mock_stripe_customer() -> MagicMock:
    customer = MagicMock()
    customer.id = "cus_test123"
    return customer


def _mock_stripe_payment_method() -> MagicMock:
    pm = MagicMock()
    pm.id = "pm_test456"
    return pm


def _mock_stripe_setup_intent() -> MagicMock:
    si = MagicMock()
    si.id = "seti_test789"
    si.client_secret = "seti_test789_secret_abc"
    return si


# ---------------------------------------------------------------------------
# POST /donations/sepa-setup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_setup_returns_201(client: AsyncClient) -> None:
    """Creating a SEPA mandate returns 201 with setup intent details."""
    with (
        patch("src.services.sepa_service.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123"}),
    ):
        mock_stripe.Customer.create.return_value = _mock_stripe_customer()
        mock_stripe.PaymentMethod.create.return_value = _mock_stripe_payment_method()
        mock_stripe.PaymentMethod.attach.return_value = None
        mock_stripe.SetupIntent.create.return_value = _mock_stripe_setup_intent()

        response = await client.post(
            "/donations/sepa-setup",
            json={
                "donor_id": str(_TEST_SEPA_DONOR_ID),
                "iban": _TEST_IBAN,
                "amount_cents": 2500,
                "interval": "month",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["donor_id"] == str(_TEST_SEPA_DONOR_ID)
    assert body["amount_cents"] == 2500
    assert body["interval"] == "month"
    assert "client_secret" in body
    assert body["stripe_setup_intent_id"] == "seti_test789"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_setup_invalid_iban_returns_422(client: AsyncClient) -> None:
    """Invalid IBAN returns 422 validation error."""
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123"}):
        response = await client.post(
            "/donations/sepa-setup",
            json={
                "donor_id": str(_TEST_SEPA_DONOR_ID),
                "iban": "INVALID_IBAN",
                "amount_cents": 2500,
                "interval": "month",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_sepa_setup_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    """SEPA setup for non-existent donor returns 404."""
    fake_donor_id = uuid4()
    with (
        patch("src.services.sepa_service.stripe") as mock_stripe,
        patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123"}),
    ):
        mock_stripe.Customer.create.return_value = _mock_stripe_customer()

        response = await client.post(
            "/donations/sepa-setup",
            json={
                "donor_id": str(fake_donor_id),
                "iban": _TEST_IBAN,
                "amount_cents": 1000,
                "interval": "month",
            },
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /donors/{donor_id}/mandates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_donor_mandates_empty(client: AsyncClient) -> None:
    """Listing mandates for a donor with no mandates returns empty list."""
    response = await client.get(f"/donors/{_TEST_SEPA_DONOR_ID}/mandates")
    assert response.status_code == 200
    body = response.json()
    assert body["donor_id"] == str(_TEST_SEPA_DONOR_ID)
    assert isinstance(body["mandates"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_mandates_nonexistent_donor_returns_404(
    client: AsyncClient,
) -> None:
    """Listing mandates for non-existent donor returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/donors/{fake_id}/mandates")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /donors/{donor_id}/mandates/{mandate_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_revoke_nonexistent_mandate_returns_404(client: AsyncClient) -> None:
    """Revoking a non-existent mandate returns 404."""
    fake_mandate_id = uuid4()
    response = await client.delete(f"/donors/{_TEST_SEPA_DONOR_ID}/mandates/{fake_mandate_id}")
    assert response.status_code == 404
