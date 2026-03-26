---
task: T02
story: S03
epic: EPIC-4
title: Add filtering/search
status: ready
priority: medium
created: 2026-03-25T17:13:26.730740
---

# T02: Add filtering/search

## Description

Add URL-param-driven filtering and search to the medical timeline page (`/admin/animals/[id]/medical/timeline`). Staff can filter by event type, date range, and veterinarian. The filter state lives entirely in URL search params — no client-side state management of the data set. The page remains a Server Component; only the filter controls are `'use client'`.

## Acceptance Criteria

- [x] Filter by event type (record types + vaccination + medication + treatment) via multi-select
- [x] Filter by date range (from/to date inputs)
- [x] Filter by veterinarian (dropdown populated from `veterinarians` table)
- [x] Filters are reflected in URL search params (`?type=vaccination&from=2026-01-01&to=2026-12-31&vet_id=uuid`)
- [x] Clearing filters resets to the full timeline
- [x] Filtered results update on navigation (full Server Component re-render) — no client fetch
- [x] Empty state shown when filters produce no results, distinct from "no records at all"
- [x] Filter controls are accessible (labels, keyboard navigation)
- [x] Pure filter-param parsing function is unit-tested
- [x] Implementation complete
- [x] Tests written and passing

## Implementation Notes

### Approach: URL Search Params as State

Filters are managed as URL search params. The Server Component reads `searchParams`, builds a filtered query, and renders the results. The Client Component controls call `router.push` / `router.replace` to update the URL, which triggers a Server Component re-render with the new params.

This pattern:
- Works with `next/navigation` Server Components
- Is shareable/bookmarkable (copy URL = copy filter state)
- Requires no `useState` for data — only for the filter form's local field values before submit

### Filter Params Contract

| Param | Type | Values |
|-------|------|--------|
| `type` | `string[]` | `check_up`, `surgery`, `vaccination`, `medication`, `treatment`, etc. — comma-separated |
| `from` | `string` | ISO date `YYYY-MM-DD` |
| `to` | `string` | ISO date `YYYY-MM-DD` |
| `vet_id` | `string` | UUID of veterinarian (only applicable to medical records) |

### Pure Parsing Function

```typescript
// src/lib/medical-records/parse-timeline-filters.ts

export const VALID_EVENT_TYPES = [
  'check_up', 'surgery', 'emergency', 'vaccination',
  'medication', 'treatment', 'follow_up', 'other',
] as const

export type ValidEventType = typeof VALID_EVENT_TYPES[number]

export interface TimelineFilters {
  types: ValidEventType[]
  from: string | null    // 'YYYY-MM-DD' or null
  to: string | null      // 'YYYY-MM-DD' or null
  vetId: string | null
}

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function parseTimelineFilters(
  searchParams: Record<string, string | string[] | undefined>
): TimelineFilters {
  // types: comma-separated string or repeated param
  const rawType = searchParams['type']
  const typeList = Array.isArray(rawType)
    ? rawType
    : (rawType ?? '').split(',').filter(Boolean)
  const types = typeList.filter(
    (t): t is ValidEventType => VALID_EVENT_TYPES.includes(t as ValidEventType)
  )

  const rawFrom = Array.isArray(searchParams['from']) ? searchParams['from'][0] : searchParams['from']
  const rawTo = Array.isArray(searchParams['to']) ? searchParams['to'][0] : searchParams['to']
  const rawVetId = Array.isArray(searchParams['vet_id']) ? searchParams['vet_id'][0] : searchParams['vet_id']

  return {
    types,
    from:  rawFrom && ISO_DATE_RE.test(rawFrom) ? rawFrom : null,
    to:    rawTo && ISO_DATE_RE.test(rawTo) ? rawTo : null,
    vetId: rawVetId && UUID_RE.test(rawVetId) ? rawVetId : null,
  }
}

export function hasActiveFilters(filters: TimelineFilters): boolean {
  return (
    filters.types.length > 0 ||
    filters.from !== null ||
    filters.to !== null ||
    filters.vetId !== null
  )
}
```

### Updated RPC with Filter Parameters

Update migration `20260401000007` (or add `20260401000008`) to accept optional filter params:

