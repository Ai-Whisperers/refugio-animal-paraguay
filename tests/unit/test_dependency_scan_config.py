"""Tests for dependency scan configuration files.

Validates that:
  - .pip-audit-ignore exists and is properly formatted
  - dependency-scan.yml workflow file exists and has required keys
  - Weekly schedule is configured
  - Issue creation step is present
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IGNORE_FILE = REPO_ROOT / ".pip-audit-ignore"
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "dependency-scan.yml"


class TestPipAuditIgnoreFile:
    def test_ignore_file_exists(self) -> None:
        assert IGNORE_FILE.exists(), ".pip-audit-ignore file must exist in repo root"

    def test_ignore_file_has_documentation_header(self) -> None:
        content = IGNORE_FILE.read_text()
        assert content.startswith("#"), "First line must be a comment explaining the format"

    def test_no_bare_ids_without_comments(self) -> None:
        """Every suppressed ID must have an inline comment explaining why."""
        lines = IGNORE_FILE.read_text().splitlines()
        id_pattern = re.compile(r"^(GHSA|CVE|PYSEC)-[\w-]+", re.IGNORECASE)
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Lines with an ID must also have an inline comment
            if id_pattern.match(stripped):
                assert "#" in stripped, (
                    f"Suppressed vulnerability ID '{stripped}' has no inline comment. "
                    "Add a comment explaining why it is suppressed."
                )

    def test_no_duplicate_ids(self) -> None:
        lines = IGNORE_FILE.read_text().splitlines()
        id_pattern = re.compile(r"^(GHSA|CVE|PYSEC)-[\w-]+", re.IGNORECASE)
        ids = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            vuln_id = stripped.split("#")[0].strip()
            if id_pattern.match(vuln_id):
                ids.append(vuln_id.upper())

        assert len(ids) == len(set(ids)), f"Duplicate IDs found in .pip-audit-ignore: {ids}"


class TestDependencyScanWorkflow:
    def _read_workflow(self) -> str:
        return WORKFLOW_FILE.read_text()

    def test_workflow_file_exists(self) -> None:
        assert WORKFLOW_FILE.exists(), "dependency-scan.yml must exist in .github/workflows/"

    def test_workflow_triggers_on_pull_request(self) -> None:
        content = self._read_workflow()
        assert "pull_request:" in content

    def test_workflow_triggers_on_push_to_develop(self) -> None:
        content = self._read_workflow()
        assert "develop" in content

    def test_workflow_triggers_on_push_to_main(self) -> None:
        content = self._read_workflow()
        assert "main" in content

    def test_workflow_has_weekly_schedule(self) -> None:
        content = self._read_workflow()
        assert "schedule:" in content
        assert "cron:" in content

    def test_workflow_supports_manual_dispatch(self) -> None:
        content = self._read_workflow()
        assert "workflow_dispatch:" in content

    def test_workflow_uses_pip_audit(self) -> None:
        content = self._read_workflow()
        assert "pip-audit" in content

    def test_workflow_runs_strict_mode(self) -> None:
        # --strict makes pip-audit fail if dependency collection itself fails
        content = self._read_workflow()
        assert "--strict" in content

    def test_workflow_creates_github_issue_on_schedule_failure(self) -> None:
        content = self._read_workflow()
        # Issue creation step must be present
        assert "github.rest.issues.create" in content

    def test_workflow_avoids_duplicate_issues(self) -> None:
        content = self._read_workflow()
        # Deduplication logic: comment on existing rather than opening duplicate
        assert "listForRepo" in content
        assert "createComment" in content

    def test_workflow_reads_ignore_file(self) -> None:
        content = self._read_workflow()
        assert ".pip-audit-ignore" in content

    def test_workflow_uploads_audit_report_as_artifact(self) -> None:
        content = self._read_workflow()
        assert "upload-artifact" in content
        assert "pip-audit-report" in content

    def test_workflow_uses_python_312(self) -> None:
        content = self._read_workflow()
        assert '"3.12"' in content

    def test_issue_creation_only_on_scheduled_or_manual_runs(self) -> None:
        content = self._read_workflow()
        # Must NOT create issues on every PR failure (only scheduled/manual)
        assert "schedule" in content and "workflow_dispatch" in content
        # The conditional logic should reference event_name
        assert "github.event_name" in content
