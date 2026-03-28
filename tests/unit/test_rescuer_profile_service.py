"""Unit tests for rescuer profile service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.rescuer_profile_service import (
    MAX_BIO_LENGTH,
    MAX_DISPLAY_NAME_LENGTH,
    MIN_DISPLAY_NAME_LENGTH,
    PARAGUAY_PHONE_PATTERN,
    DisplayNameTakenError,
    RescuerProfileError,
    RescuerProfileExistsError,
    RescuerProfileNotFoundError,
    generate_slug,
    get_rescuer_by_slug,
    register_rescuer,
    validate_bio,
    validate_contact_method,
    validate_display_name,
    validate_phone,
)

# ---------------------------------------------------------------------------
# generate_slug tests
# ---------------------------------------------------------------------------


class TestGenerateSlug:
    """Tests for slug generation from display names."""

    def test_basic_slug(self) -> None:
        assert generate_slug("Maria Gomez") == "maria-gomez"

    def test_strips_accents(self) -> None:
        assert generate_slug("José García") == "jose-garcia"

    def test_replaces_special_chars(self) -> None:
        assert generate_slug("Ana & Pedro!") == "ana-pedro"

    def test_strips_leading_trailing_hyphens(self) -> None:
        assert generate_slug("  Hello World  ") == "hello-world"

    def test_empty_name_returns_rescuer(self) -> None:
        assert generate_slug("---") == "rescuer"

    def test_unicode_normalization(self) -> None:
        slug = generate_slug("Ñoño Pérez")
        assert "n" in slug  # ñ becomes n
        assert "e" in slug  # é becomes e

    def test_truncates_long_names(self) -> None:
        long_name = "A" * 200
        slug = generate_slug(long_name)
        assert len(slug) <= 120


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidateDisplayName:
    """Tests for display name validation."""

    def test_accepts_valid_name(self) -> None:
        validate_display_name("Maria Gomez")

    def test_rejects_too_short(self) -> None:
        with pytest.raises(RescuerProfileError, match="too short"):
            validate_display_name("A")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(RescuerProfileError, match="too long"):
            validate_display_name("A" * 101)

    def test_accepts_min_length(self) -> None:
        validate_display_name("Ab")

    def test_accepts_max_length(self) -> None:
        validate_display_name("A" * 100)


class TestValidateBio:
    """Tests for bio validation."""

    def test_accepts_none(self) -> None:
        validate_bio(None)

    def test_accepts_valid_bio(self) -> None:
        validate_bio("I rescue animals in Asuncion.")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(RescuerProfileError, match="Bio too long"):
            validate_bio("A" * 1001)

    def test_accepts_max_length(self) -> None:
        validate_bio("A" * 1000)


class TestValidatePhone:
    """Tests for Paraguay phone format validation."""

    def test_accepts_valid_phone(self) -> None:
        validate_phone("+595981123456")

    def test_accepts_none(self) -> None:
        validate_phone(None)

    def test_rejects_invalid_format(self) -> None:
        with pytest.raises(RescuerProfileError, match="Invalid phone"):
            validate_phone("12345")

    def test_rejects_non_595(self) -> None:
        with pytest.raises(RescuerProfileError, match="Invalid phone"):
            validate_phone("+1234567890")

    def test_pattern_matches(self) -> None:
        assert PARAGUAY_PHONE_PATTERN.match("+595981123456")
        assert PARAGUAY_PHONE_PATTERN.match("+5959811234567")
        assert not PARAGUAY_PHONE_PATTERN.match("+595")
        assert not PARAGUAY_PHONE_PATTERN.match("595981123456")


class TestValidateContactMethod:
    """Tests for contact method requirement."""

    def test_accepts_phone_only(self) -> None:
        validate_contact_method("+595981123456", None)

    def test_accepts_social_only(self) -> None:
        validate_contact_method(None, {"facebook": "https://fb.com/rescuer"})

    def test_accepts_both(self) -> None:
        validate_contact_method("+595981123456", {"instagram": "@rescuer"})

    def test_rejects_neither(self) -> None:
        with pytest.raises(RescuerProfileError, match="Contact method"):
            validate_contact_method(None, None)

    def test_rejects_empty_social_links(self) -> None:
        with pytest.raises(RescuerProfileError, match="Contact method"):
            validate_contact_method(None, {})

    def test_rejects_social_links_all_empty(self) -> None:
        with pytest.raises(RescuerProfileError, match="Contact method"):
            validate_contact_method(None, {"facebook": "", "instagram": ""})


# ---------------------------------------------------------------------------
# register_rescuer tests
# ---------------------------------------------------------------------------


def _mock_db_no_profile() -> AsyncMock:
    """Mock DB: no existing profile, no slug conflict."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    return db


