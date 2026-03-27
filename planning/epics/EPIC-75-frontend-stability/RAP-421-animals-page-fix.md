---
story: RAP-421
epic: EPIC-75
title: "Fix /animals page 404 rendering bug"
status: ready
priority: 0
points: 5
created: 2026-03-27
---

# RAP-421: Fix /Animals Page 404 Rendering Bug

## Story

As a **user**, I want **to see all available animals** so that **I can browse animals for adoption**.

## Description

The `/animals` page returns HTTP 200 but renders "404 Not Found" content. This is a critical bug blocking the adoption feature. The page should fetch and display all available animals in a grid.

## Root Cause Analysis

Likely causes:
1. `NEXT_PUBLIC_API_URL` env var not set or wrong in production
2. API base URL has trailing slash mismatch (e.g., `localhost:8000/` vs `localhost:8000`)
3. Data fetching error is silently swallowed (no error logging)
4. API returns empty array and page shows 404 as fallback

## Acceptance Criteria

### Debug & Identify Root Cause

**Given** page is deployed
**When** user visits `/animals`
**Then**
- [ ] Page loads (HTTP 200 status)
- [ ] Browser console is checked for errors (should be none)
- [ ] Network tab shows API call to `/api/animals`
- [ ] API response status is checked (should be 200)
- [ ] API response body is examined (should be non-empty array)

**Debugging checklist**:
- [ ] Environment variables checked: `NEXT_PUBLIC_API_URL`
- [ ] API base URL is correct (matches deployed backend)
- [ ] API endpoint `/animals` exists and returns data
- [ ] CORS headers allow frontend origin
- [ ] Network request is made (not cached/skipped)

### Fix API Base URL

**Given** page fetches from wrong API endpoint
**When** API base URL is incorrect
**Then**
- [ ] `NEXT_PUBLIC_API_URL` env var is set correctly
- [ ] For production: points to actual backend (e.g., `https://api.sunstein.cloud`)
- [ ] For staging: points to staging backend
- [ ] For development: `http://localhost:8000`

**File: `frontend/.env.local` or deploy config**:
```
NEXT_PUBLIC_API_URL=https://api.sunstein.cloud
```

**Reference in code**: `frontend/src/lib/public-api.ts`
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getAnimals() {
  const response = await fetch(`${API_URL}/api/animals`);
  return response.json();
}
```

### Fix Data Fetching & Error Handling

**Given** page fetches animals
**When** data fetch completes
**Then**
- [ ] Data is properly logged (debug what's returned)
- [ ] Errors are caught and displayed (not silent)
- [ ] Empty array is handled (show "No animals available" instead of 404)

**File: `frontend/src/app/animals/page.tsx`**:
```typescript
"use client";

import { useEffect, useState } from "react";
import AnimalCard from "@/components/AnimalCard";

export default function AnimalsPage() {
  const [animals, setAnimals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnimals = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/animals`
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();
        console.log("Animals fetched:", data);  // Debug log

        setAnimals(Array.isArray(data) ? data : data.data || []);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch animals:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load animals"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAnimals();
  }, []);

  if (loading) {
    return <div>Cargando...</div>;  // Show loading state
  }

  if (error) {
    return (
      <div className="bg-red-50 p-6 rounded">
        <h1 className="text-xl font-bold text-red-900">Error</h1>
        <p className="text-red-800">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
        >
          Intentar de nuevo
        </button>
      </div>
    );
  }

  if (animals.length === 0) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">
          No hay animales disponibles
        </h1>
        <p className="mt-2 text-gray-600">
          Vuelva más tarde para ver animales disponibles para adopción.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Animales Disponibles</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {animals.map((animal) => (
          <AnimalCard key={animal.id} animal={animal} />
        ))}
      </div>
    </div>
  );
}
```

### Verify API Response Format

**Given** API returns animals data
**When** frontend receives response
**Then**
- [ ] Response format is correct (array of animal objects)
- [ ] Each animal has required fields: id, name, type, status, image_url
- [ ] Status field indicates animal is AVAILABLE

**Expected API response** (from backend):
```json
[
  {
    "id": "animal-123",
    "name": "Max",
    "type": "dog",
    "breed": "Labrador",
    "status": "AVAILABLE",
    "image_url": "https://...",
    "age_months": 36,
    "description": "Friendly dog..."
  }
]
```

### Test in All Environments

**Given** page is tested
**When** each environment is checked
**Then**
- [ ] Development (localhost) — animals list displayed
- [ ] Staging (staging backend) — animals list displayed
- [ ] Production (production backend) — animals list displayed

**Manual test steps**:
1. Open `/animals` page
2. Check browser console for errors (none should appear)
3. Check Network tab for `/api/animals` request
4. Verify response contains animal array
5. Verify animals are rendered in grid

### Add Error Boundary

**Given** page has error
**When** error occurs
**Then**
- [ ] Error boundary (from RAP-420) catches error
- [ ] User sees friendly error message
- [ ] Page doesn't show 404 by mistake

## Definition of Done

- [ ] Root cause identified and documented in progress.md
- [ ] `NEXT_PUBLIC_API_URL` env var is correct for all environments
- [ ] Data fetching includes error handling and logging
- [ ] Empty array shows "No animals available" (not 404)
- [ ] Loading state shows spinner while fetching
- [ ] Error state shows error message with retry button
- [ ] Manual testing passes (animals list displays)
- [ ] Browser console has no errors
- [ ] Network requests show correct API endpoint
- [ ] Component tests pass (RAP-409)
- [ ] Code review approved

## Technical Notes

### Files to Review/Modify
- `frontend/src/app/animals/page.tsx` — Main animals list page
- `frontend/src/lib/public-api.ts` — API utilities
- `.env.local` and deploy config — Environment variables
- `frontend/.github/workflows/deploy.yml` — Set API URL during deploy

### Environment Variable Debug

Check what value is set at runtime:
```typescript
// In component
console.log("API URL:", process.env.NEXT_PUBLIC_API_URL);
```

### CORS Issues

If API call fails with CORS error:
- [ ] Backend must have CORS middleware enabled
- [ ] CORS allows frontend origin (e.g., `https://sunstein.cloud`)
- [ ] Credentials mode is correct

### SWR Alternative

If using SWR for fetching:
```typescript
import useSWR from "swr";

export default function AnimalsPage() {
  const { data, error, isLoading } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/api/animals`,
    fetcher
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data || data.length === 0) return <div>No animals</div>;

  return (
    <div className="grid">
      {data.map((animal) => <AnimalCard key={animal.id} animal={animal} />)}
    </div>
  );
}
```

---

*Last updated: 2026-03-27*
