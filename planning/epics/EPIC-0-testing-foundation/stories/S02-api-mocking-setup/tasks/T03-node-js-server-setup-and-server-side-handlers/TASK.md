---
epic: EPIC-0
story: S02
task: T03
title: "Node.js Server Setup and Server-Side Handlers"
description: "Configure Mock Service Worker (MSW) for Node.js server-side testing with request handlers that mirror browser handlers"
effort_hours: 2
priority: high
dependencies:
  - T01-install-and-configure-msw-for-browser-tests
  - T02-create-supabase-request-handlers
status: planned
created_date: 2026-03-25
last_updated: 2026-03-25
tags:
  - testing
  - mocking
  - msw
  - node.js
  - server-side-testing
---

## Acceptance Criteria

### 1. Server-Side MSW Configuration
- [ ] `.vitest/setup-server.ts` file created with setupServer configuration
- [ ] setupServer aggregates all handlers (auth, REST, storage)
- [ ] Server instance properly scoped for test isolation
- [ ] Before/after hooks prevent handler state leakage
- [ ] Server resets between tests to ensure clean state

### 2. Server-Side Handlers Setup
- [ ] `.vitest/handlers/server.ts` created exporting server instance
- [ ] All browser handlers (auth, REST, storage) imported and reused
- [ ] Server-side handlers identical to browser handlers (DRY principle)
- [ ] Handler layer is environment-agnostic
- [ ] No browser-specific code in shared handlers

### 3. Test Utilities for Server-Side Testing
- [ ] `.vitest/utils/server-test-helpers.ts` created with utility functions:
  - `getAuthorizedHeaders()` — returns headers with mock JWT token
  - `createMockUser()` — creates authenticated user context
  - `createMockDonor()` — creates donor test data
  - `createMockAnimal()` — creates animal test data
  - `resetServerState()` — clears handler state between tests
- [ ] Helper functions return typed objects matching Supabase response format
- [ ] Helpers support customization (override defaults)
- [ ] Handlers properly documented with TypeScript JSDoc

### 4. Integration Tests Sample
- [ ] `tests/integration/api/auth.integration.test.ts` created demonstrating:
  - Server-side signup flow with successful JWT token return
  - Login with email/password and token refresh
  - Authenticated user profile retrieval
  - Password recovery request flow
  - Logout clearing session
  - Error handling (400, 401, 404 responses)
- [ ] All tests pass with server-side handlers
- [ ] Tests verify JWT token in Authorization header
- [ ] Tests validate response structure matches TypeScript types

### 5. REST API Integration Tests Sample
- [ ] `tests/integration/api/animals.integration.test.ts` created demonstrating:
  - Fetch animals list with pagination (Content-Range header)
  - Fetch single animal by ID
  - Create animal (POST with Authorization)
  - Update animal (PATCH with Authorization)
  - Multi-currency donation context (PYG, EUR, USD)
  - Error handling (401 without token, 404 not found)
- [ ] Tests verify paginated response structure
- [ ] Tests verify animals sorted by adoption_priority
- [ ] Tests validate Content-Range header format

### 6. Storage API Integration Tests Sample
- [ ] `tests/integration/api/storage.integration.test.ts` created demonstrating:
  - File upload to animals bucket
  - File retrieval by name
  - File deletion
  - List files in bucket
  - Copy file operation
  - Error handling (403 forbidden, 404 not found)
- [ ] Tests verify file metadata in response
- [ ] Tests validate bucket path structure
- [ ] Tests verify proper blob handling

### 7. TypeScript Configuration
- [ ] vitest.config.ts updated with Node.js globals if needed
- [ ] Environment-specific configuration for server tests
- [ ] No conflicts between browser and server test environments

### 8. Documentation
- [ ] `.vitest/README.md` created documenting:
  - MSW setup for both browser and server
  - How to add new request handlers
  - How to mock errors and edge cases
  - How to test authenticated endpoints
  - Common patterns for testing Supabase APIs
- [ ] Examples provided for each handler type (auth, REST, storage)
- [ ] Troubleshooting section for common issues

---

## Implementation Steps

### Step 1: Create Server-Side MSW Setup

**File**: `.vitest/setup-server.ts`

