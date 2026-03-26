"""Unit tests for GDPR consent service logic.

Tests consent grant/revoke/check operations with mocked database session.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.user_consent import ConsentMethod, ConsentStatus, ConsentType
from src.services.consent_service import (
    check_consent,
    get_consent_summary,
    grant_consent,
    revoke_consent,
)


class TestCheckConsent:
    """Tests for check_consent validation function."""

    @pytest.mark.asyncio
    async def test_returns_true_when_consent_active(self) -> None:
        mock_consent = MagicMock()
        mock_consent.status = ConsentStatus.ACTIVE.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_consent
        db.execute.return_value = mock_result

        result = await check_consent(db, uuid4(), ConsentType.NEWSLETTER)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_consent_record(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await check_consent(db, uuid4(), ConsentType.MARKETING_EMAIL)
        assert result is False


class TestGrantConsent:
    """Tests for grant_consent function."""

    @pytest.mark.asyncio
    async def test_creates_new_consent_record(self) -> None:
        user_id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        # Mock the db.add -> flush -> refresh chain
        async def mock_refresh(obj: MagicMock) -> None:
            obj.id = uuid4()

        db.refresh = mock_refresh

        consent = await grant_consent(
            db=db,
            user_id=user_id,
            consent_type=ConsentType.NEWSLETTER,
            method=ConsentMethod.USER_SELF_SERVICE,
            ip_address="127.0.0.1",
        )

        db.add.assert_called_once()
        assert consent is not None

    @pytest.mark.asyncio
    async def test_idempotent_when_already_active(self) -> None:
        user_id = uuid4()
        existing = MagicMock()
        existing.status = ConsentStatus.ACTIVE.value
        existing.consent_type = ConsentType.NEWSLETTER.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        consent = await grant_consent(
            db=db,
            user_id=user_id,
            consent_type=ConsentType.NEWSLETTER,
        )

        assert consent is existing
        # Should not call flush since no change was made
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reactivates_revoked_consent(self) -> None:
        user_id = uuid4()
        existing = MagicMock()
        existing.status = ConsentStatus.REVOKED.value
        existing.consent_type = ConsentType.NEWSLETTER.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        consent = await grant_consent(
            db=db,
            user_id=user_id,
            consent_type=ConsentType.NEWSLETTER,
            ip_address="192.168.1.1",
        )

        assert consent.status == ConsentStatus.ACTIVE.value
        assert consent.opt_out_date is None
        db.flush.assert_awaited_once()


class TestRevokeConsent:
    """Tests for revoke_consent function."""

    @pytest.mark.asyncio
    async def test_revokes_active_consent(self) -> None:
        user_id = uuid4()
        existing = MagicMock()
        existing.status = ConsentStatus.ACTIVE.value
        existing.consent_type = ConsentType.MARKETING_EMAIL.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        consent = await revoke_consent(
            db=db,
            user_id=user_id,
            consent_type=ConsentType.MARKETING_EMAIL,
        )

        assert consent is not None
        assert consent.status == ConsentStatus.REVOKED.value
        assert consent.opt_out_date is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_revoked(self) -> None:
        user_id = uuid4()
        existing = MagicMock()
        existing.status = ConsentStatus.REVOKED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        consent = await revoke_consent(
            db=db,
            user_id=user_id,
            consent_type=ConsentType.NEWSLETTER,
        )

        assert consent is existing
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_record_exists(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await revoke_consent(
            db=db,
            user_id=uuid4(),
            consent_type=ConsentType.SMS_UPDATES,
        )

        assert result is None


class TestGetConsentSummary:
    """Tests for get_consent_summary function."""

    @pytest.mark.asyncio
    async def test_returns_all_types_with_status(self) -> None:
        active_record = MagicMock()
        active_record.consent_type = ConsentType.NEWSLETTER.value
        active_record.status = ConsentStatus.ACTIVE.value

        revoked_record = MagicMock()
        revoked_record.consent_type = ConsentType.MARKETING_EMAIL.value
        revoked_record.status = ConsentStatus.REVOKED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_record, revoked_record]
        db.execute.return_value = mock_result

        summary = await get_consent_summary(db, uuid4())

        # All consent types should be present
        assert len(summary) == len(ConsentType)
        assert summary[ConsentType.NEWSLETTER.value] is True
        assert summary[ConsentType.MARKETING_EMAIL.value] is False
        # Types without records default to False
        assert summary[ConsentType.SMS_UPDATES.value] is False
        assert summary[ConsentType.EVENT_INVITATIONS.value] is False
        assert summary[ConsentType.DONATION_RECEIPTS.value] is False
