"""Service layer for WhatsApp message template registry (RAP-201).

Provides CRUD operations for WhatsApp templates. Templates must be registered
here before they can be submitted to Meta for approval and subsequently sent
via the MetaWhatsAppService.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.whatsapp_template import WhatsAppTemplate
from src.schemas.whatsapp_template import (
    WhatsAppTemplateCreate,
    WhatsAppTemplateListResponse,
    WhatsAppTemplateResponse,
    WhatsAppTemplateUpdate,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class WhatsAppTemplateNotFoundError(Exception):
    """Raised when a requested template does not exist."""

    def __init__(self, template_id: UUID) -> None:
        self.template_id = template_id
        super().__init__(f"WhatsApp template {template_id} not found")


class WhatsAppTemplateDuplicateError(Exception):
    """Raised when creating a template with a name/language that already exists."""

    def __init__(self, name: str, language_code: str) -> None:
        self.name = name
        self.language_code = language_code
        super().__init__(
            f"WhatsApp template '{name}' already exists for language '{language_code}'"
        )


async def create_template(
    session: AsyncSession,
    data: WhatsAppTemplateCreate,
) -> WhatsAppTemplateResponse:
    """Create a new WhatsApp template record.

    Raises WhatsAppTemplateDuplicateError if a template with the same
    name and language_code already exists.
    """
    existing = await session.execute(
        select(WhatsAppTemplate).where(
            WhatsAppTemplate.name == data.name,
            WhatsAppTemplate.language_code == data.language_code,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise WhatsAppTemplateDuplicateError(data.name, data.language_code)

    template = WhatsAppTemplate(
        name=data.name,
        language_code=data.language_code,
        category=data.category,
        header_text=data.header_text,
        body_text=data.body_text,
        footer_text=data.footer_text,
        description=data.description,
        status="pending",
        is_active=True,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    logger.info("Created WhatsApp template: name=%s lang=%s", template.name, template.language_code)
    return WhatsAppTemplateResponse.model_validate(template)


async def get_template(
    session: AsyncSession,
    template_id: UUID,
) -> WhatsAppTemplateResponse:
    """Fetch a single template by ID.

    Raises WhatsAppTemplateNotFoundError if not found.
    """
    result = await session.execute(
        select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise WhatsAppTemplateNotFoundError(template_id)
    return WhatsAppTemplateResponse.model_validate(template)


async def list_templates(
    session: AsyncSession,
    *,
    status: str | None = None,
    category: str | None = None,
    is_active: bool | None = True,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> WhatsAppTemplateListResponse:
    """Return a paginated list of templates with optional filters."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    query = select(WhatsAppTemplate)
    count_query = select(func.count()).select_from(WhatsAppTemplate)

    if status is not None:
        query = query.where(WhatsAppTemplate.status == status)
        count_query = count_query.where(WhatsAppTemplate.status == status)
    if category is not None:
        query = query.where(WhatsAppTemplate.category == category)
        count_query = count_query.where(WhatsAppTemplate.category == category)
    if is_active is not None:
        query = query.where(WhatsAppTemplate.is_active == is_active)
        count_query = count_query.where(WhatsAppTemplate.is_active == is_active)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(WhatsAppTemplate.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(query)
    templates = result.scalars().all()

    return WhatsAppTemplateListResponse(
        items=[WhatsAppTemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_template(
    session: AsyncSession,
    template_id: UUID,
    data: WhatsAppTemplateUpdate,
) -> WhatsAppTemplateResponse:
    """Apply a partial update to a template.

    Raises WhatsAppTemplateNotFoundError if not found.
    """
    result = await session.execute(
        select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise WhatsAppTemplateNotFoundError(template_id)

    update_data = data.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(template, field_name, value)

    await session.commit()
    await session.refresh(template)
    logger.info("Updated WhatsApp template: id=%s fields=%s", template_id, list(update_data.keys()))
    return WhatsAppTemplateResponse.model_validate(template)


async def delete_template(
    session: AsyncSession,
    template_id: UUID,
) -> None:
    """Soft-delete a template by setting is_active=False.

    Raises WhatsAppTemplateNotFoundError if not found.
    """
    result = await session.execute(
        select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise WhatsAppTemplateNotFoundError(template_id)

    template.is_active = False
    await session.commit()
    logger.info("Soft-deleted WhatsApp template: id=%s", template_id)
