# Meta-Setup Improvements — Refugio Animal Paraguay

**Created**: 2026-03-26
**Purpose**: Gaps found during autonomous work setup audit. Fixes applied inline where possible; remaining items documented for manual action.

---

## CRITICAL — Applied Now

### 1. Missing root `tests/conftest.py`
**Problem**: Only `tests/integration/conftest.py` exists. Unit tests have no shared fixtures, and new stories (intake, password reset) will need shared factories/helpers across both unit and integration tests.
**Fix**: Created `tests/conftest.py` with shared factories and `tests/unit/conftest.py` stub.

### 2. Missing `.pre-commit-config.yaml`
**Problem**: `pyproject.toml` lists `pre-commit>=3.7` as a dev dependency but no `.pre-commit-config.yaml` exists. Developers can commit without running quality gates locally.
**Fix**: Created `.pre-commit-config.yaml` with ruff, black, pyright, and bandit hooks.

### 3. Stale CLAUDE.md stats
**Problem**: CLAUDE.md says "95 tests passing" but actual count is 204. Says "18 test files" but there are more. Phase description doesn't reflect current state accurately.
**Fix**: Updated CLAUDE.md current phase section with accurate numbers.

### 4. No `tests/unit/conftest.py`
**Problem**: No unit-level conftest for lightweight mocking fixtures.
**Fix**: Created with basic stubs.

---

## HIGH — Should Fix This Sprint

### 5. Missing CI/CD skill file
**Problem**: 8 skills exist but none covers CI/CD patterns (GitHub Actions, workflows, deployment). The RAP-011 story has no skill to reference.
**Action**: Create `.claude/skills/cicd-patterns.md` covering GitHub Actions YAML patterns, service containers, artifact caching, deployment workflows.

### 6. Missing frontend skill file
**Problem**: V1 Sprint 1 includes Next.js scaffold (story #4) and animal browsing page (#5) but no frontend skill exists. The autonomous agent will have no project-specific patterns to follow.
**Action**: Create `.claude/skills/nextjs-patterns.md` covering Next.js 14 App Router, Tailwind CSS, component patterns, API integration with the FastAPI backend.

### 7. No shared test factories
**Problem**: Each test file creates its own test data inline. As models grow (intake, verification tokens), this becomes duplicated and fragile.
**Action**: Create `tests/factories.py` with factory functions for Animal, User, Adopter, Donor, IntakeRecord, VerificationToken.

### 8. Scheduled task branch conflicts
**Problem**: All 4 scheduled tasks branch from `develop` independently. If RAP-011 finishes and merges to develop before RAP-012 starts, RAP-012 gets the CI/CD changes. But if they overlap, they work on stale bases. Not a blocker (they touch different files) but messy.
**Mitigation**: The orchestrator task handles this by running sequentially. One-shot tasks are spaced 1h apart to minimize overlap. Document this as a known limitation.

### 9. No health-check script for dev environment
**Problem**: Before autonomous work, no automated check that PostgreSQL is running, migrations are applied, and the app can start. A scheduled task could fail silently if the DB is down.
**Action**: Add `make health` target that verifies DB connectivity and migration state.

---

## MEDIUM — Backlog

### 10. Agent model assignments
**Current**: schema-designer (Haiku), test-writer (Haiku), doc-writer (Haiku), security-auditor (Sonnet), ticket-manager (Sonnet), refactoring-advisor (Sonnet).
**Concern**: Haiku for test-writer may produce lower-quality tests for complex integration scenarios. Consider upgrading to Sonnet for stories with security or compliance implications.
**Action**: No change needed now — revisit when agents are used more heavily.

### 11. No QUEUE.md automation
**Problem**: Stories are manually marked DONE in QUEUE.md. The orchestrator does this, but if a human forgets, the orchestrator picks up already-done work.
**Action**: Consider a `make queue-status` script that cross-references QUEUE.md with ticket directories and git branches.

### 12. Missing stories for 2 queue items
**Problem**: QUEUE.md items #3 (CORS + Rate Limiting) and #4 (Next.js Scaffold) have no STORY.md files in `planning/epics/`. The scheduled tasks work from inline specs, but this breaks the convention.
**Action**: Create formal STORY.md files for these items.

### 13. pyright venv config points to nonexistent venv
**Problem**: `pyproject.toml` has `venvPath = "."` and `venv = "venv"` but there's no `venv/` directory — deps are installed system-wide with `--break-system-packages`.
**Action**: Remove venv config from pyright or create a proper venv. Low priority since pyright works without it.

### 14. No rollback documentation for scheduled tasks
**Problem**: If a scheduled task creates a broken branch/PR, there's no documented process for cleanup.
**Action**: Add rollback steps to AGENT-GUIDE.md.

---

## LOW — Nice to Have

### 15. Hook interference with scheduled tasks
**Observation**: The `stop.py` hook sends TTS notifications on session end. The `cost_alert_threshold.py` tracks spending. These may behave unexpectedly during overnight autonomous runs.
**Action**: Monitor first run; disable TTS for scheduled task sessions if noisy.

### 16. Orchestrator log rotation
**Problem**: `planning/orchestrator-log.md` will grow indefinitely.
**Action**: Add date-based sections or rotate monthly.

### 17. Memory bank for project context
**Observation**: Auto-memory only has one entry. As more stories complete, key architectural decisions should be saved to memory for cross-session context.
**Action**: The orchestrator should save learnings to auto-memory after each sprint.
