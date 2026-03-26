---
id: EPIC-0
title: Testing Foundation
description: Establish comprehensive testing infrastructure and best practices
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
3. **Blocks architectural decisions** — testing choices (unit vs integration vs E2E) influence how features are structured
4. **Enables confidence** — teams can refactor and optimize knowing tests catch regressions

**Critical dependency**: EPIC-0 must be **complete and merged to main** before any developer starts work on EPIC-1, EPIC-4, EPIC-5, etc.

## Scope

This epic covers:

### Testing Frameworks & Tools

- **Vitest**: Lightning-fast unit testing framework (replaces Jest for Next.js 14)
- **React Testing Library**: Modern component testing focusing on user behavior
- **Mock Service Worker (MSW)**: API mocking without modifying production code
- **Playwright**: End-to-end browser testing
- **Coverage instrumentation**: Tracking and reporting test coverage metrics

### Testing Strategy Layers

```
┌─────────────────────────────────────┐
│  E2E Testing (Playwright)           │ User journeys across entire app
├─────────────────────────────────────┤
│  Integration Testing (Vitest)       │ Component + API interaction
├─────────────────────────────────────┤
│  Component Testing (RTL)            │ Individual component behavior
├─────────────────────────────────────┤
│  Unit Testing (Vitest)              │ Pure functions, utilities
├─────────────────────────────────────┤
│  API Mocking (MSW)                  │ Intercept and mock HTTP requests
└─────────────────────────────────────┘
```

### Testing Best Practices

- Test organization structure (unit, integration, e2e directories)
- Naming conventions for test files (`.test.ts`, `.spec.ts`)
- Test data fixtures and factories
- Mocking strategies (MSW for external APIs, mocks for internal dependencies)
- Coverage requirements and measurement
- CI/CD integration with GitHub Actions
- Documentation for developers on how to write tests

## Stories in This Epic

This epic contains 5 stories:

| Story ID | Title | Purpose |
|----------|-------|---------|
| **S01** | Test Infrastructure Setup | Install and configure Vitest, React Testing Library, MSW, Playwright |
| **S02** | Component Testing Foundation | Write tests for reusable components, establish patterns |
| **S03** | API Integration Testing | Test API calls with MSW mocking, error scenarios |
| **S04** | E2E Testing Infrastructure | Set up Playwright, basic user journey tests |
| **S05** | Coverage & CI/CD Integration | Measure coverage, enforce thresholds, integrate with GitHub Actions |

## Technical Architecture

### Directory Structure

```
app/
├── (auth)/
├── (dashboard)/
├── api/
└── __tests__/          ← Test directory
    ├── unit/           ← Pure function tests
    ├── integration/    ← Component + API tests
    └── e2e/            ← Playwright scenarios

lib/
└── __tests__/
    └── utils/          ← Utility function tests

components/
└── __tests__/          ← Component tests co-located with components
    └── AnimalCard.test.tsx

playwright/
├── fixtures/           ← Test data and setup
├── pages/              ← Page object models
└── tests/              ← E2E test suites
```

### Configuration Files

**Vitest Configuration** (`vitest.config.ts`):
- ESM module resolution
- jsdom environment for DOM testing
- TypeScript support
- Coverage reporting (80% threshold)

**MSW Configuration** (`lib/msw/`):
- API request handlers
- Fixtures for common responses
- Error response patterns
- Development and testing modes

**Playwright Configuration** (`playwright.config.ts`):
- Chromium, Firefox, WebKit browsers
- Base URL configuration
- Timeout and retry settings
- Screenshot/video capture on failure

## Success Criteria

- ✅ All testing frameworks installed and configured
- ✅ Sample unit tests written demonstrating patterns
- ✅ Sample component tests written with React Testing Library
- ✅ MSW configured and working for API mocking
- ✅ Playwright E2E tests running successfully
- ✅ CI/CD pipeline enforces 80% test coverage
- ✅ Test documentation available for developers
- ✅ GitHub Actions workflow runs tests on every PR

## Dependencies

### Blocks (what this epic enables)

- **EPIC-1** (Animal Catalog) — depends on component testing setup
- **EPIC-2** (Adoption Process) — depends on form testing patterns
- **EPIC-3** (Lost & Found) — depends on component testing
- **EPIC-4** (Donations) — depends on payment integration testing
- **EPIC-5** (Admin Panel) — depends on auth testing patterns
- **EPIC-6** (User Portal) — depends on full testing stack
- **EPIC-8** (Infrastructure) — depends on API testing setup

### Blocked By (prerequisites)

- None — this is the foundational epic
- Assumes Next.js 14 project initialized with TypeScript

## Effort Estimate

| Story | Estimated Hours | Complexity |
|-------|-----------------|-----------|
| S01 - Setup | 8 hours | Medium (configuration heavy) |
| S02 - Component Testing | 12 hours | Medium (pattern establishment) |
| S03 - API Integration | 10 hours | Medium (MSW mastery) |
| S04 - E2E Testing | 7 hours | Low (Playwright is intuitive) |
| S05 - Coverage & CI/CD | 3 hours | Low (automation) |
| **TOTAL** | **40 hours** | **Medium** |

Effort assumes:
- 2 developers working in parallel (S01 splits into Vitest + Playwright setup)
- Moderate familiarity with testing concepts
- Access to project initialization and configuration

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Vitest + Next.js 14 compatibility | Low | High | Use current versions, check docs |
| MSW learning curve | Medium | Medium | Pair programming, documentation |
| E2E test flakiness | Medium | High | Explicit waits, retry logic, good selectors |
| Coverage threshold too strict | Low | Medium | Start at 70%, increase incrementally |

## Resources

### Documentation Links

- [Vitest Official Docs](https://vitest.dev/)
- [React Testing Library Docs](https://testing-library.com/react)
- [Mock Service Worker Docs](https://mswjs.io/)
- [Playwright Docs](https://playwright.dev/)

### Internal References

- Tech Stack Reference: `AGENT-GUIDE.md` > Tech Stack Reference section
- Architecture Patterns: `docs/ARCHITECTURE.md` (if exists)
- Testing Strategy: `docs/TESTING-STRATEGY.md` (if exists)

## Next Steps After Completion

Once EPIC-0 is merged to main:

1. **Communicate completion** — notify team that testing foundation is ready
2. **Unlock feature work** — agents can claim tasks from EPIC-1, EPIC-4, EPIC-8
3. **Enforce coverage** — all future PRs must maintain 80% test coverage
4. **Document learnings** — capture testing patterns discovered during S02-S03
5. **Plan for scaling** — consider performance testing infrastructure for EPIC-7

## Progress Tracking

Track progress using the task queue:

```bash
# View all tasks in this epic
grep "EPIC-0" planning/QUEUE.md

# Check which tasks are ready
grep "status: ready" planning/epics/EPIC-0-testing-foundation/stories/*/tasks/*.md

# Monitor active claims
cat planning/CLAIMING.md  # Check EPIC-0 rows
```

## Communication

- Updates to task files after each work session
- Merge PRs promptly to unblock downstream work
- Slack notifications when epic reaches "review" status
- Final completion announcement before EPIC-1 work begins

---

**Created**: 2026-03-25
**Epic Lead**: [To be assigned]
**Status**: 🟢 Ready for work
**Priority**: 🔴 CRITICAL — Must complete before feature work