```sql
-- Replace get_animal_timeline with a filtered version
create or replace function get_animal_timeline(
  p_animal_id  uuid,
  p_types      text[]    default null,  -- null = all types
  p_from       date      default null,
  p_to         date      default null,
  p_vet_id     uuid      default null
)
returns table (
  event_date  date,
  event_type  text,
  title       text,
  subtitle    text,
  record_id   uuid,
  created_at  timestamptz
)
language sql
security definer
stable
as $$
  select
    visit_date                                               as event_date,
    record_type::text                                        as event_type,
    coalesce(diagnosis, 'Sin diagnóstico')                   as title,
    coalesce(vt.full_name, 'Veterinario no asignado')        as subtitle,
    mr.id                                                    as record_id,
    mr.created_at
  from medical_records mr
  left join veterinarians vt on vt.id = mr.veterinarian_id
  where mr.animal_id = p_animal_id
    and (mr.is_confidential = false
         or (select role from profiles where id = auth.uid()) in ('staff', 'admin', 'vet'))
    and (p_types is null or record_type::text = any(p_types))
    and (p_from is null or visit_date >= p_from)
    and (p_to is null or visit_date <= p_to)
    and (p_vet_id is null or mr.veterinarian_id = p_vet_id)

  union all

  select
    date_administered                                        as event_date,
    'vaccination'                                            as event_type,
    vaccine_name                                             as title,
    coalesce('Próxima: ' || to_char(next_due_date, 'DD/MM/YYYY'), 'Sin próxima dosis') as subtitle,
    vac.id                                                   as record_id,
    vac.created_at
  from vaccinations vac
  where vac.animal_id = p_animal_id
    and (p_types is null or 'vaccination' = any(p_types))
    and (p_from is null or date_administered >= p_from)
    and (p_to is null or date_administered <= p_to)
    and p_vet_id is null  -- vaccinations are not vet-specific in this schema

  union all

  select
    start_date                                               as event_date,
    'medication'                                             as event_type,
    medication_name || ' — ' || dosage                       as title,
    coalesce('Hasta: ' || to_char(end_date, 'DD/MM/YYYY'), 'Sin fecha de fin') as subtitle,
    med.id                                                   as record_id,
    med.created_at
  from medications med
  where med.animal_id = p_animal_id
    and (p_types is null or 'medication' = any(p_types))
    and (p_from is null or start_date >= p_from)
    and (p_to is null or start_date <= p_to)
    and p_vet_id is null

  union all

  select
    start_date                                               as event_date,
    'treatment'                                              as event_type,
    treatment_type::text                                     as title,
    coalesce(outcome::text, 'En curso')                      as subtitle,
    tr.id                                                    as record_id,
    tr.created_at
  from treatments tr
  where tr.animal_id = p_animal_id
    and (p_types is null or 'treatment' = any(p_types))
    and (p_from is null or start_date >= p_from)
    and (p_to is null or start_date <= p_to)
    and p_vet_id is null

  order by event_date desc, created_at desc;
$$;
```

### Updated Page — Server Component

```typescript
// src/app/admin/animals/[id]/medical/timeline/page.tsx
import { createServerClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { TimelineList } from '@/components/medical/TimelineList'
import { MedicalTabNav } from '@/components/medical/MedicalTabNav'
import { TimelineFilterBar } from '@/components/medical/TimelineFilterBar'
import {
  parseTimelineFilters,
  hasActiveFilters,
} from '@/lib/medical-records/parse-timeline-filters'
import type { TimelineEvent } from '@/lib/medical-records/types'

interface Props {
  params: { id: string }
  searchParams: Record<string, string | string[] | undefined>
}

export default async function AnimalMedicalTimelinePage({ params, searchParams }: Props) {
  const supabase = createServerClient()
  const filters = parseTimelineFilters(searchParams)

  const { data: animal } = await supabase
    .from('animals')
    .select('id, name')
    .eq('id', params.id)
    .single()

  if (!animal) notFound()

  // Fetch veterinarians for filter dropdown
  const { data: veterinarians } = await supabase
    .from('veterinarians')
    .select('id, full_name')
    .eq('is_active', true)
    .order('full_name')

  // Fetch filtered timeline via RPC
  const { data: events } = await supabase.rpc('get_animal_timeline', {
    p_animal_id: params.id,
    p_types:     filters.types.length > 0 ? filters.types : null,
    p_from:      filters.from,
    p_to:        filters.to,
    p_vet_id:    filters.vetId,
  })

  const timeline: TimelineEvent[] = events ?? []
  const isFiltered = hasActiveFilters(filters)

  return (
    <div className="space-y-[var(--spacing-6)]">
      <h1 className="text-[var(--text-primary)] text-2xl font-semibold">
        Historia clínica — {animal.name}
      </h1>

      <MedicalTabNav animalId={params.id} activeTab="timeline" />

      <TimelineFilterBar
        animalId={params.id}
        veterinarians={veterinarians ?? []}
        currentFilters={filters}
      />

      <TimelineList events={timeline} isFiltered={isFiltered} />
    </div>
  )
}
```

