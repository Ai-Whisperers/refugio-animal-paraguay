"""Unit tests for the standardized ErrorResponse schema and error handler helpers.

Tests cover:
  - ErrorResponse serialisation with all fields
  - ErrorResponse serialisation with minimal fields (exclude_none)
  - ValidationErrorDetail structure
  - _status_to_error_code mapping
  - _parse_retry_after extraction
"""

from src.middleware.error_handler import _parse_retry_after, _status_to_error_code
from src.schemas.error import ErrorResponse, ValidationErrorDetail


# ---------------------------------------------------------------------------
# ErrorResponse schema tests
# ---------------------------------------------------------------------------
class TestErrorResponse:
    def test_full_error_response(self) -> None:
        err = ErrorResponse(
            error_code="not_found",
            message="Animal not found",
            details={"animal_id": "abc-123"},
            request_id="req-001",
        )
        data = err.model_dump()
        assert data["error_code"] == "not_found"
        assert data["message"] == "Animal not found"
        assert data["details"] == {"animal_id": "abc-123"}
        assert data["request_id"] == "req-001"

    def test_minimal_error_response_excludes_none(self) -> None:
        err = ErrorResponse(
            error_code="internal_error",
            message="Something went wrong",
        )
        data = err.model_dump(exclude_none=True)
        assert "details" not in data
        assert "request_id" not in data
        assert data["error_code"] == "internal_error"

    def test_error_response_with_validation_details(self) -> None:
        details = [
            ValidationErrorDetail(
                field="body.email",
                message="value is not a valid email address",
                type="value_error",
            ),
            ValidationErrorDetail(
                field="body.phone",
                message="field required",
                type="missing",
            ),
        ]
        err = ErrorResponse(
            error_code="validation_error",
            message="Request validation failed",
            details=details,
            request_id="req-002",
        )
        data = err.model_dump()
        assert len(data["details"]) == 2
        assert data["details"][0]["field"] == "body.email"
        assert data["details"][1]["type"] == "missing"


# ---------------------------------------------------------------------------
# ValidationErrorDetail schema tests
# ---------------------------------------------------------------------------
class TestValidationErrorDetail:
    def test_serialisation(self) -> None:
        detail = ValidationErrorDetail(
            field="body.age_months",
            message="Input should be greater than 0",
            type="greater_than",
        )
        data = detail.model_dump()
        assert data == {
            "field": "body.age_months",
            "message": "Input should be greater than 0",
            "type": "greater_than",
        }


# ---------------------------------------------------------------------------
# _status_to_error_code tests
# ---------------------------------------------------------------------------
class TestStatusToErrorCode:
    def test_known_status_codes(self) -> None:
        assert _status_to_error_code(400) == "bad_request"
        assert _status_to_error_code(401) == "unauthorized"
        assert _status_to_error_code(403) == "forbidden"
        assert _status_to_error_code(404) == "not_found"
        assert _status_to_error_code(409) == "conflict"
        assert _status_to_error_code(422) == "validation_error"
        assert _status_to_error_code(429) == "rate_limit_exceeded"
        assert _status_to_error_code(500) == "internal_error"

    def test_unknown_status_code_returns_http_prefix(self) -> None:
        assert _status_to_error_code(418) == "http_418"
        assert _status_to_error_code(507) == "http_507"


# ---------------------------------------------------------------------------
# _parse_retry_after tests
# ---------------------------------------------------------------------------
class TestParseRetryAfter:
    def test_minute_period(self) -> None:
        assert _parse_retry_after("Rate limit exceeded: 5 per 1 minute") == 60

    def test_second_period(self) -> None:
        assert _parse_retry_after("Rate limit exceeded: 10 per 1 second") == 1

    def test_hour_period(self) -> None:
        assert _parse_retry_after("Rate limit exceeded: 100 per 1 hour") == 3600

    def test_unknown_format_returns_default(self) -> None:
        assert _parse_retry_after("something unexpected") == 60

    def test_empty_string_returns_default(self) -> None:
        assert _parse_retry_after("") == 60
