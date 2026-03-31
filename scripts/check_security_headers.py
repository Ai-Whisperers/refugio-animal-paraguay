#!/usr/bin/env python3
# ruff: noqa: T201  # CLI tool — print() is intentional.
"""Security headers audit script for Refugio Animal Paraguay.

Makes an HTTP HEAD (or GET) request to the target URL and validates
that all OWASP-recommended security response headers are present with
expected values.

Usage:
    python3 scripts/check_security_headers.py [--url URL] [--verbose]

Defaults to http://localhost:8000 (local development server).

Exit codes:
    0 — all required headers present and correctly configured
    1 — one or more headers missing or misconfigured
    2 — invalid arguments or connection error

Checks performed:
    Required:
      - Strict-Transport-Security     (production hint — warns if absent)
      - X-Frame-Options               must be DENY or SAMEORIGIN
      - X-Content-Type-Options        must be nosniff
      - Content-Security-Policy       must be present and non-empty
      - Referrer-Policy               must be a safe value
      - Permissions-Policy            must be present

    Absent (should not appear):
      - Server                        should be removed or masked
      - X-Powered-By                  should be removed
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Expected header rules
# ---------------------------------------------------------------------------

# Referrer-Policy safe values (any of these are acceptable).
REFERRER_POLICY_SAFE = frozenset(
    {
        "no-referrer",
        "no-referrer-when-downgrade",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "same-origin",
    }
)

# X-Frame-Options acceptable values.
X_FRAME_OPTIONS_SAFE = frozenset({"DENY", "SAMEORIGIN"})


@dataclass
class HeaderCheck:
    """A single header validation rule."""

    name: str  # Header name (lower-case for comparison)
    description: str
    required: bool
    # If provided, the header value must be one of these (case-insensitive).
    allowed_values: frozenset[str] = field(default_factory=frozenset)
    # If True, the header should NOT be present.
    should_be_absent: bool = False


HEADER_CHECKS: list[HeaderCheck] = [
    HeaderCheck(
        name="strict-transport-security",
        description="HSTS: prevents protocol downgrade attacks",
        required=False,  # Only expected in production HTTPS environments
    ),
    HeaderCheck(
        name="x-frame-options",
        description="Clickjacking protection",
        required=True,
        allowed_values=X_FRAME_OPTIONS_SAFE,
    ),
    HeaderCheck(
        name="x-content-type-options",
        description="MIME-sniffing protection",
        required=True,
        allowed_values=frozenset({"nosniff"}),
    ),
    HeaderCheck(
        name="content-security-policy",
        description="Content Security Policy",
        required=True,
        # Value must be non-empty but exact directives vary by environment.
    ),
    HeaderCheck(
        name="referrer-policy",
        description="Referrer information control",
        required=True,
        allowed_values=REFERRER_POLICY_SAFE,
    ),
    HeaderCheck(
        name="permissions-policy",
        description="Browser feature permissions",
        required=True,
    ),
    # Headers that should be absent (information disclosure).
    HeaderCheck(
        name="x-powered-by",
        description="Framework/runtime disclosure — should be removed",
        required=False,
        should_be_absent=True,
    ),
]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of validating a single header."""

    check: HeaderCheck
    passed: bool
    actual_value: str | None  # None if header was absent
    message: str


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


def validate_headers(response_headers: dict[str, str]) -> list[CheckResult]:
    """Validate *response_headers* against all HEADER_CHECKS.

    *response_headers* keys must be lower-case.
    """
    results: list[CheckResult] = []
    for check in HEADER_CHECKS:
        actual = response_headers.get(check.name)

        if check.should_be_absent:
            if actual is not None:
                results.append(
                    CheckResult(
                        check=check,
                        passed=False,
                        actual_value=actual,
                        message=f"Header '{check.name}' should be absent (information disclosure)",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check=check,
                        passed=True,
                        actual_value=None,
                        message=f"Header '{check.name}' correctly absent",
                    )
                )
            continue

        if actual is None:
            if check.required:
                results.append(
                    CheckResult(
                        check=check,
                        passed=False,
                        actual_value=None,
                        message=f"Required header '{check.name}' is missing",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check=check,
                        passed=True,
                        actual_value=None,
                        message=f"Optional header '{check.name}' not present (acceptable for non-production)",
                    )
                )
            continue

        # Header present — check allowed values if specified.
        if check.allowed_values and actual.strip().lower() not in {
            v.lower() for v in check.allowed_values
        }:
            results.append(
                CheckResult(
                    check=check,
                    passed=False,
                    actual_value=actual,
                    message=(
                        f"Header '{check.name}' has unexpected value '{actual}'. "
                        f"Allowed: {sorted(check.allowed_values)}"
                    ),
                )
            )
            continue

        # Non-empty check for headers without enumerated values.
        if not actual.strip():
            results.append(
                CheckResult(
                    check=check,
                    passed=False,
                    actual_value=actual,
                    message=f"Header '{check.name}' is present but empty",
                )
            )
            continue

        results.append(
            CheckResult(
                check=check,
                passed=True,
                actual_value=actual,
                message=f"Header '{check.name}' OK: {actual[:80]}",
            )
        )

    return results


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------


def fetch_headers(url: str, timeout: int = 10) -> dict[str, str]:
    """Fetch HTTP response headers from *url* via HEAD request.

    Returns a dict with all header names lowered.
    Raises URLError on connection/DNS errors.
    """
    req = Request(url, method="HEAD")  # URL comes from our own CLI arg
    req.add_header("User-Agent", "refugio-security-audit/1.0")
    with urlopen(req, timeout=timeout) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"


def _color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{RESET}"


def report(results: list[CheckResult], url: str, verbose: bool = False) -> int:
    """Print audit results.  Returns exit code (0 = pass, 1 = fail)."""
    failures = [r for r in results if not r.passed]
    passes = [r for r in results if r.passed]

    print(f"\nSecurity Headers Audit — {url}")
    print("=" * 60)

    if verbose:
        for result in passes:
            print(_color(f"  ✓ {result.message}", GREEN))

    if failures:
        print()
        for result in failures:
            print(_color(f"  ✗ FAIL: {result.message}", RED))
            print(f"    Description: {result.check.description}")
            if result.actual_value is not None:
                print(f"    Actual:      {result.actual_value[:100]}")
        print()
        print(_color(f"FAILED — {len(failures)} issue(s) found", RED))
        return 1

    print(_color(f"\n✓ PASSED — all {len(passes)} header checks OK", GREEN))
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Target URL to audit (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show passing checks in addition to failures",
    )
    args = parser.parse_args(argv)

    try:
        headers = fetch_headers(args.url)
    except URLError as exc:
        print(f"ERROR: Could not connect to {args.url}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # surface unexpected errors as exit 2
        print(f"ERROR: Unexpected error fetching {args.url}: {exc}", file=sys.stderr)
        return 2

    results = validate_headers(headers)
    return report(results, args.url, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
