"""Unit tests for foster-to-adopt conversion service (RAP-193)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.services.foster_conversion_service import (
    FosterConversionResult,
    convert_foster_to_adoption,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_placement(
    placement_id: UUID | None = None,
    foster_profile_id: UUID | None = None,
    animal_id: UUID | None = None,
    ended_at: datetime | None = None,
    notes: str | None = None,
) -> MagicMock:
    """Return a mock FosterPlacement with controllable fields."""
    p = MagicMock()
    p.id = placement_id or uuid4()
    p.foster_profile_id = foster_profile_id or uuid4()
    p.animal_id = animal_id or uuid4()
    p.ended_at = ended_at
    p.notes = notes
    return p


def _make_profile(profile_id: UUID | None = None, user_id: UUID | None = None) -> MagicMock:
    p = MagicMock()
    p.id = profile_id or uuid4()
    p.user_id = user_id or uuid4()
    return p


def _make_user(user_id: UUID | None = None, email: str = "foster@example.com") -> MagicMock:
    u = MagicMock()
    u.id = user_id or uuid4()
    u.email = email
    u.full_name = "Foster Family"
    u.phone = "+595 21 123456"
    return u


def _make_animal(animal_id: UUID | None = None) -> MagicMock:
    a = MagicMock()
    a.id = animal_id or uuid4()
    a.status = "foster"
    return a


def _make_adopter(adopter_id: UUID | None = None, email: str = "foster@example.com") -> MagicMock:
    a = MagicMock()
    a.id = adopter_id or uuid4()
    a.email = email
    return a


def _make_adoption_request(req_id: UUID | None = None) -> MagicMock:
    r = MagicMock()
    r.id = req_id or uuid4()
    return r


def _make_db_with_sequence(*scalar_returns: object | None) -> AsyncMock:
    """
    Return an AsyncMock session whose execute() calls return scalars in sequence.

    Each positional argument is what scalar_one_or_none() returns for that call.
    scalar_one_or_none() is a synchronous call on the query result, so we use
    MagicMock (not AsyncMock) for the result objects.
    """
    db = AsyncMock()

    execute_results = []
    for val in scalar_returns:
        # MagicMock so scalar_one_or_none() returns a value, not a coroutine
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = val
        execute_results.append(mock_result)

    # db.execute is awaited, so side_effect items are returned directly by AsyncMock
    db.execute.side_effect = execute_results
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_convert_raises_when_placement_not_found() -> None:
    """ValueError raised with 'not found' when placement does not exist."""
    db = _make_db_with_sequence(None)  # placement → None

    with pytest.raises(ValueError, match="not found"):
        await convert_foster_to_adoption(db, uuid4())


@pytest.mark.asyncio
async def test_convert_raises_when_placement_already_closed() -> None:
    """ValueError raised with 'already closed' when ended_at is set."""
    closed_placement = _make_placement(ended_at=datetime(2026, 1, 1, tzinfo=UTC))
    db = _make_db_with_sequence(closed_placement)

    with pytest.raises(ValueError, match="already closed"):
        await convert_foster_to_adoption(db, closed_placement.id)


@pytest.mark.asyncio
async def test_convert_raises_when_foster_profile_not_found() -> None:
    """ValueError raised when the foster profile is missing (data integrity)."""
    placement = _make_placement()
    db = _make_db_with_sequence(placement, None)  # placement found, profile None

    with pytest.raises(ValueError, match="Foster profile"):
        await convert_foster_to_adoption(db, placement.id)


@pytest.mark.asyncio
async def test_convert_raises_when_user_not_found() -> None:
    """ValueError raised when the linked user is missing (data integrity)."""
    placement = _make_placement()
    profile = _make_profile(profile_id=placement.foster_profile_id)
    db = _make_db_with_sequence(placement, profile, None)  # placement, profile, user None

    with pytest.raises(ValueError, match="User"):
        await convert_foster_to_adoption(db, placement.id)


@pytest.mark.asyncio
async def test_convert_success_with_existing_adopter() -> None:
    """Successful conversion when an adopter record already exists for the user's email."""
    placement = _make_placement()
    profile = _make_profile(profile_id=placement.foster_profile_id)
    user = _make_user(user_id=profile.user_id)
    adopter = _make_adopter(email=user.email)
    animal = _make_animal(animal_id=placement.animal_id)

    db = _make_db_with_sequence(placement, profile, user, adopter, animal)

    # Patch AdoptionRequest so we can control its .id
    mock_request = _make_adoption_request()
    with patch("src.services.foster_conversion_service.AdoptionRequest", return_value=mock_request):
        result = await convert_foster_to_adoption(db, placement.id, staff_notes="Happy family!")

    assert isinstance(result, FosterConversionResult)
    assert result.placement_id == placement.id
    assert result.adopter_id == adopter.id
    assert result.animal_id == placement.animal_id
    assert result.foster_profile_id == placement.foster_profile_id
    assert result.adopter_created is False
    # Placement should be closed
    assert placement.ended_at is not None
    # Animal status should be updated
    assert animal.status == "adopted"
    # DB commit should have been called
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_convert_success_auto_creates_adopter() -> None:
    """When no adopter exists for the user email, one is auto-created."""
    placement = _make_placement()
    profile = _make_profile(profile_id=placement.foster_profile_id)
    user = _make_user(user_id=profile.user_id, email="new_foster@example.com")
    animal = _make_animal(animal_id=placement.animal_id)

    # adopter lookup returns None → auto-create path
    # NOTE: do NOT patch Adopter here — select(Adopter) needs the real class
    db = _make_db_with_sequence(placement, profile, user, None, animal)

    mock_request = _make_adoption_request()
    with patch("src.services.foster_conversion_service.AdoptionRequest", return_value=mock_request):
        result = await convert_foster_to_adoption(db, placement.id)

    assert result.adopter_created is True
    # flush() must be awaited to "commit" the new adopter UUID before using it
    db.flush.assert_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_convert_appends_notes_to_placement() -> None:
    """Staff notes are appended to the existing placement notes field."""
    original_notes = "Animal is adjusting well."
    placement = _make_placement(notes=original_notes)
    profile = _make_profile(profile_id=placement.foster_profile_id)
    user = _make_user(user_id=profile.user_id)
    adopter = _make_adopter(email=user.email)
    animal = _make_animal(animal_id=placement.animal_id)

    db = _make_db_with_sequence(placement, profile, user, adopter, animal)
    mock_request = _make_adoption_request()

    with patch("src.services.foster_conversion_service.AdoptionRequest", return_value=mock_request):
        await convert_foster_to_adoption(db, placement.id, staff_notes="Family loves the dog!")

    assert "Family loves the dog!" in placement.notes
    assert original_notes in placement.notes


@pytest.mark.asyncio
async def test_convert_no_notes_does_not_alter_placement_notes() -> None:
    """When staff_notes is None, the placement notes field is not changed."""
    placement = _make_placement(notes="Original note.")
    profile = _make_profile(profile_id=placement.foster_profile_id)
    user = _make_user(user_id=profile.user_id)
    adopter = _make_adopter(email=user.email)
    animal = _make_animal(animal_id=placement.animal_id)

    db = _make_db_with_sequence(placement, profile, user, adopter, animal)
    mock_request = _make_adoption_request()

    with patch("src.services.foster_conversion_service.AdoptionRequest", return_value=mock_request):
        await convert_foster_to_adoption(db, placement.id, staff_notes=None)

    # Notes field should remain unchanged when no staff_notes are provided
    assert placement.notes == "Original note."
