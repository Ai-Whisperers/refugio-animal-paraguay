"""Unit tests for animal update Pydantic schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.animal_update import (
    AnimalUpdateCreate,
    AnimalUpdateResponse,
    SponsorUpdatePreferenceResponse,
    SponsorUpdatePreferenceUpdate,
)

# ---------------------------------------------------------------------------
# AnimalUpdateCreate
# ---------------------------------------------------------------------------


def test_animal_update_create_defaults() -> None:
    payload = AnimalUpdateCreate(
        animal_id=uuid4(),
        title="Luna is healthy",
        content="All vaccinations are up to date.",
    )
    assert payload.update_type == "general"
    assert payload.milestone_type is None
    assert payload.photo_urls == []


def test_animal_update_create_requires_title_min_length() -> None:
    with pytest.raises(ValidationError):
        AnimalUpdateCreate(
            animal_id=uuid4(),
            title="ab",  # too short (min 3)
            content="Content is long enough.",
        )


def test_animal_update_create_requires_content_min_length() -> None:
    with pytest.raises(ValidationError):
        AnimalUpdateCreate(
            animal_id=uuid4(),
            title="Valid title",
            content="Too short",  # < 10 chars
        )


def test_animal_update_create_milestone_type_optional() -> None:
    payload = AnimalUpdateCreate(
        animal_id=uuid4(),
        title="Vaccination done",
        content="Annual vaccines administered today.",
        update_type="milestone",
        milestone_type="vaccination",
    )
    assert payload.milestone_type == "vaccination"
    assert payload.update_type == "milestone"


def test_animal_update_create_photo_urls_list() -> None:
    urls = ["https://example.com/a.jpg", "https://example.com/b.jpg"]
    payload = AnimalUpdateCreate(
        animal_id=uuid4(),
        title="Photo update",
        content="New photos attached.",
        photo_urls=urls,
    )
    assert payload.photo_urls == urls


# ---------------------------------------------------------------------------
# AnimalUpdateResponse
# ---------------------------------------------------------------------------


def test_animal_update_response_sponsors_notified_defaults_zero() -> None:
    resp = AnimalUpdateResponse(
        id=uuid4(),
        animal_id=uuid4(),
        published_by_user_id=None,
        title="Test",
        content="Content",
        update_type="general",
        milestone_type=None,
        photo_urls=[],
        published_at=datetime.now(tz=UTC),
    )
    assert resp.sponsors_notified == 0


def test_animal_update_response_from_orm_attributes() -> None:
    """Verify model_config from_attributes allows ORM-style construction."""
    now = datetime.now(tz=UTC)
    uid = uuid4()
    aid = uuid4()

    resp = AnimalUpdateResponse.model_validate(
        {
            "id": uid,
            "animal_id": aid,
            "published_by_user_id": None,
            "title": "Health check",
            "content": "All clear",
            "update_type": "health",
            "milestone_type": None,
            "photo_urls": [],
            "published_at": now,
        }
    )
    assert resp.id == uid
    assert resp.animal_id == aid


# ---------------------------------------------------------------------------
# SponsorUpdatePreferenceUpdate
# ---------------------------------------------------------------------------


def test_preference_update_defaults() -> None:
    pref = SponsorUpdatePreferenceUpdate()
    assert pref.notification_enabled is True
    assert pref.notification_frequency == "immediate"


def test_preference_update_custom_values() -> None:
    pref = SponsorUpdatePreferenceUpdate(
        notification_enabled=False,
        notification_frequency="weekly_digest",
    )
    assert pref.notification_enabled is False
    assert pref.notification_frequency == "weekly_digest"


# ---------------------------------------------------------------------------
# SponsorUpdatePreferenceResponse
# ---------------------------------------------------------------------------


def test_preference_response_round_trips() -> None:
    sid = uuid4()
    pid = uuid4()
    resp = SponsorUpdatePreferenceResponse(
        id=pid,
        sponsorship_id=sid,
        notification_enabled=True,
        notification_frequency="daily_digest",
    )
    assert resp.sponsorship_id == sid
    assert resp.notification_frequency == "daily_digest"
