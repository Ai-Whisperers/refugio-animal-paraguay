"""Open Graph image generation service.

Generates 1200x630 PNG cards for social media unfurling. Supports animal,
campaign, story, and blog card types with Refugio branding.
"""

import io
import logging
from enum import StrEnum
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OG_WIDTH = 1200
OG_HEIGHT = 630

# Colours (RGB)
COLOR_PRIMARY = (46, 125, 50)  # Refugio green
COLOR_DARK = (33, 33, 33)
COLOR_WHITE = (255, 255, 255)
COLOR_OVERLAY = (0, 0, 0, 160)  # Semi-transparent black for text backing
COLOR_PROGRESS_BG = (200, 200, 200)
COLOR_PROGRESS_FILL = (76, 175, 80)

# Font sizes (points)
FONT_TITLE = 48
FONT_SUBTITLE = 32
FONT_CTA = 36
FONT_BODY = 28
FONT_SMALL = 22

# Layout
PADDING = 40
CTA_HEIGHT = 60
LOGO_TEXT = "Refugio Animal Paraguay"


class OGCardType(StrEnum):
    """Supported card types."""

    ANIMAL = "animal"
    CAMPAIGN = "campaign"
    CASTRATION_CAMPAIGN = "castration-campaign"
    STORY = "story"
    BLOG = "blog"


VALID_CARD_TYPES = frozenset({t.value for t in OGCardType})


class CardData(NamedTuple):
    """Data needed to generate a card."""

    title: str
    subtitle: str | None = None
    cta_text: str | None = None
    progress_pct: float | None = None
    progress_text: str | None = None
    author: str | None = None
    date_text: str | None = None


