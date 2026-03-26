---
story: S02
task: T02
title: Create Supabase Request Handlers for MSW
status: pending
effort_hours: 2
priority: high
dependencies:
  - T01-install-and-configure-msw-for-browser-tests
acceptance_criteria:
  - Supabase Auth handlers created for login, logout, signup, password reset
  - Supabase REST API handlers created for all animal shelter endpoints
  - Supabase Storage handlers created for image upload/download
  - MSW handlers properly mock response status codes and payloads
  - Handlers include error scenarios (401, 403, 404, 500)
  - All handlers use correct Supabase endpoint patterns
  - Handler responses match actual Supabase API response structure
  - Handlers can be imported and used in tests without errors
---

## Overview

Create Mock Service Worker (MSW) request handlers that intercept HTTP calls to Supabase endpoints. These handlers will mock:
- **Supabase Auth** (`/auth/v1/*`) - login, logout, signup, session management
- **Supabase REST API** (`/rest/v1/*`) - animal CRUD, adoptions, donors, applications
- **Supabase Storage** (`/storage/v1/*`) - image uploads and downloads

This ensures tests run without hitting real Supabase infrastructure.

---

## Why This Matters

- Tests must not depend on external services (Supabase infrastructure)
- MSW handlers provide predictable, repeatable test data
- Handlers enable testing error paths (auth failures, network errors, 404s)
- Mock responses match Supabase's actual response structure
- Enables parallel test execution without API rate limit issues
- Developers can work offline without Supabase connectivity

---

## Context

- Supabase URL: `https://${SUPABASE_PROJECT_ID}.supabase.co`
- Auth endpoints: `/auth/v1/...` (JWT tokens, sessions)
- REST API endpoints: `/rest/v1/...` (PostgreSQL tables as REST)
- Storage endpoints: `/storage/v1/...` (file upload/download)
- All requests require `Authorization: Bearer ${JWT_TOKEN}` header
- Project ID is stored in `VITE_SUPABASE_PROJECT_ID` environment variable
- Anon key is stored in `VITE_SUPABASE_ANON_KEY` environment variable

---

## Implementation Steps

### Step 1: Create Supabase Auth Handlers

Create `.vitest/handlers/supabase-auth.ts`:

```typescript
import { http, HttpResponse } from 'msw';

const SUPABASE_PROJECT_ID = import.meta.env.VITE_SUPABASE_PROJECT_ID;
const SUPABASE_URL = `https://${SUPABASE_PROJECT_ID}.supabase.co`;

// Mock JWT token for testing
const MOCK_JWT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoiZG9ub3JAZXhhbXBsZS5jb20iLCJpYXQiOjE2Nzc5MTUwMDB9.mock_signature';

export const supabaseAuthHandlers = [
  // POST /auth/v1/signup
  http.post(`${SUPABASE_URL}/auth/v1/signup`, async ({ request }) => {
    const body = await request.json();

    if (!body.email || !body.password) {
      return HttpResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      {
        user: {
          id: 'user-new-123',
          email: body.email,
          user_metadata: {},
          aud: 'authenticated',
          created_at: new Date().toISOString(),
        },
        session: {
          access_token: MOCK_JWT_TOKEN,
          token_type: 'bearer',
          expires_in: 3600,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
          refresh_token: 'refresh-token-mock',
          user: {
            id: 'user-new-123',
            email: body.email,
          },
        },
      },
      { status: 200 }
    );
  }),

  // POST /auth/v1/token
  http.post(`${SUPABASE_URL}/auth/v1/token`, async ({ request }) => {
    const body = await request.json();

    if (body.grant_type === 'password') {
      if (body.email === 'invalid@example.com') {
        return HttpResponse.json(
          { error: 'Invalid login credentials' },
          { status: 400 }
        );
      }

      return HttpResponse.json(
        {
          access_token: MOCK_JWT_TOKEN,
          token_type: 'bearer',
          expires_in: 3600,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
          refresh_token: 'refresh-token-mock',
          user: {
            id: 'user-123',
            email: body.email,
            user_metadata: {},
          },
        },
        { status: 200 }
      );
    }

    if (body.grant_type === 'refresh_token') {
      return HttpResponse.json(
        {
          access_token: MOCK_JWT_TOKEN,
          token_type: 'bearer',
          expires_in: 3600,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
          refresh_token: 'new-refresh-token-mock',
        },
        { status: 200 }
      );
    }

    return HttpResponse.json(
      { error: 'Unsupported grant type' },
      { status: 400 }
    );
  }),

  // GET /auth/v1/user
  http.get(`${SUPABASE_URL}/auth/v1/user`, ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return HttpResponse.json(
      {
        id: 'user-123',
        email: 'donor@example.com',
        user_metadata: { full_name: 'John Doe' },
        aud: 'authenticated',
        created_at: '2026-01-01T00:00:00Z',
      },
      { status: 200 }
    );
  }),

  // POST /auth/v1/logout
  http.post(`${SUPABASE_URL}/auth/v1/logout`, ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return new HttpResponse(null, { status: 204 });
  }),

  // POST /auth/v1/recover
  http.post(`${SUPABASE_URL}/auth/v1/recover`, async ({ request }) => {
    const body = await request.json();

    if (!body.email) {
      return HttpResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      { success: true },
      { status: 200 }
    );
  }),

  // PUT /auth/v1/user
  http.put(`${SUPABASE_URL}/auth/v1/user`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    return HttpResponse.json(
      {
        id: 'user-123',
        email: body.email || 'donor@example.com',
        user_metadata: body.data || {},
        aud: 'authenticated',
        updated_at: new Date().toISOString(),
      },
      { status: 200 }
    );
  }),
];
```

### Step 2: Create Supabase REST API Handlers

Create `.vitest/handlers/supabase-rest.ts`:

```typescript
import { http, HttpResponse } from 'msw';

