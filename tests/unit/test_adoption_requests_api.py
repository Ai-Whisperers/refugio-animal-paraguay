"""Unit tests for src/api/adoption_requests.py.

Uses AsyncMock to replace DB and event bus dependencies —
no live database required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from src.api.adoption_requests import (
    _ALLOWED_TRANSITIONS,
    create_adoption_request,
    generate_adoption_contract,
    get_adoption_request,
    list_adoption_requests,
    update_adoption_request_status,
)
from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.user import User, UserRole
from src.schemas.adoption_request import (
    AdoptionRequestCreate,
    AdoptionRequestStatusUpdate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> AsyncMock:
    """Return a minimal AsyncSession mock."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_event_bus(running: bool = False) -> MagicMock:
    bus = MagicMock()
    bus.is_running = running
    bus.publish = AsyncMock()
    return bus


def _make_user(role: UserRole = UserRole.STAFF) -> User:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.role = role.value
    return user


def _make_animal(animal_id=None) -> Animal:
    animal = MagicMock(spec=Animal)
    animal.id = animal_id or uuid4()
    animal.name = "Luna"
    animal.species = "dog"
    animal.breed = "Labrador Mix"
    animal.status = "available"
    animal.updated_at = datetime.now(UTC)
    return animal


def _make_adopter(adopter_id=None, deleted: bool = False) -> Adopter:
    adopter = MagicMock(spec=Adopter)
    adopter.id = adopter_id or uuid4()
    adopter.full_name = "Maria Garcia"
    adopter.email = "maria@example.com"
    adopter.phone = "+595981234567"
    adopter.address = "Asuncion, Paraguay"
    adopter.deleted_at = datetime.now(UTC) if deleted else None
    return adopter


def _make_request(
    req_id=None,
    status: str = "pending",
    animal_id=None,
    adopter_id=None,
) -> AdoptionRequest:
    req = MagicMock(spec=AdoptionRequest)
    req.id = req_id or uuid4()
    req.status = status
    req.animal_id = animal_id or uuid4()
    req.adopter_id = adopter_id or uuid4()
    req.submitted_at = datetime.now(UTC)
    req.decided_at = None
    req.notes = None
    req.contract_pdf_path = None
    req.contract_generated_at = None
    req.updated_at = datetime.now(UTC)
    return req


# ---------------------------------------------------------------------------
# _ALLOWED_TRANSITIONS
# ---------------------------------------------------------------------------


class TestAllowedTransitions:
    def test_pending_can_approve(self) -> None:
        assert AdoptionRequestStatus.APPROVED in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.PENDING]

    def test_pending_can_reject(self) -> None:
        assert AdoptionRequestStatus.REJECTED in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.PENDING]

    def test_pending_can_cancel(self) -> None:
        assert (
            AdoptionRequestStatus.CANCELLED in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.PENDING]
        )

    def test_approved_can_cancel(self) -> None:
        assert (
            AdoptionRequestStatus.CANCELLED in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.APPROVED]
        )

    def test_approved_cannot_reject(self) -> None:
        assert (
            AdoptionRequestStatus.REJECTED
            not in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.APPROVED]
        )

    def test_rejected_can_cancel(self) -> None:
        assert (
            AdoptionRequestStatus.CANCELLED in _ALLOWED_TRANSITIONS[AdoptionRequestStatus.REJECTED]
        )

    def test_cancelled_has_no_transitions(self) -> None:
        assert len(_ALLOWED_TRANSITIONS[AdoptionRequestStatus.CANCELLED]) == 0


# ---------------------------------------------------------------------------
# list_adoption_requests
# ---------------------------------------------------------------------------


