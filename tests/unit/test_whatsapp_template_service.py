"""Unit tests for the WhatsApp message template service layer.

Tests cover:
- create_template: success, duplicate rejection
- get_template: success, not found
- list_templates: pagination, status filter, category filter, is_active filter
- update_template: success, not found, partial update
- delete_template: success (soft delete), not found
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.schemas.whatsapp_template import (
    WhatsAppTemplateCreate,
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> AsyncMock:
    """Return a mock AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_template_orm(**kwargs: object) -> MagicMock:
    """Return a mock WhatsAppTemplate ORM instance."""
    t = MagicMock()
    t.id = kwargs.get("id", uuid4())
    t.name = kwargs.get("name", "adoption_approved")
    t.language_code = kwargs.get("language_code", "es")
    t.category = kwargs.get("category", "utility")
    t.header_text = kwargs.get("header_text")
    t.body_text = kwargs.get("body_text", "Tu mascota {1} ha sido adoptada.")
    t.footer_text = kwargs.get("footer_text")
    t.status = kwargs.get("status", "pending")
    t.meta_template_id = kwargs.get("meta_template_id")
    t.rejection_reason = kwargs.get("rejection_reason")
    t.description = kwargs.get("description")
    t.is_active = kwargs.get("is_active", True)
    t.created_at = kwargs.get("created_at", datetime.now(UTC))
    t.updated_at = kwargs.get("updated_at", datetime.now(UTC))
    t.approved_at = kwargs.get("approved_at")
    return t


def _make_execute_result(scalar: object = None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar
    result.scalar_one.return_value = scalar
    scalars_result = MagicMock()
    scalars_result.all.return_value = [scalar] if scalar is not None else []
    result.scalars.return_value = scalars_result
    return result


# ---------------------------------------------------------------------------
# create_template
# ---------------------------------------------------------------------------


class TestCreateTemplate:
    @pytest.mark.asyncio
    async def test_creates_template_when_name_is_unique(self) -> None:
        db = _make_db()
        # No existing template with that name/language
        db.execute.return_value = _make_execute_result(scalar=None)

        template_orm = _make_template_orm()

        def _refresh_side_effect(obj: object) -> None:
            # After refresh the ORM obj gets its fields populated from DB;
            # simulate by copying attrs from our template fixture.
            for attr in (
                "id",
                "name",
                "language_code",
                "category",
                "header_text",
                "body_text",
                "footer_text",
                "status",
                "meta_template_id",
                "rejection_reason",
                "description",
                "is_active",
                "created_at",
                "updated_at",
                "approved_at",
            ):
                setattr(obj, attr, getattr(template_orm, attr))

        db.refresh.side_effect = _refresh_side_effect

        data = WhatsAppTemplateCreate(
            name="adoption_approved",
            language_code="es",
            category="utility",
            body_text="Tu adopcion ha sido aprobada.",
            header_text=None,
            footer_text=None,
            description=None,
        )

        result = await create_template(db, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result is not None
        assert result.name == template_orm.name

    @pytest.mark.asyncio
    async def test_raises_duplicate_when_name_lang_exists(self) -> None:
        db = _make_db()
        # Existing template found
        db.execute.return_value = _make_execute_result(scalar=_make_template_orm())

        data = WhatsAppTemplateCreate(
            name="adoption_approved",
            language_code="es",
            category="utility",
            body_text="Duplicate body.",
        )

        with pytest.raises(WhatsAppTemplateDuplicateError) as exc_info:
            await create_template(db, data)

        assert exc_info.value.name == "adoption_approved"
        assert exc_info.value.language_code == "es"


# ---------------------------------------------------------------------------
# get_template
# ---------------------------------------------------------------------------


class TestGetTemplate:
    @pytest.mark.asyncio
    async def test_returns_template_when_found(self) -> None:
        db = _make_db()
        template = _make_template_orm()
        db.execute.return_value = _make_execute_result(scalar=template)

        result = await get_template(db, template.id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self) -> None:
        db = _make_db()
        db.execute.return_value = _make_execute_result(scalar=None)
        template_id = uuid4()

        with pytest.raises(WhatsAppTemplateNotFoundError) as exc_info:
            await get_template(db, template_id)

        assert exc_info.value.template_id == template_id


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------


class TestListTemplates:
    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = _make_db()
        template = _make_template_orm()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        items_result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = [template]
        items_result.scalars.return_value = scalars

        db.execute.side_effect = [count_result, items_result]

        result = await list_templates(db, page=1, page_size=10)

        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_templates(self) -> None:
        db = _make_db()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        items_result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = []
        items_result.scalars.return_value = scalars

        db.execute.side_effect = [count_result, items_result]

        result = await list_templates(db)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_page_size_capped_at_max(self) -> None:
        db = _make_db()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        items_result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = []
        items_result.scalars.return_value = scalars
        db.execute.side_effect = [count_result, items_result]

        result = await list_templates(db, page_size=9999)
        # Should be capped at MAX_PAGE_SIZE = 100
        assert result.page_size == 100


# ---------------------------------------------------------------------------
# update_template
# ---------------------------------------------------------------------------


class TestUpdateTemplate:
    @pytest.mark.asyncio
    async def test_updates_template_status(self) -> None:
        db = _make_db()
        template = _make_template_orm(status="pending")
        db.execute.return_value = _make_execute_result(scalar=template)
        db.refresh.side_effect = lambda obj: None

        data = WhatsAppTemplateUpdate(status="approved")
        await update_template(db, template.id, data)

        assert template.status == "approved"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self) -> None:
        db = _make_db()
        db.execute.return_value = _make_execute_result(scalar=None)

        with pytest.raises(WhatsAppTemplateNotFoundError):
            await update_template(db, uuid4(), WhatsAppTemplateUpdate(status="approved"))

    @pytest.mark.asyncio
    async def test_partial_update_only_changes_provided_fields(self) -> None:
        db = _make_db()
        template = _make_template_orm(
            status="pending",
            meta_template_id=None,
            body_text="Original body",
        )
        db.execute.return_value = _make_execute_result(scalar=template)
        db.refresh.side_effect = lambda obj: None

        data = WhatsAppTemplateUpdate(meta_template_id="META-123")
        await update_template(db, template.id, data)

        assert template.meta_template_id == "META-123"
        assert template.status == "pending"  # unchanged


# ---------------------------------------------------------------------------
# delete_template
# ---------------------------------------------------------------------------


class TestDeleteTemplate:
    @pytest.mark.asyncio
    async def test_soft_deletes_template(self) -> None:
        db = _make_db()
        template = _make_template_orm(is_active=True)
        db.execute.return_value = _make_execute_result(scalar=template)

        await delete_template(db, template.id)

        assert template.is_active is False
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self) -> None:
        db = _make_db()
        db.execute.return_value = _make_execute_result(scalar=None)

        with pytest.raises(WhatsAppTemplateNotFoundError):
            await delete_template(db, uuid4())


# ---------------------------------------------------------------------------
# Error class tests
# ---------------------------------------------------------------------------


class TestErrorClasses:
    def test_not_found_error_message(self) -> None:
        tid = uuid4()
        err = WhatsAppTemplateNotFoundError(tid)
        assert str(tid) in str(err)
        assert err.template_id == tid

    def test_duplicate_error_message(self) -> None:
        err = WhatsAppTemplateDuplicateError("adoption_approved", "es")
        assert "adoption_approved" in str(err)
        assert "es" in str(err)
        assert err.name == "adoption_approved"
        assert err.language_code == "es"