```typescript
import { setupServer } from 'msw/node';
import { authHandlers } from './handlers/supabase-auth';
import { restHandlers } from './handlers/supabase-rest';
import { storageHandlers } from './handlers/supabase-storage';

/**
 * Mock Service Worker server setup for Node.js test environment.
 * Aggregates all request handlers for auth, REST API, and storage.
 *
 * Usage in tests:
 * ```typescript
 * import { server } from '.vitest/setup-server';
 *
 * beforeAll(() => server.listen());
 * afterEach(() => server.resetHandlers());
 * afterAll(() => server.close());
 * ```
 */
export const server = setupServer(
  ...authHandlers,
  ...restHandlers,
  ...storageHandlers
);

// Log unhandled requests in development
if (process.env.DEBUG_MSW) {
  server.events.on('request:unhandled', ({ request }) => {
    console.warn(`[MSW] Unhandled ${request.method} ${request.url}`);
  });
}
```

### Step 2: Create Server Handler Export

**File**: `.vitest/handlers/server.ts`

```typescript
/**
 * Re-exports all MSW handlers for server-side use.
 * Ensures handlers are environment-agnostic (browser and server use same handlers).
 */

export { authHandlers } from './supabase-auth';
export { restHandlers } from './supabase-rest';
export { storageHandlers } from './supabase-storage';

// Export aggregated handlers list for setupServer
import { authHandlers } from './supabase-auth';
import { restHandlers } from './supabase-rest';
import { storageHandlers } from './supabase-storage';

export const allHandlers = [
  ...authHandlers,
  ...restHandlers,
  ...storageHandlers,
];
```

### Step 3: Create Server-Side Test Helpers

**File**: `.vitest/utils/server-test-helpers.ts`

```typescript
import type { MockUser, MockDonor, MockAnimal, SupabaseAuthResponse } from '../handlers/types';

const MOCK_JWT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoiZG9ub3JAZXhhbXBsZS5jb20iLCJpYXQiOjE2Nzc5MTUwMDB9.mock_signature';

/**
 * Returns HTTP headers with mock JWT token for authenticated requests.
 *
 * @param token - Optional custom JWT token (defaults to mock token)
 * @returns Object with Authorization header for Supabase API requests
 *
 * @example
 * const headers = getAuthorizedHeaders();
 * const response = await fetch(`${SUPABASE_URL}/rest/v1/animals`, { headers });
 */
export function getAuthorizedHeaders(token: string = MOCK_JWT_TOKEN): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

/**
 * Creates a mock user for authenticated test contexts.
 *
 * @param overrides - Partial user properties to override defaults
 * @returns Mock user object matching Supabase user schema
 *
 * @example
 * const user = createMockUser({ email: 'custom@example.com' });
 */
export function createMockUser(overrides?: Partial<MockUser>): MockUser {
  return {
    id: 'user-123',
    email: 'donor@example.com',
    email_confirmed_at: '2026-03-01T00:00:00Z',
    phone: null,
    confirmation_sent_at: null,
    confirmed_at: '2026-03-01T00:00:00Z',
    recovery_sent_at: null,
    last_sign_in_at: '2026-03-25T00:00:00Z',
    app_metadata: { provider: 'email' },
    user_metadata: { full_name: 'John Smith' },
    aud: 'authenticated',
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-25T00:00:00Z',
    ...overrides,
  };
}

/**
 * Creates a mock donor for testing donor-related endpoints.
 *
 * @param overrides - Partial donor properties to override defaults
 * @returns Mock donor object with payment and location data
 *
 * @example
 * const europeanDonor = createMockDonor({
 *   country: 'NL',
 *   preferred_currency: 'EUR'
 * });
 */
export function createMockDonor(overrides?: Partial<MockDonor>): MockDonor {
  return {
    id: 'donor-123',
    user_id: 'user-123',
    email: 'donor@example.com',
    full_name: 'John Smith',
    country: 'NL',
    preferred_currency: 'EUR',
    monthly_amount: 50.00,
    payment_method: 'ideal',
    is_active: true,
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-25T00:00:00Z',
    ...overrides,
  };
}

/**
 * Creates a mock animal for testing animal catalog endpoints.
 *
 * @param overrides - Partial animal properties to override defaults
 * @returns Mock animal object with shelter and adoption data
 *
 * @example
 * const adoptableAnimal = createMockAnimal({
 *   status: 'adoptable',
 *   adoption_priority: 1
 * });
 */
export function createMockAnimal(overrides?: Partial<MockAnimal>): MockAnimal {
  return {
    id: 'animal-123',
    shelter_id: 'shelter-001',
    name: 'Luna',
    species: 'dog',
    breed: 'mixed',
    age_months: 24,
    gender: 'female',
    status: 'available',
    adoption_priority: 2,
    description: 'Friendly and energetic dog',
    image_url: 'https://example.com/luna.jpg',
    arrival_date: '2025-12-01T00:00:00Z',
    microchip_id: 'CHIP123456789',
    medical_notes: 'Vaccinated, neutered',
    created_at: '2025-12-01T00:00:00Z',
    updated_at: '2026-03-25T00:00:00Z',
    ...overrides,
  };
}

/**
 * Resets server state between tests to ensure clean isolation.
 * Imported server must be accessible for this to work.
 *
 * @param server - MSW server instance from setup-server.ts
 *
 * @example
 * afterEach(() => resetServerState(server));
 */
export async function resetServerState(server: any): Promise<void> {
  server.resetHandlers();
}
```

