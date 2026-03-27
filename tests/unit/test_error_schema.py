"""Unit tests for error response schemas and error code mappings.

Covers:
  - ErrorResponse schema defaults and validation
  - ErrorDetail schema
  - Error code constants
  - STATUS_TO_ERROR_CODE mapping completeness
"""

from src.schemas.error import (
    AUTHENTICATED_RESPONSES,
    COMMON_RESPONSES,
    ERROR_BAD_GATEWAY,
    ERROR_BAD_REQUEST,
    ERROR_CONFLICT,
    ERROR_FORBIDDEN,
    ERROR_INTERNAL,
    ERROR_NOT_FOUND,
    ERROR_RATE_LIMITED,
    ERROR_SERVICE_UNAVAILABLE,
    ERROR_UNAUTHORIZED,
    ERROR_VALIDATION,
    PAYMENT_RESPONSES,
    RESOURCE_RESPONSES,
    STATUS_TO_ERROR_CODE,
    ErrorDetail,
    ErrorResponse,
)


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_minimal_construction(self) -> None:
        resp = ErrorResponse(error_code="TEST_ERROR", message="Something went wrong")
        assert resp.error_code == "TEST_ERROR"
        assert resp.message == "Something went wrong"
        assert resp.details == []
        assert resp.request_id is None

    def test_full_construction(self) -> None:
        resp = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=[{"field": "email", "message": "invalid", "type": "value_error"}],
            request_id="abc-123",
        )
        assert resp.error_code == "VALIDATION_ERROR"
        assert len(resp.details) == 1
        assert resp.request_id == "abc-123"

    def test_serialization_includes_all_fields(self) -> None:
        resp = ErrorResponse(
            error_code="NOT_FOUND",
            message="Resource not found",
            request_id="req-456",
        )
        data = resp.model_dump()
        assert set(data.keys()) == {"error_code", "message", "details", "request_id"}

    def test_details_default_empty_list(self) -> None:
        resp = ErrorResponse(error_code="X", message="Y")
        assert isinstance(resp.details, list)
        assert len(resp.details) == 0


class TestErrorDetail:
    """Tests for ErrorDetail schema."""

    def test_construction(self) -> None:
        detail = ErrorDetail(field="email", message="Invalid email", type="value_error")
        assert detail.field == "email"
        assert detail.message == "Invalid email"
        assert detail.type == "value_error"

    def test_serialization(self) -> None:
        detail = ErrorDetail(field="name", message="Required", type="missing")
        data = detail.model_dump()
        assert data == {"field": "name", "message": "Required", "type": "missing"}


class TestErrorCodeConstants:
    """Tests for error code string constants."""

    def test_all_codes_are_uppercase_strings(self) -> None:
        codes = [
            ERROR_VALIDATION,
            ERROR_NOT_FOUND,
            ERROR_UNAUTHORIZED,
            ERROR_FORBIDDEN,
            ERROR_CONFLICT,
            ERROR_RATE_LIMITED,
            ERROR_BAD_REQUEST,
            ERROR_INTERNAL,
            ERROR_BAD_GATEWAY,
            ERROR_SERVICE_UNAVAILABLE,
        ]
        for code in codes:
            assert isinstance(code, str)
            assert code == code.upper()

    def test_codes_are_unique(self) -> None:
        codes = [
            ERROR_VALIDATION,
            ERROR_NOT_FOUND,
            ERROR_UNAUTHORIZED,
            ERROR_FORBIDDEN,
            ERROR_CONFLICT,
            ERROR_RATE_LIMITED,
            ERROR_BAD_REQUEST,
            ERROR_INTERNAL,
            ERROR_BAD_GATEWAY,
            ERROR_SERVICE_UNAVAILABLE,
        ]
        assert len(set(codes)) == len(codes)


class TestStatusToErrorCodeMapping:
    """Tests for STATUS_TO_ERROR_CODE mapping."""

    def test_maps_common_http_status_codes(self) -> None:
        assert STATUS_TO_ERROR_CODE[400] == ERROR_BAD_REQUEST
        assert STATUS_TO_ERROR_CODE[401] == ERROR_UNAUTHORIZED
        assert STATUS_TO_ERROR_CODE[403] == ERROR_FORBIDDEN
        assert STATUS_TO_ERROR_CODE[404] == ERROR_NOT_FOUND
        assert STATUS_TO_ERROR_CODE[409] == ERROR_CONFLICT
        assert STATUS_TO_ERROR_CODE[422] == ERROR_VALIDATION
        assert STATUS_TO_ERROR_CODE[429] == ERROR_RATE_LIMITED

    def test_maps_gateway_status_codes(self) -> None:
        """502 and 503 must map to gateway error codes for payment/external service errors."""
        assert STATUS_TO_ERROR_CODE[502] == ERROR_BAD_GATEWAY
        assert STATUS_TO_ERROR_CODE[503] == ERROR_SERVICE_UNAVAILABLE

    def test_does_not_map_success_codes(self) -> None:
        assert 200 not in STATUS_TO_ERROR_CODE
        assert 201 not in STATUS_TO_ERROR_CODE
        assert 204 not in STATUS_TO_ERROR_CODE

    def test_does_not_map_500(self) -> None:
        """500 is handled by the unhandled exception handler, not the HTTP handler."""
        assert 500 not in STATUS_TO_ERROR_CODE


class TestOpenApiResponseDicts:
    """Tests for the pre-built OpenAPI response helper dicts."""

    def test_common_responses_contains_422_and_500(self) -> None:
        assert 422 in COMMON_RESPONSES
        assert 500 in COMMON_RESPONSES

    def test_authenticated_responses_extends_common(self) -> None:
        assert 422 in AUTHENTICATED_RESPONSES
        assert 500 in AUTHENTICATED_RESPONSES
        assert 401 in AUTHENTICATED_RESPONSES
        assert 403 in AUTHENTICATED_RESPONSES

    def test_resource_responses_extends_authenticated(self) -> None:
        assert 422 in RESOURCE_RESPONSES
        assert 500 in RESOURCE_RESPONSES
        assert 401 in RESOURCE_RESPONSES
        assert 403 in RESOURCE_RESPONSES
        assert 404 in RESOURCE_RESPONSES

    def test_payment_responses_includes_gateway_codes(self) -> None:
        assert 502 in PAYMENT_RESPONSES
        assert 503 in PAYMENT_RESPONSES
        assert 409 in PAYMENT_RESPONSES
        assert 404 in PAYMENT_RESPONSES

    def test_all_response_dicts_contain_description(self) -> None:
        for responses in [
            COMMON_RESPONSES,
            AUTHENTICATED_RESPONSES,
            RESOURCE_RESPONSES,
            PAYMENT_RESPONSES,
        ]:
            for _status_code, response_dict in responses.items():
                assert "description" in response_dict

    def test_response_dicts_are_disjoint_additions(self) -> None:
        """Each level adds codes not present in its parent."""
        common_keys = set(COMMON_RESPONSES.keys())
        auth_keys = set(AUTHENTICATED_RESPONSES.keys())
        resource_keys = set(RESOURCE_RESPONSES.keys())
        payment_keys = set(PAYMENT_RESPONSES.keys())

        assert common_keys.issubset(auth_keys)
        assert auth_keys.issubset(resource_keys)
        assert auth_keys.issubset(payment_keys)
        assert payment_keys - auth_keys == {404, 409, 502, 503}
