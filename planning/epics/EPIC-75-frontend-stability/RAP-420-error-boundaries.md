---
story: RAP-420
epic: EPIC-75
title: "Add error.tsx and not-found.tsx boundaries"
status: ready
priority: 0
points: 3
created: 2026-03-27
---

# RAP-420: Add Error Boundaries and Not-Found Pages

## Story

As a **frontend developer**, I want **error boundaries on all route segments** so that **a single component error doesn't crash the entire page**.

## Description

Next.js App Router provides error.tsx and not-found.tsx files for error boundaries. These must be added to handle errors gracefully instead of showing white screens.

## Acceptance Criteria

### Root Error Boundary

**Given** unhandled error anywhere in app
**When** error occurs
**Then**
- [ ] Global error.tsx catches error (in `frontend/src/app/`)
- [ ] User sees friendly message: "Algo salió mal" or "Something went wrong"
- [ ] Retry button is available to reload page
- [ ] Error details are logged (console or Sentry)
- [ ] Support link is provided (WhatsApp/email)

**File: `frontend/src/app/error.tsx`**:
```typescript
"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Algo salió mal</h1>
        <p className="mt-2 text-gray-600">
          Hubo un problema. Por favor, intente de nuevo.
        </p>
        <div className="mt-6 space-x-4">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded"
          >
            Intentar de nuevo
          </button>
          <Link href="/" className="px-4 py-2 bg-gray-600 text-white rounded">
            Inicio
          </Link>
        </div>
        <p className="mt-6 text-sm text-gray-500">
          ¿Necesita ayuda? <a href="https://wa.me/..." className="text-blue-600">Contáctenos</a>
        </p>
      </div>
    </div>
  );
}
```

### Route-Level Error Boundaries

**Given** error in a specific section (animals, donate, contact)
**When** error occurs in that section
**Then**
- [ ] Section-level error.tsx catches error (not global boundary)
- [ ] Rest of page continues to work
- [ ] Error message is section-specific

**Create error boundaries for major sections**:
- `frontend/src/app/animals/error.tsx`
- `frontend/src/app/donate/error.tsx`
- `frontend/src/app/contact/error.tsx`
- `frontend/src/app/campaigns/error.tsx`

**File: `frontend/src/app/animals/error.tsx`**:
```typescript
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="bg-red-50 border border-red-200 rounded p-6">
      <h2 className="text-xl font-bold text-red-900">
        Error cargando animales
      </h2>
      <p className="mt-2 text-red-800">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
      >
        Intentar de nuevo
      </button>
    </div>
  );
}
```

### Not-Found Pages

**Given** user navigates to nonexistent route
**When** route does not exist
**Then**
- [ ] Global not-found.tsx shows 404 page
- [ ] Message: "Página no encontrada"
- [ ] Navigation links back to home

**File: `frontend/src/app/not-found.tsx`**:
```typescript
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-900">404</h1>
      <p className="mt-4 text-lg text-gray-600">Página no encontrada</p>
      <Link href="/" className="mt-6 px-4 py-2 bg-blue-600 text-white rounded">
        Volver al inicio
      </Link>
    </div>
  );
}
```

### Dynamic Route Not-Found

**Given** user navigates to animal that doesn't exist
**When** route `/animals/[id]` with invalid ID
**Then**
- [ ] Route-specific not-found.tsx is triggered
- [ ] User sees: "Animal no encontrado"
- [ ] Link back to animals list is provided

**File: `frontend/src/app/animals/[id]/not-found.tsx`**:
```typescript
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="text-center py-12">
      <h1 className="text-2xl font-bold text-gray-900">Animal no encontrado</h1>
      <p className="mt-2 text-gray-600">El animal que buscas no existe.</p>
      <Link href="/animals" className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded">
        Ver todos los animales
      </Link>
    </div>
  );
}
```

### Loading States (Suspense Boundaries)

**Given** page is loading data
**When** data is being fetched
**Then**
- [ ] Loading skeleton or spinner is shown
- [ ] Layout remains stable (no layout shift)

**File: `frontend/src/app/animals/loading.tsx`**:
```typescript
export default function Loading() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="bg-gray-200 rounded h-64 animate-pulse" />
      ))}
    </div>
  );
}
```

### Logging Error Details

**Given** error is caught by boundary
**When** error occurs
**Then**
- [ ] Error is logged to console (development)
- [ ] Error is logged to Sentry (production)
- [ ] Error details include: error message, stack trace, route

**Code in error.tsx**:
```typescript
"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  useEffect(() => {
    // Log to Sentry
    Sentry.captureException(error);
    // Log to console (development)
    console.error("Page error:", error);
  }, [error]);

  return (
    // ... error UI ...
  );
}
```

### Styling Consistency

**Given** error messages shown on any page
**When** error boundary is rendered
**Then**
- [ ] Error messages use consistent styling
- [ ] Red/warning colors for errors
- [ ] Clear button labels (Spanish)
- [ ] Accessible colors and text size

### Testing Error Boundaries

**Given** developer is testing error handling
**When** testing error page
**Then**
- [ ] Errors can be triggered intentionally (throw Error)
- [ ] Error page is rendered correctly
- [ ] Retry button resets error state

**Testing button (development only)**:
```typescript
{process.env.NODE_ENV === "development" && (
  <button
    onClick={() => {
      throw new Error("Test error");
    }}
    className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded"
  >
    Trigger Test Error
  </button>
)}
```

## Definition of Done

- [ ] Root error.tsx created and catches global errors
- [ ] Route-level error.tsx created for major sections
- [ ] Global not-found.tsx created
- [ ] Route-specific not-found.tsx created for dynamic routes
- [ ] Loading.tsx files created for data-loading routes
- [ ] Error details logged to console and Sentry
- [ ] All error pages styled consistently
- [ ] Retry buttons work correctly (reset error state)
- [ ] All pages tested (manually navigate and check errors)
- [ ] Component tests pass (RAP-409)
- [ ] Code review approved

## Technical Notes

### Files to Create
- `frontend/src/app/error.tsx` — Global error boundary
- `frontend/src/app/not-found.tsx` — Global 404 page
- `frontend/src/app/animals/error.tsx`
- `frontend/src/app/animals/[id]/not-found.tsx`
- `frontend/src/app/donate/error.tsx`
- `frontend/src/app/contact/error.tsx`
- `frontend/src/app/animals/loading.tsx`
- `frontend/src/app/donate/campaigns/[id]/loading.tsx`

### Next.js Special Files

| File | Purpose |
|------|---------|
| `error.tsx` | Error boundary for route segment |
| `not-found.tsx` | 404 page for route |
| `loading.tsx` | Suspense fallback while loading |
| `layout.tsx` | Shared layout for route segment |

### Sentry Integration

Ensure Sentry is initialized (from RAP-416):
```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

---

*Last updated: 2026-03-27*
