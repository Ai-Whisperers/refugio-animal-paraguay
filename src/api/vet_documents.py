"""Medical document upload endpoint for vet visits.

Endpoints:
  POST /api/vet-visits/{vet_visit_id}/documents/upload  — upload medical doc
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.vet_document import DocumentType
from src.db.session import get_db
from src.services.medical_document_service import (
    MedicalDocumentValidationError,
    VetVisitNotFoundError,
    upload_medical_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/vet-visits",
    tags=["vet-documents"],
)


class VetDocumentResponse(BaseModel):
    """Response schema for a medical document upload."""

    id: UUID = Field(..., description="Document record ID")
    document_type: str = Field(..., description="Type of medical document")
    url: str = Field(..., description="Path to serve the document")
    original_filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Detected MIME type")


@router.post(
    "/{vet_visit_id}/documents/upload",
    response_model=VetDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a medical document",
    description="Upload a medical document (PDF, JPG, PNG) and link to a vet visit.",
)
async def upload_vet_document(
    vet_visit_id: UUID,
    file: UploadFile,
    document_type: str = Form(default=DocumentType.OTHER.value),
    description: str | None = Form(default=None),
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> VetDocumentResponse:
    """Upload and validate a medical document, linking it to a vet visit."""
    if file.filename is None or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": "Filename is required"},
        )

    # Validate document_type
    valid_types = {dt.value for dt in DocumentType}
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid document type. Must be one of: {', '.join(sorted(valid_types))}",
            },
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": "Empty file"},
        )

    try:
        result = await upload_medical_document(
            content=content,
            filename=file.filename,
            vet_visit_id=vet_visit_id,
            document_type=document_type,
            description=description,
            uploaded_by=current_user.id,
            db=db,
        )
    except VetVisitNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Vet visit {vet_visit_id} not found"},
        ) from None
    except MedicalDocumentValidationError as exc:
        if "too large" in exc.message.lower():
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()

    return VetDocumentResponse(
        id=result.id,
        document_type=result.document_type,
        url=result.url,
        original_filename=result.original_filename,
        size_bytes=result.size_bytes,
        content_type=result.content_type,
    )
