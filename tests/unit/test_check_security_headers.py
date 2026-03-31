"""Unit tests for scripts/check_security_headers.py.

Tests validate:
- validate_headers() correctly passes / fails each header check.
- X-Frame-Options: DENY and SAMEORIGIN both accepted; other values rejected.
- X-Content-Type-Options: only 'nosniff' accepted.
- Content-Security-Policy: any non-empty value accepted.
- Referrer-Policy: only safe values accepted (strict-origin, no-referrer, etc.)
- Permissions-Policy: any non-empty value accepted.
- Strict-Transport-Security: optional; absent in dev/test is OK.
- X-Powered-By: should be absent; flagged when present.
- report() returns 0 when all required headers pass.
- report() returns 1 when any required header fails.
- main() returns 2 on connection error.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure scripts/ is importable.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from check_security_headers import (
    HEADER_CHECKS,
    CheckResult,
    main,
    report,
    validate_headers,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

GOOD_HEADERS: dict[str, str] = {
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "content-security-policy": "default-src 'none'; connect-src 'self'",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), geolocation=(), microphone=()",
}


# ---------------------------------------------------------------------------
# validate_headers: required headers
# ---------------------------------------------------------------------------


class TestXFrameOptions:
    def test_deny_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-frame-options": "DENY"})
        result = _find(results, "x-frame-options")
        assert result.passed

    def test_sameorigin_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-frame-options": "SAMEORIGIN"})
        result = _find(results, "x-frame-options")
        assert result.passed

    def test_allow_from_fails(self) -> None:
        results = validate_headers(
            {**GOOD_HEADERS, "x-frame-options": "ALLOW-FROM https://example.com"}
        )
        result = _find(results, "x-frame-options")
        assert not result.passed

    def test_missing_fails(self) -> None:
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "x-frame-options"}
        results = validate_headers(headers)
        result = _find(results, "x-frame-options")
        assert not result.passed


class TestXContentTypeOptions:
    def test_nosniff_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-content-type-options": "nosniff"})
        result = _find(results, "x-content-type-options")
        assert result.passed

    def test_other_value_fails(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-content-type-options": "sniff"})
        result = _find(results, "x-content-type-options")
        assert not result.passed

    def test_missing_fails(self) -> None:
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "x-content-type-options"}
        results = validate_headers(headers)
        result = _find(results, "x-content-type-options")
        assert not result.passed


class TestContentSecurityPolicy:
    def test_any_nonempty_value_passes(self) -> None:
        results = validate_headers(
            {**GOOD_HEADERS, "content-security-policy": "default-src 'self'"}
        )
        result = _find(results, "content-security-policy")
        assert result.passed

    def test_missing_fails(self) -> None:
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "content-security-policy"}
        results = validate_headers(headers)
        result = _find(results, "content-security-policy")
        assert not result.passed

    def test_empty_value_fails(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "content-security-policy": ""})
        result = _find(results, "content-security-policy")
        assert not result.passed


class TestReferrerPolicy:
    def test_strict_origin_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "referrer-policy": "strict-origin"})
        result = _find(results, "referrer-policy")
        assert result.passed

    def test_no_referrer_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "referrer-policy": "no-referrer"})
        result = _find(results, "referrer-policy")
        assert result.passed

    def test_same_origin_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "referrer-policy": "same-origin"})
        result = _find(results, "referrer-policy")
        assert result.passed

    def test_unsafe_url_fails(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "referrer-policy": "unsafe-url"})
        result = _find(results, "referrer-policy")
        assert not result.passed

    def test_origin_only_fails(self) -> None:
        # "origin" alone sends origin to cross-origin requests — not safe enough.
        results = validate_headers({**GOOD_HEADERS, "referrer-policy": "origin"})
        result = _find(results, "referrer-policy")
        assert not result.passed

    def test_missing_fails(self) -> None:
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "referrer-policy"}
        results = validate_headers(headers)
        result = _find(results, "referrer-policy")
        assert not result.passed


class TestPermissionsPolicy:
    def test_nonempty_value_passes(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "permissions-policy": "camera=()"})
        result = _find(results, "permissions-policy")
        assert result.passed

    def test_missing_fails(self) -> None:
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "permissions-policy"}
        results = validate_headers(headers)
        result = _find(results, "permissions-policy")
        assert not result.passed


class TestHSTS:
    def test_hsts_present_passes(self) -> None:
        results = validate_headers(GOOD_HEADERS)
        result = _find(results, "strict-transport-security")
        assert result.passed

    def test_hsts_absent_passes_as_optional(self) -> None:
        # HSTS is not required (only meaningful on HTTPS / production).
        headers = {k: v for k, v in GOOD_HEADERS.items() if k != "strict-transport-security"}
        results = validate_headers(headers)
        result = _find(results, "strict-transport-security")
        assert result.passed


class TestAbsentHeaders:
    def test_x_powered_by_absent_passes(self) -> None:
        results = validate_headers(GOOD_HEADERS)  # x-powered-by not in GOOD_HEADERS
        result = _find(results, "x-powered-by")
        assert result.passed

    def test_x_powered_by_present_fails(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-powered-by": "Express"})
        result = _find(results, "x-powered-by")
        assert not result.passed

    def test_x_powered_by_present_includes_actual_value(self) -> None:
        results = validate_headers({**GOOD_HEADERS, "x-powered-by": "Express"})
        result = _find(results, "x-powered-by")
        assert result.actual_value == "Express"


# ---------------------------------------------------------------------------
# Full good-headers set
# ---------------------------------------------------------------------------


class TestFullGoodHeaders:
    def test_all_required_pass_with_good_headers(self) -> None:
        results = validate_headers(GOOD_HEADERS)
        failures = [r for r in results if not r.passed]
        assert failures == [], f"Unexpected failures: {[r.message for r in failures]}"


# ---------------------------------------------------------------------------
# report() exit codes
# ---------------------------------------------------------------------------


class TestReport:
    def _pass(self) -> CheckResult:
        check = next(c for c in HEADER_CHECKS if c.name == "x-frame-options")
        return CheckResult(check=check, passed=True, actual_value="DENY", message="OK")

    def _fail(self) -> CheckResult:
        check = next(c for c in HEADER_CHECKS if c.name == "x-frame-options")
        return CheckResult(
            check=check,
            passed=False,
            actual_value=None,
            message="Required header 'x-frame-options' is missing",
        )

    def test_all_pass_returns_0(self) -> None:
        results = [self._pass(), self._pass()]
        code = report(results, "http://test")
        assert code == 0

    def test_any_failure_returns_1(self) -> None:
        results = [self._pass(), self._fail()]
        code = report(results, "http://test")
        assert code == 1

    def test_empty_results_returns_0(self) -> None:
        code = report([], "http://test")
        assert code == 0


# ---------------------------------------------------------------------------
# main() with mocked fetch
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_returns_0_for_good_headers(self) -> None:
        with patch("check_security_headers.fetch_headers", return_value=GOOD_HEADERS):
            code = main(["--url", "http://example.com"])
        assert code == 0

    def test_main_returns_1_for_missing_required_header(self) -> None:
        bad_headers = {k: v for k, v in GOOD_HEADERS.items() if k != "x-frame-options"}
        with patch("check_security_headers.fetch_headers", return_value=bad_headers):
            code = main(["--url", "http://example.com"])
        assert code == 1

    def test_main_returns_2_on_connection_error(self) -> None:
        from urllib.error import URLError

        with patch("check_security_headers.fetch_headers", side_effect=URLError("refused")):
            code = main(["--url", "http://localhost:9999"])
        assert code == 2


# ---------------------------------------------------------------------------
# Header check registry
# ---------------------------------------------------------------------------


class TestHeaderCheckRegistry:
    def test_all_checks_have_unique_names(self) -> None:
        names = [c.name for c in HEADER_CHECKS]
        assert len(names) == len(set(names))

    def test_required_headers_include_x_frame_options(self) -> None:
        required = {c.name for c in HEADER_CHECKS if c.required}
        assert "x-frame-options" in required

    def test_required_headers_include_csp(self) -> None:
        required = {c.name for c in HEADER_CHECKS if c.required}
        assert "content-security-policy" in required

    def test_x_powered_by_is_should_be_absent(self) -> None:
        check = next(c for c in HEADER_CHECKS if c.name == "x-powered-by")
        assert check.should_be_absent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find(results: list[CheckResult], header_name: str) -> CheckResult:
    for r in results:
        if r.check.name == header_name:
            return r
    raise AssertionError(f"No result found for header '{header_name}'")
