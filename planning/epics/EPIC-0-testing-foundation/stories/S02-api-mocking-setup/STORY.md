---
epic: EPIC-0
story: S02
title: API Mocking Setup (Mock Service Worker)
status: pending
effort_hours: 6
priority: high
dependencies:
  - EPIC-0/S01
acceptance_criteria:
  - MSW (Mock Service Worker) installed and configured
  - Handlers created for all core Supabase routes (auth, database, storage)
  - Mock handlers work in both browser and Node.js contexts
  - Network requests intercepted transparently in tests
  - Developers can extend handlers without modifying test infrastructure
---

## Overview

Set up Mock Service Worker (MSW) to intercept HTTP requests from both the browser (for Vitest component tests) and Node.js (for integration tests). This allows tests to run without hitting real Supabase endpoints, making tests faster, more reliable, and cheaper to run.

## Why This Matters

- **No external dependencies during tests**: Tests don't require Supabase credentials or network access
- **Deterministic responses**: Mock handlers always return the same data, making tests reproducible
- **Cost savings**: No actual API calls = no extra charges from Supabase
- **Parallel test execution**: Tests don't block each other waiting for I/O
- **Offline development**: Developers can test without internet connection

## Context

The animal shelter application communicates with Supabase for:
- Authentication (sign up, login, password reset)
- Database queries (animals, adoptions, donations, staff)
- File storage (animal photos, adoption documents)
- Real-time subscriptions

All these operations must be mocked at the HTTP level so tests remain isolated from infrastructure.

## Tasks

### T01: Install and Configure MSW for Browser Tests
**Effort**: 2 hours

Install Mock Service Worker and configure for Vitest + browser environment. Create browser setup file that initializes MSW for component tests.

**Acceptance Criteria**:
- MSW installed as dev dependency
- Browser service worker setup created
- Service worker registered before each test
- No console errors about MSW registration

### T02: Create Supabase Request Handlers
**Effort**: 2 hours

Create reusable MSW request handlers for all Supabase endpoints the application uses. Handlers should cover authentication, database operations, storage, and real-time events.

**Acceptance Criteria**:
- Handlers created for: `/auth/v1/*`, `/rest/v1/*`, `/storage/v1/*`
- Each handler returns realistic mock data matching Supabase response format
- Handlers include both success and error scenarios
- Easy to override handlers in individual tests

### T03: Node.js Server Setup and Server-Side Handlers
**Effort**: 2 hours

Configure MSW for Node.js environment (for integration tests and API route testing). Set up server-side request interception that works with Vitest.

**Acceptance Criteria**:
- MSW Node.js server created in test setup
- Server started before all tests, stopped after
- Node.js handlers mirror browser handlers
- Integration tests can override handlers per test

## Related Files

- `.vitest/setup.ts` - MSW initialization
- `.vitest/handlers/auth.ts` - Authentication request handlers
- `.vitest/handlers/database.ts` - Database query handlers
- `.vitest/handlers/storage.ts` - File storage handlers
- `.vitest/handlers/index.ts` - Handler exports and utilities

## Notes

MSW is crucial for test reliability. Without proper mocking, tests would:
- Require real Supabase credentials in test environment
- Make actual network calls (slow + unreliable)
- Cost money every time tests run
- Fail if network is unavailable

The goal is to make HTTP traffic completely transparent to tests.
