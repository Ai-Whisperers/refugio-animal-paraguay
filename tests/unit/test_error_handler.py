"""Unit tests for exception handler functions.

Covers:
  - validation_exception_handler (422 with field-level details)
  - http_exception_handler (maps status codes to error codes)
  - rate_limit_handler (429 with Retry-After header)
  - unhandled_exception_handler (500, no internal detail leak)
  - _get_request_id helper
"""

import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError
from src.middleware.error_handler import (
    _extract_constraint_name,
    _get_request_id,
    http_exception_handler,
    integrity_error_handler,
    rate_limit_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def _make_request(request_id: str | None = None) -> MagicMock:
    """Create a mock Request with optional request_id in state."""
    request = MagicMock()
    if request_id:
        request.state.request_id = request_id
    else:
        # Simulate no request_id attribute
        del request.state.request_id
    return request


class TestGetRequestId:
    """Tests for _get_request_id helper."""

    def test_returns_request_id_from_state(self) -> None:
        request = MagicMock()
        request.state.request_id = "test-id-123"
        assert _get_request_id(request) == "test-id-123"

    def test_generates_uuid_when_no_state(self) -> None:
        request = MagicMock()
        del request.state.request_id
        result = _get_request_id(request)
        assert isinstance(result, str)
        assert len(result) == 36  # UUID4 format


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_returns_422_with_field_details(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-001"

        errors: list[InitErrorDetails] = [
            {
                "type": PydanticCustomError("value_error", "Invalid value"),
                "loc": ("body", "email"),
                "input": "bad",
            }
        ]
        exc = RequestValidationError(errors=errors)

        response = await validation_exception_handler(request, exc)
        assert response.status_code == 422

        body = json.loads(response.body)
        assert body["error_code"] == "VALIDATION_ERROR"
        assert body["message"] == "Request validation failed"
        assert body["request_id"] == "req-001"
        assert len(body["details"]) >= 1

    @pytest.mark.asyncio
    async def test_field_path_includes_location(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-002"

        errors: list[InitErrorDetails] = [
            {
                "type": PydanticCustomError("missing", "Field required"),
                "loc": ("body", "name"),
                "input": None,
            }
        ]
        exc = RequestValidationError(errors=errors)

        response = await validation_exception_handler(request, exc)
        body = json.loads(response.body)
        detail = body["details"][0]
        assert "body" in detail["field"]
        assert "name" in detail["field"]


class TestHttpExceptionHandler:
    """Tests for http_exception_handler."""

    @pytest.mark.asyncio
    async def test_404_maps_to_not_found(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-003"

        exc = HTTPException(status_code=404, detail="Animal not found")
        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        body = json.loads(response.body)
        assert body["error_code"] == "NOT_FOUND"
        assert body["message"] == "Animal not found"
        assert body["request_id"] == "req-003"

    @pytest.mark.asyncio
    async def test_401_maps_to_unauthorized(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-004"

        exc = HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        response = await http_exception_handler(request, exc)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert body["error_code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_unmapped_status_uses_http_prefix(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-005"

        exc = HTTPException(status_code=418, detail="I'm a teapot")
        response = await http_exception_handler(request, exc)

        body = json.loads(response.body)
        assert body["error_code"] == "HTTP_418"

    @pytest.mark.asyncio
    async def test_preserves_exception_headers(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-006"

        exc = HTTPException(
            status_code=401,
            detail="Auth required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        response = await http_exception_handler(request, exc)
        assert response.headers.get("WWW-Authenticate") == "Bearer"


class TestRateLimitHandler:
    """Tests for rate_limit_handler."""

    @pytest.mark.asyncio
    async def test_returns_429_with_retry_after(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-007"

        # RateLimitExceeded requires a Limit object; mock it
        mock_limit = MagicMock()
        mock_limit.limit = "5/minute"
        exc = RateLimitExceeded(mock_limit)
        response = await rate_limit_handler(request, exc)

        assert response.status_code == 429
        body = json.loads(response.body)
        assert body["error_code"] == "RATE_LIMITED"
        assert "retry" in body["message"].lower()
        assert "Retry-After" in response.headers


class TestExtractConstraintName:
    """Tests for _extract_constraint_name helper."""

    def test_returns_none_when_no_orig(self) -> None:
        exc = MagicMock(spec=IntegrityError)
        exc.orig = None
        assert _extract_constraint_name(exc) is None

    def test_extracts_from_pgerror_string(self) -> None:
        orig = MagicMock()
        orig.pgerror = 'ERROR:  duplicate key value violates unique constraint "uq_adopters_email"\nDETAIL:  Key (email)=(test@test.com) already exists.'
        orig.constraint_name = None
        orig.diag = None
        exc = MagicMock(spec=IntegrityError)
        exc.orig = orig
        assert _extract_constraint_name(exc) == "uq_adopters_email"

    def test_extracts_from_asyncpg_constraint_name(self) -> None:
        orig = MagicMock()
        orig.pgerror = ""
        orig.constraint_name = "uq_donors_email"
        exc = MagicMock(spec=IntegrityError)
        exc.orig = orig
        assert _extract_constraint_name(exc) == "uq_donors_email"

    def test_extracts_from_diag(self) -> None:
        orig = MagicMock()
        orig.pgerror = ""
        orig.constraint_name = None
        orig.diag.constraint_name = "uq_users_email"
        exc = MagicMock(spec=IntegrityError)
        exc.orig = orig
        assert _extract_constraint_name(exc) == "uq_users_email"


class TestIntegrityErrorHandler:
    """Tests for integrity_error_handler."""

    @pytest.mark.asyncio
    async def test_returns_409_for_known_constraint(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-int-001"

        orig = MagicMock()
        orig.pgerror = 'duplicate key value violates unique constraint "uq_adopters_email"'
        orig.constraint_name = None
        orig.diag = None
        exc = MagicMock(spec=IntegrityError)
        exc.orig = orig

        response = await integrity_error_handler(request, exc)

        assert response.status_code == 409
        body = json.loads(response.body)
        assert body["error_code"] == "CONFLICT"
        assert "adopter" in body["message"].lower()
        assert body["request_id"] == "req-int-001"

    @pytest.mark.asyncio
    async def test_returns_409_for_unknown_constraint(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-int-002"

        orig = MagicMock()
        orig.pgerror = ""
        orig.constraint_name = "uq_some_unknown_table_column"
        orig.diag = None
        exc = MagicMock(spec=IntegrityError)
        exc.orig = orig

        response = await integrity_error_handler(request, exc)

        assert response.status_code == 409
        body = json.loads(response.body)
        assert body["error_code"] == "CONFLICT"
        assert body["message"] == "A resource conflict occurred"

    @pytest.mark.asyncio
    async def test_returns_409_when_orig_is_none(self) -> None:
        request = MagicMock()
        del request.state.request_id

        exc = MagicMock(spec=IntegrityError)
        exc.orig = None

        response = await integrity_error_handler(request, exc)

        assert response.status_code == 409
        body = json.loads(response.body)
        assert body["error_code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_known_constraints_have_specific_messages(self) -> None:
        """Each known constraint returns a message more specific than the generic fallback."""
        from src.middleware.error_handler import _CONSTRAINT_MESSAGES

        generic = "A resource conflict occurred"
        for constraint_name, message in _CONSTRAINT_MESSAGES.items():
            assert message != generic, f"Constraint '{constraint_name}' uses generic fallback message"
            assert len(message) > 10  # non-trivial message


class TestUnhandledExceptionHandler:
    """Tests for unhandled_exception_handler."""

    @pytest.mark.asyncio
    async def test_returns_500_without_internal_details(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-008"

        exc = RuntimeError("secret database connection string leaked")
        response = await unhandled_exception_handler(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["error_code"] == "INTERNAL_ERROR"
        assert body["message"] == "An unexpected error occurred"
        # Must NOT leak the actual exception message
        assert "secret" not in body["message"]
        assert "database" not in body["message"]

    @pytest.mark.asyncio
    async def test_includes_request_id(self) -> None:
        request = MagicMock()
        request.state.request_id = "req-009"

        exc = ValueError("oops")
        response = await unhandled_exception_handler(request, exc)

        body = json.loads(response.body)
        assert body["request_id"] == "req-009"
