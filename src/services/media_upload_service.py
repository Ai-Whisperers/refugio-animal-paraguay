"""Media upload service — file validation, storage, and metadata persistence.

Handles:
  - MIME type and magic-bytes validation
  - File size enforcement
  - UUID-based filename generation
  - Date-based directory structure
  - Image dimension extraction via PIL
  - Database metadata record creation
"""

import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import magic
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.media import Media, MediaContentType

logger = logging.getLogger(__name__)

# Maximum upload size: 10 MB
MAX_FILE_SIZE_BYTES = 10_485_760

# Allowed MIME types
ALLOWED_MIME_TYPES = MediaContentType.ALL

# Map MIME types to file extensions
MIME_TO_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# Default upload root directory
DEFAULT_UPLOAD_ROOT = Path("media/uploads")


class MediaValidationError(Exception):
    """Raised when an uploaded file fails validation."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class MediaStorageError(Exception):
    """Raised when file storage fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class UploadResult:
    """Result of a successful media upload."""

    id: UUID
    url: str
    thumbnail_url: str | None
    width: int
    height: int
    size_bytes: int
    content_type: str
    original_filename: str


def validate_file_size(content: bytes) -> None:
    """Raise MediaValidationError if file exceeds size limit."""
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise MediaValidationError(
            message="File too large",
            details=f"Maximum allowed size is {MAX_FILE_SIZE_BYTES} bytes, got {len(content)} bytes",
        )


def validate_mime_type(content: bytes, filename: str) -> str:
    """Validate MIME type via magic bytes. Returns the detected MIME type.

    Raises MediaValidationError if the file type is not allowed or if
    the extension does not match the detected MIME type.
    """
    detected_mime = magic.from_buffer(content[:2048], mime=True)

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise MediaValidationError(
            message="Invalid file type",
            details=f"Allowed types: jpg, png, webp. Detected: {detected_mime}",
        )

    # Verify extension matches detected MIME
    extension = Path(filename).suffix.lower().lstrip(".")
    expected_extensions = {
        "image/jpeg": {"jpg", "jpeg"},
        "image/png": {"png"},
        "image/webp": {"webp"},
    }
    valid_extensions = expected_extensions.get(detected_mime, set())
    if extension not in valid_extensions:
        raise MediaValidationError(
            message="File extension mismatch",
            details=f"Extension '.{extension}' does not match detected type '{detected_mime}'",
        )

    return detected_mime


def extract_dimensions(content: bytes) -> tuple[int, int]:
    """Extract image width and height using PIL.

    Returns (width, height) tuple.
    Raises MediaValidationError if the image cannot be read.
    """
    try:
        import io

        img = Image.open(io.BytesIO(content))
        return img.size
    except Exception as exc:
        raise MediaValidationError(
            message="Cannot read image dimensions",
            details=str(exc),
        ) from exc


def generate_storage_path(
    original_filename: str,
    upload_root: Path = DEFAULT_UPLOAD_ROOT,
) -> tuple[str, Path]:
    """Generate a date-based storage path with UUID filename.

    Returns (relative_path_str, absolute_path).
    """
    now = datetime.now(UTC)
    extension = Path(original_filename).suffix.lower().lstrip(".")
    file_uuid = uuid4()
    filename = f"{file_uuid}.{extension}"

    relative = Path(f"{now.year}/{now.month:02d}/{now.day:02d}/{filename}")
    absolute = upload_root / relative

    return str(relative), absolute


async def upload_media(
    *,
    content: bytes,
    filename: str,
    uploaded_by: UUID | None,
    db: AsyncSession,
    upload_root: Path = DEFAULT_UPLOAD_ROOT,
) -> UploadResult:
    """Validate, store, and persist metadata for an uploaded image.

    Parameters
    ----------
    content : bytes
        Raw file content.
    filename : str
        Original filename from the upload.
    uploaded_by : UUID | None
        User ID of the uploader (None for system uploads).
    db : AsyncSession
        Database session.
    upload_root : Path
        Root directory for file storage.

    Returns
    -------
    UploadResult
        Metadata about the stored file.

    Raises
    ------
    MediaValidationError
        If file fails validation (size, type, dimensions).
    MediaStorageError
        If file cannot be written to disk.
    """
    # Step 1: Validate
    validate_file_size(content)
    detected_mime = validate_mime_type(content, filename)
    width, height = extract_dimensions(content)

    # Step 2: Generate storage path
    relative_path, absolute_path = generate_storage_path(filename, upload_root)

    # Step 3: Write to disk
    try:
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)
    except OSError as exc:
        logger.error(
            "Failed to write media file",
            extra={"path": str(absolute_path), "error": str(exc)},
        )
        raise MediaStorageError(
            message=f"Failed to store file: {exc}",
        ) from exc

    # Step 4: Create DB record (within the caller's transaction)
    media_id = uuid4()
    media = Media(
        id=media_id,
        original_filename=filename,
        storage_path=relative_path,
        content_type=detected_mime,
        size_bytes=len(content),
        width=width,
        height=height,
        uploaded_by=uploaded_by,
    )

    try:
        db.add(media)
        await db.flush()
    except Exception:
        # Clean up the file if DB insert fails
        with contextlib.suppress(OSError):
            absolute_path.unlink(missing_ok=True)
        raise

    logger.info(
        "Media uploaded",
        extra={
            "media_id": str(media_id),
            "filename": filename,
            "size": len(content),
            "mime": detected_mime,
        },
    )

    return UploadResult(
        id=media_id,
        url=f"/media/uploads/{relative_path}",
        thumbnail_url=None,
        width=width,
        height=height,
        size_bytes=len(content),
        content_type=detected_mime,
        original_filename=filename,
    )
