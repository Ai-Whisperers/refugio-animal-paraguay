"""Unit tests for medical document service."""

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from src.services.medical_document_service import (
    ALLOWED_MEDICAL_MIME_TYPES,
    DEFAULT_MEDICAL_UPLOAD_ROOT,
    MAX_MEDICAL_FILE_SIZE_BYTES,
    MedicalDocumentUploadResult,
    MedicalDocumentValidationError,
    VetVisitNotFoundError,
    generate_medical_storage_path,
    upload_medical_document,
    validate_medical_file_size,
    validate_medical_mime_type,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf_bytes() -> bytes:
    """Create minimal valid PDF bytes."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"


def _make_jpeg_bytes() -> bytes:
    """Create minimal valid JPEG bytes via PIL."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes() -> bytes:
    """Create minimal valid PNG bytes via PIL."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _mock_db_with_visit(visit_exists: bool = True) -> AsyncMock:
    """Create a mock db that returns a vet visit or None."""
    db = AsyncMock()
    mock_result = MagicMock()
    if visit_exists:
        mock_visit = MagicMock()
        mock_visit.id = uuid4()
        mock_result.scalar_one_or_none.return_value = mock_visit
    else:
        mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    return db


# ---------------------------------------------------------------------------
# validate_medical_file_size tests
# ---------------------------------------------------------------------------


class TestValidateMedicalFileSize:
    """Tests for medical file size validation."""

    def test_accepts_small_file(self) -> None:
        validate_medical_file_size(b"x" * 1000)

    def test_accepts_max_size(self) -> None:
        validate_medical_file_size(b"x" * MAX_MEDICAL_FILE_SIZE_BYTES)

    def test_rejects_oversized(self) -> None:
        content = b"x" * (MAX_MEDICAL_FILE_SIZE_BYTES + 1)
        with pytest.raises(MedicalDocumentValidationError, match="File too large"):
            validate_medical_file_size(content)


# ---------------------------------------------------------------------------
# validate_medical_mime_type tests
# ---------------------------------------------------------------------------


class TestValidateMedicalMimeType:
    """Tests for MIME type validation."""

    def test_accepts_pdf(self) -> None:
        content = _make_pdf_bytes()
        result = validate_medical_mime_type(content, "report.pdf")
        assert result == "application/pdf"

    def test_accepts_jpeg(self) -> None:
        content = _make_jpeg_bytes()
        result = validate_medical_mime_type(content, "xray.jpg")
        assert result == "image/jpeg"

    def test_accepts_png(self) -> None:
        content = _make_png_bytes()
        result = validate_medical_mime_type(content, "scan.png")
        assert result == "image/png"

    def test_rejects_text_file(self) -> None:
        with pytest.raises(MedicalDocumentValidationError, match="Invalid file type"):
            validate_medical_mime_type(b"Hello text", "file.txt")

    def test_rejects_extension_mismatch(self) -> None:
        content = _make_jpeg_bytes()
        with pytest.raises(MedicalDocumentValidationError, match="extension mismatch"):
            validate_medical_mime_type(content, "photo.pdf")


# ---------------------------------------------------------------------------
# generate_medical_storage_path tests
# ---------------------------------------------------------------------------


class TestGenerateMedicalStoragePath:
    """Tests for storage path generation."""

    def test_returns_tuple(self) -> None:
        relative, absolute = generate_medical_storage_path("doc.pdf")
        assert isinstance(relative, str)
        assert isinstance(absolute, Path)

    def test_preserves_extension(self) -> None:
        relative, _ = generate_medical_storage_path("report.pdf")
        assert relative.endswith(".pdf")

    def test_uuid_in_path(self) -> None:
        relative, _ = generate_medical_storage_path("doc.pdf")
        parts = relative.split("/")
        # year/month/day/uuid/filename
        assert len(parts) == 5
        UUID(parts[3])  # Should be valid UUID


# ---------------------------------------------------------------------------
# upload_medical_document tests
# ---------------------------------------------------------------------------


class TestUploadMedicalDocument:
    """Tests for the full upload flow."""

    @pytest.mark.asyncio
    async def test_successful_pdf_upload(self, tmp_path: Path) -> None:
        content = _make_pdf_bytes()
        db = _mock_db_with_visit(visit_exists=True)
        visit_id = uuid4()

        result = await upload_medical_document(
            content=content,
            filename="report.pdf",
            vet_visit_id=visit_id,
            document_type="surgery_report",
            description="Post-op notes",
            uploaded_by=uuid4(),
            db=db,
            upload_root=tmp_path,
        )

        assert isinstance(result, MedicalDocumentUploadResult)
        assert result.document_type == "surgery_report"
        assert result.content_type == "application/pdf"
        assert result.url.startswith("/media/medical/")

    @pytest.mark.asyncio
    async def test_successful_image_upload(self, tmp_path: Path) -> None:
        content = _make_jpeg_bytes()
        db = _mock_db_with_visit(visit_exists=True)

        result = await upload_medical_document(
            content=content,
            filename="xray.jpg",
            vet_visit_id=uuid4(),
            document_type="xray",
            description=None,
            uploaded_by=None,
            db=db,
            upload_root=tmp_path,
        )

        assert result.content_type == "image/jpeg"

    @pytest.mark.asyncio
    async def test_vet_visit_not_found(self, tmp_path: Path) -> None:
        content = _make_pdf_bytes()
        db = _mock_db_with_visit(visit_exists=False)
        visit_id = uuid4()

        with pytest.raises(VetVisitNotFoundError):
            await upload_medical_document(
                content=content,
                filename="doc.pdf",
                vet_visit_id=visit_id,
                document_type="other",
                description=None,
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

    @pytest.mark.asyncio
    async def test_rejects_oversized(self, tmp_path: Path) -> None:
        content = b"x" * (MAX_MEDICAL_FILE_SIZE_BYTES + 1)
        db = _mock_db_with_visit(visit_exists=True)

        with pytest.raises(MedicalDocumentValidationError, match="File too large"):
            await upload_medical_document(
                content=content,
                filename="big.pdf",
                vet_visit_id=uuid4(),
                document_type="other",
                description=None,
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

    @pytest.mark.asyncio
    async def test_rejects_invalid_type(self, tmp_path: Path) -> None:
        db = _mock_db_with_visit(visit_exists=True)

        with pytest.raises(MedicalDocumentValidationError, match="Invalid file type"):
            await upload_medical_document(
                content=b"not a document",
                filename="file.exe",
                vet_visit_id=uuid4(),
                document_type="other",
                description=None,
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

    @pytest.mark.asyncio
    async def test_cleans_up_on_db_failure(self, tmp_path: Path) -> None:
        content = _make_pdf_bytes()
        db = _mock_db_with_visit(visit_exists=True)
        db.flush.side_effect = RuntimeError("DB error")

        with pytest.raises(RuntimeError, match="DB error"):
            await upload_medical_document(
                content=content,
                filename="doc.pdf",
                vet_visit_id=uuid4(),
                document_type="other",
                description=None,
                uploaded_by=None,
                db=db,
                upload_root=tmp_path,
            )

        # Files should be cleaned up
        pdf_files = list(tmp_path.rglob("*.pdf"))
        assert len(pdf_files) == 0


# ---------------------------------------------------------------------------
# Error class tests
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for custom exceptions."""

    def test_validation_error(self) -> None:
        err = MedicalDocumentValidationError("bad file", details="too small")
        assert err.message == "bad file"
        assert err.details == "too small"

    def test_vet_visit_not_found(self) -> None:
        uid = uuid4()
        err = VetVisitNotFoundError(uid)
        assert err.vet_visit_id == uid
        assert str(uid) in str(err)


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_max_size(self) -> None:
        assert MAX_MEDICAL_FILE_SIZE_BYTES == 20_971_520

    def test_allowed_types(self) -> None:
        assert "application/pdf" in ALLOWED_MEDICAL_MIME_TYPES
        assert "image/jpeg" in ALLOWED_MEDICAL_MIME_TYPES
        assert "image/png" in ALLOWED_MEDICAL_MIME_TYPES
        assert len(ALLOWED_MEDICAL_MIME_TYPES) == 3

    def test_default_upload_root(self) -> None:
        assert Path("media/medical") == DEFAULT_MEDICAL_UPLOAD_ROOT
