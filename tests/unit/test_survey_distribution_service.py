"""Unit tests for survey distribution service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.survey_distribution_service import (
    DEFAULT_PAGE_SIZE,
    DistributionError,
    DistributionNotFoundError,
    InvalidDistributionError,
    create_bulk_distribution,
    create_distribution,
    get_distribution,
    get_distribution_stats,
    list_distributions,
    update_delivery_status,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_distribution_error_is_exception(self) -> None:
        assert isinstance(DistributionError("test"), Exception)

    def test_not_found_is_distribution_error(self) -> None:
        assert isinstance(DistributionNotFoundError("x"), DistributionError)

    def test_invalid_is_distribution_error(self) -> None:
        assert isinstance(InvalidDistributionError("x"), DistributionError)


# --- Helper ---


def _mock_distribution(channel="email", **kwargs):
    """Create a mock survey distribution."""
    d = MagicMock()
    d.id = kwargs.get("id", uuid4())
    d.survey_id = kwargs.get("survey_id", uuid4())
    d.channel = channel
    d.recipient_email = kwargs.get("recipient_email", "test@example.com")
    d.recipient_phone = kwargs.get("recipient_phone")
    d.delivery_status = kwargs.get("delivery_status", "pending")
    d.sent_at = kwargs.get("sent_at")
    d.delivered_at = kwargs.get("delivered_at")
    d.failure_reason = kwargs.get("failure_reason")
    d.sent_by = kwargs.get("sent_by", uuid4())
    d.created_at = kwargs.get("created_at")
    return d


# --- Test create_distribution ---


class TestCreateDistribution:
    """Tests for creating distributions."""

    @pytest.mark.asyncio
    async def test_creates_email_successfully(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution()

        async def fake_refresh(obj):
            for attr in (
                "id",
                "survey_id",
                "channel",
                "recipient_email",
                "recipient_phone",
                "delivery_status",
                "sent_at",
                "delivered_at",
                "failure_reason",
                "sent_by",
                "created_at",
            ):
                setattr(obj, attr, getattr(mock_dist, attr))

        db.refresh = fake_refresh

        result = await create_distribution(
            db=db,
            survey_id=uuid4(),
            channel="email",
            sent_by=uuid4(),
            recipient_email="test@example.com",
        )

        assert result["channel"] == "email"
        assert db.add.called

    @pytest.mark.asyncio
    async def test_invalid_channel_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="Invalid channel"):
            await create_distribution(
                db=db,
                survey_id=uuid4(),
                channel="telegram",
                sent_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_email_without_address_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="requires recipient_email"):
            await create_distribution(
                db=db,
                survey_id=uuid4(),
                channel="email",
                sent_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_whatsapp_without_phone_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="requires recipient_phone"):
            await create_distribution(
                db=db,
                survey_id=uuid4(),
                channel="whatsapp",
                sent_by=uuid4(),
            )


# --- Test create_bulk_distribution ---


class TestCreateBulkDistribution:
    """Tests for bulk distribution."""

    @pytest.mark.asyncio
    async def test_creates_multiple(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution()

        async def fake_refresh(obj):
            for attr in (
                "id",
                "survey_id",
                "channel",
                "recipient_email",
                "recipient_phone",
                "delivery_status",
                "sent_at",
                "delivered_at",
                "failure_reason",
                "sent_by",
                "created_at",
            ):
                setattr(obj, attr, getattr(mock_dist, attr))

        db.refresh = fake_refresh

        recipients = [
            {"email": "a@example.com"},
            {"email": "b@example.com"},
        ]

        result = await create_bulk_distribution(
            db=db,
            survey_id=uuid4(),
            channel="email",
            sent_by=uuid4(),
            recipients=recipients,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_recipients_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="At least one recipient"):
            await create_bulk_distribution(
                db=db,
                survey_id=uuid4(),
                channel="email",
                sent_by=uuid4(),
                recipients=[],
            )

    @pytest.mark.asyncio
    async def test_invalid_channel_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="Invalid channel"):
            await create_bulk_distribution(
                db=db,
                survey_id=uuid4(),
                channel="sms",
                sent_by=uuid4(),
                recipients=[{"email": "a@example.com"}],
            )

    @pytest.mark.asyncio
    async def test_missing_email_in_bulk_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDistributionError, match="requires email"):
            await create_bulk_distribution(
                db=db,
                survey_id=uuid4(),
                channel="email",
                sent_by=uuid4(),
                recipients=[{"phone": "+595123456"}],
            )


# --- Test get_distribution ---


class TestGetDistribution:
    """Tests for fetching distributions."""

    @pytest.mark.asyncio
    async def test_returns_distribution(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_dist
        db.execute.return_value = result_mock

        result = await get_distribution(db, mock_dist.id)
        assert result["id"] == mock_dist.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(DistributionNotFoundError):
            await get_distribution(db, uuid4())


# --- Test list_distributions ---


class TestListDistributions:
    """Tests for listing distributions."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        mock_dist = _mock_distribution()
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = [mock_dist]
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_distributions(db)
        assert result["total"] == 1
        assert len(result["distributions"]) == 1
        assert result["limit"] == DEFAULT_PAGE_SIZE

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = []
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_distributions(db)
        assert result["total"] == 0
        assert result["distributions"] == []


# --- Test update_delivery_status ---


class TestUpdateDeliveryStatus:
    """Tests for updating delivery status."""

    @pytest.mark.asyncio
    async def test_marks_as_sent(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution(delivery_status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_dist
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_delivery_status(db, mock_dist.id, "sent")
        assert mock_dist.delivery_status == "sent"
        assert mock_dist.sent_at is not None

    @pytest.mark.asyncio
    async def test_marks_as_failed_with_reason(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution(delivery_status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_dist
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_delivery_status(db, mock_dist.id, "failed", failure_reason="Invalid phone")
        assert mock_dist.delivery_status == "failed"
        assert mock_dist.failure_reason == "Invalid phone"

    @pytest.mark.asyncio
    async def test_invalid_status_raises(self) -> None:
        db = AsyncMock()
        mock_dist = _mock_distribution()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_dist
        db.execute.return_value = result_mock

        with pytest.raises(InvalidDistributionError, match="Invalid delivery status"):
            await update_delivery_status(db, mock_dist.id, "unknown")

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(DistributionNotFoundError):
            await update_delivery_status(db, uuid4(), "sent")


# --- Test get_distribution_stats ---


class TestGetDistributionStats:
    """Tests for distribution statistics."""

    @pytest.mark.asyncio
    async def test_returns_stats(self) -> None:
        db = AsyncMock()
        survey_id = uuid4()

        # Mock: total=5, then 4 status counts
        total_mock = MagicMock()
        total_mock.scalar_one.return_value = 5

        pending_mock = MagicMock()
        pending_mock.scalar_one.return_value = 2
        sent_mock = MagicMock()
        sent_mock.scalar_one.return_value = 1
        delivered_mock = MagicMock()
        delivered_mock.scalar_one.return_value = 1
        failed_mock = MagicMock()
        failed_mock.scalar_one.return_value = 1

        db.execute.side_effect = [
            total_mock,
            pending_mock,
            sent_mock,
            delivered_mock,
            failed_mock,
        ]

        result = await get_distribution_stats(db, survey_id)
        assert result["total"] == 5
        assert result["survey_id"] == survey_id
        assert "by_status" in result
