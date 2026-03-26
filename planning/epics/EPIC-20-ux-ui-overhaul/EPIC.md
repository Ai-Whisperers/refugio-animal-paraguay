# [EPIC-20] UX/UI Overhaul — Align Frontend with UX Principles

## Overview

**Goal:** Transform the current English-language boilerplate frontend into a warm, Spanish-language, mobile-first experience that faithfully implements the project's `docs/UX-PRINCIPLES.md`.

**Why it matters:** The site is live at `https://sunstein.cloud/petShelter` but in its current state it:
- Speaks English to a Paraguayan audience
- Uses inverted brand colors (green primary instead of orange)
- Has 4 dead navigation links (404s on /about, /donate, /volunteer, /foster)
- Has zero WhatsApp integration (the primary communication channel)
- Has no trust signals (no photos, no team, no address)
- Has no form persistence (data lost on 3G drops)

EU donors arriving at this site will see a generic, incomplete application. Local Paraguayan adopters will see an English-only interface with no way to contact the shelter via WhatsApp.

**Target users:** Adopters, donors (EU + local), volunteers, general visitors.

**Audit reference:** `planning/epics/EPIC-20-ux-ui-overhaul/UX-AUDIT.md`

## Scope

### In Scope
- Tailwind color system alignment with UX principles
- Complete Spanish translation of all user-facing strings
- Missing pages (/about, /donate, /volunteer, /foster)
- WhatsApp floating button (global)
- Homepage redesign with trust signals
- Animal catalog polish (filters, skeleton loaders, card redesign)
- Animal detail page sticky CTA + photo gallery
- Form localStorage persistence
- Adoption form multi-step conversion
- Accessibility fixes (aria-describedby, inputMode, lang="es-PY")
- Image optimization (remove `unoptimized`, add responsive sizes)
- Custom 404 page
- Shared utility extraction (DRY cleanup)

### Out of Scope
- i18n framework (next-intl) — deferred to a future epic; this epic hardcodes Spanish
- PWA / Service Worker / offline catalog — separate epic
- Tigo Money integration — V3
- Admin panel redesign — EPIC-7
- Backend API changes (frontend-only epic)
- SEO optimization beyond basic meta tags

## Features

- [ ] [FEAT-1] Design System Foundation — Color palette, typography, shared components
- [ ] [FEAT-2] Spanish Localization — All 100+ strings translated, warm tone
- [ ] [FEAT-3] Navigation & Missing Pages — /about, /donate, /volunteer, /foster
- [ ] [FEAT-4] Homepage Redesign — Trust signals, real content structure, warm CTA
- [ ] [FEAT-5] Animal Catalog Polish — Filters, skeleton loaders, card redesign
- [ ] [FEAT-6] Animal Detail & Adoption Flow — Sticky CTA, gallery, multi-step form
- [ ] [FEAT-7] WhatsApp Integration — Global floating button, contact page integration
- [ ] [FEAT-8] Accessibility & Performance — WCAG AA fixes, image optimization

## User Stories

- [ ] [S01] Design System Realignment (RAP-171) — 5 pts
- [ ] [S02] Spanish Translation & Warm Tone (RAP-172) — 5 pts
- [ ] [S03] Missing Pages: About & Donate (RAP-173) — 5 pts
- [ ] [S04] Missing Pages: Volunteer & Foster (RAP-174) — 3 pts
- [ ] [S05] Homepage Redesign with Trust Signals (RAP-175) — 5 pts
- [ ] [S06] Animal Catalog UX Improvements (RAP-176) — 5 pts
- [ ] [S07] Animal Detail & Adoption Flow Overhaul (RAP-177) — 5 pts
- [ ] [S08] WhatsApp Integration & Accessibility Fixes (RAP-178) — 5 pts

**Total:** 38 story points across 8 stories (2 sprints)

## Sprint Plan

### Sprint UX-1 (Foundation + Critical Fixes) — 23 points
| # | Story | Points | Priority | Rationale |
|---|-------|--------|----------|-----------|
| 1 | S01: Design System Realignment | 5 | P0 | Everything else builds on correct colors/typography |
| 2 | S02: Spanish Translation | 5 | P0 | Users can't read English; blocks all UX testing |
| 3 | S03: About & Donate Pages | 5 | P0 | Dead links kill trust; donate page blocks revenue |
| 4 | S05: Homepage Redesign | 5 | P0 | First impression; trust before conversion |
| 5 | S08: WhatsApp + Accessibility | 3 | P1 | Primary contact channel for target users |

### Sprint UX-2 (Polish + Flow Optimization) — 15 points
| # | Story | Points | Priority | Rationale |
|---|-------|--------|----------|-----------|
| 1 | S04: Volunteer & Foster Pages | 3 | P1 | Dead footer links, lower traffic than about/donate |
| 2 | S06: Animal Catalog UX | 5 | P1 | Catalog is the discovery funnel |
| 3 | S07: Detail & Adoption Flow | 5 | P1 | Conversion optimization |
| 4 | S08: Accessibility (remainder) | 2 | P2 | Image optimization, WCAG cleanup |

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Dead navigation links | 4 | 0 |
| English strings on site | 100+ | 0 |
| Color alignment with UX spec | 0% | 100% |
| WhatsApp integration | absent | global floating button |
| Form data survival on page refresh | 0% | 100% (localStorage) |
| Lighthouse Accessibility score | ~70 | 90+ |

## Dependencies

- **Depends on:** EPIC-11 (Public Portal API endpoints — already complete)
- **Depends on:** Animal photo upload functionality (for real photos on homepage/catalog)
- **Blocks:** Nothing critical, but improves conversion for all downstream features

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No real animal photos yet | Homepage/catalog look empty | Use branded SVG placeholders + structure ready for real photos |
| Spanish copy quality | Awkward phrasing loses trust | Follow UX-PRINCIPLES.md tone examples; review by native speaker |
| WhatsApp number not configured | Button goes nowhere | Use configurable number via env var; placeholder until number decided |
| basePath `/petShelter` breaks new pages | 404s on production | Test all new pages with basePath before deploying |

---

*Created: 2026-03-26*
*Ticket range: RAP-171 through RAP-178*
