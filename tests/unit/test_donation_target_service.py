"""Unit tests for donation target validation service.

Tests target consistency validation, target type validation,
and individual target type validators.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.donation import DonationTargetType
from src.services.donation_target_service import (
    DIRECTED_TARGET_TYPES,
    InvalidTargetError,
    TargetNotActiveError,
    validate_donation_target,
    validate_target_consistency,
)

# --- Helpers ---


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.get = AsyncMock()
    return db


# --- Target Consistency Tests ---


class TestValidateTargetConsistency:
    """Tests for target_type and target_id consistency rules."""

    def test_general_with_no_target_id(self) -> None:
        validate_target_consistency("general", None)

    def test_general_with_target_id_raises(self) -> None:
        with pytest.raises(InvalidTargetError, match="must be null"):
            validate_target_consistency("general", uuid4())

    def test_directed_without_target_id_raises(self) -> None:
        with pytest.raises(InvalidTargetError, match="required"):
            validate_target_consistency("animal", None)

    def test_directed_with_target_id(self) -> None:
        validate_target_consistency("animal", uuid4())

    def test_unknown_target_type_raises(self) -> None:
        with pytest.raises(InvalidTargetError, match="Unknown target type"):
            validate_target_consistency("spaceship", uuid4())

    def test_all_valid_types_accepted(self) -> None:
        for target_type in DonationTargetType:
            if target_type == DonationTargetType.GENERAL:
                validate_target_consistency(target_type.value, None)
            else:
                validate_target_consistency(target_type.value, uuid4())


# --- Animal Target Validation Tests ---


class TestAnimalTargetValidation:
    """Tests for animal target validation."""

    @pytest.mark.asyncio
    async def test_valid_animal_target(self) -> None:
        db = _mock_db()
        animal_id = uuid4()
        animal = MagicMock()
        animal.status = "available"
        db.get.return_value = animal

        await validate_donation_target(db, "animal", animal_id)

    @pytest.mark.asyncio
    async def test_animal_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(InvalidTargetError, match="not found"):
            await validate_donation_target(db, "animal", uuid4())

    @pytest.mark.asyncio
    async def test_adopted_animal_rejected(self) -> None:
        db = _mock_db()
        animal = MagicMock()
        animal.status = "adopted"
        db.get.return_value = animal

        with pytest.raises(TargetNotActiveError, match="adopted"):
            await validate_donation_target(db, "animal", uuid4())


# --- Campaign Target Validation Tests ---


class TestCampaignTargetValidation:
    """Tests for campaign target validation."""

    @pytest.mark.asyncio
    async def test_valid_active_campaign(self) -> None:
        db = _mock_db()
        campaign_id = uuid4()
        campaign = MagicMock()
        campaign.status = "active"
        db.get.return_value = campaign

        await validate_donation_target(db, "campaign", campaign_id)

    @pytest.mark.asyncio
    async def test_campaign_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(InvalidTargetError, match="not found"):
            await validate_donation_target(db, "campaign", uuid4())

    @pytest.mark.asyncio
    async def test_inactive_campaign_rejected(self) -> None:
        db = _mock_db()
        campaign = MagicMock()
        campaign.status = "completed"
        db.get.return_value = campaign

        with pytest.raises(TargetNotActiveError, match="not active"):
            await validate_donation_target(db, "campaign", uuid4())


# --- Clinic Target Validation Tests ---


class TestClinicTargetValidation:
    """Tests for clinic target validation."""

    @pytest.mark.asyncio
    async def test_valid_active_clinic(self) -> None:
        db = _mock_db()
        clinic_id = uuid4()
        clinic = MagicMock()
        clinic.status = "active"
        db.get.return_value = clinic

        await validate_donation_target(db, "clinic", clinic_id)

    @pytest.mark.asyncio
    async def test_clinic_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(InvalidTargetError, match="not found"):
            await validate_donation_target(db, "clinic", uuid4())

    @pytest.mark.asyncio
    async def test_inactive_clinic_rejected(self) -> None:
        db = _mock_db()
        clinic = MagicMock()
        clinic.status = "suspended"
        db.get.return_value = clinic

        with pytest.raises(TargetNotActiveError, match="not active"):
            await validate_donation_target(db, "clinic", uuid4())


# --- Rescuer Target Validation Tests ---


class TestRescuerTargetValidation:
    """Tests for rescuer target validation."""

    @pytest.mark.asyncio
    async def test_valid_rescuer(self) -> None:
        db = _mock_db()
        user = MagicMock()
        db.get.return_value = user

        await validate_donation_target(db, "rescuer", uuid4())

    @pytest.mark.asyncio
    async def test_rescuer_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(InvalidTargetError, match="not found"):
            await validate_donation_target(db, "rescuer", uuid4())


# --- Need Target Validation Tests ---


class TestNeedTargetValidation:
    """Tests for need target validation (stub)."""

    @pytest.mark.asyncio
    async def test_need_accepted_as_stub(self) -> None:
        """Need validation is a stub — should accept any UUID."""
        db = _mock_db()
        await validate_donation_target(db, "need", uuid4())


# --- General Target Tests ---


class TestGeneralTargetValidation:
    """Tests for general (undirected) donation target."""

    @pytest.mark.asyncio
    async def test_general_passes(self) -> None:
        db = _mock_db()
        await validate_donation_target(db, "general", None)

    @pytest.mark.asyncio
    async def test_general_with_target_id_fails(self) -> None:
        db = _mock_db()
        with pytest.raises(InvalidTargetError, match="must be null"):
            await validate_donation_target(db, "general", uuid4())


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exception classes."""

    def test_invalid_target_error(self) -> None:
        tid = uuid4()
        error = InvalidTargetError("animal", tid, "not found")
        assert error.target_type == "animal"
        assert error.target_id == tid
        assert "not found" in error.message

    def test_target_not_active_error(self) -> None:
        tid = uuid4()
        error = TargetNotActiveError("campaign", tid, "not active")
        assert error.target_type == "campaign"
        assert error.target_id == tid
        assert "not active" in error.message


# --- Constants Tests ---


class TestConstants:
    """Tests for module constants."""

    def test_directed_target_types(self) -> None:
        assert DonationTargetType.ANIMAL in DIRECTED_TARGET_TYPES
        assert DonationTargetType.RESCUER in DIRECTED_TARGET_TYPES
        assert DonationTargetType.CLINIC in DIRECTED_TARGET_TYPES
        assert DonationTargetType.CAMPAIGN in DIRECTED_TARGET_TYPES
        assert DonationTargetType.NEED in DIRECTED_TARGET_TYPES
        assert DonationTargetType.GENERAL not in DIRECTED_TARGET_TYPES

    def test_target_type_enum_values(self) -> None:
        assert DonationTargetType.GENERAL == "general"
        assert DonationTargetType.ANIMAL == "animal"
        assert DonationTargetType.RESCUER == "rescuer"
        assert DonationTargetType.CLINIC == "clinic"
        assert DonationTargetType.CAMPAIGN == "campaign"
        assert DonationTargetType.NEED == "need"
        assert DonationTargetType.EMERGENCY == "emergency"
        assert len(DonationTargetType) == 7
