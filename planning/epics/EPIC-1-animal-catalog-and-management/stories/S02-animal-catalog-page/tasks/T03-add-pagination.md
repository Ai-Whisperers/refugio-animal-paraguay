---
task: T03
story: S02
epic: EPIC-1
title: Add pagination
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726152
---

# T03: Add pagination

## Description

Build the `Pagination` Client Component that allows users to navigate between pages of the animal catalog. The component reads the current page from the URL and generates page links that preserve existing filter params. Also defines the `AnimalFilters` TypeScript type used across the catalog.

## Context

- URL-based pagination: `?pagina=2` — filter params preserved across page changes
- Client Component (`'use client'`) because it uses `usePathname` + `useSearchParams`
- `AnimalGrid` (T02) passes `count` and `PAGE_SIZE`; `Pagination` receives `currentPage` and `totalPages`
- Accessible: `aria-label`, `aria-current="page"` on active page button
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors

## Files to create

### `src/types/filters.ts`

```typescript
export interface AnimalFilters {
  species?: string
  sex?: string
  ageGroup?: string
  page: number
}
```

### `src/components/catalog/Pagination.tsx`

```typescript
'use client'

import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'

interface PaginationProps {
  currentPage: number
  totalPages: number
}

function buildPageRange(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages: (number | '...')[] = [1]

  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('...')

  pages.push(total)

  return pages
}

export function Pagination({ currentPage, totalPages }: PaginationProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  function getPageUrl(page: number): string {
    const params = new URLSearchParams(searchParams.toString())
    if (page === 1) {
      params.delete('pagina')
    } else {
      params.set('pagina', String(page))
    }
    const query = params.toString()
    return query ? `${pathname}?${query}` : pathname
  }

  const pages = buildPageRange(currentPage, totalPages)

  return (
    <nav aria-label="Paginación de animales" className="flex justify-center items-center gap-1">
      {/* Previous */}
      {currentPage > 1 ? (
        <Link
          href={getPageUrl(currentPage - 1)}
          className="px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
          aria-label="Página anterior"
        >
          ←
        </Link>
      ) : (
        <span className="px-3 py-2 rounded-lg text-sm text-[var(--text-disabled)] cursor-not-allowed">
          ←
        </span>
      )}

      {/* Page numbers */}
      {pages.map((page, idx) =>
        page === '...' ? (
          <span
            key={`ellipsis-${idx}`}
            className="px-3 py-2 text-sm text-[var(--text-tertiary)]"
          >
            …
          </span>
        ) : (
          <Link
            key={page}
            href={getPageUrl(page)}
            aria-current={page === currentPage ? 'page' : undefined}
            className={
              page === currentPage
                ? 'px-3 py-2 rounded-lg text-sm font-medium bg-[var(--color-primary)] text-white'
                : 'px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors'
            }
          >
            {page}
          </Link>
        )
      )}

      {/* Next */}
      {currentPage < totalPages ? (
        <Link
          href={getPageUrl(currentPage + 1)}
          className="px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
          aria-label="Página siguiente"
        >
          →
        </Link>
      ) : (
        <span className="px-3 py-2 rounded-lg text-sm text-[var(--text-disabled)] cursor-not-allowed">
          →
        </span>
      )}
    </nav>
  )
}
```

## Acceptance Criteria

- [ ] `src/types/filters.ts` exports `AnimalFilters` interface with `species`, `sex`, `ageGroup`, `page` fields
- [ ] `Pagination` is a `'use client'` component (uses `usePathname` + `useSearchParams`)
- [ ] Page links preserve existing filter params (`?especie=dog&pagina=2` → next page keeps `especie=dog`)
- [ ] Page 1 omits `?pagina` param from URL (clean URL for default state)
- [ ] Ellipsis (`…`) shown when page range is truncated (>7 total pages)
- [ ] Current page has `aria-current="page"` for accessibility
- [ ] Prev/Next buttons disabled (non-clickable span) at first/last page
- [ ] All CSS uses CSS variable classes — no hardcoded Tailwind color utilities
- [ ] TypeScript: no type errors

## Implementation Notes

- `buildPageRange()` is a pure function — easy to unit test with Vitest
- `useSearchParams()` requires this component to be wrapped in `<Suspense>` if used in a Server Component context — `AnimalGrid` already wraps the grid area in Suspense (see T01)
- CSS vars used: `--color-primary`, `--text-secondary`, `--text-tertiary`, `--text-disabled`, `--bg-hover`
- The `AnimalFilters` type in `src/types/filters.ts` is imported by `AnimalGrid`, `FilterPanel`, and `CatalogPage` — create this file first
- Do NOT use `router.push()` for pagination — use `<Link>` for native browser navigation and prefetching

## Related

- Depends on: T01 (catalog page layout), T02 (AnimalGrid passes totalPages)
- Blocks: S05/T01 (FilterPanel also uses URL params — same pattern)
- Part of: S02 — Animal Catalog Page
