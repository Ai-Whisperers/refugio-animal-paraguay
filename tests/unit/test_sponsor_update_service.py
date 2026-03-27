"""Unit tests for the sponsor update service.

Tests cover:
  - Email HTML rendering helpers
  - publish_animal_update: persists record + returns notified count
  - _notify_immediate_sponsors: filters by preference, skips non-immediate
  - get_or_create_preference: creates defaults when absent, returns existing
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.db.models.animal_update import (
    AnimalUpdate,
    SponsorNotificationFrequency,
    SponsorUpdatePreference,
)
from src.services.sponsor_update_service import (
    _render_update_email,
    get_or_create_preference,
    publish_animal_update,
)

# ---------------------------------------------------------------------------
# _render_update_email
# ---------------------------------------------------------------------------


def test_render_update_email_basic() -> None:
    html = _render_update_email(
        animal_name="Luna",
        title="Health check",
        content="Luna is doing great!",
        milestone_type=None,
        photo_urls=[],
    )
    assert "Luna" in html
    assert "Health check" in html
    assert "Luna is doing great!" in html
    # No milestone block when milestone_type is None
    assert "Milestone:" not in html
    # No photo tags when photo_urls is empty
    assert "<img" not in html


def test_render_update_email_with_milestone() -> None:
    html = _render_update_email(
        animal_name="Rex",
        title="Vaccination",
        content="Rex received his annual vaccines.",
        milestone_type="vaccination",
        photo_urls=[],
    )
    assert "Milestone:" in html
    assert "Vaccination" in html  # title-cased


def test_render_update_email_milestone_underscores_become_spaces() -> None:
    html = _render_update_email(
        animal_name="Mia",
        title="Update",
        content="Content.",
        milestone_type="adoption_ready",
        photo_urls=[],
    )
    assert "Adoption Ready" in html


def test_render_update_email_with_photos() -> None:
    urls = ["https://example.com/a.jpg", "https://example.com/b.jpg"]
    html = _render_update_email(
        animal_name="Biscuit",
        title="Photos!",
        content="New photos.",
        milestone_type=None,
        photo_urls=urls,
    )
    assert html.count("<img") == 2
    assert "https://example.com/a.jpg" in html


def test_render_update_email_caps_photos_at_five() -> None:
    urls = [f"https://example.com/{i}.jpg" for i in range(10)]
    html = _render_update_email(
        animal_name="Spot",
        title="Many photos",
        content="Content.",
        milestone_type=None,
        photo_urls=urls,
    )
    assert html.count("<img") == 5


# ---------------------------------------------------------------------------
# publish_animal_update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_animal_update_persists_record_and_returns_notified() -> None:
    db = AsyncMock()
    email_service = MagicMock()
    email_service.is_enabled = True

    animal_id = uuid4()
    user_id = uuid4()

    update_obj = AnimalUpdate(
        id=uuid4(),
        animal_id=animal_id,
        published_by_user_id=user_id,
        title="Checkup",
        content="All good.",
        update_type="health",
        milestone_type=None,
        photo_urls=[],
    )

    with patch(
        "src.services.sponsor_update_service._notify_immediate_sponsors",
        new=AsyncMock(return_value=3),
    ):
        # Simulate db.add + flush populating the object
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        # Inject the update object into the service via side_effect on add
        captured = {}

        def capture_add(obj: object) -> None:
            if isinstance(obj, AnimalUpdate):
                captured["update"] = obj
                # Set the id as the service would expect after flush
                obj.id = update_obj.id

        db.add.side_effect = capture_add

        _record, notified = await publish_animal_update(
            db=db,
            email_service=email_service,
            animal_id=animal_id,
            title="Checkup",
            content="All good.",
            update_type="health",
            milestone_type=None,
            photo_urls=[],
            published_by_user_id=user_id,
            animal_name="Luna",
        )

    assert notified == 3
    db.add.assert_called_once()
    db.flush.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_publish_animal_update_skips_email_when_disabled() -> None:
    db = AsyncMock()
    email_service = MagicMock()
    email_service.is_enabled = False

    with patch(
        "src.services.sponsor_update_service._notify_immediate_sponsors",
        new=AsyncMock(return_value=0),
    ) as mock_notify:
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        _record, notified = await publish_animal_update(
            db=db,
            email_service=email_service,
            animal_id=uuid4(),
            title="T",
            content="C" * 10,
            update_type="general",
            milestone_type=None,
            photo_urls=[],
            published_by_user_id=None,
            animal_name="Sparky",
        )

    assert notified == 0
    mock_notify.assert_not_called()


# ---------------------------------------------------------------------------
# get_or_create_preference
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_preference_returns_existing() -> None:
    db = AsyncMock()
    sponsorship_id = uuid4()
    existing = SponsorUpdatePreference(
        id=uuid4(),
        sponsorship_id=sponsorship_id,
        notification_enabled=False,
        notification_frequency=SponsorNotificationFrequency.WEEKLY_DIGEST,
    )

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=result_mock)

    pref = await get_or_create_preference(db, sponsorship_id)

    assert pref is existing
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_preference_creates_defaults_when_absent() -> None:
    db = AsyncMock()
    sponsorship_id = uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.flush = AsyncMock()

    pref = await get_or_create_preference(db, sponsorship_id)

    assert pref.sponsorship_id == sponsorship_id
    assert pref.notification_enabled is True
    assert pref.notification_frequency == SponsorNotificationFrequency.IMMEDIATE
    db.add.assert_called_once_with(pref)
    db.flush.assert_called_once()
