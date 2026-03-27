---
epic: EPIC-72
title: "Test Coverage & Quality Gates"
status: ready
priority: 98
sprint: priority
version: V3.1
points: 18
created: 2026-03-27
---

# EPIC-72: Test Coverage & Quality Gates

## Overview

**Goal**: Close critical test coverage gaps preventing V3.1 release. Three modules have unacceptable coverage: `password_reset` at 0%, `adoption_requests` at 41%, and notification handlers with no exception-specific tests.

**Why it matters**: These are core flows (password recovery, adoption, notifications) with zero safety net. A regression could affect all users of these features.

**Target users**: All users relying on password reset, adoption workflow, and notification delivery.

## Scope

### In Scope
- Unit tests for password_reset module (0% → 80%+)
- Integration tests for adoption_requests flow (41% → 80%+)
- Exception-specific tests for notification handlers (handlers.py, in_app_handlers.py, whatsapp_handlers.py)
- Tests for audit middleware (30% → 80%+)
- Frontend component tests using Vitest (DonationForm, CampaignCard, Navbar)

### Out of Scope
- End-to-end test automation (Playwright/Cypress) — scheduled for V4
- Frontend integration tests beyond component level
- Load testing or performance profiling
- Accessibility testing beyond component snapshot verification

## Features

- [ ] RAP-405: Write tests for password_reset module — 5 pts
- [ ] RAP-406: Improve adoption_requests test coverage — 5 pts
- [ ] RAP-407: Add notification handler exception tests — 3 pts
- [ ] RAP-408: Add audit middleware tests — 3 pts
- [ ] RAP-409: Add frontend component tests (Jest/Vitest) — 2 pts

## Dependencies

- Depends on: Quality Standards (zero warnings/errors rule already in place)
- Blocks: V3.1 release; V4 Sprint 2 (frontend component reuse)

## Key Decisions Made

1. **Coverage threshold**: 80% overall, 95% for critical paths (auth, payment)
2. **Test framework**: pytest for backend, Vitest for frontend (faster, Vite-native)
3. **Mocking strategy**: Mock at I/O boundaries (DB, email, HTTP) only, not internal functions
4. **Test data**: Use existing factories in `tests/conftest.py`; add new fixtures as needed

## Risks

- **Risk**: Tests written but not integrated into CI pipeline
  → **Mitigation**: Verify CI passes with new tests before merge

- **Risk**: Test data inconsistency between unit and integration tests
  → **Mitigation**: Centralize fixtures in conftest.py; document test data generation

---

## Acceptance Criteria (Epic Level)

The epic is complete when:

- [ ] All 5 stories merged to develop
- [ ] Overall test coverage ≥ 80%
- [ ] password_reset coverage ≥ 80%
- [ ] adoption_requests coverage ≥ 80%
- [ ] No skipped tests without documented reason
- [ ] All new tests follow AAA pattern (Arrange/Act/Assert)
- [ ] CI pipeline runs all new tests and passes
- [ ] Frontend components have ≥ 70% coverage (lower bar for UI)

---

## Definition of Done (Epic)

- [ ] All user stories complete and merged
- [ ] Coverage report shows 80%+ overall, no decrease
- [ ] Code review approved by secondary reviewer
- [ ] All acceptance criteria checked
- [ ] Version bumped in `pyproject.toml` and `package.json`
- [ ] CHANGELOG.md updated with epic summary
- [ ] Deployed to staging and verified

---

*Last updated: 2026-03-27*
*Owner: Test Coverage Squad*
