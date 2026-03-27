"""Unit tests for vet referral schemas."""

import uuid

import pytest
from pydantic import ValidationError
from src.db.models.vet_referral import ReferralStatus, ReferralUrgency
from src.schemas.vet_referral import VetReferralCreate, VetReferralUpdate


class TestReferralEnums:
    """Tests for referral status and urgency enums."""

    def test_referral_status_values(self) -> None:
        expected = {"pending", "scheduled", "in_progress", "completed", "cancelled"}
        assert {s.value for s in ReferralStatus} == expected

    def test_referral_urgency_values(self) -> None:
        expected = {"low", "medium", "high", "emergency"}
        assert {u.value for u in ReferralUrgency} == expected


class TestVetReferralCreate:
    """Tests for VetReferralCreate schema validation."""

    def test_valid_minimal_create(self) -> None:
        data = VetReferralCreate(
            animal_id=uuid.uuid4(),
            external_vet_name="Dr. Garcia",
            reason="Orthopedic specialist consultation",
        )
        assert data.urgency == ReferralUrgency.MEDIUM
        assert data.external_vet_clinic is None

    def test_valid_full_create(self) -> None:
        data = VetReferralCreate(
            animal_id=uuid.uuid4(),
            external_vet_name="Dr. Rodriguez",
            external_vet_clinic="Clinica Veterinaria Asuncion",
            external_vet_phone="+595 21 123456",
            external_vet_email="dr.rodriguez@example.com",
            reason="Cardiac evaluation needed",
            specialty="Cardiology",
            urgency=ReferralUrgency.HIGH,
            estimated_cost=250000.00,
        )
        assert data.specialty == "Cardiology"
        assert data.urgency == ReferralUrgency.HIGH

    def test_empty_vet_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VetReferralCreate(
                animal_id=uuid.uuid4(),
                external_vet_name="",
                reason="Need specialist",
            )

    def test_empty_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VetReferralCreate(
                animal_id=uuid.uuid4(),
                external_vet_name="Dr. Test",
                reason="",
            )

    def test_negative_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VetReferralCreate(
                animal_id=uuid.uuid4(),
                external_vet_name="Dr. Test",
                reason="Checkup",
                estimated_cost=-100.0,
            )

    def test_excessive_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VetReferralCreate(
                animal_id=uuid.uuid4(),
                external_vet_name="Dr. Test",
                reason="Checkup",
                estimated_cost=1000000.00,
            )

    def test_vet_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            VetReferralCreate(
                animal_id=uuid.uuid4(),
                external_vet_name="A" * 256,
                reason="Checkup",
            )


class TestVetReferralUpdate:
    """Tests for VetReferralUpdate schema validation."""

    def test_partial_update(self) -> None:
        data = VetReferralUpdate(status=ReferralStatus.COMPLETED, diagnosis="Healthy")
        updates = data.model_dump(exclude_unset=True)
        assert updates == {"status": ReferralStatus.COMPLETED, "diagnosis": "Healthy"}

    def test_empty_update_valid(self) -> None:
        data = VetReferralUpdate()
        updates = data.model_dump(exclude_unset=True)
        assert updates == {}

    def test_update_with_cost(self) -> None:
        data = VetReferralUpdate(actual_cost=150000.00)
        assert data.actual_cost == 150000.00

    def test_update_follow_up(self) -> None:
        data = VetReferralUpdate(follow_up_required=True)
        assert data.follow_up_required is True