### Step 4: Create Sample Auth Integration Test

**File**: `tests/integration/api/auth.integration.test.ts`

```typescript
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest';
import { server } from '../../../.vitest/setup-server';
import { getAuthorizedHeaders, createMockUser } from '../../../.vitest/utils/server-test-helpers';

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://project.supabase.co';

describe('Supabase Auth API - Server-Side Integration Tests', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  describe('POST /auth/v1/signup', () => {
    it('should create new user with valid email and password', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'newdonor@example.com',
          password: 'secure_password_123',
        }),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.user).toBeDefined();
      expect(data.user.email).toBe('newdonor@example.com');
      expect(data.session).toBeDefined();
      expect(data.session.access_token).toBeDefined();
      expect(data.session.token_type).toBe('bearer');
    });

    it('should return 400 for invalid email', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'invalid-email',
          password: 'password123',
        }),
      });

      expect(response.status).toBe(400);
      const data = await response.json();
      expect(data.error).toBeDefined();
    });
  });

  describe('POST /auth/v1/token', () => {
    it('should return access token with valid credentials (password grant)', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'donor@example.com',
          password: 'password123',
        }),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.access_token).toBeDefined();
      expect(data.token_type).toBe('bearer');
      expect(data.refresh_token).toBeDefined();
    });

    it('should return 401 for invalid credentials', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'donor@example.com',
          password: 'wrong_password',
        }),
      });

      expect(response.status).toBe(401);
    });
  });

  describe('GET /auth/v1/user', () => {
    it('should return authenticated user profile', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
        method: 'GET',
        headers,
      });

      expect(response.status).toBe(200);
      const user = await response.json();
      expect(user.id).toBe('user-123');
      expect(user.email).toBe('donor@example.com');
      expect(user.user_metadata).toBeDefined();
    });

    it('should return 401 without Authorization header', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(401);
    });
  });

  describe('POST /auth/v1/logout', () => {
    it('should logout user and return 204', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: 'POST',
        headers,
      });

      expect(response.status).toBe(204);
    });

    it('should return 401 without token', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(401);
    });
  });

  describe('POST /auth/v1/recover', () => {
    it('should send password recovery email', async () => {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/recover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'donor@example.com',
        }),
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.message).toContain('Recovery link sent');
    });
  });
});
```

### Step 5: Create Sample Animals REST API Integration Test

**File**: `tests/integration/api/animals.integration.test.ts`

