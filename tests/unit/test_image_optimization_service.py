"""Unit tests for image optimization service."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image
from src.services.image_optimization_service import (
    JPEG_QUALITY,
    OPTIMIZED_MAX_WIDTH,
    THUMBNAIL_WIDTH,
    WEBP_QUALITY,
    ImageOptimizationError,
    OptimizationResult,
    _resize_image,
    _save_as_webp,
    _strip_exif,
    optimize_image,
    process_and_update_media,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_image(
    width: int = 4000,
    height: int = 2000,
    mode: str = "RGB",
    fmt: str = "JPEG",
    tmp_path: Path | None = None,
) -> Path:
    """Create a test image file and return its path."""
    img = Image.new(mode, (width, height), color="red")
    if tmp_path is None:
        tmp_path = Path("/tmp")
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    path = tmp_path / f"test_image.{ext}"
    img.save(path, format=fmt)
    return path


def _make_pil_image(width: int = 100, height: int = 80, mode: str = "RGB") -> Image.Image:
    """Create an in-memory PIL Image."""
    return Image.new(mode, (width, height), color="blue")


# ---------------------------------------------------------------------------
# _strip_exif tests
# ---------------------------------------------------------------------------


class TestStripExif:
    """Tests for EXIF stripping."""

    def test_returns_same_dimensions(self) -> None:
        img = _make_pil_image(200, 150)
        clean = _strip_exif(img)
        assert clean.size == (200, 150)

    def test_returns_same_mode(self) -> None:
        img = _make_pil_image(100, 100, mode="RGBA")
        clean = _strip_exif(img)
        assert clean.mode == "RGBA"

    def test_preserves_pixel_data(self) -> None:
        img = _make_pil_image(10, 10)
        original_data = list(img.getdata())
        clean = _strip_exif(img)
        clean_data = list(clean.getdata())
        assert original_data == clean_data


# ---------------------------------------------------------------------------
# _resize_image tests
# ---------------------------------------------------------------------------


class TestResizeImage:
    """Tests for image resizing."""

    def test_downsizes_wide_image(self) -> None:
        img = _make_pil_image(4000, 2000)
        resized = _resize_image(img, 1920)
        assert resized.size[0] == 1920
        assert resized.size[1] == 960

    def test_preserves_aspect_ratio(self) -> None:
        img = _make_pil_image(3000, 2000)
        resized = _resize_image(img, 1920)
        original_ratio = 3000 / 2000
        new_ratio = resized.size[0] / resized.size[1]
        assert abs(original_ratio - new_ratio) < 0.01

    def test_no_upscale_when_smaller(self) -> None:
        img = _make_pil_image(800, 600)
        resized = _resize_image(img, 1920)
        assert resized.size == (800, 600)

    def test_exact_width_not_resized(self) -> None:
        img = _make_pil_image(1920, 1080)
        resized = _resize_image(img, 1920)
        assert resized.size == (1920, 1080)

    def test_thumbnail_width(self) -> None:
        img = _make_pil_image(2000, 1500)
        resized = _resize_image(img, THUMBNAIL_WIDTH)
        assert resized.size[0] == 400
        assert resized.size[1] == 300


# ---------------------------------------------------------------------------
# _save_as_webp tests
# ---------------------------------------------------------------------------


class TestSaveAsWebp:
    """Tests for WebP conversion."""

    def test_creates_webp_file(self, tmp_path: Path) -> None:
        img = _make_pil_image(100, 80)
        output = tmp_path / "output.webp"
        size = _save_as_webp(img, output)
        assert output.exists()
        assert size > 0

    def test_converts_rgba_to_rgb(self, tmp_path: Path) -> None:
        img = _make_pil_image(100, 80, mode="RGBA")
        output = tmp_path / "rgba.webp"
        _save_as_webp(img, output)
        assert output.exists()
        # Verify the saved image is readable
        saved = Image.open(output)
        assert saved.mode == "RGB"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        img = _make_pil_image(50, 50)
        output = tmp_path / "deep" / "nested" / "output.webp"
        _save_as_webp(img, output)
        assert output.exists()


# ---------------------------------------------------------------------------
# optimize_image tests
# ---------------------------------------------------------------------------


class TestOptimizeImage:
    """Tests for the full optimization pipeline."""

    def test_generates_optimized_and_thumbnail(self, tmp_path: Path) -> None:
        original = _make_test_image(4000, 2000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_path is not None
        assert result.thumbnail_path is not None
        assert Path(result.optimized_path).exists()
        assert Path(result.thumbnail_path).exists()

    def test_optimized_is_webp(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_path is not None
        assert result.optimized_path.endswith(".webp")

    def test_thumbnail_is_webp(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.thumbnail_path is not None
        assert result.thumbnail_path.endswith(".webp")

    def test_optimized_max_width(self, tmp_path: Path) -> None:
        original = _make_test_image(4000, 2000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_path is not None
        img = Image.open(result.optimized_path)
        assert img.size[0] <= OPTIMIZED_MAX_WIDTH

    def test_thumbnail_width(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1500, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.thumbnail_path is not None
        img = Image.open(result.thumbnail_path)
        assert img.size[0] == THUMBNAIL_WIDTH

    def test_small_image_not_upscaled(self, tmp_path: Path) -> None:
        original = _make_test_image(800, 600, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_path is not None
        img = Image.open(result.optimized_path)
        assert img.size[0] == 800

    def test_compression_ratio_computed(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.compression_ratio > 0
        assert result.original_size_bytes > 0

    def test_size_metrics_populated(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_size_bytes > 0
        assert result.thumbnail_size_bytes > 0
        assert result.original_size_bytes > 0

    def test_invalid_image_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.jpg"
        bad_file.write_bytes(b"not an image")
        output_dir = tmp_path / "output"

        with pytest.raises(ImageOptimizationError, match="Cannot open image"):
            optimize_image(bad_file, output_dir)

    def test_png_with_alpha(self, tmp_path: Path) -> None:
        """PNG with RGBA mode should be handled correctly."""
        original = _make_test_image(1000, 800, mode="RGBA", fmt="PNG", tmp_path=tmp_path)
        output_dir = tmp_path / "output"

        result = optimize_image(original, output_dir)

        assert result.optimized_path is not None
        assert Path(result.optimized_path).exists()


# ---------------------------------------------------------------------------
# process_and_update_media tests
# ---------------------------------------------------------------------------


class TestProcessAndUpdateMedia:
    """Tests for the async DB-updating wrapper."""

    @pytest.mark.asyncio
    async def test_updates_status_to_complete(self, tmp_path: Path) -> None:
        original = _make_test_image(2000, 1000, tmp_path=tmp_path)
        output_dir = tmp_path / "output"
        db = AsyncMock()
        media_id = MagicMock()

        result = await process_and_update_media(
            media_id=media_id,
            original_absolute_path=original,
            output_dir=output_dir,
            db=db,
        )

        assert isinstance(result, OptimizationResult)
        # Should have called execute 3 times: processing, complete update, flush x2
        assert db.execute.await_count >= 2
        assert db.flush.await_count >= 2

    @pytest.mark.asyncio
    async def test_marks_failed_on_bad_image(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.jpg"
        bad_file.write_bytes(b"not an image")
        output_dir = tmp_path / "output"
        db = AsyncMock()
        media_id = MagicMock()

        with pytest.raises(ImageOptimizationError):
            await process_and_update_media(
                media_id=media_id,
                original_absolute_path=bad_file,
                output_dir=output_dir,
                db=db,
            )

        # Should have marked as failed
        assert db.execute.await_count >= 2  # processing + failed


# ---------------------------------------------------------------------------
# OptimizationResult tests
# ---------------------------------------------------------------------------


class TestOptimizationResult:
    """Tests for the result dataclass."""

    def test_immutable(self) -> None:
        result = OptimizationResult(
            optimized_path="/tmp/opt.webp",
            thumbnail_path="/tmp/thumb.webp",
            optimized_size_bytes=5000,
            thumbnail_size_bytes=2000,
            original_size_bytes=20000,
            compression_ratio=0.35,
        )
        with pytest.raises(AttributeError):
            result.optimized_path = "/new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_optimized_max_width(self) -> None:
        assert OPTIMIZED_MAX_WIDTH == 1920

    def test_thumbnail_width(self) -> None:
        assert THUMBNAIL_WIDTH == 400

    def test_webp_quality(self) -> None:
        assert WEBP_QUALITY == 85

    def test_jpeg_quality(self) -> None:
        assert JPEG_QUALITY == 85