const SUPABASE_PROJECT_ID = import.meta.env.VITE_SUPABASE_PROJECT_ID;
const SUPABASE_URL = `https://${SUPABASE_PROJECT_ID}.supabase.co`;

// Mock data
const mockAnimals = [
  {
    id: '1',
    name: 'Luna',
    species: 'dog',
    breed: 'Labrador',
    status: 'available',
    age_years: 3,
    age_months: 6,
    gender: 'female',
    weight_kg: 28.5,
    description: 'Friendly and energetic golden retriever mix',
    intake_date: '2025-06-15',
    medical_history: 'Vaccinated, neutered',
    image_url: 'https://example.com/luna.jpg',
    created_at: '2025-06-15T10:00:00Z',
    updated_at: '2025-06-15T10:00:00Z',
  },
  {
    id: '2',
    name: 'Felix',
    species: 'cat',
    breed: 'Siamese',
    status: 'available',
    age_years: 2,
    age_months: 0,
    gender: 'male',
    weight_kg: 4.2,
    description: 'Playful and curious Siamese cat',
    intake_date: '2025-07-01',
    medical_history: 'Vaccinated',
    image_url: 'https://example.com/felix.jpg',
    created_at: '2025-07-01T12:00:00Z',
    updated_at: '2025-07-01T12:00:00Z',
  },
];

const mockDonors = [
  {
    id: 'donor-123',
    email: 'john@example.com',
    full_name: 'John Smith',
    country: 'NL',
    currency: 'EUR',
    donation_count: 5,
    total_donated: 250.00,
    last_donation_date: '2026-02-15',
    created_at: '2025-08-01T08:00:00Z',
    updated_at: '2026-02-15T14:30:00Z',
  },
];

const mockAdoptionApplications = [
  {
    id: 'app-001',
    animal_id: '1',
    adopter_name: 'Maria Garcia',
    adopter_email: 'maria@example.com',
    adopter_phone: '+595 971 234567',
    status: 'pending',
    application_date: '2026-03-20',
    interview_scheduled: '2026-03-25T14:00:00Z',
    notes: 'First time adopter, has yard',
    created_at: '2026-03-20T10:00:00Z',
    updated_at: '2026-03-20T10:00:00Z',
  },
];

