"""Unit tests for scripts/security_audit.py.

Tests validate:
- Pattern detection: f-string in text(), %-formatted SQL, concatenation in execute(),
  raw SELECT concat, HTMLResponse with variable, Markup with user data,
  Response with text/html content-type.
- Suppression via # audit-ignore / # nosec comments.
- Exclusion globs (migrations, seeds) for applicable patterns.
- scan() returns correct findings and file paths.
- report() returns exit code 0 when all findings suppressed or no findings.
- report() returns exit code 1 when active (non-suppressed) findings exist.
- CLI entry point exit codes.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# Ensure scripts/ is importable.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from security_audit import (
    ALL_PATTERNS,
    SQL_PATTERNS,
    XSS_PATTERNS,
    Finding,
    _matches_glob,
    main,
    report,
    scan,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _src_dir(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create a fake src/ directory under *tmp_path* and populate *files*.

    Keys are filenames relative to src/; values are source code strings.
    Returns the src/ Path.
    """
    src = tmp_path / "src"
    src.mkdir()
    for name, code in files.items():
        target = src / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(code), encoding="utf-8")
    return src


# ---------------------------------------------------------------------------
# Pattern registry sanity checks
# ---------------------------------------------------------------------------


class TestPatternRegistry:
    def test_sql_patterns_nonempty(self) -> None:
        assert len(SQL_PATTERNS) >= 4

    def test_xss_patterns_nonempty(self) -> None:
        assert len(XSS_PATTERNS) >= 3

    def test_all_patterns_is_union(self) -> None:
        assert set(ALL_PATTERNS) == set(SQL_PATTERNS) | set(XSS_PATTERNS)

    def test_each_pattern_has_valid_severity(self) -> None:
        valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        for pattern in ALL_PATTERNS:
            assert pattern.severity in valid, f"{pattern.name} has invalid severity"

    def test_each_pattern_name_unique(self) -> None:
        names = [p.name for p in ALL_PATTERNS]
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# SQL injection detection
# ---------------------------------------------------------------------------


class TestSQLFstringText:
    def test_detects_fstring_in_text(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "bad.py": """\
                    from sqlalchemy import text
                    status = "active"
                    stmt = text(f"SELECT * FROM animals WHERE status = '{status}'")
                """,
            },
        )
        findings = scan(src)
        names = [f.pattern.name for f in findings]
        assert "SQL_FSTRING_TEXT" in names

    def test_clean_text_call_not_flagged(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "clean.py": """\
                    from sqlalchemy import text
                    stmt = text("SELECT * FROM animals WHERE status = :status")
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "SQL_FSTRING_TEXT" for f in findings)

    def test_server_default_static_string_not_flagged(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "model.py": """\
                    import sqlalchemy as sa
                    col = sa.Column(sa.String, server_default=sa.text("'scheduled'"))
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "SQL_FSTRING_TEXT" for f in findings)


class TestSQLPercentFormat:
    def test_detects_percent_formatted_select(self, tmp_path: Path) -> None:
        # Pattern matches: SQL keyword ... % ( or %% — use tuple-style format.
        src = _src_dir(
            tmp_path,
            {
                "bad.py": """\
                    name = "Rex"
                    q = "SELECT * FROM animals WHERE name = '%s'" % (name,)
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "SQL_PERCENT_FORMAT" for f in findings)

    def test_excluded_in_migration_files(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "alembic/versions/001_init.py": """\
                    q = "UPDATE animals SET status = '%s'" % "active"
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "SQL_PERCENT_FORMAT" for f in findings)

    def test_excluded_in_seed_files(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "seeds/animals.py": """\
                    q = "INSERT INTO animals (name) VALUES ('%s')" % "Rex"
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "SQL_PERCENT_FORMAT" for f in findings)


class TestSQLConcatInExecute:
    def test_detects_concat_in_execute(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "bad.py": """\
                    table = "animals"
                    db.execute("SELECT * FROM " + table)
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "SQL_CONCAT_IN_EXECUTE" for f in findings)

    def test_clean_execute_not_flagged(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "clean.py": """\
                    db.execute(select(Animal).where(Animal.id == animal_id))
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "SQL_CONCAT_IN_EXECUTE" for f in findings)


class TestSQLRawSelectConcat:
    def test_detects_raw_select_concat(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "bad.py": """\
                    col = "name"
                    q = "SELECT " + col + " FROM animals"
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "SQL_RAW_SELECT_CONCAT" for f in findings)

    def test_excluded_in_migration(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "alembic/versions/002_add_col.py": """\
                    q = "ALTER TABLE " + "animals"
                """,
            },
        )
        # SQL_RAW_SELECT_CONCAT only matches SELECT/INSERT/UPDATE/DELETE prefix;
        # ALTER is not matched — this just confirms no false positive either way.
        findings = scan(src)
        assert all(f.pattern.name != "SQL_RAW_SELECT_CONCAT" for f in findings)


# ---------------------------------------------------------------------------
# XSS detection
# ---------------------------------------------------------------------------


class TestXSSHTMLResponse:
    def test_detects_htmlresponse_with_variable(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    from fastapi.responses import HTMLResponse
                    def endpoint(content: str):
                        return HTMLResponse(content)
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "XSS_HTMLRESPONSE_USER_DATA" for f in findings)

    def test_htmlresponse_with_static_string_not_flagged(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    from fastapi.responses import HTMLResponse
                    def endpoint():
                        return HTMLResponse(content="<h1>OK</h1>")
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "XSS_HTMLRESPONSE_USER_DATA" for f in findings)


