"""Unit tests for the vet clinic service layer."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.vet_clinic import ClinicStatus
from src.services.vet_clinic_service import (
    VALID_STATUS_TRANSITIONS,
    ClinicNotFoundError,
    InvalidStatusTransitionError,
    create_clinic,
    delete_clinic,
    get_clinic,
    update_clinic,
    update_clinic_status,
)


class TestValidStatusTransitions:
    """Tests for status transition validation rules."""

    def test_pending_can_become_active(self) -> None:
        assert ClinicStatus.ACTIVE in VALID_STATUS_TRANSITIONS[ClinicStatus.PENDING]

    def test_pending_can_become_inactive(self) -> None:
        assert ClinicStatus.INACTIVE in VALID_STATUS_TRANSITIONS[ClinicStatus.PENDING]

    def test_pending_cannot_become_suspended(self) -> None:
        assert ClinicStatus.SUSPENDED not in VALID_STATUS_TRANSITIONS[ClinicStatus.PENDING]

    def test_active_can_become_suspended(self) -> None:
        assert ClinicStatus.SUSPENDED in VALID_STATUS_TRANSITIONS[ClinicStatus.ACTIVE]

    def test_active_can_become_inactive(self) -> None:
        assert ClinicStatus.INACTIVE in VALID_STATUS_TRANSITIONS[ClinicStatus.ACTIVE]

    def test_suspended_can_become_active(self) -> None:
        assert ClinicStatus.ACTIVE in VALID_STATUS_TRANSITIONS[ClinicStatus.SUSPENDED]

    def test_inactive_can_become_pending(self) -> None:
        assert ClinicStatus.PENDING in VALID_STATUS_TRANSITIONS[ClinicStatus.INACTIVE]


class TestCreateClinic:
    """Tests for clinic creation."""

    @pytest.mark.asyncio()
    async def test_creates_and_returns_clinic(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        data = {
            "name": "Clinica Veterinaria Central",
            "email": "info@vetcentral.com.py",
            "phone": "+595981234567",
            "contact_person": "Dr. Martinez",
            "address": "Av. Mariscal Lopez 1234",
            "city": "Asuncion",
        }

        await create_clinic(db, data)
        assert db.add.called
        assert db.flush.called
        assert db.refresh.called


class TestGetClinic:
    """Tests for fetching a single clinic."""

    @pytest.mark.asyncio()
    async def test_returns_clinic_when_found(self) -> None:
        db = AsyncMock()
        mock_clinic = MagicMock()
        mock_clinic.id = uuid4()
        db.get.return_value = mock_clinic

        result = await get_clinic(db, mock_clinic.id)
        assert result == mock_clinic

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_missing(self) -> None:
        db = AsyncMock()
        db.get.return_value = None
        clinic_id = uuid4()

        with pytest.raises(ClinicNotFoundError, match=str(clinic_id)):
            await get_clinic(db, clinic_id)


class TestUpdateClinicStatus:
    """Tests for status transitions."""

    @pytest.mark.asyncio()
    async def test_pending_to_active_sets_partnership_start(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_clinic = MagicMock()
        mock_clinic.status = ClinicStatus.PENDING
        mock_clinic.partnership_start = None
        db.get.return_value = mock_clinic

        result = await update_clinic_status(db, uuid4(), ClinicStatus.ACTIVE)
        assert result.status == ClinicStatus.ACTIVE
        assert result.partnership_start is not None

    @pytest.mark.asyncio()
    async def test_active_to_inactive_sets_partnership_end(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_clinic = MagicMock()
        mock_clinic.status = ClinicStatus.ACTIVE
        mock_clinic.partnership_end = None
        db.get.return_value = mock_clinic

        result = await update_clinic_status(db, uuid4(), ClinicStatus.INACTIVE)
        assert result.status == ClinicStatus.INACTIVE
        assert result.partnership_end is not None

    @pytest.mark.asyncio()
    async def test_rejects_invalid_transition(self) -> None:
        db = AsyncMock()
        mock_clinic = MagicMock()
        mock_clinic.status = ClinicStatus.PENDING
        db.get.return_value = mock_clinic

        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            await update_clinic_status(db, uuid4(), ClinicStatus.SUSPENDED)


class TestDeleteClinic:
    """Tests for clinic deletion."""

    @pytest.mark.asyncio()
    async def test_deletes_pending_clinic(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.delete = AsyncMock()

        mock_clinic = MagicMock()
        mock_clinic.status = ClinicStatus.PENDING
        db.get.return_value = mock_clinic

        await delete_clinic(db, uuid4())
        assert db.delete.called

    @pytest.mark.asyncio()
    async def test_rejects_deleting_active_clinic(self) -> None:
        db = AsyncMock()
        mock_clinic = MagicMock()
        mock_clinic.status = ClinicStatus.ACTIVE
        db.get.return_value = mock_clinic

        with pytest.raises(InvalidStatusTransitionError):
            await delete_clinic(db, uuid4())


class TestUpdateClinic:
    """Tests for updating clinic fields."""

    @pytest.mark.asyncio()
    async def test_updates_provided_fields(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_clinic = MagicMock()
        mock_clinic.name = "Old Name"
        db.get.return_value = mock_clinic

        result = await update_clinic(db, uuid4(), {"name": "New Name"})
        assert result.name == "New Name"

    @pytest.mark.asyncio()
    async def test_raises_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ClinicNotFoundError):
            await update_clinic(db, uuid4(), {"name": "X"})


class TestExceptionMessages:
    """Tests for exception attributes."""

    def test_clinic_not_found_has_id(self) -> None:
        clinic_id = uuid4()
        err = ClinicNotFoundError(clinic_id)
        assert err.clinic_id == clinic_id
        assert str(clinic_id) in err.message

    def test_invalid_transition_has_details(self) -> None:
        err = InvalidStatusTransitionError("pending", "suspended")
        assert err.current == "pending"
        assert err.requested == "suspended"
        assert "pending" in err.message
        assert "suspended" in err.message