class TestListAdoptionRequests:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = _make_db()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute.return_value = result_mock

        result = await list_adoption_requests(
            status_filter=None,
            animal_id=None,
            adopter_id=None,
            offset=0,
            limit=20,
            db=db,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_requests(self) -> None:
        db = _make_db()
        req1 = _make_request()
        req2 = _make_request()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [req1, req2]
        db.execute.return_value = result_mock

        result = await list_adoption_requests(
            status_filter=None,
            animal_id=None,
            adopter_id=None,
            offset=0,
            limit=20,
            db=db,
        )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filters_by_status(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [req]
        db.execute.return_value = result_mock

        result = await list_adoption_requests(
            status_filter=AdoptionRequestStatus.PENDING,
            animal_id=None,
            adopter_id=None,
            offset=0,
            limit=20,
            db=db,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_filters_by_animal_id(self) -> None:
        db = _make_db()
        animal_id = uuid4()
        req = _make_request(animal_id=animal_id)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [req]
        db.execute.return_value = result_mock

        result = await list_adoption_requests(
            status_filter=None,
            animal_id=animal_id,
            adopter_id=None,
            offset=0,
            limit=20,
            db=db,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_filters_by_adopter_id(self) -> None:
        db = _make_db()
        adopter_id = uuid4()
        req = _make_request(adopter_id=adopter_id)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [req]
        db.execute.return_value = result_mock

        result = await list_adoption_requests(
            status_filter=None,
            animal_id=None,
            adopter_id=adopter_id,
            offset=0,
            limit=20,
            db=db,
        )
        assert len(result) == 1


# ---------------------------------------------------------------------------
# get_adoption_request
# ---------------------------------------------------------------------------


class TestGetAdoptionRequest:
    @pytest.mark.asyncio
    async def test_returns_request(self) -> None:
        db = _make_db()
        req = _make_request()
        db.get.return_value = req

        result = await get_adoption_request(request_id=req.id, db=db)
        assert result.id == req.id

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self) -> None:
        db = _make_db()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_adoption_request(request_id=uuid4(), db=db)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# create_adoption_request
# ---------------------------------------------------------------------------


class TestCreateAdoptionRequest:
    @pytest.mark.asyncio
    async def test_creates_request_successfully(self) -> None:
        db = _make_db()
        animal = _make_animal()
        adopter = _make_adopter()

        # db.get returns animal first, then adopter
        db.get.side_effect = [animal, adopter]

        req_id = uuid4()

        async def refresh_side_effect(obj: AdoptionRequest) -> None:
            obj.id = req_id

        db.refresh.side_effect = refresh_side_effect

        payload = AdoptionRequestCreate(
            animal_id=animal.id,
            adopter_id=adopter.id,
        )
        user = _make_user()
        event_bus = _make_event_bus(running=False)

        await create_adoption_request(
            payload=payload,
            db=db,
            current_user=user,
            event_bus=event_bus,
        )
        db.add.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_404_when_animal_not_found(self) -> None:
        db = _make_db()
        db.get.return_value = None  # animal not found

        payload = AdoptionRequestCreate(animal_id=uuid4(), adopter_id=uuid4())
        user = _make_user()
        event_bus = _make_event_bus()

        with pytest.raises(HTTPException) as exc:
            await create_adoption_request(
                payload=payload, db=db, current_user=user, event_bus=event_bus
            )
        assert exc.value.status_code == 404
        assert "Animal not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_raises_404_when_adopter_not_found(self) -> None:
        db = _make_db()
        animal = _make_animal()
        db.get.side_effect = [animal, None]  # animal ok, adopter None

        payload = AdoptionRequestCreate(animal_id=animal.id, adopter_id=uuid4())
        user = _make_user()
        event_bus = _make_event_bus()

        with pytest.raises(HTTPException) as exc:
            await create_adoption_request(
                payload=payload, db=db, current_user=user, event_bus=event_bus
            )
        assert exc.value.status_code == 404
        assert "Adopter not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_raises_404_when_adopter_soft_deleted(self) -> None:
        db = _make_db()
        animal = _make_animal()
        adopter = _make_adopter(deleted=True)
        db.get.side_effect = [animal, adopter]

        payload = AdoptionRequestCreate(animal_id=animal.id, adopter_id=adopter.id)
        user = _make_user()
        event_bus = _make_event_bus()

        with pytest.raises(HTTPException) as exc:
            await create_adoption_request(
                payload=payload, db=db, current_user=user, event_bus=event_bus
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_publishes_event_when_bus_running(self) -> None:
        db = _make_db()
        animal = _make_animal()
        adopter = _make_adopter()
        db.get.side_effect = [animal, adopter]
        db.refresh.side_effect = AsyncMock()

        payload = AdoptionRequestCreate(animal_id=animal.id, adopter_id=adopter.id)
        user = _make_user()
        event_bus = _make_event_bus(running=True)

        await create_adoption_request(
            payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_publish_event_when_bus_stopped(self) -> None:
        db = _make_db()
        animal = _make_animal()
        adopter = _make_adopter()
        db.get.side_effect = [animal, adopter]
        db.refresh.side_effect = AsyncMock()

        payload = AdoptionRequestCreate(animal_id=animal.id, adopter_id=adopter.id)
        user = _make_user()
        event_bus = _make_event_bus(running=False)

        await create_adoption_request(
            payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        event_bus.publish.assert_not_called()


# ---------------------------------------------------------------------------
# update_adoption_request_status
# ---------------------------------------------------------------------------


class TestUpdateAdoptionRequestStatus:
    @pytest.mark.asyncio
    async def test_raises_404_when_request_not_found(self) -> None:
        db = _make_db()
        db.get.return_value = None

        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.APPROVED)
        user = _make_user()
        event_bus = _make_event_bus()

        with pytest.raises(HTTPException) as exc:
            await update_adoption_request_status(
                request_id=uuid4(), payload=payload, db=db, current_user=user, event_bus=event_bus
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_422_for_invalid_transition(self) -> None:
        db = _make_db()
        req = _make_request(status="approved")
        db.get.return_value = req

        # APPROVED → PENDING is not allowed
        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.PENDING)
        user = _make_user()
        event_bus = _make_event_bus()

        with pytest.raises(HTTPException) as exc:
            await update_adoption_request_status(
                request_id=req.id, payload=payload, db=db, current_user=user, event_bus=event_bus
            )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_approves_request_and_sets_animal_adopted(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        animal = _make_animal(animal_id=req.animal_id)
        # First call returns req, second returns animal for side-effect
        db.get.side_effect = [req, animal]

        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.APPROVED)
        user = _make_user()
        event_bus = _make_event_bus(running=False)

        await update_adoption_request_status(
            request_id=req.id, payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        assert animal.status == "adopted"
        assert req.status == "approved"

    @pytest.mark.asyncio
    async def test_cancels_pending_request(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        db.get.return_value = req

        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.CANCELLED)
        user = _make_user()
        event_bus = _make_event_bus(running=False)

        await update_adoption_request_status(
            request_id=req.id, payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        assert req.status == "cancelled"

    @pytest.mark.asyncio
    async def test_rejects_pending_request(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        db.get.return_value = req

        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.REJECTED)
        user = _make_user()
        event_bus = _make_event_bus(running=False)

        await update_adoption_request_status(
            request_id=req.id, payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        assert req.status == "rejected"

    @pytest.mark.asyncio
    async def test_publishes_event_when_bus_running(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        db.get.return_value = req

        payload = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.APPROVED)
        user = _make_user()
        event_bus = _make_event_bus(running=True)

        await update_adoption_request_status(
            request_id=req.id, payload=payload, db=db, current_user=user, event_bus=event_bus
        )
        event_bus.publish.assert_called_once()


# ---------------------------------------------------------------------------
# generate_adoption_contract
# ---------------------------------------------------------------------------


class TestGenerateAdoptionContract:
    @pytest.mark.asyncio
    async def test_raises_404_when_request_not_found(self) -> None:
        db = _make_db()
        db.get.return_value = None
        user = _make_user()

        with pytest.raises(HTTPException) as exc:
            await generate_adoption_contract(request_id=uuid4(), db=db, _=user)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_422_when_not_approved(self) -> None:
        db = _make_db()
        req = _make_request(status="pending")
        db.get.return_value = req
        user = _make_user()

        with pytest.raises(HTTPException) as exc:
            await generate_adoption_contract(request_id=req.id, db=db, _=user)
        assert exc.value.status_code == 422
        assert "approved" in exc.value.detail

    @pytest.mark.asyncio
    async def test_raises_404_when_adopter_missing(self) -> None:
        db = _make_db()
        req = _make_request(status="approved")
        # req found, adopter not found
        db.get.side_effect = [req, None]
        user = _make_user()

        with pytest.raises(HTTPException) as exc:
            await generate_adoption_contract(request_id=req.id, db=db, _=user)
        assert exc.value.status_code == 404
        assert "Adopter not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_raises_404_when_animal_missing(self) -> None:
        db = _make_db()
        req = _make_request(status="approved")
        adopter = _make_adopter()
        # req found, adopter found, animal not found
        db.get.side_effect = [req, adopter, None]
        user = _make_user()

        with pytest.raises(HTTPException) as exc:
            await generate_adoption_contract(request_id=req.id, db=db, _=user)
        assert exc.value.status_code == 404
        assert "Animal not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_generates_contract_successfully(self) -> None:
        db = _make_db()
        req = _make_request(status="approved")
        req.decided_at = datetime.now(UTC)
        adopter = _make_adopter()
        animal = _make_animal()
        db.get.side_effect = [req, adopter, animal]

        user = _make_user()

        with patch("src.api.adoption_requests.ContractPDFGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "/tmp/contract.pdf"
            mock_gen.return_value = mock_instance

            result = await generate_adoption_contract(request_id=req.id, db=db, _=user)

        assert "request_id" in result
        assert "contract_pdf_path" in result
        assert "contract_generated_at" in result
        mock_instance.generate.assert_called_once()
