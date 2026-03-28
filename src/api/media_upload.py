"""Media upload endpoint — multipart file upload with validation.

Endpoints:
  POST /api/media/upload  — upload a single image file (staff auth required)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.media_upload_service import (
    MediaStorageError,
    MediaValidationError,
    upload_media,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/media",
    tags=["media"],
)


class MediaUploadResponse(BaseModel):
    """Response schema for a successful media upload."""

    id: UUID = Field(..., description="Media record ID")
    url: str = Field(..., description="Path to serve the uploaded file")
    thumbnail_url: str | None = Field(None, description="Path to thumbnail (if generated)")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Detected MIME type")
    original_filename: str = Field(..., description="Original upload filename")


class MediaErrorResponse(BaseModel):
    """Structured error response for upload failures."""

    error: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    details: str | None = Field(None, description="Additional error details")


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file",
    description="Upload a single image file (jpg, png, webp). Max 10MB.",
    responses={
        400: {"description": "Validation error", "model": MediaErrorResponse},
        413: {"description": "File too large", "model": MediaErrorResponse},
        500: {"description": "Storage failure", "model": MediaErrorResponse},
    },
)
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> MediaUploadResponse:
    """Upload and validate a single image file."""
    if file.filename is None or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": "Filename is required"},
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": "Empty file"},
        )

    try:
        result = await upload_media(
            content=content,
            filename=file.filename,
            uploaded_by=current_user.id,
            db=db,
        )
    except MediaValidationError as exc:
        # Distinguish size errors (413) from other validation errors (400)
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
    except MediaStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "storage_error",
                "message": exc.message,
            },
        ) from None

    await db.commit()

    return MediaUploadResponse(
        id=result.id,
        url=result.url,
        thumbnail_url=result.thumbnail_url,
        width=result.width,
        height=result.height,
        size_bytes=result.size_bytes,
        content_type=result.content_type,
        original_filename=result.original_filename,
    )
