"""Image optimization pipeline — resize, thumbnail, WebP conversion.

Processes uploaded images into three versions:
  - original: kept as-is (fallback)
  - optimized: max 1920px wide, WebP format, 85% quality, EXIF stripped
  - thumbnail: 400px wide, WebP format, 85% quality, EXIF stripped

All processing uses Pillow. EXIF data is stripped for privacy (no
geolocation, camera info in output files).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from PIL import Image

from src.db.models.media import OptimizationStatus

logger = logging.getLogger(__name__)

# Maximum width for the optimized version
OPTIMIZED_MAX_WIDTH = 1920

# Width for thumbnail
THUMBNAIL_WIDTH = 400

# WebP quality (0-100)
WEBP_QUALITY = 85

# JPEG quality for fallback (when saving as JPEG)
JPEG_QUALITY = 85


class ImageOptimizationError(Exception):
    """Raised when image optimization fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class OptimizationResult:
    """Result of image optimization processing."""

    optimized_path: str | None
    thumbnail_path: str | None
    optimized_size_bytes: int
    thumbnail_size_bytes: int
    original_size_bytes: int
    compression_ratio: float


def _strip_exif(img: Image.Image) -> Image.Image:
    """Return a copy of the image with EXIF data removed.

    Creates a new image from pixel data, discarding all metadata
    (EXIF, ICC profile, etc.) for privacy.
    """
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    return clean_img


def _resize_image(img: Image.Image, max_width: int) -> Image.Image:
    """Resize image to max_width while maintaining aspect ratio.

    If the image is already smaller than max_width, returns it unchanged.
    Uses LANCZOS resampling for high-quality downscaling.
    """
    current_width, current_height = img.size

    if current_width <= max_width:
        return img

    ratio = max_width / current_width
    new_height = int(current_height * ratio)

    return img.resize((max_width, new_height), Image.LANCZOS)


def _save_as_webp(img: Image.Image, output_path: Path, quality: int = WEBP_QUALITY) -> int:
    """Save image as WebP, return file size in bytes.

    Converts RGBA to RGB before saving (WebP lossy doesn't support alpha well
    at all quality levels).
    """
    if img.mode == "RGBA":
        # Composite onto white background for WebP
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="WEBP", quality=quality)
    return output_path.stat().st_size


def optimize_image(
    original_path: Path,
    output_dir: Path,
) -> OptimizationResult:
    """Run the full optimization pipeline on an uploaded image.

    Parameters
    ----------
    original_path : Path
        Path to the original uploaded image.
    output_dir : Path
        Directory for optimized and thumbnail outputs (usually
        the same parent as original, e.g. /media/uploads/2026/03/27/{uuid}/).

    Returns
    -------
    OptimizationResult
        Paths and size metrics for all generated versions.

    Raises
    ------
    ImageOptimizationError
        If the image cannot be processed.
    """
    try:
        img = Image.open(original_path)
    except Exception as exc:
        raise ImageOptimizationError(
            message=f"Cannot open image: {exc}",
        ) from exc

    original_size = original_path.stat().st_size

    # Strip EXIF from all versions
    clean_img = _strip_exif(img)

    # Generate optimized version (max 1920px wide, WebP)
    optimized_img = _resize_image(clean_img, OPTIMIZED_MAX_WIDTH)
    optimized_path = output_dir / "optimized.webp"
    optimized_size = _save_as_webp(optimized_img, optimized_path)

    # Generate thumbnail (400px wide, WebP)
    thumbnail_img = _resize_image(clean_img, THUMBNAIL_WIDTH)
    thumbnail_path = output_dir / "thumbnail.webp"
    thumbnail_size = _save_as_webp(thumbnail_img, thumbnail_path)

    total_optimized = optimized_size + thumbnail_size
    compression_ratio = total_optimized / original_size if original_size > 0 else 1.0

    logger.info(
        "Image optimized",
        extra={
            "original_size": original_size,
            "optimized_size": optimized_size,
            "thumbnail_size": thumbnail_size,
            "compression_ratio": f"{compression_ratio:.2f}",
        },
    )

    return OptimizationResult(
        optimized_path=str(optimized_path),
        thumbnail_path=str(thumbnail_path),
        optimized_size_bytes=optimized_size,
        thumbnail_size_bytes=thumbnail_size,
        original_size_bytes=original_size,
        compression_ratio=compression_ratio,
    )


async def process_and_update_media(
    media_id: UUID,
    original_absolute_path: Path,
    output_dir: Path,
    db: "AsyncSession",  # noqa: F821
) -> OptimizationResult:
    """Run optimization pipeline and update the Media record.

    Parameters
    ----------
    media_id : UUID
        ID of the Media record to update.
    original_absolute_path : Path
        Path to the original uploaded file on disk.
    output_dir : Path
        Directory to write optimized/thumbnail files.
    db : AsyncSession
        Database session for updating the Media record.
    """
    from sqlalchemy import update

    from src.db.models.media import Media

    try:
        # Mark as processing
        await db.execute(
            update(Media)
            .where(Media.id == media_id)
            .values(optimization_status=OptimizationStatus.PROCESSING)
        )
        await db.flush()

        result = optimize_image(original_absolute_path, output_dir)

        # Update record with optimization results
        await db.execute(
            update(Media)
            .where(Media.id == media_id)
            .values(
                has_optimized=True,
                has_thumbnail=True,
                optimization_status=OptimizationStatus.COMPLETE,
                optimized_path=result.optimized_path,
                thumbnail_path=result.thumbnail_path,
            )
        )
        await db.flush()

        return result

    except ImageOptimizationError:
        # Mark as failed but don't raise — original is still usable
        await db.execute(
            update(Media)
            .where(Media.id == media_id)
            .values(optimization_status=OptimizationStatus.FAILED)
        )
        await db.flush()
        logger.warning(
            "Image optimization failed, original still usable",
            extra={"media_id": str(media_id)},
        )
        raise
