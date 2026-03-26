"""Unit tests for SEPA Direct Debit service logic.

Tests mandate lifecycle with mocked database and Stripe API.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.sepa_mandate import MandateStatus
from src.services.sepa_service import (
    activate_mandate,
    fail_mandate,
    get_donor_mandates,
    revoke_mandate,
)


class TestActivateMandate:
    """Tests for activate_mandate function."""

    @pytest.mark.asyncio
    async def test_activates_pending_mandate(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.PENDING.value
        mandate.id = uuid4()
        mandate.donor_id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mandate
        db.execute.return_value = mock_result

        result = await activate_mandate(db, "seti_123", "mandate_abc")

        assert result is not None
        assert result.status == MandateStatus.ACTIVE.value
        assert result.stripe_mandate_id == "mandate_abc"
        assert result.activated_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_active(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.ACTIVE.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mandate
        db.execute.return_value = mock_result

        result = await activate_mandate(db, "seti_123")

        assert result is mandate
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await activate_mandate(db, "seti_nonexistent")

        assert result is None


class TestFailMandate:
    """Tests for fail_mandate function."""

    @pytest.mark.asyncio
    async def test_fails_pending_mandate(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.PENDING.value
        mandate.id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mandate
        db.execute.return_value = mock_result

        result = await fail_mandate(db, "seti_123", "Bank account closed")

        assert result is not None
        assert result.status == MandateStatus.FAILED.value
        assert result.failure_reason == "Bank account closed"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_failed(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.FAILED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mandate
        db.execute.return_value = mock_result

        result = await fail_mandate(db, "seti_123")

        assert result is mandate
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await fail_mandate(db, "seti_nonexistent")

        assert result is None


class TestRevokeMandate:
    """Tests for revoke_mandate function."""

    @pytest.mark.asyncio
    async def test_revokes_active_mandate(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.ACTIVE.value
        mandate.id = uuid4()
        mandate.donor_id = uuid4()
        mandate.stripe_subscription_id = None

        db = AsyncMock()
        db.get.return_value = mandate

        result = await revoke_mandate(db, mandate.id)

        assert result is not None
        assert result.status == MandateStatus.REVOKED.value
        assert result.revoked_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_revoked(self) -> None:
        mandate = MagicMock()
        mandate.status = MandateStatus.REVOKED.value

        db = AsyncMock()
        db.get.return_value = mandate

        result = await revoke_mandate(db, uuid4())

        assert result is mandate
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await revoke_mandate(db, uuid4())

        assert result is None


class TestGetDonorMandates:
    """Tests for get_donor_mandates function."""

    @pytest.mark.asyncio
    async def test_returns_list_of_mandates(self) -> None:
        m1 = MagicMock()
        m2 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [m1, m2]
        db.execute.return_value = mock_result

        result = await get_donor_mandates(db, uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_mandates(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_donor_mandates(db, uuid4())

        assert result == []
