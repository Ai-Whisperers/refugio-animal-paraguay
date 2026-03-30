"""Unit tests for adopter document service functions."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.db.models.adopter_document import AdopterDocument, AdopterDocumentType
from src.services.adopter_document_service import (
    MAX_DOCUMENT_SIZE_BYTES,
    DocumentStorageError,
    DocumentValidationError,
    build_storage_path,
    delete_adopter_document,
    list_adopter_documents,
    upload_adopter_document,
    validate_document_mime_type,
    validate_document_size,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_db() -> AsyncMock:
    """Async mock DB session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


def _make_document(adopter_id: uuid.UUID | None = None) -> AdopterDocument:
    doc = MagicMock(spec=AdopterDocument)
    doc.id = uuid.uuid4()
    doc.adopter_id = adopter_id or uuid.uuid4()
    doc.original_filename = "id_document.pdf"
    doc.storage_path = "/tmp/test_doc.pdf"
    doc.content_type = "application/pdf"
    doc.size_bytes = 1024
    doc.document_type = AdopterDocumentType.IDENTITY.value
    doc.description = None
    doc.created_at = datetime.now(UTC)
    return doc


# ---------------------------------------------------------------------------
# validate_document_size
# ---------------------------------------------------------------------------


class TestValidateDocumentSize:
    def test_passes_for_small_file(self) -> None:
        content = b"x" * 100
        validate_document_size(content)  # should not raise

    def test_passes_at_exact_limit(self) -> None:
        content = b"x" * MAX_DOCUMENT_SIZE_BYTES
        validate_document_size(content)  # should not raise

    def test_raises_for_oversized_file(self) -> None:
        content = b"x" * (MAX_DOCUMENT_SIZE_BYTES + 1)
        with pytest.raises(DocumentValidationError) as exc_info:
            validate_document_size(content)
        assert "too large" in exc_info.value.message.lower()


# ---------------------------------------------------------------------------
# validate_document_mime_type
# ---------------------------------------------------------------------------