class TestXSSMarkupSafe:
    def test_detects_markup_with_user_data(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "template.py": """\
                    from markupsafe import Markup
                    def render(user_input: str):
                        return Markup(user_input)
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "XSS_MARKUPSAFE_MARKUP" for f in findings)

    def test_markup_with_static_not_flagged(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "template.py": """\
                    from markupsafe import Markup
                    safe = Markup("<b>bold</b>")
                """,
            },
        )
        findings = scan(src)
        assert all(f.pattern.name != "XSS_MARKUPSAFE_MARKUP" for f in findings)


class TestXSSResponseHTMLContentType:
    def test_detects_response_with_html_media_type(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    from fastapi import Response
                    def endpoint(data: str):
                        return Response(data, media_type="text/html")
                """,
            },
        )
        findings = scan(src)
        assert any(f.pattern.name == "XSS_RESPONSE_HTML_CONTENT_TYPE" for f in findings)


# ---------------------------------------------------------------------------
# Suppression via # audit-ignore / # nosec
# ---------------------------------------------------------------------------


class TestSuppression:
    def test_audit_ignore_marks_finding_suppressed(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    status = "active"
                    stmt = text(f"SELECT * FROM animals WHERE status = '{status}'")  # audit-ignore
                """,
            },
        )
        findings = scan(src)
        fstring_findings = [f for f in findings if f.pattern.name == "SQL_FSTRING_TEXT"]
        assert fstring_findings, "Expected finding before suppression check"
        assert all(f.suppressed for f in fstring_findings)

    def test_nosec_marks_finding_suppressed(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    status = "active"
                    stmt = text(f"SELECT * FROM animals WHERE status = '{status}'")  # nosec B608
                """,
            },
        )
        findings = scan(src)
        fstring_findings = [f for f in findings if f.pattern.name == "SQL_FSTRING_TEXT"]
        assert all(f.suppressed for f in fstring_findings)

    def test_unsuppressed_line_not_marked_suppressed(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "router.py": """\
                    status = "active"
                    stmt = text(f"SELECT * FROM animals WHERE status = '{status}'")
                """,
            },
        )
        findings = scan(src)
        fstring_findings = [f for f in findings if f.pattern.name == "SQL_FSTRING_TEXT"]
        assert fstring_findings
        assert all(not f.suppressed for f in fstring_findings)


# ---------------------------------------------------------------------------
# report() return values
# ---------------------------------------------------------------------------


class TestReport:
    def _make_finding(self, src_root: Path, suppressed: bool = False) -> Finding:
        pattern = SQL_PATTERNS[0]
        return Finding(
            pattern=pattern,
            file_path=src_root / "bad.py",
            line_number=10,
            line_content='stmt = text(f"SELECT * FROM animals")',
            suppressed=suppressed,
        )

    def test_empty_findings_returns_0(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        code = report([], src)
        assert code == 0

    def test_all_suppressed_returns_0(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        findings = [self._make_finding(src, suppressed=True)]
        code = report(findings, src)
        assert code == 0

    def test_active_finding_returns_1(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        findings = [self._make_finding(src, suppressed=False)]
        code = report(findings, src)
        assert code == 1

    def test_mixed_findings_returns_1(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        findings = [
            self._make_finding(src, suppressed=False),
            self._make_finding(src, suppressed=True),
        ]
        code = report(findings, src)
        assert code == 1


# ---------------------------------------------------------------------------
# scan() integration on a clean directory
# ---------------------------------------------------------------------------


class TestScanClean:
    def test_scan_returns_no_findings_for_safe_code(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "service.py": """\
                    from sqlalchemy import select
                    from src.db.models.animal import Animal

                    async def get_animal(db, animal_id):
                        stmt = select(Animal).where(Animal.id == animal_id)
                        result = await db.execute(stmt)
                        return result.scalar_one_or_none()
                """,
            },
        )
        findings = scan(src)
        active = [f for f in findings if not f.suppressed]
        assert active == []

    def test_scan_skips_pycache(self, tmp_path: Path) -> None:
        src = _src_dir(tmp_path, {"service.py": "x = 1\n"})
        pycache = src / "__pycache__"
        pycache.mkdir()
        (pycache / "evil.py").write_text(
            "stmt = text(f\"SELECT * FROM x WHERE y = '{z}'\")\n", encoding="utf-8"
        )
        findings = scan(src)
        # The file in __pycache__ must not produce findings.
        pycache_findings = [f for f in findings if "__pycache__" in str(f.file_path)]
        assert pycache_findings == []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


class TestMainCLI:
    def test_returns_0_for_clean_src(self, tmp_path: Path) -> None:
        src = _src_dir(tmp_path, {"service.py": "x = 1\n"})
        code = main(["--src", str(src)])
        assert code == 0

    def test_returns_1_for_src_with_issues(self, tmp_path: Path) -> None:
        src = _src_dir(
            tmp_path,
            {
                "bad.py": "stmt = text(f\"SELECT * FROM animals WHERE status = '{s}'\")\n",
            },
        )
        code = main(["--src", str(src)])
        assert code == 1

    def test_returns_2_for_nonexistent_src(self, tmp_path: Path) -> None:
        code = main(["--src", str(tmp_path / "does_not_exist")])
        assert code == 2


# ---------------------------------------------------------------------------
# _matches_glob helper
# ---------------------------------------------------------------------------


class TestMatchesGlob:
    def test_matches_alembic_versions(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        migration = src / "alembic" / "versions" / "001_init.py"
        migration.parent.mkdir(parents=True)
        migration.touch()
        assert _matches_glob(migration, src, ("**/alembic/versions/*.py",))

    def test_does_not_match_regular_file(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        service = src / "service.py"
        service.touch()
        assert not _matches_glob(service, src, ("**/alembic/versions/*.py",))