```typescript
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest';
import { server } from '../../../.vitest/setup-server';
import { getAuthorizedHeaders, createMockAnimal } from '../../../.vitest/utils/server-test-helpers';

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://project.supabase.co';

describe('Supabase REST API - Animals Endpoints Integration Tests', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  describe('GET /rest/v1/animals', () => {
    it('should return paginated list of animals', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals?limit=10&offset=0`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(200);
      const animals = await response.json();
      expect(Array.isArray(animals)).toBe(true);
      expect(animals.length).toBeGreaterThan(0);

      const contentRange = response.headers.get('Content-Range');
      expect(contentRange).toBeDefined();
      expect(contentRange).toMatch(/\d+-\d+\/\d+/);
    });

    it('should filter animals by status', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals?status=eq.available`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(200);
      const animals = await response.json();
      animals.forEach((animal: any) => {
        expect(animal.status).toBe('available');
      });
    });

    it('should sort animals by adoption priority', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals?order=adoption_priority.asc`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(200);
      const animals = await response.json();
      for (let i = 0; i < animals.length - 1; i++) {
        expect(animals[i].adoption_priority).toBeLessThanOrEqual(animals[i + 1].adoption_priority);
      }
    });
  });

  describe('GET /rest/v1/animals/:id', () => {
    it('should return single animal by ID', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals/animal-123`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(200);
      const animal = await response.json();
      expect(animal.id).toBe('animal-123');
      expect(animal.name).toBe('Luna');
      expect(animal.species).toBe('dog');
    });

    it('should return 404 for non-existent animal', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals/non-existent-id`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      expect(response.status).toBe(404);
    });
  });

  describe('POST /rest/v1/animals', () => {
    it('should create new animal with authentication', async () => {
      const headers = getAuthorizedHeaders();
      const newAnimal = createMockAnimal({
        name: 'Felix',
        species: 'cat',
        breed: 'siamese',
      });

      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newAnimal),
      });

      expect(response.status).toBe(201);
      const created = await response.json();
      expect(created.name).toBe('Felix');
      expect(created.id).toBeDefined();
    });

    it('should return 401 without authentication', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createMockAnimal()),
      });

      expect(response.status).toBe(401);
    });
  });

  describe('PATCH /rest/v1/animals/:id', () => {
    it('should update animal with authentication', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals/animal-123`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({
          status: 'adopted',
          adoption_date: '2026-03-25T00:00:00Z',
        }),
      });

      expect(response.status).toBe(200);
      const updated = await response.json();
      expect(updated.status).toBe('adopted');
    });

    it('should return 401 without authentication', async () => {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/animals/animal-123`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'adopted' }),
      });

      expect(response.status).toBe(401);
    });
  });
});
```

### Step 6: Create Sample Storage API Integration Test

**File**: `tests/integration/api/storage.integration.test.ts`

```typescript
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest';
import { server } from '../../../.vitest/setup-server';
import { getAuthorizedHeaders } from '../../../.vitest/utils/server-test-helpers';

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://project.supabase.co';
const ANIMALS_BUCKET = 'animals';

describe('Supabase Storage API - Files Integration Tests', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  describe('POST /storage/v1/b/:bucket/upload', () => {
    it('should upload file to animals bucket with metadata', async () => {
      const headers = getAuthorizedHeaders();

      const formData = new FormData();
      const blob = new Blob(['test image data'], { type: 'image/jpeg' });
      formData.append('file', blob, 'luna-profile.jpg');
      formData.append('bucket_id', ANIMALS_BUCKET);
      formData.append('name', 'luna-profile.jpg');

      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/upload`,
        {
          method: 'POST',
          headers: { Authorization: headers.Authorization },
          body: formData,
        }
      );

      expect(response.status).toBe(200);
      const result = await response.json();
      expect(result.Key).toBe('luna-profile.jpg');
    });

    it('should return 401 without authentication', async () => {
      const formData = new FormData();
      const blob = new Blob(['test'], { type: 'image/jpeg' });
      formData.append('file', blob, 'test.jpg');

      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/upload`,
        { method: 'POST', body: formData }
      );

      expect(response.status).toBe(401);
    });
  });

  describe('GET /storage/v1/b/:bucket/o/:fileName', () => {
    it('should retrieve file from animals bucket', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/o/luna-profile.jpg`,
        { method: 'GET', headers }
      );

      expect(response.status).toBe(200);
      expect(response.headers.get('Content-Type')).toContain('image');
    });

    it('should return 404 for non-existent file', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/o/nonexistent.jpg`,
        { method: 'GET', headers }
      );

      expect(response.status).toBe(404);
    });
  });

  describe('DELETE /storage/v1/b/:bucket/o/:fileName', () => {
    it('should delete file from animals bucket', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/o/luna-profile.jpg`,
        { method: 'DELETE', headers }
      );

      expect(response.status).toBe(204);
    });

    it('should return 401 without authentication', async () => {
      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/o/luna-profile.jpg`,
        { method: 'DELETE' }
      );

      expect(response.status).toBe(401);
    });
  });

  describe('GET /storage/v1/b/:bucket/list', () => {
    it('should list files in animals bucket', async () => {
      const headers = getAuthorizedHeaders();
      const response = await fetch(
        `${SUPABASE_URL}/storage/v1/b/${ANIMALS_BUCKET}/list`,
        { method: 'GET', headers }
      );

      expect(response.status).toBe(200);
      const files = await response.json();
      expect(Array.isArray(files)).toBe(true);
    });
  });
});
```

### Step 7: Update vitest.config.ts

Add Node.js globals configuration if needed:

```typescript
export default defineConfig({
  test: {
    // ... existing browser config ...
    globals: true,
    environment: 'jsdom',
    setupFiles: ['.vitest/setup.ts'],
    // Server-side tests can use the same config or override
  },
});
```

### Step 8: Create Documentation

**File**: `.vitest/README.md`

```markdown
# Mock Service Worker (MSW) Setup

