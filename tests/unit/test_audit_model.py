"""Unit tests for the AuditLog model, enums, and mappings."""

from src.db.models.audit_log import (
    HTTP_METHOD_TO_ACTION,
    PATH_TO_RESOURCE_TYPE,
    AuditAction,
    AuditLog,
    ResourceType,
)


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
            "login",
            "logout",
        }
        actual = {a.value for a in AuditAction}
        assert actual == expected

    def test_enum_values_are_lowercase(self) -> None:
        for action in AuditAction:
            assert action.value == action.value.lower()

    def test_is_str_enum(self) -> None:
        assert isinstance(AuditAction.CREATE, str)
        assert AuditAction.CREATE == "create"


class TestResourceType:
    """Tests for the ResourceType enum."""

    def test_all_expected_types_exist(self) -> None:
        expected = {
            "animal",
            "adopter",
            "adoption_request",
            "donor",
            "donation",
            "user",
            "photo",
            "system",
        }
        actual = {r.value for r in ResourceType}
        assert actual == expected

    def test_is_str_enum(self) -> None:
        assert isinstance(ResourceType.ANIMAL, str)
        assert ResourceType.ANIMAL == "animal"


class TestHTTPMethodToActionMapping:
    """Tests for the HTTP method to audit action mapping."""

    def test_post_maps_to_create(self) -> None:
        assert HTTP_METHOD_TO_ACTION["POST"] == AuditAction.CREATE

    def test_put_maps_to_update(self) -> None:
        assert HTTP_METHOD_TO_ACTION["PUT"] == AuditAction.UPDATE

    def test_patch_maps_to_update(self) -> None:
        assert HTTP_METHOD_TO_ACTION["PATCH"] == AuditAction.UPDATE

    def test_delete_maps_to_delete(self) -> None:
        assert HTTP_METHOD_TO_ACTION["DELETE"] == AuditAction.DELETE

    def test_get_not_in_mapping(self) -> None:
        assert "GET" not in HTTP_METHOD_TO_ACTION


class TestPathToResourceTypeMapping:
    """Tests for the URL path prefix to resource type mapping."""

    def test_animals_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/animals"] == ResourceType.ANIMAL

    def test_adopters_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/adopters"] == ResourceType.ADOPTER

    def test_adoption_requests_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/adoption-requests"] == ResourceType.ADOPTION_REQUEST

    def test_donors_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/donors"] == ResourceType.DONOR

    def test_donations_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/donations"] == ResourceType.DONATION

    def test_auth_path(self) -> None:
        assert PATH_TO_RESOURCE_TYPE["/auth"] == ResourceType.USER

    def test_mapping_covers_all_api_routes(self) -> None:
        assert len(PATH_TO_RESOURCE_TYPE) == 6


class TestAuditLogModel:
    """Tests for the AuditLog ORM model structure."""

    def test_tablename(self) -> None:
        assert AuditLog.__tablename__ == "audit_logs"

    def test_has_required_columns(self) -> None:
        column_names = {c.name for c in AuditLog.__table__.columns}
        expected = {
            "id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "ip_address",
            "user_agent",
            "http_method",
            "path",
            "status_code",
            "old_values",
            "new_values",
        }
        assert expected.issubset(column_names)

    def test_id_is_primary_key(self) -> None:
        assert AuditLog.__table__.c.id.primary_key

    def test_user_id_is_indexed(self) -> None:
        assert AuditLog.__table__.c.user_id.index

    def test_timestamp_is_indexed(self) -> None:
        assert AuditLog.__table__.c.timestamp.index
