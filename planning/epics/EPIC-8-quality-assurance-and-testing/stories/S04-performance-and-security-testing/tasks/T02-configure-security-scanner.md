---
task: T02
story: S04
epic: EPIC-8
title: Configure security scanner
status: ready
priority: medium
created: 2026-03-25T17:13:26.735874
---

# T02: Configure security scanner

## Description

Integrate automated security scanning into the development workflow and the CI/CD pipeline. Security scanning covers four distinct concerns: Python source code static analysis for insecure patterns using bandit, dependency vulnerability scanning using pip-audit, secret and credential detection using gitleaks, and a manual OWASP Top 10 compliance checklist specific to the FastAPI application. All four tools are configured to produce machine-readable output and to fail the pipeline on any finding above the configured severity threshold.

## Python Static Analysis with bandit

bandit is a Python-specific static application security testing tool that parses the abstract syntax tree of every Python source file and flags patterns associated with common security vulnerabilities. It is added to the development and CI dependency list and is configured through a bandit.yaml file at the project root.

The bandit.yaml configuration skips the tests directory, since test code often uses patterns that would trigger false positives (such as hardcoded passwords in test fixtures). It also skips migrations, since Alembic-generated migration files contain raw SQL that bandit can misinterpret. The configuration sets the minimum severity level to medium, meaning low-severity informational findings do not fail the scan. The minimum confidence level is also set to medium, filtering out findings where bandit has low confidence in the detection.

Findings that are confirmed false positives may be suppressed with a nosec comment on the specific line, but each suppression must include a comment explaining why the suppression is justified. Blanket suppression of entire files or test modules is prohibited. The CI job treats any finding at medium or high severity as a pipeline failure.

bandit is run recursively over the src directory and produces output in JSON format, which is uploaded as a GitHub Actions artifact after each pipeline run. This JSON artifact serves as the audit trail for security review.

## Dependency Vulnerability Scanning with pip-audit

pip-audit queries the Python Packaging Advisory Database (PyPA Advisory DB) and the OSV database for known vulnerabilities in the project's installed dependencies. It is run against the full requirements file, including both production and development dependencies, since vulnerabilities in development tools can also be exploited in CI environments.

pip-audit is configured to produce output in JSON format and to exit with a non-zero code on any finding. The CI pipeline treats any critical or high severity vulnerability as an immediate pipeline failure. Medium severity findings generate a warning that is reported to the team but do not block the pipeline, since medium findings often require more context to evaluate. Low severity findings are logged but do not trigger any notification.

When pip-audit identifies a vulnerability in a dependency, the remediation path is to upgrade to the patched version as soon as it is available. If no patched version exists and the vulnerability is in a transitive dependency, the dependency that introduces the vulnerable transitive dependency is replaced with an alternative. Maintaining a known-vulnerable dependency without a remediation plan is not acceptable. Vulnerabilities that are evaluated and determined to be unexploitable in this specific application context may be suppressed with a corresponding entry in a pip-audit-ignore file, but each entry must include the CVE identifier, the date of evaluation, and the reason the finding is not exploitable.

## Secret Detection with gitleaks

gitleaks scans git history and staged changes for patterns matching known credential formats: API keys, connection strings, private keys, tokens, and passwords. It is configured through a .gitleaks.toml file at the project root that specifies which file patterns to scan, which rules to apply, and which paths to allowlist.

The allowlist configuration excludes example files with the suffix .example, test fixture files under tests/fixtures, and documentation files that intentionally contain placeholder strings like sk_test_xxxx. The allowlist is conservative: a path is only allowlisted if it has been reviewed and confirmed to contain no real credentials.

gitleaks is integrated in two places. First, it is added as a pre-commit hook using the pre-commit framework, so that any commit attempt that would introduce a new credential pattern is blocked immediately on the developer's machine with a clear error message identifying the offending file and line. Second, it is run as a GitHub Actions pipeline job that scans the full commit range of the pull request, catching any secrets that bypassed the local hook or were committed on a different machine without the hook installed.

If a secret is accidentally committed, the response procedure is documented in docs/security/secret-rotation-runbook.md. The procedure covers: rotating the compromised credential immediately through the issuing service's dashboard, updating the secret in the GitHub Actions environment secrets, verifying that the old credential no longer works, and then purging the secret from git history using git-filter-repo. Simply overwriting the file in a follow-up commit does not remove the secret from history.

## OWASP Top 10 Compliance Checklist for FastAPI

Beyond automated scanning, the application is evaluated against the OWASP Top 10 vulnerabilities with checks specific to FastAPI and the project's architecture. This checklist is maintained in docs/security/owasp-checklist.md and is reviewed at the start of each EPIC that touches the API layer.

Injection (A03): All database queries use SQLAlchemy's parameterized query interface. No string formatting or f-string interpolation is used to construct SQL. The checklist item is verified by running a bandit scan looking specifically for bandit rule B608 (hardcoded SQL expressions) and confirming zero findings.

Broken Authentication (A07): JWT tokens are validated on every protected route using the require_role dependency. Token expiry is enforced. The checklist item is verified by a specific pytest test that attempts to call a protected endpoint with an expired token and asserts that the response is 401 Unauthorized.

Sensitive Data Exposure (A02): All API responses are reviewed to confirm that password hashes, internal database IDs beyond what is necessary, and raw Stripe API keys are never included in response bodies. Donor PII (email, name) is only returned to requests authenticated as the donor themselves or as staff or admin. The checklist item is verified by reviewing the Pydantic response schemas for every endpoint and confirming that no sensitive fields are present.

Security Misconfiguration (A05): CORS is configured to allow requests only from the known frontend origins, not from wildcard origins. The list of allowed origins is specified in the application configuration and differs per environment. The checklist item is verified by a pytest test that sends a request with an Origin header set to an unauthorized domain and asserts that the response does not include the Access-Control-Allow-Origin header.

Broken Access Control (A01): Every endpoint that returns or modifies data belonging to a specific user asserts that the authenticated user is authorized to access that specific record. Adopters cannot read other adopters' adoption requests. Staff can read any record. The checklist item is verified by integration tests that call cross-user endpoints and assert 403 Forbidden responses.

## Integration into GitHub Actions

The security scanning pipeline job runs in parallel with the test job after the linting job passes. It is not blocked by the test job, so security findings are reported to the developer at the same time as test results rather than sequentially. The job runs bandit, pip-audit, and gitleaks in sequence and uploads all three output artifacts regardless of whether any tool found issues. If any tool exits with a non-zero code at the configured severity threshold, the job is marked as failed and the pull request cannot be merged until the issue is resolved or explicitly documented as a known exception.

The security job is also scheduled to run on the default branch every twenty-four hours via a GitHub Actions scheduled workflow, even without a push event. This daily scan catches newly disclosed vulnerabilities in dependencies that were not vulnerable when last pushed.