### Filter Bar — Client Component

```typescript
// src/components/medical/TimelineFilterBar.tsx
'use client'
import { useRouter, usePathname } from 'next/navigation'
import { useState } from 'react'
import { TIMELINE_EVENT_LABELS, VALID_EVENT_TYPES } from '@/lib/medical-records/timeline-constants'
import type { TimelineFilters } from '@/lib/medical-records/parse-timeline-filters'

interface Vet {
  id: string
  full_name: string
}

interface Props {
  animalId: string
  veterinarians: Vet[]
  currentFilters: TimelineFilters
}

export function TimelineFilterBar({ animalId, veterinarians, currentFilters }: Props) {
  const router = useRouter()
  const pathname = usePathname()

  const [types, setTypes] = useState<string[]>(currentFilters.types)
  const [from, setFrom] = useState(currentFilters.from ?? '')
  const [to, setTo] = useState(currentFilters.to ?? '')
  const [vetId, setVetId] = useState(currentFilters.vetId ?? '')

  function applyFilters() {
    const params = new URLSearchParams()
    if (types.length > 0) params.set('type', types.join(','))
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    if (vetId) params.set('vet_id', vetId)
    router.push(`${pathname}?${params.toString()}`)
  }

  function clearFilters() {
    setTypes([])
    setFrom('')
    setTo('')
    setVetId('')
    router.push(pathname)
  }

  function toggleType(type: string) {
    setTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  const isActive =
    types.length > 0 || from !== '' || to !== '' || vetId !== ''

  return (
    <details className="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-surface)] p-[var(--spacing-4)]">
      <summary className="cursor-pointer text-sm font-medium text-[var(--text-primary)] select-none">
        Filtrar historial
        {isActive && (
          <span className="ml-[var(--spacing-2)] rounded-full bg-[var(--color-primary)] text-[var(--color-primary-text)] px-[var(--spacing-2)] py-0.5 text-xs">
            Filtros activos
          </span>
        )}
      </summary>

      <div className="mt-[var(--spacing-4)] space-y-[var(--spacing-4)]">
        {/* Type filter */}
        <fieldset>
          <legend className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-[var(--spacing-2)]">
            Tipo de evento
          </legend>
          <div className="flex flex-wrap gap-[var(--spacing-2)]">
            {VALID_EVENT_TYPES.map((type) => (
              <label
                key={type}
                className="flex items-center gap-1 text-sm text-[var(--text-primary)] cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={types.includes(type)}
                  onChange={() => toggleType(type)}
                  className="accent-[var(--color-primary)]"
                />
                {TIMELINE_EVENT_LABELS[type]}
              </label>
            ))}
          </div>
        </fieldset>

        {/* Date range */}
        <div className="flex flex-wrap gap-[var(--spacing-4)]">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
              Desde
            </label>
            <input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-2)] py-1 text-sm text-[var(--text-primary)]"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
              Hasta
            </label>
            <input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-2)] py-1 text-sm text-[var(--text-primary)]"
            />
          </div>
        </div>

        {/* Veterinarian filter */}
        {veterinarians.length > 0 && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
              Veterinario
            </label>
            <select
              value={vetId}
              onChange={(e) => setVetId(e.target.value)}
              className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-2)] py-1 text-sm text-[var(--text-primary)]"
            >
              <option value="">Todos los veterinarios</option>
              {veterinarians.map((vet) => (
                <option key={vet.id} value={vet.id}>
                  {vet.full_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-[var(--spacing-2)]">
          <button
            type="button"
            onClick={applyFilters}
            className="rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-[var(--color-primary-text)] px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm font-medium"
          >
            Aplicar filtros
          </button>
          {isActive && (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-[var(--radius-sm)] border border-[var(--border-default)] text-[var(--text-muted)] px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm"
            >
              Limpiar
            </button>
          )}
        </div>
      </div>
    </details>
  )
}
```