def _mock_db_with_profile() -> AsyncMock:
    """Mock DB: existing profile found."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = uuid4()
    db.execute.return_value = mock_result
    return db


class TestRegisterRescuer:
    """Tests for rescuer registration."""

    @pytest.mark.asyncio
    async def test_successful_registration(self) -> None:
        db = _mock_db_no_profile()
        profile = await register_rescuer(
            user_id=uuid4(),
            display_name="Maria Gomez",
            phone_whatsapp="+595981123456",
            db=db,
        )
        assert profile.display_name == "Maria Gomez"
        assert profile.slug == "maria-gomez"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_existing_profile(self) -> None:
        db = _mock_db_with_profile()
        with pytest.raises(RescuerProfileExistsError):
            await register_rescuer(
                user_id=uuid4(),
                display_name="Maria Gomez",
                phone_whatsapp="+595981123456",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_no_contact(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerProfileError, match="Contact method"):
            await register_rescuer(
                user_id=uuid4(),
                display_name="Maria Gomez",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_invalid_phone(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerProfileError, match="Invalid phone"):
            await register_rescuer(
                user_id=uuid4(),
                display_name="Maria Gomez",
                phone_whatsapp="bad-number",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_sets_optional_fields(self) -> None:
        db = _mock_db_no_profile()
        profile = await register_rescuer(
            user_id=uuid4(),
            display_name="Pedro Lopez",
            bio="I love animals",
            location_city="Asuncion",
            location_coords={"lat": -25.2637, "lng": -57.5759},
            social_links={"instagram": "@pedro_rescuer"},
            phone_whatsapp="+595981999888",
            db=db,
        )
        assert profile.bio == "I love animals"
        assert profile.location_city == "Asuncion"
        assert profile.social_links == {"instagram": "@pedro_rescuer"}


# ---------------------------------------------------------------------------
# get_rescuer_by_slug tests
# ---------------------------------------------------------------------------


class TestGetRescuerBySlug:
    """Tests for slug-based profile lookup."""

    @pytest.mark.asyncio
    async def test_returns_profile(self) -> None:
        db = AsyncMock()
        mock_profile = MagicMock()
        mock_profile.slug = "maria-gomez"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        db.execute.return_value = mock_result

        result = await get_rescuer_by_slug("maria-gomez", db)
        assert result.slug == "maria-gomez"

    @pytest.mark.asyncio
    async def test_raises_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(RescuerProfileNotFoundError):
            await get_rescuer_by_slug("nonexistent", db)


# ---------------------------------------------------------------------------
# Error class tests
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for custom exception classes."""

    def test_profile_error(self) -> None:
        err = RescuerProfileError("bad", details="detail")
        assert err.message == "bad"
        assert err.details == "detail"

    def test_exists_error(self) -> None:
        uid = uuid4()
        err = RescuerProfileExistsError(uid)
        assert err.user_id == uid

    def test_not_found_error(self) -> None:
        err = RescuerProfileNotFoundError("slug-here")
        assert err.identifier == "slug-here"

    def test_display_name_taken_error(self) -> None:
        err = DisplayNameTakenError("Maria")
        assert err.display_name == "Maria"


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_min_display_name(self) -> None:
        assert MIN_DISPLAY_NAME_LENGTH == 2

    def test_max_display_name(self) -> None:
        assert MAX_DISPLAY_NAME_LENGTH == 100

    def test_max_bio(self) -> None:
        assert MAX_BIO_LENGTH == 1000
