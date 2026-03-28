"""Unit tests for shift API schemas (RAP-180)."""

from datetime import date, time

import pytest
from pydantic import ValidationError
from src.api.shifts import ShiftCreateRequest, ShiftUpdateRequest
from src.db.models.shift import ShiftRole, ShiftStatus


class TestShiftCreateRequest:
    def test_minimal_valid_payload(self) -> None:
        req = ShiftCreateRequest(
            shift_date=date(2026, 4, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        assert req.shift_date == date(2026, 4, 1)
        assert req.start_time == time(9, 0)
        assert req.end_time == time(12, 0)
        assert req.role == ShiftRole.GENERAL
        assert req.capacity == 1

    def test_full_valid_payload(self) -> None:
        req = ShiftCreateRequest(
            shift_date=date(2026, 4, 1),
            start_time=time(8, 0),
            end_time=time(16, 0),
            role=ShiftRole.ANIMAL_CARE,
            capacity=5,
            title="Morning animal care",
            notes="Bring gloves",
            location="Shelter Block A",
        )
        assert req.role == ShiftRole.ANIMAL_CARE
        assert req.capacity == 5
        assert req.title == "Morning animal care"
        assert req.location == "Shelter Block A"

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_time must be after start_time"):
            ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(14, 0),
                end_time=time(9, 0),
            )

    def test_end_equal_start_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_time must be after start_time"):
            ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
                end_time=time(9, 0),
            )

    def test_capacity_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                capacity=0,
            )

    def test_capacity_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                capacity=51,
            )

    def test_capacity_at_maximum_is_valid(self) -> None:
        req = ShiftCreateRequest(
            shift_date=date(2026, 4, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=50,
        )
        assert req.capacity == 50

    def test_missing_date_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(  # type: ignore[call-arg]
                start_time=time(9, 0),
                end_time=time(12, 0),
            )

    def test_missing_start_time_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(  # type: ignore[call-arg]
                shift_date=date(2026, 4, 1),
                end_time=time(12, 0),
            )

    def test_missing_end_time_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(  # type: ignore[call-arg]
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
            )

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                title="x" * 201,
            )

    def test_all_valid_roles(self) -> None:
        for role in ShiftRole:
            req = ShiftCreateRequest(
                shift_date=date(2026, 4, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                role=role,
            )
            assert req.role == role


class TestShiftUpdateRequest:
    def test_empty_update_is_valid(self) -> None:
        req = ShiftUpdateRequest()
        assert req.shift_date is None
        assert req.capacity is None

    def test_partial_update_with_valid_data(self) -> None:
        req = ShiftUpdateRequest(capacity=10, title="Updated title")
        assert req.capacity == 10
        assert req.title == "Updated title"

    def test_status_update_to_completed(self) -> None:
        req = ShiftUpdateRequest(status=ShiftStatus.COMPLETED)
        assert req.status == ShiftStatus.COMPLETED

    def test_end_before_start_when_both_provided_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_time must be after start_time"):
            ShiftUpdateRequest(
                start_time=time(14, 0),
                end_time=time(9, 0),
            )

    def test_only_start_time_no_validation_error(self) -> None:
        # Only one of start/end provided — no cross-validation needed
        req = ShiftUpdateRequest(start_time=time(10, 0))
        assert req.start_time == time(10, 0)
        assert req.end_time is None

    def test_capacity_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            ShiftUpdateRequest(capacity=0)


class TestShiftModelConstants:
    def test_shift_status_values(self) -> None:
        assert ShiftStatus.OPEN == "open"
        assert ShiftStatus.FULL == "full"
        assert ShiftStatus.CANCELLED == "cancelled"
        assert ShiftStatus.COMPLETED == "completed"

    def test_shift_role_values(self) -> None:
        assert ShiftRole.ANIMAL_CARE == "animal_care"
        assert ShiftRole.GENERAL == "general"
        assert ShiftRole.CLEANING == "cleaning"
