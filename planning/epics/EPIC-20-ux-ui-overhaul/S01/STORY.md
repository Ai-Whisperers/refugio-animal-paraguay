# [S01] Design System Realignment — RAP-171

## Story

As a **visitor**, I want the shelter's website to use warm, inviting colors that match the brand identity so that I feel the organization is professional and trustworthy.

## Context

The `tailwind.config.ts` defines `primary` as Tailwind's default green scale (`#16a34a`) when `UX-PRINCIPLES.md` mandates `#E8622A` (warm orange) as primary and `#2A7E62` (nature green) as secondary. Every component in the frontend references `primary-*` and `accent-*` classes, so fixing the config cascades the correct colors everywhere. The `themeColor` in `layout.tsx` viewport config also uses the wrong green.

## Acceptance Criteria

**Given** the `UX-PRINCIPLES.md` color palette definition
**When** I update the Tailwind config and related files
**Then:**
- [ ] `primary` color scale in `tailwind.config.ts` centers on `#E8622A` (warm orange) with proper light/dark variants
- [ ] `secondary` color scale (new) centers on `#2A7E62` (nature green)
- [ ] `accent` scale is kept or repurposed for status/utility colors
- [ ] Neutral/background colors use warm tones (`#FAFAF8` not pure white)
- [ ] `shelter` custom colors removed or aligned with the spec
- [ ] `themeColor` in `layout.tsx` updated to `#E8622A`
- [ ] `globals.css` CSS custom properties match the UX spec values
- [ ] Status colors defined: success `#2A7E62`, warning `#E8922A`, error `#D93025`, urgent `#D93025`
- [ ] All existing component references to `primary-*` render the new orange (no manual updates needed — Tailwind config change cascades)
- [ ] Font heading class uses Inter (confirm, no change needed) but at proper weights (400/500/600/700)
- [ ] Extract shared utilities: `calculateAge()`, `statusBadgeClass()`, `STATUS_LABELS` into `src/lib/animal-utils.ts`
- [ ] Extract `AnimalPlaceholder` component into `src/components/AnimalPlaceholder.tsx`
- [ ] No visual regressions — all existing pages render correctly with new colors

## Technical Notes

- The `primary` scale needs 50-950 shades generated from `#E8622A` base. Use a tool like `uicolors.app/create` or manually define the scale.
- The `secondary` scale needs 50-950 shades from `#2A7E62`.
- Components referencing `bg-primary-600` will automatically get the new orange — no per-file changes needed.
- The `accent-*` classes used on the homepage "Donate Now" button will need review — if accent stays orange, it collides with the new primary.

## Definition of Done

- [ ] Code complete, no linting errors
- [ ] Color values verified against UX-PRINCIPLES.md spec
- [ ] All pages visually checked (home, animals list, animal detail, apply, contact)
- [ ] Shared utilities extracted and imported in all consuming files
- [ ] Deployed to staging and verified

## Story Points: 5
