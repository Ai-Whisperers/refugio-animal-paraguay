"""Unit tests for GDPR deletion audit trail (RAP-228).

Verifies that process_deletion_request() and profile_service functions
record audit entries using AuditAction.GDPR_ERASURE.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.db.models.audit_log import AuditAction


class TestAuditActionGdprErasure:
    """Tests that GDPR_ERASURE is a valid AuditAction."""

    def test_gdpr_erasure_is_string_enum(self) -> None:
        assert isinstance(AuditAction.GDPR_ERASURE, str)

    def test_gdpr_erasure_value(self) -> None:
        assert AuditAction.GDPR_ERASURE == "gdpr_erasure"

    def test_gdpr_erasure_in_action_values(self) -> None:
        values = {a.value for a in AuditAction}
        assert "gdpr_erasure" in values


class TestGdprDeletionServiceAudit:
    """Tests that process_deletion_request records audit entry."""

    @pytest.mark.asyncio
    async def test_process_deletion_request_records_audit(self) -> None:
        """process_deletion_request calls record_audit with GDPR_ERASURE action."""
        user_id = uuid4()

        db = MagicMock()
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(rowcount=0, scalars=lambda: MagicMock(all=lambda: [])))

        with (
            patch("src.services.gdpr_deletion_service.deactivate_user_account", new=AsyncMock(return_value=True)),
            patch("src.services.gdpr_deletion_service.delete_user_consents", new=AsyncMock(return_value=0)),
            patch("src.services.gdpr_deletion_service.delete_user_notifications", new=AsyncMock(return_value=0)),
            patch("src.services.gdpr_deletion_service.record_audit", new=AsyncMock()) as mock_record_audit,
        ):
            from src.services.gdpr_deletion_service import process_deletion_request

            await process_deletion_request(db, user_id=user_id)

            mock_record_audit.assert_awaited_once()
            call_kwargs = mock_record_audit.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.GDPR_ERASURE
            assert call_kwargs["resource_type"] == "user"
            assert call_kwargs["resource_id"] == str(user_id)
            assert call_kwargs["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_process_deletion_request_audit_includes_summary(self) -> None:
        """Audit entry new_values contains the deletion summary."""
        user_id = uuid4()

        db = MagicMock()
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(rowcount=0, scalars=lambda: MagicMock(all=lambda: [])))

        with (
            patch("src.services.gdpr_deletion_service.deactivate_user_account", new=AsyncMock(return_value=True)),
            patch("src.services.gdpr_deletion_service.delete_user_consents", new=AsyncMock(return_value=2)),
            patch("src.services.gdpr_deletion_service.delete_user_notifications", new=AsyncMock(return_value=3)),
            patch("src.services.gdpr_deletion_service.record_audit", new=AsyncMock()) as mock_record_audit,
        ):
            from src.services.gdpr_deletion_service import process_deletion_request

            await process_deletion_request(db, user_id=user_id)

            call_kwargs = mock_record_audit.call_args.kwargs
            new_values = call_kwargs["new_values"]
            assert new_values["user_id"] == str(user_id)
            assert new_values["user_deactivated"] is True
            assert new_values["consents_deleted"] == 2
            assert new_values["notifications_deleted"] == 3


class TestProfileServiceDeletionAudit:
    """Tests that profile_service deletion functions record audit entries."""

    @pytest.mark.asyncio
    async def test_request_account_deletion_records_audit(self) -> None:
        """request_account_deletion records GDPR_ERASURE audit at initiation."""
        from src.auth.utils import hash_password

        user = MagicMock()
        user.id = uuid4()
        user.hashed_password = hash_password("TestPass123!")

        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))
        db.add = MagicMock()
        db.flush = AsyncMock()

        with patch("src.services.profile_service.record_audit", new=AsyncMock()) as mock_audit:
            from src.services.profile_service import request_account_deletion

            result = await request_account_deletion(db, user, "TestPass123!")

            assert result is not None
            mock_audit.assert_awaited_once()
            call_kwargs = mock_audit.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.GDPR_ERASURE
            assert call_kwargs["new_values"]["stage"] == "deletion_requested"

    @pytest.mark.asyncio
    async def test_request_account_deletion_wrong_password_no_audit(self) -> None:
        """request_account_deletion does NOT record audit when password is wrong."""
        from src.auth.utils import hash_password

        user = MagicMock()
        user.id = uuid4()
        user.hashed_password = hash_password("CorrectPass123!")

        db = MagicMock()

        with patch("src.services.profile_service.record_audit", new=AsyncMock()) as mock_audit:
            from src.services.profile_service import request_account_deletion

            result = await request_account_deletion(db, user, "WrongPass999!")

            assert result is None
            mock_audit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_confirm_account_deletion_records_audit(self) -> None:
        """confirm_account_deletion records GDPR_ERASURE audit on success."""
        from datetime import UTC, datetime, timedelta

        user_id = uuid4()
        token_value = "valid-token-abc123"

        mock_token = MagicMock()
        mock_token.user_id = user_id
        mock_token.token_type = "account_deletion"
        mock_token.used_at = None
        mock_token.expires_at = datetime.now(UTC) + timedelta(hours=24)

        mock_user = MagicMock()
        mock_user.id = user_id

        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_token)))
        db.get = AsyncMock(return_value=mock_user)
        db.flush = AsyncMock()

        with patch("src.services.profile_service.record_audit", new=AsyncMock()) as mock_audit:
            from src.services.profile_service import confirm_account_deletion

            result = await confirm_account_deletion(db, token_value)

            assert result is True
            mock_audit.assert_awaited_once()
            call_kwargs = mock_audit.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.GDPR_ERASURE
            assert call_kwargs["resource_id"] == str(user_id)
            assert call_kwargs["new_values"]["stage"] == "deletion_confirmed"
            assert call_kwargs["new_values"]["user_deactivated"] is True

    @pytest.mark.asyncio
    async def test_confirm_account_deletion_invalid_token_no_audit(self) -> None:
        """confirm_account_deletion does NOT record audit when token is invalid."""
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        with patch("src.services.profile_service.record_audit", new=AsyncMock()) as mock_audit:
            from src.services.profile_service import confirm_account_deletion

            result = await confirm_account_deletion(db, "invalid-token")

            assert result is False
            mock_audit.assert_not_awaited()
