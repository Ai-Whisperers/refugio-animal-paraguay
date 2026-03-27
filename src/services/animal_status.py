"""Animal status transition validation.

Defines the valid state transitions for animals in the shelter lifecycle
and provides validation functions used by the API layer.
"""

from src.db.models.animal import AnimalStatus

# Map of current status to list of valid next statuses.
VALID_TRANSITIONS: dict[str, list[str]] = {
    AnimalStatus.INTAKE: [
        AnimalStatus.QUARANTINE,
        AnimalStatus.AVAILABLE,
        AnimalStatus.UNDER_TREATMENT,
    ],
    AnimalStatus.QUARANTINE: [
        AnimalStatus.AVAILABLE,
        AnimalStatus.UNDER_TREATMENT,
        AnimalStatus.DECEASED,
    ],
    AnimalStatus.AVAILABLE: [
        AnimalStatus.FOSTER,
        AnimalStatus.ADOPTED,
        AnimalStatus.UNDER_TREATMENT,
        AnimalStatus.QUARANTINE,
        AnimalStatus.DECEASED,
    ],
    AnimalStatus.FOSTER: [
        AnimalStatus.AVAILABLE,
        AnimalStatus.ADOPTED,
        AnimalStatus.UNDER_TREATMENT,
        AnimalStatus.DECEASED,
    ],
    AnimalStatus.UNDER_TREATMENT: [
        AnimalStatus.AVAILABLE,
        AnimalStatus.QUARANTINE,
        AnimalStatus.FOSTER,
        AnimalStatus.DECEASED,
    ],
    AnimalStatus.ADOPTED: [
        AnimalStatus.AVAILABLE,  # returned animal
    ],
    AnimalStatus.DECEASED: [],  # terminal state
}


class InvalidStatusTransitionError(Exception):
    """Raised when an animal status transition is not allowed."""

    def __init__(self, current_status: str, requested_status: str) -> None:
        self.current_status = current_status
        self.requested_status = requested_status
        valid = VALID_TRANSITIONS.get(current_status, [])
        valid_labels = ", ".join(valid) if valid else "ninguno (estado terminal)"
        super().__init__(
            f"Transicion de estado invalida: {current_status} -> {requested_status}. "
            f"Transiciones validas desde {current_status}: {valid_labels}"
        )


def validate_status_transition(current_status: str, new_status: str) -> None:
    """Validate that transitioning from current_status to new_status is allowed.

    Raises InvalidStatusTransitionError if the transition is not valid.
    Does nothing if the status is unchanged.
    """
    if current_status == new_status:
        return

    valid_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in valid_next:
        raise InvalidStatusTransitionError(current_status, new_status)


def get_valid_transitions(current_status: str) -> list[str]:
    """Return the list of valid next statuses for the given current status."""
    return VALID_TRANSITIONS.get(current_status, [])