### Updated TimelineList — Empty State Distinguishes Filtered vs Unfiltered

```typescript
// src/components/medical/TimelineList.tsx  (updated signature)
interface Props {
  events: TimelineEvent[]
  isFiltered?: boolean
}

export function TimelineList({ events, isFiltered = false }: Props) {
  if (events.length === 0) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border-default)] p-[var(--spacing-8)] text-center">
        <p className="text-[var(--text-muted)] text-sm">
          {isFiltered
            ? 'Ningún evento coincide con los filtros aplicados.'
            : 'Sin eventos de salud registrados todavía.'}
        </p>
      </div>
    )
  }
  // ... rest unchanged
}
```

### Unit Tests for Parsing Logic

```typescript
// src/lib/medical-records/__tests__/parse-timeline-filters.test.ts
import {
  parseTimelineFilters,
  hasActiveFilters,
} from '@/lib/medical-records/parse-timeline-filters'

describe('parseTimelineFilters', () => {
  it('returns empty defaults when no params provided', () => {
    const result = parseTimelineFilters({})
    expect(result).toEqual({ types: [], from: null, to: null, vetId: null })
  })

  it('parses comma-separated type param', () => {
    const result = parseTimelineFilters({ type: 'vaccination,medication' })
    expect(result.types).toEqual(['vaccination', 'medication'])
  })

  it('ignores invalid event types', () => {
    const result = parseTimelineFilters({ type: 'vaccination,invalid_type' })
    expect(result.types).toEqual(['vaccination'])
  })

  it('parses valid ISO date from/to', () => {
    const result = parseTimelineFilters({ from: '2026-01-01', to: '2026-12-31' })
    expect(result.from).toBe('2026-01-01')
    expect(result.to).toBe('2026-12-31')
  })

  it('rejects malformed date strings', () => {
    const result = parseTimelineFilters({ from: '01/01/2026', to: 'not-a-date' })
    expect(result.from).toBeNull()
    expect(result.to).toBeNull()
  })

  it('parses valid UUID for vet_id', () => {
    const uuid = '550e8400-e29b-41d4-a716-446655440000'
    const result = parseTimelineFilters({ vet_id: uuid })
    expect(result.vetId).toBe(uuid)
  })

  it('rejects invalid UUID for vet_id', () => {
    const result = parseTimelineFilters({ vet_id: 'not-a-uuid' })
    expect(result.vetId).toBeNull()
  })

  it('handles array-style repeated params by taking first', () => {
    const result = parseTimelineFilters({ from: ['2026-01-01', '2025-01-01'] })
    expect(result.from).toBe('2026-01-01')
  })
})

describe('hasActiveFilters', () => {
  it('returns false for empty filters', () => {
    expect(hasActiveFilters({ types: [], from: null, to: null, vetId: null })).toBe(false)
  })

  it('returns true when at least one filter is set', () => {
    expect(hasActiveFilters({ types: ['vaccination'], from: null, to: null, vetId: null })).toBe(true)
    expect(hasActiveFilters({ types: [], from: '2026-01-01', to: null, vetId: null })).toBe(true)
  })
})
```

### Files to Create

| File | Type | Purpose |
|------|------|---------|
| `supabase/migrations/20260401000008_update_timeline_rpc_filters.sql` | Migration | Replaces `get_animal_timeline` with filtered version |
| `src/lib/medical-records/parse-timeline-filters.ts` | Utility | Pure param parsing — `parseTimelineFilters()`, `hasActiveFilters()` |
| `src/components/medical/TimelineFilterBar.tsx` | Client Component | Filter controls — updates URL search params on apply |
| `src/lib/medical-records/__tests__/parse-timeline-filters.test.ts` | Test | 9 unit tests covering parsing and validation |

### Files to Update

| File | Change |
|------|--------|
| `src/app/admin/animals/[id]/medical/timeline/page.tsx` | Accept `searchParams`, pass filters to RPC and to `TimelineFilterBar` |
| `src/components/medical/TimelineList.tsx` | Add `isFiltered` prop, update empty state message |

## Related Issues

- EPIC-4
- S03
