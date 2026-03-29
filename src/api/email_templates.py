"""Email template management endpoints (staff/admin only).

Endpoints:
  POST   /email-templates          — create a new template
  GET    /email-templates          — list templates
  GET    /email-templates/{id}     — get template detail
  PATCH  /email-templates/{id}     — update template
  DELETE /email-templates/{id}     — archive template
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.email_template import EmailTemplate, TemplateStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateSummary,
    EmailTemplateUpdate,
)
from src.schemas.error import RESOURCE_RESPONSES

router = APIRouter(
    prefix="/email-templates",
    tags=["email-templates"],
    responses=RESOURCE_RESPONSES,
)


@router.post("", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> EmailTemplate:
    """Create a new email template. Staff or admin only."""
    template = EmailTemplate(
        name=payload.name,
        description=payload.description,
        subject=payload.subject,
        html_body=payload.html_body,
        text_body=payload.text_body,
        status=TemplateStatus.DRAFT.value,
        created_by_id=current_user.id,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


@router.get("", response_model=list[EmailTemplateSummary])
async def list_templates(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[EmailTemplate]:
    """List email templates. Optionally filter by status."""
    stmt = select(EmailTemplate)
    if status_filter:
        stmt = stmt.where(EmailTemplate.status == status_filter)
    stmt = stmt.order_by(EmailTemplate.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailTemplate:
    """Get email template detail."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )
    return template


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: UUID,
    payload: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailTemplate:
    """Update an email template. Staff or admin only."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> None:
    """Archive an email template (soft delete). Staff or admin only."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )
    template.status = TemplateStatus.ARCHIVED.value
    await db.flush()
