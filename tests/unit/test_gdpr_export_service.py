"""Unit tests for GDPR data export service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.gdpr_export_service import (
    _export_adopter_data,
    _export_consents,
    _export_donor_data,
    _export_notifications,
    _export_user_profile,
    generate_data_export,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock async database session."""
    return AsyncMock()


class TestExportUserProfile:
    """Tests for _export_user_profile()."""

    @pytest.mark.asyncio
    async def test_export_user_found(self, mock_db: AsyncMock) -> None:
        """Return user profile dict when user exists."""
        user = MagicMock()
        user.id = uuid4()
        user.email = "user@example.com"
        user.role = "staff"
        user.is_active = True
        user.created_at = MagicMock()
        user.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        user.updated_at = MagicMock()
        user.updated_at.isoformat.return_value = "2026-01-02T00:00:00"
        mock_db.get.return_value = user

        result = await _export_user_profile(mock_db, user.id)

        assert result is not None
        assert result["id"] == str(user.id)
        assert result["email"] == "user@example.com"
        assert result["role"] == "staff"
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_export_user_not_found(self, mock_db: AsyncMock) -> None:
        """Return None when user does not exist."""
        mock_db.get.return_value = None

        result = await _export_user_profile(mock_db, uuid4())

        assert result is None


class TestExportDonorData:
    """Tests for _export_donor_data()."""

    @pytest.mark.asyncio
    async def test_export_donor_with_donations(self, mock_db: AsyncMock) -> None:
        """Return donor profile and donations when donor exists."""
        donor = MagicMock()
        donor.id = uuid4()
        donor.full_name = "Test Donor"
        donor.email = "donor@example.com"
        donor.country = "NL"
        donor.currency_preference = "EUR"
        donor.gdpr_consent_at = None
        donor.created_at = MagicMock()
        donor.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        donor.updated_at = MagicMock()
        donor.updated_at.isoformat.return_value = "2026-01-02T00:00:00"
        mock_db.get.return_value = donor

        donation = MagicMock()
        donation.id = uuid4()
        donation.amount_cents = 5000
        donation.currency = "EUR"
        donation.payment_method = "card"
        donation.status = "completed"
        donation.receipt_number = "REC-001"
        donation.fund_category = "medical"
        donation.notes = None
        donation.created_at = MagicMock()
        donation.created_at.isoformat.return_value = "2026-03-01T00:00:00"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [donation]
        mock_db.execute.return_value = mock_result

        result = await _export_donor_data(mock_db, donor.id)

        assert result is not None
        assert result["profile"]["full_name"] == "Test Donor"
        assert result["profile"]["country"] == "NL"
        assert len(result["donations"]) == 1
        assert result["donations"][0]["amount_cents"] == 5000
        assert result["donations"][0]["currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_export_donor_not_found(self, mock_db: AsyncMock) -> None:
        """Return None when donor does not exist."""
        mock_db.get.return_value = None

        result = await _export_donor_data(mock_db, uuid4())

        assert result is None


class TestExportAdopterData:
    """Tests for _export_adopter_data()."""

    @pytest.mark.asyncio
    async def test_export_adopter_with_requests(self, mock_db: AsyncMock) -> None:
        """Return adopter profile and adoption requests when adopter exists."""
        adopter = MagicMock()
        adopter.id = uuid4()
        adopter.full_name = "Test Adopter"
        adopter.email = "adopter@example.com"
        adopter.phone = "+595981234567"
        adopter.address = "Asuncion, PY"
        adopter.gdpr_consent_at = None
        adopter.created_at = MagicMock()
        adopter.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        adopter.updated_at = MagicMock()
        adopter.updated_at.isoformat.return_value = "2026-01-02T00:00:00"
        mock_db.get.return_value = adopter

        request = MagicMock()
        request.id = uuid4()
        request.animal_id = uuid4()
        request.status = "approved"
        request.notes = "Good home"
        request.created_at = MagicMock()
        request.created_at.isoformat.return_value = "2026-02-01T00:00:00"
        request.updated_at = MagicMock()
        request.updated_at.isoformat.return_value = "2026-02-15T00:00:00"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [request]
        mock_db.execute.return_value = mock_result

        result = await _export_adopter_data(mock_db, adopter.id)

        assert result is not None
        assert result["profile"]["full_name"] == "Test Adopter"
        assert result["profile"]["phone"] == "+595981234567"
        assert len(result["adoption_requests"]) == 1
        assert result["adoption_requests"][0]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_export_adopter_not_found(self, mock_db: AsyncMock) -> None:
        """Return None when adopter does not exist."""
        mock_db.get.return_value = None

        result = await _export_adopter_data(mock_db, uuid4())

        assert result is None


class TestExportConsents:
    """Tests for _export_consents()."""

    @pytest.mark.asyncio
    async def test_export_consents_found(self, mock_db: AsyncMock) -> None:
        """Return list of consent records."""
        consent = MagicMock()
        consent.id = uuid4()
        consent.consent_type = "newsletter"
        consent.status = "active"
        consent.opt_in_date = MagicMock()
        consent.opt_in_date.isoformat.return_value = "2026-01-01T00:00:00"
        consent.opt_out_date = None
        consent.method = "user_self_service"
        consent.created_at = MagicMock()
        consent.created_at.isoformat.return_value = "2026-01-01T00:00:00"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [consent]
        mock_db.execute.return_value = mock_result

        result = await _export_consents(mock_db, uuid4())

        assert len(result) == 1
        assert result[0]["consent_type"] == "newsletter"
        assert result[0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_export_consents_empty(self, mock_db: AsyncMock) -> None:
        """Return empty list when no consents exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await _export_consents(mock_db, uuid4())

        assert result == []


class TestExportNotifications:
    """Tests for _export_notifications()."""

    @pytest.mark.asyncio
    async def test_export_notifications_found(self, mock_db: AsyncMock) -> None:
        """Return list of notification records."""
        notif = MagicMock()
        notif.id = uuid4()
        notif.notification_type = "adoption_status"
        notif.title = "Status Update"
        notif.message = "Your request was approved"
        notif.is_read = False
        notif.created_at = MagicMock()
        notif.created_at.isoformat.return_value = "2026-03-01T00:00:00"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [notif]
        mock_db.execute.return_value = mock_result

        result = await _export_notifications(mock_db, uuid4())

        assert len(result) == 1
        assert result[0]["notification_type"] == "adoption_status"
        assert result[0]["is_read"] is False

    @pytest.mark.asyncio
    async def test_export_notifications_empty(self, mock_db: AsyncMock) -> None:
        """Return empty list when no notifications exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await _export_notifications(mock_db, uuid4())

        assert result == []


class TestGenerateDataExport:
    """Tests for generate_data_export()."""

    @pytest.mark.asyncio
    @patch("src.services.gdpr_export_service._export_adopter_data")
    @patch("src.services.gdpr_export_service._export_donor_data")
    @patch("src.services.gdpr_export_service._export_notifications")
    @patch("src.services.gdpr_export_service._export_consents")
    @patch("src.services.gdpr_export_service._export_user_profile")
    async def test_full_export(
        self,
        mock_profile: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_donor: AsyncMock,
        mock_adopter: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Generate full export with all data types."""
        user_id = uuid4()
        donor_id = uuid4()
        adopter_id = uuid4()

        mock_profile.return_value = {"id": str(user_id), "email": "test@test.com"}
        mock_consents.return_value = [{"consent_type": "newsletter"}]
        mock_notifications.return_value = [{"title": "Test"}]
        mock_donor.return_value = {"profile": {}, "donations": []}
        mock_adopter.return_value = {"profile": {}, "adoption_requests": []}

        result = await generate_data_export(
            mock_db, user_id, donor_id=donor_id, adopter_id=adopter_id
        )

        assert result["export_metadata"]["user_id"] == str(user_id)
        assert result["export_metadata"]["format_version"] == "1.0"
        assert "Article 15" in result["export_metadata"]["gdpr_articles"][0]
        assert result["user_profile"] is not None
        assert len(result["consents"]) == 1
        assert len(result["notifications"]) == 1
        assert result["donor_data"] is not None
        assert result["adopter_data"] is not None

    @pytest.mark.asyncio
    @patch("src.services.gdpr_export_service._export_notifications")
    @patch("src.services.gdpr_export_service._export_consents")
    @patch("src.services.gdpr_export_service._export_user_profile")
    async def test_export_user_only(
        self,
        mock_profile: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Export with only user data (no donor/adopter)."""
        user_id = uuid4()
        mock_profile.return_value = {"id": str(user_id)}
        mock_consents.return_value = []
        mock_notifications.return_value = []

        result = await generate_data_export(mock_db, user_id)

        assert result["donor_data"] is None
        assert result["adopter_data"] is None
        assert result["user_profile"] is not None
