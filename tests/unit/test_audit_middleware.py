"""Unit tests for audit trail middleware utilities."""

from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.audit.middleware import (
    AUDITABLE_METHODS,
    EXCLUDED_PATHS,
    METHOD_TO_ACTION,
    AuditMiddleware,
    _extract_resource_info,
    _extract_user_id_from_token,
)
from src.auth.utils import create_access_token
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

_TEST_SECRET = "test-secret-key-for-audit-middleware-unit-tests"
_TEST_ALGORITHM = "HS256"


def _make_token(user_id: str | None = None) -> str:
    """Create a signed JWT with the given sub (user_id)."""
    uid = user_id or str(uuid4())
    return create_access_token(
        data={"sub": uid},
        secret_key=_TEST_SECRET,
        algorithm=_TEST_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )


def _make_fake_db_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _patch_audit_db(session: MagicMock):
    @asynccontextmanager
    async def _fake():
        yield session

    return patch("src.audit.middleware.get_async_session", _fake)


def _patch_settings(secret_key: str = _TEST_SECRET, algorithm: str = _TEST_ALGORITHM):
    settings = MagicMock()
    settings.secret_key = secret_key
    settings.algorithm = algorithm
    return patch("src.audit.middleware.get_settings", return_value=settings)


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

    def test_three_segment_path_where_third_is_not_uuid(self) -> None:
        # /admin/audit-logs/export — third segment is a string, not a UUID
        resource_type, resource_id = _extract_resource_info("/admin/audit-logs/export")
        assert resource_type == "admin.audit-logs"
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


# ---------------------------------------------------------------------------
# _extract_user_id_from_token
# ---------------------------------------------------------------------------


class TestExtractUserIdFromToken:
    """Test JWT extraction from Authorization header."""

    def test_returns_uuid_for_valid_bearer_token(self) -> None:
        user_id = str(uuid4())
        token = _make_token(user_id)
        request = MagicMock()
        request.headers = {"authorization": f"Bearer {token}"}

        with _patch_settings():
            result = _extract_user_id_from_token(request)

        assert result is not None
        assert str(result) == user_id

    def test_returns_none_when_no_auth_header(self) -> None:
        request = MagicMock()
        request.headers = {}

        with _patch_settings():
            result = _extract_user_id_from_token(request)

        assert result is None

    def test_returns_none_when_auth_is_not_bearer(self) -> None:
        request = MagicMock()
        request.headers = {"authorization": "Basic dXNlcjpwYXNz"}

        with _patch_settings():
            result = _extract_user_id_from_token(request)

        assert result is None

    def test_returns_none_for_invalid_token(self) -> None:
        request = MagicMock()
        request.headers = {"authorization": "Bearer not-a-real-token"}

        with _patch_settings():
            result = _extract_user_id_from_token(request)

        assert result is None

    def test_returns_none_when_sub_is_missing(self) -> None:
        from jose import jwt

        token = jwt.encode({"data": "no-sub"}, _TEST_SECRET, algorithm=_TEST_ALGORITHM)
        request = MagicMock()
        request.headers = {"authorization": f"Bearer {token}"}

        with _patch_settings():
            result = _extract_user_id_from_token(request)

        assert result is None


# ---------------------------------------------------------------------------
# AuditMiddleware.dispatch
# ---------------------------------------------------------------------------


def _build_app(response_status: int = 200) -> Starlette:
    """Build a minimal Starlette app wrapped with AuditMiddleware."""

    async def _endpoint(_request: Request) -> JSONResponse:
        return JSONResponse({}, status_code=response_status)

    return Starlette(
        routes=[Route("/animals", _endpoint, methods=["GET", "POST", "DELETE"])],
        middleware=[Middleware(AuditMiddleware)],
    )


class TestAuditMiddlewareDispatch:
    """Test AuditMiddleware.dispatch end-to-end with a Starlette TestClient."""

    def test_skips_audit_for_get_request(self) -> None:
        app = _build_app()
        session = _make_fake_db_session()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            client.get("/animals")

        session.add.assert_not_called()

    def test_skips_audit_for_non_2xx_response(self) -> None:
        app = _build_app(response_status=400)
        session = _make_fake_db_session()
        token = _make_token()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            client.post("/animals", headers={"Authorization": f"Bearer {token}"})

        session.add.assert_not_called()

    def test_skips_audit_when_no_auth_token(self) -> None:
        app = _build_app()
        session = _make_fake_db_session()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            client.post("/animals")

        session.add.assert_not_called()

    def test_records_audit_for_authenticated_post(self) -> None:
        app = _build_app()
        session = _make_fake_db_session()
        token = _make_token()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            response = client.post("/animals", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        session.add.assert_called_once()
        entry = session.add.call_args[0][0]
        assert entry.action == "create"
        assert entry.resource_type == "animals"

    def test_records_audit_for_authenticated_delete(self) -> None:
        app = _build_app()
        session = _make_fake_db_session()
        token = _make_token()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            client.delete("/animals", headers={"Authorization": f"Bearer {token}"})

        session.add.assert_called_once()
        entry = session.add.call_args[0][0]
        assert entry.action == "delete"

    def test_does_not_raise_when_db_fails(self) -> None:
        app = _build_app()
        session = _make_fake_db_session()
        session.commit = AsyncMock(side_effect=RuntimeError("DB exploded"))
        token = _make_token()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            response = client.post("/animals", headers={"Authorization": f"Bearer {token}"})

        # Middleware should swallow the DB error and still return the response
        assert response.status_code == 200

    def test_skips_audit_for_excluded_path(self) -> None:
        async def _health(_request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        app = Starlette(
            routes=[Route("/health", _health, methods=["POST"])],
            middleware=[Middleware(AuditMiddleware)],
        )
        session = _make_fake_db_session()
        token = _make_token()

        with (
            _patch_audit_db(session),
            _patch_settings(),
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            client.post("/health", headers={"Authorization": f"Bearer {token}"})

        session.add.assert_not_called()
