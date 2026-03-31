"""Unit tests for GDPR data deletion service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.gdpr_deletion_service import (
    ANONYMIZED_ADDRESS,
    ANONYMIZED_NAME,
    ANONYMIZED_PHONE,
    ANONYMIZED_TEXT,
    anonymize_adopter,
    anonymize_donor,
    anonymize_foster,
    anonymize_rescuer,
    anonymize_volunteer,
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
    async def test_anonymize_donor_generates_unique_emails(self, mock_db: AsyncMock) -> None:
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
    async def test_delete_notifications_returns_count(self, mock_db: AsyncMock) -> None:
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
    @patch("src.services.gdpr_third_party_deletion_service.process_third_party_deletion")
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
        mock_third_party: AsyncMock,
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
        mock_third_party.return_value = {
            "stripe_subscriptions_cancelled": 1,
            "stripe_subscriptions_failed": 0,
            "stripe_customer_deleted": True,
            "email_lists_removed": 3,
        }
        # Make db.get return a mock donor so third-party cascade can read email/stripe_customer_id
        mock_donor_obj = MagicMock()
        mock_donor_obj.email = "donor@example.com"
        mock_donor_obj.stripe_customer_id = "cus_test"
        mock_db.get.return_value = mock_donor_obj

        result = await process_deletion_request(
            mock_db, user_id, donor_id=donor_id, adopter_id=adopter_id
        )

        assert result["user_id"] == str(user_id)
        assert result["user_deactivated"] is True
        assert result["consents_deleted"] == 2
        assert result["notifications_deleted"] == 5
        assert result["donor_anonymized"] is True
        assert result["adopter_anonymized"] is True
        assert result["stripe_subscriptions_cancelled"] == 1
        assert result["stripe_customer_deleted"] is True
        assert result["email_lists_removed"] == 3

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


class TestAnonymizeVolunteer:
    """Tests for anonymize_volunteer()."""

    @pytest.mark.asyncio
    async def test_anonymize_volunteer_found(self, mock_db: AsyncMock) -> None:
        """Anonymize a volunteer profile's personal data when found."""
        volunteer_id = uuid4()
        volunteer = MagicMock()
        mock_db.get.return_value = volunteer

        result = await anonymize_volunteer(mock_db, volunteer_id)

        assert result is True
        assert volunteer.emergency_contact_name is None
        assert volunteer.emergency_contact_phone is None
        assert volunteer.bio is None
        assert volunteer.motivation == ANONYMIZED_TEXT
        assert volunteer.status == "inactive"
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anonymize_volunteer_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when volunteer profile does not exist."""
        mock_db.get.return_value = None

        result = await anonymize_volunteer(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()


class TestAnonymizeRescuer:
    """Tests for anonymize_rescuer()."""

    @pytest.mark.asyncio
    async def test_anonymize_rescuer_found(self, mock_db: AsyncMock) -> None:
        """Anonymize a rescuer profile's personal data when found."""
        rescuer_id = uuid4()
        rescuer = MagicMock()
        mock_db.get.return_value = rescuer

        result = await anonymize_rescuer(mock_db, rescuer_id)

        assert result is True
        assert rescuer.display_name == ANONYMIZED_NAME
        assert rescuer.slug.startswith("deleted-")
        assert rescuer.bio is None
        assert rescuer.location_city is None
        assert rescuer.location_coords is None
        assert rescuer.social_links is None
        assert rescuer.phone_whatsapp is None
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anonymize_rescuer_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when rescuer profile does not exist."""
        mock_db.get.return_value = None

        result = await anonymize_rescuer(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_anonymize_rescuer_generates_unique_slugs(self, mock_db: AsyncMock) -> None:
        """Each anonymization produces a unique slug to avoid UNIQUE constraint violations."""
        rescuer1 = MagicMock()
        rescuer2 = MagicMock()
        mock_db.get.side_effect = [rescuer1, rescuer2]

        await anonymize_rescuer(mock_db, uuid4())
        await anonymize_rescuer(mock_db, uuid4())

        assert rescuer1.slug != rescuer2.slug


class TestAnonymizeFoster:
    """Tests for anonymize_foster()."""

    @pytest.mark.asyncio
    async def test_anonymize_foster_found(self, mock_db: AsyncMock) -> None:
        """Anonymize a foster profile's personal data when found."""
        foster_id = uuid4()
        foster = MagicMock()
        mock_db.get.return_value = foster

        result = await anonymize_foster(mock_db, foster_id)

        assert result is True
        assert foster.motivation == ANONYMIZED_TEXT
        assert foster.experience_description is None
        assert foster.other_pets_description is None
        assert foster.status == "inactive"
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anonymize_foster_not_found(self, mock_db: AsyncMock) -> None:
        """Return False when foster profile does not exist."""
        mock_db.get.return_value = None

        result = await anonymize_foster(mock_db, uuid4())

        assert result is False
        mock_db.flush.assert_not_awaited()


