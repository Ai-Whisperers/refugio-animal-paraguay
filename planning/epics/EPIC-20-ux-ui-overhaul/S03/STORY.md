# [S03] Missing Pages: About & Donate — RAP-173

## Story

As a **visitor**, I want to learn about the shelter's mission, team, and location so that I trust the organization before donating or adopting.

As a **donor**, I want a dedicated donation page so that I can contribute financially to the shelter without hitting a 404 error.

## Context

The Navbar and Footer both link to `/about` and `/donate`, but neither page exists. The homepage's second CTA ("Donate Now") leads to a 404. For an NGO that depends on donations, a broken donate link is a critical revenue blocker. The About page is the primary trust-building page per UX principles.

## Acceptance Criteria

### About Page (`/about`)
**Given** I navigate to `/about` (via Navbar, Footer, or direct URL)
**When** the page loads
**Then:**
- [ ] Page renders without 404
- [ ] Hero section with shelter mission statement in warm Spanish
- [ ] "Nuestra Historia" section — founding story, motivation, connection to Paraguay
- [ ] "Nuestro Equipo" section — placeholder structure for team members (name, role, photo placeholder)
- [ ] "Donde Estamos" section — physical address, hours of operation, embedded map placeholder
- [ ] Stats/impact section — number of animals helped (can be hardcoded initially, API later)
- [ ] CTA to adopt or donate at the bottom
- [ ] Page metadata (title, description) in Spanish
- [ ] Responsive layout (mobile-first)

### Donate Page (`/donate`)
**Given** I navigate to `/donate` (via Navbar, Footer, Homepage CTA, or direct URL)
**When** the page loads
**Then:**
- [ ] Page renders without 404
- [ ] Hero section explaining why donations matter, in warm tone
- [ ] "Como Ayuda Tu Donacion" section — breakdown of what donations fund (food, medical care, shelter maintenance)
- [ ] Donation options section — structure ready for payment integration (Stripe EUR for EU donors, local options for PY)
- [ ] For now: display bank transfer info and/or a "coming soon" for online payments
- [ ] EU donor callout — mention EUR donations welcome, SEPA transfer info placeholder
- [ ] "Otras Formas de Ayudar" — in-kind donations, supplies wishlist
- [ ] Transparency section — how funds are used, commitment to accountability
- [ ] CTA: WhatsApp contact for donation questions
- [ ] Page metadata (title, description) in Spanish
- [ ] Responsive layout

## Technical Notes

- Both pages are static content — server components, no `"use client"` needed.
- Use the new color system from S01 (primary orange for CTAs).
- All text strings should go in `src/lib/strings.ts` per S02.
- The donate page structure should be ready for Stripe integration (V2 work) — a future story will add the actual payment form.

## Definition of Done

- [ ] `/about` and `/donate` render correctly
- [ ] No dead links remain in Navbar or Footer for these routes
- [ ] Content is in Spanish with warm tone
- [ ] Mobile responsive
- [ ] Deployed to staging and verified

## Story Points: 5