class TestValidateDocumentMimeType:
    def test_accepts_pdf(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            result = validate_document_mime_type(b"fake pdf", "document.pdf")
        assert result == "application/pdf"

    def test_accepts_jpeg(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "image/jpeg"
            result = validate_document_mime_type(b"fake jpeg", "photo.jpg")
        assert result == "image/jpeg"

    def test_accepts_png(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "image/png"
            result = validate_document_mime_type(b"fake png", "photo.png")
        assert result == "image/png"

    def test_rejects_unsupported_type(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/zip"
            with pytest.raises(DocumentValidationError) as exc_info:
                validate_document_mime_type(b"fake zip", "archive.zip")
        assert "Unsupported file type" in exc_info.value.message

    def test_rejects_extension_mismatch(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            with pytest.raises(DocumentValidationError) as exc_info:
                validate_document_mime_type(b"fake pdf", "image.png")
        assert "extension does not match" in exc_info.value.message.lower()

    def test_accepts_file_without_extension(self) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            result = validate_document_mime_type(b"fake pdf", "noextension")
        assert result == "application/pdf"


# ---------------------------------------------------------------------------
# build_storage_path
# ---------------------------------------------------------------------------


class TestBuildStoragePath:
    def test_returns_path_with_adopter_and_date(self) -> None:
        adopter_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        document_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        root = Path("/tmp/test_docs")

        path = build_storage_path(adopter_id, document_id, "pdf", root)

        assert str(adopter_id) in str(path)
        assert str(document_id) in str(path)
        assert path.suffix == ".pdf"
        assert str(root) in str(path)


# ---------------------------------------------------------------------------
# upload_adopter_document
# ---------------------------------------------------------------------------


class TestUploadAdopterDocument:
    @pytest.mark.asyncio()
    async def test_raises_on_oversized_file(self, mock_db: AsyncMock) -> None:
        content = b"x" * (MAX_DOCUMENT_SIZE_BYTES + 1)
        adopter_id = uuid.uuid4()
        with pytest.raises(DocumentValidationError) as exc_info:
            await upload_adopter_document(
                adopter_id=adopter_id,
                content=content,
                original_filename="big.pdf",
                document_type=AdopterDocumentType.IDENTITY,
                description=None,
                uploaded_by_user_id=None,
                db=mock_db,
            )
        assert "too large" in exc_info.value.message.lower()

    @pytest.mark.asyncio()
    async def test_raises_on_invalid_mime(self, mock_db: AsyncMock) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/x-executable"
            with pytest.raises(DocumentValidationError) as exc_info:
                await upload_adopter_document(
                    adopter_id=uuid.uuid4(),
                    content=b"binary content",
                    original_filename="malware.exe",
                    document_type=AdopterDocumentType.OTHER,
                    description=None,
                    uploaded_by_user_id=None,
                    db=mock_db,
                )
        assert "Unsupported file type" in exc_info.value.message

    @pytest.mark.asyncio()
    async def test_raises_storage_error_on_write_failure(
        self, mock_db: AsyncMock, tmp_path: Path
    ) -> None:
        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            with patch(
                "src.services.adopter_document_service.build_storage_path"
            ) as mock_path_builder:
                bad_path = MagicMock(spec=Path)
                bad_path.parent = MagicMock()
                bad_path.parent.mkdir = MagicMock()
                bad_path.write_bytes = MagicMock(side_effect=OSError("disk full"))
                mock_path_builder.return_value = bad_path

                with pytest.raises(DocumentStorageError):
                    await upload_adopter_document(
                        adopter_id=uuid.uuid4(),
                        content=b"pdf content",
                        original_filename="doc.pdf",
                        document_type=AdopterDocumentType.IDENTITY,
                        description=None,
                        uploaded_by_user_id=None,
                        db=mock_db,
                        upload_root=tmp_path,
                    )

    @pytest.mark.asyncio()
    async def test_successful_upload_persists_record(
        self, mock_db: AsyncMock, tmp_path: Path
    ) -> None:
        adopter_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_db.refresh = AsyncMock(side_effect=lambda doc: None)

        with patch("src.services.adopter_document_service.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"

            result = await upload_adopter_document(
                adopter_id=adopter_id,
                content=b"PDF content here",
                original_filename="identification.pdf",
                document_type=AdopterDocumentType.IDENTITY,
                description="My national ID",
                uploaded_by_user_id=user_id,
                db=mock_db,
                upload_root=tmp_path,
            )

        # DB operations were called
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result.original_filename == "identification.pdf"
        assert result.content_type == "application/pdf"
        assert result.document_type == AdopterDocumentType.IDENTITY.value


# ---------------------------------------------------------------------------
# list_adopter_documents
# ---------------------------------------------------------------------------


class TestListAdopterDocuments:
    @pytest.mark.asyncio()
    async def test_returns_empty_list(self, mock_db: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await list_adopter_documents(uuid.uuid4(), mock_db)
        assert result == []

    @pytest.mark.asyncio()
    async def test_returns_documents_for_adopter(self, mock_db: AsyncMock) -> None:
        adopter_id = uuid.uuid4()
        doc1 = _make_document(adopter_id)
        doc2 = _make_document(adopter_id)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [doc1, doc2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await list_adopter_documents(adopter_id, mock_db)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# delete_adopter_document
# ---------------------------------------------------------------------------


class TestDeleteAdopterDocument:
    @pytest.mark.asyncio()
    async def test_deletes_record_and_file(self, mock_db: AsyncMock, tmp_path: Path) -> None:
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")

        doc = _make_document()
        doc.storage_path = str(test_file)

        await delete_adopter_document(doc, mock_db)

        mock_db.delete.assert_called_once_with(doc)
        mock_db.flush.assert_called_once()
        assert not test_file.exists()

    @pytest.mark.asyncio()
    async def test_continues_if_file_missing(self, mock_db: AsyncMock) -> None:
        doc = _make_document()
        doc.storage_path = "/nonexistent/path/doc.pdf"

        await delete_adopter_document(doc, mock_db)

        mock_db.delete.assert_called_once_with(doc)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio()
    async def test_logs_warning_on_deletion_failure(
        self, mock_db: AsyncMock, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"content")

        doc = _make_document()
        doc.storage_path = str(test_file)

        with patch("src.services.adopter_document_service.Path") as mock_path_cls:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.unlink = MagicMock(side_effect=OSError("permission denied"))
            mock_path_cls.return_value = mock_path_instance

            await delete_adopter_document(doc, mock_db)

        # Should still delete the DB record despite file error
        mock_db.delete.assert_called_once_with(doc)
