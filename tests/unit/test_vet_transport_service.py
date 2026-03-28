"""Unit tests for vet transport integration service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.vet_transport_service import (
    DEFAULT_PAGE_SIZE,
    VALID_TRANSITIONS,
    DuplicateLinkError,
    InvalidLinkError,
    InvalidStatusTransitionError,
    LinkNotFoundError,
    VetTransportError,
    create_link,
    delete_link,
    get_link,
    list_links,
    update_link_status,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_vet_transport_error_is_exception(self) -> None:
        assert isinstance(VetTransportError("test"), Exception)

    def test_not_found_is_vet_transport_error(self) -> None:
        assert isinstance(LinkNotFoundError("x"), VetTransportError)

    def test_duplicate_is_vet_transport_error(self) -> None:
        assert isinstance(DuplicateLinkError("x"), VetTransportError)

    def test_invalid_is_vet_transport_error(self) -> None:
        assert isinstance(InvalidLinkError("x"), VetTransportError)

    def test_invalid_transition_is_vet_transport_error(self) -> None:
        assert isinstance(InvalidStatusTransitionError("x"), VetTransportError)


# --- Test Status Transitions ---


class TestStatusTransitions:
    """Tests for valid transition map."""

    def test_scheduled_can_go_in_progress(self) -> None:
        assert "in_progress" in VALID_TRANSITIONS["scheduled"]

    def test_scheduled_can_be_cancelled(self) -> None:
        assert "cancelled" in VALID_TRANSITIONS["scheduled"]

    def test_in_progress_can_complete(self) -> None:
        assert "completed" in VALID_TRANSITIONS["in_progress"]

    def test_completed_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["completed"]) == 0

    def test_cancelled_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["cancelled"]) == 0


# --- Helper ---


def _mock_link(status="scheduled", **kwargs):
    """Create a mock vet-transport link."""
    link = MagicMock()
    link.id = kwargs.get("id", uuid4())
    link.transport_request_id = kwargs.get("transport_request_id", uuid4())
    link.vet_visit_id = kwargs.get("vet_visit_id", uuid4())
    link.animal_id = kwargs.get("animal_id", uuid4())
    link.status = status
    link.pickup_time = kwargs.get("pickup_time")
    link.dropoff_time = kwargs.get("dropoff_time")
    link.notes = kwargs.get("notes")
    link.created_by = kwargs.get("created_by", uuid4())
    link.created_at = kwargs.get("created_at")
    link.updated_at = kwargs.get("updated_at")
    return link


# --- Test create_link ---


class TestCreateLink:
    """Tests for creating vet-transport links."""

    @pytest.mark.asyncio
    async def test_creates_successfully(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link()

        # Mock duplicate check returning 0
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result

        async def fake_refresh(obj):
            for attr in (
                "id",
                "transport_request_id",
                "vet_visit_id",
                "animal_id",
                "status",
                "pickup_time",
                "dropoff_time",
                "notes",
                "created_by",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_lnk, attr))

        db.refresh = fake_refresh

        result = await create_link(
            db=db,
            transport_request_id=uuid4(),
            vet_visit_id=uuid4(),
            animal_id=uuid4(),
            created_by=uuid4(),
        )

        assert result["status"] == "scheduled"
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_duplicate_link_raises(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        db.execute.return_value = count_result

        with pytest.raises(DuplicateLinkError, match="already exists"):
            await create_link(
                db=db,
                transport_request_id=uuid4(),
                vet_visit_id=uuid4(),
                animal_id=uuid4(),
                created_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_dropoff_before_pickup_raises(self) -> None:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.return_value = count_result

        now = datetime.now(UTC)
        with pytest.raises(InvalidLinkError, match="Dropoff time must be after"):
            await create_link(
                db=db,
                transport_request_id=uuid4(),
                vet_visit_id=uuid4(),
                animal_id=uuid4(),
                created_by=uuid4(),
                pickup_time=now,
                dropoff_time=now - timedelta(hours=1),
            )


# --- Test get_link ---


class TestGetLink:
    """Tests for fetching links."""

    @pytest.mark.asyncio
    async def test_returns_link(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        result = await get_link(db, mock_lnk.id)
        assert result["id"] == mock_lnk.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(LinkNotFoundError):
            await get_link(db, uuid4())


# --- Test list_links ---


class TestListLinks:
    """Tests for listing links."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        mock_lnk = _mock_link()
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = [mock_lnk]
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_links(db)
        assert result["total"] == 1
        assert len(result["links"]) == 1
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

        result = await list_links(db)
        assert result["total"] == 0
        assert result["links"] == []


# --- Test update_link_status ---


class TestUpdateLinkStatus:
    """Tests for updating link status."""

    @pytest.mark.asyncio
    async def test_valid_transition(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link(status="scheduled")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_link_status(db, mock_lnk.id, "in_progress")
        assert mock_lnk.status == "in_progress"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link(status="completed")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            await update_link_status(db, mock_lnk.id, "scheduled")

    @pytest.mark.asyncio
    async def test_invalid_status_raises(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link(status="scheduled")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        with pytest.raises(InvalidLinkError, match="Invalid status"):
            await update_link_status(db, mock_lnk.id, "bogus")

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(LinkNotFoundError):
            await update_link_status(db, uuid4(), "in_progress")


# --- Test delete_link ---


class TestDeleteLink:
    """Tests for deleting links."""

    @pytest.mark.asyncio
    async def test_deletes_scheduled(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link(status="scheduled")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        await delete_link(db, mock_lnk.id)
        db.delete.assert_called_once_with(mock_lnk)

    @pytest.mark.asyncio
    async def test_cannot_delete_in_progress(self) -> None:
        db = AsyncMock()
        mock_lnk = _mock_link(status="in_progress")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_lnk
        db.execute.return_value = result_mock

        with pytest.raises(InvalidLinkError, match="Cannot delete"):
            await delete_link(db, mock_lnk.id)

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(LinkNotFoundError):
            await delete_link(db, uuid4())
