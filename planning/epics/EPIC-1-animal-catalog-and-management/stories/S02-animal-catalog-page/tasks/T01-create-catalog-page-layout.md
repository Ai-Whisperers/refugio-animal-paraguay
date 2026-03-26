---
task: T01
story: S02
epic: EPIC-1
title: Create catalog page layout
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.725982
---

# T01: Create catalog page layout

## Description

Create the public-facing animal catalog page at `/animales` using Next.js 14 App Router. This is the main adoption discovery page — visitors browse available animals here. The layout includes a filter sidebar, the animal grid, and pagination. Server-side rendered for SEO.

## Context

- Route: `app/(public)/animales/page.tsx`
- Architecture: Next.js 14 App Router, Server Components by default
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS variables (`bg-[var(--bg-card)]`), NOT `bg-white` or `bg-gray-100`
- No authentication required — public page
- Filter state is in URL search params (not client state) for shareability and SSR

## Page structure to implement

```
app/(public)/animales/
├── page.tsx           ← Server component (main catalog page)
├── loading.tsx        ← Streaming skeleton
└── error.tsx          ← Error boundary
```

Create `app/(public)/animales/page.tsx`:

```typescript
import { Suspense } from 'react'
import { AnimalGrid } from '@/components/catalog/AnimalGrid'
import { FilterPanel } from '@/components/catalog/FilterPanel'
import { AnimalGridSkeleton } from '@/components/catalog/AnimalGridSkeleton'
import type { AnimalFilters } from '@/types/filters'

interface CatalogPageProps {
  searchParams: {
    especie?: string
    sexo?: string
    edad?: string
    pagina?: string
  }
}

export const metadata = {
  title: 'Animales en Adopción | Refugio Animal Paraguay',
  description: 'Conocé a los animales que buscan un hogar. Adoptá y cambiá una vida.',
}

export default function CatalogPage({ searchParams }: CatalogPageProps) {
  const filters: AnimalFilters = {
    species: searchParams.especie,
    sex: searchParams.sexo,
    ageGroup: searchParams.edad,
    page: Number(searchParams.pagina) || 1,
  }

  return (
    <main className="min-h-screen bg-[var(--bg-base)]">
      {/* Hero header */}
      <section className="bg-[var(--bg-card)] border-b border-[var(--border-subtle)] py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
            Animales en Adopción
          </h1>
          <p className="text-[var(--text-secondary)]">
            Cada animal merece un hogar lleno de amor. Encontrá tu compañero perfecto.
          </p>
        </div>
      </section>

      {/* Content: filters + grid */}
      <div className="max-w-6xl mx-auto px-4 py-8 flex gap-8">
        {/* Filter sidebar */}
        <aside className="w-64 flex-shrink-0 hidden md:block">
          <FilterPanel currentFilters={filters} />
        </aside>

        {/* Animal grid with streaming */}
        <div className="flex-1 min-w-0">
          <Suspense fallback={<AnimalGridSkeleton />}>
            <AnimalGrid filters={filters} />
          </Suspense>
        </div>
      </div>
    </main>
  )
}
```

Create `app/(public)/animales/loading.tsx`:

```typescript
import { AnimalGridSkeleton } from '@/components/catalog/AnimalGridSkeleton'

export default function Loading() {
  return (
    <main className="min-h-screen bg-[var(--bg-base)]">
      <section className="bg-[var(--bg-card)] border-b border-[var(--border-subtle)] py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="h-8 w-64 bg-[var(--bg-skeleton)] rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-[var(--bg-skeleton)] rounded animate-pulse" />
        </div>
      </section>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <AnimalGridSkeleton />
      </div>
    </main>
  )
}
```

Create `app/(public)/animales/error.tsx`:

```typescript
'use client'

interface ErrorProps {
  error: Error
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <main className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
      <div className="text-center px-4">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
          No pudimos cargar los animales
        </h2>
        <p className="text-[var(--text-secondary)] mb-6">{error.message}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          Intentar de nuevo
        </button>
      </div>
    </main>
  )
}
```

## Acceptance Criteria

- [ ] `app/(public)/animales/page.tsx` created as a Server Component (no `'use client'`)
- [ ] Page reads filter state from `searchParams` (URL params), not React state
- [ ] `metadata` export sets Spanish title and description for SEO
- [ ] Layout uses CSS variable classes (`bg-[var(--bg-base)]`, `text-[var(--text-primary)]`), NOT hardcoded Tailwind colors
- [ ] `AnimalGrid` wrapped in `<Suspense>` with `AnimalGridSkeleton` fallback (enables streaming)
- [ ] Filter sidebar hidden on mobile (`hidden md:block`)
- [ ] `loading.tsx` exports a skeleton that matches page shape
- [ ] `error.tsx` is a `'use client'` component with reset button
- [ ] TypeScript: no type errors (`npm run type-check` passes)

## Implementation Notes

- Do NOT use `bg-white`, `bg-gray-100`, `text-gray-900` etc. — Tailwind v4 breaks these in the build. Always use `bg-[var(--bg-card)]` style.
- `AnimalGrid` and `FilterPanel` components are created in T02 and S05/T01 — create stubs for them if building T01 in isolation
- `(public)` route group: no authentication middleware applied to this group
- `searchParams` filter keys use Spanish names (`especie`, `sexo`, `edad`, `pagina`) for SEO-friendly URLs

## Related

- Depends on: S01/T01 (animals table), S01/T02 (TypeScript types)
- Blocks: T02 (AnimalGrid component), T03 (pagination)
- Part of: S02 — Animal Catalog Page
