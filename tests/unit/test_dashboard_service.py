"""Unit tests for portal dashboard service."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.user import User
from src.services.dashboard_service import (
    ApplicationSummary,
    DashboardData,
    DonationSummary,
    SponsoredAnimalSummary,
    get_dashboard_data,
)


@pytest.fixture()
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture()
def adopter_user():
    """Create a mock adopter user with full_name."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "adopter@refugio-shelter.org"
    user.full_name = "Maria Garcia"
    user.role = "adopter"
    user.is_active = True
    user.email_verified = True
    return user


@pytest.fixture()
def donor_user():
    """Create a mock donor user without full_name."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "donor@refugio-shelter.org"
    user.full_name = None
    user.role = "donor"
    user.is_active = True
    user.email_verified = True
    return user


def _mock_execute_results(mock_db, results_sequence):
    """Configure mock_db.execute to return different results per call."""
    side_effects = []
    for result_rows in results_sequence:
        mock_result = MagicMock()
        mock_result.all.return_value = result_rows
        mock_result.first.return_value = result_rows[0] if result_rows else None
        side_effects.append(mock_result)
    mock_db.execute.side_effect = side_effects


class TestGetDashboardData:
    """Tests for the get_dashboard_data orchestrator."""

    @pytest.mark.asyncio()
    async def test_returns_dashboard_data_with_display_name(self, mock_db, adopter_user):
        """Should use full_name as display_name when available."""
        _mock_execute_results(mock_db, [[], [], []])

        data = await get_dashboard_data(mock_db, adopter_user)

        assert isinstance(data, DashboardData)
        assert data.display_name == "Maria Garcia"
        assert data.email == "adopter@refugio-shelter.org"
        assert data.role == "adopter"
        assert data.user_id == adopter_user.id

    @pytest.mark.asyncio()
    async def test_falls_back_to_email_prefix_when_no_name(self, mock_db, donor_user):
        """Should use email prefix as display_name when full_name is None."""
        _mock_execute_results(mock_db, [[], [], []])

        data = await get_dashboard_data(mock_db, donor_user)

        assert data.display_name == "donor"

    @pytest.mark.asyncio()
    async def test_returns_empty_applications_when_none(self, mock_db, adopter_user):
        """Should return empty applications list when user has no adoption requests."""
        _mock_execute_results(mock_db, [[], [], []])

        data = await get_dashboard_data(mock_db, adopter_user)

        assert data.applications == []

    @pytest.mark.asyncio()
    async def test_returns_empty_donation_summary_when_no_donor(self, mock_db, adopter_user):
        """Should return zero-valued donation summary when user has no donations."""
        _mock_execute_results(mock_db, [[], [], []])

        data = await get_dashboard_data(mock_db, adopter_user)

        assert data.donation_summary.total_count == 0
        assert data.donation_summary.total_amount_cents == 0
        assert data.donation_summary.currency == "EUR"
        assert data.donation_summary.last_donation_at is None

    @pytest.mark.asyncio()
    async def test_returns_empty_sponsored_animals_when_none(self, mock_db, adopter_user):
        """Should return empty sponsored animals list."""
        _mock_execute_results(mock_db, [[], [], []])

        data = await get_dashboard_data(mock_db, adopter_user)

        assert data.sponsored_animals == []

    @pytest.mark.asyncio()
    async def test_returns_applications_from_query(self, mock_db, adopter_user):
        """Should map query rows to ApplicationSummary objects."""
        app_row = MagicMock()
        app_row.id = uuid.uuid4()
        app_row.name = "Luna"
        app_row.species = "dog"
        app_row.submitted_at = datetime.now(UTC)
        app_row.status = "pending"

        _mock_execute_results(mock_db, [[app_row], [], []])

        data = await get_dashboard_data(mock_db, adopter_user)

        assert len(data.applications) == 1
        assert data.applications[0].animal_name == "Luna"
        assert data.applications[0].status == "pending"

    @pytest.mark.asyncio()
    async def test_returns_donation_summary_from_query(self, mock_db, donor_user):
        """Should map donation aggregate row to DonationSummary."""
        donation_row = MagicMock()
        donation_row.total_count = 5
        donation_row.total_amount_cents = 50000
        donation_row.last_donation_at = datetime.now(UTC) - timedelta(days=3)
        donation_row.currency_preference = "EUR"

        _mock_execute_results(mock_db, [[], [donation_row], []])

        data = await get_dashboard_data(mock_db, donor_user)

        assert data.donation_summary.total_count == 5
        assert data.donation_summary.total_amount_cents == 50000
        assert data.donation_summary.currency == "EUR"

    @pytest.mark.asyncio()
    async def test_returns_sponsored_animals_from_query(self, mock_db, donor_user):
        """Should map sponsorship rows to SponsoredAnimalSummary objects."""
        sponsor_row = MagicMock()
        sponsor_row.animal_id = uuid.uuid4()
        sponsor_row.animal_name = "Max"
        sponsor_row.animal_species = "dog"
        sponsor_row.tier_name = "Gold"
        sponsor_row.frequency = "monthly"
        sponsor_row.status = "active"

        _mock_execute_results(mock_db, [[], [], [sponsor_row]])

        data = await get_dashboard_data(mock_db, donor_user)

        assert len(data.sponsored_animals) == 1
        assert data.sponsored_animals[0].animal_name == "Max"
        assert data.sponsored_animals[0].tier_name == "Gold"


class TestApplicationSummary:
    """Tests for ApplicationSummary data structure."""

    def test_stores_all_fields(self) -> None:
        app_id = uuid.uuid4()
        now = datetime.now(UTC)
        summary = ApplicationSummary(
            id=app_id,
            animal_name="Luna",
            animal_species="cat",
            submitted_at=now,
            status="approved",
        )
        assert summary.id == app_id
        assert summary.animal_name == "Luna"
        assert summary.animal_species == "cat"
        assert summary.submitted_at == now
        assert summary.status == "approved"


class TestDonationSummary:
    """Tests for DonationSummary data structure."""

    def test_stores_zero_values(self) -> None:
        summary = DonationSummary(
            total_count=0,
            total_amount_cents=0,
            currency="PYG",
            last_donation_at=None,
        )
        assert summary.total_count == 0
        assert summary.total_amount_cents == 0
        assert summary.currency == "PYG"
        assert summary.last_donation_at is None


class TestSponsoredAnimalSummary:
    """Tests for SponsoredAnimalSummary data structure."""

    def test_stores_all_fields(self) -> None:
        animal_id = uuid.uuid4()
        summary = SponsoredAnimalSummary(
            animal_id=animal_id,
            animal_name="Rex",
            animal_species="dog",
            tier_name="Silver",
            frequency="annual",
            status="paused",
        )
        assert summary.animal_id == animal_id
        assert summary.animal_name == "Rex"
        assert summary.frequency == "annual"
        assert summary.status == "paused"
