---
task: T02
story: S05
epic: EPIC-1
title: Implement filter logic
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.727146
---

# T02: Implement filter logic

## Description

Wire the filter URL params from `FilterPanel` (T01) into the Supabase query inside `AnimalGrid`. The catalog page reads `especie`, `sexo`, and `edad` from the URL search params and passes them to the server-side data fetching function, which translates age group labels into `age_years` ranges and adds `.eq()` / `.lte()` / `.gte()` clauses to the Supabase query.

## Context

- Server-side filtering — happens in the Supabase query, not after data fetch
- Age groups map to `age_years` numeric ranges in the `animals` table
- `AnimalFilters` type already defined in `src/types/filters.ts` (S02/T03)
- Catalog page reads `searchParams` from Next.js page props (App Router)
- CSS: Tailwind CSS 3.4.19 PINNED — no new UI in this task

## Age Group → age_years Mapping

| Group | Label | age_years range |
|---|---|---|
| `cachorro` | Cachorro (< 1 año) | `age_years = 0` |
| `joven` | Joven (1–3 años) | `age_years >= 1 AND age_years <= 3` |
| `adulto` | Adulto (3–8 años) | `age_years >= 3 AND age_years <= 8` |
| `senior` | Senior (> 8 años) | `age_years > 8` |

## Files to modify

### `src/lib/animals/catalog.ts` (new file — server-side data fetching)

```typescript
import { createServerClient } from '@/lib/supabase/server'
import type { AnimalFilters } from '@/types/filters'

const PAGE_SIZE = 12

export interface CatalogResult {
  animals: CatalogAnimal[]
  count: number
  totalPages: number
}

export interface CatalogAnimal {
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

export async function fetchCatalogAnimals(filters: AnimalFilters): Promise<CatalogResult> {
  const supabase = createServerClient()

  let query = supabase
    .from('animals')
    .select('id, name, species, breed, age_years, age_months, sex, status, photo_primary_url, is_featured', { count: 'exact' })
    .eq('status', 'available')
    .order('is_featured', { ascending: false })
    .order('created_at', { ascending: false })

  // Species filter
  if (filters.species) {
    query = query.eq('species', filters.species)
  }

  // Sex filter
  if (filters.sex) {
    query = query.eq('sex', filters.sex)
  }

  // Age group filter
  if (filters.ageGroup) {
    query = applyAgeGroupFilter(query, filters.ageGroup)
  }

  // Pagination
  const offset = (filters.page - 1) * PAGE_SIZE
  query = query.range(offset, offset + PAGE_SIZE - 1)

  const { data, count, error } = await query

  if (error) throw new Error(`Error fetching catalog: ${error.message}`)

  const total = count ?? 0

  return {
    animals: data ?? [],
    count: total,
    totalPages: Math.ceil(total / PAGE_SIZE),
  }
}

type SupabaseQuery = ReturnType<typeof buildBaseQuery>

function buildBaseQuery() {
  const supabase = createServerClient()
  return supabase.from('animals').select('*')
}

function applyAgeGroupFilter(query: any, ageGroup: string): any {
  switch (ageGroup) {
    case 'cachorro':
      return query.eq('age_years', 0)
    case 'joven':
      return query.gte('age_years', 1).lte('age_years', 3)
    case 'adulto':
      return query.gte('age_years', 3).lte('age_years', 8)
    case 'senior':
      return query.gt('age_years', 8)
    default:
      return query
  }
}
```

### `app/(public)/animales/page.tsx` (update — add filter parsing)

Update the catalog page to parse filters from URL search params and pass to `fetchCatalogAnimals`:

```typescript
import { Suspense } from 'react'
import type { AnimalFilters } from '@/types/filters'
import { fetchCatalogAnimals } from '@/lib/animals/catalog'
import { AnimalGrid } from '@/components/catalog/AnimalGrid'
import { FilterPanel } from '@/components/catalog/FilterPanel'
import { Pagination } from '@/components/catalog/Pagination'

interface CatalogPageProps {
  searchParams: {
    especie?: string
    sexo?: string
    edad?: string
    pagina?: string
  }
}

export default async function AnimalesCatalogPage({ searchParams }: CatalogPageProps) {
  const filters: AnimalFilters = {
    species: searchParams.especie ?? '',
    sex: searchParams.sexo ?? '',
    ageGroup: searchParams.edad ?? '',
    page: Number(searchParams.pagina ?? '1'),
  }

  const { animals, totalPages } = await fetchCatalogAnimals(filters)

  return (
    <main className="min-h-screen bg-[var(--bg-base)]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-8">
          Animales en adopción
        </h1>

        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar filters */}
          <div className="w-full md:w-56 shrink-0">
            <Suspense>
              <FilterPanel />
            </Suspense>
          </div>

          {/* Main content */}
          <div className="flex-1 space-y-6">
            <AnimalGrid animals={animals} />

            {totalPages > 1 && (
              <Suspense>
                <Pagination
                  currentPage={filters.page}
                  totalPages={totalPages}
                />
              </Suspense>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
```

## Acceptance Criteria

- [ ] `fetchCatalogAnimals(filters)` applies `.eq('species', ...)` when `filters.species` is non-empty
- [ ] `fetchCatalogAnimals(filters)` applies `.eq('sex', ...)` when `filters.sex` is non-empty
- [ ] Age group `cachorro` → `.eq('age_years', 0)`
- [ ] Age group `joven` → `.gte('age_years', 1).lte('age_years', 3)`
- [ ] Age group `adulto` → `.gte('age_years', 3).lte('age_years', 8)`
- [ ] Age group `senior` → `.gt('age_years', 8)`
- [ ] No filter applied when the corresponding URL param is absent
- [ ] Catalog page parses `searchParams.especie`, `searchParams.sexo`, `searchParams.edad`, `searchParams.pagina` from URL
- [ ] `page` param defaults to `1` when absent
- [ ] `FilterPanel` and `Pagination` are each wrapped in `<Suspense>` (required for `useSearchParams`)
- [ ] Only animals with `status = 'available'` are returned
- [ ] Featured animals (`is_featured = true`) appear first
- [ ] TypeScript: no type errors

## Implementation Notes

- `applyAgeGroupFilter` uses `any` for the chained query type — this is acceptable because Supabase's query builder uses method chaining and the return type varies by filter combination. TypeScript can't infer it precisely without complex generics.
- The `joven` and `adulto` ranges overlap at `age_years = 3` — this is intentional: a 3-year-old animal appears in both groups. The shelter can adjust these boundaries by changing the constants.
- `{ count: 'exact' }` in the select call asks Supabase PostgREST to return the total count alongside the paginated results — avoids a second round-trip.
- `is_featured` ordering ensures manually promoted animals always appear first regardless of filters.
- The catalog page passes `totalPages` from the server to `Pagination` — the pagination component does not make its own data fetch.

## Related

- Depends on: S02/T01 (catalog page), S02/T03 (AnimalFilters type, Pagination), S05/T01 (FilterPanel)
- Part of: S05 — Advanced Search and Filters
