---
story: RAP-424
epic: EPIC-75
title: "Add centralized API error handling in frontend"
status: ready
priority: 2
points: 2
created: 2026-03-27
---

# RAP-424: Add Centralized API Error Handling in Frontend

## Story

As a **frontend developer**, I want **centralized error handling for all API calls** so that **errors are displayed consistently and users know how to recover**.

## Description

API errors (4xx, 5xx) are currently handled inconsistently. Each component handles errors differently. A centralized error handler will:
1. Catch all API errors
2. Show appropriate user messages
3. Implement recovery actions (redirect, retry, etc.)

## Acceptance Criteria

### Create Error Handling Utility

**Given** any API call
**When** error is returned
**Then**
- [ ] Error is caught by centralized handler
- [ ] Appropriate user message is shown
- [ ] Recovery action is suggested (retry, login, etc.)

**File: `frontend/src/lib/error-handling.ts`**:
```typescript
export type ApiError = {
  status: number;
  error_code: string;
  detail: string;
};

/**
 * Parse API error response and return user-friendly message
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Network error
    if (error.message.includes("fetch")) {
      return "Problemas de conexión. Por favor, intente de nuevo.";
    }
    return error.message;
  }

  const apiError = error as ApiError;

  // Handle specific error codes
  switch (apiError.error_code) {
    case "NOT_AUTHENTICATED":
      return "Debe iniciar sesión para continuar.";
    case "INSUFFICIENT_PERMISSIONS":
      return "No tiene permiso para realizar esta acción.";
    case "ANIMAL_NOT_FOUND":
      return "El animal no fue encontrado.";
    case "DUPLICATE_ADOPTION_REQUEST":
      return "Ya tiene una solicitud de adopción pendiente para este animal.";
    case "INVALID_EMAIL":
      return "El correo electrónico no es válido.";
    case "VALIDATION_ERROR":
      return "Por favor, revise los datos ingresados.";
    case "CARD_DECLINED":
      return "Tu tarjeta fue rechazada. Intenta con otra tarjeta.";
    case "PAYMENT_SERVICE_UNAVAILABLE":
      return "El servicio de pagos no está disponible. Intenta más tarde.";
    default:
      return apiError.detail || "Ocurrió un error. Por favor, intente de nuevo.";
  }
}

/**
 * Handle API error and determine recovery action
 */
export type RecoveryAction = "retry" | "reload" | "login" | "none";

export function getRecoveryAction(error: ApiError): RecoveryAction {
  switch (error.status) {
    case 401:
      return "login";  // Redirect to login
    case 403:
      return "none";   // No recovery possible
    case 404:
      return "reload"; // Page not found, reload
    case 409:
      return "reload"; // Conflict, reload to get fresh data
    case 422:
      return "none";   // Validation error, user must fix
    case 503:
      return "retry";  // Service unavailable, retry
    default:
      return "retry";
  }
}

/**
 * Handle API error with toast message and recovery
 */
export async function handleApiError(
  error: unknown,
  options: {
    showToast?: boolean;
    onError?: (action: RecoveryAction) => void;
  } = {}
): Promise<void> {
  const message = getErrorMessage(error);

  if (options.showToast) {
    // Show toast message (implement with your toast library)
    console.log("Error:", message);  // TODO: Replace with toast
  }

  const action = getRecoveryAction(error as ApiError);
  options.onError?.(action);

  // Implement recovery actions
  switch (action) {
    case "login":
      // Redirect to login
      window.location.href = "/login";
      break;
    case "reload":
      // Reload page
      window.location.reload();
      break;
    case "retry":
      // Return so caller can retry
      break;
    case "none":
      // No automatic recovery
      break;
  }
}
```

### API Fetcher with Error Handling

**Given** all API calls use centralized fetcher
**When** request is made
**Then**
- [ ] Error response is parsed and validated
- [ ] Error code is used for handling
- [ ] User-friendly message is returned

**File: `frontend/src/lib/public-api.ts`**:
```typescript
import { getErrorMessage, RecoveryAction } from "./error-handling";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public error_code: string,
    public detail: string
  ) {
    super(detail);
  }
}

/**
 * Centralized fetch with error handling
 */
async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const url = `${API_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      // API returned error
      throw new ApiError(
        response.status,
        data.error_code || "UNKNOWN_ERROR",
        data.detail || "Unknown error"
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network error
    throw new Error("Network error. Please check your connection.");
  }
}

