---
story: RAP-423
epic: EPIC-75
title: "Add loading and error states to all client pages"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-423: Add Loading and Error States to All Client Pages

## Story

As a **user**, I want **to see loading spinners and error messages** so that **I know the page is working and what to do if something fails**.

## Description

All pages that fetch data (animals, campaigns, donations, contact submissions) need loading and error states. Currently, pages show nothing while loading and may show unexpected errors.

## Acceptance Criteria

### Loading States

**Given** page is fetching data
**When** data fetch is in progress
**Then**
- [ ] Loading spinner or skeleton is displayed
- [ ] Page layout remains stable (no layout shift)
- [ ] User knows to wait (visual feedback)

**For each data-fetching page, create `loading.tsx`**:
- `frontend/src/app/animals/loading.tsx`
- `frontend/src/app/donate/campaigns/[id]/loading.tsx`
- `frontend/src/app/animals/[id]/loading.tsx`
- `frontend/src/app/contact/loading.tsx`

**Example: `frontend/src/app/animals/loading.tsx`**:
```typescript
export default function Loading() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Animales Disponibles</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="bg-gray-200 rounded-lg h-64 animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}
```

### Error States

**Given** data fetch fails
**When** API returns error
**Then**
- [ ] Error message is displayed (friendly, not technical)
- [ ] Retry button is available
- [ ] Page layout is preserved (readable)

**Example error state in component**:
```typescript
if (error) {
  return (
    <div className="bg-red-50 border border-red-200 rounded p-6">
      <h2 className="text-lg font-bold text-red-900">
        Error al cargar animales
      </h2>
      <p className="mt-2 text-red-800">{error.message}</p>
      <button
        onClick={() => refetch()}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
      >
        Intentar de nuevo
      </button>
    </div>
  );
}
```

### /animals/[id] Page

**Given** user views single animal details
**When** page loads
**Then**
- [ ] Loading skeleton is shown while fetching
- [ ] Animal image, name, description, adoption button displayed
- [ ] Error state with retry if fetch fails

**File: `frontend/src/app/animals/[id]/page.tsx`**:
```typescript
"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

export default function AnimalDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [animal, setAnimal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnimal = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/animals/${params.id}`
        );
        if (!response.ok) throw new Error("Animal not found");
        setAnimal(await response.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading animal");
      } finally {
        setLoading(false);
      }
    };

    fetchAnimal();
  }, [params.id]);

  if (loading) {
    return (
      <div className="bg-gray-200 rounded-lg h-96 animate-pulse" />
    );
  }

  if (error || !animal) {
    return (
      <div className="bg-red-50 p-6 rounded text-red-900">
        {error || "Animal not found"}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Image
          src={animal.image_url}
          alt={animal.name}
          width={400}
          height={400}
          className="rounded-lg"
        />
      </div>
      <h1 className="text-3xl font-bold">{animal.name}</h1>
      <p className="text-gray-600 mt-2">{animal.description}</p>
      <button className="mt-6 px-6 py-2 bg-blue-600 text-white rounded">
        Solicitar Adopción
      </button>
    </div>
  );
}
```

### /donate/campaigns/[id] Page

**Given** user views campaign details
**When** page loads
**Then**
- [ ] Loading state shows while fetching campaign
- [ ] Campaign title, image, progress bar, donate button displayed
- [ ] Error state with retry if fetch fails

### /contact Page

**Given** user submits contact form
**When** form is submitted
**Then**
- [ ] Submit button shows loading spinner: "Enviando..."
- [ ] Disabled while submitting (prevent double-submit)
- [ ] Success message shown: "¡Gracias! Hemos recibido tu mensaje"
- [ ] Error message shown if submission fails
- [ ] Form is reset after successful submission

**File: `frontend/src/app/contact/page.tsx`**:
```typescript
"use client";

import { useState } from "react";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, message }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      setSuccess(true);
      setName("");
      setEmail("");
      setMessage("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error sending message"
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="bg-green-50 p-6 rounded text-green-900">
        ¡Gracias! Hemos recibido tu mensaje y te contactaremos pronto.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Tu nombre"
        required
      />
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Tu email"
        required
      />
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Tu mensaje"
        required
      />

      {error && (
        <div className="bg-red-50 p-4 text-red-800 rounded">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
      >
        {loading ? "Enviando..." : "Enviar"}
      </button>
    </form>
  );
}
```

### Reusable Loading Skeleton Components

Create skeleton components to avoid repeating loading UI:

**File: `frontend/src/components/AnimalCardSkeleton.tsx`**:
```typescript
export default function AnimalCardSkeleton() {
  return (
    <div className="bg-gray-200 rounded-lg h-64 animate-pulse" />
  );
}
```

**File: `frontend/src/components/LoadingSpinner.tsx`**:
```typescript
export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>
  );
}
```

### SWR Hook for Data Fetching

Use SWR for automatic loading/error states:

```typescript
import useSWR from "swr";

export default function AnimalsPage() {
  const { data, error, isLoading } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/api/animals`,
    fetcher
  );

  if (isLoading) return <AnimalCardSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <div>No animals</div>;

  return (
    <div className="grid">
      {data.map((animal) => <AnimalCard key={animal.id} animal={animal} />)}
    </div>
  );
}
```

## Definition of Done

- [ ] All data-fetching pages have loading.tsx
- [ ] All pages handle API errors with message + retry
- [ ] Submit buttons show "Submitting..." while loading
- [ ] Success messages shown after form submission
- [ ] Forms are reset after successful submission
- [ ] No layout shift during loading (skeleton same size)
- [ ] Error messages are user-friendly (no API errors)
- [ ] Retry buttons work and refetch data
- [ ] Component tests pass (RAP-409)
- [ ] Code review approved

## Technical Notes

### Pages to Update
- `/animals` — List view
- `/animals/[id]` — Detail view
- `/donate/campaigns/[id]` — Campaign detail
- `/contact` — Contact form

### Loading UI Options
1. Skeleton screens (same layout, gray placeholders)
2. Spinners (rotating loader)
3. Pulse animation (alternating opacity)

### SWR Configuration
```typescript
// frontend/src/lib/swr.ts
import useSWR, { SWRConfig } from "swr";

export const fetcher = (url: string) =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error("API error");
    return r.json();
  });

export const swrConfig: SWRConfig = {
  revalidateOnFocus: false,
  dedupingInterval: 60000,
};
```

---

*Last updated: 2026-03-27*
