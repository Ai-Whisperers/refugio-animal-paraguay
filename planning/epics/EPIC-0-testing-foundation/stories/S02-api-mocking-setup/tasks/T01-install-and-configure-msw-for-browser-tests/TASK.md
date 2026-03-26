---
story: S02
task: T01
title: Install and Configure MSW for Browser Tests
status: pending
effort_hours: 2
priority: high
dependencies: []
acceptance_criteria:
  - MSW installed as dev dependency
  - Browser service worker setup created at .vitest/handlers/browser.ts
  - Service worker registered in vitest.config.ts before each test
  - No console errors about MSW registration
  - Tests can import mock handlers without errors
---

## Overview

Install Mock Service Worker (MSW) and configure it for the Vitest browser testing environment. This task prepares the browser-side HTTP interception layer that will allow component and UI tests to run without hitting real Supabase endpoints.

## Why This Matters

Without MSW configured for browser tests, Vitest's jsdom environment would attempt to make real HTTP requests during component testing. This leads to:
- Tests failing due to missing credentials
- Network timeouts slowing down test runs
- Unnecessary API calls hitting real Supabase
- Tests that depend on external infrastructure being unavailable

## Context

The Refugio Animal Paraguay application runs in a browser environment (Next.js frontend) where components interact with Supabase via the `@supabase/supabase-js` client library. These HTTP calls need to be intercepted at the network level during tests.

**Related Files**:
- `vitest.config.ts` - Test framework configuration
- `package.json` - Dependencies
- `.vitest/handlers/browser.ts` - Service worker setup (to be created in this task)
- `src/**/*.test.tsx` - Component test files that will use MSW

## Implementation Steps

### Step 1: Install MSW as Dev Dependency

Install Mock Service Worker and its peer dependencies:

```bash
npm install --save-dev msw
npm install --save-dev @types/node  # Required for service worker types
```

**Verification**:
- `msw` appears in `package.json` devDependencies
- `npm list msw` shows version ≥1.3.0

### Step 2: Create Browser Service Worker Setup

Create `.vitest/handlers/browser.ts` that initializes MSW for the browser environment:

```typescript
import { setupServer } from 'msw/node';
import { setupWorker } from 'msw/browser';
import { handlers } from './index';

/**
 * Browser-side MSW setup for Vitest component tests
 *
 * MSW will intercept HTTP requests in jsdom before they leave the "browser"
 * This allows components to use @supabase/supabase-js without hitting real endpoints
 */

export const server = setupServer(...handlers);

export const worker = setupWorker(...handlers);

/**
 * Start the worker (called in vitest setup file)
 * This must happen BEFORE any components are rendered in tests
 */
export async function startMSW() {
  return await worker.start({
    onUnhandledRequest: 'warn',
  });
}

/**
 * Stop the worker (called after all tests complete)
 */
export function stopMSW() {
  return worker.stop();
}

/**
 * Reset handlers between tests to prevent state leakage
 */
export function resetMSW() {
  worker.resetHandlers();
}
```

**Verification**:
- File created at correct path
- TypeScript compiles without errors
- `setupWorker` is imported from `msw/browser` (not `msw/node`)

### Step 3: Update vitest.config.ts

Configure Vitest to initialize MSW before running tests:

```typescript
// In vitest.config.ts, add to the config object:

export default defineConfig({
  test: {
    // ... other config ...

    environment: 'jsdom',

    setupFiles: [
      // MSW setup must run before any tests
      './.vitest/setup.ts',
    ],

    // Global test timeout
    testTimeout: 10000,

    // Ensure jsdom runs in browser context (required for MSW)
    pool: 'threads',
  },
});
```

### Step 4: Create Vitest Setup File

Create `.vitest/setup.ts` to initialize MSW before tests run:

```typescript
import { beforeAll, afterEach, afterAll } from 'vitest';
import { worker, resetMSW } from './handlers/browser';

/**
 * Start MSW before all tests
 * This must complete before any test runs
 */
beforeAll(async () => {
  await worker.start({
    onUnhandledRequest: 'warn',
  });
});

/**
 * Reset MSW handlers between tests
 * Prevents mock state from leaking between tests
 */
afterEach(() => {
  resetMSW();
});

/**
 * Stop MSW after all tests complete
 * Cleanup to prevent port conflicts if tests run again
 */
afterAll(() => {
  worker.stop();
});
```

**Verification**:
- File created at `.vitest/setup.ts`
- `beforeAll` hook properly initializes worker
- `afterEach` hook resets handlers
- `afterAll` hook cleans up

### Step 5: Test MSW Registration

Create a simple test to verify MSW is working:

```typescript
// .vitest/handlers/__tests__/msw-health.test.ts

import { describe, it, expect } from 'vitest';
import { worker } from '../browser';

describe('MSW Setup Health Check', () => {
  it('should have MSW worker initialized', () => {
    expect(worker).toBeDefined();
  });

  it('should be able to reset handlers without errors', () => {
    expect(() => worker.resetHandlers()).not.toThrow();
  });
});
```

Run with: `npm test -- msw-health.test.ts`

## Acceptance Criteria Verification

- [ ] `npm list msw` shows MSW installed
- [ ] `.vitest/handlers/browser.ts` exists with proper exports
- [ ] `vitest.config.ts` includes `setupFiles: ['./.vitest/setup.ts']`
- [ ] `.vitest/setup.ts` exists with beforeAll, afterEach, afterAll hooks
- [ ] `npm run test -- msw-health.test.ts` passes without console errors
- [ ] No "MSW worker not initialized" warnings in test output
- [ ] No "unhandled request" warnings for requests to MSW handlers

## Common Issues & Solutions

### Issue: "TypeError: Cannot read properties of undefined (reading 'start')"
**Cause**: MSW worker not properly imported or setupFiles hook not running
**Solution**: Verify setupFiles is correctly configured in vitest.config.ts and beforeAll hook runs before tests

### Issue: "XMLHttpRequest is not defined"
**Cause**: jsdom environment not properly configured
**Solution**: Ensure `environment: 'jsdom'` is set in vitest.config.ts

### Issue: "Service Worker registration failed"
**Cause**: Port conflict or permission issues
**Solution**: Check that no other processes are using the MSW port, or restart test runner

## Related Tasks

- S02/T02: Create Supabase Request Handlers — defines what requests MSW will intercept
- S02/T03: Node.js Server Setup — configures server-side MSW for integration tests

## References

- [MSW Official Documentation](https://mswjs.io/)
- [MSW Browser Setup Guide](https://mswjs.io/docs/getting-started)
- [Vitest Setup Files](https://vitest.dev/config/#setupfiles)
- [jsdom Environment](https://github.com/jsdom/jsdom)