export async function getAnimals() {
  return apiFetch("/api/animals");
}

export async function getAnimal(id: string) {
  return apiFetch(`/api/animals/${id}`);
}

export async function createDonation(data: any) {
  return apiFetch("/api/donations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitContactForm(data: any) {
  return apiFetch("/api/contact", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
```

### Use in Components

**Given** component uses API
**When** API call is made
**Then**
- [ ] Error is caught and handled
- [ ] User message is shown
- [ ] Recovery action is executed

**Example component**:
```typescript
"use client";

import { useState } from "react";
import { createDonation, ApiError } from "@/lib/public-api";
import { getErrorMessage, getRecoveryAction } from "@/lib/error-handling";

export default function DonationForm() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await createDonation({ amount_cents: 10000 });
      // Success
    } catch (err) {
      if (err instanceof ApiError) {
        const message = getErrorMessage(err);
        setError(message);

        // Handle recovery action
        const action = getRecoveryAction(err);
        if (action === "login") {
          // Redirect happens in handleApiError
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div className="bg-red-50 p-4 text-red-800 rounded">
          {error}
        </div>
      )}
      {/* Form fields... */}
    </form>
  );
}
```

### Toast Notifications (Optional)

Add toast library for better UX:

**Install**:
```bash
npm install react-hot-toast
```

**Wrap app with provider**:
```typescript
// frontend/src/app/layout.tsx
import { Toaster } from "react-hot-toast";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

**Update error handler**:
```typescript
import toast from "react-hot-toast";

export async function handleApiError(error: unknown) {
  const message = getErrorMessage(error);
  toast.error(message);
  // ... recovery actions ...
}
```

### Use Centralized Fetcher in SWR

If using SWR, use centralized fetcher:

```typescript
// frontend/src/lib/swr.ts
import { apiFetch } from "./public-api";

export const fetcher = async (url: string) => {
  try {
    return await apiFetch(url);
  } catch (error) {
    throw error;  // SWR will handle and pass to error state
  }
};

// In component
const { data, error } = useSWR("/api/animals", fetcher);

if (error) {
  const message = getErrorMessage(error);
  return <div>{message}</div>;
}
```

### Error Logging

All errors should be logged (for debugging and Sentry):

```typescript
export async function handleApiError(error: unknown) {
  console.error("API Error:", error);

  // Log to Sentry (if integrated)
  if (window.Sentry) {
    window.Sentry.captureException(error);
  }

  // Show user message
  const message = getErrorMessage(error);
  toast.error(message);
}
```

## Definition of Done

- [ ] Error handling utility created (`frontend/src/lib/error-handling.ts`)
- [ ] Centralized fetcher created (`frontend/src/lib/public-api.ts`)
- [ ] ApiError class with status, error_code, detail
- [ ] getErrorMessage() returns Spanish user-friendly messages
- [ ] getRecoveryAction() suggests retry/reload/login/none
- [ ] All components use centralized fetcher
- [ ] Error messages are shown in UI (toast or inline)
- [ ] Recovery actions are implemented (redirect, reload, etc.)
- [ ] Errors are logged to console and Sentry
- [ ] Component tests pass (RAP-409)
- [ ] Code review approved

## Technical Notes

### Files to Create
- `frontend/src/lib/error-handling.ts`
- `frontend/src/lib/public-api.ts` (enhance existing if present)

### Error Code Mapping

Keep in sync with backend error codes (EPIC-73):
- `NOT_AUTHENTICATED` (401)
- `INSUFFICIENT_PERMISSIONS` (403)
- `ANIMAL_NOT_FOUND` (404)
- `VALIDATION_ERROR` (422)
- `CARD_DECLINED` (402)
- `PAYMENT_SERVICE_UNAVAILABLE` (503)

### Internationalization (Optional)

For multi-language support:
```typescript
type ErrorMessages = Record<string, Record<string, string>>;

const errorMessages: ErrorMessages = {
  es: {
    NOT_AUTHENTICATED: "Debe iniciar sesión...",
    CARD_DECLINED: "Tu tarjeta fue rechazada...",
  },
  en: {
    NOT_AUTHENTICATED: "You must log in...",
    CARD_DECLINED: "Your card was declined...",
  },
};
```

---

*Last updated: 2026-03-27*
