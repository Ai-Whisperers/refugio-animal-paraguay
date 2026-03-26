"""Unit tests for audit trail middleware utilities."""

from src.audit.middleware import (
    AUDITABLE_METHODS,
    EXCLUDED_PATHS,
    METHOD_TO_ACTION,
    _extract_resource_info,
)


class TestExtractResourceInfo:
    """Tests for URL path parsing into resource type and ID."""

    def test_simple_resource_path(self) -> None:
        resource_type, resource_id = _extract_resource_info("/animals")
        assert resource_type == "animals"
        assert resource_id is None

    def test_resource_with_uuid_id(self) -> None:
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        resource_type, resource_id = _extract_resource_info(f"/animals/{test_uuid}")
        assert resource_type == "animals"
        assert resource_id == test_uuid

    def test_nested_resource_without_id(self) -> None:
        resource_type, resource_id = _extract_resource_info("/auth/token")
        assert resource_type == "auth.token"
        assert resource_id is None

    def test_nested_resource_with_id(self) -> None:
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        resource_type, resource_id = _extract_resource_info(f"/admin/audit-logs/{test_uuid}")
        assert resource_type == "admin.audit-logs"
        assert resource_id == test_uuid

    def test_empty_path(self) -> None:
        resource_type, resource_id = _extract_resource_info("/")
        assert resource_type == "unknown"
        assert resource_id is None

    def test_trailing_slash(self) -> None:
        resource_type, resource_id = _extract_resource_info("/animals/")
        assert resource_type == "animals"
        assert resource_id is None


class TestConstants:
    """Verify audit middleware configuration constants."""

    def test_auditable_methods_are_write_operations(self) -> None:
        assert {"POST", "PUT", "PATCH", "DELETE"} == AUDITABLE_METHODS

    def test_health_is_excluded(self) -> None:
        assert "/health" in EXCLUDED_PATHS

    def test_method_to_action_mapping(self) -> None:
        assert METHOD_TO_ACTION["POST"] == "create"
        assert METHOD_TO_ACTION["PUT"] == "update"
        assert METHOD_TO_ACTION["PATCH"] == "update"
        assert METHOD_TO_ACTION["DELETE"] == "delete"
