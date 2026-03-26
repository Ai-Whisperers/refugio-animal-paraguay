"""Unit tests for GDPR data deletion service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.gdpr_deletion_service import (
    ANONYMIZED_ADDRESS,
    ANONYMIZED_NAME,
    ANONYMIZED_PHONE,
    anonymize_adopter,
    anonymize_donor,
    deactivate_user_account,
    delete_user_consents,
    delete_user_notifications,
    process_deletion_request,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.flush = AsyncMock()
    return db


class TestAnonymizeDonor:
    """Tests for anonymize_donor()."""

    @pytest.mark.asyncio
    async def test_anonymize_donor_found(self, mock_db: AsyncMock) -> None:
        """Anonymize a donor's personal data when found."""
        donor_id = uuid4()
        donor = MagicMock()
        mock_db.get.return_value = donor

        result = await anonymize_donor(mock_db, donor_id)

        assert result is True
        assert donor.full_name == ANONYMIZED_NAME
        assert donor.email.startswith("deleted-")
        assert donor.email.endswith("@anonymized.invalid")
        assert donor.country is None
        assert donor.gdpr_consent_at is None
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anonymize_donor_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when donor does not exist."""
        mock_db.get.return_value = None

        result = await anonymize_donor(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_anonymize_donor_generates_unique_emails(
        self, mock_db: AsyncMock
    ) -> None:
        """Each anonymization produces a unique email to avoid constraint violations."""
        donor1 = MagicMock()
        donor2 = MagicMock()
        mock_db.get.side_effect = [donor1, donor2]

        await anonymize_donor(mock_db, uuid4())
        await anonymize_donor(mock_db, uuid4())

        assert donor1.email != donor2.email


class TestAnonymizeAdopter:
    """Tests for anonymize_adopter()."""

    @pytest.mark.asyncio
    async def test_anonymize_adopter_found(self, mock_db: AsyncMock) -> None:
        """Anonymize an adopter's personal data when found."""
        adopter_id = uuid4()
        adopter = MagicMock()
        mock_db.get.return_value = adopter

        result = await anonymize_adopter(mock_db, adopter_id)

        assert result is True
        assert adopter.full_name == ANONYMIZED_NAME
        assert adopter.email.startswith("deleted-")
        assert adopter.email.endswith("@anonymized.invalid")
        assert adopter.phone == ANONYMIZED_PHONE
        assert adopter.address == ANONYMIZED_ADDRESS
        assert adopter.gdpr_consent_at is None
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anonymize_adopter_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when adopter does not exist."""
        mock_db.get.return_value = None

        result = await anonymize_adopter(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()


class TestDeleteUserConsents:
    """Tests for delete_user_consents()."""

    @pytest.mark.asyncio
    async def test_delete_consents_returns_count(self, mock_db: AsyncMock) -> None:
        """Return count of deleted consent records."""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute.return_value = mock_result

        count = await delete_user_consents(mock_db, uuid4())

        assert count == 3

    @pytest.mark.asyncio
    async def test_delete_consents_none_found(self, mock_db: AsyncMock) -> None:
        """Return 0 when no consent records exist."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        count = await delete_user_consents(mock_db, uuid4())

        assert count == 0


class TestDeleteUserNotifications:
    """Tests for delete_user_notifications()."""

    @pytest.mark.asyncio
    async def test_delete_notifications_returns_count(
        self, mock_db: AsyncMock
    ) -> None:
        """Return count of deleted notification records."""
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result

        count = await delete_user_notifications(mock_db, uuid4())

        assert count == 5

    @pytest.mark.asyncio
    async def test_delete_notifications_none_found(self, mock_db: AsyncMock) -> None:
        """Return 0 when no notifications exist."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        count = await delete_user_notifications(mock_db, uuid4())

        assert count == 0


class TestDeactivateUserAccount:
    """Tests for deactivate_user_account()."""

    @pytest.mark.asyncio
    async def test_deactivate_user_found(self, mock_db: AsyncMock) -> None:
        """Deactivate and anonymize user account when found."""
        user_id = uuid4()
        user = MagicMock()
        mock_db.get.return_value = user

        result = await deactivate_user_account(mock_db, user_id)

        assert result is True
        assert user.email.startswith("deleted-")
        assert user.email.endswith("@anonymized.invalid")
        assert user.is_active is False
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when user does not exist."""
        mock_db.get.return_value = None

        result = await deactivate_user_account(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()


class TestProcessDeletionRequest:
    """Tests for process_deletion_request()."""

    @pytest.mark.asyncio
    @patch("src.services.gdpr_deletion_service.anonymize_adopter")
    @patch("src.services.gdpr_deletion_service.anonymize_donor")
    @patch("src.services.gdpr_deletion_service.delete_user_notifications")
    @patch("src.services.gdpr_deletion_service.delete_user_consents")
    @patch("src.services.gdpr_deletion_service.deactivate_user_account")
    async def test_full_deletion_request(
        self,
        mock_deactivate: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_donor: AsyncMock,
        mock_adopter: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Process full deletion with user, donor, and adopter."""
        user_id = uuid4()
        donor_id = uuid4()
        adopter_id = uuid4()

        mock_deactivate.return_value = True
        mock_consents.return_value = 2
        mock_notifications.return_value = 5
        mock_donor.return_value = True
        mock_adopter.return_value = True

        result = await process_deletion_request(
            mock_db, user_id, donor_id=donor_id, adopter_id=adopter_id
        )

        assert result["user_id"] == str(user_id)
        assert result["user_deactivated"] is True
        assert result["consents_deleted"] == 2
        assert result["notifications_deleted"] == 5
        assert result["donor_anonymized"] is True
        assert result["adopter_anonymized"] is True

    @pytest.mark.asyncio
    @patch("src.services.gdpr_deletion_service.delete_user_notifications")
    @patch("src.services.gdpr_deletion_service.delete_user_consents")
    @patch("src.services.gdpr_deletion_service.deactivate_user_account")
    async def test_deletion_request_user_only(
        self,
        mock_deactivate: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Process deletion with only user_id (no donor/adopter)."""
        user_id = uuid4()
        mock_deactivate.return_value = True
        mock_consents.return_value = 0
        mock_notifications.return_value = 0

        result = await process_deletion_request(mock_db, user_id)

        assert result["user_id"] == str(user_id)
        assert result["user_deactivated"] is True
        assert result["donor_anonymized"] is False
        assert result["adopter_anonymized"] is False

    @pytest.mark.asyncio
    @patch("src.services.gdpr_deletion_service.delete_user_notifications")
    @patch("src.services.gdpr_deletion_service.delete_user_consents")
    @patch("src.services.gdpr_deletion_service.deactivate_user_account")
    async def test_deletion_request_user_not_found(
        self,
        mock_deactivate: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Still processes consents/notifications even if user not found."""
        user_id = uuid4()
        mock_deactivate.return_value = False
        mock_consents.return_value = 0
        mock_notifications.return_value = 0

        result = await process_deletion_request(mock_db, user_id)

        assert result["user_deactivated"] is False
        mock_consents.assert_awaited_once()
        mock_notifications.assert_awaited_once()
