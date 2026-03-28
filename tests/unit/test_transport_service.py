"""Unit tests for transport service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.transport_service import (
    DEFAULT_PAGE_SIZE,
    VALID_TRANSITIONS,
    InvalidStatusTransitionError,
    InvalidTransportError,
    TransportError,
    TransportNotFoundError,
    cancel_transport_request,
    create_transport_request,
    get_transport_request,
    list_transport_requests,
    update_transport_request,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_transport_error_is_exception(self) -> None:
        assert isinstance(TransportError("test"), Exception)

    def test_not_found_is_transport_error(self) -> None:
        assert isinstance(TransportNotFoundError("x"), TransportError)

    def test_invalid_transport_is_transport_error(self) -> None:
        assert isinstance(InvalidTransportError("x"), TransportError)

    def test_invalid_transition_is_transport_error(self) -> None:
        assert isinstance(InvalidStatusTransitionError("x"), TransportError)


# --- Test Status Transitions ---


class TestStatusTransitions:
    """Tests for valid transition map."""

    def test_open_can_be_claimed(self) -> None:
        assert "claimed" in VALID_TRANSITIONS["open"]

    def test_open_can_be_cancelled(self) -> None:
        assert "cancelled" in VALID_TRANSITIONS["open"]

    def test_claimed_can_go_in_transit(self) -> None:
        assert "in_transit" in VALID_TRANSITIONS["claimed"]

    def test_in_transit_can_be_delivered(self) -> None:
        assert "delivered" in VALID_TRANSITIONS["in_transit"]

    def test_delivered_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["delivered"]) == 0

    def test_cancelled_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["cancelled"]) == 0


# --- Helper ---


def _mock_transport(status="open", **kwargs):
    """Create a mock transport request."""
    t = MagicMock()
    t.id = kwargs.get("id", uuid4())
    t.requester_id = kwargs.get("requester_id", uuid4())
    t.animal_id = kwargs.get("animal_id")
    t.pickup_location = kwargs.get("pickup_location", "Location A")
    t.destination = kwargs.get("destination", "Location B")
    t.urgency = kwargs.get("urgency", "normal")
    t.preferred_date = kwargs.get("preferred_date")
    t.status = status
    t.notes = kwargs.get("notes")
    t.claimed_by = kwargs.get("claimed_by")
    t.created_at = kwargs.get("created_at")
    t.updated_at = kwargs.get("updated_at")
    return t


# --- Test create_transport_request ---


class TestCreateTransportRequest:
    """Tests for creating transport requests."""

    @pytest.mark.asyncio
    async def test_creates_successfully(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        mock_req = _mock_transport(requester_id=user_id)

        async def fake_refresh(obj):
            for attr in (
                "id",
                "requester_id",
                "animal_id",
                "pickup_location",
                "destination",
                "urgency",
                "preferred_date",
                "status",
                "notes",
                "claimed_by",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_req, attr))

        db.refresh = fake_refresh

        result = await create_transport_request(
            db=db,
            requester_id=user_id,
            pickup_location="Park entrance",
            destination="Vet clinic",
        )

        assert result["pickup_location"] == "Location A"  # from mock
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_invalid_urgency_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidTransportError, match="Invalid urgency"):
            await create_transport_request(
                db=db,
                requester_id=uuid4(),
                pickup_location="A",
                destination="B",
                urgency="super_urgent",
            )

    @pytest.mark.asyncio
    async def test_empty_pickup_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidTransportError, match="Pickup location"):
            await create_transport_request(
                db=db,
                requester_id=uuid4(),
                pickup_location="   ",
                destination="B",
            )

    @pytest.mark.asyncio
    async def test_empty_destination_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidTransportError, match="Destination"):
            await create_transport_request(
                db=db,
                requester_id=uuid4(),
                pickup_location="A",
                destination="  ",
            )


# --- Test get_transport_request ---


class TestGetTransportRequest:
    """Tests for fetching transport requests."""

    @pytest.mark.asyncio
    async def test_returns_request(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        result = await get_transport_request(db, mock_req.id)
        assert result["id"] == mock_req.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(TransportNotFoundError):
            await get_transport_request(db, uuid4())


# --- Test update_transport_request ---


class TestUpdateTransportRequest:
    """Tests for updating transport requests."""

    @pytest.mark.asyncio
    async def test_updates_fields(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_transport_request(db, mock_req.id, notes="Updated note")
        assert mock_req.notes == "Updated note"

    @pytest.mark.asyncio
    async def test_valid_status_transition(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport(status="open")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await update_transport_request(db, mock_req.id, status="claimed")
        assert mock_req.status == "claimed"

    @pytest.mark.asyncio
    async def test_invalid_status_transition_raises(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport(status="open")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            await update_transport_request(db, mock_req.id, status="delivered")

    @pytest.mark.asyncio
    async def test_invalid_urgency_raises(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        with pytest.raises(InvalidTransportError, match="Invalid urgency"):
            await update_transport_request(db, mock_req.id, urgency="extreme")

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(TransportNotFoundError):
            await update_transport_request(db, uuid4(), notes="X")


# --- Test cancel_transport_request ---


class TestCancelTransportRequest:
    """Tests for cancelling transport requests."""

    @pytest.mark.asyncio
    async def test_cancels_open_request(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport(status="open")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await cancel_transport_request(db, mock_req.id, uuid4())
        assert mock_req.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cannot_cancel_delivered(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport(status="delivered")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError, match="already"):
            await cancel_transport_request(db, mock_req.id, uuid4())

    @pytest.mark.asyncio
    async def test_cannot_cancel_already_cancelled(self) -> None:
        db = AsyncMock()
        mock_req = _mock_transport(status="cancelled")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_req
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError):
            await cancel_transport_request(db, mock_req.id, uuid4())

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(TransportNotFoundError):
            await cancel_transport_request(db, uuid4(), uuid4())


# --- Test list_transport_requests ---


class TestListTransportRequests:
    """Tests for listing transport requests."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        mock_req = _mock_transport()
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = [mock_req]
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_transport_requests(db)
        assert result["total"] == 1
        assert len(result["requests"]) == 1
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

        result = await list_transport_requests(db)
        assert result["total"] == 0
        assert result["requests"] == []
