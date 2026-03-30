"""Pydantic schemas for adopter document upload and retrieval."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdopterDocumentResponse(BaseModel):
    """Shape returned for every adopter document record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    adopter_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    document_type: str
    description: str | None
    created_at: datetime


class AdopterDocumentListResponse(BaseModel):
    """Paginated list of adopter documents."""

    documents: list[AdopterDocumentResponse]
    total: int


class AdopterDocumentUploadResponse(BaseModel):
    """Response returned immediately after a successful upload."""

    id: UUID = Field(..., description="Document record ID")
    original_filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="Detected MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    document_type: str = Field(..., description="Document category")
    created_at: datetime = Field(..., description="Upload timestamp")


class AdopterDocumentErrorResponse(BaseModel):
    """Structured error response for document upload failures."""

    error: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    details: str | None = Field(None, description="Additional error details")
