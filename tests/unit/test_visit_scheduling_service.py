"""Unit tests for visit scheduling service functions."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.visit_request import VisitRequest, VisitRequestStatus
from src.services.visit_scheduling_service import (
    VisitSchedulingError,
    cancel_visit_request,
    create_visit_request,
    list_adopter_visits,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_visit_request(adopter_id: uuid.UUID, status: str = "pending") -> VisitRequest:
    vr = MagicMock(spec=VisitRequest)
    vr.id = uuid.uuid4()
    vr.adopter_id = adopter_id
    vr.adoption_request_id = uuid.uuid4()
    vr.proposed_slots = ["2026-04-10T10:00:00Z", "2026-04-11T14:00:00Z"]
    vr.address = "Calle Principal 123, Asunción"
    vr.notes = None
    vr.status = status
    vr.created_at = datetime.now(UTC)
    return vr


# ---------------------------------------------------------------------------
# create_visit_request
# ---------------------------------------------------------------------------


class TestCreateVisitRequest:
    @pytest.mark.asyncio()
    async def test_raises_when_no_slots_provided(self, mock_db: AsyncMock) -> None:
        with pytest.raises(VisitSchedulingError) as exc_info:
            await create_visit_request(
                adoption_request_id=uuid.uuid4(),
                adopter_id=uuid.uuid4(),
                proposed_slots=[],
                address="Any address",
                notes=None,
                db=mock_db,
            )
        assert "slot" in exc_info.value.message.lower()

    @pytest.mark.asyncio()
    async def test_raises_when_too_many_slots(self, mock_db: AsyncMock) -> None:
        slots = [f"2026-04-{10+i:02d}T10:00:00Z" for i in range(6)]
        with pytest.raises(VisitSchedulingError) as exc_info:
            await create_visit_request(
                adoption_request_id=uuid.uuid4(),
                adopter_id=uuid.uuid4(),
                proposed_slots=slots,
                address="Any address",
                notes=None,
                db=mock_db,
            )
        assert "maximum" in exc_info.value.message.lower()

    @pytest.mark.asyncio()
    async def test_raises_when_adoption_not_found(self, mock_db: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(VisitSchedulingError) as exc_info:
            await create_visit_request(
                adoption_request_id=uuid.uuid4(),
                adopter_id=uuid.uuid4(),
                proposed_slots=["2026-04-10T10:00:00Z"],
                address="Test address",
                notes=None,
                db=mock_db,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio()
    async def test_creates_request_when_valid(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        adoption_id = uuid.uuid4()

        # Mock finding the adoption request
        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.adopter_id = adopter_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        result = await create_visit_request(
            adoption_request_id=adoption_id,
            adopter_id=adopter_id,
            proposed_slots=["2026-04-10T10:00:00Z", "2026-04-11T14:00:00Z"],
            address="Test address, Asunción",
            notes="Morning preferred",
            db=mock_db,
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result is not None


# ---------------------------------------------------------------------------
# cancel_visit_request
# ---------------------------------------------------------------------------


class TestCancelVisitRequest:
    @pytest.mark.asyncio()
    async def test_raises_when_not_found(self, mock_db: AsyncMock) -> None:
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(VisitSchedulingError) as exc_info:
            await cancel_visit_request(uuid.uuid4(), uuid.uuid4(), mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio()
    async def test_raises_when_wrong_adopter(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        other_adopter_id = uuid.uuid4()
        visit_request = _make_visit_request(other_adopter_id)
        mock_db.get = AsyncMock(return_value=visit_request)

        with pytest.raises(VisitSchedulingError) as exc_info:
            await cancel_visit_request(visit_request.id, adopter_id, mock_db)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio()
    async def test_raises_when_not_pending(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        visit_request = _make_visit_request(adopter_id, status="confirmed")
        mock_db.get = AsyncMock(return_value=visit_request)

        with pytest.raises(VisitSchedulingError) as exc_info:
            await cancel_visit_request(visit_request.id, adopter_id, mock_db)
        assert exc_info.value.status_code == 409
        assert "confirmed" in exc_info.value.message

    @pytest.mark.asyncio()
    async def test_cancels_pending_request(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        visit_request = _make_visit_request(adopter_id, status="pending")
        mock_db.get = AsyncMock(return_value=visit_request)

        await cancel_visit_request(visit_request.id, adopter_id, mock_db)

        assert visit_request.status == VisitRequestStatus.CANCELLED
        mock_db.flush.assert_called_once()


# ---------------------------------------------------------------------------
# list_adopter_visits
# ---------------------------------------------------------------------------


class TestListAdopterVisits:
    @pytest.mark.asyncio()
    async def test_returns_empty_when_no_adoptions(self, mock_db: AsyncMock) -> None:
        # No adoption IDs
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        visits, requests = await list_adopter_visits(uuid.uuid4(), mock_db)
        assert visits == []
        assert requests == []

    @pytest.mark.asyncio()
    async def test_returns_visits_and_requests(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        adoption_id = uuid.uuid4()

        # Call sequence: adoption IDs, home visits, visit requests
        adoption_result = MagicMock()
        adoption_result.fetchall.return_value = [(adoption_id,)]

        mock_home_visit = MagicMock()
        mock_home_visit.id = uuid.uuid4()
        mock_home_visit.adoption_request_id = adoption_id
        mock_home_visit.scheduled_at = datetime.now(UTC)
        mock_home_visit.address = "Test address"
        mock_home_visit.status = "scheduled"
        mock_home_visit.notes = None

        visits_result = MagicMock()
        visits_result.scalars.return_value.all.return_value = [mock_home_visit]

        mock_visit_req = MagicMock()
        mock_visit_req.id = uuid.uuid4()
        mock_visit_req.adoption_request_id = adoption_id
        mock_visit_req.proposed_slots = ["2026-04-10T10:00:00Z"]
        mock_visit_req.address = "Test address"
        mock_visit_req.notes = None
        mock_visit_req.status = "pending"
        mock_visit_req.created_at = datetime.now(UTC)

        requests_result = MagicMock()
        requests_result.scalars.return_value.all.return_value = [mock_visit_req]

        mock_db.execute = AsyncMock(side_effect=[adoption_result, visits_result, requests_result])

        visits, visit_requests = await list_adopter_visits(adopter_id, mock_db)

        assert len(visits) == 1
        assert len(visit_requests) == 1
        assert visits[0].status == "scheduled"
        assert visit_requests[0].status == "pending"
