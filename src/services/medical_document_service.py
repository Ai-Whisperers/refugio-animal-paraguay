"""Medical document upload service — validation, storage, and vet visit linking.

Handles upload of medical documents (PDF, images) with magic-bytes
validation. Documents are linked to vet visit records in the database.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import magic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.medical import VetVisit
from src.db.models.vet_document import VetDocument

logger = logging.getLogger(__name__)

# Maximum upload size: 20 MB
MAX_MEDICAL_FILE_SIZE_BYTES = 20_971_520

# Allowed MIME types for medical documents
ALLOWED_MEDICAL_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
    }
)

# MIME to extension mapping
MEDICAL_MIME_TO_EXTENSION: dict[str, set[str]] = {
    "application/pdf": {"pdf"},
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
}

# Default storage root for medical documents
DEFAULT_MEDICAL_UPLOAD_ROOT = Path("media/medical")


class MedicalDocumentValidationError(Exception):
    """Raised when a medical document fails validation."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class VetVisitNotFoundError(Exception):
    """Raised when the target vet visit does not exist."""

    def __init__(self, vet_visit_id: UUID) -> None:
        super().__init__(f"Vet visit not found: {vet_visit_id}")
        self.vet_visit_id = vet_visit_id


@dataclass(frozen=True)
class MedicalDocumentUploadResult:
    """Result of a successful medical document upload."""

    id: UUID
    document_type: str
    url: str
    uploaded_date: datetime
    original_filename: str
    size_bytes: int
    content_type: str


def validate_medical_file_size(content: bytes) -> None:
    """Raise error if file exceeds 20MB limit."""
    if len(content) > MAX_MEDICAL_FILE_SIZE_BYTES:
        raise MedicalDocumentValidationError(
            message="File too large",
            details=(
                f"Maximum allowed size is {MAX_MEDICAL_FILE_SIZE_BYTES} bytes, "
                f"got {len(content)} bytes"
            ),
        )


def validate_medical_mime_type(content: bytes, filename: str) -> str:
    """Validate MIME type via magic bytes. Returns detected MIME type."""
    detected_mime = magic.from_buffer(content[:2048], mime=True)

    if detected_mime not in ALLOWED_MEDICAL_MIME_TYPES:
        raise MedicalDocumentValidationError(
            message="Invalid file type",
            details=f"Allowed types: pdf, jpg, png. Detected: {detected_mime}",
        )

    # Verify extension matches
    extension = Path(filename).suffix.lower().lstrip(".")
    valid_extensions = MEDICAL_MIME_TO_EXTENSION.get(detected_mime, set())
    if extension not in valid_extensions:
        raise MedicalDocumentValidationError(
            message="File extension mismatch",
            details=f"Extension '.{extension}' does not match detected type '{detected_mime}'",
        )

    return detected_mime


def generate_medical_storage_path(
    original_filename: str,
    upload_root: Path = DEFAULT_MEDICAL_UPLOAD_ROOT,
) -> tuple[str, Path]:
    """Generate date-based storage path for medical documents."""
    now = datetime.now(UTC)
    extension = Path(original_filename).suffix.lower().lstrip(".")
    file_uuid = uuid4()
    filename = f"{file_uuid}.{extension}"

    relative = Path(f"{now.year}/{now.month:02d}/{now.day:02d}/{file_uuid}/{filename}")
    absolute = upload_root / relative

    return str(relative), absolute


async def upload_medical_document(
    *,
    content: bytes,
    filename: str,
    vet_visit_id: UUID,
    document_type: str,
    description: str | None,
    uploaded_by: UUID | None,
    db: AsyncSession,
    upload_root: Path = DEFAULT_MEDICAL_UPLOAD_ROOT,
) -> MedicalDocumentUploadResult:
    """Validate, store, and link a medical document to a vet visit.

    Raises
    ------
    VetVisitNotFoundError
        If the vet visit does not exist.
    MedicalDocumentValidationError
        If the file fails validation.
    """
    # Step 1: Verify vet visit exists
    result = await db.execute(select(VetVisit).where(VetVisit.id == vet_visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise VetVisitNotFoundError(vet_visit_id)

    # Step 2: Validate
    validate_medical_file_size(content)
    detected_mime = validate_medical_mime_type(content, filename)

    # Step 3: Generate path and store
    relative_path, absolute_path = generate_medical_storage_path(filename, upload_root)

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)

    # Step 4: Create DB record
    doc_id = uuid4()
    # Virus scanning placeholder — log warning if ClamAV not available
    is_scanned = False
    logger.warning(
        "ClamAV not available — medical document uploaded without virus scan",
        extra={"document_id": str(doc_id), "original_filename": filename},
    )

    doc = VetDocument(
        id=doc_id,
        vet_visit_id=vet_visit_id,
        original_filename=filename,
        storage_path=relative_path,
        content_type=detected_mime,
        size_bytes=len(content),
        document_type=document_type,
        description=description,
        uploaded_by=uploaded_by,
        is_virus_scanned=is_scanned,
    )

    try:
        db.add(doc)
        await db.flush()
    except Exception:
        # Clean up file if DB fails
        import contextlib

        with contextlib.suppress(OSError):
            absolute_path.unlink(missing_ok=True)
        raise

    logger.info(
        "Medical document uploaded",
        extra={
            "document_id": str(doc_id),
            "vet_visit_id": str(vet_visit_id),
            "type": document_type,
            "size": len(content),
        },
    )

    return MedicalDocumentUploadResult(
        id=doc_id,
        document_type=document_type,
        url=f"/media/medical/{relative_path}",
        uploaded_date=datetime.now(UTC),
        original_filename=filename,
        size_bytes=len(content),
        content_type=detected_mime,
    )
