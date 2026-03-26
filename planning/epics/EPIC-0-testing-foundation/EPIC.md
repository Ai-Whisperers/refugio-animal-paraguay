---
id: EPIC-0
title: Testing Foundation
description: Establish comprehensive testing infrastructure and best practices for FastAPI + PostgreSQL backend
status: ready
priority: critical
estimated_effort: 40 hours
stories_count: 5
---

# EPIC-0: Testing Foundation

## Overview

The Testing Foundation epic establishes all testing infrastructure, frameworks, and best practices for the Refugio Animal Paraguay project. This is the **foundational epic** — all other work depends on having a solid testing framework in place. No feature work can begin until this epic is complete.

## Why This Epic Must Be Done First

Testing infrastructure is not a "nice to have" feature to be added later. It must be established **first** because:

1. **All subsequent code must be testable** — developers writing features in later epics need the testing framework ready
2. **Quality gates require tests** — CI/CD pipeline enforces test coverage, which requires infrastructure
3. **Blocks architectural decisions** — testing choices influence how features are structured
4. **Enables confidence** — teams can refactor and optimize knowing tests catch regressions

**Critical dependency**: EPIC-0 must be **complete and merged to main** before any developer starts work on EPIC-1, EPIC-4, EPIC-5, etc.

## Scope

This epic covers the FastAPI backend testing stack. All testing infrastructure is for Python services using pytest and httpx.

### Testing Frameworks and Tools

The primary test runner is pytest with the asyncio plugin for testing async FastAPI endpoints. HTTP integration tests use httpx with ASGITransport to call FastAPI directly without a network socket. Database tests run against a real PostgreSQL test database seeded via Alembic migrations; there is no in-memory database substitute. Test coverage is measured by pytest-cov targeting an 80% minimum threshold.

### Testing Strategy Layers

Unit tests cover pure Python functions: validation logic, business rules, data transformations, currency calculations, and permission checks. These tests have no I/O dependencies and run entirely in memory.

Integration tests cover FastAPI route handlers calling SQLAlchemy against a live PostgreSQL test database. Each integration test receives a fresh database transaction that is rolled back after the test completes, ensuring isolation without requiring a full database reset between tests.

End-to-end tests cover complete user journeys such as the donation flow and adoption submission. These tests run against a running server with a seeded database and verify the full stack from HTTP request to database state.

### Testing Best Practices

Test files are organized in a tests directory mirroring the src directory structure: unit tests in tests/unit, integration tests in tests/integration, and end-to-end tests in tests/e2e. Fixtures for authentication tokens, database sessions, and test users are defined in tests/conftest.py and shared across the test suite. Each test follows the Arrange-Act-Assert pattern. Test names describe behavior using the convention test_verb_subject_condition.

## Stories in This Epic

| Story ID | Title | Purpose |
|----------|-------|---------|
| S01 | Test Infrastructure Setup | Install pytest, httpx, pytest-asyncio, pytest-cov, configure test database |
| S02 | API Mocking and HTTP Testing | Configure httpx AsyncClient with ASGITransport for endpoint testing |
| S03 | Database Test Fixtures | Create conftest.py with session, client, and user fixtures |
| S04 | End-to-End Test Infrastructure | Configure full-stack test scenarios with seeded data |
| S05 | Coverage and CI/CD Integration | Enforce coverage thresholds in GitHub Actions |

## Technical Architecture

The test configuration lives in pyproject.toml under the tool.pytest.ini_options section. The asyncio mode is set to auto so that async test functions run without requiring explicit event loop management. The test database URL is loaded from environment variables so that developers can run tests against a local PostgreSQL instance without affecting the development database.

The shared conftest.py file at the project root defines three key fixtures. The db_session fixture creates a database session and wraps each test in a transaction that is rolled back at the end, preventing test pollution. The client fixture creates an httpx.AsyncClient bound to the FastAPI app via ASGITransport, allowing full request-response cycle testing without a running server process. The auth_headers fixture generates a valid JWT token for each role (admin, staff, vet, volunteer, adopter, foster) so that protected endpoints can be tested with the correct authorization.

## Success Criteria

- All testing packages installed and importable in the project virtual environment
- pytest runs successfully against the test database with zero errors
- httpx.AsyncClient successfully calls at least one FastAPI endpoint in a test
- Database session rollback between tests is verified by isolation tests
- Coverage report shows 80% or above for all src modules
- GitHub Actions workflow runs the full test suite on every pull request

## Dependencies

### Blocks

- EPIC-1 (Animal Catalog) — depends on test fixtures for animals
- EPIC-2 (Adoption Process) — depends on form validation test patterns
- EPIC-3 (Donation Systems) — depends on Stripe mock patterns
- EPIC-4 (Medical Records) — depends on audit log test patterns
- EPIC-5 (Volunteer Management) — depends on auth role test fixtures
- EPIC-6 (Communications) — depends on email and WhatsApp mock patterns

### Blocked By

- None — this is the foundational epic
- Assumes Python 3.12 virtual environment and PostgreSQL 16 are available locally

## Effort Estimate

| Story | Estimated Hours | Complexity |
|-------|-----------------|-----------|
| S01 - Setup | 8 hours | Medium (environment configuration) |
| S02 - API Mocking | 10 hours | Medium (async patterns) |
| S03 - DB Fixtures | 12 hours | Medium (rollback isolation) |
| S04 - E2E | 7 hours | Low (seeding and assertions) |
| S05 - Coverage CI/CD | 3 hours | Low (automation) |
| **TOTAL** | **40 hours** | **Medium** |

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Async event loop conflicts in pytest | Medium | High | Use pytest-asyncio with asyncio_mode=auto |
| Test database isolation failures | Low | High | Verify rollback fixture with explicit isolation test |
| Coverage threshold too strict initially | Low | Medium | Start at 70%, increase to 80% after first sprint |
| Stripe webhook testing complexity | Medium | Medium | Use Stripe test mode and stripe-mock for unit tests |

---

**Created**: 2026-03-25
**Epic Lead**: [To be assigned]
**Status**: Ready for work
**Priority**: CRITICAL — Must complete before feature work
