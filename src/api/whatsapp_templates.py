"""WhatsApp message template registry API endpoints.

Allows staff to register and manage WhatsApp template metadata before
submitting to Meta for approval.

Endpoints:
  GET    /api/whatsapp/templates           - List templates (staff/admin)
  POST   /api/whatsapp/templates           - Register new template (staff/admin)
  GET    /api/whatsapp/templates/{id}      - Get template detail (staff/admin)
  PATCH  /api/whatsapp/templates/{id}      - Update template (staff/admin)
  DELETE /api/whatsapp/templates/{id}      - Soft-delete template (admin only)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.whatsapp_template import (
    WhatsAppTemplateCreate,
    WhatsAppTemplateListResponse,
    WhatsAppTemplateResponse,
    WhatsAppTemplateUpdate,
)
from src.services.whatsapp_template_service import (
    WhatsAppTemplateDuplicateError,
    WhatsAppTemplateNotFoundError,
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/whatsapp/templates",
    tags=["whatsapp-templates"],
    responses=COMMON_RESPONSES,
)


@router.get("", response_model=WhatsAppTemplateListResponse)
async def list_whatsapp_templates(
    status: str | None = Query(None, description="Filter by approval status"),
    category: str | None = Query(None, description="Filter by category"),
    is_active: bool = Query(True, description="Filter by active state"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> WhatsAppTemplateListResponse:
    """List all registered WhatsApp templates with optional filters.

    Requires staff or admin role.
    """
    return await list_templates(
        session,
        status=status,
        category=category,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=WhatsAppTemplateResponse, status_code=status.HTTP_201_CREATED)
async def register_whatsapp_template(
    data: WhatsAppTemplateCreate,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> WhatsAppTemplateResponse:
    """Register a new WhatsApp message template.

    The template is created with status=pending. Staff must then submit it
    to Meta Business Manager for approval before it can be sent.

    Requires staff or admin role.
    """
    try:
        return await create_template(session, data)
    except WhatsAppTemplateDuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template '{exc.name}' already exists for language '{exc.language_code}'.",
        ) from exc


@router.get("/{template_id}", response_model=WhatsAppTemplateResponse)
async def get_whatsapp_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> WhatsAppTemplateResponse:
    """Get a single WhatsApp template by ID.

    Requires staff or admin role.
    """
    try:
        return await get_template(session, template_id)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WhatsApp template {template_id} not found.",
        ) from exc


@router.patch("/{template_id}", response_model=WhatsAppTemplateResponse)
async def update_whatsapp_template(
    template_id: UUID,
    data: WhatsAppTemplateUpdate,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> WhatsAppTemplateResponse:
    """Update a WhatsApp template (status, meta_template_id, content, etc.).

    Used to record approval status updates received from Meta webhooks
    or to correct template content before submission.

    Requires staff or admin role.
    """
    try:
        return await update_template(session, template_id, data)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WhatsApp template {template_id} not found.",
        ) from exc


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whatsapp_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> None:
    """Soft-delete a WhatsApp template (sets is_active=False).

    Archived templates are excluded from active lists but preserved for audit.

    Requires admin role.
    """
    try:
        await delete_template(session, template_id)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WhatsApp template {template_id} not found.",
        ) from exc
