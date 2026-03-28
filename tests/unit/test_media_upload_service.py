"""Unit tests for media upload service."""

import io
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from PIL import Image
from src.services.media_upload_service import (
    ALLOWED_MIME_TYPES,
    DEFAULT_UPLOAD_ROOT,
    MAX_FILE_SIZE_BYTES,
    MIME_TO_EXTENSION,
    MediaStorageError,
    MediaValidationError,
    UploadResult,
    extract_dimensions,
    generate_storage_path,
    upload_media,
    validate_file_size,
    validate_mime_type,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jpeg_bytes(width: int = 100, height: int = 80) -> bytes:
    """Create minimal valid JPEG bytes."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width: int = 50, height: int = 50) -> bytes:
    """Create minimal valid PNG bytes."""
    img = Image.new("RGBA", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_webp_bytes(width: int = 60, height: int = 40) -> bytes:
    """Create minimal valid WebP bytes."""
    img = Image.new("RGB", (width, height), color="green")
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# validate_file_size tests
# ---------------------------------------------------------------------------


class TestValidateFileSize:
    """Tests for file size validation."""

    def test_accepts_small_file(self) -> None:
        validate_file_size(b"x" * 1000)

    def test_accepts_max_size(self) -> None:
        validate_file_size(b"x" * MAX_FILE_SIZE_BYTES)

    def test_rejects_oversized_file(self) -> None:
        content = b"x" * (MAX_FILE_SIZE_BYTES + 1)
        with pytest.raises(MediaValidationError, match="File too large"):
            validate_file_size(content)

    def test_accepts_empty_content(self) -> None:
        # Size validation passes — emptiness is checked elsewhere
        validate_file_size(b"")


# ---------------------------------------------------------------------------
# validate_mime_type tests
# ---------------------------------------------------------------------------


class TestValidateMimeType:
    """Tests for MIME type and magic bytes validation."""

    def test_accepts_valid_jpeg(self) -> None:
        content = _make_jpeg_bytes()
        result = validate_mime_type(content, "photo.jpg")
        assert result == "image/jpeg"

    def test_accepts_jpeg_extension(self) -> None:
        content = _make_jpeg_bytes()
        result = validate_mime_type(content, "photo.jpeg")
        assert result == "image/jpeg"

    def test_accepts_valid_png(self) -> None:
        content = _make_png_bytes()
        result = validate_mime_type(content, "image.png")
        assert result == "image/png"

    def test_accepts_valid_webp(self) -> None:
        content = _make_webp_bytes()
        result = validate_mime_type(content, "image.webp")
        assert result == "image/webp"

    def test_rejects_text_file(self) -> None:
        with pytest.raises(MediaValidationError, match="Invalid file type"):
            validate_mime_type(b"Hello, world!", "file.txt")

    def test_rejects_extension_mismatch(self) -> None:
        content = _make_jpeg_bytes()
        with pytest.raises(MediaValidationError, match="extension mismatch"):
            validate_mime_type(content, "photo.png")

    def test_rejects_spoofed_extension(self) -> None:
        """A JPEG file with .webp extension should be rejected."""
        content = _make_jpeg_bytes()
        with pytest.raises(MediaValidationError, match="extension mismatch"):
            validate_mime_type(content, "fake.webp")


# ---------------------------------------------------------------------------
# extract_dimensions tests
# ---------------------------------------------------------------------------


class TestExtractDimensions:
    """Tests for image dimension extraction."""

    def test_jpeg_dimensions(self) -> None:
        content = _make_jpeg_bytes(200, 150)
        w, h = extract_dimensions(content)
        assert w == 200
        assert h == 150

    def test_png_dimensions(self) -> None:
        content = _make_png_bytes(300, 250)
        w, h = extract_dimensions(content)
        assert w == 300
        assert h == 250

    def test_webp_dimensions(self) -> None:
        content = _make_webp_bytes(400, 300)
        w, h = extract_dimensions(content)
        assert w == 400
        assert h == 300

    def test_invalid_content_raises(self) -> None:
        with pytest.raises(MediaValidationError, match="Cannot read image"):
            extract_dimensions(b"not an image")


# ---------------------------------------------------------------------------
# generate_storage_path tests
# ---------------------------------------------------------------------------


class TestGenerateStoragePath:
    """Tests for storage path generation."""

    def test_returns_relative_and_absolute(self) -> None:
        relative, absolute = generate_storage_path("photo.jpg")
        assert isinstance(relative, str)
        assert isinstance(absolute, Path)

    def test_preserves_extension(self) -> None:
        relative, _ = generate_storage_path("my-photo.png")
        assert relative.endswith(".png")

    def test_uses_uuid_filename(self) -> None:
        relative, _ = generate_storage_path("original.jpg")
        filename = Path(relative).stem
        # Should be a valid UUID
        UUID(filename)

    def test_date_based_directory(self) -> None:
        relative, _ = generate_storage_path("photo.jpg")
        parts = relative.split("/")
        # year/month/day/filename
        assert len(parts) == 4
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # zero-padded month
        assert len(parts[2]) == 2  # zero-padded day

    def test_custom_upload_root(self) -> None:
        _, absolute = generate_storage_path("photo.jpg", upload_root=Path("/tmp/test"))
        assert str(absolute).startswith("/tmp/test/")


# ---------------------------------------------------------------------------
# upload_media tests
# ---------------------------------------------------------------------------


class TestUploadMedia:
    """Tests for the full upload flow."""

    @pytest.mark.asyncio
    async def test_successful_upload(self, tmp_path: Path) -> None:
        content = _make_jpeg_bytes(200, 150)
        db = AsyncMock()

        result = await upload_media(
            content=content,
            filename="test.jpg",
            uploaded_by=None,
            db=db,
            upload_root=tmp_path,
        )

        assert isinstance(result, UploadResult)
        assert result.width == 200
        assert result.height == 150
        assert result.content_type == "image/jpeg"
        assert result.original_filename == "test.jpg"
        assert result.size_bytes == len(content)
        assert result.url.startswith("/media/uploads/")
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_file_written_to_disk(self, tmp_path: Path) -> None:
        content = _make_png_bytes(50, 50)
        db = AsyncMock()

        await upload_media(
            content=content,
            filename="img.png",
            uploaded_by=None,
            db=db,
            upload_root=tmp_path,
        )

        # Verify file exists on disk
        files = list(tmp_path.rglob("*.png"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self, tmp_path: Path) -> None:
        content = b"x" * (MAX_FILE_SIZE_BYTES + 1)
        db = AsyncMock()

        with pytest.raises(MediaValidationError, match="File too large"):
            await upload_media(
                content=content,
                filename="big.jpg",
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

    @pytest.mark.asyncio
    async def test_rejects_invalid_type(self, tmp_path: Path) -> None:
        db = AsyncMock()

        with pytest.raises(MediaValidationError, match="Invalid file type"):
            await upload_media(
                content=b"not an image",
                filename="file.txt",
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

    @pytest.mark.asyncio
    async def test_cleans_up_on_db_failure(self, tmp_path: Path) -> None:
        content = _make_jpeg_bytes()
        db = AsyncMock()
        db.flush.side_effect = RuntimeError("DB error")

        with pytest.raises(RuntimeError, match="DB error"):
            await upload_media(
                content=content,
                filename="test.jpg",
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

        # File should be cleaned up
        files = list(tmp_path.rglob("*.jpg"))
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_storage_error_on_write_failure(self, tmp_path: Path) -> None:
        content = _make_jpeg_bytes()
        db = AsyncMock()

        # Use a path that can't be written to
        read_only_path = tmp_path / "readonly"
        read_only_path.mkdir()
        read_only_path.chmod(0o444)

        with pytest.raises(MediaStorageError, match="Failed to store"):
            await upload_media(
                content=content,
                filename="test.jpg",
                uploaded_by=None,
                db=db,
                upload_root=read_only_path,
            )

        # Restore permissions for cleanup
        read_only_path.chmod(0o755)


# ---------------------------------------------------------------------------
# UploadResult tests
# ---------------------------------------------------------------------------


class TestUploadResult:
    """Tests for the result dataclass."""

    def test_immutable(self) -> None:
        result = UploadResult(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            url="/media/uploads/2026/03/27/test.jpg",
            thumbnail_url=None,
            width=100,
            height=80,
            size_bytes=5000,
            content_type="image/jpeg",
            original_filename="test.jpg",
        )
        with pytest.raises(AttributeError):
            result.width = 200  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_max_file_size(self) -> None:
        assert MAX_FILE_SIZE_BYTES == 10_485_760

    def test_allowed_mime_types(self) -> None:
        assert "image/jpeg" in ALLOWED_MIME_TYPES
        assert "image/png" in ALLOWED_MIME_TYPES
        assert "image/webp" in ALLOWED_MIME_TYPES
        assert len(ALLOWED_MIME_TYPES) == 3

    def test_mime_to_extension_mapping(self) -> None:
        assert MIME_TO_EXTENSION["image/jpeg"] == "jpg"
        assert MIME_TO_EXTENSION["image/png"] == "png"
        assert MIME_TO_EXTENSION["image/webp"] == "webp"

    def test_default_upload_root(self) -> None:
        assert Path("media/uploads") == DEFAULT_UPLOAD_ROOT
