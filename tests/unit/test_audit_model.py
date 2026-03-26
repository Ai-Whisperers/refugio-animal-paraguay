"""Unit tests for AuditLog model and AuditAction enum."""

from uuid import uuid4

from src.db.models.audit_log import AuditAction, AuditLog


class TestAuditAction:
    """Tests for the AuditAction enum."""

    def test_all_expected_actions_exist(self) -> None:
        expected = {
            "create",
            "read",
            "update",
            "delete",
            "approve",
            "reject",
            "assign",
            "export",
            "generate_report",
            "login",
            "logout",
        }
        actual = {a.value for a in AuditAction}
        assert actual == expected

    def test_action_is_string_enum(self) -> None:
        assert isinstance(AuditAction.CREATE, str)
        assert AuditAction.CREATE == "create"

    def test_action_count(self) -> None:
        assert len(AuditAction) == 11


class TestAuditLogModel:
    """Tests for the AuditLog ORM model."""

    def test_tablename(self) -> None:
        assert AuditLog.__tablename__ == "audit_logs"

    def test_instantiate_with_required_fields(self) -> None:
        user_id = uuid4()
        entry = AuditLog(
            user_id=user_id,
            action="create",
            resource_type="animals",
        )
        assert entry.user_id == user_id
        assert entry.action == "create"
        assert entry.resource_type == "animals"

    def test_optional_fields_default_to_none(self) -> None:
        entry = AuditLog(
            user_id=uuid4(),
            action="update",
            resource_type="adopters",
        )
        assert entry.resource_id is None
        assert entry.ip_address is None
        assert entry.user_agent is None
        assert entry.old_values is None
        assert entry.new_values is None
        assert entry.request_id is None

    def test_optional_fields_accept_values(self) -> None:
        resource_id = str(uuid4())
        entry = AuditLog(
            user_id=uuid4(),
            action="delete",
            resource_type="animals",
            resource_id=resource_id,
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
            request_id="abc-123",
        )
        assert entry.resource_id == resource_id
        assert entry.ip_address == "192.168.1.1"
        assert entry.user_agent == "TestAgent/1.0"
        assert entry.old_values == {"name": "Old Name"}
        assert entry.new_values == {"name": "New Name"}
        assert entry.request_id == "abc-123"

    def test_table_has_expected_indexes(self) -> None:
        index_names = {idx.name for idx in AuditLog.__table__.indexes}
        assert "ix_audit_logs_user_timestamp" in index_names
        assert "ix_audit_logs_resource_timestamp" in index_names
        assert "ix_audit_logs_timestamp" in index_names
