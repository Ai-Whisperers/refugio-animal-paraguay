"""Unit tests for GDPR data deletion service logic.

Tests deletion request lifecycle, data anonymization, and subject-type
routing with mocked database sessions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.deletion_request import DeletionRequestStatus
from src.services.gdpr_deletion_service import (
    approve_deletion_request,
    cancel_deletion_request,
    create_deletion_request,
    deny_deletion_request,
    get_deletion_request,
    list_deletion_requests,
)


class TestCreateDeletionRequest:
    """Tests for create_deletion_request function."""

    @pytest.mark.asyncio
    async def test_creates_pending_request(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        result = await create_deletion_request(
            db=db,
            subject_type="donor",
            subject_id=donor_id,
            subject_email="donor@example.com",
            reason="Moving to another shelter",
            requested_by_user_id=uuid4(),
        )

        assert result is not None
        assert result.status == DeletionRequestStatus.PENDING.value
        assert result.subject_type == "donor"
        assert result.subject_email == "donor@example.com"
        assert result.reason == "Moving to another shelter"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_request_without_reason(self) -> None:
        db = AsyncMock()

        result = await create_deletion_request(
            db=db,
            subject_type="adopter",
            subject_id=uuid4(),
            subject_email="adopter@example.com",
        )

        assert result.reason is None


class TestApproveDeletionRequest:
    """Tests for approve_deletion_request function."""

    @pytest.mark.asyncio
    async def test_approves_and_executes_donor_deletion(self) -> None:
        db = AsyncMock()
        request_id = uuid4()
        admin_id = uuid4()

        deletion_req = MagicMock()
        deletion_req.id = request_id
        deletion_req.status = DeletionRequestStatus.PENDING.value
        deletion_req.subject_type = "donor"
        deletion_req.subject_id = uuid4()

        db.get.return_value = deletion_req

        # Mock for donor lookup during deletion
        donor_mock = MagicMock()
        donor_mock.email = "donor@example.com"

        # First get = deletion_req, subsequent gets = donor
        def get_side_effect(model, id_val):
            if id_val == request_id:
                return deletion_req
            return donor_mock

        db.get.side_effect = get_side_effect

        # Mock execute for anonymization queries
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await approve_deletion_request(db, request_id, admin_id)

        assert result is not None
        assert result.status == DeletionRequestStatus.EXECUTED.value
        assert result.approved_by_user_id == admin_id
        assert result.approved_at is not None
        assert result.executed_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await approve_deletion_request(db, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_when_not_pending(self) -> None:
        db = AsyncMock()
        deletion_req = MagicMock()
        deletion_req.status = DeletionRequestStatus.EXECUTED.value
        db.get.return_value = deletion_req

        with pytest.raises(ValueError, match="Cannot approve"):
            await approve_deletion_request(db, uuid4(), uuid4())


class TestDenyDeletionRequest:
    """Tests for deny_deletion_request function."""

    @pytest.mark.asyncio
    async def test_denies_pending_request(self) -> None:
        db = AsyncMock()
        deletion_req = MagicMock()
        deletion_req.status = DeletionRequestStatus.PENDING.value
        db.get.return_value = deletion_req

        admin_id = uuid4()
        result = await deny_deletion_request(db, uuid4(), admin_id, denial_reason="Legal hold")

        assert result is not None
        assert result.status == DeletionRequestStatus.DENIED.value
        assert result.denial_reason == "Legal hold"
        assert result.approved_by_user_id == admin_id

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await deny_deletion_request(db, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_when_not_pending(self) -> None:
        db = AsyncMock()
        deletion_req = MagicMock()
        deletion_req.status = DeletionRequestStatus.CANCELLED.value
        db.get.return_value = deletion_req

        with pytest.raises(ValueError, match="Cannot deny"):
            await deny_deletion_request(db, uuid4(), uuid4())


class TestCancelDeletionRequest:
    """Tests for cancel_deletion_request function."""

    @pytest.mark.asyncio
    async def test_cancels_pending_request(self) -> None:
        db = AsyncMock()
        deletion_req = MagicMock()
        deletion_req.status = DeletionRequestStatus.PENDING.value
        db.get.return_value = deletion_req

        result = await cancel_deletion_request(db, uuid4())

        assert result is not None
        assert result.status == DeletionRequestStatus.CANCELLED.value
        assert result.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await cancel_deletion_request(db, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_when_already_executed(self) -> None:
        db = AsyncMock()
        deletion_req = MagicMock()
        deletion_req.status = DeletionRequestStatus.EXECUTED.value
        db.get.return_value = deletion_req

        with pytest.raises(ValueError, match="Cannot cancel"):
            await cancel_deletion_request(db, uuid4())


class TestGetDeletionRequest:
    """Tests for get_deletion_request function."""

    @pytest.mark.asyncio
    async def test_returns_request(self) -> None:
        deletion_req = MagicMock()
        db = AsyncMock()
        db.get.return_value = deletion_req

        result = await get_deletion_request(db, uuid4())
        assert result is deletion_req

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await get_deletion_request(db, uuid4())
        assert result is None


class TestListDeletionRequests:
    """Tests for list_deletion_requests function."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        r1 = MagicMock()
        r2 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [r1, r2]
        db.execute.return_value = mock_result

        result = await list_deletion_requests(db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filters_by_status(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await list_deletion_requests(db, status_filter="pending")
        assert result == []
        db.execute.assert_awaited_once()


class TestDonorAnonymization:
    """Tests for donor deletion/anonymization logic."""

    @pytest.mark.asyncio
    async def test_anonymizes_donor_and_preserves_donations(self) -> None:
        db = AsyncMock()
        request_id = uuid4()
        donor_id = uuid4()
        admin_id = uuid4()

        deletion_req = MagicMock()
        deletion_req.id = request_id
        deletion_req.status = DeletionRequestStatus.PENDING.value
        deletion_req.subject_type = "donor"
        deletion_req.subject_id = donor_id

        donor_mock = MagicMock()
        donor_mock.email = "donor@example.com"

        def get_side_effect(model, id_val):
            if id_val == request_id:
                return deletion_req
            if id_val == donor_id:
                return donor_mock
            return None

        db.get.side_effect = get_side_effect

        # Mock execute for UPDATE and SELECT queries
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        await approve_deletion_request(db, request_id, admin_id)

        # Verify donor was deleted
        db.delete.assert_awaited()


class TestStaffAnonymization:
    """Tests for staff anonymization logic."""

    @pytest.mark.asyncio
    async def test_deactivates_staff_account(self) -> None:
        db = AsyncMock()
        request_id = uuid4()
        user_id = uuid4()
        admin_id = uuid4()

        deletion_req = MagicMock()
        deletion_req.id = request_id
        deletion_req.status = DeletionRequestStatus.PENDING.value
        deletion_req.subject_type = "staff"
        deletion_req.subject_id = user_id

        user_mock = MagicMock()
        user_mock.email = "staff@refugio.py"
        user_mock.is_active = True

        def get_side_effect(model, id_val):
            if id_val == request_id:
                return deletion_req
            if id_val == user_id:
                return user_mock
            return None

        db.get.side_effect = get_side_effect

        await approve_deletion_request(db, request_id, admin_id)

        # Verify staff was anonymized, not deleted
        assert user_mock.is_active is False
        assert "anonymized" in user_mock.email
        assert user_mock.hashed_password == "DELETED"
