"""Unit tests for RequestLoggingMiddleware and helpers.

Covers:
  - _extract_user_id: no header, bad header, valid token, expired/invalid token
  - RequestLoggingMiddleware.dispatch:
    - excluded paths pass through without logging
    - normal request logged at INFO with expected fields
    - slow request (> 1000ms) logged at WARNING
    - 5xx response logged at ERROR
    - user_id set on request.state
    - request_id forwarded from state
    - response_size_bytes included when Content-Length present
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.middleware.logging_middleware import (
    _EXCLUDED_PATHS,
    _LARGE_RESPONSE_THRESHOLD_BYTES,
    _SLOW_REQUEST_THRESHOLD_MS,
    RequestLoggingMiddleware,
    _extract_user_id,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    path: str = "/animals",
    method: str = "GET",
    headers: dict | None = None,
    request_id: str = "req-test-123",
) -> Request:
    """Build a minimal Starlette Request with optional state pre-populated."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    request = Request(scope)
    request.state.request_id = request_id
    return request


# ---------------------------------------------------------------------------
# _extract_user_id
# ---------------------------------------------------------------------------


class TestExtractUserId:
    def test_returns_none_when_no_auth_header(self) -> None:
        request = _make_request()
        assert _extract_user_id(request) is None

    def test_returns_none_when_not_bearer(self) -> None:
        request = _make_request(headers={"Authorization": "Basic abc123"})
        assert _extract_user_id(request) is None

    def test_returns_none_when_jwt_decode_fails(self) -> None:
        request = _make_request(headers={"Authorization": "Bearer invalid.token.here"})
        # decode_access_token will raise JWTError — _extract_user_id must catch it
        with patch("src.middleware.logging_middleware.decode_access_token", side_effect=Exception("bad")):
            result = _extract_user_id(request)
        assert result is None

    def test_returns_sub_from_valid_token(self) -> None:
        request = _make_request(headers={"Authorization": "Bearer valid.token"})
        with patch("src.middleware.logging_middleware.decode_access_token", return_value={"sub": "user-uuid-42"}):
            result = _extract_user_id(request)
        assert result == "user-uuid-42"

    def test_returns_none_when_sub_missing(self) -> None:
        request = _make_request(headers={"Authorization": "Bearer valid.token"})
        with patch("src.middleware.logging_middleware.decode_access_token", return_value={"role": "staff"}):
            result = _extract_user_id(request)
        assert result is None


# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------


class TestConstants:
    def test_health_in_excluded_paths(self) -> None:
        assert "/health" in _EXCLUDED_PATHS

    def test_docs_in_excluded_paths(self) -> None:
        assert "/docs" in _EXCLUDED_PATHS

    def test_openapi_json_in_excluded_paths(self) -> None:
        assert "/openapi.json" in _EXCLUDED_PATHS

    def test_slow_threshold_is_positive(self) -> None:
        assert _SLOW_REQUEST_THRESHOLD_MS > 0

    def test_large_response_threshold_is_positive(self) -> None:
        assert _LARGE_RESPONSE_THRESHOLD_BYTES > 0


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware — dispatch
# ---------------------------------------------------------------------------


def _make_app_with_middleware(
    response: Response,
) -> TestClient:
    """Wrap a trivial ASGI app with RequestLoggingMiddleware for integration-style tests."""

    async def _simple_app(scope, receive, send) -> None:  # type: ignore[type-arg]
        await response(scope, receive, send)

    # Wrap the simple app in middleware
    class _MiddlewareApp:
        def __init__(self) -> None:
            self._middleware = RequestLoggingMiddleware(_simple_app)  # type: ignore[arg-type]

        async def __call__(self, scope, receive, send) -> None:  # type: ignore[type-arg]
            await self._middleware(scope, receive, send)

    return TestClient(_MiddlewareApp())


class TestRequestLoggingMiddlewareDispatch:
    @pytest.mark.asyncio
    async def test_excluded_path_skips_logging(self) -> None:
        """Requests to /health must not reach the logger."""
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]

        response_mock = Response("ok")
        call_next = AsyncMock(return_value=response_mock)

        with patch("src.middleware.logging_middleware.logger") as mock_logger:
            request = _make_request(path="/health")
            await middleware.dispatch(request, call_next)

        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        call_next.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_static_path_skips_logging(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("css")
        call_next = AsyncMock(return_value=response_mock)

        with patch("src.middleware.logging_middleware.logger") as mock_logger:
            request = _make_request(path="/static/app.css")
            await middleware.dispatch(request, call_next)

        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_normal_request_logged_at_info(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("ok", status_code=200)
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger") as mock_logger,
            patch("src.middleware.logging_middleware._extract_user_id", return_value="user-1"),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "http_request"
        extra = call_args[1]["extra"]
        assert extra["method"] == "GET"
        assert extra["path"] == "/animals"
        assert extra["status_code"] == 200
        assert "duration_ms" in extra
        assert extra["user_id"] == "user-1"
        assert extra["request_id"] == "req-test-123"

    @pytest.mark.asyncio
    async def test_server_error_logged_at_error(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("error", status_code=500)
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger") as mock_logger,
            patch("src.middleware.logging_middleware._extract_user_id", return_value=None),
        ):
            request = _make_request(path="/donations")
            await middleware.dispatch(request, call_next)

        mock_logger.error.assert_called_once()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_slow_request_logged_at_warning(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("ok", status_code=200)
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger") as mock_logger,
            patch("src.middleware.logging_middleware._extract_user_id", return_value=None),
            patch("src.middleware.logging_middleware._SLOW_REQUEST_THRESHOLD_MS", -1),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        mock_logger.warning.assert_called()
        logged_msg = mock_logger.warning.call_args[0][0]
        assert "slow" in logged_msg

    @pytest.mark.asyncio
    async def test_user_id_set_on_request_state(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("ok", status_code=200)
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger"),
            patch("src.middleware.logging_middleware._extract_user_id", return_value="user-99"),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        assert request.state.user_id == "user-99"

    @pytest.mark.asyncio
    async def test_unauthenticated_request_has_none_user_id(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("ok", status_code=200)
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger"),
            patch("src.middleware.logging_middleware._extract_user_id", return_value=None),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        assert request.state.user_id is None

    @pytest.mark.asyncio
    async def test_response_size_included_when_content_length_present(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        response_mock = Response("body", status_code=200, headers={"content-length": "4"})
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger") as mock_logger,
            patch("src.middleware.logging_middleware._extract_user_id", return_value=None),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        extra = mock_logger.info.call_args[1]["extra"]
        assert extra["response_size_bytes"] == 4

    @pytest.mark.asyncio
    async def test_response_size_omitted_when_no_content_length(self) -> None:
        middleware = RequestLoggingMiddleware(app=MagicMock())  # type: ignore[arg-type]
        # Use a response with no body so Starlette does not auto-add content-length.
        response_mock = Response(status_code=204)  # 204 No Content has no body
        call_next = AsyncMock(return_value=response_mock)

        with (
            patch("src.middleware.logging_middleware.logger") as mock_logger,
            patch("src.middleware.logging_middleware._extract_user_id", return_value=None),
        ):
            request = _make_request(path="/animals")
            await middleware.dispatch(request, call_next)

        extra = mock_logger.info.call_args[1]["extra"]
        assert "response_size_bytes" not in extra