This directory contains Mock Service Worker configuration for testing Supabase APIs in both browser and Node.js environments.

## Structure

```
.vitest/
├── setup.ts              # Browser test setup with beforeAll/afterEach hooks
├── setup-server.ts       # Node.js server setup
├── handlers/
│   ├── supabase-auth.ts  # Authentication endpoint handlers
│   ├── supabase-rest.ts  # REST API endpoint handlers
│   ├── supabase-storage.ts # Storage endpoint handlers
│   ├── server.ts         # Re-export handlers for server use
│   └── types.ts          # TypeScript type definitions
└── utils/
    └── server-test-helpers.ts # Utility functions for tests
```

## Browser-Side Testing

```typescript
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from '.vitest/setup-server';

describe('My API Test', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  it('should fetch data', async () => {
    const response = await fetch('https://project.supabase.co/rest/v1/animals');
    expect(response.status).toBe(200);
  });
});
```

## Adding New Handlers

1. Create new handler file in `handlers/` directory
2. Export handlers as array: `export const myHandlers = [...]`
3. Import and include in `setup-server.ts`
4. Test with `server.use(handler)` override

## Mocking Errors

Override specific handlers for error scenarios:

```typescript
import { server } from '.vitest/setup-server';
import { http, HttpResponse } from 'msw';

it('should handle 401 errors', () => {
  server.use(
    http.get('https://project.supabase.co/rest/v1/animals', () => {
      return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 });
    })
  );

  // Test unauthorized access
});
```

## Testing Authenticated Endpoints

Use `getAuthorizedHeaders()` helper:

```typescript
import { getAuthorizedHeaders } from '.vitest/utils/server-test-helpers';

const headers = getAuthorizedHeaders();
const response = await fetch(url, { headers });
```

## Mock Data Helpers

Create test data with builders:

```typescript
import {
  createMockUser,
  createMockDonor,
  createMockAnimal,
} from '.vitest/utils/server-test-helpers';

const user = createMockUser({ email: 'custom@example.com' });
const europeanDonor = createMockDonor({ country: 'NL', preferred_currency: 'EUR' });
const adoptableAnimal = createMockAnimal({ status: 'adoptable' });
```

## Common Issues

### "Unhandled request" warnings
Verify the URL matches exactly. Check:
- Correct Supabase URL (with protocol)
- Query string parameters included in URL
- HTTP method matches handler

### JWT token not recognized
Ensure `Authorization: Bearer <token>` header format. Use `getAuthorizedHeaders()` helper.

### File upload test failing
FormData handling: ensure blob and filename are set correctly.

## Performance

MSW is fast (~1-5ms per request). If tests slow down:
- Use `afterEach(() => server.resetHandlers())` to clear state
- Avoid creating new handlers inside tests
- Batch assertions when possible
```

---

## Definition of Done

- [ ] All implementation steps completed
- [ ] All acceptance criteria verified
- [ ] TypeScript compilation passes (zero errors)
- [ ] All integration tests pass
- [ ] Code follows project style conventions
- [ ] Documentation updated (.vitest/README.md)
- [ ] No console errors or warnings
- [ ] Ready for code review

---

## Notes

- Server-side handlers are identical to browser handlers (DRY principle enforced)
- Test helpers provide typed interfaces for mock data
- Integration tests demonstrate each API endpoint category
- Error scenarios (401, 404) included in tests
- Multi-currency support (PYG, EUR, USD) included in mock donor data
- All file paths follow project structure conventions