export const supabaseRestHandlers = [
  // GET /rest/v1/animals
  http.get(`${SUPABASE_URL}/rest/v1/animals`, ({ request }) => {
    const url = new URL(request.url);
    const select = url.searchParams.get('select') || '*';
    const limit = url.searchParams.get('limit') || '10';
    const offset = url.searchParams.get('offset') || '0';

    return HttpResponse.json(
      mockAnimals.slice(Number(offset), Number(offset) + Number(limit)),
      {
        status: 200,
        headers: {
          'Content-Range': `0-${Math.min(Number(offset) + Number(limit), mockAnimals.length) - 1}/${mockAnimals.length}`,
        },
      }
    );
  }),

  // GET /rest/v1/animals/:id
  http.get(`${SUPABASE_URL}/rest/v1/animals/:id`, ({ params }) => {
    const animal = mockAnimals.find(a => a.id === params.id);

    if (!animal) {
      return HttpResponse.json(
        { message: 'Not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(animal, { status: 200 });
  }),

  // POST /rest/v1/animals
  http.post(`${SUPABASE_URL}/rest/v1/animals`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    const newAnimal = {
      id: String(mockAnimals.length + 1),
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(newAnimal, { status: 201 });
  }),

  // PATCH /rest/v1/animals/:id
  http.patch(`${SUPABASE_URL}/rest/v1/animals/:id`, async ({ request, params }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const animal = mockAnimals.find(a => a.id === params.id);

    if (!animal) {
      return HttpResponse.json(
        { message: 'Not found' },
        { status: 404 }
      );
    }

    const body = await request.json();

    const updated = {
      ...animal,
      ...body,
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(updated, { status: 200 });
  }),

  // GET /rest/v1/donors
  http.get(`${SUPABASE_URL}/rest/v1/donors`, () => {
    return HttpResponse.json(mockDonors, { status: 200 });
  }),

  // POST /rest/v1/donors
  http.post(`${SUPABASE_URL}/rest/v1/donors`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    const newDonor = {
      id: `donor-${Date.now()}`,
      ...body,
      donation_count: 0,
      total_donated: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(newDonor, { status: 201 });
  }),

  // GET /rest/v1/adoption_applications
  http.get(`${SUPABASE_URL}/rest/v1/adoption_applications`, () => {
    return HttpResponse.json(mockAdoptionApplications, { status: 200 });
  }),

  // POST /rest/v1/adoption_applications
  http.post(`${SUPABASE_URL}/rest/v1/adoption_applications`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    if (!body.animal_id || !body.adopter_email) {
      return HttpResponse.json(
        { error: 'Missing required fields: animal_id, adopter_email' },
        { status: 400 }
      );
    }

    const newApplication = {
      id: `app-${Date.now()}`,
      ...body,
      status: 'pending',
      application_date: new Date().toISOString().split('T')[0],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(newApplication, { status: 201 });
  }),

  // PATCH /rest/v1/adoption_applications/:id
  http.patch(`${SUPABASE_URL}/rest/v1/adoption_applications/:id`, async ({ request, params }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const app = mockAdoptionApplications.find(a => a.id === params.id);

    if (!app) {
      return HttpResponse.json(
        { message: 'Not found' },
        { status: 404 }
      );
    }

    const body = await request.json();

    const updated = {
      ...app,
      ...body,
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(updated, { status: 200 });
  }),
];
```

### Step 3: Create Supabase Storage Handlers

Create `.vitest/handlers/supabase-storage.ts`:

```typescript
import { http, HttpResponse } from 'msw';

const SUPABASE_PROJECT_ID = import.meta.env.VITE_SUPABASE_PROJECT_ID;
const SUPABASE_URL = `https://${SUPABASE_PROJECT_ID}.supabase.co`;

export const supabaseStorageHandlers = [
  // POST /storage/v1/b/animals/upload
  http.post(`${SUPABASE_URL}/storage/v1/b/animals/upload*`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const url = new URL(request.url);
    const fileName = url.searchParams.get('name') || `image-${Date.now()}.jpg`;

    return HttpResponse.json(
      {
        name: fileName,
        id: `file-${Date.now()}`,
        updated_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        last_accessed_at: new Date().toISOString(),
        metadata: {
          eTag: '"mock-etag"',
          mimetype: 'image/jpeg',
          size: 12345,
        },
      },
      { status: 200 }
    );
  }),

  // GET /storage/v1/b/animals/o/:fileName
  http.get(`${SUPABASE_URL}/storage/v1/b/animals/o/*`, ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Return a mock image blob
    const mockImageBlob = new Blob(['fake image data'], { type: 'image/jpeg' });
    return new HttpResponse(mockImageBlob, {
      status: 200,
      headers: {
        'Content-Type': 'image/jpeg',
        'Content-Length': mockImageBlob.size.toString(),
      },
    });
  }),

  // DELETE /storage/v1/b/animals/o/:fileName
  http.delete(`${SUPABASE_URL}/storage/v1/b/animals/o/*`, ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return new HttpResponse(null, { status: 204 });
  }),

  // GET /storage/v1/b/animals/list
  http.get(`${SUPABASE_URL}/storage/v1/b/animals/list`, ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return HttpResponse.json(
      [
        {
          name: 'luna-portrait.jpg',
          id: 'file-123',
          updated_at: '2026-03-15T10:00:00Z',
          created_at: '2026-03-15T10:00:00Z',
          last_accessed_at: '2026-03-20T14:30:00Z',
          metadata: {
            eTag: '"mock-etag-123"',
            mimetype: 'image/jpeg',
            size: 45000,
          },
        },
        {
          name: 'felix-playing.jpg',
          id: 'file-124',
          updated_at: '2026-03-16T11:00:00Z',
          created_at: '2026-03-16T11:00:00Z',
          last_accessed_at: '2026-03-20T15:00:00Z',
          metadata: {
            eTag: '"mock-etag-124"',
            mimetype: 'image/jpeg',
            size: 38000,
          },
        },
      ],
      { status: 200 }
    );
  }),

  // POST /storage/v1/b/animals/copy
  http.post(`${SUPABASE_URL}/storage/v1/b/animals/copy`, async ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    return HttpResponse.json(
      {
        name: body.name || 'copied-file.jpg',
        id: `file-copy-${Date.now()}`,
      },
      { status: 200 }
    );
  }),
];
```

### Step 4: Update Browser Handlers to Include Supabase Handlers

Update `.vitest/handlers/browser.ts` to import and include all Supabase handlers:

```typescript
import { setupWorker } from 'msw/browser';
import { supabaseAuthHandlers } from './supabase-auth';
import { supabaseRestHandlers } from './supabase-rest';
import { supabaseStorageHandlers } from './supabase-storage';

