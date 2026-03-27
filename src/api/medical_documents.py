"""Medical documents CRUD router.

Endpoints:
  GET    /vet-visits/{visit_id}/documents              -- list documents for a visit
  GET    /medical-documents/{document_id}              -- single document
  POST   /vet-visits/{visit_id}/documents              -- create (register upload), returns 201
  DELETE /medical-documents/{document_id}              -- delete document record
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.medical import MedicalDocument, VetVisit
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.medical import (
    MedicalDocumentCreate,
    MedicalDocumentResponse,
)

router = APIRouter(tags=["medical-documents"], responses=RESOURCE_RESPONSES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_visit_or_404(visit_id: UUID, db: AsyncSession) -> VetVisit:
    """Fetch a vet visit by ID or raise 404."""
    visit = await db.get(VetVisit, visit_id)
    if visit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vet visit not found",
        )
    return visit


async def _get_document_or_404(document_id: UUID, db: AsyncSession) -> MedicalDocument:
    """Fetch a medical document by ID or raise 404."""
    doc = await db.get(MedicalDocument, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical document not found",
        )
    return doc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/vet-visits/{visit_id}/documents",
    response_model=list[MedicalDocumentResponse],
)
async def list_documents_for_visit(
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[MedicalDocument]:
    """List all medical documents for a vet visit."""
    await _get_visit_or_404(visit_id, db)
    stmt = (
        select(MedicalDocument)
        .where(MedicalDocument.vet_visit_id == visit_id)
        .order_by(MedicalDocument.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/medical-documents/{document_id}",
    response_model=MedicalDocumentResponse,
)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> MedicalDocument:
    """Get a single medical document by ID."""
    return await _get_document_or_404(document_id, db)


@router.post(
    "/vet-visits/{visit_id}/documents",
    response_model=MedicalDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    visit_id: UUID,
    payload: MedicalDocumentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> MedicalDocument:
    """Register a medical document upload for a vet visit.

    The actual file upload is handled externally (e.g., Cloudinary).
    This endpoint stores the metadata and URL reference.
    """
    await _get_visit_or_404(visit_id, db)
    doc_data = payload.model_dump(exclude_unset=True)
    document = MedicalDocument(vet_visit_id=visit_id, **doc_data)
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


@router.delete(
    "/medical-documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete a medical document record."""
    doc = await _get_document_or_404(document_id, db)
    await db.delete(doc)
    await db.flush()