class TestDeactivateUserAccountExtended:
    """Extended tests for deactivate_user_account() — new full_name/phone clearing."""

    @pytest.mark.asyncio
    async def test_deactivate_clears_full_name_and_phone(self, mock_db: AsyncMock) -> None:
        """User account deactivation also clears full_name and phone (new PII fields)."""
        user = MagicMock()
        mock_db.get.return_value = user

        await deactivate_user_account(mock_db, uuid4())

        assert user.full_name is None
        assert user.phone is None


class TestProcessDeletionRequestExtended:
    """Extended tests for process_deletion_request() — new entity types."""

    @pytest.mark.asyncio
    @patch("src.services.gdpr_deletion_service.anonymize_foster")
    @patch("src.services.gdpr_deletion_service.anonymize_rescuer")
    @patch("src.services.gdpr_deletion_service.anonymize_volunteer")
    @patch("src.services.gdpr_deletion_service.delete_user_notifications")
    @patch("src.services.gdpr_deletion_service.delete_user_consents")
    @patch("src.services.gdpr_deletion_service.deactivate_user_account")
    async def test_full_deletion_all_entity_types(
        self,
        mock_deactivate: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_volunteer: AsyncMock,
        mock_rescuer: AsyncMock,
        mock_foster: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Full deletion request covers volunteer, rescuer, and foster profiles."""
        user_id = uuid4()
        volunteer_id = uuid4()
        rescuer_id = uuid4()
        foster_id = uuid4()

        mock_deactivate.return_value = True
        mock_consents.return_value = 0
        mock_notifications.return_value = 0
        mock_volunteer.return_value = True
        mock_rescuer.return_value = True
        mock_foster.return_value = True

        result = await process_deletion_request(
            mock_db,
            user_id,
            volunteer_id=volunteer_id,
            rescuer_id=rescuer_id,
            foster_id=foster_id,
        )

        assert result["volunteer_anonymized"] is True
        assert result["rescuer_anonymized"] is True
        assert result["foster_anonymized"] is True
        mock_volunteer.assert_awaited_once_with(mock_db, volunteer_id)
        mock_rescuer.assert_awaited_once_with(mock_db, rescuer_id)
        mock_foster.assert_awaited_once_with(mock_db, foster_id)

    @pytest.mark.asyncio
    @patch("src.services.gdpr_deletion_service.delete_user_notifications")
    @patch("src.services.gdpr_deletion_service.delete_user_consents")
    @patch("src.services.gdpr_deletion_service.deactivate_user_account")
    async def test_deletion_skips_profiles_when_ids_not_provided(
        self,
        mock_deactivate: AsyncMock,
        mock_consents: AsyncMock,
        mock_notifications: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Profile anonymization is skipped when IDs are not provided."""
        mock_deactivate.return_value = True
        mock_consents.return_value = 0
        mock_notifications.return_value = 0

        result = await process_deletion_request(mock_db, uuid4())

        assert result["volunteer_anonymized"] is False
        assert result["rescuer_anonymized"] is False
        assert result["foster_anonymized"] is False
