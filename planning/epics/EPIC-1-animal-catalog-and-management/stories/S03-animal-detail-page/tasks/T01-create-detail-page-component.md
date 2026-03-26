---
task: T01
story: S03
epic: EPIC-1
title: Create detail page component
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726373
---

# T01: Create detail page component

## Description

Create the public-facing animal detail page at `/animales/[id]` using Next.js 14 App Router. This page shows full information about a single animal and includes the primary CTA (adoption request button). Server-side rendered for SEO — each animal gets its own indexed page.

## Context

- Route: `app/(public)/animales/[id]/page.tsx`
- Dynamic segment `[id]` is the animal's UUID
- `generateMetadata` exports per-animal Open Graph metadata for social sharing
- `generateStaticParams` is NOT used — pages are server-rendered on demand (shelter adds animals frequently)
- No auth required — public page

## Files to create

### `app/(public)/animales/[id]/page.tsx`

```typescript
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { createServerClient } from '@/lib/supabase/server'
import { AnimalDetailView } from '@/components/animals/AnimalDetailView'

interface AnimalDetailPageProps {
  params: { id: string }
}

export async function generateMetadata(
  { params }: AnimalDetailPageProps
): Promise<Metadata> {
  const supabase = createServerClient()
  const { data: animal } = await supabase
    .from('animals')
    .select('name, species, description, photo_primary_url')
    .eq('id', params.id)
    .single()

  if (!animal) return { title: 'Animal no encontrado' }

  const speciesLabel = animal.species === 'dog' ? 'perro' : 'gato'

  return {
    title: `${animal.name} — ${speciesLabel} en adopción | Refugio Animal Paraguay`,
    description: animal.description?.slice(0, 155) ?? `Conocé a ${animal.name} y ayudalo a encontrar un hogar.`,
    openGraph: {
      title: `Adoptá a ${animal.name}`,
      description: animal.description?.slice(0, 155) ?? '',
      images: animal.photo_primary_url ? [animal.photo_primary_url] : [],
    },
  }
}

export default async function AnimalDetailPage({ params }: AnimalDetailPageProps) {
  const supabase = createServerClient()

  const { data: animal, error } = await supabase
    .from('animals')
    .select(`
      id, name, species, breed, age_years, age_months, sex,
      weight_kg, status, description, intake_date, intake_reason,
      location, microchip_number, is_featured,
      photo_primary_url, photo_gallery_urls
    `)
    .eq('id', params.id)
    .single()

  if (error || !animal) notFound()

  return (
    <main className="min-h-screen bg-[var(--bg-base)]">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <AnimalDetailView animal={animal} />
      </div>
    </main>
  )
}
```

### `app/(public)/animales/[id]/not-found.tsx`

```typescript
import Link from 'next/link'

export default function AnimalNotFound() {
  return (
    <main className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
      <div className="text-center px-4">
        <h2 className="text-2xl font-semibold text-[var(--text-primary)] mb-2">
          Animal no encontrado
        </h2>
        <p className="text-[var(--text-secondary)] mb-6">
          Este animal ya no está disponible o el enlace es incorrecto.
        </p>
        <Link
          href="/animales"
          className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          Ver todos los animales
        </Link>
      </div>
    </main>
  )
}
```

### `app/(public)/animales/[id]/error.tsx`

```typescript
'use client'

interface ErrorProps {
  error: Error
  reset: () => void
}

export default function AnimalDetailError({ error, reset }: ErrorProps) {
  return (
    <main className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
      <div className="text-center px-4">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
          No pudimos cargar la información del animal
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

- [ ] `app/(public)/animales/[id]/page.tsx` created as a Server Component
- [ ] `generateMetadata` fetches animal name, species, description, photo for Open Graph
- [ ] Page calls `notFound()` when animal UUID does not exist — renders `not-found.tsx`
- [ ] `not-found.tsx` includes a link back to `/animales`
- [ ] `error.tsx` is `'use client'` with a reset button
- [ ] Layout uses CSS variable classes — no hardcoded Tailwind colors
- [ ] TypeScript: no type errors

## Implementation Notes

- `notFound()` from `next/navigation` triggers the nearest `not-found.tsx` — no need to return a 404 component manually
- `generateMetadata` and the page component make separate Supabase queries — this is intentional (Next.js deduplicates fetch calls with the same URL in the same request, but Supabase client calls use connection pooling so the overhead is minimal)
- `AnimalDetailView` component is built in T02
- Photo gallery is built in T03 as a sub-component of `AnimalDetailView`

## Related

- Depends on: S01/T01 (animals table), S01/T02 (TypeScript types), S02/T02 (AnimalCard links here)
- Blocks: T02 (AnimalDetailView), T03 (photo gallery)
- Part of: S03 — Animal Detail Page
