---
task: T02
story: S02
epic: EPIC-1
title: Implement animal list component
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726066
---

# T02: Implement animal list component

## Description

Build the `AnimalGrid` Server Component that fetches animals from Supabase and renders them as adoption cards. Also build the `AnimalCard` sub-component and `AnimalGridSkeleton` for loading states. This is the core visual component of the adoption catalog.

## Context

- Server Component: fetches data directly using Supabase server client
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- Photos served from Supabase Storage public bucket `animals-photos`
- Responsive grid: 1 col mobile, 2 col tablet, 3 col desktop
- Uses TanStack Query on client only if interactive refetch is needed — default to Server Component fetch

## Files to create

### `src/components/catalog/AnimalGrid.tsx`

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { AnimalCard } from './AnimalCard'
import { Pagination } from './Pagination'
import type { AnimalFilters } from '@/types/filters'

const PAGE_SIZE = 12

interface AnimalGridProps {
  filters: AnimalFilters
}

export async function AnimalGrid({ filters }: AnimalGridProps) {
  const supabase = createServerClient()

  let query = supabase
    .from('animals')
    .select('id, name, species, breed, age_years, age_months, sex, status, photo_primary_url, is_featured', {
      count: 'exact',
    })
    .eq('status', 'available')
    .order('is_featured', { ascending: false })
    .order('created_at', { ascending: false })

  if (filters.species) query = query.eq('species', filters.species)
  if (filters.sex) query = query.eq('sex', filters.sex)
  if (filters.ageGroup === 'cachorro') query = query.lt('age_years', 1)
  if (filters.ageGroup === 'joven') query = query.gte('age_years', 1).lt('age_years', 3)
  if (filters.ageGroup === 'adulto') query = query.gte('age_years', 3).lt('age_years', 8)
  if (filters.ageGroup === 'senior') query = query.gte('age_years', 8)

  const offset = (filters.page - 1) * PAGE_SIZE
  query = query.range(offset, offset + PAGE_SIZE - 1)

  const { data: animals, count, error } = await query

  if (error) throw new Error(`Error cargando animales: ${error.message}`)

  if (!animals || animals.length === 0) {
    return (
      <div className="text-center py-16 text-[var(--text-secondary)]">
        <p className="text-lg">No hay animales disponibles con esos filtros.</p>
        <p className="text-sm mt-2">Intentá cambiar los filtros o volvé pronto.</p>
      </div>
    )
  }

  const totalPages = Math.ceil((count ?? 0) / PAGE_SIZE)

  return (
    <div>
      <p className="text-sm text-[var(--text-secondary)] mb-4">
        {count} animales disponibles
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {animals.map((animal) => (
          <AnimalCard key={animal.id} animal={animal} />
        ))}
      </div>
      {totalPages > 1 && (
        <div className="mt-8">
          <Pagination currentPage={filters.page} totalPages={totalPages} />
        </div>
      )}
    </div>
  )
}
```

### `src/components/catalog/AnimalCard.tsx`

```typescript
import Image from 'next/image'
import Link from 'next/link'

interface AnimalCardProps {
  animal: {
    id: string
    name: string
    species: string
    breed: string | null
    age_years: number
    age_months: number
    sex: string
    status: string
    photo_primary_url: string | null
    is_featured: boolean
  }
}

function formatAge(years: number, months: number): string {
  if (years === 0) return months <= 1 ? '1 mes' : `${months} meses`
  if (years === 1) return '1 año'
  return `${years} años`
}

const SEX_LABELS: Record<string, string> = { male: 'Macho', female: 'Hembra' }
const SPECIES_LABELS: Record<string, string> = { dog: 'Perro', cat: 'Gato' }
const PLACEHOLDER_IMAGE = '/images/animal-placeholder.webp'

export function AnimalCard({ animal }: AnimalCardProps) {
  return (
    <Link
      href={`/animales/${animal.id}`}
      className="group block rounded-xl overflow-hidden bg-[var(--bg-card)] border border-[var(--border-subtle)] hover:border-[var(--color-primary)] hover:shadow-lg transition-all duration-200"
    >
      {/* Photo */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <Image
          src={animal.photo_primary_url ?? PLACEHOLDER_IMAGE}
          alt={`Foto de ${animal.name}`}
          fill
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          className="object-cover group-hover:scale-105 transition-transform duration-300"
        />
        {animal.is_featured && (
          <span className="absolute top-2 left-2 bg-[var(--color-primary)] text-white text-xs font-medium px-2 py-1 rounded-full">
            Destacado
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="font-semibold text-lg text-[var(--text-primary)] group-hover:text-[var(--color-primary)] transition-colors">
          {animal.name}
        </h3>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          {SPECIES_LABELS[animal.species] ?? animal.species}
          {animal.breed ? ` · ${animal.breed}` : ''}
        </p>
        <div className="flex gap-3 mt-3 text-xs text-[var(--text-tertiary)]">
          <span>{SEX_LABELS[animal.sex] ?? animal.sex}</span>
          <span>·</span>
          <span>{formatAge(animal.age_years, animal.age_months)}</span>
        </div>
      </div>
    </Link>
  )
}
```

### `src/components/catalog/AnimalGridSkeleton.tsx`

```typescript
export function AnimalGridSkeleton() {
  return (
    <div>
      <div className="h-4 w-40 bg-[var(--bg-skeleton)] rounded animate-pulse mb-4" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-xl overflow-hidden bg-[var(--bg-card)] border border-[var(--border-subtle)]">
            <div className="aspect-[4/3] bg-[var(--bg-skeleton)] animate-pulse" />
            <div className="p-4 space-y-2">
              <div className="h-5 w-24 bg-[var(--bg-skeleton)] rounded animate-pulse" />
              <div className="h-4 w-32 bg-[var(--bg-skeleton)] rounded animate-pulse" />
              <div className="h-3 w-20 bg-[var(--bg-skeleton)] rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `AnimalGrid` is a Server Component (no `'use client'`) that fetches from Supabase directly
- [ ] Query filters by `status = 'available'` — never shows reserved/adopted animals in catalog
- [ ] Featured animals (`is_featured = true`) appear first in the grid
- [ ] Age display: "2 meses", "1 año", "3 años" — correct singular/plural in Spanish
- [ ] Empty state shown when no animals match filters
- [ ] `AnimalCard` uses `next/image` with `fill` and proper `sizes` attribute for responsive loading
- [ ] `AnimalCard` links to `/animales/[id]` for the detail page
- [ ] `AnimalGridSkeleton` exported for use in `loading.tsx` and Suspense fallback
- [ ] All CSS uses CSS variable classes — no hardcoded Tailwind color utilities
- [ ] TypeScript: no type errors

## Implementation Notes

- Use CSS vars throughout: `bg-[var(--bg-card)]`, `text-[var(--text-primary)]`, `border-[var(--border-subtle)]`
- `photo_primary_url` can be `null` — always have a placeholder image at `public/images/animal-placeholder.webp`
- The `Pagination` component referenced is created in T03
- `PAGE_SIZE = 12` gives a good grid (3×4 on desktop)
- Do NOT add `'use client'` — keep this as a Server Component for SSR/SEO

## Related

- Depends on: T01 (catalog page layout)
- Blocks: T03 (pagination uses count from this component)
- Blocks: S03/T01 (detail page — needs animal IDs from this list)
- Part of: S02 — Animal Catalog Page
