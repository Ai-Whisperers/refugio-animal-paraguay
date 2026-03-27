"""Unit tests for animal status transition validation."""

import pytest

from src.services.animal_status import (
    InvalidStatusTransitionError,
    get_valid_transitions,
    validate_status_transition,
)


class TestValidateStatusTransition:
    """Tests for validate_status_transition."""

    def test_same_status_is_always_valid(self) -> None:
        """No-op transition (same status) should not raise."""
        validate_status_transition("intake", "intake")
        validate_status_transition("adopted", "adopted")
        validate_status_transition("deceased", "deceased")

    def test_intake_to_quarantine_is_valid(self) -> None:
        validate_status_transition("intake", "quarantine")

    def test_intake_to_available_is_valid(self) -> None:
        validate_status_transition("intake", "available")

    def test_intake_to_under_treatment_is_valid(self) -> None:
        validate_status_transition("intake", "under_treatment")

    def test_intake_to_adopted_is_invalid(self) -> None:
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            validate_status_transition("intake", "adopted")
        assert "intake" in str(exc_info.value)
        assert "adopted" in str(exc_info.value)

    def test_available_to_adopted_is_valid(self) -> None:
        validate_status_transition("available", "adopted")

    def test_available_to_foster_is_valid(self) -> None:
        validate_status_transition("available", "foster")

    def test_foster_to_adopted_is_valid(self) -> None:
        validate_status_transition("foster", "adopted")

    def test_foster_to_available_is_valid(self) -> None:
        """Foster return to available (foster ended)."""
        validate_status_transition("foster", "available")

    def test_adopted_to_available_is_valid(self) -> None:
        """Animal returned after adoption."""
        validate_status_transition("adopted", "available")

    def test_adopted_to_foster_is_invalid(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("adopted", "foster")

    def test_deceased_is_terminal(self) -> None:
        """Deceased animals cannot transition to any other state."""
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("deceased", "available")

    def test_deceased_to_intake_is_invalid(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("deceased", "intake")

    def test_quarantine_to_available_is_valid(self) -> None:
        validate_status_transition("quarantine", "available")

    def test_under_treatment_to_available_is_valid(self) -> None:
        validate_status_transition("under_treatment", "available")

    def test_under_treatment_to_deceased_is_valid(self) -> None:
        validate_status_transition("under_treatment", "deceased")

    def test_unknown_current_status_raises(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("unknown_status", "available")


class TestGetValidTransitions:
    """Tests for get_valid_transitions."""

    def test_intake_transitions(self) -> None:
        result = get_valid_transitions("intake")
        assert "quarantine" in result
        assert "available" in result
        assert "under_treatment" in result
        assert "adopted" not in result

    def test_deceased_has_no_transitions(self) -> None:
        result = get_valid_transitions("deceased")
        assert result == []

    def test_adopted_can_return(self) -> None:
        result = get_valid_transitions("adopted")
        assert result == ["available"]

    def test_unknown_status_returns_empty(self) -> None:
        result = get_valid_transitions("nonexistent")
        assert result == []

    def test_available_has_most_transitions(self) -> None:
        result = get_valid_transitions("available")
        assert len(result) >= 4
        assert "foster" in result
        assert "adopted" in result


class TestInvalidStatusTransitionError:
    """Tests for error message formatting."""

    def test_error_message_contains_both_statuses(self) -> None:
        error = InvalidStatusTransitionError("intake", "adopted")
        assert "intake" in str(error)
        assert "adopted" in str(error)

    def test_terminal_status_error_message(self) -> None:
        error = InvalidStatusTransitionError("deceased", "available")
        assert "ninguno" in str(error)
