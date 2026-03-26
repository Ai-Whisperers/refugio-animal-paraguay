---
task: T01
story: S05
epic: EPIC-1
title: Build filter UI
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.727067
---

# T01: Build filter UI

## Description

Build the `FilterPanel` Client Component that renders species, sex, and age group filter controls for the animal catalog. Filters update the URL search params — no local state management needed beyond rendering selected state from URL. This component works alongside the `Pagination` component (S02/T03) which uses the same URL param pattern.

## Context

- Client Component (`'use client'`) — uses `useRouter`, `usePathname`, `useSearchParams`
- Filters are URL-based: `?especie=dog&sexo=male&edad=cachorro` — browser back/forward works
- Active filter state read from URL — no controlled component state
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- `AnimalFilters` type defined in `src/types/filters.ts` (created in S02/T03)

## Files to create

### `src/components/catalog/FilterPanel.tsx`

```typescript
'use client'

import { useRouter, usePathname, useSearchParams } from 'next/navigation'

interface FilterOption {
  value: string
  label: string
}

const SPECIES_OPTIONS: FilterOption[] = [
  { value: 'dog', label: 'Perros' },
  { value: 'cat', label: 'Gatos' },
]

const SEX_OPTIONS: FilterOption[] = [
  { value: 'male', label: 'Macho' },
  { value: 'female', label: 'Hembra' },
]

const AGE_OPTIONS: FilterOption[] = [
  { value: 'cachorro', label: 'Cachorro (< 1 año)' },
  { value: 'joven', label: 'Joven (1–3 años)' },
  { value: 'adulto', label: 'Adulto (3–8 años)' },
  { value: 'senior', label: 'Senior (> 8 años)' },
]

const FILTER_PARAMS: Record<string, string> = {
  species: 'especie',
  sex: 'sexo',
  ageGroup: 'edad',
}

export function FilterPanel() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const currentSpecies = searchParams.get('especie') ?? ''
  const currentSex = searchParams.get('sexo') ?? ''
  const currentAge = searchParams.get('edad') ?? ''

  function setFilter(param: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    // Reset to page 1 whenever a filter changes
    params.delete('pagina')
    if (value) {
      params.set(param, value)
    } else {
      params.delete(param)
    }
    const query = params.toString()
    router.push(query ? `${pathname}?${query}` : pathname)
  }

  function clearFilters() {
    router.push(pathname)
  }

  const hasActiveFilters = !!(currentSpecies || currentSex || currentAge)

  return (
    <aside className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide">
          Filtros
        </h2>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-[var(--color-primary)] hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Species */}
      <FilterGroup
        label="Especie"
        options={SPECIES_OPTIONS}
        selected={currentSpecies}
        onSelect={(v) => setFilter('especie', v)}
      />

      {/* Sex */}
      <FilterGroup
        label="Sexo"
        options={SEX_OPTIONS}
        selected={currentSex}
        onSelect={(v) => setFilter('sexo', v)}
      />

      {/* Age group */}
      <FilterGroup
        label="Edad"
        options={AGE_OPTIONS}
        selected={currentAge}
        onSelect={(v) => setFilter('edad', v)}
      />
    </aside>
  )
}

interface FilterGroupProps {
  label: string
  options: FilterOption[]
  selected: string
  onSelect: (value: string) => void
}

function FilterGroup({ label, options, selected, onSelect }: FilterGroupProps) {
  return (
    <div>
      <p className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide mb-2">
        {label}
      </p>
      <div className="space-y-1">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onSelect(selected === opt.value ? '' : opt.value)}
            aria-pressed={selected === opt.value}
            className={`
              w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
              ${selected === opt.value
                ? 'bg-[var(--color-primary)] text-white font-medium'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
              }
            `}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `FilterPanel` is a `'use client'` component using `useRouter`, `usePathname`, `useSearchParams`
- [ ] Species filter sets/clears `?especie` param; clicking active filter again clears it
- [ ] Sex filter sets/clears `?sexo` param
- [ ] Age group filter sets/clears `?edad` param with values: `cachorro`, `joven`, `adulto`, `senior`
- [ ] Selecting any filter resets `?pagina` to avoid stale page numbers
- [ ] "Limpiar filtros" button visible only when at least one filter is active — clears all filters
- [ ] Active filter button has `aria-pressed={true}` for accessibility
- [ ] Active filter style uses `bg-[var(--color-primary)]` — not hardcoded colors
- [ ] All CSS uses CSS variable classes — no hardcoded Tailwind color utilities
- [ ] TypeScript: no type errors

## Implementation Notes

- Filter state lives in the URL — no `useState` for filter values needed
- `useSearchParams()` requires a `<Suspense>` wrapper in parent Server Component (catalog page wraps the sidebar area in Suspense)
- Clicking the currently active option (e.g., "Perros" when `especie=dog`) deselects it by passing `''` to `setFilter` — this calls `params.delete(param)`
- `router.push()` (not `router.replace()`) — keeps navigation history so browser back works
- The URL params use Spanish names (`especie`, `sexo`, `edad`) for public URL friendliness; the `FILTER_PARAMS` map is available if param names need to be referenced programmatically

## Related

- Depends on: S02/T03 (AnimalFilters type, Pagination — same URL param pattern)
- Used by: S02/T01 (catalog page layout slots FilterPanel in the sidebar)
- Filter logic applied server-side in: S05/T02 (Supabase query filters)
- Part of: S05 — Advanced Search and Filters
