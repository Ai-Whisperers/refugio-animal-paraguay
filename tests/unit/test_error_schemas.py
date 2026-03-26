"""Unit tests for error response schemas and formatting."""

from src.schemas.error import ErrorDetail, ErrorResponse


class TestErrorResponse:
    def test_minimal_error(self) -> None:
        err = ErrorResponse(error_code="not_found", message="Resource not found")
        assert err.error_code == "not_found"
        assert err.message == "Resource not found"
        assert err.details is None
        assert err.request_id is None

    def test_error_with_request_id(self) -> None:
        err = ErrorResponse(
            error_code="internal_error",
            message="An unexpected error occurred",
            request_id="abc123def456",
        )
        assert err.request_id == "abc123def456"

    def test_error_with_details(self) -> None:
        details = [
            ErrorDetail(field="body.email", message="value is not a valid email address"),
            ErrorDetail(field="body.name", message="field required"),
        ]
        err = ErrorResponse(
            error_code="validation_error",
            message="Request validation failed",
            details=details,
            request_id="req123",
        )
        assert len(err.details) == 2
        assert err.details[0].field == "body.email"
        assert err.details[1].field == "body.name"

    def test_error_serialization(self) -> None:
        err = ErrorResponse(
            error_code="conflict",
            message="Duplicate email",
            request_id="req456",
        )
        data = err.model_dump()
        assert data["error_code"] == "conflict"
        assert data["message"] == "Duplicate email"
        assert data["details"] is None
        assert data["request_id"] == "req456"

    def test_error_serialization_excludes_none_details(self) -> None:
        err = ErrorResponse(error_code="bad_request", message="Bad request")
        data = err.model_dump(exclude_none=True)
        assert "details" not in data
        assert "request_id" not in data


class TestErrorDetail:
    def test_field_detail(self) -> None:
        detail = ErrorDetail(field="body.amount_cents", message="value must be greater than 0")
        assert detail.field == "body.amount_cents"
        assert detail.message == "value must be greater than 0"
