"""Service layer for adopter document upload and management.

Handles:
  - File validation (MIME type, size)
  - Storage to filesystem with structured paths
  - Database metadata persistence
  - Access control helpers (adopter owns their documents)
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import magic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adopter_document import AdopterDocument, AdopterDocumentType

logger = logging.getLogger(__name__)

# Maximum document size: 10 MB
MAX_DOCUMENT_SIZE_BYTES = 10_485_760

# Allowed MIME types for adopter documents
ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Map MIME types to file extensions
MIME_TO_EXTENSION: dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# Default upload root directory
DEFAULT_DOCUMENT_ROOT = Path("media/adopter_documents")


class DocumentValidationError(Exception):
    """Raised when an uploaded document fails validation."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class DocumentStorageError(Exception):
    """Raised when document storage fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class DocumentUploadResult:
    """Result of a successful document upload."""

    id: UUID
    original_filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    document_type: str
    created_at: datetime


def validate_document_size(content: bytes) -> None:
    """Raise DocumentValidationError if file exceeds size limit."""
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise DocumentValidationError(
            message="File too large",
            details=f"Maximum allowed size is {MAX_DOCUMENT_SIZE_BYTES} bytes, got {len(content)} bytes",
        )


def validate_document_mime_type(content: bytes, filename: str) -> str:
    """Validate MIME type via magic bytes. Returns the detected MIME type.

    Raises DocumentValidationError if the detected type is not allowed or
    the extension does not match the detected MIME type.
    """
    detected_mime = magic.from_buffer(content[:2048], mime=True)

    if detected_mime not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise DocumentValidationError(
            message="Unsupported file type",
            details=f"Allowed types: pdf, jpg, png, webp. Detected: {detected_mime}",
        )

    # Verify extension roughly matches detected MIME
    extension_map: dict[str, set[str]] = {
        "application/pdf": {"pdf"},
        "image/jpeg": {"jpg", "jpeg"},
        "image/png": {"png"},
        "image/webp": {"webp"},
    }
    suffix = Path(filename).suffix.lstrip(".").lower()
    valid_extensions = extension_map.get(detected_mime, set())
    if valid_extensions and suffix and suffix not in valid_extensions:
        raise DocumentValidationError(
            message="File extension does not match content",
            details=f"Detected {detected_mime} but filename has extension .{suffix}",
        )

    return detected_mime


def build_storage_path(
    adopter_id: UUID,
    document_id: UUID,
    extension: str,
    upload_root: Path = DEFAULT_DOCUMENT_ROOT,
) -> Path:
    """Build a structured storage path for the document file."""
    today = datetime.now(UTC)
    return upload_root / str(adopter_id) / today.strftime("%Y/%m") / f"{document_id}.{extension}"


async def get_adopter_by_email(email: str, db: AsyncSession) -> Adopter | None:
    """Fetch an active adopter by email address."""
    stmt = select(Adopter).where(
        Adopter.email == email,
        Adopter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upload_adopter_document(
    adopter_id: UUID,
    content: bytes,
    original_filename: str,
    document_type: AdopterDocumentType,
    description: str | None,
    uploaded_by_user_id: UUID | None,
    db: AsyncSession,
    upload_root: Path = DEFAULT_DOCUMENT_ROOT,
) -> DocumentUploadResult:
    """Validate, store, and record an adopter document upload.

    Steps:
      1. Validate file size
      2. Validate MIME type via magic bytes
      3. Write file to structured path
      4. Persist metadata record

    Raises DocumentValidationError or DocumentStorageError on failure.
    """
    validate_document_size(content)
    detected_mime = validate_document_mime_type(content, original_filename)

    document_id = uuid4()
    extension = MIME_TO_EXTENSION[detected_mime]
    storage_path = build_storage_path(adopter_id, document_id, extension, upload_root)

    # Ensure directory exists
    try:
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(content)
    except OSError as exc:
        raise DocumentStorageError(f"Failed to write document to disk: {exc}") from exc

    # Persist metadata
    doc = AdopterDocument(
        id=document_id,
        adopter_id=adopter_id,
        original_filename=original_filename[:255],
        storage_path=str(storage_path),
        content_type=detected_mime,
        size_bytes=len(content),
        document_type=document_type.value,
        description=description,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    logger.info(
        "Adopter document uploaded",
        extra={
            "adopter_id": str(adopter_id),
            "document_id": str(document_id),
            "content_type": detected_mime,
            "size_bytes": len(content),
        },
    )

    return DocumentUploadResult(
        id=doc.id,
        original_filename=doc.original_filename,
        storage_path=doc.storage_path,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        document_type=doc.document_type,
        created_at=doc.created_at,
    )


async def list_adopter_documents(
    adopter_id: UUID,
    db: AsyncSession,
) -> list[AdopterDocument]:
    """Return all documents for a given adopter, newest first."""
    stmt = (
        select(AdopterDocument)
        .where(AdopterDocument.adopter_id == adopter_id)
        .order_by(AdopterDocument.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_document_or_none(
    document_id: UUID,
    db: AsyncSession,
) -> AdopterDocument | None:
    """Fetch a single adopter document by ID."""
    return await db.get(AdopterDocument, document_id)


async def delete_adopter_document(
    document: AdopterDocument,
    db: AsyncSession,
) -> None:
    """Delete the document record and its file from storage."""
    storage_path = Path(document.storage_path)
    if storage_path.exists():
        try:
            storage_path.unlink()
            logger.info(
                "Adopter document file deleted",
                extra={"storage_path": str(storage_path)},
            )
        except OSError as exc:
            # Log but don't block DB deletion — orphaned files handled by cleanup job
            logger.warning(
                "Could not delete document file — orphan may require cleanup",
                extra={"storage_path": str(storage_path), "error": str(exc)},
            )
    await db.delete(document)
    await db.flush()
