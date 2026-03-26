"""Unit tests for audit trail Pydantic schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.audit import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    AuditLogFilters,
    AuditLogListResponse,
    AuditLogResponse,
)


class TestAuditLogResponse:
    """Tests for AuditLogResponse schema."""

    def test_minimal_construction(self) -> None:
        resp = AuditLogResponse(
            id=uuid4(),
            user_id=uuid4(),
            action="create",
            resource_type="animals",
            timestamp=datetime.now(UTC),
        )
        assert resp.resource_id is None
        assert resp.old_values is None
        assert resp.new_values is None

    def test_full_construction(self) -> None:
        entry_id = uuid4()
        user_id = uuid4()
        now = datetime.now(UTC)
        resp = AuditLogResponse(
            id=entry_id,
            user_id=user_id,
            action="update",
            resource_type="adopters",
            resource_id=str(uuid4()),
            timestamp=now,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            old_values={"status": "pending"},
            new_values={"status": "approved"},
            request_id="req-123",
        )
        assert resp.id == entry_id
        assert resp.user_id == user_id
        assert resp.action == "update"
        assert resp.ip_address == "10.0.0.1"

    def test_serialization_roundtrip(self) -> None:
        resp = AuditLogResponse(
            id=uuid4(),
            user_id=uuid4(),
            action="delete",
            resource_type="animals",
            timestamp=datetime.now(UTC),
        )
        data = resp.model_dump(mode="json")
        restored = AuditLogResponse.model_validate(data)
        assert restored.action == "delete"


class TestAuditLogListResponse:
    """Tests for paginated response."""

    def test_empty_list(self) -> None:
        resp = AuditLogListResponse(items=[], total=0, page=1, page_size=50)
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        item = AuditLogResponse(
            id=uuid4(),
            user_id=uuid4(),
            action="create",
            resource_type="animals",
            timestamp=datetime.now(UTC),
        )
        resp = AuditLogListResponse(items=[item], total=1, page=1, page_size=50)
        assert len(resp.items) == 1


class TestAuditLogFilters:
    """Tests for query filter schema."""

    def test_defaults(self) -> None:
        filters = AuditLogFilters()
        assert filters.user_id is None
        assert filters.action is None
        assert filters.page == DEFAULT_PAGE
        assert filters.page_size == DEFAULT_PAGE_SIZE

    def test_page_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            AuditLogFilters(page=0)

    def test_page_size_cannot_exceed_max(self) -> None:
        with pytest.raises(ValidationError):
            AuditLogFilters(page_size=MAX_PAGE_SIZE + 1)

    def test_all_filters(self) -> None:
        user_id = uuid4()
        now = datetime.now(UTC)
        filters = AuditLogFilters(
            user_id=user_id,
            action="create",
            resource_type="animals",
            resource_id="abc",
            start_date=now,
            end_date=now,
            page=2,
            page_size=25,
        )
        assert filters.user_id == user_id
        assert filters.action == "create"
        assert filters.page == 2
        assert filters.page_size == 25