class OGImageError(Exception):
    """Error during OG image generation."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidCardTypeError(OGImageError):
    """Raised for unsupported card type."""

    def __init__(self, card_type: str) -> None:
        super().__init__(
            message="Invalid card type",
            details=f"Must be one of: {', '.join(sorted(VALID_CARD_TYPES))}",
        )


# ---------------------------------------------------------------------------
# Font loading (system fallback)
# ---------------------------------------------------------------------------


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font, falling back to Pillow default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    # Fallback to default bitmap font
    return ImageFont.load_default()


def _load_regular_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a regular-weight TrueType font."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, ...] = COLOR_WHITE,
    shadow_offset: int = 2,
) -> None:
    """Draw text with a dark shadow for legibility on images."""
    x, y = position
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=COLOR_DARK)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_overlay_bar(
    img: Image.Image,
    y_start: int,
    height: int,
) -> None:
    """Draw a semi-transparent bar across the image."""
    overlay = Image.new("RGBA", (OG_WIDTH, height), COLOR_OVERLAY)
    img.paste(overlay, (0, y_start), overlay)


def _draw_progress_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
    progress_pct: float,
) -> None:
    """Draw a progress bar."""
    # Background
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=height // 2,
        fill=COLOR_PROGRESS_BG,
    )
    # Fill
    fill_width = max(int(width * min(progress_pct, 100.0) / 100.0), height)
    draw.rounded_rectangle(
        [x, y, x + fill_width, y + height],
        radius=height // 2,
        fill=COLOR_PROGRESS_FILL,
    )


def _truncate_text(text: str, max_chars: int = 60) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


# ---------------------------------------------------------------------------
# Card generators
# ---------------------------------------------------------------------------


def _generate_base_image() -> Image.Image:
    """Create a base RGBA image with the Refugio gradient background."""
    img = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)
    # Gradient effect: darker at bottom
    for y in range(OG_HEIGHT):
        alpha = int(y / OG_HEIGHT * 80)
        draw.line([(0, y), (OG_WIDTH, y)], fill=(0, 0, 0, alpha))
    return img


def generate_animal_card(data: CardData) -> bytes:
    """Generate an animal adoption card.

    Shows animal name, 'Adoptame!' CTA, and Refugio branding.
    """
    img = _generate_base_image()
    draw = ImageDraw.Draw(img)

    title_font = _load_font(FONT_TITLE)
    cta_font = _load_font(FONT_CTA)
    small_font = _load_regular_font(FONT_SMALL)

    # Overlay bar for title area
    _draw_overlay_bar(img, OG_HEIGHT - 200, 200)
    draw = ImageDraw.Draw(img)  # Refresh draw after paste

    # Animal name
    title = _truncate_text(data.title, 40)
    _draw_text_with_shadow(draw, (PADDING, OG_HEIGHT - 180), title, title_font)

    # CTA
    cta = data.cta_text or "Adoptame!"
    _draw_text_with_shadow(draw, (PADDING, OG_HEIGHT - 110), cta, cta_font, fill=(255, 235, 59))

    # Logo
    draw.text(
        (PADDING, PADDING),
        LOGO_TEXT,
        font=small_font,
        fill=COLOR_WHITE,
    )

    return _image_to_png(img)


def generate_campaign_card(data: CardData) -> bytes:
    """Generate a campaign card with progress bar."""
    img = _generate_base_image()
    draw = ImageDraw.Draw(img)

    title_font = _load_font(FONT_TITLE)
    subtitle_font = _load_regular_font(FONT_SUBTITLE)
    cta_font = _load_font(FONT_CTA)
    small_font = _load_regular_font(FONT_SMALL)

    # Logo
    draw.text((PADDING, PADDING), LOGO_TEXT, font=small_font, fill=COLOR_WHITE)

    # Title
    title = _truncate_text(data.title, 40)
    _draw_text_with_shadow(draw, (PADDING, 120), title, title_font)

    # Progress bar
    progress_pct = data.progress_pct or 0.0
    _draw_progress_bar(draw, PADDING, 250, OG_WIDTH - 2 * PADDING, 30, progress_pct)

    # Progress text
    progress_text = data.progress_text or f"{progress_pct:.0f}%"
    draw.text((PADDING, 290), progress_text, font=subtitle_font, fill=COLOR_WHITE)

    # Subtitle
    if data.subtitle:
        draw.text(
            (PADDING, 350),
            _truncate_text(data.subtitle, 60),
            font=subtitle_font,
            fill=COLOR_WHITE,
        )

    # CTA
    cta = data.cta_text or "Donate!"
    _draw_overlay_bar(img, OG_HEIGHT - 100, 100)
    draw = ImageDraw.Draw(img)
    _draw_text_with_shadow(
        draw,
        (PADDING, OG_HEIGHT - 80),
        cta,
        cta_font,
        fill=(255, 235, 59),
    )

    return _image_to_png(img)


def generate_story_card(data: CardData) -> bytes:
    """Generate a story card with title and Read Story CTA."""
    img = _generate_base_image()
    draw = ImageDraw.Draw(img)

    title_font = _load_font(FONT_TITLE)
    cta_font = _load_font(FONT_CTA)
    small_font = _load_regular_font(FONT_SMALL)

    # Logo
    draw.text((PADDING, PADDING), LOGO_TEXT, font=small_font, fill=COLOR_WHITE)

    # Title (centered vertically)
    title = _truncate_text(data.title, 50)
    _draw_text_with_shadow(draw, (PADDING, OG_HEIGHT // 2 - 60), title, title_font)

    # Subtitle
    if data.subtitle:
        subtitle_font = _load_regular_font(FONT_SUBTITLE)
        draw.text(
            (PADDING, OG_HEIGHT // 2 + 10),
            _truncate_text(data.subtitle, 70),
            font=subtitle_font,
            fill=COLOR_WHITE,
        )

    # CTA
    cta = data.cta_text or "Read Story"
    _draw_overlay_bar(img, OG_HEIGHT - 100, 100)
    draw = ImageDraw.Draw(img)
    _draw_text_with_shadow(draw, (PADDING, OG_HEIGHT - 80), cta, cta_font, fill=(255, 235, 59))

    return _image_to_png(img)


def generate_blog_card(data: CardData) -> bytes:
    """Generate a blog card with title, author, and date."""
    img = _generate_base_image()
    draw = ImageDraw.Draw(img)

    title_font = _load_font(FONT_TITLE)
    body_font = _load_regular_font(FONT_BODY)
    small_font = _load_regular_font(FONT_SMALL)

    # Logo
    draw.text((PADDING, PADDING), LOGO_TEXT, font=small_font, fill=COLOR_WHITE)

    # "BLOG" label
    draw.text((PADDING, 100), "BLOG", font=_load_font(FONT_SUBTITLE), fill=(255, 235, 59))

    # Title
    title = _truncate_text(data.title, 50)
    _draw_text_with_shadow(draw, (PADDING, 170), title, title_font)

    # Author and date
    meta_parts = []
    if data.author:
        meta_parts.append(f"By {data.author}")
    if data.date_text:
        meta_parts.append(data.date_text)
    if meta_parts:
        meta_text = " | ".join(meta_parts)
        draw.text((PADDING, 280), meta_text, font=body_font, fill=COLOR_WHITE)

    # Branding bar
    _draw_overlay_bar(img, OG_HEIGHT - 80, 80)
    draw = ImageDraw.Draw(img)
    draw.text(
        (PADDING, OG_HEIGHT - 60),
        LOGO_TEXT,
        font=small_font,
        fill=COLOR_WHITE,
    )

    return _image_to_png(img)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GENERATORS = {
    OGCardType.ANIMAL: generate_animal_card,
    OGCardType.CAMPAIGN: generate_campaign_card,
    OGCardType.STORY: generate_story_card,
    OGCardType.BLOG: generate_blog_card,
}


def generate_og_image(card_type: str, data: CardData) -> bytes:
    """Generate an OG image for the given card type and data.

    Returns PNG bytes.

    Raises:
        InvalidCardTypeError: If card_type is not supported.
        OGImageError: If image generation fails.
    """
    if card_type not in VALID_CARD_TYPES:
        raise InvalidCardTypeError(card_type)

    generator = _GENERATORS[OGCardType(card_type)]
    try:
        return generator(data)
    except Exception as exc:
        logger.error(
            "OG image generation failed: type=%s title=%s error=%s",
            card_type,
            data.title,
            exc,
        )
        raise OGImageError(
            message="Image generation failed",
            details=f"Could not generate {card_type} card: {exc}",
        ) from exc


def generate_placeholder() -> bytes:
    """Generate a placeholder image for fallback scenarios."""
    img = _generate_base_image()
    draw = ImageDraw.Draw(img)
    title_font = _load_font(FONT_TITLE)
    small_font = _load_regular_font(FONT_SMALL)

    draw.text((PADDING, PADDING), LOGO_TEXT, font=small_font, fill=COLOR_WHITE)
    _draw_text_with_shadow(
        draw,
        (OG_WIDTH // 2 - 200, OG_HEIGHT // 2 - 30),
        "Refugio Animal Paraguay",
        title_font,
    )

    return _image_to_png(img)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _image_to_png(img: Image.Image) -> bytes:
    """Convert RGBA image to PNG bytes."""
    # Flatten RGBA to RGB for PNG output
    rgb_img = Image.new("RGB", img.size, COLOR_WHITE)
    rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
    buf = io.BytesIO()
    rgb_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