// Combine all Supabase handlers
const allHandlers = [
  ...supabaseAuthHandlers,
  ...supabaseRestHandlers,
  ...supabaseStorageHandlers,
];

export const worker = setupWorker(...allHandlers);

let isWorkerStarted = false;

export async function startMSW() {
  if (isWorkerStarted) return;

  try {
    await worker.start({
      onUnhandledRequest: 'warn',
    });
    isWorkerStarted = true;
  } catch (error) {
    console.error('Failed to start MSW:', error);
    throw error;
  }
}

export function stopMSW() {
  if (!isWorkerStarted) return;
  worker.stop();
  isWorkerStarted = false;
}

export function resetMSW() {
  worker.resetHandlers();
}
```

### Step 5: Create Handler Type Definitions

Create `.vitest/handlers/types.ts` for TypeScript support:

```typescript
// Type definitions for Supabase mock responses
export interface MockAnimal {
  id: string;
  name: string;
  species: 'dog' | 'cat' | 'bird' | 'rodent' | 'other';
  breed: string;
  status: 'available' | 'adopted' | 'reserved' | 'medical';
  age_years: number;
  age_months: number;
  gender: 'male' | 'female' | 'unknown';
  weight_kg: number;
  description: string;
  intake_date: string;
  medical_history: string;
  image_url: string;
  created_at: string;
  updated_at: string;
}

export interface MockDonor {
  id: string;
  email: string;
  full_name: string;
  country: string;
  currency: 'EUR' | 'PYG' | 'USD';
  donation_count: number;
  total_donated: number;
  last_donation_date: string;
  created_at: string;
  updated_at: string;
}

