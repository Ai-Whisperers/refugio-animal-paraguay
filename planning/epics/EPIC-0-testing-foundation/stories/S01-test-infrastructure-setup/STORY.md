---
id: EPIC-0-S01
title: Test Infrastructure Setup
epic: EPIC-0
status: ready
priority: critical
estimated_effort: 8 hours
---

# Story: Test Infrastructure Setup

## User Story
As a developer, I want a complete testing infrastructure (Vitest, React Testing Library, MSW, Playwright) installed and configured so that I can write unit, component, API, and E2E tests following consistent patterns.

## Acceptance Criteria
- [ ] Vitest installed and configured with TypeScript support
- [ ] React Testing Library integrated with vitest environment
- [ ] Mock Service Worker (MSW) configured for API mocking
- [ ] Playwright installed and configured for E2E testing
- [ ] All test configurations pass validation (can run a sample test)
- [ ] Documentation created for running tests locally and in CI
- [ ] Coverage instrumentation configured (80% threshold)

## Tasks
| Task ID | Title | Agent Type | Status |
|---------|-------|-----------|--------|
| T01 | Install Vitest and React Testing Library | code | ready |
| T02 | Configure TypeScript for testing environments | code | ready |
| T03 | Set up test utilities and helper functions | code | ready |
| T04 | Configure Mock Service Worker for API mocking | code | ready |
| T05 | Set up Playwright for E2E testing | code | ready |

## Dependencies
- None — foundational work
- Assumes Next.js 14 project initialized with TypeScript

## Technical Notes

### Vitest Setup
- Install: `npm install -D vitest @vitest/ui @vitest/coverage-v8`
- Config file: `vitest.config.ts` at project root
- Environment: jsdom for DOM testing
- Coverage: Istanbul provider, 80% threshold

### React Testing Library
- Install: `npm install -D @testing-library/react @testing-library/jest-dom`
- Use `@testing-library/jest-dom` for matchers
- Follow user-centric testing approach

### MSW Setup
- Install: `npm install -D msw`
- Create `lib/msw/` with handlers and fixtures
- Set up both browser and node environments

### Playwright
- Install: `npm install -D @playwright/test`
- Config: `playwright.config.ts`
- Support Chromium, Firefox, WebKit

## Definition of Done
- [ ] All dependencies installed successfully
- [ ] Sample test files run without errors
- [ ] Coverage instrumentation reports metrics
- [ ] TypeScript compilation clean
- [ ] All 5 tasks completed and merged

---
**Created**: 2026-03-25
**Status**: 🟢 Ready for work
