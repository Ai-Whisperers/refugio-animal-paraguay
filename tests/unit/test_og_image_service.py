"""Unit tests for OG image generation service."""

import io

import pytest
from PIL import Image
from src.services.og_image_service import (
    OG_HEIGHT,
    OG_WIDTH,
    VALID_CARD_TYPES,
    CardData,
    InvalidCardTypeError,
    OGImageError,
    generate_og_image,
    generate_placeholder,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _png_to_image(png_bytes: bytes) -> Image.Image:
    """Convert PNG bytes to a PIL Image for inspection."""
    return Image.open(io.BytesIO(png_bytes))


# ---------------------------------------------------------------------------
# Card type validation
# ---------------------------------------------------------------------------


class TestCardTypeValidation:
    """Tests for card type validation."""

    def test_valid_types(self) -> None:
        assert "animal" in VALID_CARD_TYPES
        assert "campaign" in VALID_CARD_TYPES
        assert "story" in VALID_CARD_TYPES
        assert "blog" in VALID_CARD_TYPES

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(InvalidCardTypeError):
            generate_og_image("invalid", CardData(title="Test"))

    def test_empty_type_raises(self) -> None:
        with pytest.raises(InvalidCardTypeError):
            generate_og_image("", CardData(title="Test"))


# ---------------------------------------------------------------------------
# Animal card
# ---------------------------------------------------------------------------


class TestAnimalCard:
    """Tests for animal card generation."""

    def test_generates_png_bytes(self) -> None:
        data = CardData(title="Luna", subtitle="Dog - Golden Retriever", cta_text="Adoptame!")
        result = generate_og_image("animal", data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_correct_dimensions(self) -> None:
        data = CardData(title="Luna")
        result = generate_og_image("animal", data)
        img = _png_to_image(result)
        assert img.size == (OG_WIDTH, OG_HEIGHT)

    def test_is_valid_png(self) -> None:
        data = CardData(title="Luna")
        result = generate_og_image("animal", data)
        img = _png_to_image(result)
        assert img.format == "PNG"

    def test_handles_long_title(self) -> None:
        data = CardData(title="A" * 100)
        result = generate_og_image("animal", data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_handles_empty_title(self) -> None:
        data = CardData(title="")
        result = generate_og_image("animal", data)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Campaign card
# ---------------------------------------------------------------------------


class TestCampaignCard:
    """Tests for campaign card generation."""

    def test_generates_png(self) -> None:
        data = CardData(
            title="Save the Shelter",
            subtitle="Help us build a new wing",
            cta_text="Donate!",
            progress_pct=65.5,
            progress_text="$6,550 / $10,000 (65%)",
        )
        result = generate_og_image("campaign", data)
        img = _png_to_image(result)
        assert img.size == (OG_WIDTH, OG_HEIGHT)

    def test_zero_progress(self) -> None:
        data = CardData(title="New Campaign", progress_pct=0.0)
        result = generate_og_image("campaign", data)
        assert isinstance(result, bytes)

    def test_full_progress(self) -> None:
        data = CardData(title="Funded!", progress_pct=100.0)
        result = generate_og_image("campaign", data)
        assert isinstance(result, bytes)

    def test_over_100_progress_capped(self) -> None:
        data = CardData(title="Overfunded", progress_pct=150.0)
        result = generate_og_image("campaign", data)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Story card
# ---------------------------------------------------------------------------


class TestStoryCard:
    """Tests for story card generation."""

    def test_generates_png(self) -> None:
        data = CardData(
            title="Happy Ending for Luna",
            subtitle="Luna found her forever home",
            cta_text="Read Story",
        )
        result = generate_og_image("story", data)
        img = _png_to_image(result)
        assert img.size == (OG_WIDTH, OG_HEIGHT)

    def test_without_subtitle(self) -> None:
        data = CardData(title="Story Title")
        result = generate_og_image("story", data)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Blog card
# ---------------------------------------------------------------------------


class TestBlogCard:
    """Tests for blog card generation."""

    def test_generates_png(self) -> None:
        data = CardData(
            title="Understanding Animal Welfare in Paraguay",
            author="Ivan Weiss",
            date_text="March 27, 2026",
        )
        result = generate_og_image("blog", data)
        img = _png_to_image(result)
        assert img.size == (OG_WIDTH, OG_HEIGHT)

    def test_without_author(self) -> None:
        data = CardData(title="Blog Post")
        result = generate_og_image("blog", data)
        assert isinstance(result, bytes)

    def test_with_only_date(self) -> None:
        data = CardData(title="Blog Post", date_text="2026-03-27")
        result = generate_og_image("blog", data)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Placeholder
# ---------------------------------------------------------------------------


class TestPlaceholder:
    """Tests for placeholder image generation."""

    def test_generates_png(self) -> None:
        result = generate_placeholder()
        img = _png_to_image(result)
        assert img.size == (OG_WIDTH, OG_HEIGHT)
        assert img.format == "PNG"

    def test_returns_bytes(self) -> None:
        result = generate_placeholder()
        assert isinstance(result, bytes)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling in generate_og_image."""

    def test_og_image_error_attributes(self) -> None:
        err = OGImageError("test error", details="detail")
        assert err.message == "test error"
        assert err.details == "detail"

    def test_invalid_card_type_error_attributes(self) -> None:
        err = InvalidCardTypeError("bad")
        assert err.message == "Invalid card type"
        assert "animal" in err.details
