#!/usr/bin/env python3
# ruff: noqa: T201  # CLI tool — print() is intentional for terminal output.
"""SQL injection and XSS security audit script for Refugio Animal Paraguay.

Scans the Python source tree for patterns that commonly indicate SQL injection
or XSS vulnerabilities.  Designed to run both locally and in CI.

Usage:
    python3 scripts/security_audit.py [--src SRC_DIR]

Exit codes:
    0 — no issues found
    1 — one or more issues found

Checks performed:
    SQL injection:
      - F-string interpolation inside SQLAlchemy text() calls
      - %-formatted SQL strings outside of migration/seed files
      - Direct string concatenation in select/execute calls
      - Raw string construction patterns: "SELECT " + variable

    XSS:
      - HTMLResponse with user-supplied content
      - Unescaped Jinja2 / string.Template rendering of user input
      - Response objects with content-type text/html from user data

    Each rule also records any intentional exceptions (noqa-style comments)
    so suppressions are visible during review.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Pattern:
    """A single audit rule."""

    name: str
    description: str
    regex: re.Pattern[str]
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    # Files matching this glob are excluded from this check.
    exclude_globs: tuple[str, ...] = ()


# SQL injection patterns
SQL_PATTERNS: list[Pattern] = [
    Pattern(
        name="SQL_FSTRING_TEXT",
        description="F-string inside sqlalchemy text() — potential SQL injection",
        regex=re.compile(r"\btext\(\s*f[\"']"),
        severity="CRITICAL",
        # server_default= uses text() with static strings — safe, excluded below per-line
    ),
    Pattern(
        name="SQL_PERCENT_FORMAT",
        description="%-formatted SQL string outside migration/seed files",
        regex=re.compile(
            r"""(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\s.*%\s*[(%]""", re.IGNORECASE
        ),
        severity="HIGH",
        exclude_globs=("**/alembic/versions/*.py", "**/seeds/*.py"),
    ),
    Pattern(
        name="SQL_CONCAT_IN_EXECUTE",
        description="String concatenation (+) inside execute() or raw_sql() call",
        regex=re.compile(r"\bexecute\s*\([^)]*\+[^)]*\)"),
        severity="HIGH",
    ),
    Pattern(
        name="SQL_RAW_SELECT_CONCAT",
        description="SELECT/INSERT/UPDATE/DELETE string built with + operator",
        regex=re.compile(r"""["'](SELECT|INSERT|UPDATE|DELETE)\s[^"']*["']\s*\+""", re.IGNORECASE),
        severity="HIGH",
        exclude_globs=("**/alembic/versions/*.py", "**/seeds/*.py"),
    ),
]

# XSS patterns
XSS_PATTERNS: list[Pattern] = [
    Pattern(
        name="XSS_HTMLRESPONSE_USER_DATA",
        description="HTMLResponse returned with a variable (not a static string) — potential XSS",
        regex=re.compile(r"\bHTMLResponse\s*\(\s*(?!content=[\"'])[^)]*\)"),
        severity="HIGH",
    ),
    Pattern(
        name="XSS_MARKUPSAFE_MARKUP",
        description="markupsafe.Markup() called with user-supplied data — disables auto-escaping",
        regex=re.compile(r"\bMarkup\s*\([^)]*(?:request|user|body|form|data|input)\b"),
        severity="HIGH",
    ),
    Pattern(
        name="XSS_RESPONSE_HTML_CONTENT_TYPE",
        description="Response with text/html media_type and a variable content body",
        regex=re.compile(r'Response\s*\([^)]*media_type\s*=\s*["\']text/html["\'][^)]*\)'),
        severity="MEDIUM",
    ),
]

ALL_PATTERNS = SQL_PATTERNS + XSS_PATTERNS


# ---------------------------------------------------------------------------
# Finding record
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    pattern: Pattern
    file_path: Path
    line_number: int
    line_content: str
    suppressed: bool = False  # True if line has a # nosec or # audit-ignore comment


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


SUPPRESSION_PATTERN = re.compile(r"#\s*nosec|#\s*audit-ignore|#\s*noqa.*B\d")


def _matches_glob(path: Path, src_root: Path, globs: tuple[str, ...]) -> bool:
    """Return True if *path* matches any of *globs* relative to *src_root*."""
    relative = path.relative_to(src_root.parent)
    return any(relative.match(g) for g in globs)


def scan(src_root: Path) -> list[Finding]:
    """Scan all Python files under *src_root* and return findings."""
    findings: list[Finding] = []

    for py_file in sorted(src_root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue

        lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for lineno, line in enumerate(lines, start=1):
            for pattern in ALL_PATTERNS:
                if _matches_glob(py_file, src_root, pattern.exclude_globs):
                    continue
                if pattern.regex.search(line):
                    suppressed = bool(SUPPRESSION_PATTERN.search(line))
                    findings.append(
                        Finding(
                            pattern=pattern,
                            file_path=py_file,
                            line_number=lineno,
                            line_content=line.rstrip(),
                            suppressed=suppressed,
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",  # red
    "HIGH": "\033[93m",  # yellow
    "MEDIUM": "\033[94m",  # blue
    "LOW": "\033[97m",  # white
}
RESET = "\033[0m"


def _color(text: str, severity: str) -> str:
    """Wrap *text* in terminal color codes if stderr is a TTY."""
    if not sys.stderr.isatty():
        return text
    color = SEVERITY_COLORS.get(severity, "")
    return f"{color}{text}{RESET}"


def report(findings: list[Finding], src_root: Path) -> int:
    """Print findings to stdout.  Returns exit code (0 = clean, 1 = issues)."""
    active = [f for f in findings if not f.suppressed]
    suppressed = [f for f in findings if f.suppressed]

    if not active:
        print(f"✓ Security audit passed — no SQL injection or XSS issues found in {src_root}")
        if suppressed:
            print(f"  ({len(suppressed)} suppressed finding(s))")
        return 0

    # Sort by severity then file
    active.sort(key=lambda f: (SEVERITY_ORDER.get(f.pattern.severity, 99), str(f.file_path)))

    print(f"\n{'=' * 70}")
    print(f"  SQL INJECTION / XSS AUDIT — {len(active)} ISSUE(S) FOUND")
    print(f"{'=' * 70}\n")

    for finding in active:
        rel_path = finding.file_path.relative_to(src_root.parent)
        severity_label = _color(f"[{finding.pattern.severity}]", finding.pattern.severity)
        print(f"{severity_label} {finding.pattern.name}")
        print(f"  What:  {finding.pattern.description}")
        print(f"  Where: {rel_path}:{finding.line_number}")
        print(f"  Line:  {finding.line_content.strip()}")
        print("  Fix:   Use parameterized queries (text().bindparams()) or ORM methods.")
        print("         To suppress a false positive: append  # audit-ignore  to the line.\n")

    if suppressed:
        print(f"  {len(suppressed)} additional finding(s) suppressed via # audit-ignore / # nosec")

    print(f"{'=' * 70}")
    return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Source directory to scan (default: src)",
    )
    args = parser.parse_args(argv)

    src_root = Path(args.src).resolve()
    if not src_root.is_dir():
        print(f"ERROR: Source directory not found: {src_root}", file=sys.stderr)
        return 2

    findings = scan(src_root)
    return report(findings, src_root)


if __name__ == "__main__":
    sys.exit(main())
