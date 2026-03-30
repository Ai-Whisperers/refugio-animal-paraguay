"""Adopter document upload and management endpoints.

Endpoints:
  POST   /portal/documents               -- adopter uploads a document
  GET    /portal/documents               -- adopter lists their own documents
  DELETE /portal/documents/{document_id} -- adopter deletes their own document
  GET    /adopters/{adopter_id}/documents -- staff views all documents for an adopter
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_staff
from src.db.models.adopter_document import AdopterDocumentType
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.adopter_document import (
    AdopterDocumentErrorResponse,
    AdopterDocumentListResponse,
    AdopterDocumentResponse,
    AdopterDocumentUploadResponse,
)
from src.schemas.error import COMMON_RESPONSES
from src.services.adopter_document_service import (
    DocumentStorageError,
    DocumentValidationError,
    delete_adopter_document,
    get_adopter_by_email,
    get_document_or_none,
    list_adopter_documents,
    upload_adopter_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["adopter-documents"], responses=COMMON_RESPONSES)

# Maximum file size accepted by the upload endpoint (10 MB)
MAX_UPLOAD_BYTES = 10_485_760


async def _resolve_adopter_for_user(user: User, db: AsyncSession) -> UUID:
    """Resolve the adopter ID for the authenticated user.

    Matches by email — raises 404 if no adopter profile exists for this user.
    """
    adopter = await get_adopter_by_email(user.email, db)
    if adopter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No adopter profile found for this user. Please contact the shelter.",
        )
    return adopter.id


# ---------------------------------------------------------------------------
# Adopter self-service endpoints (authenticated portal user)
# ---------------------------------------------------------------------------


@router.post(
    "/portal/documents",
    response_model=AdopterDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a supporting document",
    description=(
        "Authenticated adopter uploads a document (PDF, JPG, PNG). "
        "Documents are linked to the adopter profile matched by user email."
    ),
    responses={
        400: {"description": "Validation error", "model": AdopterDocumentErrorResponse},
        404: {"description": "No adopter profile for this user"},
        413: {"description": "File too large", "model": AdopterDocumentErrorResponse},
    },
)
async def upload_document(
    file: UploadFile,
    document_type: AdopterDocumentType = Form(default=AdopterDocumentType.OTHER),
    description: str | None = Form(default=None),
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdopterDocumentUploadResponse:
    """Upload a supporting document to the adopter's portal file collection."""
    adopter_id = await _resolve_adopter_for_user(user, db)

    content = await file.read()
    original_filename = file.filename or "upload"

    try:
        result = await upload_adopter_document(
            adopter_id=adopter_id,
            content=content,
            original_filename=original_filename,
            document_type=document_type,
            description=description,
            uploaded_by_user_id=user.id,
            db=db,
        )
    except DocumentValidationError as exc:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if "too large" in exc.message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error": "validation_error", "message": exc.message, "details": exc.details},
        ) from exc
    except DocumentStorageError as exc:
        logger.error(
            "Document storage failed",
            extra={"adopter_id": str(adopter_id), "error": exc.message},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "storage_error", "message": "Failed to store document"},
        ) from exc

    return AdopterDocumentUploadResponse(
        id=result.id,
        original_filename=result.original_filename,
        content_type=result.content_type,
        size_bytes=result.size_bytes,
        document_type=result.document_type,
        created_at=result.created_at,
    )


@router.get(
    "/portal/documents",
    response_model=AdopterDocumentListResponse,
    summary="List my uploaded documents",
    description="Return all documents uploaded by the authenticated adopter.",
)
async def list_my_documents(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdopterDocumentListResponse:
    """List documents belonging to the authenticated adopter."""
    adopter_id = await _resolve_adopter_for_user(user, db)
    documents = await list_adopter_documents(adopter_id, db)
    return AdopterDocumentListResponse(
        documents=[
            AdopterDocumentResponse(
                id=doc.id,
                adopter_id=doc.adopter_id,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                size_bytes=doc.size_bytes,
                document_type=doc.document_type,
                description=doc.description,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.delete(
    "/portal/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my document",
    description="Authenticated adopter deletes one of their own documents.",
    responses={
        403: {"description": "Document belongs to another adopter"},
        404: {"description": "Document not found"},
    },
)
async def delete_my_document(
    document_id: UUID,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document owned by the authenticated adopter."""
    adopter_id = await _resolve_adopter_for_user(user, db)
    document = await get_document_or_none(document_id, db)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.adopter_id != adopter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document",
        )

    await delete_adopter_document(document, db)


# ---------------------------------------------------------------------------
# Staff-only endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/adopters/{adopter_id}/documents",
    response_model=AdopterDocumentListResponse,
    summary="List documents for an adopter (staff)",
    description="Staff view all documents uploaded by a specific adopter.",
)
async def list_adopter_documents_staff(
    adopter_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> AdopterDocumentListResponse:
    """List all documents for a given adopter — staff access only."""
    documents = await list_adopter_documents(adopter_id, db)
    return AdopterDocumentListResponse(
        documents=[
            AdopterDocumentResponse(
                id=doc.id,
                adopter_id=doc.adopter_id,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                size_bytes=doc.size_bytes,
                document_type=doc.document_type,
                description=doc.description,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
        total=len(documents),
    )
