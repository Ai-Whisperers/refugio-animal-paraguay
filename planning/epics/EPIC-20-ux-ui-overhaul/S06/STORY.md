# [S06] Animal Catalog UX Improvements — RAP-176

## Story

As an **adopter**, I want to browse animals with rich filters, smooth loading, and attractive cards so that I can quickly find and connect with an animal I want to adopt.

## Context

The catalog works but has: emoji placeholders for missing photos, inline status badges competing with name typography, only species filters (API supports breed/size/gender/age/search), a single spinner instead of skeleton loaders, and duplicated utility code. The UX principles specify edge-to-edge card photos with overlay badges, skeleton placeholders, and granular filters.

## Acceptance Criteria

### Card Redesign
- [ ] Animal cards use edge-to-edge photos (4:3 aspect ratio, `aspect-[4/3]`)
- [ ] Status badge floats over top-right corner of photo (absolute positioned)
- [ ] Badge uses status-specific colors: green "Disponible", orange "En Tratamiento", blue "Adoptado", etc.
- [ ] When no photo: branded SVG placeholder with shelter logo outline (not emoji)
- [ ] Card CTA area: "Conocer a [name]" link at bottom of card
- [ ] Hover effect: subtle card lift (`hover:shadow-lg hover:-translate-y-1 transition-all`)
- [ ] Photo hover: subtle zoom (`group-hover:scale-105`)

### Skeleton Loaders
- [ ] While fetching: render 4-8 skeleton cards matching the real card layout
- [ ] Skeleton has: gray animated pulse for photo area, 2 text line placeholders, badge placeholder
- [ ] Replace single spinner with skeleton grid

### Enhanced Filters
- [ ] Species filter (existing): "Todos", "Perros", "Gatos", "Otros"
- [ ] Size filter (new): "Todos", "Pequeno", "Mediano", "Grande"
- [ ] Age filter (new): "Todos", "Cachorro (<1 ano)", "Joven (1-3)", "Adulto (3-8)", "Senior (8+)"
- [ ] Search bar (new): text search by name (uses existing API full-text search)
- [ ] Filter bar is sticky on scroll (or scrolls with content on mobile)
- [ ] Active filter count indicator

### Empty & Error States
- [ ] Empty state: branded illustration (not emoji), warm message, suggestion to remove filters
- [ ] Error state: warm Spanish message with retry button

### Code Cleanup
- [ ] Import shared `calculateAge`, `statusBadgeClass`, `STATUS_LABELS` from `src/lib/animal-utils.ts`
- [ ] Import `AnimalPlaceholder` from shared component
- [ ] All strings from `src/lib/strings.ts`

## Technical Notes

- The public API already supports `species`, `status`, `size`, `age_min`, `age_max`, and `search` query params. No backend changes needed.
- Skeleton component: create `src/components/AnimalCardSkeleton.tsx`
- Filter state: use URL search params (`useSearchParams`) so filters are bookmarkable/shareable

## Definition of Done

- [ ] Card redesign matches UX principles spec
- [ ] Skeleton loaders during fetch
- [ ] 3+ filter dimensions available
- [ ] No duplicated utility code
- [ ] All strings in Spanish
- [ ] Mobile responsive
- [ ] Deployed to staging

## Story Points: 5