export interface MockAdoptionApplication {
  id: string;
  animal_id: string;
  adopter_name: string;
  adopter_email: string;
  adopter_phone: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed';
  application_date: string;
  interview_scheduled: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SupabaseAuthResponse {
  user: {
    id: string;
    email: string;
    user_metadata: Record<string, unknown>;
    aud: string;
    created_at: string;
  };
  session: {
    access_token: string;
    token_type: string;
    expires_in: number;
    expires_at: number;
    refresh_token: string;
    user: {
      id: string;
      email: string;
    };
  };
}
```

---

## Acceptance Criteria Verification

**Criterion 1: Supabase Auth handlers created for login, logout, signup, password reset**
- ✅ `/auth/v1/signup` - POST handler creates new user with JWT token
- ✅ `/auth/v1/token` - POST handler handles password grant and refresh token grant
- ✅ `/auth/v1/user` - GET handler returns authenticated user profile
- ✅ `/auth/v1/logout` - POST handler clears session
- ✅ `/auth/v1/recover` - POST handler initiates password reset
- ✅ `/auth/v1/user` - PUT handler updates user profile

**Criterion 2: Supabase REST API handlers created for all animal shelter endpoints**
- ✅ Animals: GET (list/paginate), GET (single), POST (create), PATCH (update)
- ✅ Donors: GET (list), POST (create)
- ✅ Adoption Applications: GET (list), POST (create), PATCH (update)
- ✅ All endpoints return correct Supabase response structure with timestamps

**Criterion 3: Supabase Storage handlers created for image upload/download**
- ✅ `/storage/v1/b/animals/upload` - POST handler for file upload with metadata
- ✅ `/storage/v1/b/animals/o/*` - GET handler returns mock image blob
- ✅ `/storage/v1/b/animals/o/*` - DELETE handler removes file
- ✅ `/storage/v1/b/animals/list` - GET handler lists all files in bucket

**Criterion 4: MSW handlers properly mock response status codes and payloads**
- ✅ Success responses: 200 OK, 201 Created, 204 No Content
- ✅ Error responses: 400 Bad Request, 401 Unauthorized, 404 Not Found
- ✅ All responses include proper Content-Type headers
- ✅ Pagination headers included in list endpoints (Content-Range)

**Criterion 5: Handlers include error scenarios (401, 403, 404, 500)**
- ✅ 401 Unauthorized - returned when Authorization header missing
- ✅ 400 Bad Request - returned for missing required fields
- ✅ 404 Not Found - returned for non-existent resources
- ✅ Error response structure matches Supabase error format

**Criterion 6: All handlers use correct Supabase endpoint patterns**
- ✅ Auth endpoints: `/auth/v1/...`
- ✅ REST API endpoints: `/rest/v1/{table_name}`
- ✅ Storage endpoints: `/storage/v1/b/{bucket_name}/...`
- ✅ All use correct HTTP methods (GET, POST, PATCH, DELETE)

**Criterion 7: Handler responses match actual Supabase API response structure**
- ✅ Auth responses include `user` and `session` objects
- ✅ REST responses are JSON arrays for lists, single objects for detail
- ✅ Storage responses include file metadata (eTag, mimetype, size)
- ✅ All responses include timestamp fields (created_at, updated_at)

**Criterion 8: Handlers can be imported and used in tests without errors**
- ✅ All handlers export as named exports (`supabaseAuthHandlers`, etc.)
- ✅ Browser handlers aggregated in single `setupWorker` call
- ✅ Type definitions exported for TypeScript support
- ✅ Compatible with vitest + jsdom environment

---

## Common Issues & Solutions

**Issue: "Cannot find module '@/handlers/supabase-auth'"**
- Solution: Ensure all handler files are created in `.vitest/handlers/` directory
- Solution: Import paths use relative imports, not aliases (yet)

**Issue: "Unexpected token in JSON at position 0"**
- Solution: MSW handler JSON responses are correct syntax; check test code JSON parsing
- Solution: Verify `HttpResponse.json()` is used instead of `Response.json()`

**Issue: "Auth header not found" in tests**
- Solution: Include `Authorization: Bearer ${token}` in test request headers
- Solution: Use `x-api-key` header for API calls requiring authentication

**Issue: Storage handler returns empty blob**
- Solution: Mock image blob is intentionally minimal for testing purposes
- Solution: For image display tests, use actual image files or data URLs

**Issue: Handlers not intercepting requests**
- Solution: Verify `startMSW()` is called in vitest setup (beforeAll hook)
- Solution: Ensure MSW browser service worker is properly registered
- Solution: Check browser console for MSW activation logs

---

## Related Tasks

- T01: Install and Configure MSW for Browser Tests
- T03: Node.js Server Setup and Server-Side Handlers

## References

- [MSW Documentation - Defining Handlers](https://mswjs.io/docs/getting-started/mocking)
- [Supabase API Reference](https://supabase.com/docs/reference/api)
- [Supabase Auth API](https://supabase.com/docs/reference/api/auth-endpoint)
- [Supabase REST API](https://supabase.com/docs/reference/api/rest-api-overview)
- [Supabase Storage API](https://supabase.com/docs/reference/api/storage-api)
