"""Unit tests for audit trail middleware logic.

Tests the pure functions used by AuditMiddleware: path parsing,
action determination, user ID extraction, and resource mapping.
"""

from src.audit.middleware import (
    AUDITED_METHODS,
    EXCLUDED_PATHS,
    determine_action,
    extract_user_id_from_token,
    parse_resource_from_path,
)
from src.db.models.audit_log import AuditAction, ResourceType


class TestExtractUserIdFromToken:
    """Tests for JWT user ID extraction."""

    def test_returns_none_for_missing_header(self) -> None:
        from src.config import Settings

        settings = Settings()
        assert extract_user_id_from_token(None, settings) is None

    def test_returns_none_for_non_bearer_header(self) -> None:
        from src.config import Settings

        settings = Settings()
        assert extract_user_id_from_token("Basic abc123", settings) is None

    def test_returns_none_for_empty_string(self) -> None:
        from src.config import Settings

        settings = Settings()
        assert extract_user_id_from_token("", settings) is None

    def test_returns_none_for_invalid_token(self) -> None:
        from src.config import Settings

        settings = Settings()
        assert extract_user_id_from_token("Bearer invalid.jwt.token", settings) is None

    def test_returns_user_id_for_valid_token(self) -> None:
        from datetime import timedelta

        from src.auth.utils import create_access_token
        from src.config import Settings

        settings = Settings()
        token = create_access_token(
            data={"sub": "user-123"},
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
            expires_delta=timedelta(minutes=30),
        )
        result = extract_user_id_from_token(f"Bearer {token}", settings)
        assert result == "user-123"


class TestParseResourceFromPath:
    """Tests for URL path to resource type/ID parsing."""

    def test_animals_collection(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/animals")
        assert resource_type == ResourceType.ANIMAL
        assert resource_id is None

    def test_animals_with_uuid(self) -> None:
        resource_type, resource_id = parse_resource_from_path(
            "/animals/12345678-1234-1234-1234-123456789abc"
        )
        assert resource_type == ResourceType.ANIMAL
        assert resource_id == "12345678-1234-1234-1234-123456789abc"

    def test_adopters_collection(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/adopters")
        assert resource_type == ResourceType.ADOPTER
        assert resource_id is None

    def test_adoption_requests_collection(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/adoption-requests")
        assert resource_type == ResourceType.ADOPTION_REQUEST
        assert resource_id is None

    def test_donors_collection(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/donors")
        assert resource_type == ResourceType.DONOR
        assert resource_id is None

    def test_donations_collection(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/donations")
        assert resource_type == ResourceType.DONATION
        assert resource_id is None

    def test_auth_path(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/auth/users")
        assert resource_type == ResourceType.USER
        assert resource_id is None

    def test_unknown_path_returns_system(self) -> None:
        resource_type, resource_id = parse_resource_from_path("/unknown-endpoint")
        assert resource_type == ResourceType.SYSTEM
        assert resource_id is None

    def test_nested_path_with_uuid(self) -> None:
        resource_type, resource_id = parse_resource_from_path(
            "/animals/12345678-1234-1234-1234-123456789abc/photos"
        )
        assert resource_type == ResourceType.ANIMAL
        assert resource_id == "12345678-1234-1234-1234-123456789abc"


class TestDetermineAction:
    """Tests for HTTP method to audit action mapping."""

    def test_post_maps_to_create(self) -> None:
        assert determine_action("POST", "/animals") == AuditAction.CREATE

    def test_put_maps_to_update(self) -> None:
        assert determine_action("PUT", "/animals/123") == AuditAction.UPDATE

    def test_patch_maps_to_update(self) -> None:
        assert determine_action("PATCH", "/animals/123") == AuditAction.UPDATE

    def test_delete_maps_to_delete(self) -> None:
        assert determine_action("DELETE", "/animals/123") == AuditAction.DELETE

    def test_unknown_method_maps_to_read(self) -> None:
        assert determine_action("GET", "/animals") == AuditAction.READ

    def test_auth_users_post_maps_to_create(self) -> None:
        assert determine_action("POST", "/auth/users") == AuditAction.CREATE


class TestAuditedMethodsAndExcludedPaths:
    """Tests for the audited methods and excluded paths constants."""

    def test_audited_methods_include_mutating(self) -> None:
        assert "POST" in AUDITED_METHODS
        assert "PUT" in AUDITED_METHODS
        assert "PATCH" in AUDITED_METHODS
        assert "DELETE" in AUDITED_METHODS

    def test_audited_methods_exclude_read(self) -> None:
        assert "GET" not in AUDITED_METHODS
        assert "HEAD" not in AUDITED_METHODS
        assert "OPTIONS" not in AUDITED_METHODS

    def test_sensitive_paths_excluded(self) -> None:
        assert "/auth/token" in EXCLUDED_PATHS
        assert "/auth/password-reset" in EXCLUDED_PATHS
        assert "/health" in EXCLUDED_PATHS

    def test_api_paths_not_excluded(self) -> None:
        assert "/animals" not in EXCLUDED_PATHS
        assert "/adopters" not in EXCLUDED_PATHS
        assert "/donors" not in EXCLUDED_PATHS
