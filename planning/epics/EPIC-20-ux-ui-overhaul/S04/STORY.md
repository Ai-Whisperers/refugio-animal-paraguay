# [S04] Missing Pages: Volunteer & Foster — RAP-174

## Story

As a **potential volunteer**, I want to learn about volunteer opportunities at the shelter so that I can decide how to contribute my time.

As a **potential foster parent**, I want to understand the foster program so that I can temporarily care for an animal in need.

## Context

Footer links to `/volunteer` and `/foster` both 404. These pages serve lower-traffic but important audiences. Both programs are core to shelter operations per the project roadmap.

## Acceptance Criteria

### Volunteer Page (`/volunteer`)
- [ ] Page renders without 404
- [ ] Hero section explaining the volunteer program in warm Spanish
- [ ] "Que Hacen Nuestros Voluntarios" — types of volunteer activities (daily care, events, transport, outreach)
- [ ] "Requisitos" — age, availability, any requirements
- [ ] "Como Unirte" — WhatsApp contact or simple sign-up form (name, email, phone, availability)
- [ ] Testimonial placeholder — structure for volunteer quotes
- [ ] CTA: WhatsApp link to express interest
- [ ] Responsive, Spanish, warm tone

### Foster Page (`/foster`)
- [ ] Page renders without 404
- [ ] Hero explaining the foster concept: temporary home for animals awaiting adoption
- [ ] "Como Funciona" — step-by-step foster process
- [ ] "Que Necesitas" — basic requirements (space, time commitment, supplies provided by shelter)
- [ ] "Animales que Necesitan Acogida" — could link to filtered animal list (status=foster) in future
- [ ] FAQ section — common questions about fostering
- [ ] CTA: WhatsApp link to apply as foster
- [ ] Responsive, Spanish, warm tone

## Technical Notes

- Both are static content pages, server components.
- These are lower priority than About/Donate but still fix dead links.
- Volunteer sign-up form (if included) should use localStorage persistence per UX principles.

## Definition of Done

- [ ] `/volunteer` and `/foster` render correctly
- [ ] No dead links in Footer
- [ ] Content in Spanish with warm tone
- [ ] Mobile responsive
- [ ] Deployed to staging

## Story Points: 3
